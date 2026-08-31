"""House Clerk annual financial-disclosure index helpers."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
import zipfile
import re


def _filing_sort_key(value: str) -> tuple[int, int, int]:
    try:
        parsed = datetime.strptime(value, "%m/%d/%Y")
        return (parsed.year, parsed.month, parsed.day)
    except ValueError:
        return (0, 0, 0)


def _filing_types(value: str | Iterable[str] | None) -> set[str] | None:
    if value is None or value == "":
        return None
    values = value.split(",") if isinstance(value, str) else value
    normalized = {str(item).strip().upper() for item in values if str(item).strip()}
    return normalized or None


def read_house_index(path: Path | str, *, filing_type: str | Iterable[str] | None = "P", member: str | None = None) -> list[dict[str, Any]]:
    """Read a House Clerk ``YYYYFD.txt`` or ZIP and return normalized rows."""

    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"House Clerk index not found: {source}")
    if source.suffix.lower() == ".zip":
        with zipfile.ZipFile(source) as archive:
            names = [name for name in archive.namelist() if name.lower().endswith(".txt")]
            if not names:
                raise ValueError(f"House Clerk ZIP has no .txt index: {source}")
            text = archive.read(names[0]).decode("utf-8-sig", errors="replace")
    else:
        text = source.read_text(encoding="utf-8-sig", errors="replace")
    rows: list[dict[str, Any]] = []
    wanted = (member or "").strip().lower()
    wanted_types = _filing_types(filing_type)
    reader = csv.DictReader(text.splitlines(), delimiter="\t")
    for raw in reader:
        normalized = {str(key or "").strip().lower(): str(value or "").strip() for key, value in raw.items()}
        row = {
            "prefix": normalized.get("prefix", ""),
            "last_name": normalized.get("last", ""),
            "first_name": normalized.get("first", ""),
            "suffix": normalized.get("suffix", ""),
            "filing_type": normalized.get("filingtype", ""),
            "district": normalized.get("statedst", ""),
            "year": normalized.get("year", ""),
            "filing_date": normalized.get("filingdate", ""),
            "document_id": normalized.get("docid", ""),
            "amends_report_id": next((normalized.get(key, "") for key in ("amendsreportid", "amendeddocid", "originaldocid", "relateddocid") if normalized.get(key)), ""),
            "source_file": str(source),
        }
        if wanted_types and row["filing_type"].upper() not in wanted_types:
            continue
        haystack = " ".join((row["first_name"], row["last_name"], row["district"], row["document_id"])).lower()
        if wanted and wanted not in haystack:
            continue
        rows.append(row)
    return rows


def summarize_house_index(rows: list[dict[str, Any]]) -> dict[str, Any]:
    member_records: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["first_name"].lower(), row["last_name"].lower(), row["district"].upper())
        record = member_records.setdefault(key, {
            "member_id": re.sub(r"[^a-z0-9]+", "-", f"{row['first_name']}-{row['last_name']}".lower()).strip("-") or row["document_id"],
            "name": f"{row['first_name']} {row['last_name']}".strip(),
            "district": row["district"],
            "ptr_count": 0,
            "first_filing_date": row["filing_date"],
            "last_filing_date": row["filing_date"],
            "report_ids": [],
        })
        record["ptr_count"] += 1
        if row["filing_date"]:
            if not record["first_filing_date"] or _filing_sort_key(row["filing_date"]) < _filing_sort_key(record["first_filing_date"]):
                record["first_filing_date"] = row["filing_date"]
            if _filing_sort_key(row["filing_date"]) > _filing_sort_key(record["last_filing_date"]):
                record["last_filing_date"] = row["filing_date"]
        if row["document_id"] not in record["report_ids"]:
            record["report_ids"].append(row["document_id"])
    return {
        "ptr_count": len(rows),
        "member_count": len(member_records),
        "members": sorted(member_records.values(), key=lambda item: item["name"]),
        "date_range": {
            "from": min((row["filing_date"] for row in rows if row["filing_date"]), default=None),
            "to": max((row["filing_date"] for row in rows if row["filing_date"]), default=None),
        },
        "rows": rows,
    }
