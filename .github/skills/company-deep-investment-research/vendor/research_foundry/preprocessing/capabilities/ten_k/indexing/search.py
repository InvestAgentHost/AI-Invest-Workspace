"""Read-only Agent tools for lexical search and exact Markdown retrieval."""

import json
from pathlib import Path
import re
from typing import Any

from .citation import resolve_locator
from .models import SemanticIndexError


def search_index(index_directory: str | Path, query: str, *, limit: int = 20, kind: str = "all") -> list[dict[str, Any]]:
    root = Path(index_directory).expanduser().resolve()
    if limit < 1:
        raise SemanticIndexError("limit must be positive")
    if kind not in {"all", "chunks", "tables", "sections"}:
        raise SemanticIndexError("kind must be all, chunks, tables, or sections")
    manifest = _load_manifest(root)
    terms = [term.casefold() for term in re.findall(r"\w+", query) if term.strip()]
    if not terms:
        raise SemanticIndexError("query must contain at least one searchable term")
    matches: list[dict[str, Any]] = []
    kinds = ("chunks", "tables", "sections") if kind == "all" else (kind,)
    for record_kind in kinds:
        for record in _read_jsonl(root / f"{record_kind}.jsonl"):
            haystack = json.dumps(record, ensure_ascii=False).casefold()
            score = sum(haystack.count(term) for term in terms)
            if score:
                matches.append({"kind": record_kind[:-1], "score": score, "record": record})
    matches.sort(key=lambda value: (-value["score"], value["kind"], value["record"].get("start_line", 0), value["record"].get("section_id", "")))
    return [{"package_id": manifest["package_id"], **match} for match in matches[:limit]]


def read_markdown_lines(package_directory: str | Path, start_line: int, end_line: int) -> dict[str, Any]:
    from .materialize import load_prepared_markdown
    prepared = load_prepared_markdown(package_directory)
    locator = {"schema_version": "markdown_line_locator.v1", "artifact_sha256": prepared.artifact_sha256, "start_line": start_line, "end_line": end_line}
    try:
        text = resolve_locator(prepared.document_bytes, locator)
    except (ValueError, TypeError) as error:
        raise SemanticIndexError(str(error)) from error
    return {"package_id": prepared.package_id, "artifact_sha256": prepared.artifact_sha256, "locator": locator, "text": text}


def _load_manifest(root: Path) -> dict[str, Any]:
    try:
        manifest = json.loads((root / "index_manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise SemanticIndexError(f"invalid index manifest: {root}") from error
    if manifest.get("schema_version") != "research_foundry_ten_k_index.v1":
        raise SemanticIndexError("unsupported index schema")
    return manifest


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, ValueError) as error:
        raise SemanticIndexError(f"invalid index records: {path}") from error
