"""Build checked-in JSON Schemas for research handoff contracts."""

import json
from pathlib import Path

from pydantic import BaseModel

from .models import (
    AgentLedger,
    QuantitativeModelChecks,
    QuantitativeModelInput,
    QuantitativeModelManifest,
    QuantitativeModelSpec,
    ResearchNotebookReleaseManifest,
    ResearchPanel,
    ReportEvidenceMap,
    ResearchBrief,
    ResearchClaim,
    ResearchCoverage,
    ResearchMethodCatalog,
    ResearchQualityReport,
    ResearchReleaseManifest,
    ResearchSourceManifest,
    ResearchSourceMetadata,
    WorkPackageBrief,
    WorkPackageResult,
)


SCHEMA_MODELS: dict[str, tuple[type[BaseModel], str]] = {
    "research_agent_ledger.v1.schema.json": (
        AgentLedger,
        "urn:research_foundry:schema:research_agent_ledger:v1",
    ),
    "research_panel.v1.schema.json": (
        ResearchPanel,
        "urn:research_foundry:schema:research_panel:v1",
    ),
    "report_evidence_map.v1.schema.json": (
        ReportEvidenceMap,
        "urn:research_foundry:schema:report_evidence_map:v1",
    ),
    "research_method_catalog.v1.schema.json": (
        ResearchMethodCatalog,
        "urn:research_foundry:schema:research_method_catalog:v1",
    ),
    "research_coverage.v1.schema.json": (
        ResearchCoverage,
        "urn:research_foundry:schema:research_coverage:v1",
    ),
    "research_notebook_release.v1.schema.json": (
        ResearchNotebookReleaseManifest,
        "urn:research_foundry:schema:research_notebook_release:v1",
    ),
    "research_source_metadata.v1.schema.json": (
        ResearchSourceMetadata,
        "urn:research_foundry:schema:research_source_metadata:v1",
    ),
    "research_source_manifest.v1.schema.json": (
        ResearchSourceManifest,
        "urn:research_foundry:schema:research_source_manifest:v1",
    ),
    "quantitative_model_input.v1.schema.json": (
        QuantitativeModelInput,
        "urn:research_foundry:schema:quantitative_model_input:v1",
    ),
    "quantitative_model_spec.v1.schema.json": (
        QuantitativeModelSpec,
        "urn:research_foundry:schema:quantitative_model_spec:v1",
    ),
    "quantitative_model_checks.v1.schema.json": (
        QuantitativeModelChecks,
        "urn:research_foundry:schema:quantitative_model_checks:v1",
    ),
    "quantitative_model_manifest.v1.schema.json": (
        QuantitativeModelManifest,
        "urn:research_foundry:schema:quantitative_model_manifest:v1",
    ),
    "research_brief.v1.schema.json": (
        ResearchBrief,
        "urn:research_foundry:schema:research_brief:v1",
    ),
    "work_package_brief.v1.schema.json": (
        WorkPackageBrief,
        "urn:research_foundry:schema:work_package_brief:v1",
    ),
    "research_claim.v1.schema.json": (
        ResearchClaim,
        "urn:research_foundry:schema:research_claim:v1",
    ),
    "work_package_result.v1.schema.json": (
        WorkPackageResult,
        "urn:research_foundry:schema:work_package_result:v1",
    ),
    "research_quality_report.v1.schema.json": (
        ResearchQualityReport,
        "urn:research_foundry:schema:research_quality_report:v1",
    ),
    "research_release_manifest.v1.schema.json": (
        ResearchReleaseManifest,
        "urn:research_foundry:schema:research_release_manifest:v1",
    ),
}


def build_schema_documents() -> dict[str, dict[str, object]]:
    """Return canonical Draft 2020-12 schema documents keyed by filename."""

    documents: dict[str, dict[str, object]] = {}
    for filename, (model, schema_id) in SCHEMA_MODELS.items():
        body = model.model_json_schema(mode="validation")
        documents[filename] = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": schema_id,
            **body,
        }
    return documents


def render_schema(document: dict[str, object]) -> str:
    """Render one schema deterministically for source control."""

    return json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def export_schemas(directory: Path) -> None:
    """Write all research schemas to the provided package directory."""

    directory.mkdir(parents=True, exist_ok=True)
    for filename, document in build_schema_documents().items():
        (directory / filename).write_text(render_schema(document), encoding="utf-8")
