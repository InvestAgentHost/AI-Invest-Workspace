"""Deterministic coverage boundary for comprehensive research notebooks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Any, Iterable

from pydantic import ValidationError
import yaml

from research_foundry.runtime.artifacts import hash_file, publish_bytes

from .contracts import (
    CoverageBranch,
    CoverageCatalogSnapshot,
    CoverageResponsibility,
    CoverageSourceRequirement,
    DimensionDisposition,
    ResearchCoverage,
    ResearchMethodCatalog,
    ResearchMethodDimension,
    ResearchMethodReportTopic,
    ResearchMethodPanelSpec,
    ResearchMethodResponsibility,
    ResearchMethodSourceRequirement,
)


_PLACEHOLDER = re.compile(
    r"(?:\bTODO\b|\bTBD\b|\[Agent synthesis required\])", re.IGNORECASE
)
_MINIMUM_NOTE_CHARACTERS = 200
_MINIMUM_EVIDENCE_NOTE_CHARACTERS = 800
_MINIMUM_SYNTHESIS_NOTE_CHARACTERS = 1_000
_LIGHTWEIGHT_CITATION = re.compile(
    r"\[\[([A-Za-z][A-Za-z0-9_-]{2,95}):L([1-9][0-9]*)(?:-L([1-9][0-9]*))?\]\]"
)
_DIRECT_WEB_LINK = re.compile(r"https?://", re.IGNORECASE)
_REPORT_TOPIC_MARKER = re.compile(
    r"<!--\s*rf:topic=([A-Za-z][A-Za-z0-9_-]{2,95})\s*-->"
)
_REPORT_TABLE_MARKER = re.compile(
    r"<!--\s*rf:table=([A-Za-z][A-Za-z0-9_-]{2,95})\s*-->"
)


class ResearchCoverageError(ValueError):
    """Raised when a comprehensive coverage boundary is unsafe or inconsistent."""


@dataclass(frozen=True, slots=True)
class CoverageValidationReport:
    """Mechanical coverage result without assessing research conclusions."""

    valid: bool
    release_scope: str | None
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    catalog_count: int
    responsibility_count: int
    branch_count: int
    dimension_count: int
    source_requirement_count: int = 0
    report_topic_count: int = 0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class _MarkdownTable:
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


def load_method_catalog(path: str | Path) -> ResearchMethodCatalog:
    """Load one strict method catalog from a regular YAML file."""

    source = Path(path).expanduser()
    if source.is_symlink() or not source.is_file():
        raise ResearchCoverageError("method catalog must be a regular YAML file")
    try:
        payload = yaml.safe_load(source.read_text(encoding="utf-8"))
        return ResearchMethodCatalog.model_validate(payload)
    except (OSError, UnicodeDecodeError, yaml.YAMLError, ValidationError) as error:
        raise ResearchCoverageError(f"invalid method catalog {source}: {error}") from error


def initialize_research_coverage(
    research_root: str | Path,
    *,
    research_id: str,
    catalog_paths: Iterable[str | Path],
    workspace_root: str | Path,
) -> ResearchCoverage:
    """Freeze selected catalogs and create an unfinished comprehensive skeleton."""

    root = _resolve_research_root(research_root, workspace_root=workspace_root)
    if (root / "release_manifest.json").exists():
        raise ResearchCoverageError("published notebook cannot initialize coverage")
    coverage_path = root / "research_coverage.yaml"
    if coverage_path.exists() or coverage_path.is_symlink():
        raise ResearchCoverageError("research coverage is already initialized")

    sources = tuple(Path(item).expanduser() for item in catalog_paths)
    if not sources:
        raise ResearchCoverageError("coverage initialization requires a method catalog")
    loaded_items = [(source, load_method_catalog(source)) for source in sources]
    loaded_ids = {catalog.catalog_id for _, catalog in loaded_items}
    loaded = tuple(loaded_items)
    responsibilities, dimensions, source_requirements, report_topics = _merge_catalogs(
        item for _, item in loaded
    )

    catalog_directory = root / "method_catalogs"
    if catalog_directory.is_symlink():
        raise ResearchCoverageError("method_catalogs cannot be a symlink")
    snapshots: list[CoverageCatalogSnapshot] = []
    snapshot_payloads: list[tuple[Path, bytes]] = []
    for source, catalog in loaded:
        try:
            data = source.read_bytes()
        except OSError as error:
            raise ResearchCoverageError(f"unable to read method catalog: {error}") from error
        destination = catalog_directory / f"{catalog.catalog_id}.yaml"
        if destination.exists() or destination.is_symlink():
            raise ResearchCoverageError(
                f"method catalog snapshot already exists: {catalog.catalog_id}"
            )
        snapshot_payloads.append((destination, data))

    for destination, data in snapshot_payloads:
        identity = publish_bytes(data, destination)
        catalog_id = destination.stem
        snapshots.append(
            CoverageCatalogSnapshot(
                catalog_id=catalog_id,
                snapshot_ref=destination.relative_to(root).as_posix(),
                snapshot_sha256=identity.sha256,
            )
        )

    coverage = ResearchCoverage(
        research_id=research_id,
        catalogs=tuple(sorted(snapshots, key=lambda item: item.catalog_id)),
        responsibilities=tuple(
            CoverageResponsibility(
                responsibility_id=item.responsibility_id,
                disposition="unreviewed",
            )
            for item in sorted(
                responsibilities.values(), key=lambda item: item.responsibility_id
            )
        ),
        branches=tuple(
            CoverageBranch(
                branch_id=item.responsibility_id,
                responsibility_id=item.responsibility_id,
                question=item.description,
                execution_mode="delegated",
                note_ref=f"notes/{item.responsibility_id}.md",
                readiness="planned",
                evidence_status="unreviewed",
            )
            for item in sorted(
                responsibilities.values(), key=lambda item: item.responsibility_id
            )
        ),
        dimensions=tuple(
            DimensionDisposition(
                dimension_id=item.dimension_id,
                disposition="unreviewed",
            )
            for item in sorted(dimensions.values(), key=lambda item: item.dimension_id)
        ),
        source_requirements=tuple(
            CoverageSourceRequirement(
                source_requirement_id=item.source_requirement_id,
                disposition="unreviewed",
            )
            for item in sorted(
                source_requirements.values(),
                key=lambda item: item.source_requirement_id,
            )
        ),
    )
    rendered = yaml.safe_dump(
        coverage.model_dump(mode="json"),
        allow_unicode=True,
        sort_keys=False,
    ).encode("utf-8")
    publish_bytes(rendered, coverage_path)
    has_panel_output = any(catalog.panel_specs for _, catalog in loaded)
    report_scaffold = (
        root / "notes" / "report_draft.md"
        if has_panel_output
        else root / "report.md"
    )
    if report_topics and not report_scaffold.exists():
        publish_bytes(
            _render_report_scaffold(report_topics.values()).encode("utf-8"),
            report_scaffold,
        )
    return coverage


def load_research_coverage(research_root: str | Path) -> ResearchCoverage:
    """Load one run-local comprehensive coverage file."""

    root = _resolve_research_root(research_root)
    path = root / "research_coverage.yaml"
    if path.is_symlink() or not path.is_file():
        raise ResearchCoverageError("comprehensive notebook is missing research_coverage.yaml")
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        return ResearchCoverage.model_validate(payload)
    except (OSError, UnicodeDecodeError, yaml.YAMLError, ValidationError) as error:
        raise ResearchCoverageError(f"invalid research_coverage.yaml: {error}") from error


def load_method_panel_specs(
    research_root: str | Path,
) -> dict[str, ResearchMethodPanelSpec]:
    """Return merged panel requirements from the run's frozen method catalogs."""

    root = _resolve_research_root(research_root)
    coverage = load_research_coverage(root)
    specs: dict[str, ResearchMethodPanelSpec] = {}
    for snapshot in coverage.catalogs:
        catalog = load_method_catalog(root / snapshot.snapshot_ref)
        for spec in catalog.panel_specs:
            existing = specs.get(spec.panel_id)
            if existing is not None and existing != spec:
                raise ResearchCoverageError(f"conflicting method panel spec: {spec.panel_id}")
            specs[spec.panel_id] = spec
    return specs


