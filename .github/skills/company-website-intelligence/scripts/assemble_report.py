#!/usr/bin/env python3
"""Assemble the final structured Markdown report + data tables from Agent drafts.

Input layout this script expects (the Agent produces these during Phase 5):

    <topics-dir>/<topic_id>.md   # one file per topic, YAML frontmatter + body
    <data-dir>/business_units.jsonl
    <data-dir>/leadership.jsonl
    <data-dir>/timeline.jsonl        # shared by news_and_announcements and
                                      # strategy_partnerships_ma via `category`
    <data-dir>/ir_documents.jsonl

Frontmatter contract for each `<topic_id>.md` (see references/deliverable-
contract.md for the full spec):

    ---
    coverage_status: covered   # covered | partial | not_found
    source_count: 4
    ---
    ## Key Facts
    - ...

A missing topic file is treated as `not_found` rather than an error — Phase 7
(`validate_report.py`) is what decides whether that is acceptable for a
required topic.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from topics import TABLE_SCHEMAS, TOPICS, Topic  # noqa: E402

_FRONTMATTER_DELIM = "---"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _parse_topic_draft(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != _FRONTMATTER_DELIM:
        raise ValueError(f"{path}: missing YAML frontmatter (must start with '---')")
    try:
        closing = lines[1:].index(_FRONTMATTER_DELIM) + 1
    except ValueError:
        raise ValueError(f"{path}: unterminated YAML frontmatter") from None
    import yaml

    frontmatter = yaml.safe_load("\n".join(lines[1:closing])) or {}
    body = "\n".join(lines[closing + 1 :]).strip("\n")
    return frontmatter, body


def _render_table_preview(rows: list[dict[str, Any]], fields: list[str], *, limit: int = 20) -> str:
    if not rows:
        return "_No structured rows recorded._\n"
    header = "| " + " | ".join(fields) + " |"
    divider = "| " + " | ".join("---" for _ in fields) + " |"
    body_lines = []
    for row in rows[:limit]:
        cells = []
        for field in fields:
            value = row.get(field, "")
            if isinstance(value, list):
                value = "; ".join(str(item) for item in value)
            cells.append(str(value).replace("\n", " ").replace("|", "\\|"))
        body_lines.append("| " + " | ".join(cells) + " |")
    table = "\n".join([header, divider, *body_lines])
    if len(rows) > limit:
        table += f"\n\n_...and {len(rows) - limit} more rows — see the linked data file._"
    return table


def assemble(
    *,
    topics_dir: Path,
    data_dir: Path,
    output_dir: Path,
    company: str,
    domains: list[str],
    as_of: str,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_data_dir = output_dir / "data"
    report_data_dir.mkdir(exist_ok=True)

    table_rows_cache: dict[str, list[dict[str, Any]]] = {}
    for table_name in TABLE_SCHEMAS:
        source = data_dir / f"{table_name}.jsonl"
        rows = _read_jsonl(source)
        table_rows_cache[table_name] = rows
        destination = report_data_dir / f"{table_name}.jsonl"
        if source.exists():
            shutil.copyfile(source, destination)
        else:
            destination.write_text("", encoding="utf-8")

    sections: list[str] = []
    toc: list[str] = []
    for number, topic in enumerate(TOPICS, start=1):
        anchor = topic.title.lower().replace(" ", "-").replace("&", "").replace(",", "").replace("--", "-")
        toc.append(f"{number}. [{topic.title}](#{number}-{anchor})")
        sections.append(_render_topic_section(number, topic, topics_dir, table_rows_cache))

    header = (
        f"# {company} — Official Website Intelligence Report\n\n"
        f"- **As of:** {as_of}\n"
        f"- **Domains crawled:** {', '.join(domains)}\n"
        f"- **Source tier:** Tier-3 (company's own public statements — not "
        "independently verified; cross-check against filings/press coverage "
        "before treating as fact)\n\n"
        "## Table of Contents\n" + "\n".join(toc) + "\n"
    )
    report_path = output_dir / "official_website_report.md"
    report_path.write_text(header + "\n" + "\n\n".join(sections) + "\n", encoding="utf-8")
    return report_path


def _render_topic_section(
    number: int, topic: Topic, topics_dir: Path, table_rows_cache: dict[str, list[dict[str, Any]]]
) -> str:
    draft_path = topics_dir / f"{topic.id}.md"
    if draft_path.exists():
        frontmatter, body = _parse_topic_draft(draft_path)
        coverage_status = frontmatter.get("coverage_status", "partial")
        source_count = frontmatter.get("source_count", 0)
    else:
        coverage_status, source_count, body = "not_found", 0, "_No content produced for this topic._"

    lines = [f"## {number}. {topic.title}", f"**Coverage:** {coverage_status} ({source_count} sources)", "", body]

    if topic.table:
        rows = table_rows_cache.get(topic.table, [])
        if topic.table == "timeline":
            rows = [row for row in rows if row.get("category") == topic.id]
        fields = sorted(TABLE_SCHEMAS[topic.table] - {"evidence_refs"}) + ["evidence_refs"]
        lines += ["", f"### Data table: `{topic.table}.jsonl`" + ("" if topic.table != "timeline" else f" (category={topic.id})"), "", _render_table_preview(rows, fields)]

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topics-dir", required=True, type=Path)
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--company", required=True)
    parser.add_argument("--domain", action="append", required=True, dest="domains")
    parser.add_argument("--as-of", required=True, help="e.g. 2026-09-10")
    args = parser.parse_args(argv)

    report_path = assemble(
        topics_dir=args.topics_dir,
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        company=args.company,
        domains=args.domains,
        as_of=args.as_of,
    )
    print(f"wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
