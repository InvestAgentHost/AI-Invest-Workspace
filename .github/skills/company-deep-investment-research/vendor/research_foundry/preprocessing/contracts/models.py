"""Strict Stage 1 request, binding, locator, and package models."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    StringConstraints,
    model_validator,
)

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
PositiveVersion = Annotated[int, Field(ge=1)]
Sha256Hex = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Stage1FailureCode = Literal[
    "invalid_request",
    "input_failed",
    "pipeline_failed",
    "output_invalid",
    "policy_blocked",
]


class ContractModel(BaseModel):
    """Shared strictness for versioned public contracts."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class Stage1Request(ContractModel):
    """Common envelope used to select one exact Stage 1 pipeline."""

    schema_version: Literal["stage1_request.v1"]
    source_type: NonEmptyStr
    source_method: NonEmptyStr
    stage1_pipeline: NonEmptyStr
    input: dict[NonEmptyStr, JsonValue]


class SecHtmlInput(ContractModel):
    """SEC EDGAR accession or archive URL selected by the user."""

    reference: NonEmptyStr
    accession: NonEmptyStr | None = None
    user_agent: NonEmptyStr | None = None
    download_assets: bool = True


class TenKSecHtmlRequest(Stage1Request):
    """Request contract for SEC native HTML 10-K acquisition."""

    source_type: Literal["10k"]
    source_method: Literal["sec_edgar_html"]
    stage1_pipeline: Literal["10k_sec_html_v1"]
    input: SecHtmlInput


class Stage1Work(ContractModel):
    """Public result of executing one request against one exact binding."""

    schema_version: Literal["stage1_work.v1"]
    work_id: NonEmptyStr
    request_ref: NonEmptyStr
    source_binding_key: NonEmptyStr
    stage1_pipeline: NonEmptyStr
    status: Literal["pending", "running", "completed", "failed", "cancelled"]
    package_id: NonEmptyStr | None = None
    failure_code: Stage1FailureCode | None = None
    error: NonEmptyStr | None = None
    started_at: datetime
    finished_at: datetime | None = None

    @model_validator(mode="after")
    def validate_terminal_result(self) -> "Stage1Work":
        if self.status == "completed":
            if self.package_id is None or self.finished_at is None:
                raise ValueError("completed work requires package_id and finished_at")
            if self.failure_code is not None or self.error is not None:
                raise ValueError("completed work cannot contain failure details")
        elif self.status == "failed":
            if self.failure_code is None or self.error is None or self.finished_at is None:
                raise ValueError("failed work requires failure details and finished_at")
            if self.package_id is not None:
                raise ValueError("failed work cannot contain package_id")
        elif self.status == "cancelled" and self.finished_at is None:
            raise ValueError("cancelled work requires finished_at")
        elif self.status in {"pending", "running"} and self.finished_at is not None:
            raise ValueError("nonterminal work cannot contain finished_at")
        return self


class MarkdownLineLocator(ContractModel):
    """Inclusive line range in one exact immutable Prepared Markdown artifact."""

    schema_version: Literal["markdown_line_locator.v1"]
    artifact_sha256: Sha256Hex
    start_line: PositiveVersion
    end_line: PositiveVersion

    @model_validator(mode="after")
    def validate_line_range(self) -> "MarkdownLineLocator":
        if self.end_line < self.start_line:
            raise ValueError("end_line must be greater than or equal to start_line")
        return self


class Stage1PipelineRef(ContractModel):
    """Fixed implementation selected by a SourceBinding."""

    key: NonEmptyStr
    version: PositiveVersion
    implementation: NonEmptyStr


class AcceptedInput(ContractModel):
    """One input role accepted by a SourceBinding."""

    role: NonEmptyStr
    media_type: NonEmptyStr


class PreparedOutput(ContractModel):
    """One prepared artifact role promised by a SourceBinding."""

    role: NonEmptyStr
    format: NonEmptyStr
    schema_ref: NonEmptyStr | None = Field(default=None, alias="schema")


class SourceBinding(ContractModel):
    """Versioned mapping from an explicit source choice to a fixed pipeline."""

    schema_version: Literal["source_binding.v1"]
    source_binding_key: NonEmptyStr
    version: PositiveVersion
    source_type: NonEmptyStr
    source_method: NonEmptyStr
    stage1_pipeline: Stage1PipelineRef
    request_schema: NonEmptyStr
    accepted_inputs: Annotated[tuple[AcceptedInput, ...], Field(min_length=1)]
    prepared_outputs: Annotated[tuple[PreparedOutput, ...], Field(min_length=1)]
    quality_checks: NonEmptyStr
    usage_policy_ref: NonEmptyStr | None = None

    @model_validator(mode="after")
    def validate_unique_roles(self) -> "SourceBinding":
        input_roles = [item.role for item in self.accepted_inputs]
        output_roles = [item.role for item in self.prepared_outputs]
        if len(input_roles) != len(set(input_roles)):
            raise ValueError("accepted input roles must be unique")
        if len(output_roles) != len(set(output_roles)):
            raise ValueError("prepared output roles must be unique")
        return self


class PackageSource(ContractModel):
    """Exact source and Stage 1 binding that produced a package."""

    source_type: NonEmptyStr = Field(alias="type")
    method: NonEmptyStr
    binding_key: NonEmptyStr
    binding_version: PositiveVersion
    stage1_pipeline: NonEmptyStr


class RawInputArtifact(ContractModel):
    """Immutable Raw input referenced by a PreparedSourcePackage."""

    role: NonEmptyStr
    artifact_ref: NonEmptyStr
    sha256: Sha256Hex
    byte_size: Annotated[int, Field(ge=0)]
    media_type: NonEmptyStr


class PreparedOutputArtifact(ContractModel):
    """Immutable Prepared output handed to Stage 2."""

    role: NonEmptyStr
    artifact_ref: NonEmptyStr
    sha256: Sha256Hex
    byte_size: Annotated[int, Field(ge=0)]
    format: NonEmptyStr
    schema_ref: NonEmptyStr | None = Field(default=None, alias="schema")


class PreparedSourcePackage(ContractModel):
    """The only published Stage 1 handoff to downstream consumers."""

    schema_version: Literal["prepared_source_package.v1"]
    prepared_source_package_id: NonEmptyStr
    source: PackageSource
    request_ref: NonEmptyStr
    request_sha256: Sha256Hex
    raw_inputs: Annotated[tuple[RawInputArtifact, ...], Field(min_length=1)]
    prepared_outputs: Annotated[
        tuple[PreparedOutputArtifact, ...], Field(min_length=1)
    ]
    pipeline_manifest_ref: NonEmptyStr
    pipeline_manifest_sha256: Sha256Hex
    warnings: tuple[NonEmptyStr, ...] = ()
    usage_policy_ref: NonEmptyStr | None = None
    created_at: datetime

    @model_validator(mode="after")
    def validate_unique_artifact_roles(self) -> "PreparedSourcePackage":
        raw_roles = [item.role for item in self.raw_inputs]
        prepared_roles = [item.role for item in self.prepared_outputs]
        if len(raw_roles) != len(set(raw_roles)):
            raise ValueError("raw input roles must be unique")
        if len(prepared_roles) != len(set(prepared_roles)):
            raise ValueError("prepared output roles must be unique")
        return self