def uses_comprehensive_output(research_root: str | Path) -> bool:
    """Return whether this run froze a catalog with the panel/Writer boundary."""

    return bool(load_method_panel_specs(research_root))


def validate_research_coverage(
    research_root: str | Path,
    *,
    research_id: str,
    known_source_ids: set[str] | None = None,
) -> CoverageValidationReport:
    """Validate catalog identity, dispositions, DAG branches, notes, and scope."""

    errors: list[str] = []
    warnings: list[str] = []
    try:
        root = _resolve_research_root(research_root)
        coverage = load_research_coverage(root)
    except ResearchCoverageError as error:
        return CoverageValidationReport(False, None, (str(error),), (), 0, 0, 0, 0)

    if coverage.research_id != research_id:
        errors.append("coverage research_id does not match task.md")

    catalogs: list[ResearchMethodCatalog] = []
    expected_snapshot_refs = {
        f"method_catalogs/{snapshot.catalog_id}.yaml" for snapshot in coverage.catalogs
    }
    actual_snapshot_refs = {
        path.relative_to(root).as_posix()
        for path in (root / "method_catalogs").glob("*.yaml")
        if path.is_file() and not path.is_symlink()
    }
    if actual_snapshot_refs != expected_snapshot_refs:
        errors.append("method catalog snapshot inventory does not match coverage")
    for snapshot in coverage.catalogs:
        expected_ref = f"method_catalogs/{snapshot.catalog_id}.yaml"
        if snapshot.snapshot_ref != expected_ref:
            errors.append(f"method catalog snapshot path mismatch: {snapshot.catalog_id}")
            continue
        path = root / snapshot.snapshot_ref
        if path.is_symlink() or not path.is_file() or not _is_below(path.resolve(), root):
            errors.append(f"unsafe or missing method catalog snapshot: {snapshot.catalog_id}")
            continue
        identity = hash_file(path)
        if identity.sha256 != snapshot.snapshot_sha256:
            errors.append(f"method catalog snapshot identity changed: {snapshot.catalog_id}")
            continue
        try:
            catalog = load_method_catalog(path)
        except ResearchCoverageError as error:
            errors.append(str(error))
            continue
        if catalog.catalog_id != snapshot.catalog_id:
            errors.append(f"method catalog ID mismatch: {snapshot.catalog_id}")
            continue
        catalogs.append(catalog)

    try:
        (
            expected_responsibilities,
            expected_dimensions,
            expected_source_requirements,
            expected_report_topics,
        ) = _merge_catalogs(catalogs)
    except ResearchCoverageError as error:
        errors.append(str(error))
        expected_responsibilities = {}
        expected_dimensions = {}
        expected_source_requirements = {}
        expected_report_topics = {}

    actual_responsibilities = {
        item.responsibility_id: item for item in coverage.responsibilities
    }
    actual_dimensions = {item.dimension_id: item for item in coverage.dimensions}
    actual_source_requirements = {
        item.source_requirement_id: item for item in coverage.source_requirements
    }
    if set(actual_responsibilities) != set(expected_responsibilities):
        errors.append("coverage responsibilities do not match frozen method catalogs")
    if set(actual_dimensions) != set(expected_dimensions):
        errors.append("coverage dimensions do not match frozen method catalogs")
    if set(actual_source_requirements) != set(expected_source_requirements):
        errors.append("coverage source requirements do not match frozen method catalogs")

    branches_by_responsibility: dict[str, list[CoverageBranch]] = {}
    branch_by_id = {item.branch_id: item for item in coverage.branches}
    modern_coverage = bool(
        expected_source_requirements
        or expected_report_topics
        or any(item.evidence_status is not None for item in coverage.branches)
    )
    note_owners: dict[str, str] = {}
    for branch in coverage.branches:
        branches_by_responsibility.setdefault(branch.responsibility_id, []).append(branch)
        if branch.readiness in {"planned", "in_progress"}:
            errors.append(
                f"branch is not ready for publication: {branch.branch_id} ({branch.readiness})"
            )
        if branch.execution_mode == "delegated" and not branch.agent_ref:
            errors.append(f"delegated branch is missing agent_ref: {branch.branch_id}")
        if branch.execution_mode == "lead" and branch.agent_ref:
            errors.append(f"lead branch cannot declare agent_ref: {branch.branch_id}")
        if branch.evidence_status is None:
            if modern_coverage:
                errors.append(f"branch lacks evidence_status: {branch.branch_id}")
            else:
                warnings.append(
                    "legacy branch lacks evidence_status and receives no evidence gate: "
                    f"{branch.branch_id}"
                )
        elif branch.evidence_status == "unreviewed":
            errors.append(f"branch evidence remains unreviewed: {branch.branch_id}")
        elif branch.readiness == "blocked" and branch.evidence_status != "blocked":
            errors.append(
                f"blocked branch must declare blocked evidence_status: {branch.branch_id}"
            )
        elif branch.readiness in {"usable", "bounded"} and branch.evidence_status == "blocked":
            errors.append(
                f"ready branch cannot declare blocked evidence_status: {branch.branch_id}"
            )
        if branch.readiness in {"usable", "bounded", "blocked"}:
            _validate_branch_note(
                root,
                branch,
                errors,
                warnings,
                enforce_depth=modern_coverage,
            )
        previous_owner = note_owners.get(branch.note_ref)
        if previous_owner is not None and previous_owner != branch.branch_id:
            if modern_coverage and not branch.exception:
                errors.append(
                    "coverage branches reuse note_ref without an exception: "
                    f"{previous_owner}, {branch.branch_id}"
                )
        else:
            note_owners[branch.note_ref] = branch.branch_id

    required_agent_refs: dict[str, str] = {}
    for responsibility_id, method in expected_responsibilities.items():
        disposition = actual_responsibilities.get(responsibility_id)
        if disposition is None:
            continue
        branches = branches_by_responsibility.get(responsibility_id, [])
        if disposition.disposition == "unreviewed":
            errors.append(f"responsibility remains unreviewed: {responsibility_id}")
        if method.requirement == "required" and disposition.disposition == "not_material":
            errors.append(f"required responsibility cannot be not_material: {responsibility_id}")
        if disposition.disposition in {"selected", "blocked"} and not branches:
            errors.append(f"responsibility has no research branch: {responsibility_id}")
        if disposition.disposition == "not_material" and branches:
            errors.append(f"not_material responsibility retains branches: {responsibility_id}")
        if disposition.disposition == "selected" and branches and not any(
            item.readiness in {"usable", "bounded"} for item in branches
        ):
            errors.append(f"selected responsibility has no usable branch: {responsibility_id}")
        if disposition.disposition == "blocked" and any(
            item.readiness != "blocked" for item in branches
        ):
            errors.append(f"blocked responsibility retains a non-blocked branch: {responsibility_id}")

        if method.requirement != "required" or disposition.disposition == "not_material":
            continue
        delegated_refs = {
            item.agent_ref
            for item in branches
            if item.execution_mode == "delegated" and item.agent_ref
        }
        if not delegated_refs:
            if not branches or any(not item.exception for item in branches):
                errors.append(
                    f"required responsibility lacks delegated ownership or exception: {responsibility_id}"
                )
            if coverage.release_scope != "limited":
                errors.append(
                    f"lead-owned required responsibility requires limited scope: {responsibility_id}"
                )
        for agent_ref in delegated_refs:
            other = required_agent_refs.get(agent_ref)
            if other is not None and other != responsibility_id:
                errors.append(
                    "required responsibilities reuse delegated agent_ref: "
                    f"{other}, {responsibility_id}"
                )
            else:
                required_agent_refs[agent_ref] = responsibility_id

    for dimension_id, method in expected_dimensions.items():
        disposition = actual_dimensions.get(dimension_id)
        if disposition is None:
            continue
        if disposition.disposition == "unreviewed":
            errors.append(f"dimension remains unreviewed: {dimension_id}")
        if disposition.branch_id is None:
            continue
        branch = branch_by_id.get(disposition.branch_id)
        if branch is not None and branch.responsibility_id != method.responsibility_id:
            errors.append(
                f"dimension branch responsibility mismatch: {dimension_id}"
            )
    selected_dimensions = [
        item for item in coverage.dimensions if item.disposition == "selected"
    ]
    if modern_coverage and len(coverage.dimensions) >= 10:
        rationales = [item.rationale for item in selected_dimensions if item.rationale]
        if len(selected_dimensions) == len(coverage.dimensions) and not rationales:
            warnings.append(
                "all method dimensions are selected without differentiated rationale"
            )
        if rationales and len(set(rationales)) == 1 and len(rationales) >= 5:
            errors.append(
                "selected dimensions reuse one boilerplate rationale; make task-specific choices"
            )

    for branch in coverage.branches:
        if branch.readiness not in {"usable", "bounded"}:
            continue
        for dependency_id in branch.depends_on:
            dependency = branch_by_id[dependency_id]
            if dependency.readiness not in {"usable", "bounded"}:
                errors.append(
                    f"ready branch depends on an unready branch: {branch.branch_id} -> {dependency_id}"
                )

    source_limited = False
    for requirement_id, method in expected_source_requirements.items():
        disposition = actual_source_requirements.get(requirement_id)
        if disposition is None:
            continue
        if disposition.disposition == "unreviewed":
            errors.append(f"source requirement remains unreviewed: {requirement_id}")
        if method.requirement == "required" and disposition.disposition == "not_material":
            errors.append(f"required source requirement cannot be not_material: {requirement_id}")
        if known_source_ids is not None:
            unknown = set(disposition.source_ids).difference(known_source_ids)
            if unknown:
                errors.append(
                    f"source requirement references unregistered source: {sorted(unknown)[0]}"
                )
        if method.requirement == "required" and disposition.disposition in {
            "unavailable",
            "failed",
        }:
            source_limited = True

    required_blocked = [
        responsibility_id
        for responsibility_id, method in expected_responsibilities.items()
        if method.requirement == "required"
        and actual_responsibilities.get(responsibility_id) is not None
        and actual_responsibilities[responsibility_id].disposition == "blocked"
    ]
    if required_blocked and coverage.release_scope != "limited":
        errors.append("blocked required responsibility requires limited release_scope")
    required_evidence_gaps = [
        branch.branch_id
        for branch in coverage.branches
        if branch.evidence_status == "bounded_gap"
        and expected_responsibilities.get(branch.responsibility_id) is not None
        and expected_responsibilities[branch.responsibility_id].requirement == "required"
    ]
    if required_evidence_gaps and coverage.release_scope != "limited":
        errors.append("required responsibility with an evidence gap requires limited release_scope")
    if source_limited and coverage.release_scope != "limited":
        errors.append("unavailable required evidence category requires limited release_scope")

    return CoverageValidationReport(
        valid=not errors,
        release_scope=coverage.release_scope,
        errors=tuple(errors),
        warnings=tuple(warnings),
        catalog_count=len(catalogs),
        responsibility_count=len(coverage.responsibilities),
        branch_count=len(coverage.branches),
        dimension_count=len(coverage.dimensions),
        source_requirement_count=len(coverage.source_requirements),
        report_topic_count=len(expected_report_topics),
    )


