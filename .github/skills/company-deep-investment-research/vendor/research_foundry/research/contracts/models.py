"""Strict, deliberately small contracts for research handoffs."""

from datetime import date, datetime
from decimal import Decimal
from pathlib import PurePosixPath
import re
from typing import Annotated, Literal
from urllib.parse import urlparse

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Sha256Hex = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
_WINDOWS_RESERVED = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{number}" for number in range(1, 10)),
    *(f"lpt{number}" for number in range(1, 10)),
}


def _validate_stable_id(value: str) -> str:
    if value.casefold() in _WINDOWS_RESERVED:
        raise ValueError("identifier is reserved on Windows")
    return value


StableId = Annotated[
    str,
    StringConstraints(strip_whitespace=True, pattern=r"^[A-Za-z][A-Za-z0-9_-]{2,95}$"),
    AfterValidator(_validate_stable_id),
]
CatalogId = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, pattern=r"^[A-Za-z][A-Za-z0-9_.-]{2,95}$"
    ),
    AfterValidator(_validate_stable_id),
]
NonEmptyTuple = Annotated[tuple[NonEmptyStr, ...], Field(min_length=1)]


class ContractModel(BaseModel):
    """Shared strictness for persisted research contracts."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


def _unique(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must contain unique values")
    return values


def _validate_relative_posix_ref(value: str, field_name: str) -> str:
    if "\\" in value or re.match(r"^[A-Za-z]:", value):
        raise ValueError(f"{field_name} must use a relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(
        part in {"", ".", ".."} for part in path.parts
    ):
        raise ValueError(f"{field_name} must stay below the research root")
    return value


class ResearchScope(ContractModel):
    """Only the task boundaries needed by downstream research work."""

    subjects: NonEmptyTuple
    included: tuple[NonEmptyStr, ...] = ()
    excluded: tuple[NonEmptyStr, ...] = ()

    @model_validator(mode="after")
    def validate_scope(self) -> "ResearchScope":
        _unique(self.subjects, "subjects")
        _unique(self.included, "included")
        _unique(self.excluded, "excluded")
        overlap = set(self.included).intersection(self.excluded)
        if overlap:
            raise ValueError(f"scope cannot both include and exclude: {sorted(overlap)[0]}")
        return self


class ResearchBrief(ContractModel):
    """Decision question and boundaries for one research run."""

    schema_version: Literal["research_brief.v1"] = "research_brief.v1"
    research_id: StableId
    domain: NonEmptyStr
    decision_question: NonEmptyStr
    as_of: date
    scope: ResearchScope
    deliverables: NonEmptyTuple
    constraints: tuple[NonEmptyStr, ...] = ()
    material_questions: NonEmptyTuple
    release_criteria: NonEmptyTuple

    @model_validator(mode="after")
    def validate_lists(self) -> "ResearchBrief":
        _unique(self.deliverables, "deliverables")
        _unique(self.constraints, "constraints")
        _unique(self.material_questions, "material_questions")
        _unique(self.release_criteria, "release_criteria")
        return self


class WorkPackageBrief(ContractModel):
    """One independently verifiable, conclusion-sensitive question."""

    schema_version: Literal["work_package_brief.v1"] = "work_package_brief.v1"
    package_id: StableId
    question: NonEmptyStr
    why_it_matters: NonEmptyStr
    dependencies: tuple[StableId, ...] = ()
    expected_outputs: NonEmptyTuple
    closure_criteria: NonEmptyTuple
    falsifiers: NonEmptyTuple

    @model_validator(mode="after")
    def validate_package(self) -> "WorkPackageBrief":
        _unique(self.dependencies, "dependencies")
        _unique(self.expected_outputs, "expected_outputs")
        _unique(self.closure_criteria, "closure_criteria")
        _unique(self.falsifiers, "falsifiers")
        if self.package_id in self.dependencies:
            raise ValueError("work package cannot depend on itself")
        return self


class EvidenceRef(ContractModel):
    """Exact lines in one immutable artifact below the user workspace."""

    artifact_ref: NonEmptyStr
    artifact_sha256: Sha256Hex
    start_line: Annotated[int, Field(ge=1)]
    end_line: Annotated[int, Field(ge=1)]

    @field_validator("artifact_ref")
    @classmethod
    def validate_artifact_ref(cls, value: str) -> str:
        if "\\" in value or re.match(r"^[A-Za-z]:", value):
            raise ValueError("artifact_ref must use a workspace-relative POSIX path")
        path = PurePosixPath(value)
        if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
            raise ValueError("artifact_ref must stay below the workspace root")
        return value

    @model_validator(mode="after")
    def validate_line_range(self) -> "EvidenceRef":
        if self.end_line < self.start_line:
            raise ValueError("end_line must be greater than or equal to start_line")
        return self


class ResearchSourceMetadata(ContractModel):
    """Agent-supplied provenance for one externally acquired research source."""

    schema_version: Literal["research_source_metadata.v1"] = "research_source_metadata.v1"
    source_id: StableId
    title: NonEmptyStr
    publisher: NonEmptyStr
    source_type: Literal[
        "regulatory_filing",
        "official_website",
        "government",
        "industry_data",
        "transcript",
        "news",
        "research",
        "other",
    ]
    source_url: NonEmptyStr | None = None
    published_at: date | None = None
    retrieved_at: datetime
    acquisition_method: Literal[
        "browser",
        "web_search",
        "mcp",
        "api",
        "http_download",
        "manual",
        "other",
    ]
    notes: tuple[NonEmptyStr, ...] = ()

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value: str | None) -> str | None:
        if value is None:
            return value
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("source_url must be an absolute HTTP(S) URL")
        if parsed.username or parsed.password:
            raise ValueError("source_url cannot contain credentials")
        return value

    @field_validator("retrieved_at")
    @classmethod
    def validate_retrieved_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("retrieved_at must include a timezone")
        return value

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _unique(value, "notes")


class ResearchSourceManifest(ContractModel):
    """Frozen identity and provenance for one run-local research source."""

    schema_version: Literal["research_source_manifest.v1"] = "research_source_manifest.v1"
    source_id: StableId
    title: NonEmptyStr
    publisher: NonEmptyStr
    source_type: Literal[
        "regulatory_filing",
        "official_website",
        "government",
        "industry_data",
        "transcript",
        "news",
        "research",
        "other",
    ]
    source_url: NonEmptyStr | None = None
    published_at: date | None = None
    retrieved_at: datetime
    acquisition_method: Literal[
        "browser",
        "web_search",
        "mcp",
        "api",
        "http_download",
        "manual",
        "other",
    ]
    content_status: Literal["raw_only", "evidence_ready"]
    raw_artifact: "PublishedArtifact"
    prepared_artifact: "PublishedArtifact | None" = None
    notes: tuple[NonEmptyStr, ...] = ()

    @model_validator(mode="after")
    def validate_content_status(self) -> "ResearchSourceManifest":
        if self.content_status == "evidence_ready" and self.prepared_artifact is None:
            raise ValueError("evidence_ready source requires prepared_artifact")
        if self.content_status == "raw_only" and self.prepared_artifact is not None:
            raise ValueError("raw_only source cannot contain prepared_artifact")
        return self


class ResearchClaim(ContractModel):
    """One material claim handed to another package or the final report."""

    schema_version: Literal["research_claim.v1"] = "research_claim.v1"
    claim_id: StableId
    statement: NonEmptyStr
    claim_type: Literal["fact", "calculation", "interpretation", "forecast"]
    evidence: Annotated[tuple[EvidenceRef, ...], Field(min_length=1)]
    period: NonEmptyStr | None = None
    unit: NonEmptyStr | None = None
    perimeter: NonEmptyStr | None = None
    counterevidence: tuple[EvidenceRef, ...] = ()
    confidence: Literal["high", "medium", "low"]

    @model_validator(mode="after")
    def require_numeric_context(self) -> "ResearchClaim":
        if self.claim_type in {"calculation", "forecast"}:
            missing = [
                field_name
                for field_name in ("period", "unit", "perimeter")
                if not getattr(self, field_name)
            ]
            if missing:
                raise ValueError(
                    f"{self.claim_type} claim requires {', '.join(missing)}"
                )
        return self


class QuantitativeModelInput(ContractModel):
    """One evidence-bound numeric input used by a research model."""

    schema_version: Literal["quantitative_model_input.v1"] = "quantitative_model_input.v1"
    input_id: StableId
    metric: NonEmptyStr
    value: Decimal
    period: NonEmptyStr
    unit: NonEmptyStr
    entity: NonEmptyStr
    perimeter: NonEmptyStr
    data_state: Literal["reported", "adjusted", "derived", "guidance", "model", "scenario"]
    definition: NonEmptyStr
    formula: NonEmptyStr | None = None
    scenario: NonEmptyStr | None = None
    evidence: Annotated[tuple[EvidenceRef, ...], Field(min_length=1)]

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: Decimal) -> Decimal:
        if not value.is_finite():
            raise ValueError("model input value must be finite")
        return value

    @model_validator(mode="after")
    def validate_state(self) -> "QuantitativeModelInput":
        if self.data_state in {"derived", "model", "scenario"} and self.formula is None:
            raise ValueError(f"{self.data_state} model input requires formula")
        if self.data_state == "scenario" and self.scenario is None:
            raise ValueError("scenario model input requires scenario")
        if self.data_state != "scenario" and self.scenario is not None:
            raise ValueError("scenario is only valid for scenario model inputs")
        return self


class QuantitativeCheckTerm(ContractModel):
    """One coefficient and input in a declared linear model identity."""

    input_id: StableId
    coefficient: Decimal

    @field_validator("coefficient")
    @classmethod
    def validate_coefficient(cls, value: Decimal) -> Decimal:
        if not value.is_finite() or value == 0:
            raise ValueError("check coefficient must be finite and non-zero")
        return value


class QuantitativeCheckSpec(ContractModel):
    """A deterministic linear reconciliation declared by the research Agent."""

    check_id: StableId
    category: Literal["segment_reconciliation", "cash_bridge", "formula", "scenario", "other"]
    description: NonEmptyStr
    terms: Annotated[tuple[QuantitativeCheckTerm, ...], Field(min_length=2)]
    expected_value: Decimal = Decimal("0")
    tolerance: Annotated[Decimal, Field(ge=0)] = Decimal("0")
    period: NonEmptyStr | None = None
    unit: NonEmptyStr | None = None
    perimeter: NonEmptyStr | None = None

    @model_validator(mode="after")
    def validate_terms(self) -> "QuantitativeCheckSpec":
        ids = tuple(term.input_id for term in self.terms)
        _unique(ids, "check terms")
        if not self.expected_value.is_finite() or not self.tolerance.is_finite():
            raise ValueError("check expected value and tolerance must be finite")
        return self


class QuantitativeChartSeries(ContractModel):
    """One ordered series selected from bound model inputs."""

    name: NonEmptyStr
    input_ids: Annotated[tuple[StableId, ...], Field(min_length=1)]

    @field_validator("input_ids")
    @classmethod
    def validate_input_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _unique(value, "chart input_ids")


class QuantitativeChartSpec(ContractModel):
    """A report-ready chart generated from explicit model input IDs."""

    chart_id: StableId
    title: NonEmptyStr
    chart_type: Literal["line", "column"]
    unit: NonEmptyStr
    series: Annotated[tuple[QuantitativeChartSeries, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_series(self) -> "QuantitativeChartSpec":
        _unique(tuple(series.name for series in self.series), "chart series names")
        return self


class QuantitativeModelSpec(ContractModel):
    """Agent-authored model purpose, checks, and chart selections."""

    schema_version: Literal["quantitative_model_spec.v1"] = "quantitative_model_spec.v1"
    model_id: StableId
    research_id: StableId
    purpose: NonEmptyStr
    checks: Annotated[tuple[QuantitativeCheckSpec, ...], Field(min_length=1)]
    charts: Annotated[tuple[QuantitativeChartSpec, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_ids(self) -> "QuantitativeModelSpec":
        _unique(tuple(check.check_id for check in self.checks), "check IDs")
        _unique(tuple(chart.chart_id for chart in self.charts), "chart IDs")
        return self


class QuantitativeCheckResult(ContractModel):
    """One recomputed model check result."""

    check_id: StableId
    category: Literal["segment_reconciliation", "cash_bridge", "formula", "scenario", "other"]
    description: NonEmptyStr
    status: Literal["passed", "failed"]
    observed_value: Decimal
    expected_value: Decimal
    difference: Decimal
    tolerance: Annotated[Decimal, Field(ge=0)]
    input_ids: Annotated[tuple[StableId, ...], Field(min_length=2)]


class QuantitativeModelChecks(ContractModel):
    """Deterministic output from declared quantitative model checks."""

    schema_version: Literal["quantitative_model_checks.v1"] = "quantitative_model_checks.v1"
    model_id: StableId
    all_passed: bool
    results: Annotated[tuple[QuantitativeCheckResult, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_summary(self) -> "QuantitativeModelChecks":
        _unique(tuple(result.check_id for result in self.results), "check result IDs")
        if self.all_passed != all(result.status == "passed" for result in self.results):
            raise ValueError("all_passed does not match check results")
        return self


class QuantitativeModelManifest(ContractModel):
    """Frozen generated artifacts and boundaries for one quantitative model."""

    schema_version: Literal["quantitative_model_manifest.v1"] = "quantitative_model_manifest.v1"
    model_id: StableId
    research_id: StableId
    purpose: NonEmptyStr
    input_count: Annotated[int, Field(ge=1)]
    check_count: Annotated[int, Field(ge=1)]
    chart_count: Annotated[int, Field(ge=1)]
    artifacts: Annotated[tuple["PublishedArtifact", ...], Field(min_length=4)]

    @model_validator(mode="after")
    def validate_artifacts(self) -> "QuantitativeModelManifest":
        _unique(tuple(artifact.artifact_ref for artifact in self.artifacts), "model artifacts")
        return self


class WorkPackageResult(ContractModel):
    """Compact handoff from one completed or stopped research package."""

    schema_version: Literal["work_package_result.v1"] = "work_package_result.v1"
    package_id: StableId
    status: Literal["completed", "needs_followup", "blocked"]
    conclusion: NonEmptyStr
    material_claim_ids: tuple[StableId, ...] = ()
    key_calculations: tuple[NonEmptyStr, ...] = ()
    open_gaps: tuple[NonEmptyStr, ...] = ()
    downstream_implications: tuple[NonEmptyStr, ...] = ()
    recommended_followups: tuple[NonEmptyStr, ...] = ()

    @model_validator(mode="after")
    def validate_status(self) -> "WorkPackageResult":
        _unique(self.material_claim_ids, "material_claim_ids")
        if self.status == "completed" and not self.material_claim_ids:
            raise ValueError("completed package requires at least one material claim")
        if self.status == "needs_followup" and not self.recommended_followups:
            raise ValueError("needs_followup package requires recommended_followups")
        if self.status == "blocked" and not (self.open_gaps or self.recommended_followups):
            raise ValueError("blocked package requires a gap or follow-up")
        return self


class ResearchQualityReport(ContractModel):
    """Research Lead's qualitative release assessment."""

    schema_version: Literal["research_quality_report.v1"] = "research_quality_report.v1"
    research_id: StableId
    research_ready: bool
    lead_assessment: Literal["sufficient", "limited", "not_ready"]
    material_gaps: tuple[NonEmptyStr, ...] = ()
    limitations: tuple[NonEmptyStr, ...] = ()
    remaining_uncertainties: tuple[NonEmptyStr, ...] = ()
    warnings: tuple[NonEmptyStr, ...] = ()
    independently_challenged_claim_ids: tuple[StableId, ...] = ()

    @model_validator(mode="after")
    def validate_readiness(self) -> "ResearchQualityReport":
        _unique(self.independently_challenged_claim_ids, "independently_challenged_claim_ids")
        if self.research_ready:
            if self.lead_assessment != "sufficient":
                raise ValueError("research_ready requires a sufficient lead assessment")
            if self.material_gaps:
                raise ValueError("research_ready cannot retain material_gaps")
            if not self.independently_challenged_claim_ids:
                raise ValueError("research_ready requires at least one independently challenged claim")
        elif self.lead_assessment == "sufficient":
            raise ValueError("sufficient lead assessment requires research_ready")
        return self


