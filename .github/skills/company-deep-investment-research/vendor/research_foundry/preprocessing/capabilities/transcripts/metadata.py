"""Human-editable metadata for manually supplied transcript sources."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .planning import (
    TranscriptEventType,
    TranscriptSourceMethod,
    TranscriptPlan,
    build_transcript_plan,
)


class TranscriptMetadata(BaseModel):
    """Portable metadata needed to turn one local source into a plan."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    schema_version: Literal["research_foundry_transcript_metadata.v1"]
    source_path: str = Field(min_length=1)
    target_name: str = Field(min_length=1)
    event_date: date
    event_type: TranscriptEventType
    fiscal_period: str | None = None
    workspace_root: str = Field(min_length=1)
    source_method: TranscriptSourceMethod = "user_upload"
    provider: str = Field(default="local", min_length=1)
    provider_record_id: str | None = None
    provenance_path: str | None = None


def render_transcript_metadata_template(
    *,
    source_path: str = "",
    target_name: str = "",
    event_date_value: str = "",
    event_type: str = "",
    fiscal_period: str = "",
    workspace_root: str = "",
) -> str:
    """Render a commented template without claiming that blank fields are valid."""

    def quoted(value: str) -> str:
        return json.dumps(value, ensure_ascii=False)

    return (
        "# One file describes one manually supplied transcript event.\n"
        "# Fill every required field, then let the Agent show and confirm the plan.\n"
        "schema_version: research_foundry_transcript_metadata.v1\n"
        f"source_path: {quoted(source_path)}  # raw transcript file; relative paths resolve from this YAML\n"
        f"target_name: {quoted(target_name)}\n"
        f"event_date: {quoted(event_date_value)}  # YYYY-MM-DD\n"
        f"event_type: {quoted(event_type)}  # earnings_call | fireside_chat | investor_meeting | roadshow | conference | other\n"
        f"fiscal_period: {quoted(fiscal_period)}  # optional, for example FY2026 Q2\n"
        f"workspace_root: {quoted(workspace_root)}\n"
        "source_method: user_upload\n"
        "provider: local\n"
        "provider_record_id: null\n"
        "provenance_path: null\n"
    )


def write_transcript_metadata_template(output: Path | str, **values: str) -> Path:
    destination = Path(output).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite existing transcript metadata: {destination}")
    destination.write_text(render_transcript_metadata_template(**values), encoding="utf-8")
    return destination


def load_transcript_metadata(path: Path | str) -> TranscriptMetadata:
    metadata_path = Path(path).expanduser().resolve()
    try:
        payload: Any = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ValueError(f"invalid transcript metadata YAML: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError("transcript metadata must be a YAML mapping")
    return TranscriptMetadata.model_validate(payload)


def build_transcript_plan_from_metadata(
    metadata_path: Path | str, *, confirmed: bool = False
) -> TranscriptPlan:
    path = Path(metadata_path).expanduser().resolve()
    metadata = load_transcript_metadata(path)

    def resolve(value: str) -> Path:
        candidate = Path(value).expanduser()
        return (path.parent / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()

    provenance = resolve(metadata.provenance_path) if metadata.provenance_path else None
    return build_transcript_plan(
        resolve(metadata.source_path),
        target_name=metadata.target_name,
        event_date=metadata.event_date,
        event_type=metadata.event_type,
        workspace_root=resolve(metadata.workspace_root),
        fiscal_period=metadata.fiscal_period or None,
        source_method=metadata.source_method,
        provider=metadata.provider,
        provider_record_id=metadata.provider_record_id,
        provenance_path=provenance,
        confirmed=confirmed,
    )
