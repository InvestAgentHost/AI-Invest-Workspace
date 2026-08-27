"""Build checked-in JSON Schema documents from Stage 1 contract models."""

import json
from pathlib import Path

from pydantic import BaseModel

from .models import (
    MarkdownLineLocator,
    PreparedSourcePackage,
    SourceBinding,
    Stage1Request,
    Stage1Work,
)

SCHEMA_MODELS: dict[str, tuple[type[BaseModel], str]] = {
    "stage1_request.v1.schema.json": (
        Stage1Request,
        "urn:research_foundry:schema:stage1_request:v1",
    ),
    "stage1_work.v1.schema.json": (
        Stage1Work,
        "urn:research_foundry:schema:stage1_work:v1",
    ),
    "source_binding.v1.schema.json": (
        SourceBinding,
        "urn:research_foundry:schema:source_binding:v1",
    ),
    "markdown_line_locator.v1.schema.json": (
        MarkdownLineLocator,
        "urn:research_foundry:schema:markdown_line_locator:v1",
    ),
    "prepared_source_package.v1.schema.json": (
        PreparedSourcePackage,
        "urn:research_foundry:schema:prepared_source_package:v1",
    ),
}


def build_schema_documents() -> dict[str, dict[str, object]]:
    """Return canonical Draft 2020-12 schema documents keyed by filename."""

    documents: dict[str, dict[str, object]] = {}
    for filename, (model, schema_id) in SCHEMA_MODELS.items():
        body = model.model_json_schema(by_alias=True, mode="validation")
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
    """Write all Stage 1 schemas to the provided package directory."""

    directory.mkdir(parents=True, exist_ok=True)
    for filename, document in build_schema_documents().items():
        (directory / filename).write_text(render_schema(document), encoding="utf-8")
