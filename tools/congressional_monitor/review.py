"""Review decisions and conservative promotion of OCR candidates."""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import re
from typing import Any


VALID_STATUSES = {"approved", "rejected", "needs_more_evidence"}
VALID_CODES = {"P", "S", "E"}
VALID_ASSET_TYPES = {"ST", "OP", "AB", "OT"}
AMOUNT_RANGE_RE = re.compile(r"^\$?\s*[\d,]+(?:\.\d{2})?\s*-\s*\$?\s*[\d,]+(?:\.\d{2})?$|^\$?\s*[\d,]+(?:\.\d{2})?$|^N/?A$", re.IGNORECASE)


def _stable_id(record: dict[str, Any]) -> str:
    key = "|".join(str(record.get(field, "")) for field in ("report_id", "member_id", "transaction_date", "ticker", "asset_type", "transaction_code", "owner_code", "candidate_id"))
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]


def _iso_date(value: Any) -> bool:
    try:
        date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return False
    return True


def review_template(review_payload: dict[str, Any]) -> dict[str, Any]:
    """Create an editable decision template from an OCR review queue."""

    queue = review_payload.get("candidates") or review_payload.get("review_queue") or []
    decisions = []
    for index, candidate in enumerate(queue):
        ticker_options = candidate.get("ticker_candidates") or []
        amount_options = candidate.get("amount_range_candidates") or []
        decisions.append({
            "candidate_index": index,
            "candidate_id": candidate.get("candidate_id"),
            "status": "needs_more_evidence",
            "ticker": ticker_options[0].get("ticker", "") if len(ticker_options) == 1 else "",
            "issuer": candidate.get("asset_name") or "",
            "asset_type": (candidate.get("asset_type_candidates") or [""])[0],
            "transaction_code": (candidate.get("transaction_codes") or [""])[0],
            "amount_range": amount_options[0] if len(amount_options) == 1 else "",
            "owner_code": candidate.get("owner_code") or "",
            "transaction_date": candidate.get("transaction_date") or "",
            "filing_date": "",
            "member_id": "",
            "member_name": "",
            "district": "",
            "report_id": "",
            "notes": "",
        })
    return {
        "source_file": review_payload.get("source_file"),
        "source_sha256": review_payload.get("source_sha256"),
        "decisions": decisions,
    }


def _validate_approved(record: dict[str, Any]) -> list[str]:
    required = ("ticker", "issuer", "asset_type", "transaction_code", "amount_range", "member_id", "report_id", "transaction_date", "filing_date")
    issues = [f"missing_{field}" for field in required if not str(record.get(field, "")).strip()]
    if record.get("asset_type") and record["asset_type"] not in VALID_ASSET_TYPES:
        issues.append("invalid_asset_type")
    if record.get("transaction_code") and record["transaction_code"] not in VALID_CODES:
        issues.append("invalid_transaction_code")
    if record.get("transaction_date") and not _iso_date(record["transaction_date"]):
        issues.append("invalid_transaction_date")
    if record.get("filing_date") and not _iso_date(record["filing_date"]):
        issues.append("invalid_filing_date")
    if record.get("amount_range") and not AMOUNT_RANGE_RE.match(str(record["amount_range"]).strip()):
        issues.append("invalid_amount_range")
    return issues


def apply_review_decisions(review_payload: dict[str, Any], decisions_payload: dict[str, Any], *, defaults: dict[str, Any] | None = None) -> dict[str, Any]:
    """Apply decisions and return a new curated-compatible payload.

    Approved rows are validated and promoted; rejected or unresolved rows stay
    in the audit output. No source OCR evidence is discarded.
    """

    defaults = defaults or {}
    queue = review_payload.get("candidates") or review_payload.get("review_queue", [])
    queue_by_id = {item.get("candidate_id"): item for item in queue if item.get("candidate_id")}
    promoted: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for decision in decisions_payload.get("decisions", []):
        if not isinstance(decision, dict):
            continue
        candidate_id = decision.get("candidate_id")
        candidate = queue_by_id.get(candidate_id) if candidate_id else None
        if candidate is None and isinstance(decision.get("candidate_index"), int):
            index = decision["candidate_index"]
            if 0 <= index < len(queue):
                candidate = queue[index]
                candidate_id = candidate.get("candidate_id") or f"index-{index}"
        status = str(decision.get("status", "needs_more_evidence"))
        audit_row = {"candidate_id": candidate_id, "status": status, "notes": decision.get("notes", "")}
        if candidate is None:
            audit_row["issues"] = ["unknown_candidate_id"]
            errors.append(audit_row)
            audit.append(audit_row)
            continue
        if status not in VALID_STATUSES:
            audit_row["issues"] = ["invalid_review_status"]
            errors.append(audit_row)
            audit.append(audit_row)
            continue
        if status != "approved":
            audit_row["source"] = candidate
            audit.append(audit_row)
            continue
        record = dict(candidate)
        record.update(defaults)
        record.update({key: value for key, value in decision.items() if key not in {"candidate_id", "status", "notes"} and value not in (None, "")})
        if not record.get("transaction_code") and len(candidate.get("transaction_codes") or []) == 1:
            record["transaction_code"] = candidate["transaction_codes"][0]
        if not record.get("asset_type") and len(candidate.get("asset_type_candidates") or []) == 1:
            record["asset_type"] = candidate["asset_type_candidates"][0]
        record["id"] = record.get("id") or _stable_id({**record, "candidate_id": candidate_id})
        issues = _validate_approved(record)
        if record["id"] in seen_ids:
            issues.append("duplicate_trade_id")
        if issues:
            audit_row["issues"] = issues
            audit_row["record"] = record
            errors.append(audit_row)
        else:
            seen_ids.add(record["id"])
            curated = {key: record.get(key) for key in ("id", "report_id", "filing_date", "transaction_date", "ticker", "issuer", "asset_type", "transaction_code", "amount_range", "owner_code", "description", "member_name", "district") if record.get(key) not in (None, "")}
            curated["member_id"] = record["member_id"]
            promoted.append(curated)
            audit_row["record_id"] = curated["id"]
        audit.append(audit_row)
    members = {}
    for record in promoted:
        member_id = record["member_id"]
        members.setdefault(member_id, {
            "member_id": member_id,
            "name": record.get("member_name", member_id),
            "district": record.get("district", ""),
            "loaded_report_ids": [],
            "filing_date": record.get("filing_date", ""),
        })
        if record.get("report_id") not in members[member_id]["loaded_report_ids"]:
            members[member_id]["loaded_report_ids"].append(record["report_id"])
    return {
        "source": {"name": "OCR-reviewed House Clerk PTR", "source_file": review_payload.get("source_file"), "source_sha256": review_payload.get("source_sha256")},
        "members": list(members.values()),
        "trades": promoted,
        "review_audit": audit,
        "errors": errors,
        "promoted_count": len(promoted),
    }
