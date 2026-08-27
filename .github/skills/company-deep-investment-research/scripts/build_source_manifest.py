#!/usr/bin/env python3
"""Build a deterministic, hash-backed manifest for a source directory."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


FIELDS = [
    "source_id",
    "category",
    "title",
    "content_date",
    "accessed_at",
    "original_url_or_reference",
    "local_path",
    "sha256",
    "content_type",
    "locator_scheme",
    "usability",
    "notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--url-map", type=Path, help="JSON mapping of relative path to URL/reference")
    parser.add_argument("--category", default="external")
    parser.add_argument("--accessed-at", default=datetime.now(timezone.utc).date().isoformat())
    parser.add_argument("--force", action="store_true", help="Overwrite an existing generated manifest")
    return parser.parse_args()


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    return {
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".html": "text/html",
        ".htm": "text/html",
        ".json": "application/json",
        ".csv": "text/csv",
        ".pdf": "application/pdf",
    }.get(suffix, "application/octet-stream")


def read_existing_ids(output: Path) -> dict[str, str]:
    if not output.exists():
        return {}
    mapping: dict[str, str] = {}
    with output.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rel = row.get("local_path", "")
            source_id = row.get("source_id", "")
            if rel and source_id:
                mapping[rel] = source_id
    return mapping


def next_id(existing: set[str]) -> str:
    numbers = []
    for value in existing:
        match = re.fullmatch(r"S(\d+)", value)
        if match:
            numbers.append(int(match.group(1)))
    return f"S{(max(numbers, default=0) + 1):03d}"


def main() -> int:
    args = parse_args()
    source_root = args.source_root.resolve()
    output = args.output.resolve()
    if not source_root.is_dir():
        raise SystemExit(f"source_root is not a directory: {source_root}")
    if output.exists() and not args.force:
        raise SystemExit(f"output exists; pass --force to replace: {output}")

    url_map: dict[str, str] = {}
    if args.url_map:
        url_map = json.loads(args.url_map.read_text(encoding="utf-8"))
        if not isinstance(url_map, dict):
            raise SystemExit("--url-map must contain a JSON object")

    existing = read_existing_ids(output)
    used_ids = set(existing.values())
    files = sorted(path for path in source_root.rglob("*") if path.is_file() and path.resolve() != output)
    rows = []
    for path in files:
        rel = path.relative_to(source_root).as_posix()
        source_id = existing.get(rel)
        if not source_id:
            source_id = next_id(used_ids)
            used_ids.add(source_id)
        rows.append(
            {
                "source_id": source_id,
                "category": args.category,
                "title": path.name,
                "content_date": "",
                "accessed_at": args.accessed_at,
                "original_url_or_reference": str(url_map.get(rel, "")),
                "local_path": rel,
                "sha256": hash_file(path),
                "content_type": content_type(path),
                "locator_scheme": "page/line/turn as applicable",
                "usability": "pending",
                "notes": "",
            }
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(f".{output.name}.tmp-{os.getpid()}")
    with temp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    temp.replace(output)
    print(f"manifest: {output}")
    print(f"source_root: {source_root}")
    print(f"files: {len(rows)}")
    print(f"preserved_ids: {len(existing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
