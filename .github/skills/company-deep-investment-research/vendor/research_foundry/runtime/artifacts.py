"""Content hashing and immutable atomic artifact publication."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import tempfile


DEFAULT_CHUNK_SIZE = 1024 * 1024


class ArtifactAlreadyExistsError(FileExistsError):
    """Raised when an immutable artifact destination is already published."""


@dataclass(frozen=True, slots=True)
class ContentIdentity:
    """Identity derived only from an artifact's bytes."""

    sha256: str
    byte_size: int


def hash_file(path: Path | str, *, chunk_size: int = DEFAULT_CHUNK_SIZE) -> ContentIdentity:
    """Calculate a file's SHA-256 and size without loading it into memory."""

    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")

    digest = hashlib.sha256()
    byte_size = 0
    with Path(path).open("rb") as source:
        while chunk := source.read(chunk_size):
            digest.update(chunk)
            byte_size += len(chunk)
    return ContentIdentity(sha256=digest.hexdigest(), byte_size=byte_size)


def publish_file(
    source: Path | str,
    destination: Path | str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    validator: Callable[[Path], None] | None = None,
) -> ContentIdentity:
    """Validate and copy a file to a new immutable destination atomically."""

    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")

    source_path = Path(source)

    def chunks() -> Iterable[bytes]:
        with source_path.open("rb") as source_file:
            while chunk := source_file.read(chunk_size):
                yield chunk

    return _publish_chunks(chunks(), Path(destination), validator=validator)


def publish_bytes(data: bytes, destination: Path | str) -> ContentIdentity:
    """Publish bytes to a new immutable destination atomically."""

    return _publish_chunks((data,), Path(destination))


def publish_directory(staging: Path | str, destination: Path | str) -> None:
    """Atomically publish a complete staging directory without overwriting."""

    staging_path = Path(staging)
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    if destination_path.exists():
        raise ArtifactAlreadyExistsError(str(destination_path))
    try:
        staging_path.rename(destination_path)
    except FileExistsError as error:
        raise ArtifactAlreadyExistsError(str(destination_path)) from error
    _fsync_directory(destination_path.parent)


def _publish_chunks(
    chunks: Iterable[bytes],
    destination: Path,
    *,
    validator: Callable[[Path], None] | None = None,
) -> ContentIdentity:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise ArtifactAlreadyExistsError(str(destination))

    digest = hashlib.sha256()
    byte_size = 0
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="xb",
            prefix=f".{destination.name}.",
            # Keep the source media suffix so validators such as PyMuPDF can
            # infer the format from the staged path.
            suffix=destination.suffix or ".tmp",
            dir=destination.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            for chunk in chunks:
                temporary_file.write(chunk)
                digest.update(chunk)
                byte_size += len(chunk)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        if validator is not None:
            validator(temporary_path)

        try:
            os.link(temporary_path, destination)
        except FileExistsError as error:
            raise ArtifactAlreadyExistsError(str(destination)) from error

        _fsync_directory(destination.parent)
        return ContentIdentity(sha256=digest.hexdigest(), byte_size=byte_size)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
