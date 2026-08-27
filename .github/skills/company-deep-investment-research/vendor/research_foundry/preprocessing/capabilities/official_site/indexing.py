"""Compact multi-document lexical index and exact source reader."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

from research_foundry.preprocessing.capabilities.ten_k.indexing.parser import parse_markdown

from .models import SourceRecord


class OfficialSiteIndexError(ValueError):
    """Raised when a website index or requested source is invalid."""


def build_official_site_index(snapshot_directory: str | Path, sources: list[SourceRecord], *, max_chunk_chars: int = 8_000) -> dict[str, Any]:
    root = Path(snapshot_directory).resolve()
    index = root / "index"
    index.mkdir(parents=True, exist_ok=False)
    combined: dict[str, list[dict[str, Any]]] = {"sections": [], "chunks": [], "tables": []}
    documents: list[dict[str, Any]] = []
    for source in sources:
        if not source.prepared_ref:
            continue
        path = _safe_ref(root, source.prepared_ref)
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != source.prepared_sha256:
            raise OfficialSiteIndexError(f"prepared source hash mismatch: {source.alias}")
        records = parse_markdown(content, max_chunk_chars=max_chunk_chars)
        for kind, values in records.items():
            for value in values:
                value = {"source_id": source.source_id, "source_alias": source.alias, "prepared_ref": source.prepared_ref, **value}
                combined[kind].append(value)
        documents.append(
            {
                "source_id": source.source_id,
                "source_alias": source.alias,
                "prepared_ref": source.prepared_ref,
                "sha256": source.prepared_sha256,
                "line_count": source.prepared_line_count,
                "title": source.title,
                "url": source.final_url,
            }
        )
    for kind, values in combined.items():
        path = index / f"{kind}.jsonl"
        path.write_text(
            "".join(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for value in values),
            encoding="utf-8",
        )
    manifest = {
        "schema_version": "research_foundry_official_site_index.v1",
        "max_chunk_chars": max_chunk_chars,
        "counts": {key: len(values) for key, values in combined.items()},
        "documents": documents,
        "files": {
            key: {
                "artifact_ref": f"{key}.jsonl",
                "sha256": hashlib.sha256((index / f"{key}.jsonl").read_bytes()).hexdigest(),
                "row_count": len(values),
            }
            for key, values in combined.items()
        },
    }
    (index / "index_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def search_official_site_index(index_directory: str | Path, query: str, *, limit: int = 20, kind: str = "all") -> list[dict[str, Any]]:
    root = Path(index_directory).expanduser().resolve()
    manifest = _manifest(root)
    if limit < 1:
        raise OfficialSiteIndexError("limit must be positive")
    if kind not in {"all", "chunks", "tables", "sections"}:
        raise OfficialSiteIndexError("kind must be all, chunks, tables, or sections")
    terms = [term.casefold() for term in re.findall(r"\w+", query) if term.strip()]
    if not terms:
        raise OfficialSiteIndexError("query must contain searchable text")
    matches: list[dict[str, Any]] = []
    kinds = ("chunks", "tables", "sections") if kind == "all" else (kind,)
    for record_kind in kinds:
        for record in _read_jsonl(root / f"{record_kind}.jsonl"):
            haystack = json.dumps(record, ensure_ascii=False).casefold()
            score = sum(haystack.count(term) for term in terms)
            if score:
                matches.append({"kind": record_kind[:-1], "score": score, "record": record})
    matches.sort(
        key=lambda value: (
            -value["score"],
            value["record"].get("source_alias", ""),
            value["record"].get("start_line", 0),
            value["kind"],
        )
    )
    return [{"schema_version": manifest["schema_version"], **value} for value in matches[:limit]]


def read_official_site_lines(snapshot_directory: str | Path, source: str, start_line: int, end_line: int) -> dict[str, Any]:
    root = Path(snapshot_directory).expanduser().resolve()
    records = [SourceRecord.model_validate(value) for value in _read_jsonl(root / "sources.jsonl")]
    matches = [record for record in records if source in {record.source_id, record.alias}]
    if len(matches) != 1 or not matches[0].prepared_ref:
        raise OfficialSiteIndexError("source does not identify one prepared document")
    record = matches[0]
    path = _safe_ref(root, record.prepared_ref)
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != record.prepared_sha256:
        raise OfficialSiteIndexError("prepared source hash mismatch")
    lines = content.decode("utf-8").splitlines()
    if start_line < 1 or end_line < start_line or end_line > len(lines):
        raise OfficialSiteIndexError("requested line range is outside the prepared source")
    return {
        "source_id": record.source_id,
        "source_alias": record.alias,
        "sha256": record.prepared_sha256,
        "start_line": start_line,
        "end_line": end_line,
        "citation": f"[{record.alias}:L{start_line}-L{end_line}]",
        "text": "\n".join(lines[start_line - 1 : end_line]),
    }


def _manifest(root: Path) -> dict[str, Any]:
    try:
        value = json.loads((root / "index_manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise OfficialSiteIndexError(f"invalid official-site index: {root}") from error
    if value.get("schema_version") != "research_foundry_official_site_index.v1":
        raise OfficialSiteIndexError("unsupported official-site index schema")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, ValueError) as error:
        raise OfficialSiteIndexError(f"invalid JSONL: {path}") from error


def _safe_ref(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    if root not in path.parents or not path.is_file():
        raise OfficialSiteIndexError(f"unsafe or missing artifact reference: {value}")
    return path
