#!/usr/bin/env python3
"""Normalize Gangtise SKILL.md frontmatter for Codex compatibility."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
from typing import Any

import yaml


MOVABLE_KEYS = ("version", "author")
TOP_LEVEL_PATTERN = re.compile(r"^(version|author):(.*)$")
METADATA_PATTERN = re.compile(r"^metadata:\s*(?:#.*)?$")


def _parse_frontmatter(path: Path, text: str) -> tuple[list[str], int, dict[str, Any]]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path}: missing opening YAML frontmatter delimiter")

    try:
        end_index = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as exc:
        raise ValueError(f"{path}: missing closing YAML frontmatter delimiter") from exc

    frontmatter = yaml.safe_load("".join(lines[1:end_index]))
    if not isinstance(frontmatter, dict):
        raise ValueError(f"{path}: YAML frontmatter must be a mapping")
    return lines, end_index, frontmatter


def _normalized_text(path: Path, text: str) -> tuple[str, bool]:
    lines, end_index, parsed = _parse_frontmatter(path, text)
    movable = {key: parsed[key] for key in MOVABLE_KEYS if key in parsed}
    if not movable:
        return text, False

    metadata = parsed.get("metadata")
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise ValueError(f"{path}: metadata must be a mapping")

    for key, value in movable.items():
        if key in metadata and metadata[key] != value:
            raise ValueError(f"{path}: conflicting top-level and metadata values for {key}")

    front_lines = lines[1:end_index]
    retained: list[str] = []
    raw_values: dict[str, str] = {}
    for line in front_lines:
        match = TOP_LEVEL_PATTERN.match(line.rstrip("\r\n"))
        if match and match.group(1) in movable:
            key = match.group(1)
            if key in raw_values:
                raise ValueError(f"{path}: duplicate top-level {key} field")
            raw_values[key] = match.group(2)
            continue
        retained.append(line)

    if set(raw_values) != set(movable):
        raise ValueError(f"{path}: movable fields use an unsupported YAML layout")

    metadata_index = next(
        (index for index, line in enumerate(retained) if METADATA_PATTERN.match(line.rstrip("\r\n"))),
        None,
    )
    newline = "\r\n" if "\r\n" in text else "\n"
    if metadata_index is None:
        retained.append(f"metadata:{newline}")
        metadata_index = len(retained) - 1

    moved_lines = [f"  {key}:{raw_values[key]}{newline}" for key in MOVABLE_KEYS if key in raw_values]
    retained[metadata_index + 1 : metadata_index + 1] = moved_lines

    normalized = "".join([lines[0], *retained, *lines[end_index:]])

    expected = dict(parsed)
    expected_metadata = dict(metadata)
    for key in MOVABLE_KEYS:
        if key in expected:
            expected_metadata[key] = expected.pop(key)
    expected["metadata"] = expected_metadata
    _, _, reparsed = _parse_frontmatter(path, normalized)
    if reparsed != expected:
        raise ValueError(f"{path}: normalized YAML does not preserve frontmatter semantics")

    return normalized, True


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Move Gangtise version/author fields into metadata without changing skill bodies."
    )
    parser.add_argument(
        "--skills-root",
        type=Path,
        default=Path(".github/skills"),
        help="Directory containing gangtise-* skill folders.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report files requiring normalization without modifying them.",
    )
    args = parser.parse_args()

    skill_files = sorted(args.skills_root.glob("gangtise-*/SKILL.md"))
    if not skill_files:
        print(f"No Gangtise SKILL.md files found under {args.skills_root}", file=sys.stderr)
        return 2

    changed: list[Path] = []
    try:
        for path in skill_files:
            original = path.read_text(encoding="utf-8")
            normalized, needs_change = _normalized_text(path, original)
            if not needs_change:
                continue
            changed.append(path)
            if not args.check:
                path.write_text(normalized, encoding="utf-8")
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(exc, file=sys.stderr)
        return 2

    if args.check:
        for path in changed:
            print(f"needs normalization: {_display_path(path)}")
        return 1 if changed else 0

    for path in changed:
        print(f"normalized: {_display_path(path)}")
    print(f"Gangtise skills checked: {len(skill_files)}; normalized: {len(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
