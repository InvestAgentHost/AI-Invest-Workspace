"""Verify a Prepared package and publish a compact deterministic index beside it."""

import json
from pathlib import Path
import tempfile
from typing import Any

from research_foundry.preprocessing.capabilities.ten_k.prepared_markdown import (
    validate_prepared_markdown,
)
from research_foundry.preprocessing.verification import verify_ten_k_sec_html_package
from research_foundry.runtime.artifacts import ArtifactAlreadyExistsError, publish_directory

from .models import IndexBuildResult, PreparedMarkdown, SemanticIndexError
from .parser import parse_markdown


def load_prepared_markdown(package_directory: str | Path) -> PreparedMarkdown:
    root = Path(package_directory).expanduser().resolve()
    try:
        package_payload = json.loads((root / "prepared_source_package.json").read_text(encoding="utf-8"))
        pipeline = package_payload.get("source", {}).get("stage1_pipeline")
    except (OSError, ValueError) as error:
        raise SemanticIndexError(f"unable to identify Prepared package: {root}") from error
    if pipeline == "10k_sec_html_v1":
        package = verify_ten_k_sec_html_package(root)
    else:
        raise SemanticIndexError(f"unsupported Prepared package pipeline: {pipeline!r}")
    output = next(item for item in package.prepared_outputs if item.role == "document")
    document_path = (root / output.artifact_ref).resolve()
    document_bytes = document_path.read_bytes()
    validate_prepared_markdown(document_bytes)
    lines = tuple(document_bytes.decode("utf-8")[:-1].split("\n"))
    return PreparedMarkdown(package.prepared_source_package_id, root, document_path, document_bytes, lines, output.sha256)


def materialize_index(package_directory: str | Path, *, output_root: str | Path | None = None, max_chunk_chars: int = 8_000) -> IndexBuildResult:
    prepared = load_prepared_markdown(package_directory)
    records = parse_markdown(prepared.document_bytes, max_chunk_chars=max_chunk_chars)
    destination = Path(output_root).expanduser().resolve() if output_root else prepared.package_directory.parent / "index"
    manifest = {
        "schema_version": "research_foundry_ten_k_index.v1",
        "package_id": prepared.package_id,
        "document_ref": str(prepared.document_path.relative_to(prepared.package_directory)),
        "artifact_sha256": prepared.artifact_sha256,
        "line_count": len(prepared.lines),
        "max_chunk_chars": max_chunk_chars,
        "counts": {key: len(value) for key, value in records.items()},
        "files": {key: f"{key}.jsonl" for key in records},
    }
    if destination.exists():
        existing_path = destination / "index_manifest.json"
        try:
            existing = json.loads(existing_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise SemanticIndexError(f"existing index is unreadable: {destination}") from error
        for key in ("schema_version", "package_id", "artifact_sha256", "max_chunk_chars", "counts"):
            if existing.get(key) != manifest[key]:
                raise SemanticIndexError(f"existing index does not match requested package: {destination}")
        return IndexBuildResult(destination, existing)

    parent = destination.parent
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{destination.name}.", dir=parent) as temporary:
        staging = Path(temporary)
        for key, values in records.items():
            (staging / f"{key}.jsonl").write_text(
                "".join(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for value in values),
                encoding="utf-8",
            )
        (staging / "index_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        try:
            publish_directory(staging, destination)
        except ArtifactAlreadyExistsError:
            return materialize_index(prepared.package_directory, output_root=destination, max_chunk_chars=max_chunk_chars)
    return IndexBuildResult(destination, manifest)
