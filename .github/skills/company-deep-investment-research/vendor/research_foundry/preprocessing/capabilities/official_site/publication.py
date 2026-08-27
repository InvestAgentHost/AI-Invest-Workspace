"""Validate, immutably publish, and inspect official-site snapshots."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any

from research_foundry.runtime.artifacts import ArtifactAlreadyExistsError, publish_directory
from research_foundry.runtime.run_records import RunRecord, load_run_record, write_run_record
from research_foundry.runtime.workspace import Workspace

from .models import OfficialSitePlan
from .validation import validate_official_site_snapshot, verify_official_site_artifact


class OfficialSitePublicationError(RuntimeError):
    """Raised when a run is not publishable without changing its identity."""


def publish_official_site_run(workspace_root: str | Path, run_id: str) -> tuple[RunRecord, Path]:
    _validate_run_id(run_id)
    workspace = Workspace.from_path(workspace_root)
    record = load_run_record(workspace.root, run_id)
    if record.capability != "official_site":
        raise OfficialSitePublicationError("run is not an official-site run")
    if record.status in {"completed", "partial"}:
        destination = Path(str(record.items[0].get("artifact_directory", "")))
        verify_official_site_artifact(destination)
        return record, destination
    if record.status != "awaiting_synthesis":
        raise OfficialSitePublicationError(f"run cannot be published from status {record.status!r}")
    plan = OfficialSitePlan.model_validate(record.input_manifest["plan"])
    item = record.items[0]
    snapshot_id = str(item["snapshot_id"])
    snapshot = Path(str(item["snapshot_working_directory"])).resolve()
    expected_snapshot = (workspace.runs / run_id / "snapshot").resolve()
    if snapshot != expected_snapshot or not snapshot.is_dir():
        raise OfficialSitePublicationError("run snapshot working directory is invalid")
    validated = validate_official_site_snapshot(
        snapshot,
        plan=plan,
        run_id=run_id,
        snapshot_id=snapshot_id,
    )
    target = _safe_component(plan.target_name)
    destination = workspace.artifacts / "official_site" / target / plan.as_of.isoformat() / snapshot_id
    manifest = {
        "schema_version": "research_foundry_official_site_manifest.v1",
        "snapshot_id": snapshot_id,
        "run_id": run_id,
        "target": {"name": plan.target_name},
        "as_of": plan.as_of.isoformat(),
        "research_ready": validated["quality"].research_ready,
        "counts": validated["counts"],
        "plan": plan.model_dump(mode="json"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        existing = verify_official_site_artifact(destination)
        if existing.get("snapshot_id") != snapshot_id or existing.get("run_id") != run_id:
            raise OfficialSitePublicationError("immutable official-site artifact already exists with different identity")
    else:
        with tempfile.TemporaryDirectory(prefix=f".{snapshot_id}.", dir=destination.parent) as temporary:
            staging = Path(temporary) / snapshot_id
            shutil.copytree(snapshot, staging)
            (staging / "official_site_manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            try:
                publish_directory(staging, destination)
            except ArtifactAlreadyExistsError:
                verify_official_site_artifact(destination)
        verify_official_site_artifact(destination)
    record.status = "completed" if validated["quality"].research_ready else "partial"
    record.finished_at = datetime.now(timezone.utc)
    record.warnings = list(validated["quality"].warnings)
    record.items = [
        {
            **item,
            "status": record.status,
            "artifact_directory": str(destination),
            "research_ready": validated["quality"].research_ready,
            "counts": validated["counts"],
        }
    ]
    write_run_record(workspace.root, record)
    return record, destination


def inspect_official_site_run(workspace_root: str | Path, run_id: str) -> dict[str, Any]:
    _validate_run_id(run_id)
    record = load_run_record(workspace_root, run_id)
    if record.capability != "official_site":
        raise OfficialSitePublicationError("run is not an official-site run")
    payload = record.model_dump(mode="json")
    if record.status in {"completed", "partial"}:
        directory = Path(str(record.items[0].get("artifact_directory", "")))
        payload["artifact_verified"] = bool(verify_official_site_artifact(directory))
    return payload


def _safe_component(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "._-" else "_" for char in value.strip())
    if not cleaned:
        raise OfficialSitePublicationError("target_name must contain a filesystem-safe character")
    return cleaned


def _validate_run_id(run_id: str) -> None:
    if not re.fullmatch(r"run_[A-Za-z0-9]+", run_id):
        raise OfficialSitePublicationError("invalid run id")
