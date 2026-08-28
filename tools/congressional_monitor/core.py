"""Load and analyse curated congressional PTR data.

The module deliberately calls the records *trades* or *transaction reports*.
PTR filings are delayed transaction disclosures, not a complete current
holdings statement.
"""

from __future__ import annotations

from collections import Counter
from datetime import date
import json
from pathlib import Path
import re
from typing import Any, Iterable

from tools.shared.workspace_paths import find_workspace_root


DEFAULT_FILES = ("congressional-pelosi-2026.json", "congressional-members-2026.json")
QUANTITY_PATTERNS = (
    (re.compile(r"([\d,]+(?:\.\d+)?)\s+shares?", re.IGNORECASE), "shares"),
    (re.compile(r"([\d,]+(?:\.\d+)?)\s+(?:call\s+options?|put options?|puts?|options?)", re.IGNORECASE), "contracts"),
)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"curated data file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"curated data must be an object: {path}")
    return value


def _member_from_pelosi(payload: dict[str, Any]) -> dict[str, Any]:
    member = dict(payload.get("member") or {})
    member.setdefault("member_id", "pelosi-nancy")
    member.setdefault("name", "Nancy Pelosi")
    member["district"] = f"{member.get('state', '')}{member.get('district', '')}".replace("House", "")
    member["reports_2026"] = len(payload.get("source", {}).get("reports", []))
    member["loaded_report_ids"] = [item["report_id"] for item in payload.get("source", {}).get("reports", [])]
    member["filing_date"] = max((item.get("filing_date", "") for item in payload.get("source", {}).get("reports", [])), default="")
    member["report_url"] = payload.get("source", {}).get("url", "")
    return member


def _normalize_trade(trade: dict[str, Any], member_id: str, ordinal: int | None = None, *, chamber: str = "House", source: str = "house-clerk") -> dict[str, Any]:
    result = dict(trade)
    result["member_id"] = member_id
    result["chamber"] = result.get("chamber") or chamber
    result["source"] = result.get("source") or source
    if not result.get("id") and result.get("report_id") and ordinal is not None:
        result["id"] = f"{result['report_id']}-{member_id}-{ordinal:03d}"
    result["transaction_code"] = result.get("transaction_code", result.get("code", ""))
    result["amount_range"] = result.get("amount_range", result.get("amount", ""))
    result["owner_code"] = result.get("owner_code", result.get("owner", ""))
    result["asset_type"] = result.get("asset_type", "")
    result["quantity"], result["quantity_unit"] = _extract_quantity(result.get("description", ""))
    return result


def _extract_quantity(description: str) -> tuple[float | None, str | None]:
    """Extract an explicitly stated share or option-contract count."""

    text = str(description or "")
    for pattern, unit in QUANTITY_PATTERNS:
        matches = list(pattern.finditer(text))
        if matches:
            # For option exercise text, prefer the underlying share count.
            match = matches[-1] if unit == "shares" else matches[0]
            return float(match.group(1).replace(",", "")), unit
    return None, None


