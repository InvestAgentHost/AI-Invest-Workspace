#!/usr/bin/env python3
"""Initialize, check, or snapshot a company's local research checkpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, datetime, timezone
from graphlib import CycleError, TopologicalSorter
from pathlib import Path, PureWindowsPath
from uuid import uuid4


STATE = "data/research-state.json"
RESUME = "data/RESUME.md"
CHECKPOINTS = "data/checkpoints"
STATUSES = {"pending", "in_progress", "complete", "partial", "blocked", "not_applicable"}
READY = {"complete", "partial"}
CHAPTER_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SHA256 = re.compile(r"[0-9a-f]{64}")
RESUME_TEMPLATE = """# 研究恢复摘要

- 目标与交付：待填写。具体决定见 `data/research-context.md`。
- 范围与口径：待填写。资料截止日 {as_of}。
- 已完成：待填写。章节状态及依赖见 `data/research-state.json`。
- 当前章节与阻碍：待填写。
- 下一步：待填写可执行动作、所需证据和产物路径。
- 已确认的决定与未决问题：待填写决定或证据 ID、原始记录定位。
- 关键路径：列出现行底稿、草稿、来源索引及证据台账。
"""


def local_path(root: Path, value: str) -> Path:
    """Resolve a portable relative path without following a link outside root."""
    if (
        not isinstance(value, str)
        or "\\" in value
        or "\0" in value
        or any(part in {"", ".", ".."} for part in value.split("/"))
        or PureWindowsPath(value).drive
    ):
        raise ValueError(f"expected a company-relative path, got {value!r}")
    path = root / value
    if not path.resolve().is_relative_to(root):
        raise ValueError(f"path escapes the company root: {value}")
    return path


def file_path(root: Path, value: str) -> Path:
    path = local_path(root, value)
    if not path.is_file():
        raise ValueError(f"missing or not a file: {value}")
    return path


def iso_date(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("as_of must be YYYY-MM-DD")
    date.fromisoformat(value)
    return value


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def create_if_missing(path: Path, content: bytes) -> bool:
    try:
        with path.open("xb") as handle:
            handle.write(content)
    except FileExistsError:
        if not path.is_file():
            raise ValueError(f"expected a regular file: {path}") from None
        return False
    return True


def initialize(root: Path, as_of: str) -> None:
    as_of = iso_date(as_of)
    data = local_path(root, "data")
    state_path = local_path(root, STATE)
    resume_path = local_path(root, RESUME)
    data.mkdir(exist_ok=True)
    if state_path.is_file() and not resume_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        if not isinstance(state, dict):
            raise ValueError(f"{STATE} must contain an object")
        as_of = iso_date(state.get("as_of"))
    template = {
        "schema_version": 2,
        "as_of": as_of,
        "current_chapter": None,
        "references": [],
        "chapters": [],
    }
    state_created = create_if_missing(state_path, json_bytes(template))
    resume_created = create_if_missing(resume_path, RESUME_TEMPLATE.format(as_of=as_of).encode("utf-8"))
    for path, created in ((STATE, state_created), (RESUME, resume_created)):
        print(f"{'created' if created else 'preserved'} {path}")


def string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{label} must be a list of nonempty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{label} contains duplicates")
    return value


def reading_review(chapter: dict) -> dict | None:
    name = chapter["id"]
    kind = chapter.get("kind")
    if kind not in ("narrative", "data_only"):
        raise ValueError(f"{name}: schema_version 2 requires kind narrative or data_only")
    review = chapter.get("reading_review")
    if kind == "data_only" and review is not None:
        raise ValueError(f"{name}: data_only chapters do not carry a reading_review")
    if review is not None and (
        not isinstance(review, dict) or review.get("status") not in ("pass", "revise", "pending")
    ):
        raise ValueError(f"{name}: reading_review requires status pass, revise, or pending")
    passed = review is not None and review["status"] == "pass"
    if kind == "narrative" and chapter["status"] in READY and not passed:
        raise ValueError(f"{name}: complete/partial narrative chapter requires a passing reading_review")
    if review is None:
        return None
    record = review.get("record_path")
    if (passed or record is not None) and (not isinstance(record, str) or not record.strip()):
        raise ValueError(f"{name}: reading_review requires a company-relative record_path")
    if passed:
        revision = review.get("chapter_revision")
        if type(revision) is not int or revision < 1 or revision != chapter["revision"]:
            raise ValueError(f"{name}: reading_review chapter_revision must match the current revision")
        expected = review.get("draft_sha256")
        if not isinstance(expected, str) or not SHA256.fullmatch(expected):
            raise ValueError(f"{name}: reading_review draft_sha256 must be 64 lowercase hexadecimal characters")
        if chapter["draft"] is None:
            raise ValueError(f"{name}: passing reading_review requires a draft")
    return review


def validate_state(root: Path, raw: bytes, *, require_reading_review: bool = False) -> tuple[dict, dict[str, Path]]:
    state = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    required = {"schema_version", "as_of", "current_chapter", "references", "chapters"}
    if not isinstance(state, dict) or not required <= state.keys():
        raise ValueError(f"{STATE} requires: {', '.join(sorted(required))}")
    version = state["schema_version"]
    if type(version) is not int or version not in (1, 2):
        raise ValueError("schema_version must be 1 or 2")
    if version == 1 and require_reading_review:
        raise ValueError("schema_version 1 has no reading review validation; migrate to schema_version 2")
    cutoff = iso_date(state["as_of"])
    if not isinstance(state["chapters"], list):
        raise ValueError("chapters must be a list")

    paths = set(string_list(state["references"], "references"))
    by_id = {}
    reviews = []
    chapter_fields = {
        "id", "status", "revision", "as_of", "memo", "draft", "evidence_ids", "depends_on", "artifacts",
    }
    for chapter in state["chapters"]:
        if not isinstance(chapter, dict) or not chapter_fields <= chapter.keys():
            raise ValueError(f"each chapter requires: {', '.join(sorted(chapter_fields))}")
        name = chapter["id"]
        if not isinstance(name, str) or not CHAPTER_ID.fullmatch(name) or name in by_id:
            raise ValueError(f"chapter id must be unique and use lowercase ASCII letters, digits or hyphens: {name!r}")
        status = chapter["status"]
        if not isinstance(status, str) or status not in STATUSES:
            raise ValueError(f"{name}: unknown status {status!r}")
        revision = chapter["revision"]
        if type(revision) is not int or revision < 0 or (status in READY and revision == 0):
            raise ValueError(f"{name}: invalid revision (complete/partial chapters require a positive integer)")
        chapter_cutoff = chapter["as_of"]
        if chapter_cutoff is not None and iso_date(chapter_cutoff) > cutoff:
            raise ValueError(f"{name}: chapter as_of cannot be later than the research cutoff {cutoff}")
        if status in READY and chapter_cutoff != cutoff:
            raise ValueError(f"{name}: chapter as_of {chapter_cutoff!r} does not match research cutoff {cutoff}")
        for field in ("memo", "draft"):
            path = chapter[field]
            if path is None and status not in READY:
                continue
            if not isinstance(path, str) or not path:
                raise ValueError(f"{name}: {field} must point to an existing file for complete/partial chapters")
            paths.add(path)
        evidence = string_list(chapter["evidence_ids"], f"{name}.evidence_ids")
        if status in READY and not evidence:
            raise ValueError(f"{name}: record evidence IDs for complete/partial chapters")
        paths.update(string_list(chapter["artifacts"], f"{name}.artifacts"))
        if not isinstance(chapter["depends_on"], dict):
            raise ValueError(f"{name}.depends_on must map chapter IDs to recorded revisions")
        if version == 2:
            review = reading_review(chapter)
            if review is not None and review.get("record_path") is not None:
                paths.add(review["record_path"])
                reviews.append((chapter, review))
        by_id[name] = chapter

    current = state["current_chapter"]
    if current is not None and (not isinstance(current, str) or current not in by_id):
        raise ValueError(f"current_chapter must be null or a listed chapter ID: {current!r}")
    for name, chapter in by_id.items():
        for dependency, expected in chapter["depends_on"].items():
            if dependency not in by_id or type(expected) is not int or expected < 1:
                raise ValueError(f"{name}: invalid prerequisite {dependency!r} at revision {expected!r}")
            actual = by_id[dependency]
            if chapter["status"] in READY and (actual["status"] not in READY or actual["revision"] != expected):
                raise ValueError(
                    f"{name}: stale prerequisite {dependency} r{expected}; "
                    f"current is r{actual['revision']} ({actual['status']})"
                )
    try:
        tuple(TopologicalSorter({name: row["depends_on"] for name, row in by_id.items()}).static_order())
    except CycleError as exc:
        raise ValueError(f"cyclic chapter prerequisites: {exc.args[1]}") from exc

    files = {}
    for relative in sorted(paths):
        if relative in {STATE, RESUME} or relative == CHECKPOINTS or relative.startswith(CHECKPOINTS + "/"):
            raise ValueError(f"do not reference checkpoint metadata or snapshots as artifacts: {relative}")
        path = file_path(root, relative)
        if any(path.samefile(file_path(root, metadata)) for metadata in (STATE, RESUME)):
            raise ValueError(f"do not reference checkpoint metadata as artifacts: {relative}")
        checkpoint_root = local_path(root, CHECKPOINTS).resolve()
        if checkpoint_root.is_dir() and any(parent.samefile(checkpoint_root) for parent in path.resolve().parents):
            raise ValueError(f"do not reference snapshot files as artifacts: {relative}")
        files[relative] = path
    chapter_text = {files[row[field]] for row in by_id.values() for field in ("memo", "draft") if row[field] is not None}
    for chapter, review in reviews:
        name = chapter["id"]
        record = files[review["record_path"]]
        if any(record.samefile(path) for path in chapter_text):
            raise ValueError(f"{name}: reading review record must be separate from chapter drafts and memos")
        try:
            record_text = record.read_text(encoding="utf-8-sig")
        except UnicodeError as exc:
            raise ValueError(f"{name}: reading review record must be UTF-8") from exc
        if not record_text.strip():
            raise ValueError(f"{name}: reading review record is empty")
        if review["status"] == "pass" and sha256_file(files[chapter["draft"]]) != review["draft_sha256"]:
            raise ValueError(f"{name}: reading_review draft_sha256 does not match the current draft")
    return state, files


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def read_checkpoint(
    root: Path, *, require_reading_review: bool = False
) -> tuple[bytes, bytes, dict, dict[str, Path]]:
    raw_state = file_path(root, STATE).read_bytes()
    resume = file_path(root, RESUME).read_bytes()
    if not resume.decode("utf-8").strip():
        raise ValueError(f"{RESUME} is empty")
    state, files = validate_state(root, raw_state, require_reading_review=require_reading_review)
    return raw_state, resume, state, files


def snapshot(root: Path, raw_state: bytes, resume: bytes, files: dict[str, Path]) -> Path:
    started = datetime.now(timezone.utc)
    snapshot_files = {STATE: raw_state, RESUME: resume}
    hashes = {relative: hashlib.sha256(payload).hexdigest() for relative, payload in snapshot_files.items()}
    hashes.update((relative, sha256_file(path)) for relative, path in files.items())
    container = local_path(root, CHECKPOINTS)
    container.mkdir(exist_ok=True)
    directory = container / f"{started:%Y%m%dT%H%M%SZ}-{uuid4().hex[:12]}"
    directory.mkdir()
    for relative, data in snapshot_files.items():
        with (directory / Path(relative).name).open("xb") as handle:
            handle.write(data)
    manifest = {"created_at_utc": started.isoformat(), "sha256": hashes}
    with (directory / "manifest.json").open("xb") as handle:
        handle.write(json_bytes(manifest))
    return directory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("init", "create missing state and summary templates without overwriting"),
        ("check", "check schema, prerequisite revisions, local files and reading review records"),
        ("snapshot", "copy state and summary, and hash current local references"),
    ):
        subparser = commands.add_parser(command, help=help_text)
        subparser.add_argument("--company-root", required=True, type=Path)
        if command == "init":
            subparser.add_argument("--as-of", required=True, metavar="YYYY-MM-DD")
        else:
            subparser.add_argument(
                "--require-reading-review",
                action="store_true",
                help="reject legacy schema_version 1, which does not validate reading reviews",
            )
    args = parser.parse_args()
    try:
        root = args.company_root.resolve(strict=True)
        if not root.is_dir():
            raise ValueError(f"company root must be a directory: {root}")
        if args.command == "init":
            initialize(root, args.as_of)
        else:
            raw, resume, state, files = read_checkpoint(root, require_reading_review=args.require_reading_review)
            if state["schema_version"] == 1:
                print("research_checkpoint: legacy schema_version 1; reading reviews were not validated", file=sys.stderr)
            if args.command == "check":
                print(f"OK: {len(state['chapters'])} chapter(s), {len(files)} local reference(s), as of {state['as_of']}")
            else:
                print(snapshot(root, raw, resume, files).relative_to(root))
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"research_checkpoint: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