class ResearchMethodResponsibility(ContractModel):
    """One material research responsibility offered by a method catalog."""

    responsibility_id: StableId
    title: NonEmptyStr
    description: NonEmptyStr
    requirement: Literal["required", "conditional"]


class ResearchMethodDimension(ContractModel):
    """One candidate question to review without prescribing an answer."""

    dimension_id: StableId
    responsibility_id: StableId
    core_question: NonEmptyStr
    selection_guidance: NonEmptyStr
    completion_signal: NonEmptyStr
    requirement: Literal["review"] = "review"


class ResearchMethodSourceRequirement(ContractModel):
    """One evidence category that a comprehensive run must explicitly dispose."""

    source_requirement_id: StableId
    title: NonEmptyStr
    description: NonEmptyStr
    requirement: Literal["required", "conditional"]


class ResearchMethodReportTable(ContractModel):
    """One decision-useful table required inside a comprehensive report topic."""

    table_id: StableId
    title: NonEmptyStr
    description: NonEmptyStr
    table_layout: Literal["freeform", "metric_by_period"] = "freeform"


class ResearchMethodReportSubtopic(ContractModel):
    """One method-pack writing cue below a report topic."""

    subtopic_id: StableId
    title: NonEmptyStr
    description: NonEmptyStr


class ResearchMethodReportTopic(ContractModel):
    """One substantive topic required in the final comprehensive report."""

    topic_id: StableId
    title: NonEmptyStr
    description: NonEmptyStr
    subtopics: tuple[ResearchMethodReportSubtopic, ...] = ()
    tables: tuple[ResearchMethodReportTable, ...] = ()

    @model_validator(mode="after")
    def validate_tables(self) -> "ResearchMethodReportTopic":
        _unique(tuple(item.subtopic_id for item in self.subtopics), "report subtopic IDs")
        _unique(tuple(item.table_id for item in self.tables), "report table IDs")
        return self