def _merge_catalogs(
    catalogs: Iterable[ResearchMethodCatalog],
) -> tuple[
    dict[str, ResearchMethodResponsibility],
    dict[str, ResearchMethodDimension],
    dict[str, ResearchMethodSourceRequirement],
    dict[str, ResearchMethodReportTopic],
]:
    responsibilities: dict[str, ResearchMethodResponsibility] = {}
    dimensions: dict[str, ResearchMethodDimension] = {}
    source_requirements: dict[str, ResearchMethodSourceRequirement] = {}
    report_topics: dict[str, ResearchMethodReportTopic] = {}
    report_table_ids: set[str] = set()
    catalog_ids: set[str] = set()
    for catalog in catalogs:
        if catalog.catalog_id in catalog_ids:
            raise ResearchCoverageError(f"duplicate method catalog: {catalog.catalog_id}")
        catalog_ids.add(catalog.catalog_id)
        for responsibility in catalog.responsibilities:
            existing = responsibilities.get(responsibility.responsibility_id)
            if existing is not None and existing != responsibility:
                raise ResearchCoverageError(
                    "conflicting method responsibility: "
                    f"{responsibility.responsibility_id}"
                )
            responsibilities[responsibility.responsibility_id] = responsibility
        for dimension in catalog.dimensions:
            if dimension.dimension_id in dimensions:
                raise ResearchCoverageError(
                    f"duplicate method dimension: {dimension.dimension_id}"
                )
            dimensions[dimension.dimension_id] = dimension
        for requirement in catalog.source_requirements:
            existing = source_requirements.get(requirement.source_requirement_id)
            if existing is not None and existing != requirement:
                raise ResearchCoverageError(
                    "conflicting method source requirement: "
                    f"{requirement.source_requirement_id}"
                )
            source_requirements[requirement.source_requirement_id] = requirement
        for topic in catalog.report_topics:
            if topic.topic_id in report_topics:
                raise ResearchCoverageError(
                    f"duplicate method report topic: {topic.topic_id}"
                )
            for table in topic.tables:
                if table.table_id in report_table_ids:
                    raise ResearchCoverageError(
                        f"duplicate method report table: {table.table_id}"
                    )
                report_table_ids.add(table.table_id)
            report_topics[topic.topic_id] = topic
    if not responsibilities:
        raise ResearchCoverageError("selected method catalogs define no responsibilities")
    for dimension in dimensions.values():
        if dimension.responsibility_id not in responsibilities:
            raise ResearchCoverageError(
                "method dimension references unknown responsibility: "
                f"{dimension.dimension_id}"
            )
    return responsibilities, dimensions, source_requirements, report_topics


