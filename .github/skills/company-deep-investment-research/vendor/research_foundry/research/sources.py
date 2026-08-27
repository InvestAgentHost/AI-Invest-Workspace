"""Freeze Agent-acquired external material into one research workspace."""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import tempfile

from research_foundry.runtime.artifacts import hash_file, publish_bytes

from .contracts import PublishedArtifact, ResearchSourceManifest, ResearchSourceMetadata


class ResearchSourceError(ValueError):
    """Raised when an external research source cannot be frozen safely."""


def load_source_metadata(path: str | Path) -> ResearchSourceMetadata:
    """Load Agent-authored source provenance metadata."""

    source = Path(path).expanduser()
    if source.is_symlink() or not source.is_file():
        raise ResearchSourceError("source metadata must be a regular file")
    try:
        return ResearchSourceMetadata.model_validate_json(source.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ResearchSourceError(f"invalid source metadata: {error}") from error


def capture_research_source(
    research_root: str | Path,
    metadata: ResearchSourceMetadata,
    *,
    source_path: str | Path,
    workspace_root: str | Path,
    prepared_path: str | Path | None = None,
) -> ResearchSourceManifest:
    """Copy one raw source and optional citation-ready Markdown into a run."""

    root_input = Path(research_root).expanduser()
    if root_input.is_symlink():
        raise ResearchSourceError(
            "research root must be an initialized run below workspace root"
        )
    root = root_input.resolve()
    workspace = Path(workspace_root).expanduser().resolve()
    initialized = (root / "research_brief.yaml").is_file() or (
        root / "task.md"
    ).is_file()
    if not _is_below(root, workspace) or not initialized:
        raise ResearchSourceError("research root must be an initialized run below workspace root")
    if (root / "release_manifest.json").exists():
        raise ResearchSourceError("published research cannot accept new sources")

    source = _regular_input(source_path, "raw source")
    prepared = _regular_input(prepared_path, "prepared source") if prepared_path else None
    if prepared is not None:
        try:
            text = prepared.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise ResearchSourceError(f"prepared source must be readable UTF-8 text: {error}") from error
        if len(re.sub(r"\s+", "", text)) < 40:
            raise ResearchSourceError("prepared source is not substantive")

    source_dir = root / "sources" / metadata.source_id
    suffix = _portable_suffix(source.suffix)
    raw_destination = source_dir / "raw" / f"source{suffix}"
    prepared_destination = source_dir / "source.md" if prepared is not None else None
    manifest_path = source_dir / "source_manifest.json"

    raw_identity = hash_file(source)
    prepared_identity = hash_file(prepared) if prepared is not None else None
    expected = ResearchSourceManifest(
        source_id=metadata.source_id,
        title=metadata.title,
        publisher=metadata.publisher,
        source_type=metadata.source_type,
        source_url=metadata.source_url,
        published_at=metadata.published_at,
        retrieved_at=metadata.retrieved_at,
        acquisition_method=metadata.acquisition_method,
        content_status="evidence_ready" if prepared is not None else "raw_only",
        raw_artifact=PublishedArtifact(
            artifact_ref=raw_destination.relative_to(workspace).as_posix(),
            sha256=raw_identity.sha256,
            byte_size=raw_identity.byte_size,
        ),
        prepared_artifact=(
            PublishedArtifact(
                artifact_ref=prepared_destination.relative_to(workspace).as_posix(),
                sha256=prepared_identity.sha256,
                byte_size=prepared_identity.byte_size,
            )
            if prepared_destination is not None and prepared_identity is not None
            else None
        ),
        notes=metadata.notes,
    )

    if manifest_path.exists():
        existing = verify_research_source_manifest(manifest_path, workspace_root=workspace)
        if existing != expected:
            raise ResearchSourceError("source_id already contains different metadata or content")
        return existing
    if source_dir.exists():
        raise ResearchSourceError("source directory exists without a valid manifest")

    raw_destination.parent.mkdir(parents=True)
    _copy_atomically(source, raw_destination)
    if prepared is not None and prepared_destination is not None:
        _copy_atomically(prepared, prepared_destination)
    rendered = expected.model_dump_json(indent=2, exclude_none=True) + "\n"
    publish_bytes(rendered.encode("utf-8"), manifest_path)
    return verify_research_source_manifest(manifest_path, workspace_root=workspace)


def verify_research_source_manifest(
    manifest_path: str | Path,
    *,
    workspace_root: str | Path,
) -> ResearchSourceManifest:
    """Verify one source manifest and every artifact identity it records."""

    path = Path(manifest_path).expanduser().resolve()
    workspace = Path(workspace_root).expanduser().resolve()
    if not _is_below(path, workspace) or path.is_symlink() or not path.is_file():
        raise ResearchSourceError("source manifest must be a regular file below workspace root")
    try:
        manifest = ResearchSourceManifest.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ResearchSourceError(f"invalid source manifest: {error}") from error
    for artifact in (manifest.raw_artifact, manifest.prepared_artifact):
        if artifact is None:
            continue
        artifact_path = (workspace / artifact.artifact_ref).resolve()
        if not _is_below(artifact_path, workspace) or artifact_path.is_symlink() or not artifact_path.is_file():
            raise ResearchSourceError(f"unsafe or missing source artifact: {artifact.artifact_ref}")
        identity = hash_file(artifact_path)
        if identity.sha256 != artifact.sha256 or identity.byte_size != artifact.byte_size:
            raise ResearchSourceError(f"source artifact identity mismatch: {artifact.artifact_ref}")
    return manifest


def _regular_input(path: str | Path, label: str) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_symlink() or not candidate.is_file():
        raise ResearchSourceError(f"{label} must be a regular file")
    return candidate.resolve()


def _portable_suffix(value: str) -> str:
    suffix = value.lower()
    return suffix if re.fullmatch(r"\.[a-z0-9]{1,10}", suffix) else ".bin"


def _copy_atomically(source: Path, destination: Path) -> None:
    with source.open("rb") as input_handle, tempfile.NamedTemporaryFile(
        mode="wb", dir=destination.parent, prefix=f".{destination.name}.", delete=False
    ) as output_handle:
        temporary = Path(output_handle.name)
        shutil.copyfileobj(input_handle, output_handle)
        output_handle.flush()
        os.fsync(output_handle.fileno())
    try:
        os.replace(temporary, destination)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise


def _is_below(path: Path, root: Path) -> bool:
    return path != root and root in path.parents