class ResearchMethodPanelSpec(ContractModel):
    """One quantitative panel required by a method pack."""

    panel_id: StableId
    panel_type: StableId
    title: NonEmptyStr
    description: NonEmptyStr
    requirement: Literal["required", "conditional"]
    required_sections: tuple[StableId, ...] = ()
    required_metric_groups: tuple[tuple[StableId, ...], ...] = ()

    @model_validator(mode="after")
    def validate_required_sections(self) -> "ResearchMethodPanelSpec":
        _unique(self.required_sections, "required panel sections")
        for group in self.required_metric_groups:
            if not group:
                raise ValueError("required metric groups cannot be empty")
            _unique(group, "required metric group IDs")
        return self


class ResearchMethodCatalog(ContractModel):
    """Industry or business-model questions available to comprehensive research."""

    schema_version: Literal["research_method_catalog.v1"] = (
        "research_method_catalog.v1"
    )
    catalog_id: CatalogId
    title: NonEmptyStr
    applies_to: Literal["comprehensive_company_research"]
    responsibilities: tuple[ResearchMethodResponsibility, ...] = ()
    dimensions: tuple[ResearchMethodDimension, ...] = ()
    source_requirements: tuple[ResearchMethodSourceRequirement, ...] = ()
    report_topics: tuple[ResearchMethodReportTopic, ...] = ()
    panel_specs: tuple[ResearchMethodPanelSpec, ...] = ()

    @model_validator(mode="after")
    def validate_catalog(self) -> "ResearchMethodCatalog":
        _unique(
            tuple(item.responsibility_id for item in self.responsibilities),
            "method responsibility IDs",
        )
        _unique(
            tuple(item.dimension_id for item in self.dimensions),
            "method dimension IDs",
        )
        _unique(
            tuple(item.source_requirement_id for item in self.source_requirements),
            "method source requirement IDs",
        )
        _unique(
            tuple(item.topic_id for item in self.report_topics),
            "method report topic IDs",
        )
        _unique(
            tuple(
                subtopic.subtopic_id
                for topic in self.report_topics
                for subtopic in topic.subtopics
            ),
            "method report subtopic IDs",
        )
        _unique(
            tuple(
                table.table_id
                for topic in self.report_topics
                for table in topic.tables
            ),
            "method report table IDs",
        )
        _unique(
            tuple(item.panel_id for item in self.panel_specs),
            "method panel IDs",
        )
        return self


