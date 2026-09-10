#!/usr/bin/env python3
"""Mechanical validation for the assembled report: coverage, depth, citations.

This is the Phase 5 gate. It checks the same *kinds* of things a citation
gate always checks — every claim must cite a real, known source — against
this skill's own 8-topic schema and its `[page_id]` citation format (a page
is "real" if it's recorded in `<workspace>/pages.jsonl`; there is no line-
range to resolve, since the Agent reads and cites whole pages it fetched
itself, not indexed chunks of cleaned Markdown).

Exit code is non-zero if any REQUIRED topic is missing its draft file, claims
`covered` without meeting its depth threshold, or contains a citation that
does not resolve to a page_id in `pages.jsonl`. `partial` and `not_found` are
legitimate, honest outcomes and do not fail validation on their own — they
just get reported.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from topics import TABLE_SCHEMAS, TOPICS  # noqa: E402

_CITATION = re.compile(r"\[(?P<page_id>P\d+)\]")
_BULLET = re.compile(r"^\s*[-*]\s+\S", re.MULTILINE)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _load_pages(workspace: Path) -> set[str]:
    """Set of page_ids recorded in pages.jsonl — the citation resolution target."""

    return {record["page_id"] for record in _read_jsonl(workspace / "pages.jsonl") if record.get("page_id")}


def _check_citations(text: str, known_pages: set[str], errors: list[str], context: str) -> int:
    found = 0
    for match in _CITATION.finditer(text):
        found += 1
        page_id = match.group("page_id")
        if page_id not in known_pages:
            errors.append(f"{context}: citation references unknown page id {page_id!r}")
    return found


def _parse_topic_draft(path: Path) -> tuple[dict[str, Any], str]:
    import yaml

    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path}: missing YAML frontmatter")
    closing = lines[1:].index("---") + 1
    frontmatter = yaml.safe_load("\n".join(lines[1:closing])) or {}
    body = "\n".join(lines[closing + 1 :])
    return frontmatter, body


def validate(*, workspace: Path, topics_dir: Path, data_dir: Path) -> list[str]:
    errors: list[str] = []
    known_pages = _load_pages(workspace)
    coverage_summary: dict[str, str] = {}

    table_rows: dict[str, list[dict[str, Any]]] = {name: _read_jsonl(data_dir / f"{name}.jsonl") for name in TABLE_SCHEMAS}
    for table_name, schema in TABLE_SCHEMAS.items():
        required_fields = schema - {"evidence_refs"}
        for index, row in enumerate(table_rows[table_name]):
            missing = required_fields - row.keys()
            if missing:
                errors.append(f"{table_name}.jsonl row {index}: missing fields {sorted(missing)}")
            refs = row.get("evidence_refs") or []
            if not refs:
                errors.append(f"{table_name}.jsonl row {index}: no evidence_refs")
            for ref in refs:
                _check_citations(ref, known_pages, errors, f"{table_name}.jsonl row {index}")

    for topic in TOPICS:
        draft_path = topics_dir / f"{topic.id}.md"
        if not draft_path.exists():
            errors.append(f"{topic.id}: required topic has no draft file (must exist, even to declare not_found)")
            coverage_summary[topic.id] = "missing"
            continue

        frontmatter, body = _parse_topic_draft(draft_path)
        status = frontmatter.get("coverage_status")
        if status not in {"covered", "partial", "not_found"}:
            errors.append(f"{topic.id}: coverage_status must be covered/partial/not_found, got {status!r}")
        coverage_summary[topic.id] = status or "unknown"

        citation_count = _check_citations(body, known_pages, errors, topic.id)
        if topic.table:
            rows = table_rows[topic.table]
            if topic.table == "timeline":
                rows = [row for row in rows if row.get("category") == topic.id]
            depth = len(rows)
        else:
            depth = len(_BULLET.findall(body))

        if status == "covered":
            if depth < topic.min_key_facts:
                errors.append(f"{topic.id}: marked covered but depth={depth} < min_key_facts={topic.min_key_facts}")
            if citation_count == 0 and not topic.table:
                errors.append(f"{topic.id}: marked covered but body has zero evidence citations")
        elif status not in {"partial", "not_found"} and status is not None:
            pass  # already flagged above

    print("Coverage summary:")
    for topic in TOPICS:
        print(f"  {topic.id:32s} {coverage_summary.get(topic.id, 'skipped'):10s}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path, help="workspace dir containing pages.jsonl")
    parser.add_argument("--topics-dir", required=True, type=Path)
    parser.add_argument("--data-dir", required=True, type=Path)
    args = parser.parse_args(argv)

    errors = validate(workspace=args.workspace, topics_dir=args.topics_dir, data_dir=args.data_dir)
    if errors:
        print(f"\n{len(errors)} validation error(s):")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("\nvalidation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
