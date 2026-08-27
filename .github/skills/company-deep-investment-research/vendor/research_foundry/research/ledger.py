"""Deterministic execution ledger for comprehensive research assignments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
from typing import Iterable, Literal

from pydantic import ValidationError

from .contracts import AgentLedger, AgentLedgerEntry
from .coverage import load_research_coverage
from .notebook import _replace_atomically, _resolve_notebook


LEDGER_FILENAME = "agent_ledger.json"
LedgerRole = Literal["research", "writer", "reviewer"]
LedgerStatus = Literal[
    "planned",
    "started",
    "checkpointed",
    "completed",
    "failed",
    "interrupted",
    "blocked",
]
TERMINAL_STATUSES = frozenset({"completed", "failed", "interrupted", "blocked"})
ACTIVE_STATUSES = frozenset({"started", "checkpointed"})


class AgentLedgerError(ValueError):
    """Raised when an execution ledger cannot be safely advanced."""


@dataclass(frozen=True, slots=True)
class AgentLedgerValidationReport:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    entry_count: int
    completed_count: int
    retry_count: int = 0

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _now() -> datetime:
    return datetime.now(UTC)


def _ledger_path(root: Path) -> Path:
    return root / LEDGER_FILENAME


def load_agent_ledger(
    research_root: str | Path, *, workspace_root: str | Path
) -> AgentLedger:
    root, _, identity = _resolve_notebook(research_root, workspace_root)
    path = _ledger_path(root)
    if path.is_symlink() or not path.is_file():
        raise AgentLedgerError(f"notebook is missing {LEDGER_FILENAME}")
    try:
        ledger = AgentLedger.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValidationError, ValueError) as error:
        raise AgentLedgerError(f"invalid {LEDGER_FILENAME}: {error}") from error
    if ledger.research_id != identity.research_id:
        raise AgentLedgerError("agent ledger research_id does not match task.md")
    return ledger


def initialize_agent_ledger(
    research_root: str | Path, *, workspace_root: str | Path
) -> AgentLedger:
    """Create planned research assignments from the current coverage DAG."""

    root, _, identity = _resolve_notebook(research_root, workspace_root)
    path = _ledger_path(root)
    if path.exists() or path.is_symlink():
        raise AgentLedgerError(f"{LEDGER_FILENAME} already exists")
    coverage = load_research_coverage(root)
    branches = {item.branch_id: item for item in coverage.branches}
    entries: list[AgentLedgerEntry] = []
    now = _now()
    for branch in sorted(coverage.branches, key=lambda item: item.branch_id):
        assignment_id = f"research_{branch.branch_id}"
        entries.append(
            AgentLedgerEntry(
                assignment_id=assignment_id,
                role="research",
                branch_id=branch.branch_id,
                responsibility_id=branch.responsibility_id,
                agent_ref=branch.agent_ref,
                depends_on=tuple(f"research_{item}" for item in branch.depends_on),
                owned_files=(branch.note_ref,),
                note_ref=branch.note_ref,
                status="planned",
                updated_at=now,
            )
        )
    if not entries:
        raise AgentLedgerError("coverage has no branches for ledger initialization")
    ledger = AgentLedger(research_id=identity.research_id, updated_at=now, entries=tuple(entries))
    _write_ledger(path, ledger)
    return ledger


def record_agent_event(
    research_root: str | Path,
    *,
    workspace_root: str | Path,
    assignment_id: str,
    status: LedgerStatus,
    agent_ref: str | None = None,
    role: LedgerRole | None = None,
    branch_id: str | None = None,
    responsibility_id: str | None = None,
    depends_on: Iterable[str] = (),
    owned_files: Iterable[str] = (),
    note_ref: str | None = None,
    error: str | None = None,
    retry: bool = False,
) -> AgentLedger:
    """Record a start/checkpoint/finish event without accepting identity fields."""

    if not assignment_id.strip():
        raise AgentLedgerError("assignment_id must be non-empty")
    root, _, identity = _resolve_notebook(research_root, workspace_root)
    try:
        ledger = load_agent_ledger(root, workspace_root=workspace_root)
    except AgentLedgerError as exc:
        if "missing" not in str(exc):
            raise
        ledger = initialize_agent_ledger(root, workspace_root=workspace_root)
    entries = list(ledger.entries)
    index = next(
        (position for position, item in enumerate(entries) if item.assignment_id == assignment_id),
        None,
    )
    if index is None:
        if role is None:
            raise AgentLedgerError("new ledger assignment requires role")
        entries.append(
            AgentLedgerEntry(
                assignment_id=assignment_id,
                role=role,
                branch_id=branch_id,
                responsibility_id=responsibility_id,
                agent_ref=agent_ref,
                depends_on=tuple(depends_on),
                owned_files=tuple(owned_files),
                note_ref=note_ref,
                status="planned",
                updated_at=_now(),
            )
        )
        index = len(entries) - 1
    current = entries[index]
    if retry:
        if current.status not in TERMINAL_STATUSES:
            raise AgentLedgerError("can only retry a terminal Agent assignment")
        if status != "started":
            raise AgentLedgerError("a retry must begin with status started")
        base_id = current.assignment_id.split("_retry", 1)[0]
        previous_attempts = [
            item.attempt
            for item in entries
            if item.role == current.role and item.branch_id == current.branch_id
        ]
        next_attempt = max(previous_attempts, default=current.attempt) + 1
        assignment_id = f"{base_id}_retry{next_attempt}"
        current = AgentLedgerEntry(
            assignment_id=assignment_id,
            role=current.role,
            branch_id=current.branch_id,
            responsibility_id=current.responsibility_id,
            agent_ref=agent_ref,
            depends_on=current.depends_on,
            owned_files=current.owned_files,
            note_ref=current.note_ref,
            attempt=next_attempt,
            status="planned",
            updated_at=_now(),
        )
        entries.append(current)
        index = len(entries) - 1
    elif current.status in TERMINAL_STATUSES and status != current.status:
        raise AgentLedgerError(
            f"terminal assignment cannot change state without --retry: {current.assignment_id}"
        )
    if current.agent_ref and agent_ref and current.agent_ref != agent_ref:
        raise AgentLedgerError(
            f"assignment already belongs to {current.agent_ref}; use --retry for a new Agent"
        )
    if current.role == "writer" and status in ACTIVE_STATUSES | {"completed"}:
        incomplete_research = [
            item.assignment_id
            for item in entries
            if item.role == "research" and item.status not in TERMINAL_STATUSES
        ]
        if incomplete_research:
            raise AgentLedgerError(
                "Writer cannot start before research assignments are terminal: "
                + ", ".join(sorted(incomplete_research))
            )
    if current.role == "reviewer" and status in ACTIVE_STATUSES | {"completed"}:
        if not any(
            item.role == "writer" and item.status == "completed" for item in entries
        ):
            raise AgentLedgerError("Reviewer cannot start before Writer is completed")
    allowed_transitions = {
        "planned": {"started", "blocked", "failed", "interrupted"},
        "started": ACTIVE_STATUSES | TERMINAL_STATUSES,
        "checkpointed": ACTIVE_STATUSES | TERMINAL_STATUSES,
        "completed": {"completed"},
        "failed": {"failed"},
        "interrupted": {"interrupted"},
        "blocked": {"blocked"},
    }
    if status not in allowed_transitions[current.status]:
        raise AgentLedgerError(
            f"invalid Agent status transition: {current.status} -> {status}"
        )
    dependency_ids = tuple(depends_on) or current.depends_on
    entry_by_id = {item.assignment_id: item for item in entries}
    missing = set(dependency_ids).difference(entry_by_id)
    if missing:
        raise AgentLedgerError(f"unknown agent dependency: {sorted(missing)[0]}")
    if status in {"started", "checkpointed"}:
        incomplete = [
            item.assignment_id
            for item in (entry_by_id[item_id] for item_id in dependency_ids)
            if item.status not in {"completed", "blocked"}
        ]
        if incomplete:
            raise AgentLedgerError(
                f"assignment dependencies are not complete: {', '.join(sorted(incomplete))}"
            )
    now = _now()
    merged_files = tuple(dict.fromkeys((*current.owned_files, *tuple(owned_files))))
    started_at = current.started_at or (now if status != "planned" else None)
    finished_at = (
        now if status in {"completed", "failed", "interrupted", "blocked"} else current.finished_at
    )
    entries[index] = AgentLedgerEntry(
        assignment_id=current.assignment_id,
        role=current.role,
        branch_id=current.branch_id,
        responsibility_id=current.responsibility_id,
        agent_ref=agent_ref or current.agent_ref,
        depends_on=dependency_ids,
        owned_files=merged_files,
        note_ref=note_ref or current.note_ref,
        attempt=current.attempt,
        status=status,
        started_at=started_at,
        updated_at=now,
        finished_at=finished_at,
        error=error,
    )
    updated = AgentLedger(research_id=identity.research_id, updated_at=now, entries=tuple(entries))
    _write_ledger(_ledger_path(root), updated)
    return updated


def validate_agent_ledger(
    research_root: str | Path,
    *,
    workspace_root: str | Path,
    require_roles: Iterable[LedgerRole] = (),
    stale_after_seconds: int | None = None,
) -> AgentLedgerValidationReport:
    """Check ledger completion, coverage ownership, DAG order, and role separation."""

    errors: list[str] = []
    warnings: list[str] = []
    try:
        root, _, identity = _resolve_notebook(research_root, workspace_root)
        ledger = load_agent_ledger(root, workspace_root=workspace_root)
        coverage = load_research_coverage(root)
    except (AgentLedgerError, ValueError) as error:
        return AgentLedgerValidationReport(False, (str(error),), (), 0, 0, 0)
    if ledger.research_id != identity.research_id:
        errors.append("agent ledger research_id does not match task.md")
    entry_by_branch = {
        item.branch_id: item
        for item in ledger.entries
        if item.role == "research" and item.branch_id is not None
    }
    entry_by_id = {item.assignment_id: item for item in ledger.entries}
    if stale_after_seconds is not None:
        if stale_after_seconds < 1:
            errors.append("stale_after_seconds must be positive")
        else:
            cutoff = _now() - timedelta(seconds=stale_after_seconds)
            for item in ledger.entries:
                if item.status in ACTIVE_STATUSES and item.updated_at < cutoff:
                    errors.append(
                        f"Agent assignment appears stale: {item.assignment_id}; "
                        "record checkpointed, interrupted, blocked, or completed"
                    )
    for branch in coverage.branches:
        if branch.execution_mode != "delegated":
            continue
        entry = entry_by_branch.get(branch.branch_id)
        if entry is None:
            errors.append(f"ledger lacks delegated branch: {branch.branch_id}")
            continue
        if branch.agent_ref and entry.agent_ref != branch.agent_ref:
            errors.append(f"ledger agent_ref mismatch: {branch.branch_id}")
        if branch.note_ref not in entry.owned_files:
            errors.append(f"ledger does not own branch note: {branch.branch_id}")
        expected = {f"research_{item}" for item in branch.depends_on}
        if not expected.issubset(entry_by_id):
            errors.append(f"ledger dependencies missing: {branch.branch_id}")
        if branch.readiness == "blocked":
            if entry.status not in {"blocked", "failed", "interrupted"}:
                errors.append(f"blocked branch has non-blocked ledger state: {branch.branch_id}")
        elif entry.status != "completed":
            errors.append(f"delegated branch is not completed: {branch.branch_id}")
        for dependency_id in entry.depends_on:
            dependency = entry_by_id.get(dependency_id)
            if dependency is not None and dependency.status not in {"completed", "blocked"}:
                errors.append(f"ledger dependency is incomplete: {entry.assignment_id}")
    for role in require_roles:
        matches = [item for item in ledger.entries if item.role == role]
        if not matches:
            errors.append(f"ledger lacks required role: {role}")
        elif not any(item.status == "completed" for item in matches):
            errors.append(f"required ledger role is not completed: {role}")
    delegated_refs = {
        item.agent_ref
        for item in ledger.entries
        if item.role == "research" and item.agent_ref
    }
    for role in ("writer", "reviewer"):
        for item in ledger.entries:
            if item.role == role and item.agent_ref in delegated_refs:
                errors.append(f"{role} Agent overlaps research Agent: {item.assignment_id}")
    for item in ledger.entries:
        for owned_file in item.owned_files:
            path = (root / owned_file).resolve()
            if root not in path.parents or path.is_symlink() or not path.is_file():
                if item.status in TERMINAL_STATUSES:
                    errors.append(
                        f"completed Agent assignment owns missing or unsafe file: "
                        f"{item.assignment_id} -> {owned_file}"
                    )
    return AgentLedgerValidationReport(
        not errors,
        tuple(errors),
        tuple(warnings),
        len(ledger.entries),
        sum(item.status == "completed" for item in ledger.entries),
        sum(max(0, item.attempt - 1) for item in ledger.entries),
    )


def _write_ledger(path: Path, ledger: AgentLedger) -> None:
    _replace_atomically((ledger.model_dump_json(indent=2) + "\n").encode("utf-8"), path)