class CoverageCatalogSnapshot(ContractModel):
    """Tool-owned identity for one method catalog frozen into a research run."""

    catalog_id: CatalogId
    snapshot_ref: NonEmptyStr
    snapshot_sha256: Sha256Hex

    @field_validator("snapshot_ref")
    @classmethod
    def validate_snapshot_ref(cls, value: str) -> str:
        return _validate_relative_posix_ref(value, "snapshot_ref")


class CoverageResponsibility(ContractModel):
    """Task-specific disposition of one catalog responsibility."""

    responsibility_id: StableId
    disposition: Literal["unreviewed", "selected", "not_material", "blocked"]
    rationale: NonEmptyStr | None = None

    @model_validator(mode="after")
    def validate_disposition(self) -> "CoverageResponsibility":
        if self.disposition in {"not_material", "blocked"} and self.rationale is None:
            raise ValueError(f"{self.disposition} responsibility requires rationale")
        return self


class CoverageBranch(ContractModel):
    """One semantic research branch and its persisted free-form note."""

    branch_id: StableId
    responsibility_id: StableId
    question: NonEmptyStr
    depends_on: tuple[StableId, ...] = ()
    execution_mode: Literal["delegated", "lead"]
    agent_ref: NonEmptyStr | None = None
    exception: NonEmptyStr | None = None
    note_ref: NonEmptyStr
    readiness: Literal["planned", "in_progress", "usable", "bounded", "blocked"]
    evidence_status: Literal[
        "unreviewed", "evidence_ready", "bounded_gap", "blocked"
    ] | None = None
    limitation: NonEmptyStr | None = None

    @field_validator("note_ref")
    @classmethod
    def validate_note_ref(cls, value: str) -> str:
        _validate_relative_posix_ref(value, "note_ref")
        path = PurePosixPath(value)
        if path.parts[0] != "notes" or path.suffix.casefold() != ".md":
            raise ValueError("note_ref must identify Markdown below notes/")
        return value

    @model_validator(mode="after")
    def validate_branch(self) -> "CoverageBranch":
        _unique(self.depends_on, "branch dependencies")
        if self.branch_id in self.depends_on:
            raise ValueError("coverage branch cannot depend on itself")
        if self.readiness == "blocked" and self.limitation is None:
            raise ValueError("blocked branch requires limitation")
        if self.evidence_status in {"bounded_gap", "blocked"} and self.limitation is None:
            raise ValueError(f"{self.evidence_status} branch requires limitation")
        return self


