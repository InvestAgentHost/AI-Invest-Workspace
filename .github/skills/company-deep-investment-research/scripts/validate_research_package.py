#!/usr/bin/env python3
"""Run portable mechanical checks over one company research package."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path


REQUIRED_FILES = (
    "research-context.md",
    "source-index.md",
    "evidence-ledger.md",
    "acquisition-attempt-log.md",
    "coverage-matrix.md",
    "validation-log.md",
    "release-review.md",
)
GATES = ("A1", "A2", "B1", "B2", "C1", "C2", "D1", "D2", "E1", "E2", "R1", "R2", "R3")
SOURCE_ID_RE = re.compile(r"\bS\d{3,}\b")
ABSOLUTE_PATH_RE = re.compile(r"(?:^|[\s`(])/(?:Users|home|private|var)/|[A-Za-z]:[\\/][^\s`)]*")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("research_root", type=Path)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--report", type=Path, help="Report path; defaults to the first top-level Markdown file not in the ledger list")
    parser.add_argument("--forbid-term", action="append", default=[], help="Case-insensitive term that must not occur in Markdown")
    parser.add_argument("--allow-absolute", action="store_true")
    parser.add_argument("--allow-pending", action="store_true", help="Do not fail when release-review gate markers are pending")
    return parser.parse_args()


def choose_report(root: Path, requested: Path | None) -> Path | None:
    if requested:
        return requested.resolve()
    excluded = set(REQUIRED_FILES) | {"research-context.md"}
    candidates = sorted(path for path in root.glob("*.md") if path.name not in excluded)
    return candidates[0] if candidates else None


def package_file(root: Path, name: str) -> Path | None:
    """Resolve package metadata from the root or the ignored company data folder."""
    for candidate in (root / name, root / "data" / name):
        if candidate.is_file():
            return candidate
    return None


def check_markdown(path: Path, errors: list[str], warnings: list[str], allow_absolute: bool) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        errors.append(f"{path}: not valid UTF-8 ({exc})")
        return ""
    if text.count("```") % 2:
        errors.append(f"{path}: unbalanced fenced code blocks")
    if not allow_absolute and ABSOLUTE_PATH_RE.search(text):
        warnings.append(f"{path}: absolute path detected; use a repository-relative path in tracked Markdown")
    return text


def parse_structured(data_root: Path, errors: list[str]) -> None:
    if not data_root.exists():
        return
    for path in sorted(data_root.rglob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: invalid JSON ({exc})")
    for path in sorted(data_root.rglob("*.csv")):
        try:
            with path.open(newline="", encoding="utf-8") as handle:
                list(csv.reader(handle))
        except (OSError, UnicodeDecodeError, csv.Error) as exc:
            errors.append(f"{path}: invalid CSV ({exc})")


def main() -> int:
    args = parse_args()
    root = args.research_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    if not root.is_dir():
        print(f"ERROR: research root is not a directory: {root}")
        return 1

    markdown: dict[Path, str] = {}
    for name in REQUIRED_FILES:
        path = package_file(root, name)
        if path is None:
            errors.append(f"missing required file: {root / name}")
        else:
            markdown[path] = check_markdown(path, errors, warnings, args.allow_absolute)

    report = choose_report(root, args.report)
    if report is None or not report.is_file():
        errors.append("no report Markdown found; pass --report explicitly")
    else:
        report_text = check_markdown(report, errors, warnings, args.allow_absolute)
        markdown[report] = report_text
        if len(re.findall(r"^# ", report_text, flags=re.MULTILINE)) != 1:
            errors.append(f"{report}: expected exactly one H1 heading")
        if len(re.findall(r"^## ", report_text, flags=re.MULTILINE)) < 3:
            warnings.append(f"{report}: fewer than three H2 chapters")

    index_path = package_file(root, "source-index.md")
    index_text = markdown.get(index_path, "") if index_path else ""
    indexed_ids = set(SOURCE_ID_RE.findall(index_text))
    cited_ids = set()
    for text in markdown.values():
        cited_ids.update(SOURCE_ID_RE.findall(text))
    missing_ids = sorted(cited_ids - indexed_ids)
    if missing_ids:
        errors.append(f"source IDs cited but absent from source-index.md: {', '.join(missing_ids)}")

    release_path = package_file(root, "release-review.md")
    release_text = markdown.get(release_path, "") if release_path else ""
    missing_gates = [gate for gate in GATES if gate not in release_text]
    if missing_gates and not args.allow_pending:
        errors.append(f"release-review.md missing gate markers: {', '.join(missing_gates)}")
    elif missing_gates:
        warnings.append(f"release-review.md pending gate markers: {', '.join(missing_gates)}")

    corpus = "\n".join(markdown.values())
    for term in args.forbid_term:
        if term and re.search(re.escape(term), corpus, flags=re.IGNORECASE):
            errors.append(f"forbidden term found in Markdown: {term}")

    parse_structured(args.data_root.resolve() if args.data_root else root / "data", errors)

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"PASS: research package checks passed ({len(markdown)} Markdown files, {len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
