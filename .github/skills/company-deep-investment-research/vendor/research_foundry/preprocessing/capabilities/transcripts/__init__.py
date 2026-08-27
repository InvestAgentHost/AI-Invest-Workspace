"""Transcript preparation contracts and integrity checks."""

from .validation import TranscriptCheckResult, validate_cleaned_transcript
from .planning import TranscriptPlan, build_transcript_plan
from .metadata import (
    TranscriptMetadata,
    build_transcript_plan_from_metadata,
    load_transcript_metadata,
    write_transcript_metadata_template,
)
from .execution import (
    TranscriptExecutionError,
    inspect_transcript_run,
    publish_transcript_run,
    start_transcript_run,
    verify_transcript_artifact,
)

__all__ = [
    "TranscriptCheckResult",
    "TranscriptExecutionError",
    "TranscriptPlan",
    "TranscriptMetadata",
    "build_transcript_plan",
    "build_transcript_plan_from_metadata",
    "inspect_transcript_run",
    "publish_transcript_run",
    "start_transcript_run",
    "load_transcript_metadata",
    "validate_cleaned_transcript",
    "verify_transcript_artifact",
    "write_transcript_metadata_template",
]
