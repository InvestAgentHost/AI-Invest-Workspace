"""Explainable priority ranking for congressional members.

Role and media fields are intentionally optional.  PTR data normally contains
transactions, not a member's current leadership, committee, or press profile.
When those fields are absent this module reports the missing dimensions instead
of treating them as evidence of low political importance.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
import json
from math import log1p
from pathlib import Path
from typing import Any, Iterable


def _day(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10]) if value else None
    except ValueError:
        return None


def _key(row: dict[str, Any]) -> str:
    return str(row.get("member_id") or row.get("member_name") or "unknown-member")


def _num(value: Any) -> float | None:
    try:
        return float(value) if value is not None and str(value).strip() else None
    except (TypeError, ValueError):
        return None


def load_member_profiles(path: Path | str | None) -> dict[str, dict[str, Any]]:
    """Load optional role/media metadata keyed by member ID or name.

    Accepted formats are ``{"members": [{"member_id": ...}, ...]}`` and a
    direct mapping from identifier to profile object.
    """

    if not path:
        return {}
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("members"), list):
        items = payload["members"]
    elif isinstance(payload, dict):
        items = [{"member_id": key, **(value if isinstance(value, dict) else {})} for key, value in payload.items()]
    else:
        raise ValueError("member profile metadata must be a JSON object")
    profiles: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        identifier = str(item.get("member_id") or item.get("name") or item.get("member_name") or "").strip().lower()
        if identifier:
            profiles[identifier] = dict(item)
    return profiles


def load_important_members(path: Path | str | None) -> dict[str, dict[str, Any]]:
    """Load a conservative, human-curated list of publicly influential members."""

    if not path:
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    items = payload.get("members", []) if isinstance(payload, dict) else []
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        identifier = str(item.get("member_id") or item.get("name") or "").strip().lower()
        if identifier:
            result[identifier] = dict(item)
    return result


def _profile_for(member_id: str, member_name: str, profiles: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return profiles.get(member_id.lower()) or profiles.get(member_name.lower()) or {}


def _leadership_score(profile: dict[str, Any]) -> tuple[float, str]:
    explicit = _num(profile.get("leadership_score"))
    if explicit is not None:
        return max(0.0, min(30.0, explicit)), "provided"
    text = " ".join(str(profile.get(key) or "") for key in ("leadership", "leadership_role", "title", "role")).strip().lower()
    if not text:
        return 0.0, "missing"
    for terms, score in (
        (("speaker",), 30),
        (("majority leader", "minority leader", "majority whip", "minority whip"), 25),
        (("caucus chair", "conference chair", "caucus vice chair", "conference vice chair"), 22),
        (("chair emeritus",), 15),
    ):
        if any(term in text for term in terms):
            return float(score), "inferred_from_role"
    return 8.0, "provided_role"


def _committee_score(profile: dict[str, Any]) -> tuple[float, str]:
    explicit = _num(profile.get("committee_score"))
    if explicit is not None:
        return max(0.0, min(20.0, explicit)), "provided"
    roles = profile.get("committee_roles") or profile.get("committees") or profile.get("committee")
    if not roles:
        return 0.0, "missing"
    if isinstance(roles, str):
        roles = [roles]
    roles = list(roles) if isinstance(roles, (list, tuple, set)) else [str(roles)]
    text = " ".join(str(item) for item in roles).lower()
    score = 0.0
    if "chair" in text or "ranking" in text:
        score += 14.0
    score += min(6.0, max(0.0, len(roles) - 1) * 2.0)
    return min(20.0, score), "provided_committee"


def _media_score(profile: dict[str, Any]) -> tuple[float, str]:
    explicit = _num(profile.get("media_attention_score"))
    if explicit is not None:
        return max(0.0, min(20.0, explicit)), "provided"
    mentions = _num(profile.get("media_mentions_90d"))
    if mentions is None:
        mentions = _num(profile.get("media_mentions"))
    if mentions is None:
        return 0.0, "missing"
    return min(20.0, round(log1p(max(0.0, mentions)) * 5.0, 1)), "derived_from_mentions"


def rank_member_priorities(
    trades: Iterable[dict[str, Any]],
    *,
    profiles: dict[str, dict[str, Any]] | None = None,
    recent_days: int = 90,
    as_of: date | None = None,
) -> list[dict[str, Any]]:
    """Rank members using role metadata plus observed PTR behavior.

    Total score is 100 points: leadership 30, committee 20, media 20,
    recent activity 20, and historical coverage 10.  Missing metadata is
    listed in ``missing_dimensions`` and does not silently become a negative
    political signal.
    """

    rows = [dict(row) for row in trades if isinstance(row, dict) and _day(row.get("transaction_date"))]
    if not rows:
        return []
    end = as_of or max(_day(row.get("transaction_date")) for row in rows if _day(row.get("transaction_date")))
    recent_start = end - timedelta(days=max(1, recent_days) - 1)
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_key(row)].append(row)
    profiles = profiles or {}
    output: list[dict[str, Any]] = []
    for member_id, member_rows in grouped.items():
        name = str(next((row.get("member_name") for row in member_rows if row.get("member_name")), member_id))
        profile = _profile_for(member_id, name, profiles)
        recent = [row for row in member_rows if recent_start <= _day(row.get("transaction_date")) <= end]
        recent_tickers = {str(row.get("ticker") or "").upper() for row in recent if row.get("ticker")}
        history_tickers = {str(row.get("ticker") or "").upper() for row in member_rows if row.get("ticker")}
        recent_dates = {_day(row.get("transaction_date")) for row in recent if _day(row.get("transaction_date"))}
        history_dates = [_day(row.get("transaction_date")) for row in member_rows if _day(row.get("transaction_date"))]
        repeat_count = sum(1 for ticker in recent_tickers if sum(str(row.get("ticker") or "").upper() == ticker and str(row.get("transaction_code") or "").upper() == "P" for row in recent) >= 2)
        leadership, leadership_source = _leadership_score(profile)
        committee, committee_source = _committee_score(profile)
        media, media_source = _media_score(profile)
        activity = min(20.0, round(min(12.0, len(recent) * 1.5) + min(5.0, len(recent_tickers) * 0.5) + min(3.0, repeat_count * 1.5), 1))
        span_days = (max(history_dates) - min(history_dates)).days if history_dates else 0
        history = min(10.0, round(min(6.0, span_days / 365 * 3.0) + min(4.0, len(history_tickers) / 10), 1))
        missing = [name for name, source in (("领导职务", leadership_source), ("委员会职务", committee_source), ("媒体关注度", media_source)) if source == "missing"]
        total = round(leadership + committee + media + activity + history, 1)
        level = "A 核心" if total >= 70 else "B 重点" if total >= 45 else "C 观察" if total >= 25 else "D 普通"
        output.append({
            "member_id": member_id,
            "member_name": name,
            "party": next((row.get("party") for row in member_rows if row.get("party")), profile.get("party")),
            "chamber": next((row.get("chamber") for row in member_rows if row.get("chamber")), profile.get("chamber")),
            "district": next((row.get("district") for row in member_rows if row.get("district")), profile.get("district")),
            "priority_score": total,
            "priority_level": level,
            "priority_components": {"leadership": leadership, "committee": committee, "media": media, "recent_activity": activity, "historical_coverage": history},
            "missing_dimensions": missing,
            "recent_trade_count": len(recent),
            "recent_ticker_count": len(recent_tickers),
            "historical_trade_count": len(member_rows),
            "historical_ticker_count": len(history_tickers),
            "metadata_source": profile.get("source") or None,
        })
    return sorted(output, key=lambda item: (-item["priority_score"], -item["recent_trade_count"], item["member_name"]))