def _validate_branch_note(
    root: Path,
    branch: CoverageBranch,
    errors: list[str],
    warnings: list[str],
    *,
    enforce_depth: bool,
) -> None:
    candidate = root / branch.note_ref
    if candidate.is_symlink() or not candidate.is_file():
        errors.append(f"branch note is missing or unsafe: {branch.branch_id}")
        return
    path = candidate.resolve()
    if not _is_below(path, root):
        errors.append(f"branch note escapes research root: {branch.branch_id}")
        return
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        errors.append(f"unable to read branch note {branch.branch_id}: {error}")
        return
    minimum = _MINIMUM_NOTE_CHARACTERS
    if enforce_depth:
        minimum = (
            _MINIMUM_SYNTHESIS_NOTE_CHARACTERS
            if branch.execution_mode == "lead" and branch.depends_on
            else _MINIMUM_EVIDENCE_NOTE_CHARACTERS
        )
    character_count = len(re.sub(r"\s+", "", text))
    if character_count < minimum:
        errors.append(f"branch note is not substantive: {branch.branch_id}")
    if _PLACEHOLDER.search(text):
        errors.append(f"branch note contains a placeholder: {branch.branch_id}")
    citations = tuple(_LIGHTWEIGHT_CITATION.finditer(text))
    if branch.evidence_status == "evidence_ready" and not citations:
        errors.append(
            f"evidence-ready branch note contains no registered citation: {branch.branch_id}"
        )
    if branch.evidence_status == "evidence_ready" and _DIRECT_WEB_LINK.search(text):
        errors.append(
            f"evidence-ready branch note contains direct web links; freeze and cite them: {branch.branch_id}"
        )
    elif _DIRECT_WEB_LINK.search(text):
        warnings.append(
            f"branch note contains direct web links that are not publication evidence: {branch.branch_id}"
        )


