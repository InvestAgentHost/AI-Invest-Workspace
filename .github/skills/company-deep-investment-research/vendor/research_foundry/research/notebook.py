"""Free-form research notebooks with deterministic citations and publication."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Literal

from pydantic import TypeAdapter, ValidationError
import yaml

from research_foundry.runtime.artifacts import hash_file, publish_bytes

from .coverage import (
    load_method_panel_specs,
    load_research_coverage,
    uses_comprehensive_output,
    validate_comprehensive_report,
    validate_research_coverage,
)
from .contracts import (
    NotebookCitation,
    NotebookSourceRecord,
    PublishedArtifact,
    ResearchNotebookReleaseManifest,
)
from .contracts.models import StableId
from .workspace import _safe_segment


_PLACEHOLDER = re.compile(
    r"(?:\bTODO\b|\bTBD\b|\[Agent synthesis required\])", re.IGNORECASE
)
_SOURCE_DEFINITION = re.compile(
    r"^\[source:([A-Za-z][A-Za-z0-9_-]{2,95})\]:\s+(.+?)\s*$"
)
_CITATION = re.compile(
    r"\[\[([A-Za-z][A-Za-z0-9_-]{2,95}):L([1-9][0-9]*)(?:-L?([1-9][0-9]*))?\]\]"
)
_TASK_SCHEMA = "research_notebook_task.v1"
_CITATION_LINE_WARNING_CHARS = 2_000
_SOURCE_HEADER = (
    "# Sources\n\n"
    "<!-- Managed by ResearchFoundry. Use the notebook source boundary. -->\n"
)
_STABLE_ID = TypeAdapter(StableId)


class ResearchNotebookError(ValueError):
    """Raised when a free-form research notebook violates a mechanical boundary."""


@dataclass(frozen=True, slots=True)
class NotebookIdentity:
    """Small machine-owned identity header embedded in task.md."""

    research_id: str
    domain: str
    subject: str
    as_of: date
    research_shape: Literal["bounded", "comprehensive"] = "bounded"
    company_id: str | None = None
    knowledge_policy: Literal["reuse", "raw_only", "isolated"] = "reuse"


@dataclass(frozen=True, slots=True)
class ResearchNotebookWorkspace:
    """Paths owned by one free-form research notebook."""

    workspace_root: Path
    research_root: Path
    identity: NotebookIdentity
    company_root: Path | None = None

    @property
    def notes(self) -> Path:
        return self.research_root / "notes"


@dataclass(frozen=True, slots=True)
class NotebookValidationReport:
    """Compact mechanical result without a research-process schema."""

    valid: bool
    publishable: bool
    research_id: str | None
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    source_count: int
    citation_count: int
    research_shape: str | None = None
    release_scope: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_notebook_identity(
    research_root: str | Path, *, workspace_root: str | Path
) -> NotebookIdentity:
    """Return the checked machine-owned identity for one notebook."""

    _, _, identity = _resolve_notebook(research_root, workspace_root)
    return identity


def initialize_research_notebook(
    workspace_root: str | Path,
    task_path: str | Path,
    *,
    research_id: str,
    domain: str,
    subject: str,
    as_of: date | str,
    research_shape: Literal["bounded", "comprehensive"] = "bounded",
    company_root: str | Path | None = None,
    company_id: str | None = None,
    knowledge_policy: Literal["reuse", "raw_only", "isolated"] = "reuse",
    knowledge_snapshot: Any | None = None,
) -> ResearchNotebookWorkspace:
    """Create or idempotently reopen a free-form notebook research run."""

    workspace = Path(workspace_root).expanduser().resolve()
    task_source = Path(task_path).expanduser()
    if task_source.is_symlink() or not task_source.is_file():
        raise ResearchNotebookError("task input must be a regular Markdown file")
    try:
        task_body = task_source.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError) as error:
        raise ResearchNotebookError(f"unable to read task input: {error}") from error
    if len(re.sub(r"\s+", "", task_body)) < 40:
        raise ResearchNotebookError("task input is not substantive")

    try:
        stable_id = _STABLE_ID.validate_python(research_id)
        cutoff = date.fromisoformat(as_of) if isinstance(as_of, str) else as_of
    except (ValidationError, ValueError) as error:
        raise ResearchNotebookError(f"invalid notebook identity: {error}") from error
    if not domain.strip() or not subject.strip():
        raise ResearchNotebookError("domain and subject must be non-empty")
    if research_shape not in {"bounded", "comprehensive"}:
        raise ResearchNotebookError("research_shape must be bounded or comprehensive")
    identity = NotebookIdentity(
        stable_id,
        domain.strip(),
        subject.strip(),
        cutoff,
        research_shape,
        company_id.strip() if company_id else None,
        knowledge_policy,
    )
    if company_root is not None:
        company_path = Path(company_root).expanduser().resolve()
        if not _is_below(company_path, workspace) and company_path != workspace:
            raise ResearchNotebookError("company_root must stay below workspace root")
        if not company_id:
            raise ResearchNotebookError("company_id is required when company_root is provided")
        root = (
            company_path
            / "research"
            / identity.as_of.isoformat()
            / identity.research_id
        )
    else:
        company_path = None
        root = (
            workspace
            / "artifacts"
            / "research"
            / _safe_segment(identity.domain, fallback_prefix="domain")
            / _safe_segment(identity.subject, fallback_prefix="subject")
            / identity.as_of.isoformat()
            / identity.research_id
        )
    rendered_task = _render_task(identity, task_body)
    task_destination = root / "task.md"
    sources_destination = root / "sources.md"
    if root.exists() and (root / "release_manifest.json").exists():
        raise ResearchNotebookError("published notebook cannot be reinitialized")
    root.mkdir(parents=True, exist_ok=True)
    if task_destination.exists():
        if task_destination.read_text(encoding="utf-8") != rendered_task:
            raise ResearchNotebookError("notebook already contains a different task")
    else:
        task_destination.write_text(rendered_task, encoding="utf-8")
    if not sources_destination.exists():
        sources_destination.write_text(_SOURCE_HEADER, encoding="utf-8")
    (root / "notes").mkdir(exist_ok=True)
    if knowledge_snapshot is not None:
        from .knowledge import write_run_knowledge_snapshot

        write_run_knowledge_snapshot(knowledge_snapshot, root / "knowledge_snapshot.json")
    return ResearchNotebookWorkspace(workspace, root, identity, company_path)


def add_notebook_source(
    research_root: str | Path,
    *,
    source_id: str,
    artifact: str | Path,
    workspace_root: str | Path,
) -> str:
    """Register one existing citation-ready Markdown artifact under a short ID."""

    root, workspace, _ = _resolve_notebook(research_root, workspace_root)
    if (root / "release_manifest.json").exists():
        raise ResearchNotebookError("published notebook cannot accept new sources")
    try:
        stable_id = _STABLE_ID.validate_python(source_id)
    except ValidationError as error:
        raise ResearchNotebookError(f"invalid source_id: {error}") from error

    candidate = Path(artifact).expanduser()
    candidate = candidate if candidate.is_absolute() else workspace / candidate
    if candidate.is_symlink() or not candidate.is_file():
        raise ResearchNotebookError("notebook source must be a regular file")
    source = candidate.resolve()
    if not _is_below(source, workspace):
        raise ResearchNotebookError("notebook source must stay below workspace root")
    try:
        text = source.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ResearchNotebookError(f"notebook source must be UTF-8 text: {error}") from error
    if not text.splitlines():
        raise ResearchNotebookError("notebook source is empty")
    artifact_ref = source.relative_to(workspace).as_posix()

    catalog_path = root / "sources.md"
    catalog = _load_source_catalog(catalog_path)
    existing = catalog.get(stable_id)
    if existing is not None and existing != artifact_ref:
        raise ResearchNotebookError("source_id already points to a different artifact")
    if existing == artifact_ref:
        return artifact_ref
    if artifact_ref in catalog.values():
        raise ResearchNotebookError("artifact is already registered under another source_id")
    catalog[stable_id] = artifact_ref
    rendered = _SOURCE_HEADER + "\n".join(
        f"[source:{key}]: {value}" for key, value in sorted(catalog.items())
    ) + "\n"
    _replace_atomically(rendered.encode("utf-8"), catalog_path)
    return artifact_ref


def validate_research_notebook(
    research_root: str | Path,
    *,
    workspace_root: str | Path,
) -> NotebookValidationReport:
    """Validate only notebook identity, final prose, citations, and source files."""

    errors: list[str] = []
    warnings: list[str] = []
    try:
        root, workspace, identity = _resolve_notebook(research_root, workspace_root)
    except ResearchNotebookError as error:
        return NotebookValidationReport(
            False, False, None, (str(error),), (), 0, 0, None, None
        )

    try:
        catalog = _load_source_catalog(root / "sources.md")
    except ResearchNotebookError as error:
        errors.append(str(error))
        catalog = {}
    if not catalog:
        errors.append("notebook contains no registered sources")

    release_scope = "bounded"
    coverage_record = None
    comprehensive_output = False
    if identity.research_shape == "comprehensive":
        coverage = validate_research_coverage(
            root,
            research_id=identity.research_id,
            known_source_ids=set(catalog),
        )
        errors.extend(f"coverage: {error}" for error in coverage.errors)
        warnings.extend(f"coverage: {warning}" for warning in coverage.warnings)
        release_scope = coverage.release_scope
        try:
            coverage_record = load_research_coverage(root)
            comprehensive_output = uses_comprehensive_output(root)
        except ValueError:
            coverage_record = None
        if coverage_record is not None and comprehensive_output:
            from .ledger import validate_agent_ledger

            ledger = validate_agent_ledger(
                root,
                workspace_root=workspace,
                require_roles=("writer", "reviewer"),
            )
            errors.extend(f"ledger: {error}" for error in ledger.errors)
            warnings.extend(f"ledger: {warning}" for warning in ledger.warnings)

    source_records: dict[str, NotebookSourceRecord] = {}
    source_line_lengths: dict[str, tuple[int, ...]] = {}
    for source_id, artifact_ref in sorted(catalog.items()):
        try:
            source = _inspect_source(
                source_id, artifact_ref, workspace
            )
            source_records[source_id] = source
            source_line_lengths[source_id] = _source_line_lengths(source, workspace)
        except ResearchNotebookError as error:
            errors.append(str(error))

    citations: list[NotebookCitation] = []
    validation_citations: list[NotebookCitation] = []
    final_texts: dict[str, str] = {}
    for document_name, minimum in (("report.md", 200), ("review.md", 100)):
        path = root / document_name
        text = _read_final_text(path, document_name, minimum, errors)
        if text is None:
            continue
        final_texts[document_name] = text
        if comprehensive_output and document_name == "report.md":
            document_citations, malformed = [], False
        else:
            document_citations, malformed = _parse_citations(text, document_name)
        if malformed:
            errors.append(f"{document_name} contains a malformed lightweight citation")
        citations.extend(document_citations)
        validation_citations.extend(document_citations)
    if comprehensive_output:
        try:
            from .reports import load_report_evidence_map, validate_finalized_report

            finalized = validate_finalized_report(root, workspace_root=workspace)
            errors.extend(f"report: {error}" for error in finalized.errors)
            warnings.extend(f"report: {warning}" for warning in finalized.warnings)
            evidence_map = load_report_evidence_map(root)
            for block in evidence_map.blocks:
                for source_ref in block.source_refs:
                    citation = NotebookCitation(
                        document_ref="report.md",
                        source_id=source_ref.source_id,
                        start_line=source_ref.start_line,
                        end_line=source_ref.end_line,
                    )
                    citations.append(citation)
                    validation_citations.append(citation)
            _validate_comprehensive_panels_and_writer(
                root,
                workspace,
                coverage_record,
                evidence_map,
                errors,
            )
        except ValueError as error:
            errors.append(f"report: {error}")
    modern_comprehensive = coverage_record is not None and (
        bool(coverage_record.source_requirements)
        or any(branch.evidence_status is not None for branch in coverage_record.branches)
    )
    if identity.research_shape == "comprehensive" and "report.md" in final_texts:
        report_errors, report_warnings = validate_comprehensive_report(
            root,
            report_text=final_texts["report.md"],
        )
        errors.extend(f"report: {error}" for error in report_errors)
        warnings.extend(f"report: {warning}" for warning in report_warnings)
        if modern_comprehensive and not comprehensive_output:
            errors.extend(
                f"report: {error}"
                for error in _validate_material_numeric_citations(final_texts["report.md"])
            )
    if coverage_record is not None:
        for branch in coverage_record.branches:
            if branch.evidence_status is None or branch.readiness not in {
                "usable",
                "bounded",
                "blocked",
            }:
                continue
            path = root / branch.note_ref
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            note_citations, malformed = _parse_citations(text, branch.note_ref)
            if malformed:
                errors.append(
                    f"{branch.note_ref} contains a malformed lightweight citation"
                )
            validation_citations.extend(note_citations)
        cited_source_ids = {item.source_id for item in validation_citations}
        for requirement in coverage_record.source_requirements:
            if requirement.disposition != "obtained":
                continue
            uncited = set(requirement.source_ids).difference(cited_source_ids)
            if uncited:
                errors.append(
                    "coverage source requirement lists an unused source: "
                    f"{requirement.source_requirement_id} -> {sorted(uncited)[0]}"
                )
    report_citations = [item for item in citations if item.document_ref == "report.md"]
    if not report_citations:
        errors.append("report.md contains no lightweight citations")

    used_sources: set[str] = set()
    locator_warnings: set[str] = set()
    for citation in validation_citations:
        source = source_records.get(citation.source_id)
        if source is None:
            errors.append(
                f"{citation.document_ref} cites unknown source: {citation.source_id}"
            )
            continue
        used_sources.add(citation.source_id)
        if citation.end_line > source.line_count:
            errors.append(
                f"{citation.document_ref} citation exceeds source lines: "
                f"{citation.source_id}:L{citation.start_line}-L{citation.end_line}"
            )
            continue
        lengths = source_line_lengths[citation.source_id]
        cited_lengths = lengths[citation.start_line - 1 : citation.end_line]
        longest_offset, longest_length = max(
            enumerate(cited_lengths), key=lambda item: item[1]
        )
        if longest_length > _CITATION_LINE_WARNING_CHARS:
            line_number = citation.start_line + longest_offset
            locator_warnings.add(
                f"{citation.document_ref} citation targets an unusually long source "
                f"line ({longest_length} characters): "
                f"{citation.source_id}:L{line_number}"
            )
    warnings.extend(sorted(locator_warnings))
    for source_id in sorted(set(source_records).difference(used_sources)):
        warnings.append(
            f"registered source is not cited in report, review, or branch notes: {source_id}"
        )

    if (root / "release_manifest.json").exists():
        try:
            verify_published_notebook(root, workspace_root=workspace)
        except ResearchNotebookError as error:
            errors.append(f"published notebook verification failed: {error}")
    unique_citations = _unique_citations(citations)
    return NotebookValidationReport(
        valid=not errors,
        publishable=not errors,
        research_id=identity.research_id,
        errors=tuple(errors),
        warnings=tuple(warnings),
        source_count=len(source_records),
        citation_count=len(unique_citations),
        research_shape=identity.research_shape,
        release_scope=release_scope,
    )


def publish_research_notebook(
    research_root: str | Path,
    *,
    workspace_root: str | Path,
) -> ResearchNotebookReleaseManifest:
    """Freeze one validated free-form notebook without process-level handoffs."""

    root, workspace, identity = _resolve_notebook(research_root, workspace_root)
    manifest_path = root / "release_manifest.json"
    if manifest_path.exists():
        return verify_published_notebook(root, workspace_root=workspace)
    validation = validate_research_notebook(root, workspace_root=workspace)
    if not validation.publishable:
        detail = validation.errors[0] if validation.errors else "notebook is not publishable"
        raise ResearchNotebookError(f"notebook is not publishable: {detail}")

    catalog = _load_source_catalog(root / "sources.md")
    sources = tuple(
        _inspect_source(source_id, artifact_ref, workspace)
        for source_id, artifact_ref in sorted(catalog.items())
    )
    citations: list[NotebookCitation] = []
    comprehensive_output = (
        identity.research_shape == "comprehensive" and uses_comprehensive_output(root)
    )
    for document_name in (("review.md",) if comprehensive_output else ("report.md", "review.md")):
        text = (root / document_name).read_text(encoding="utf-8")
        values, _ = _parse_citations(text, document_name)
        citations.extend(values)
    if comprehensive_output:
        from .reports import load_report_evidence_map

        for block in load_report_evidence_map(root).blocks:
            citations.extend(
                NotebookCitation(
                    document_ref="report.md",
                    source_id=item.source_id,
                    start_line=item.start_line,
                    end_line=item.end_line,
                )
                for item in block.source_refs
            )
    artifacts = tuple(_published_artifact(path, root) for path in _release_files(root))
    manifest = ResearchNotebookReleaseManifest(
        research_id=identity.research_id,
        domain=identity.domain,
        subject=identity.subject,
        as_of=identity.as_of,
        published_at=datetime.now(UTC),
        research_shape=identity.research_shape,
        release_scope=validation.release_scope or "bounded",
        sources=sources,
        citations=_unique_citations(citations),
        artifacts=artifacts,
    )
    publish_bytes((manifest.model_dump_json(indent=2) + "\n").encode("utf-8"), manifest_path)
    return verify_published_notebook(root, workspace_root=workspace)


def _validate_comprehensive_panels_and_writer(
    root: Path,
    workspace: Path,
    coverage: Any,
    evidence_map: Any,
    errors: list[str],
) -> None:
    """Apply current comprehensive panel consumption and independent Writer gates."""

    from .panels import load_research_panel, validate_research_panel
    from .ledger import load_agent_ledger

    try:
        specs = load_method_panel_specs(root)
    except ValueError as error:
        errors.append(f"panel catalog: {error}")
        return
    referenced_panels = {
        panel_ref.panel_id
        for block in evidence_map.blocks
        for panel_ref in block.panel_refs
    }
    note_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((root / "notes").glob("*.md"))
        if path.name != "report_draft.md" and path.is_file() and not path.is_symlink()
    )
    delegated_refs = {
        branch.agent_ref
        for branch in coverage.branches
        if branch.agent_ref is not None
    }
    try:
        ledger = load_agent_ledger(root, workspace_root=workspace)
        completed_writers = {
            entry.agent_ref
            for entry in ledger.entries
            if entry.role == "writer" and entry.status == "completed" and entry.agent_ref
        }
        completed_reviewers = [
            entry
            for entry in ledger.entries
            if entry.role == "reviewer" and entry.status == "completed"
        ]
        if evidence_map.writer_ref not in completed_writers:
            errors.append("report Writer is not the completed ledger Writer")
        if not any("review.md" in entry.owned_files for entry in completed_reviewers):
            errors.append("completed ledger Reviewer does not own review.md")
    except ValueError as error:
        errors.append(f"agent ledger: {error}")
    if evidence_map.writer_ref in delegated_refs:
        errors.append("report Writer must be independent from research branch Agents")
    for spec in specs.values():
        panel_path = root / "panels" / f"{spec.panel_id}.json"
        if not panel_path.is_file():
            unavailable = root / "panels" / f"{spec.panel_id}.unavailable.md"
            if spec.requirement == "required" and not (
                coverage.release_scope == "limited" and unavailable.is_file()
            ):
                errors.append(f"required research panel is missing: {spec.panel_id}")
            continue
        validation = validate_research_panel(root, spec.panel_id, workspace_root=workspace)
        errors.extend(f"panel {spec.panel_id}: {item}" for item in validation.errors)
        try:
            panel = load_research_panel(root, spec.panel_id)
        except ValueError as error:
            errors.append(str(error))
            continue
        panel_sections = {row.section for row in panel.rows if row.section is not None}
        missing_sections = set(spec.required_sections).difference(panel_sections)
        if missing_sections:
            errors.append(
                f"panel is missing required section: {spec.panel_id} -> "
                f"{sorted(missing_sections)[0]}"
            )
        if spec.requirement == "required" and spec.panel_id not in referenced_panels:
            errors.append(f"required panel is not consumed by the final report: {spec.panel_id}")
        if spec.requirement == "required" and not re.search(
            rf"<!--\s*rf:uses-panel={re.escape(spec.panel_id)}\s*-->", note_text
        ):
            errors.append(f"required panel is not consumed by an upstream analysis note: {spec.panel_id}")
        try:
            build = json.loads(
                (root / "panels" / f"{spec.panel_id}.build.json").read_text(encoding="utf-8")
            )
            if build.get("owner_ref") == evidence_map.writer_ref:
                errors.append(f"report Writer cannot own required panel: {spec.panel_id}")
        except (OSError, ValueError, json.JSONDecodeError):
            pass


def verify_published_notebook(
    research_root: str | Path,
    *,
    workspace_root: str | Path,
) -> ResearchNotebookReleaseManifest:
    """Verify notebook files, linked evidence, and resolved citation inventory."""

    root, workspace, identity = _resolve_notebook(research_root, workspace_root)
    manifest_path = root / "release_manifest.json"
    try:
        manifest = ResearchNotebookReleaseManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
    except (OSError, ValueError) as error:
        raise ResearchNotebookError(f"invalid notebook release manifest: {error}") from error
    if (
        manifest.research_id != identity.research_id
        or manifest.domain != identity.domain
        or manifest.subject != identity.subject
        or manifest.as_of != identity.as_of
        or manifest.research_shape != identity.research_shape
    ):
        raise ResearchNotebookError("notebook manifest identity does not match task.md")
    catalog = _load_source_catalog(root / "sources.md")
    if identity.research_shape == "comprehensive":
        coverage_validation = validate_research_coverage(
            root,
            research_id=identity.research_id,
            known_source_ids=set(catalog),
        )
        if not coverage_validation.valid:
            raise ResearchNotebookError(
                f"published notebook coverage failed: {coverage_validation.errors[0]}"
            )
        coverage_record = load_research_coverage(root)
        if manifest.release_scope != coverage_validation.release_scope:
            raise ResearchNotebookError("notebook manifest release_scope changed")
        if uses_comprehensive_output(root):
            from .ledger import validate_agent_ledger

            ledger = validate_agent_ledger(
                root,
                workspace_root=workspace,
                require_roles=("writer", "reviewer"),
            )
            if not ledger.valid:
                raise ResearchNotebookError(
                    f"published notebook ledger failed: {ledger.errors[0]}"
                )

    expected_files = {path.relative_to(root).as_posix() for path in _release_files(root)}
    recorded_files = {item.artifact_ref for item in manifest.artifacts}
    if expected_files != recorded_files:
        raise ResearchNotebookError("notebook file inventory does not match manifest")
    for artifact in manifest.artifacts:
        path = (root / artifact.artifact_ref).resolve()
        if not _is_below(path, root) or path.is_symlink() or not path.is_file():
            raise ResearchNotebookError(
                f"unsafe or missing notebook artifact: {artifact.artifact_ref}"
            )
        actual = hash_file(path)
        if actual.sha256 != artifact.sha256 or actual.byte_size != artifact.byte_size:
            raise ResearchNotebookError(
                f"notebook artifact identity mismatch: {artifact.artifact_ref}"
            )

    current_sources = tuple(
        _inspect_source(source_id, artifact_ref, workspace)
        for source_id, artifact_ref in sorted(catalog.items())
    )
    if current_sources != manifest.sources:
        raise ResearchNotebookError("notebook source identity changed after publication")
    current_citations: list[NotebookCitation] = []
    comprehensive_output = (
        identity.research_shape == "comprehensive" and uses_comprehensive_output(root)
    )
    for document_name in (("review.md",) if comprehensive_output else ("report.md", "review.md")):
        text = (root / document_name).read_text(encoding="utf-8")
        values, malformed = _parse_citations(text, document_name)
        if malformed:
            raise ResearchNotebookError(
                f"{document_name} contains a malformed lightweight citation"
            )
        current_citations.extend(values)
    if comprehensive_output:
        from .reports import load_report_evidence_map, validate_finalized_report

        finalized = validate_finalized_report(root, workspace_root=workspace)
        if not finalized.valid:
            raise ResearchNotebookError(
                f"published finalized report failed: {finalized.errors[0]}"
            )
        evidence_map = load_report_evidence_map(root)
        for block in evidence_map.blocks:
            current_citations.extend(
                NotebookCitation(
                    document_ref="report.md",
                    source_id=item.source_id,
                    start_line=item.start_line,
                    end_line=item.end_line,
                )
                for item in block.source_refs
            )
        coverage_record = load_research_coverage(root)
        report_errors: list[str] = []
        _validate_comprehensive_panels_and_writer(
            root,
            workspace,
            coverage_record,
            evidence_map,
            report_errors,
        )
        if report_errors:
            raise ResearchNotebookError(report_errors[0])
    if _unique_citations(current_citations) != manifest.citations:
        raise ResearchNotebookError("notebook citation inventory changed after publication")
    return manifest


def _resolve_notebook(
    research_root: str | Path, workspace_root: str | Path
) -> tuple[Path, Path, NotebookIdentity]:
    root_input = Path(research_root).expanduser()
    if root_input.is_symlink():
        raise ResearchNotebookError(
            "research notebook must be a regular directory below workspace root"
        )
    root = root_input.resolve()
    workspace = Path(workspace_root).expanduser().resolve()
    if not _is_below(root, workspace) or not root.is_dir():
        raise ResearchNotebookError(
            "research notebook must be a regular directory below workspace root"
        )
    identity = _load_task_identity(root / "task.md")
    if root.name != identity.research_id:
        raise ResearchNotebookError("notebook directory does not match research_id")
    return root, workspace, identity


def _render_task(identity: NotebookIdentity, body: str) -> str:
    payload = {
        "schema_version": _TASK_SCHEMA,
        "research_id": identity.research_id,
        "domain": identity.domain,
        "subject": identity.subject,
        "as_of": identity.as_of.isoformat(),
        "research_shape": identity.research_shape,
    }
    if identity.company_id is not None:
        payload["company_id"] = identity.company_id
        payload["knowledge_policy"] = identity.knowledge_policy
    metadata = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{metadata}\n---\n\n{body}\n"


def _load_task_identity(path: Path) -> NotebookIdentity:
    if path.is_symlink() or not path.is_file():
        raise ResearchNotebookError("notebook is missing task.md")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ResearchNotebookError(f"unable to read task.md: {error}") from error
    if not text.startswith("---\n"):
        raise ResearchNotebookError("task.md is missing its machine-owned identity header")
    boundary = text.find("\n---\n", 4)
    if boundary < 0:
        raise ResearchNotebookError("task.md has an invalid identity header")
    try:
        payload = yaml.safe_load(text[4:boundary])
        if not isinstance(payload, dict) or payload.get("schema_version") != _TASK_SCHEMA:
            raise ValueError("unsupported task header")
        stable_id = _STABLE_ID.validate_python(payload["research_id"])
        domain = str(payload["domain"]).strip()
        subject = str(payload["subject"]).strip()
        cutoff = date.fromisoformat(str(payload["as_of"]))
        research_shape = str(payload.get("research_shape", "bounded"))
        if research_shape not in {"bounded", "comprehensive"}:
            raise ValueError("unsupported research_shape")
    except (KeyError, TypeError, ValueError, ValidationError, yaml.YAMLError) as error:
        raise ResearchNotebookError(f"invalid task.md identity header: {error}") from error
    if not domain or not subject:
        raise ResearchNotebookError("task.md domain and subject must be non-empty")
    body = text[boundary + 5 :]
    if len(re.sub(r"\s+", "", body)) < 40:
        raise ResearchNotebookError("task.md body is not substantive")
    company_id = payload.get("company_id")
    policy = str(payload.get("knowledge_policy", "reuse"))
    if company_id is not None:
        company_id = str(company_id).strip()
    if policy not in {"reuse", "raw_only", "isolated"}:
        raise ResearchNotebookError("unsupported knowledge_policy")
    return NotebookIdentity(stable_id, domain, subject, cutoff, research_shape, company_id, policy)


def _load_source_catalog(path: Path) -> dict[str, str]:
    if path.is_symlink() or not path.is_file():
        raise ResearchNotebookError("notebook is missing sources.md")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise ResearchNotebookError(f"unable to read sources.md: {error}") from error
    catalog: dict[str, str] = {}
    for line_number, line in enumerate(lines, start=1):
        match = _SOURCE_DEFINITION.fullmatch(line.strip())
        if match is None:
            if line.lstrip().startswith("[source:"):
                raise ResearchNotebookError(
                    f"invalid source definition on sources.md line {line_number}"
                )
            continue
        source_id, artifact_ref = match.groups()
        if source_id in catalog:
            raise ResearchNotebookError(f"duplicate source_id in sources.md: {source_id}")
        catalog[source_id] = artifact_ref
    return catalog


def _inspect_source(
    source_id: str, artifact_ref: str, workspace: Path
) -> NotebookSourceRecord:
    candidate = workspace / artifact_ref
    if candidate.is_symlink() or not candidate.is_file():
        raise ResearchNotebookError(f"unsafe or missing notebook source: {source_id}")
    path = candidate.resolve()
    if not _is_below(path, workspace):
        raise ResearchNotebookError(f"notebook source escapes workspace: {source_id}")
    try:
        line_count = len(path.read_text(encoding="utf-8").splitlines())
    except (OSError, UnicodeDecodeError) as error:
        raise ResearchNotebookError(
            f"notebook source must be UTF-8 text ({source_id}): {error}"
        ) from error
    if line_count < 1:
        raise ResearchNotebookError(f"notebook source is empty: {source_id}")
    identity = hash_file(path)
    return NotebookSourceRecord(
        source_id=source_id,
        artifact_ref=artifact_ref,
        artifact_sha256=identity.sha256,
        byte_size=identity.byte_size,
        line_count=line_count,
    )


def _source_line_lengths(
    source: NotebookSourceRecord, workspace: Path
) -> tuple[int, ...]:
    path = (workspace / source.artifact_ref).resolve()
    try:
        return tuple(len(line) for line in path.read_text(encoding="utf-8").splitlines())
    except (OSError, UnicodeDecodeError) as error:
        raise ResearchNotebookError(
            f"unable to inspect notebook source lines ({source.source_id}): {error}"
        ) from error


def _read_final_text(
    path: Path, label: str, minimum: int, errors: list[str]
) -> str | None:
    if path.is_symlink():
        errors.append(f"{label} cannot be a symlink")
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        errors.append(f"invalid or missing {label}: {error}")
        return None
    if len(re.sub(r"\s+", "", text)) < minimum:
        errors.append(f"{label} is not substantive")
    if _PLACEHOLDER.search(text):
        errors.append(f"{label} contains a placeholder")
    return text


def _parse_citations(
    text: str, document_ref: str
) -> tuple[list[NotebookCitation], bool]:
    citations: list[NotebookCitation] = []
    for match in _CITATION.finditer(text):
        source_id, start, end = match.groups()
        citations.append(
            NotebookCitation(
                document_ref=document_ref,
                source_id=source_id,
                start_line=int(start),
                end_line=int(end or start),
            )
        )
    scrubbed = _CITATION.sub("", text)
    return citations, "[[" in scrubbed or "]]" in scrubbed


def _validate_material_numeric_citations(text: str) -> tuple[str, ...]:
    """Require primary locators beside material numbers in comprehensive prose."""

    errors: list[str] = []
    blocks = re.split(r"\n\s*\n", text)
    material_number = re.compile(
        r"(?:[$€£]\s*\(?[0-9]|\b[0-9][0-9,.]*\s*(?:%|bps\b|bp\b|million\b|billion\b|trillion\b|bn\b))",
        re.IGNORECASE,
    )
    for offset, block in enumerate(blocks):
        index = offset + 1
        visible = re.sub(r"<!--.*?-->", "", block, flags=re.DOTALL).strip()
        if not visible or visible.startswith("#") and "\n" not in visible:
            continue
        if not material_number.search(visible):
            continue
        if _CITATION.search(visible):
            continue
        if offset + 1 < len(blocks):
            following = blocks[offset + 1].strip()
            if re.match(r"^(?:source|sources|来源|资料来源)\s*[:：]", following, re.IGNORECASE):
                if _CITATION.search(following):
                    continue
        excerpt = re.sub(r"\s+", " ", visible)[:100]
        errors.append(
            f"material numeric block {index} lacks a lightweight source citation: {excerpt}"
        )
    return tuple(errors)


def _unique_citations(
    citations: list[NotebookCitation],
) -> tuple[NotebookCitation, ...]:
    values = {
        (item.document_ref, item.source_id, item.start_line, item.end_line): item
        for item in citations
    }
    return tuple(values[key] for key in sorted(values))


def _published_artifact(path: Path, root: Path) -> PublishedArtifact:
    identity = hash_file(path)
    return PublishedArtifact(
        artifact_ref=path.relative_to(root).as_posix(),
        sha256=identity.sha256,
        byte_size=identity.byte_size,
    )


def _release_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ResearchNotebookError(
                f"notebook release cannot contain symlink: {path.relative_to(root)}"
            )
        if not path.is_file() or path.name == "release_manifest.json":
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def _replace_atomically(data: bytes, destination: Path) -> None:
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
