"""Adapter for Senate eFD exports and normalized transaction rows.

The Senate eFD site is protected against automated browsing; this adapter accepts
an official JSON/CSV export saved under ``sources/providers/senate-efd``.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import re
from typing import Any, Iterable


FIELD_ALIASES = {
    "report_id": ("report_id", "document_id", "docid", "id"),
    "member_id": ("member_id", "filer_id", "senator_id"),
    "member_name": ("member_name", "senator", "filer_name", "name"),
    "filing_date": ("filing_date", "date_filed", "filed_date"),
    "transaction_date": ("transaction_date", "date_of_transaction", "transactiondate", "date"),
    "asset_name": ("asset_name", "full_asset_name", "asset", "security", "issuer"),
    "ticker": ("ticker", "symbol"),
    "transaction_type": ("transaction_type", "type_of_transaction", "type", "action"),
    "amount_range": ("amount_range", "amount", "transaction_amount", "value"),
    "owner_code": ("owner_code", "owner", "ownership"),
    "asset_type": ("asset_type", "security_type", "category"),
}


def _value(row: dict[str, Any], names: Iterable[str]) -> str:
    lowered = {str(key).strip().lower(): value for key, value in row.items()}
    for name in names:
        value = lowered.get(name)
        if value not in (None, ""):
            return str(value).strip()
    return ""


def _transaction_code(value: str) -> str:
    text = value.upper()
    if text in {"P", "S", "E"}:
        return text
    if re.search(r"PURCHASE|BUY|ACQUIRE|RECEIVED", text):
        return "P"
    if re.search(r"SALE|SOLD|DISPOSE|TRANSFER", text):
        return "S"
    if re.search(r"EXCHANGE|SWAP", text):
        return "E"
    return ""


def _asset_type(asset_name: str, explicit: str) -> str:
    code = explicit.upper().strip()
    if code in {"ST", "OP", "AB", "OT"}:
        return code
    text = asset_name.upper()
    if re.search(r"CALL|PUT|OPTION|WARRANT", text):
        return "OP"
    if re.search(r"COMMON|ORDINARY|EQUITY|STOCK|SHARES?", text):
        return "ST"
    if re.search(r"BOND|NOTE|TREASURY|MUNICIPAL", text):
        return "AB"
    return "OT"


def normalize_efd_row(row: dict[str, Any], *, source_file: str = "") -> dict[str, Any]:
    asset_name = _value(row, FIELD_ALIASES["asset_name"])
    normalized = {
        "report_id": _value(row, FIELD_ALIASES["report_id"]),
        "member_id": _value(row, FIELD_ALIASES["member_id"]),
        "member_name": _value(row, FIELD_ALIASES["member_name"]),
        "filing_date": _value(row, FIELD_ALIASES["filing_date"]),
        "transaction_date": _value(row, FIELD_ALIASES["transaction_date"]),
        "asset_name": asset_name,
        "ticker": _value(row, FIELD_ALIASES["ticker"]),
        "issuer": _value(row, ("issuer", "asset_name", "asset")) or asset_name,
        "transaction_code": _transaction_code(_value(row, FIELD_ALIASES["transaction_type"])),
        "amount_range": _value(row, FIELD_ALIASES["amount_range"]),
        "owner_code": _value(row, FIELD_ALIASES["owner_code"]),
        "asset_type": _asset_type(asset_name, _value(row, FIELD_ALIASES["asset_type"])),
    }
    if source_file:
        normalized["source_file"] = source_file
    normalized["id"] = _value(row, ("id", "transaction_id")) or "|".join(normalized.get(key, "") for key in ("report_id", "member_id", "transaction_date", "ticker", "transaction_code", "asset_name"))
    return normalized


def read_senate_efd(path: Path | str, *, member: str | None = None) -> list[dict[str, Any]]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Senate eFD export not found: {source}")
    if source.suffix.lower() == ".json":
        payload = json.loads(source.read_text(encoding="utf-8"))
        raw_rows = payload.get("data", payload.get("rows", payload)) if isinstance(payload, dict) else payload
        if not isinstance(raw_rows, list):
            raise ValueError("Senate eFD JSON must contain a list or data/rows list")
    else:
        raw_rows = list(csv.DictReader(source.read_text(encoding="utf-8-sig", errors="replace").splitlines()))
    wanted = (member or "").lower()
    rows = [normalize_efd_row(row, source_file=str(source)) for row in raw_rows if isinstance(row, dict)]
    if wanted:
        rows = [row for row in rows if wanted in " ".join((row["member_id"], row["member_name"])).lower()]
    return rows


def summarize_senate_efd(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "trade_count": len(rows),
        "member_count": len({row["member_id"] or row["member_name"] for row in rows}),
        "members": sorted({row["member_name"] or row["member_id"] for row in rows}),
        "date_range": {"from": min((row["transaction_date"] for row in rows if row["transaction_date"]), default=None), "to": max((row["transaction_date"] for row in rows if row["transaction_date"]), default=None)},
        "rows": rows,
    }
