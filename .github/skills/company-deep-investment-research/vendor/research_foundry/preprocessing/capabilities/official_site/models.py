"""Lean contracts for one Agent-directed official-site snapshot."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class OfficialSiteScope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    include: list[str] = Field(
        default_factory=lambda: [
            "business_and_offerings",
            "strategy_and_developments",
            "important_information",
        ]
    )
    exclude: list[str] = Field(default_factory=lambda: ["financial_reports"])
    development_window_months: int = Field(default=24, ge=1, le=120)

    @model_validator(mode="after")
    def require_financial_report_exclusion(self) -> "OfficialSiteScope":
        normalized = {value.strip().casefold() for value in self.exclude}
        if "financial_reports" not in normalized:
            raise ValueError("financial_reports must remain excluded")
        return self


class AgentReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["approved"]
    warnings: list[str] = Field(default_factory=list)


class OfficialSiteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["research_foundry_official_site_request.v1"] = (
        "research_foundry_official_site_request.v1"
    )
    target_name: str = Field(min_length=1, max_length=240)
    as_of: date
    workspace_root: str = Field(min_length=1)
    official_domains: list[str] = Field(min_length=1)
    seed_urls: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    scope: OfficialSiteScope = Field(default_factory=OfficialSiteScope)
    agent_review: AgentReview

    @field_validator("target_name", "workspace_root")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value cannot be blank")
        return stripped

    @field_validator("official_domains")
    @classmethod
    def normalize_domains(cls, values: list[str]) -> list[str]:
        from .discovery import normalize_domain

        normalized = list(dict.fromkeys(normalize_domain(value) for value in values))
        if not normalized:
            raise ValueError("at least one official domain is required")
        return normalized

    @field_validator("seed_urls")
    @classmethod
    def normalize_seeds(cls, values: list[str]) -> list[str]:
        from .discovery import normalize_url

        return list(dict.fromkeys(normalize_url(value) for value in values))

    @field_validator("languages")
    @classmethod
    def normalize_languages(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(value.strip() for value in values if value.strip()))

    @model_validator(mode="after")
    def require_official_seed_domains(self) -> "OfficialSiteRequest":
        from .discovery import is_approved_url

        invalid = [url for url in self.seed_urls if not is_approved_url(url, self.official_domains)]
        if invalid:
            raise ValueError(f"seed URL is outside approved official domains: {invalid[0]}")
        return self


class OfficialSiteCoverageAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    area: str = Field(min_length=1, max_length=240)
    status: Literal["covered", "not_disclosed", "not_applicable"]
    evidence_source_ids: list[str] = Field(default_factory=list)
    notes: str = Field(min_length=1, max_length=2_000)

    @field_validator("area", "notes")
    @classmethod
    def strip_assessment_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("coverage assessment text cannot be blank")
        return stripped

    @model_validator(mode="after")
    def require_covered_evidence(self) -> "OfficialSiteCoverageAssessment":
        if self.status == "covered" and not self.evidence_source_ids:
            raise ValueError("covered assessment requires evidence_source_ids")
        return self


class OfficialSiteCoverageReview(BaseModel):
    """One Agent coverage decision inside an unpublished official-site run."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["research_foundry_official_site_coverage_review.v1"] = (
        "research_foundry_official_site_coverage_review.v1"
    )
    decision: Literal["expand", "complete"]
    selected_urls: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1, max_length=4_000)
    material_gaps: list[str] = Field(default_factory=list)
    coverage_assessment: list[OfficialSiteCoverageAssessment] = Field(default_factory=list)
    non_material_source_reasons: dict[str, str] = Field(default_factory=dict)

    @field_validator("rationale")
    @classmethod
    def strip_rationale(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("rationale cannot be blank")
        return stripped

    @field_validator("material_gaps")
    @classmethod
    def strip_material_gaps(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(value.strip() for value in values if value.strip()))

    @field_validator("non_material_source_reasons")
    @classmethod
    def strip_non_material_reasons(cls, values: dict[str, str]) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for source_id, reason in values.items():
            key = source_id.strip()
            explanation = reason.strip()
            if not key or not explanation:
                raise ValueError("non-material source reasons cannot be blank")
            normalized[key] = explanation
        return normalized

    @model_validator(mode="after")
    def enforce_decision_shape(self) -> "OfficialSiteCoverageReview":
        if self.decision == "expand" and not self.selected_urls:
            raise ValueError("expand decision requires selected_urls")
        if self.decision == "complete" and self.selected_urls:
            raise ValueError("complete decision cannot contain selected_urls")
        if self.decision == "expand" and self.non_material_source_reasons:
            raise ValueError("expand decision cannot accept non-material sources")
        return self


class OfficialSiteSourceImport(BaseModel):
    """Run-local source acquired by an Agent-selected tool or adapter."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["research_foundry_official_site_source_import.v1"] = (
        "research_foundry_official_site_source_import.v1"
    )
    source_url: str = Field(min_length=1)
    final_url: str | None = None
    content_type: str = Field(min_length=1, max_length=240)
    raw_file: str = Field(min_length=1)
    prepared_markdown_file: str | None = None
    title: str | None = None
    http_status: int = Field(default=200, ge=100, le=599)
    acquisition_method: Literal[
        "browser",
        "site_api",
        "agent_script",
        "manual_download",
        "other",
    ]
    tool_name: str = Field(min_length=1, max_length=240)
    script_file: str | None = None
    notes: str = Field(default="", max_length=4_000)

    @field_validator("source_url", "content_type", "raw_file", "tool_name")
    @classmethod
    def strip_import_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("source import value cannot be blank")
        return stripped


class OfficialSitePlan(OfficialSiteRequest):
    schema_version: Literal["research_foundry_official_site_plan.v1"] = (
        "research_foundry_official_site_plan.v1"
    )
    plan_id: str
    status: Literal["ready"] = "ready"


class SourceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    alias: str
    requested_url: str
    canonical_url: str
    final_url: str
    url_aliases: list[str] = Field(default_factory=list)
    fetched_at: str
    http_status: int
    content_type: str
    language: str | None = None
    title: str | None = None
    source_type: Literal["html", "pdf", "data"]
    raw_ref: str
    raw_sha256: str
    raw_byte_size: int
    prepared_ref: str | None = None
    prepared_sha256: str | None = None
    prepared_line_count: int | None = None
    status: Literal["prepared", "preserved_unprepared"]
    warnings: list[str] = Field(default_factory=list)
    acquisition_method: str = "http"
    preparation_method: str | None = None
    preparation_health: Literal["healthy", "low_content", "unprepared"] | None = None
    substantive_char_count: int | None = None
    content_block_count: int | None = None
    heading_count: int | None = None
    adapter_ref: str | None = None
    adapter_sha256: str | None = None
    origin_run_id: str | None = None


class QualityReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["research_foundry_official_site_quality.v1"]
    research_ready: bool
    checks: dict[
        Literal["provenance", "material_coverage", "evidence", "consistency", "limitations"],
        Literal["pass", "warn", "fail"],
    ]
    material_gaps: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def enforce_quality_consistency(self) -> "QualityReport":
        required = {"provenance", "material_coverage", "evidence", "consistency", "limitations"}
        if set(self.checks) != required:
            raise ValueError("quality checks must contain exactly the five required checks")
        if self.research_ready and ("fail" in self.checks.values() or self.material_gaps):
            raise ValueError("research_ready cannot contain failed checks or material gaps")
        return self
