"""Mechanical integrity checks for Agent-prepared earnings transcripts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any


MARKER = re.compile(r"^###\s+(T\d{4,})\s+\|\s+(.+?)\s+\|\s+([^|]+?)\s+\|\s+([^|]+?)\s*$")
HEADER_FIELD = re.compile(r"^[-*]\s*(Source SHA-256|Source coverage|Limitations):\s*(.*?)\s*$", re.IGNORECASE)
SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class TranscriptCheckResult:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    marker_count: int

    @property
    def usable(self) -> bool:
        return not self.errors


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_metadata(path: Path, warnings: list[str]) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        warnings.append(f"transcript_metadata.json is unreadable: {type(error).__name__}")
        return None
    if not isinstance(value, dict):
        warnings.append("transcript_metadata.json root is not an object")
        return None
    return value


def validate_cleaned_transcript(source: Path | None, output: Path) -> TranscriptCheckResult:
    """Validate public transcript provenance and citation mechanics.

    Content uncertainty is intentionally a warning or a disclosed limitation.
    Only unreadable output, incorrect provenance, and unusable turn markers fail.
    """

    errors: list[str] = []
    warnings: list[str] = []
    transcript_path = output / "cleaned_transcript.md"
    try:
        text = transcript_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return TranscriptCheckResult((f"cleaned_transcript.md is unreadable: {type(error).__name__}",), (), 0)
    if not text.strip():
        return TranscriptCheckResult(("cleaned_transcript.md contains no substantive content",), (), 0)

    lines = text.splitlines()
    first_marker = next((index for index, line in enumerate(lines) if MARKER.fullmatch(line.strip())), len(lines))
    header_lines = lines[:first_marker]
    if not any(line.strip().startswith("# ") for line in header_lines):
        errors.append("cleaned_transcript.md header has no title")
    fields: dict[str, str] = {}
    for line in header_lines:
        match = HEADER_FIELD.fullmatch(line.strip())
        if match is None:
            continue
        key = match.group(1).casefold()
        if key in fields:
            errors.append(f"cleaned_transcript.md header repeats {match.group(1)}")
        fields[key] = match.group(2).strip().strip("`")
    coverage = fields.get("source coverage")
    if coverage not in {"complete", "partial", "unknown"}:
        errors.append("cleaned_transcript.md header requires Source coverage: complete | partial | unknown")
    limitations = fields.get("limitations")
    if not limitations:
        errors.append("cleaned_transcript.md header requires non-empty Limitations")
    elif coverage in {"partial", "unknown"} and limitations.casefold() in {"none", "none known", "none known."}:
        warnings.append("partial or unknown source coverage has no disclosed limitation")
    declared_hash = fields.get("source sha-256")
    if declared_hash is not None and SHA256.fullmatch(declared_hash) is None:
        errors.append("cleaned_transcript.md Source SHA-256 is not 64 lowercase hex characters")
    if source is not None:
        if declared_hash is None:
            errors.append("cleaned_transcript.md header requires Source SHA-256 for supplied source")
        else:
            try:
                if declared_hash != _sha256(source):
                    errors.append("cleaned_transcript.md Source SHA-256 does not match supplied source")
            except OSError as error:
                errors.append(f"supplied source cannot be hashed: {type(error).__name__}")

    markers = [(index, match.group(1)) for index, line in enumerate(lines) if (match := MARKER.fullmatch(line.strip()))]
    for position, (line_index, marker_id) in enumerate(markers):
        next_index = markers[position + 1][0] if position + 1 < len(markers) else len(lines)
        if not any(line.strip() for line in lines[line_index + 1:next_index]):
            errors.append(f"cleaned_transcript.md marker {marker_id} has no turn content")
    marker_ids = [marker_id for _, marker_id in markers]
    if not marker_ids:
        errors.append("cleaned_transcript.md contains no valid T#### evidence markers")
    if len(marker_ids) != len(set(marker_ids)):
        errors.append("cleaned_transcript.md contains duplicate evidence markers")
    numbers = [int(marker_id[1:]) for marker_id in marker_ids]
    if numbers and numbers != list(range(1, len(numbers) + 1)):
        warnings.append("evidence markers are not contiguous from T0001")

    metadata = _read_metadata(output / "transcript_metadata.json", warnings)
    if metadata is not None:
        if metadata.get("schema_version") != "analysis_ready_transcript.v2":
            warnings.append("metadata schema_version is not analysis_ready_transcript.v2")
        metadata_markers = metadata.get("markers")
        if isinstance(metadata_markers, list):
            metadata_ids = [
                item.get("id")
                for item in metadata_markers
                if isinstance(item, dict) and isinstance(item.get("id"), str)
            ]
            missing = sorted(set(marker_ids) - set(metadata_ids))
            extra = sorted(set(metadata_ids) - set(marker_ids))
            if missing or extra:
                warnings.append(f"metadata marker inventory differs: missing={missing}, extra={extra}")
        else:
            warnings.append("metadata markers is not an array")
        issues = metadata.get("issues")
        if isinstance(issues, list):
            for issue in issues:
                if not isinstance(issue, dict) or issue.get("severity") not in {"warning", "error", "critical"}:
                    continue
                warnings.append(
                    f"metadata issue {issue.get('code', 'unspecified')}: {issue.get('description', '')}".rstrip()
                )
        elif issues is not None:
            warnings.append("metadata issues is not an array")
        if source is not None:
            try:
                if metadata.get("source_sha256") != _sha256(source):
                    warnings.append("metadata source_sha256 does not match the supplied source")
            except OSError as error:
                warnings.append(f"source cannot be hashed: {type(error).__name__}")
    return TranscriptCheckResult(tuple(errors), tuple(warnings), len(marker_ids))