class DimensionDisposition(ContractModel):
    """Task-specific selection of one catalog candidate question."""

    dimension_id: StableId
    disposition: Literal["unreviewed", "selected", "not_material", "blocked"]
    branch_id: StableId | None = None
    rationale: NonEmptyStr | None = None

    @model_validator(mode="after")
    def validate_disposition(self) -> "DimensionDisposition":
        if self.disposition in {"selected", "blocked"} and self.branch_id is None:
            raise ValueError(f"{self.disposition} dimension requires branch_id")
        if self.disposition in {"not_material", "blocked"} and self.rationale is None:
            raise ValueError(f"{self.disposition} dimension requires rationale")
        if self.disposition in {"unreviewed", "not_material"} and self.branch_id is not None:
            raise ValueError(f"{self.disposition} dimension cannot have branch_id")
        return self


class CoverageSourceRequirement(ContractModel):
    """Run-specific disposition of one required evidence category."""

    source_requirement_id: StableId
    disposition: Literal[
        "unreviewed", "obtained", "unavailable", "failed", "not_material"
    ]
    source_ids: tuple[StableId, ...] = ()
    rationale: NonEmptyStr | None = None

    @model_validator(mode="after")
    def validate_disposition(self) -> "CoverageSourceRequirement":
        _unique(self.source_ids, "coverage source IDs")
        if self.disposition == "obtained" and not self.source_ids:
            raise ValueError("obtained source requirement requires source_ids")
        if self.disposition != "obtained" and self.source_ids:
            raise ValueError(f"{self.disposition} source requirement cannot have source_ids")
        if self.disposition in {"unavailable", "failed", "not_material"} and self.rationale is None:
            raise ValueError(f"{self.disposition} source requirement requires rationale")
        return self


