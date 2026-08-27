"""Deterministic binding of semantic claim drafts to workspace evidence."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import json
import os
import re
import tempfile
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError

from research_foundry.runtime.artifacts import hash_file, publish_bytes

from .contracts import EvidenceRef, ResearchClaim


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ResearchEvidenceBindingError(ValueError):
    """Raised when a semantic claim draft cannot be bound safely."""


class EvidenceLocatorDraft(BaseModel):
    """Semantic evidence locator before content identity is attached."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    artifact_ref: NonEmptyStr
    start_line: Annotated[int, Field(ge=1)]
    end_line: Annotated[int, Field(ge=1)]

    @property
    def line_range(self) -> tuple[int, int]:
        if self.end_line < self.start_line:
            raise ResearchEvidenceBindingError(
                "end_line must be greater than or equal to start_line"
            )
        return self.start_line, self.end_line


class ResearchClaimDraft(BaseModel):
    """Small semantic handoff accepted before deterministic evidence binding."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    claim_id: Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[A-Za-z][A-Za-z0-9_-]{2,95}$")]
    statement: NonEmptyStr
    claim_type: Literal["fact", "calculation", "interpretation", "forecast"]
    evidence: Annotated[tuple[EvidenceLocatorDraft, ...], Field(min_length=1)]
    period: NonEmptyStr | None = None
    unit: NonEmptyStr | None = None
    perimeter: NonEmptyStr | None = None
    counterevidence: tuple[EvidenceLocatorDraft, ...] = ()
    confidence: Literal["high", "medium", "low"]


def bind_claim_drafts(
    draft_path: str | Path,
    *,
    workspace_root: str | Path,
    output_path: str | Path | None = None,
) -> tuple[ResearchClaim, ...]:
    """Bind claim evidence to hashes and write canonical ResearchClaim JSONL.

    The draft and output may be the same path, allowing an Agent to write a
    semantic ``claims.jsonl`` draft and have this primitive finalize it in place.
    Existing published destinations are never overwritten.
    """

    draft_input = Path(draft_path).expanduser()
    output_input = Path(output_path or draft_path).expanduser()
    if draft_input.is_symlink():
        raise ResearchEvidenceBindingError("claim draft cannot be a symlink")
    if output_input.is_symlink():
        raise ResearchEvidenceBindingError("claim output cannot be a symlink")
    draft = draft_input.resolve()
    workspace = Path(workspace_root).expanduser().resolve()
    destination = output_input.resolve()
    if not draft.is_file():
        raise ResearchEvidenceBindingError("claim draft must be a regular file")
    if not _is_below(draft, workspace):
        raise ResearchEvidenceBindingError("claim draft must stay below workspace root")
    if not _is_below(destination, workspace):
        raise ResearchEvidenceBindingError("claim output must stay below workspace root")
    if destination.name == "release_manifest.json":
        raise ResearchEvidenceBindingError("release manifest cannot be overwritten")
    same_path = draft == destination
    if destination.exists() and not same_path:
        raise ResearchEvidenceBindingError(f"claim output already exists: {destination}")

    try:
        lines = draft.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise ResearchEvidenceBindingError(f"unable to read claim draft: {error}") from error

    drafts: list[ResearchClaimDraft] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            drafts.append(ResearchClaimDraft.model_validate_json(line))
        except ValidationError as error:
            raise ResearchEvidenceBindingError(
                f"invalid claim draft line {line_number}: {error}"
            ) from error

    if not drafts:
        raise ResearchEvidenceBindingError("claim draft contains no claims")
    claim_ids = [draft.claim_id for draft in drafts]
    if len(claim_ids) != len(set(claim_ids)):
        raise ResearchEvidenceBindingError("claim draft contains duplicate claim_id")

    identity_cache: dict[Path, tuple[str, int]] = {}
    bound_claims: list[ResearchClaim] = []
    for draft_claim in sorted(drafts, key=lambda item: item.claim_id):
        try:
            bound_claims.append(
                ResearchClaim(
                    claim_id=draft_claim.claim_id,
                    statement=draft_claim.statement,
                    claim_type=draft_claim.claim_type,
                    evidence=tuple(
                        bind_evidence_locator(locator, workspace, identity_cache)
                        for locator in draft_claim.evidence
                    ),
                    period=draft_claim.period,
                    unit=draft_claim.unit,
                    perimeter=draft_claim.perimeter,
                    counterevidence=tuple(
                        bind_evidence_locator(locator, workspace, identity_cache)
                        for locator in draft_claim.counterevidence
                    ),
                    confidence=draft_claim.confidence,
                )
            )
        except ValidationError as error:
            raise ResearchEvidenceBindingError(
                f"invalid bound claim {draft_claim.claim_id}: {error}"
            ) from error
    claims = tuple(bound_claims)
    rendered = "".join(
        json.dumps(claim.model_dump(mode="json", exclude_none=True), ensure_ascii=False, sort_keys=True)
        + "\n"
        for claim in claims
    ).encode("utf-8")

    destination.parent.mkdir(parents=True, exist_ok=True)
    if same_path:
        _replace_atomically(rendered, destination)
    else:
        publish_bytes(rendered, destination)
    return claims


def bind_evidence_locator(
    locator: EvidenceLocatorDraft,
    workspace: Path,
    identity_cache: dict[Path, tuple[str, int]],
) -> EvidenceRef:
    start_line, end_line = locator.line_range
    artifact_ref = locator.artifact_ref
    if "\\" in artifact_ref or re.match(r"^[A-Za-z]:", artifact_ref):
        raise ResearchEvidenceBindingError(
            f"evidence path must be a workspace-relative POSIX path: {artifact_ref}"
        )
    relative = PurePosixPath(artifact_ref)
    if relative.is_absolute() or not relative.parts or any(
        part in {"", ".", ".."} for part in relative.parts
    ):
        raise ResearchEvidenceBindingError(
            f"evidence path must stay below workspace root: {artifact_ref}"
        )
    raw_path = workspace / Path(*relative.parts)
    if _contains_symlink(raw_path, workspace):
        raise ResearchEvidenceBindingError(f"evidence cannot use a symlink: {artifact_ref}")
    path = raw_path.resolve()
    if not _is_below(path, workspace) or not path.is_file():
        raise ResearchEvidenceBindingError(f"unsafe or missing evidence: {artifact_ref}")
    if path not in identity_cache:
        try:
            line_count = len(path.read_text(encoding="utf-8").splitlines())
        except (OSError, UnicodeDecodeError) as error:
            raise ResearchEvidenceBindingError(
                f"evidence is not readable UTF-8 text: {artifact_ref}: {error}"
            ) from error
        identity_cache[path] = (hash_file(path).sha256, line_count)
    sha256, line_count = identity_cache[path]
    if end_line > line_count:
        raise ResearchEvidenceBindingError(
            f"evidence line range exceeds file: {artifact_ref}:{start_line}-{end_line}"
        )
    return EvidenceRef(
        artifact_ref=PurePosixPath(artifact_ref).as_posix(),
        artifact_sha256=sha256,
        start_line=start_line,
        end_line=end_line,
    )


def _replace_atomically(data: bytes, destination: Path) -> None:
    """Replace a draft in place without exposing a partially written file."""

    with tempfile.NamedTemporaryFile(
        mode="wb", dir=destination.parent, prefix=f".{destination.name}.", delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temporary, destination)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise


def _is_below(path: Path, root: Path) -> bool:
    return path != root and root in path.parents


def _contains_symlink(path: Path, root: Path) -> bool:
    """Reject symlink components between a workspace and an evidence path."""

    current = path
    while current != root and root in current.parents:
        if current.is_symlink():
            return True
        current = current.parent
    return False