def load_dataset(data_dir: Path | str | None = None, data_files: Iterable[Path | str] | None = None, senate_files: Iterable[Path | str] | None = None) -> dict[str, Any]:
    """Load the current curated congressional dataset and unify its schemas."""

    workspace = find_workspace_root()
    root = Path(data_dir) if data_dir else workspace / "data" / "curated"
    if not root.is_absolute():
        root = (workspace / root).resolve()
    payloads = [_read_json(root / filename) for filename in DEFAULT_FILES]
    payloads.extend(_read_json(Path(item) if Path(item).is_absolute() else root / Path(item)) for item in (data_files or []))

    members: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []
    seen_trade_ids: set[str] = set()
    seen_member_ids: set[str] = set()
    for payload in payloads:
        if payload.get("member"):
            member = _member_from_pelosi(payload)
            if member["member_id"] not in seen_member_ids:
                members.append(member)
                seen_member_ids.add(member["member_id"])
            payload_trades = payload.get("trades", [])
            member_id = member["member_id"]
        else:
            payload_trades = payload.get("trades", [])
            member_id = ""
            for item in payload.get("members", []):
                member = dict(item)
                if member.get("member_id") not in seen_member_ids:
                    members.append(member)
                    seen_member_ids.add(member["member_id"])
        for ordinal, item in enumerate(payload_trades, start=1):
            trade_member_id = item.get("member_id", member_id)
            normalized = _normalize_trade(item, trade_member_id, ordinal, chamber="House", source="house-clerk")
            trade_id = str(normalized.get("id", ""))
            if trade_id and trade_id in seen_trade_ids:
                continue
            if trade_id:
                seen_trade_ids.add(trade_id)
            trades.append(normalized)

    if senate_files:
        from .senate_efd import read_senate_efd

        for item in senate_files:
            senate_rows = read_senate_efd(item)
            for ordinal, row in enumerate(senate_rows, start=1):
                member_id = row.get("member_id") or row.get("member_name") or f"senate-member-{ordinal}"
                member_id = str(member_id).strip().lower().replace(" ", "-")
                if member_id not in seen_member_ids:
                    members.append({"member_id": member_id, "name": row.get("member_name") or member_id, "chamber": "Senate", "district": "", "loaded_report_ids": []})
                    seen_member_ids.add(member_id)
                normalized = _normalize_trade(row, member_id, ordinal, chamber="Senate", source="senate-efd")
                trade_id = str(normalized.get("id", ""))
                if trade_id and trade_id in seen_trade_ids:
                    continue
                if trade_id:
                    seen_trade_ids.add(trade_id)
                trades.append(normalized)

    member_by_id = {item["member_id"]: item for item in members}
    for trade in trades:
        member = member_by_id.get(trade["member_id"], {})
        trade["member_name"] = member.get("name", trade["member_id"])
        trade["district"] = member.get("district", "")
        trade["chamber"] = member.get("chamber", trade.get("chamber", "House"))
    return {
        "source": {"files": [str(item) for item in DEFAULT_FILES] + [str(item) for item in (data_files or [])], "senate_files": [str(item) for item in (senate_files or [])]},
        "members": members,
        "trades": trades,
    }


def _parse_day(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"date must use YYYY-MM-DD: {value}") from exc


def filter_trades(
    trades: Iterable[dict[str, Any]],
    *,
    member: str | None = None,
    ticker: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    direction: str | None = None,
    asset_type: str | None = None,
) -> list[dict[str, Any]]:
    """Filter trades using stable identifiers and report-native codes."""

    start, end = _parse_day(from_date), _parse_day(to_date)
    member_value = member.lower() if member else None
    ticker_value = ticker.upper() if ticker else None
    direction_value = direction.upper() if direction else None
    asset_value = asset_type.upper() if asset_type else None
    result = []
    for trade in trades:
        transaction_day = _parse_day(trade.get("transaction_date"))
        member_fields = (
            str(trade.get("member_id", "")).lower(),
            str(trade.get("member_name", "")).lower(),
            str(trade.get("district", "")).lower(),
        )
        member_match = not member_value or any(member_value in field for field in member_fields)
        if member_match and ticker_value:
            member_match = str(trade.get("ticker", "")).upper() == ticker_value
        if not member_match:
            continue
        if start and (transaction_day is None or transaction_day < start):
            continue
        if end and (transaction_day is None or transaction_day > end):
            continue
        if direction_value and str(trade.get("transaction_code", "")).upper() != direction_value:
            continue
        if asset_value and str(trade.get("asset_type", "")).upper() != asset_value:
            continue
        result.append(trade)
    return sorted(result, key=lambda item: (item.get("transaction_date", ""), item.get("id", "")), reverse=True)


