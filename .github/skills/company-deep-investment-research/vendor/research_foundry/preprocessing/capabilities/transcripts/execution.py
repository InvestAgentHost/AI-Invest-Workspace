"""Single-event transcript workspaces and immutable publication."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any

from research_foundry.runtime.artifacts import (
    ArtifactAlreadyExistsError,
    hash_file,
    publish_directory,
)
from research_foundry.runtime.run_records import (
    RunRecord,
    create_run,
    load_run_record,
    write_run_record,
)
from research_foundry.runtime.workspace import Workspace

from .planning import TranscriptPlan
from .provider_prepared import prepare_provider_minutes
from .validation import validate_cleaned_transcript


class TranscriptExecutionError(RuntimeError):
    """Raised when transcript work cannot proceed without changing identity."""


def start_transcript_run(plan: TranscriptPlan) -> RunRecord:
    if plan.status != "ready" or not plan.confirmed:
        raise TranscriptExecutionError("transcript plan is not confirmed")
    workspace = Workspace.from_path(plan.workspace_root)
    workspace.ensure_layout()
    source = Path(plan.source_path)
    _require_identity(source, plan.source_sha256, plan.source_byte_size)
    record = create_run(
        workspace.root,
        "transcript",
        {"schema_version": plan.schema_version, "plan": plan.model_dump(mode="json")},
    )
    run_directory = workspace.runs / record.run_id
    raw_directory = run_directory / "raw"
    prepared_directory = run_directory / "prepared"
    raw_directory.mkdir(parents=True, exist_ok=False)
    prepared_directory.mkdir(parents=True, exist_ok=False)
    frozen_source = raw_directory / f"source{source.suffix.lower() or '.txt'}"
    shutil.copyfile(source, frozen_source)
    _require_identity(frozen_source, plan.source_sha256, plan.source_byte_size)
    if plan.provenance_path:
        shutil.copyfile(plan.provenance_path, raw_directory / "provenance.json")
    auto_marker_count = prepare_provider_minutes(plan, frozen_source, prepared_directory)
    (run_directory / "plan.json").write_text(plan.model_dump_json(indent=2) + "\n", encoding="utf-8")
    record.status = "awaiting_preparation"
    record.items = [
        {
            "status": "awaiting_preparation",
            "frozen_source": str(frozen_source),
            "prepared_directory": str(prepared_directory),
            "source_representation": (
                "provider_prepared_minutes" if auto_marker_count is not None else plan.source_representation
            ),
            "auto_prepared": auto_marker_count is not None,
            "auto_marker_count": auto_marker_count,
        }
    ]
    write_run_record(workspace.root, record)
    return record


def publish_transcript_run(workspace_root: Path | str, run_id: str) -> tuple[RunRecord, Path | None]:
    _validate_run_id(run_id)
    workspace = Workspace.from_path(workspace_root)
    record = load_run_record(workspace.root, run_id)
    if record.capability != "transcript":
        raise TranscriptExecutionError("run is not a transcript run")
    if record.status == "completed":
        output = Path(str(record.items[0].get("artifact_directory", "")))
        if not output.is_dir():
            raise TranscriptExecutionError("completed transcript run has no artifact directory")
        verify_transcript_artifact(output, expected_identity=record.items[0].get("transcript_id"))
        return record, output
    if record.status not in {"awaiting_preparation", "failed"}:
        raise TranscriptExecutionError(f"transcript run cannot be published from status {record.status!r}")
    plan = TranscriptPlan.model_validate(record.input_manifest["plan"])
    run_directory = workspace.runs / run_id
    frozen_source = next((run_directory / "raw").glob("source.*"), None)
    if frozen_source is None:
        raise TranscriptExecutionError("frozen transcript source is missing")
    _require_identity(frozen_source, plan.source_sha256, plan.source_byte_size)
    prepared_directory = run_directory / "prepared"
    result = validate_cleaned_transcript(frozen_source, prepared_directory)
    if not result.usable:
        record.status = "failed"
        record.warnings = list(result.warnings)
        record.items = [
            {
                "status": "failed",
                "frozen_source": str(frozen_source),
                "prepared_directory": str(prepared_directory),
                "errors": list(result.errors),
            }
        ]
        record.finished_at = datetime.now(timezone.utc)
        write_run_record(workspace.root, record)
        return record, None

    transcript_identity = _transcript_identity(plan)
    destination = (
        workspace.artifacts
        / "transcripts"
        / _safe_component(plan.target_name)
        / f"{plan.event_date.isoformat()}_{plan.event_type}_{transcript_identity}"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_representation = str(record.items[0].get("source_representation") or plan.source_representation)
    manifest = _manifest(
        plan, record.run_id, frozen_source, prepared_directory, result.marker_count, result.warnings,
        source_representation=source_representation,
    )
    if destination.exists():
        existing = verify_transcript_artifact(destination, expected_identity=transcript_identity)
        _require_matching_publication(existing, manifest)
    else:
        with tempfile.TemporaryDirectory(prefix=f".{transcript_identity}.", dir=destination.parent) as temporary:
            staging = Path(temporary)
            (staging / "raw").mkdir()
            (staging / "prepared").mkdir()
            shutil.copyfile(frozen_source, staging / "raw" / frozen_source.name)
            shutil.copyfile(prepared_directory / "cleaned_transcript.md", staging / "prepared" / "cleaned_transcript.md")
            metadata = prepared_directory / "transcript_metadata.json"
            if metadata.is_file():
                shutil.copyfile(metadata, staging / "prepared" / "transcript_metadata.json")
            provenance = run_directory / "raw" / "provenance.json"
            if provenance.is_file():
                shutil.copyfile(provenance, staging / "raw" / "provenance.json")
            (staging / "transcript_manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            try:
                publish_directory(staging, destination)
            except ArtifactAlreadyExistsError:
                existing = verify_transcript_artifact(destination, expected_identity=transcript_identity)
                _require_matching_publication(existing, manifest)
        verify_transcript_artifact(destination, expected_identity=transcript_identity)

    completed_item = {
        "status": "completed",
        "transcript_id": transcript_identity,
        "artifact_directory": str(destination),
        "source_representation": source_representation,
    }
    if record.items:
        completed_item["auto_prepared"] = bool(record.items[0].get("auto_prepared", False))
        completed_item["auto_marker_count"] = record.items[0].get("auto_marker_count")
    record.status = "completed"
    record.warnings = list(result.warnings)
    record.items = [completed_item]
    record.finished_at = datetime.now(timezone.utc)
    write_run_record(workspace.root, record)
    return record, destination


def inspect_transcript_run(workspace_root: Path | str, run_id: str) -> dict[str, Any]:
    _validate_run_id(run_id)
    record = load_run_record(workspace_root, run_id)
    if record.capability != "transcript":
        raise TranscriptExecutionError("run is not a transcript run")
    payload = record.model_dump(mode="json")
    if record.status == "completed":
        output = Path(str(record.items[0].get("artifact_directory", "")))
        verify_transcript_artifact(output, expected_identity=record.items[0].get("transcript_id"))
        payload["artifact_verified"] = True
    return payload


def verify_transcript_artifact(directory: Path | str, *, expected_identity: str | None = None) -> dict[str, Any]:
    root = Path(directory).resolve()
    try:
        manifest = json.loads((root / "transcript_manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise TranscriptExecutionError(f"invalid transcript_manifest.json: {error}") from error
    required = {"schema_version", "transcript_id", "target", "event", "source", "prepared", "run_id", "created_at"}
    if not isinstance(manifest, dict) or not required.issubset(manifest):
        raise TranscriptExecutionError("transcript manifest is missing required fields")
    if manifest["schema_version"] != "research_foundry_transcript_manifest.v1":
        raise TranscriptExecutionError("unsupported transcript manifest schema")
    if expected_identity and manifest["transcript_id"] != expected_identity:
        raise TranscriptExecutionError("transcript identity does not match destination")
    for section in ("source", "prepared"):
        item = manifest[section]
        path = (root / item["artifact_ref"]).resolve()
        if root not in path.parents or not path.is_file():
            raise TranscriptExecutionError(f"invalid {section} artifact reference")
        identity = hash_file(path)
        if identity.sha256 != item["sha256"] or identity.byte_size != item["byte_size"]:
            raise TranscriptExecutionError(f"{section} artifact identity mismatch")
    provenance = manifest["source"].get("provenance")
    if provenance is not None:
        path = (root / provenance["artifact_ref"]).resolve()
        if root not in path.parents or not path.is_file():
            raise TranscriptExecutionError("invalid provenance artifact reference")
        identity = hash_file(path)
        if identity.sha256 != provenance["sha256"] or identity.byte_size != provenance["byte_size"]:
            raise TranscriptExecutionError("provenance artifact identity mismatch")
    return manifest


def _manifest(
    plan: TranscriptPlan,
    run_id: str,
    source: Path,
    prepared: Path,
    marker_count: int,
    warnings: tuple[str, ...],
    *,
    source_representation: str,
) -> dict[str, Any]:
    source_identity = hash_file(source)
    cleaned_identity = hash_file(prepared / "cleaned_transcript.md")
    source_ref = f"raw/{source.name}"
    source_manifest = {
        "method": plan.source_method,
        "provider": plan.provider,
        "provider_record_id": plan.provider_record_id,
        "representation": source_representation,
        "artifact_ref": source_ref,
        "sha256": source_identity.sha256,
        "byte_size": source_identity.byte_size,
    }
    frozen_provenance = source.parent / "provenance.json"
    if frozen_provenance.is_file():
        provenance_identity = hash_file(frozen_provenance)
        source_manifest["provenance"] = {
            "artifact_ref": "raw/provenance.json",
            "sha256": provenance_identity.sha256,
            "byte_size": provenance_identity.byte_size,
        }
    return {
        "schema_version": "research_foundry_transcript_manifest.v1",
        "transcript_id": _transcript_identity(plan),
        "target": {"name": plan.target_name},
        "event": {
            "date": plan.event_date.isoformat(),
            "type": plan.event_type,
            "fiscal_period": plan.fiscal_period,
        },
        "source": source_manifest,
        "prepared": {
            "artifact_ref": "prepared/cleaned_transcript.md",
            "sha256": cleaned_identity.sha256,
            "byte_size": cleaned_identity.byte_size,
            "marker_count": marker_count,
        },
        "warnings": list(warnings),
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _transcript_identity(plan: TranscriptPlan) -> str:
    payload = "\n".join(
        (
            plan.target_name.casefold(),
            plan.event_date.isoformat(),
            plan.event_type,
            plan.fiscal_period or "",
            plan.source_method,
            plan.provider.casefold(),
            plan.provider_record_id or "",
            plan.source_sha256,
        )
    ).encode("utf-8")
    return f"trn_{hashlib.sha256(payload).hexdigest()[:16]}"


def _require_identity(path: Path, expected_sha256: str, expected_size: int) -> None:
    try:
        identity = hash_file(path)
    except OSError as error:
        raise TranscriptExecutionError(f"unable to read transcript source: {error}") from error
    if identity.sha256 != expected_sha256 or identity.byte_size != expected_size:
        raise TranscriptExecutionError("transcript source changed after planning")


def _safe_component(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "._-" else "_" for char in value.strip())
    if not cleaned:
        raise TranscriptExecutionError("target_name must contain a filesystem-safe character")
    return cleaned


def _validate_run_id(run_id: str) -> None:
    if not re.fullmatch(r"run_[A-Za-z0-9]+", run_id):
        raise TranscriptExecutionError("invalid run id")


def _require_matching_publication(existing: dict[str, Any], requested: dict[str, Any]) -> None:
    keys = (
        ("transcript_id",),
        ("target", "name"),
        ("event", "date"),
        ("event", "type"),
        ("event", "fiscal_period"),
        ("source", "sha256"),
        ("prepared", "sha256"),
    )
    for path in keys:
        left: Any = existing
        right: Any = requested
        for key in path:
            left = left[key]
            right = right[key]
        if left != right:
            raise TranscriptExecutionError(
                "immutable transcript artifact already exists with different prepared content or identity"
            )