def validate_comprehensive_report(
    research_root: str | Path,
    *,
    report_text: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Validate catalog-defined report topics and tables without grading conclusions."""

    errors: list[str] = []
    warnings: list[str] = []
    root = _resolve_research_root(research_root)
    coverage = load_research_coverage(root)
    catalogs: list[ResearchMethodCatalog] = []
    for snapshot in coverage.catalogs:
        path = root / snapshot.snapshot_ref
        try:
            catalogs.append(load_method_catalog(path))
        except ResearchCoverageError as error:
            errors.append(str(error))
    try:
        _, _, _, topics = _merge_catalogs(catalogs)
    except ResearchCoverageError as error:
        return (str(error),), ()
    if not topics:
        return (), ()

    topic_matches = tuple(_REPORT_TOPIC_MARKER.finditer(report_text))
    topic_ids = tuple(match.group(1) for match in topic_matches)
    duplicates = sorted({item for item in topic_ids if topic_ids.count(item) > 1})
    if duplicates:
        errors.append(f"report repeats topic marker: {duplicates[0]}")
    unknown = sorted(set(topic_ids).difference(topics))
    if unknown:
        errors.append(f"report contains unknown topic marker: {unknown[0]}")
    missing = sorted(set(topics).difference(topic_ids))
    if missing:
        errors.append(f"report is missing required topic marker: {missing[0]}")

    for index, match in enumerate(topic_matches):
        topic = topics.get(match.group(1))
        if topic is None:
            continue
        end = topic_matches[index + 1].start() if index + 1 < len(topic_matches) else len(report_text)
        section = report_text[match.end() : end]
        substantive = _strip_html_comments(section)
        prose_lines = [
            line.strip()
            for line in substantive.splitlines()
            if line.strip()
            and not line.lstrip().startswith(("#", "|", "<!--"))
            and not re.fullmatch(r"[-: ]+", line.strip())
        ]
        if _PLACEHOLDER.search(section) or not prose_lines:
            errors.append(f"report topic is empty or only a stub: {topic.topic_id}")
        _validate_report_tables(section, topic, errors)

    return tuple(errors), tuple(warnings)


def _validate_report_tables(
    section: str,
    topic: ResearchMethodReportTopic,
    errors: list[str],
) -> None:
    matches = tuple(_REPORT_TABLE_MARKER.finditer(section))
    markers = tuple(match.group(1) for match in matches)
    expected = {item.table_id: item for item in topic.tables}
    unknown = sorted(set(markers).difference(expected))
    if unknown:
        errors.append(
            f"report topic {topic.topic_id} contains unknown table marker: {unknown[0]}"
        )
    for table_id, requirement in expected.items():
        if markers.count(table_id) != 1:
            errors.append(
                f"report topic {topic.topic_id} requires one table marker: {table_id}"
            )
            continue
        marker_index = markers.index(table_id)
        start = matches[marker_index].end()
        end = matches[marker_index + 1].start() if marker_index + 1 < len(matches) else len(section)
        table_block = _first_markdown_table(section[start:end])
        if table_block is None:
            errors.append(f"report table marker has no Markdown table: {table_id}")
            continue
        if len(table_block.headers) < 2 or not table_block.rows:
            errors.append(f"report table is structurally empty: {table_id}")
        if requirement.table_layout == "metric_by_period":
            _validate_metric_period_orientation(table_id, table_block, errors)
        _validate_financial_table_arithmetic(table_id, table_block, errors)


def _first_markdown_table(text: str) -> _MarkdownTable | None:
    lines = text.splitlines()
    for index in range(len(lines) - 1):
        header = lines[index].strip()
        separator = lines[index + 1].strip()
        if not (header.startswith("|") and header.endswith("|")):
            continue
        if not re.fullmatch(r"\|(?:\s*:?-{3,}:?\s*\|)+", separator):
            continue
        headers = tuple(cell.strip() for cell in header.split("|")[1:-1])
        rows: list[tuple[str, ...]] = []
        for row in lines[index + 2 :]:
            stripped = row.strip()
            if not (stripped.startswith("|") and stripped.endswith("|")):
                break
            cells = tuple(cell.strip() for cell in stripped.split("|")[1:-1])
            rows.append(cells)
        return _MarkdownTable(headers, tuple(rows))
    return None


def _validate_financial_table_arithmetic(
    table_id: str,
    table: _MarkdownTable,
    errors: list[str],
) -> None:
    if table_id == "income_statement":
        _validate_margin_rows(table, errors)
    elif table_id == "balance_sheet":
        _validate_balance_sheet_rows(table, errors)


_PERIOD_HEADER = re.compile(
    r"^(?:fy|q[1-4]|h[12]|ytd|9m|年|季度|财年|期间|日期|date|period|year)"
    r"|(?:19|20)\d{2}(?:[-/]\d{1,2}(?:[-/]\d{1,2})?|\s+(?:q[1-4]|h[12]|ytd|9m))?$",
    re.IGNORECASE,
)


def _looks_like_period(value: str) -> bool:
    normalized = re.sub(r"[\s()（）]", "", value.strip())
    return bool(normalized and _PERIOD_HEADER.match(normalized))


def _validate_metric_period_orientation(
    table_id: str,
    table: _MarkdownTable,
    errors: list[str],
) -> None:
    """Require metric/index rows and period/date columns for historical tables."""

    if not table.rows:
        return
    period_columns = sum(_looks_like_period(header) for header in table.headers[1:])
    period_rows = sum(bool(row) and _looks_like_period(row[0]) for row in table.rows)
    period_first_header = bool(table.headers) and _looks_like_period(table.headers[0])
    if period_first_header or (period_rows > 0 and period_rows >= max(1, len(table.rows) // 2)):
        errors.append(
            f"{table_id} must use metric names as rows/index and periods or dates as columns; "
            "transpose the table before finalization"
        )
        return
    if period_columns == 0:
        errors.append(
            f"{table_id} must expose periods or dates as columns with metric names as rows/index"
        )


def _validate_margin_rows(table: _MarkdownTable, errors: list[str]) -> None:
    revenue = _find_metric_row(table, ("revenue", "net sales", "sales", "营业收入", "销售收入"))
    if revenue is None:
        return
    for profit_names, margin_names, label in (
        (("gross profit", "毛利"), ("gross margin", "毛利率"), "gross margin"),
        (
            ("operating income", "operating profit", "经营利润", "营业利润"),
            ("operating margin", "经营利润率", "营业利润率"),
            "operating margin",
        ),
    ):
        profit = _find_metric_row(table, profit_names)
        margin = _find_metric_row(table, margin_names)
        if profit is None or margin is None:
            continue
        for column in range(1, min(len(revenue), len(profit), len(margin))):
            sales_value = _parse_table_number(revenue[column])
            profit_value = _parse_table_number(profit[column])
            margin_value = _parse_table_number(margin[column])
            if sales_value in {None, 0.0} or profit_value is None or margin_value is None:
                continue
            expected = profit_value / sales_value * 100
            if abs(expected - margin_value) > 0.2:
                period = table.headers[column] if column < len(table.headers) else str(column)
                errors.append(
                    f"income_statement {label} does not recalculate for {period}: "
                    f"reported {margin_value:.2f}% versus {expected:.2f}%"
                )


def _validate_balance_sheet_rows(table: _MarkdownTable, errors: list[str]) -> None:
    assets = _find_metric_row(table, ("total assets", "资产总额", "总资产"))
    liabilities = _find_metric_row(table, ("total liabilities", "负债总额", "总负债"))
    equity = _find_metric_row(
        table,
        ("total equity", "stockholders' equity", "shareholders' equity", "股东权益", "权益总额"),
    )
    if assets is None or liabilities is None or equity is None:
        return
    for column in range(1, min(len(assets), len(liabilities), len(equity))):
        asset_value = _parse_table_number(assets[column])
        liability_value = _parse_table_number(liabilities[column])
        equity_value = _parse_table_number(equity[column])
        if asset_value is None or liability_value is None or equity_value is None:
            continue
        tolerance = max(abs(asset_value) * 0.001, 0.1)
        if abs(asset_value - liability_value - equity_value) > tolerance:
            period = table.headers[column] if column < len(table.headers) else str(column)
            errors.append(
                f"balance_sheet does not balance for {period}: assets {asset_value:g}, "
                f"liabilities plus equity {liability_value + equity_value:g}"
            )


def _find_metric_row(
    table: _MarkdownTable,
    names: tuple[str, ...],
) -> tuple[str, ...] | None:
    normalized_names = {_normalize_metric(name) for name in names}
    for row in table.rows:
        if row and _normalize_metric(row[0]) in normalized_names:
            return row
    return None


def _normalize_metric(value: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]+", " ", value.casefold()).strip()


def _parse_table_number(value: str) -> float | None:
    text = value.strip().replace(",", "").replace("$", "")
    if text in {"", "-", "--", "n/a", "N/A", "nm", "NM"}:
        return None
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1].strip()
    text = text.rstrip("%").strip()
    try:
        number = float(text)
    except ValueError:
        return None
    return -number if negative else number


def _render_report_scaffold(
    topics: Iterable[ResearchMethodReportTopic],
) -> str:
    lines = ["# Comprehensive company research", ""]
    for topic in topics:
        lines.extend(
            [
                f"## {topic.title}",
                "",
                f"<!-- rf:topic={topic.topic_id} -->",
                f"<!-- {topic.description} -->",
                "",
            ]
        )
        for subtopic in topic.subtopics:
            lines.extend(
                [
                    f"### {subtopic.title}",
                    "",
                    f"<!-- {subtopic.description} -->",
                    "",
                ]
            )
        for table in topic.tables:
            lines.extend(
                [
                    f"<!-- rf:table={table.table_id} -->",
                    f"<!-- {table.description} -->",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def _strip_html_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def _resolve_research_root(
    research_root: str | Path, *, workspace_root: str | Path | None = None
) -> Path:
    source = Path(research_root).expanduser()
    if source.is_symlink() or not source.is_dir():
        raise ResearchCoverageError("research root must be a regular directory")
    root = source.resolve()
    if workspace_root is not None:
        workspace = Path(workspace_root).expanduser().resolve()
        if not _is_below(root, workspace):
            raise ResearchCoverageError("research root must stay below workspace root")
    return root


def _is_below(path: Path, root: Path) -> bool:
    return path != root and root in path.parents
