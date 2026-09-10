#!/usr/bin/env python3
"""Read-only coverage summary for Phase 3 — advisory, not a gate.

Prints, per topic: how many fetched pages guessed into it, whether a draft
file exists yet (and its declared `coverage_status`), and how many unvisited
candidate URLs in `urls.json` still guess into it. The Agent uses this to
decide whether to keep reading pages or move on — nothing here blocks
Phase 4/5 the way the old engine's coverage-review gate did.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import topics  # noqa: E402
import yaml  # noqa: E402


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _load_urls(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _draft_status(topics_dir: Path, topic_id: str) -> str:
    draft_path = topics_dir / f"{topic_id}.md"
    if not draft_path.exists():
        return "no draft"
    text = draft_path.read_text(encoding="utf-8")
    if text.startswith("---"):
        _, frontmatter, _ = text.split("---", 2)
        data = yaml.safe_load(frontmatter) or {}
        return str(data.get("coverage_status", "unknown"))
    return "unknown (no frontmatter)"


def summarize(workspace: Path, topics_dir: Path) -> list[dict]:
    pages = _read_jsonl(workspace / "pages.jsonl")
    urls = _load_urls(workspace / "urls.json")

    rows = []
    for topic in topics.TOPICS:
        visited = sum(1 for record in pages if record.get("topic_guess") == topic.id)
        remaining = sum(1 for entry in urls if entry.get("topic_guess") == topic.id and entry.get("status") == "unvisited")
        rows.append(
            {
                "topic_id": topic.id,
                "pages_visited": visited,
                "draft_status": _draft_status(topics_dir, topic.id),
                "unvisited_candidates": remaining,
            }
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--topics-dir", required=True, type=Path)
    args = parser.parse_args(argv)

    rows = summarize(args.workspace, args.topics_dir)
    header = f"{'topic':<28} {'pages':>6} {'draft status':<24} {'unvisited':>10}"
    print(header)
    print("-" * len(header))
    for row in rows:
        print(f"{row['topic_id']:<28} {row['pages_visited']:>6} {row['draft_status']:<24} {row['unvisited_candidates']:>10}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
