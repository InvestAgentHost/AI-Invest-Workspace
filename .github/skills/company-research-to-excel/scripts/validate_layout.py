#!/usr/bin/env python3
"""Validate that a thematic Excel layout places every bundle table exactly once."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


INVALID_SHEET_CHARS = re.compile(r"[\[\]:*?/\\]")


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("layout", type=Path)
    args = parser.parse_args()

    bundle = load_object(args.bundle)
    layout = load_object(args.layout)
    if bundle.get("schema") != "company-research-excel-bundle.v2":
        raise ValueError("Unsupported or missing bundle schema")

    expected = [table.get("table_id") for table in bundle.get("tables", [])]
    if not expected or any(not table_id for table_id in expected):
        raise ValueError("Bundle contains no valid table IDs")
    if len(expected) != len(set(expected)):
        raise ValueError("Bundle table IDs are not unique")

    sheets = layout.get("sheets")
    if not isinstance(sheets, list) or not sheets:
        raise ValueError("Layout must contain a non-empty sheets list")

    sheet_names: list[str] = []
    placements: list[str] = []
    section_count = 0
    for sheet in sheets:
        if not isinstance(sheet, dict):
            raise ValueError("Every sheet entry must be an object")
        name = str(sheet.get("name") or "").strip()
        if not name:
            raise ValueError("Every sheet needs a name")
        if len(name) > 31 or INVALID_SHEET_CHARS.search(name):
            raise ValueError(f"Invalid Excel sheet name: {name}")
        sheet_names.append(name.lower())
        sections = sheet.get("sections")
        if not isinstance(sections, list) or not sections:
            raise ValueError(f"Sheet has no sections: {name}")
        for section in sections:
            if not isinstance(section, dict):
                raise ValueError(f"Invalid section on sheet: {name}")
            title = str(section.get("title") or "").strip()
            table_ids = section.get("table_ids")
            if not title:
                raise ValueError(f"Section without title on sheet: {name}")
            if not isinstance(table_ids, list) or not table_ids:
                raise ValueError(f"Section has no table IDs: {name} / {title}")
            placements.extend(str(table_id) for table_id in table_ids)
            section_count += 1

    duplicate_sheets = sorted(name for name, count in Counter(sheet_names).items() if count > 1)
    counts = Counter(placements)
    missing = sorted(set(expected) - set(placements))
    unknown = sorted(set(placements) - set(expected))
    duplicates = sorted(table_id for table_id, count in counts.items() if count > 1)
    failures = []
    if duplicate_sheets:
        failures.append("Duplicate sheet names: " + ", ".join(duplicate_sheets))
    if missing:
        failures.append("Missing table IDs: " + ", ".join(missing))
    if unknown:
        failures.append("Unknown table IDs: " + ", ".join(unknown))
    if duplicates:
        failures.append("Repeated table IDs: " + ", ".join(duplicates))

    result = {
        "status": "FAIL" if failures else "PASS",
        "tables": len(expected),
        "sheets": len(sheets),
        "sections": section_count,
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
