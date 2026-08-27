"""Internal records used by the compact 10-K semantic index."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class PreparedMarkdown:
    package_id: str
    package_directory: Path
    document_path: Path
    document_bytes: bytes
    lines: tuple[str, ...]
    artifact_sha256: str


@dataclass(frozen=True, slots=True)
class IndexBuildResult:
    index_directory: Path
    manifest: dict[str, Any]


class SemanticIndexError(ValueError):
    """Raised when a package or derived index is not safe to use."""