class ResearchCoverage(ContractModel):
    """Small comprehensive-research coverage and release-scope boundary."""

    schema_version: Literal["research_coverage.v1"] = "research_coverage.v1"
    research_id: StableId
    research_shape: Literal["comprehensive"] = "comprehensive"
    catalogs: Annotated[tuple[CoverageCatalogSnapshot, ...], Field(min_length=1)]
    responsibilities: Annotated[
        tuple[CoverageResponsibility, ...], Field(min_length=1)
    ]
    branches: Annotated[tuple[CoverageBranch, ...], Field(min_length=1)]
    dimensions: Annotated[tuple[DimensionDisposition, ...], Field(min_length=1)]
    source_requirements: tuple[CoverageSourceRequirement, ...] = ()
    release_scope: Literal["comprehensive", "limited"] = "comprehensive"

    @model_validator(mode="after")
    def validate_coverage(self) -> "ResearchCoverage":
        _unique(tuple(item.catalog_id for item in self.catalogs), "coverage catalog IDs")
        responsibility_ids = tuple(
            item.responsibility_id for item in self.responsibilities
        )
        branch_ids = tuple(item.branch_id for item in self.branches)
        dimension_ids = tuple(item.dimension_id for item in self.dimensions)
        source_requirement_ids = tuple(
            item.source_requirement_id for item in self.source_requirements
        )
        _unique(responsibility_ids, "coverage responsibility IDs")
        _unique(branch_ids, "coverage branch IDs")
        _unique(dimension_ids, "coverage dimension IDs")
        _unique(source_requirement_ids, "coverage source requirement IDs")
        responsibility_set = set(responsibility_ids)
        branch_set = set(branch_ids)
        for branch in self.branches:
            if branch.responsibility_id not in responsibility_set:
                raise ValueError(
                    f"branch references unknown responsibility: {branch.responsibility_id}"
                )
            unknown = set(branch.depends_on).difference(branch_set)
            if unknown:
                raise ValueError(
                    f"branch dependency does not exist: {sorted(unknown)[0]}"
                )
        for dimension in self.dimensions:
            if dimension.branch_id is not None and dimension.branch_id not in branch_set:
                raise ValueError(
                    f"dimension references unknown branch: {dimension.branch_id}"
                )
        _validate_acyclic_branches(self.branches)
        return self


def _validate_acyclic_branches(branches: tuple[CoverageBranch, ...]) -> None:
    dependencies = {item.branch_id: set(item.depends_on) for item in branches}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(branch_id: str) -> None:
        if branch_id in visited:
            return
        if branch_id in visiting:
            raise ValueError(f"coverage branch dependency cycle includes: {branch_id}")
        visiting.add(branch_id)
        for dependency in dependencies[branch_id]:
            visit(dependency)
        visiting.remove(branch_id)
        visited.add(branch_id)

    for branch_id in dependencies:
        visit(branch_id)


