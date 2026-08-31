"""Deterministic de-duplication for normalized congressional trades."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from typing import Any, Iterable


FINGERPRINT_FIELDS = (
    "member_id", "transaction_date", "ticker", "asset_type", "transaction_code",
    "owner_code", "amount_range", "issuer", "description", "quantity", "quantity_unit",
)


def trade_fingerprint(trade: dict[str, Any]) -> str:
    """Return a source-independent key for an otherwise identical transaction."""

    payload = [str(trade.get(field) or "").strip().upper() if field not in {"quantity"} else trade.get(field) for field in FINGERPRINT_FIELDS]
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def deduplicate_trades(trades: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Drop exact cross-file duplicates while preserving conflicts for review.

    Rows with the same explicit transaction ID are duplicates. Rows without a
    reliable ID use a source-independent transaction fingerprint. A collision
    with different report IDs is retained as one effective row and listed in
    ``duplicates`` so amendments or source disagreements remain auditable.
    """

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in trades:
        key = f"fp:{trade_fingerprint(row)}"
        groups[key].append(row)
    unique: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    for key, rows in groups.items():
        if len(rows) == 1:
            unique.append(rows[0])
            continue
        report_ids_by_id = {str(row.get("id") or ""): str(row.get("report_id") or "") for row in rows}
        report_ids = {value for value in report_ids_by_id.values() if value}
        # A single report may legitimately contain repeated-looking rows (for
        # example separate owners). Keep distinct IDs from that report.
        if len(report_ids) <= 1 and len(report_ids_by_id) == len(rows):
            unique.extend(rows)
            continue
        ordered = sorted(rows, key=lambda item: (str(item.get("filing_date") or ""), str(item.get("source") or "")), reverse=True)
        winner = dict(ordered[0])
        report_ids = sorted({str(item.get("report_id")) for item in rows if item.get("report_id")})
        source_files = sorted({str(item.get("source_file")) for item in rows if item.get("source_file")})
        if report_ids:
            winner["duplicate_report_ids"] = report_ids
        if source_files:
            winner["duplicate_source_files"] = source_files
        unique.append(winner)
        duplicates.append({"key": key, "kept_id": winner.get("id"), "report_ids": report_ids, "count": len(rows)})
    return {"trades": unique, "duplicates": duplicates, "duplicate_count": sum(item["count"] - 1 for item in duplicates)}
