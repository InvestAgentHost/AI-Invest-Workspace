"""Confirmed single-event plans for transcript preparation."""

from __future__ import annotations

from datetime import date
import hashlib
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


TranscriptEventType = Literal[
    "earnings_call",
    "fireside_chat",
    "investor_meeting",
    "roadshow",
    "conference",
    "other",
]
TranscriptSourceMethod = Literal["user_upload"]
TranscriptSourceRepresentation = Literal["raw_transcript", "provider_prepared_minutes"]


class TranscriptPlan(BaseModel):
    """One confirmed source and event identity awaiting Agent preparation."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    schema_version: Literal["research_foundry_transcript_plan.v1"]
    plan_id: str
    status: Literal["needs_confirmation", "ready"]
    target_name: str = Field(min_length=1)
    event_date: date
    event_type: TranscriptEventType
    fiscal_period: str | None = None
    workspace_root: str
    source_path: str
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_byte_size: int = Field(gt=0)
    source_method: TranscriptSourceMethod
    provider: str = Field(min_length=1)
    provider_record_id: str | None = None
    provenance_path: str | None = None
    source_representation: TranscriptSourceRepresentation = "raw_transcript"
    source_title: str | None = None
    confirmed: bool
    warnings: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_state(self) -> "TranscriptPlan":
        if self.status == "ready" and not self.confirmed:
            raise ValueError("ready transcript plan must be confirmed")
        return self


def build_transcript_plan(
    source_path: Path | str,
    *,
    target_name: str,
    event_date: date,
    event_type: TranscriptEventType,
    workspace_root: Path | str,
    fiscal_period: str | None = None,
    source_method: TranscriptSourceMethod = "user_upload",
    provider: str = "local",
    provider_record_id: str | None = None,
    provenance_path: Path | str | None = None,
    source_representation: TranscriptSourceRepresentation = "raw_transcript",
    source_title: str | None = None,
    confirmed: bool = False,
) -> TranscriptPlan:
    source = Path(source_path).expanduser().resolve()
    if not source.is_file():
        raise ValueError(f"transcript source does not exist: {source}")
    data = source.read_bytes()
    if not data:
        raise ValueError("transcript source is empty")
    try:
        if not data.decode("utf-8").strip():
            raise ValueError("transcript source has no substantive UTF-8 text")
    except UnicodeDecodeError as error:
        raise ValueError("transcript source must be UTF-8") from error
    provenance = None
    if provenance_path is not None:
        provenance_file = Path(provenance_path).expanduser().resolve()
        if not provenance_file.is_file():
            raise ValueError(f"transcript provenance does not exist: {provenance_file}")
        provenance = str(provenance_file)
    return TranscriptPlan(
        schema_version="research_foundry_transcript_plan.v1",
        plan_id=f"trp_{uuid4().hex}",
        status="ready" if confirmed else "needs_confirmation",
        target_name=target_name,
        event_date=event_date,
        event_type=event_type,
        fiscal_period=fiscal_period,
        workspace_root=str(Path(workspace_root).expanduser().resolve()),
        source_path=str(source),
        source_sha256=hashlib.sha256(data).hexdigest(),
        source_byte_size=len(data),
        source_method=source_method,
        provider=provider,
        provider_record_id=provider_record_id,
        provenance_path=provenance,
        source_representation=source_representation,
        source_title=source_title,
        confirmed=confirmed,
    )