class AgentLedgerEntry(ContractModel):
    """One persisted Harness assignment and its execution state."""

    assignment_id: StableId
    role: Literal["research", "writer", "reviewer"]
    branch_id: StableId | None = None
    responsibility_id: StableId | None = None
    agent_ref: NonEmptyStr | None = None
    depends_on: tuple[StableId, ...] = ()
    owned_files: tuple[NonEmptyStr, ...] = ()
    note_ref: NonEmptyStr | None = None
    attempt: Annotated[int, Field(ge=1)] = 1
    status: Literal[
        "planned",
        "started",
        "checkpointed",
        "completed",
        "failed",
        "interrupted",
        "blocked",
    ] = "planned"
    started_at: datetime | None = None
    updated_at: datetime
    finished_at: datetime | None = None
    error: NonEmptyStr | None = None

    @field_validator("owned_files")
    @classmethod
    def validate_owned_files(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            _validate_relative_posix_ref(item, "owned_files")
        return _unique(value, "owned_files")

    @field_validator("note_ref")
    @classmethod
    def validate_note_ref(cls, value: str | None) -> str | None:
        if value is not None:
            _validate_relative_posix_ref(value, "note_ref")
        return value

    @model_validator(mode="after")
    def validate_entry(self) -> "AgentLedgerEntry":
        _unique(self.depends_on, "agent dependencies")
        if self.role == "research" and self.branch_id is None:
            raise ValueError("research ledger entry requires branch_id")
        if self.status in {
            "started",
            "checkpointed",
            "completed",
            "failed",
            "interrupted",
            "blocked",
        } and self.agent_ref is None:
            raise ValueError(f"{self.status} ledger entry requires agent_ref")
        if self.status != "planned" and self.started_at is None:
            raise ValueError(f"{self.status} ledger entry requires started_at")
        if self.status in {"completed", "failed", "interrupted", "blocked"}:
            if self.finished_at is None:
                raise ValueError(f"{self.status} ledger entry requires finished_at")
        if self.status in {"failed", "blocked"} and self.error is None:
            raise ValueError(f"{self.status} ledger entry requires error")
        if self.finished_at is not None and self.started_at is not None:
            if self.finished_at < self.started_at:
                raise ValueError("finished_at cannot precede started_at")
        return self


class AgentLedger(ContractModel):
    """Tool-owned execution ledger for delegated research, Writer, and review."""

    schema_version: Literal["research_agent_ledger.v1"] = "research_agent_ledger.v1"
    research_id: StableId
    updated_at: datetime
    entries: Annotated[tuple[AgentLedgerEntry, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_entries(self) -> "AgentLedger":
        _unique(tuple(item.assignment_id for item in self.entries), "assignment IDs")
        keys = [
            (item.role, item.branch_id, item.attempt)
            for item in self.entries
            if item.branch_id is not None
        ]
        if len(keys) != len(set(keys)):
            raise ValueError("ledger contains duplicate role/branch/attempt entries")
        entry_ids = {item.assignment_id for item in self.entries}
        for item in self.entries:
            unknown = set(item.depends_on).difference(entry_ids)
            if unknown:
                raise ValueError(
                    f"agent dependency does not exist: {item.assignment_id} -> "
                    f"{sorted(unknown)[0]}"
                )
        return self


class PublishedArtifact(ContractModel):
    """Content identity for one file frozen by the release manifest."""

    artifact_ref: NonEmptyStr
    sha256: Sha256Hex
    byte_size: Annotated[int, Field(ge=0)]


class NotebookSourceRecord(ContractModel):
    """Identity of one Markdown source registered by a research notebook."""

    source_id: StableId
    artifact_ref: NonEmptyStr
    artifact_sha256: Sha256Hex
    byte_size: Annotated[int, Field(ge=1)]
    line_count: Annotated[int, Field(ge=1)]

    @field_validator("artifact_ref")
    @classmethod
    def validate_artifact_ref(cls, value: str) -> str:
        if "\\" in value or re.match(r"^[A-Za-z]:", value):
            raise ValueError("artifact_ref must use a workspace-relative POSIX path")
        path = PurePosixPath(value)
        if path.is_absolute() or not path.parts or any(
            part in {"", ".", ".."} for part in path.parts
        ):
            raise ValueError("artifact_ref must stay below the workspace root")
        return value


class NotebookCitation(ContractModel):
    """One lightweight Markdown citation resolved during notebook publication."""

    document_ref: NonEmptyStr
    source_id: StableId
    start_line: Annotated[int, Field(ge=1)]
    end_line: Annotated[int, Field(ge=1)]

    @model_validator(mode="after")
    def validate_line_range(self) -> "NotebookCitation":
        _validate_relative_posix_ref(self.document_ref, "document_ref")
        if PurePosixPath(self.document_ref).suffix.casefold() != ".md":
            raise ValueError("document_ref must identify Markdown")
        if self.end_line < self.start_line:
            raise ValueError("end_line must be greater than or equal to start_line")
        return self


class PanelSourceRef(ContractModel):
    """One exact registered-source locator used by a panel value."""

    source_id: StableId
    start_line: Annotated[int, Field(ge=1)]
    end_line: Annotated[int, Field(ge=1)]

    @model_validator(mode="after")
    def validate_line_range(self) -> "PanelSourceRef":
        if self.end_line < self.start_line:
            raise ValueError("end_line must be greater than or equal to start_line")
        return self


class ResearchPanelValue(ContractModel):
    """One period value with explicit disclosure and comparability state."""

    period: NonEmptyStr
    value: Decimal | None = None
    status: Literal[
        "reported",
        "derived",
        "not_disclosed",
        "not_comparable",
        "not_applicable",
    ]
    source_refs: tuple[PanelSourceRef, ...] = ()
    formula: NonEmptyStr | None = None
    note: NonEmptyStr | None = None

    @model_validator(mode="after")
    def validate_value_state(self) -> "ResearchPanelValue":
        if self.status in {"reported", "derived"}:
            if self.value is None:
                raise ValueError(f"{self.status} panel value requires value")
            if not self.source_refs:
                raise ValueError(f"{self.status} panel value requires source_refs")
        elif self.value is not None:
            raise ValueError(f"{self.status} panel value cannot contain value")
        if self.status == "derived" and self.formula is None:
            raise ValueError("derived panel value requires formula")
        if self.status != "derived" and self.formula is not None:
            raise ValueError(f"{self.status} panel value cannot contain formula")
        if self.status in {"not_disclosed", "not_comparable"} and self.note is None:
            raise ValueError(f"{self.status} panel value requires note")
        if self.status == "not_comparable" and not self.source_refs:
            raise ValueError("not_comparable panel value requires source_refs")
        return self


class ResearchPanelRow(ContractModel):
    """One semantically adjudicated metric across panel periods."""

    metric_id: StableId
    label: NonEmptyStr
    section: StableId | None = None
    scope: NonEmptyStr
    unit: NonEmptyStr | None = None
    values: Annotated[tuple[ResearchPanelValue, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_values(self) -> "ResearchPanelRow":
        _unique(tuple(item.period for item in self.values), "panel row periods")
        return self


class ResearchPanel(ContractModel):
    """Auditable metric-by-period panel without research conclusions."""

    schema_version: Literal["research_panel.v1"] = "research_panel.v1"
    panel_id: StableId
    panel_type: StableId
    title: NonEmptyStr
    periods: Annotated[tuple[NonEmptyStr, ...], Field(min_length=1)]
    default_unit: NonEmptyStr | None = None
    rows: Annotated[tuple[ResearchPanelRow, ...], Field(min_length=1)]
    comparability_notes: tuple[NonEmptyStr, ...] = ()
    missing_periods: tuple[NonEmptyStr, ...] = ()

    @model_validator(mode="after")
    def validate_panel(self) -> "ResearchPanel":
        _unique(self.periods, "panel periods")
        _unique(tuple(item.metric_id for item in self.rows), "panel metric IDs")
        _unique(self.missing_periods, "missing_periods")
        unknown_missing = set(self.missing_periods).difference(self.periods)
        if unknown_missing:
            raise ValueError(f"missing period is outside panel periods: {sorted(unknown_missing)[0]}")
        period_set = set(self.periods)
        for row in self.rows:
            unknown = {item.period for item in row.values}.difference(period_set)
            if unknown:
                raise ValueError(
                    f"panel row references unknown period: {row.metric_id} -> {sorted(unknown)[0]}"
                )
        if any(
            value.status == "not_comparable"
            for row in self.rows
            for value in row.values
        ) and not self.comparability_notes:
            raise ValueError("not_comparable values require comparability_notes")
        for period in self.missing_periods:
            if not any(period in note for note in self.comparability_notes):
                raise ValueError(
                    f"missing period requires a period-specific comparability note: {period}"
                )
        return self


class ReportPanelRef(ContractModel):
    """One final-report block dependency on a quantitative panel."""

    panel_id: StableId
    metric_ids: Annotated[tuple[StableId, ...], Field(min_length=1)]
    periods: Annotated[tuple[NonEmptyStr, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_refs(self) -> "ReportPanelRef":
        _unique(self.metric_ids, "report panel metric IDs")
        _unique(self.periods, "report panel periods")
        return self


class ReportEvidenceSourceRef(PanelSourceRef):
    """One report-block source locator and its evidentiary role."""

    evidence_role: Literal[
        "support", "context", "management_attribution", "calculation_input"
    ] = "support"


class ReportEvidenceBlock(ContractModel):
    """Evidence bindings for one stable final-report block."""

    block_id: StableId
    topic_id: StableId
    block_kind: Literal["heading", "prose", "table", "list", "other"]
    source_refs: tuple[ReportEvidenceSourceRef, ...] = ()
    panel_refs: tuple[ReportPanelRef, ...] = ()


class ReportEvidenceMap(ContractModel):
    """Hidden traceability from a clean report to sources and panels."""

    schema_version: Literal["report_evidence_map.v1"] = "report_evidence_map.v1"
    research_id: StableId
    report_ref: NonEmptyStr = "report.md"
    report_sha256: Sha256Hex
    draft_ref: NonEmptyStr = "notes/report_draft.md"
    draft_sha256: Sha256Hex
    writer_ref: NonEmptyStr
    blocks: Annotated[tuple[ReportEvidenceBlock, ...], Field(min_length=1)]

    @field_validator("report_ref", "draft_ref")
    @classmethod
    def validate_artifact_ref(cls, value: str, info: object) -> str:
        return _validate_relative_posix_ref(value, str(getattr(info, "field_name", "artifact_ref")))

    @model_validator(mode="after")
    def validate_blocks(self) -> "ReportEvidenceMap":
        _unique(tuple(item.block_id for item in self.blocks), "report evidence block IDs")
        return self


class ResearchNotebookReleaseManifest(ContractModel):
    """Immutable release boundary for free-form notebook research."""

    schema_version: Literal["research_notebook_release.v1"] = (
        "research_notebook_release.v1"
    )
    research_id: StableId
    domain: NonEmptyStr
    subject: NonEmptyStr
    as_of: date
    published_at: datetime
    research_shape: Literal["bounded", "comprehensive"] = "bounded"
    release_scope: Literal["bounded", "comprehensive", "limited"] = "bounded"
    quality_status: Literal["mechanically_valid", "research_ready"] = (
        "mechanically_valid"
    )
    sources: Annotated[tuple[NotebookSourceRecord, ...], Field(min_length=1)]
    citations: Annotated[tuple[NotebookCitation, ...], Field(min_length=1)]
    artifacts: Annotated[tuple[PublishedArtifact, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_manifest(self) -> "ResearchNotebookReleaseManifest":
        if self.research_shape == "bounded" and self.release_scope != "bounded":
            raise ValueError("bounded notebook requires bounded release_scope")
        if self.research_shape == "comprehensive" and self.release_scope == "bounded":
            raise ValueError("comprehensive notebook cannot use bounded release_scope")
        _unique(tuple(item.source_id for item in self.sources), "notebook source IDs")
        _unique(
            tuple(item.artifact_ref for item in self.sources),
            "notebook source artifacts",
        )
        _unique(tuple(item.artifact_ref for item in self.artifacts), "notebook artifacts")
        return self


class ResearchReleaseManifest(ContractModel):
    """Complete immutable file inventory for a research release."""

    schema_version: Literal["research_release_manifest.v1"] = "research_release_manifest.v1"
    research_id: StableId
    domain: NonEmptyStr
    as_of: date
    published_at: datetime
    quality_status: Literal["research_ready"] = "research_ready"
    package_ids: Annotated[tuple[StableId, ...], Field(min_length=1)]
    key_claim_ids: Annotated[tuple[StableId, ...], Field(min_length=1)]
    artifacts: Annotated[tuple[PublishedArtifact, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_manifest(self) -> "ResearchReleaseManifest":
        _unique(self.package_ids, "package_ids")
        _unique(self.key_claim_ids, "key_claim_ids")
        refs = tuple(item.artifact_ref for item in self.artifacts)
        _unique(refs, "artifacts")
        return self