def summarize(trades: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Return counts useful for a terminal report or downstream JSON."""

    rows = list(trades)
    dates = [item.get("transaction_date", "") for item in rows if item.get("transaction_date")]
    direction_labels = {"P": "买入/取得", "S": "卖出/转出", "E": "交换"}
    return {
        "trade_count": len(rows),
        "member_count": len({item.get("member_id") for item in rows}),
        "date_range": {"from": min(dates) if dates else None, "to": max(dates) if dates else None},
        "directions": {direction_labels.get(key, key): value for key, value in sorted(Counter(item.get("transaction_code", "") for item in rows).items())},
        "asset_types": dict(sorted(Counter(item.get("asset_type", "") for item in rows).items())),
        "members": dict(Counter(item.get("member_name", item.get("member_id", "")) for item in rows).most_common()),
        "tickers": dict(Counter(item.get("ticker", "") for item in rows).most_common()),
        "chambers": dict(Counter(item.get("chamber", "Unknown") for item in rows)),
        "sources": dict(Counter(item.get("source", "Unknown") for item in rows)),
        "quantity": {
            "explicit_trade_count": sum(item.get("quantity") is not None for item in rows),
            "unknown_trade_count": sum(item.get("quantity") is None for item in rows),
        },
    }


def infer_positions(trades: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate known quantity changes without inventing an opening balance.

    The result is a *disclosed net change estimate*. Unknown quantities remain
    visible in ``unknown_quantity_trade_count`` and do not become zero.
    """

    groups: dict[tuple[str, str, str], dict[str, Any]] = {}
    for trade in trades:
        key = (trade.get("member_id", ""), trade.get("ticker", ""), trade.get("asset_type", ""))
        row = groups.setdefault(key, {
            "member_id": trade.get("member_id", ""),
            "member_name": trade.get("member_name", trade.get("member_id", "")),
            "district": trade.get("district", ""),
            "ticker": trade.get("ticker", ""),
            "issuer": trade.get("issuer", ""),
            "asset_type": trade.get("asset_type", ""),
            "quantity_unit": None,
            "known_net_quantity_change": 0.0,
            "known_purchase_quantity": 0.0,
            "known_sale_quantity": 0.0,
            "known_quantity_trade_count": 0,
            "unknown_quantity_trade_count": 0,
            "trade_count": 0,
            "first_transaction_date": trade.get("transaction_date", ""),
            "last_transaction_date": trade.get("transaction_date", ""),
        })
        row["trade_count"] += 1
        transaction_date = trade.get("transaction_date", "")
        row["first_transaction_date"] = min(row["first_transaction_date"], transaction_date)
        row["last_transaction_date"] = max(row["last_transaction_date"], transaction_date)
        quantity = trade.get("quantity")
        if quantity is None:
            row["unknown_quantity_trade_count"] += 1
            continue
        row["quantity_unit"] = row["quantity_unit"] or trade.get("quantity_unit")
        code = str(trade.get("transaction_code", "")).upper()
        signed = quantity if code == "P" else -quantity if code == "S" else quantity if code == "E" and "received" in str(trade.get("description", "")).lower() else None
        if signed is None:
            row["unknown_quantity_trade_count"] += 1
            continue
        row["known_quantity_trade_count"] += 1
        row["known_net_quantity_change"] += signed
        if signed > 0:
            row["known_purchase_quantity"] += signed
        else:
            row["known_sale_quantity"] += abs(signed)
    for row in groups.values():
        if row["known_quantity_trade_count"] == 0:
            row["known_net_quantity_change"] = None
        for key in ("known_net_quantity_change", "known_purchase_quantity", "known_sale_quantity"):
            if row[key] is not None and float(row[key]).is_integer():
                row[key] = int(row[key])
        row["confidence"] = "complete_for_explicit_quantities" if row["unknown_quantity_trade_count"] == 0 else "partial"
    return sorted(groups.values(), key=lambda item: (item["last_transaction_date"], item["member_name"], item["ticker"]), reverse=True)


def validate_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    """Check the normalized dataset without changing it."""

    members = dataset.get("members", [])
    trades = dataset.get("trades", [])
    member_ids = {item.get("member_id") for item in members}
    trade_ids = [item.get("id") for item in trades if item.get("id")]
    duplicate_ids = sorted(item for item, count in Counter(trade_ids).items() if count > 1)
    missing_member_refs = sorted({item.get("member_id") for item in trades if item.get("member_id") not in member_ids})
    missing_required = []
    required = ("id", "member_id", "transaction_date", "ticker", "transaction_code", "asset_type")
    for trade in trades:
        absent = [field for field in required if not trade.get(field)]
        if absent:
            missing_required.append({"id": trade.get("id"), "fields": absent})
    warnings = []
    unknown_quantity = sum(item.get("quantity") is None for item in trades)
    if unknown_quantity:
        warnings.append(f"{unknown_quantity} trades have no explicit quantity and are excluded from numeric net-change totals")
    return {
        "ok": not duplicate_ids and not missing_member_refs and not missing_required,
        "member_count": len(members),
        "trade_count": len(trades),
        "duplicate_trade_ids": duplicate_ids,
        "missing_member_refs": missing_member_refs,
        "missing_required_fields": missing_required,
        "warnings": warnings,
    }


def coverage(dataset: dict[str, Any]) -> dict[str, Any]:
    """Summarize the loaded coverage and report-level provenance."""

    trades = dataset.get("trades", [])
    members = dataset.get("members", [])
    report_rows: dict[str, dict[str, Any]] = {}
    for trade in trades:
        report_id = trade.get("report_id")
        if not report_id:
            continue
        row = report_rows.setdefault(report_id, {"report_id": report_id, "member_ids": set(), "filing_dates": set()})
        row["member_ids"].add(trade.get("member_id"))
        if trade.get("filing_date"):
            row["filing_dates"].add(trade["filing_date"])
    reports = []
    for row in report_rows.values():
        reports.append({"report_id": row["report_id"], "member_ids": sorted(row["member_ids"]), "filing_dates": sorted(row["filing_dates"])})
    return {
        "member_count": len(members),
        "trade_count": len(trades),
        "chambers": {key: sum(1 for item in trades if item.get("chamber") == key) for key in sorted({item.get("chamber", "Unknown") for item in trades})},
        "members_by_chamber": {key: len({item.get("member_id") for item in trades if item.get("chamber") == key}) for key in sorted({item.get("chamber", "Unknown") for item in trades})},
        "date_range": summarize(trades)["date_range"],
        "members": [{"member_id": item.get("member_id"), "name": item.get("name"), "district": item.get("district"), "loaded_report_ids": item.get("loaded_report_ids", [])} for item in members],
        "reports": sorted(reports, key=lambda item: item["report_id"]),
        "source": dataset.get("source", {}),
    }


def cross_chamber_report(trades: Iterable[dict[str, Any]], *, from_date: str | None = None, to_date: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Summarize comparable House/Senate behavior without implying intent."""

    rows = filter_trades(list(trades), from_date=from_date, to_date=to_date)
    chamber_rows: dict[str, dict[str, Any]] = {}
    for chamber in sorted({item.get("chamber", "Unknown") for item in rows}):
        subset = [item for item in rows if item.get("chamber", "Unknown") == chamber]
        stats = summarize(subset)
        chamber_rows[chamber] = {"trade_count": stats["trade_count"], "member_count": stats["member_count"], "directions": stats["directions"], "asset_types": stats["asset_types"]}
    ticker_members: dict[str, dict[str, set[str]]] = {}
    for row in rows:
        ticker = str(row.get("ticker") or "").upper()
        if not ticker:
            continue
        chamber = row.get("chamber", "Unknown")
        direction = row.get("transaction_code", "")
        ticker_members.setdefault(ticker, {}).setdefault(chamber, set()).add(row.get("member_id", ""))
    joint = []
    for ticker, by_chamber in ticker_members.items():
        if len(by_chamber) >= 2:
            joint.append({"ticker": ticker, "chambers": {key: len(value) for key, value in by_chamber.items()}, "member_count": len(set().union(*by_chamber.values()))})
    joint.sort(key=lambda item: (-item["member_count"], item["ticker"]))
    recent = [{key: item.get(key) for key in ("transaction_date", "filing_date", "member_name", "member_id", "chamber", "ticker", "issuer", "transaction_code", "asset_type", "amount_range", "report_id") } for item in rows[:limit]]
    return {"date_range": summarize(rows)["date_range"], "trade_count": len(rows), "chambers": chamber_rows, "joint_tickers": joint[:limit], "recent_trades": recent}
