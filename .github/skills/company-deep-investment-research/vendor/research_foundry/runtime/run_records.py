"""Human- and agent-readable run records stored below a user workspace."""

from datetime import datetime, timezone
import json
import os
import re
from typing import Any
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class RunRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    capability: str
    status: str
    created_at: datetime
    input_manifest: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    recovery_actions: list[dict] = Field(default_factory=list)
    items: list[dict[str, Any]] = Field(default_factory=list)
    finished_at: datetime | None = None


def create_run(workspace_root: str | Path, capability: str, input_manifest: dict) -> RunRecord:
    record = RunRecord(
        run_id=f"run_{uuid4().hex}",
        capability=capability,
        status="running",
        created_at=datetime.now(timezone.utc),
        input_manifest=input_manifest,
    )
    path = Path(workspace_root).expanduser().resolve() / "runs" / record.run_id
    path.mkdir(parents=True, exist_ok=True)
    (path / "run.json").write_text(record.model_dump_json(indent=2), encoding="utf-8")
    return record


def write_run_record(workspace_root: str | Path, record: RunRecord) -> Path:
    path = Path(workspace_root).expanduser().resolve() / "runs" / record.run_id / "run.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_run_record(workspace_root: str | Path, run_id: str) -> RunRecord:
    path = Path(workspace_root).expanduser().resolve() / "runs" / run_id / "run.json"
    return RunRecord.model_validate_json(path.read_text(encoding="utf-8"))


def append_recovery_action(
    workspace_root: str | Path, run_id: str, action: dict[str, Any]
) -> Path:
    """Append one durable recovery event without exposing credentials."""

    path = Path(workspace_root).expanduser().resolve() / "runs" / run_id / "recovery_log.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp": datetime.now(timezone.utc).isoformat(), **action}
    with path.open("ab") as stream:
        stream.write((json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
        stream.flush()
        os.fsync(stream.fileno())
    return path


def append_debug_iteration(
    workspace_root: str | Path,
    run_id: str,
    iteration: dict[str, Any],
) -> Path:
    """Append an auditable, generalization-focused debugging iteration."""

    if not isinstance(iteration, dict):
        raise ValueError("debug iteration must be a JSON object")
    if not re.fullmatch(r"run_[A-Za-z0-9]+", run_id):
        raise ValueError("invalid run id")
    reserved = {"schema_version", "timestamp", "run_id"}
    if reserved.intersection(iteration):
        raise ValueError("debug iteration cannot override system fields")
    required = (
        "problem",
        "structural_basis",
        "positive_regression",
        "negative_regression",
        "validation",
        "result",
    )
    missing = [key for key in required if not str(iteration.get(key) or "").strip()]
    if missing:
        raise ValueError(f"debug iteration is missing required fields: {', '.join(missing)}")
    path = Path(workspace_root).expanduser().resolve() / "runs" / run_id / "debug_iterations.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "research_foundry_debug_iteration.v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        **iteration,
    }
    with path.open("ab") as stream:
        stream.write((json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
        stream.flush()
        os.fsync(stream.fileno())
    return path
