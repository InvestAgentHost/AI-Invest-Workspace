"""Mechanical validation for Agent-authored official-site outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

import yaml

from .models import OfficialSitePlan, QualityReport, SourceRecord
from .preparation import analyze_prepared_markdown


class OfficialSiteValidationError(ValueError):
    """Raised when a snapshot cannot be safely published."""


_CITATION = re.compile(r"\[(O\d{4})(?::L(\d+)-L(\d+))?\]")
_DOCUMENT_TYPES = (
    "business_and_offering_handbook",
    "strategy_and_developments",
    "important_information",
)


def validate_official_site_snapshot(
    snapshot_directory: str | Path,
    *,
    plan: OfficialSitePlan,
    run_id: str,
    snapshot_id: str,
) -> dict[str, Any]:
    root = Path(snapshot_directory).resolve()
    sources = _load_sources(root)
    if not sources or not any(source.status == "prepared" for source in sources):
        raise OfficialSiteValidationError("snapshot contains no prepared official source")
    by_alias = {source.alias: source for source in sources}
    if len(by_alias) != len(sources):
        raise OfficialSiteValidationError("source aliases must be unique")
    for source in sources:
        _verify_ref(root, source.raw_ref, source.raw_sha256, source.raw_byte_size)
        if source.adapter_ref or source.adapter_sha256:
            if not source.adapter_ref or not source.adapter_sha256:
                raise OfficialSiteValidationError(
                    f"adapter provenance is incomplete: {source.alias}"
                )
            _verify_ref(root, source.adapter_ref, source.adapter_sha256)
        if source.status == "prepared":
            if not source.prepared_ref or not source.prepared_sha256 or not source.prepared_line_count:
                raise OfficialSiteValidationError(f"prepared metadata is incomplete: {source.alias}")
            _verify_ref(root, source.prepared_ref, source.prepared_sha256)
            health = analyze_prepared_markdown((root / source.prepared_ref).read_bytes())
            recorded = source.preparation_health or "healthy"
            if recorded != health.status:
                raise OfficialSiteValidationError(
                    f"prepared health metadata mismatch: {source.alias}"
                )
            if source.substantive_char_count is not None and (
                source.substantive_char_count != health.substantive_char_count
            ):
                raise OfficialSiteValidationError(
                    f"prepared health metrics mismatch: {source.alias}"
                )
    _validate_preparation_health(root, sources)
    _verify_index(root)

    quality = _load_quality(root)
    expected_quality = "research_ready" if quality.research_ready else "partial"
    citation_texts: list[str] = []
    for document_type in _DOCUMENT_TYPES:
        path = root / "deliverables" / f"{document_type}.md"
        frontmatter, body = _read_deliverable(path)
        expected = {
            "schema_version": "research_foundry_official_site_deliverable.v1",
            "document_type": document_type,
            "target_name": plan.target_name,
            "as_of": plan.as_of.isoformat(),
            "snapshot_id": snapshot_id,
            "run_id": run_id,
            "quality_status": expected_quality,
        }
        normalized = {key: _yaml_scalar(value) for key, value in frontmatter.items()}
        if any(normalized.get(key) != value for key, value in expected.items()):
            raise OfficialSiteValidationError(f"deliverable metadata mismatch: {path.name}")
        if "[Agent synthesis required]" in body or len(re.sub(r"\s+", "", body)) < 40:
            raise OfficialSiteValidationError(f"deliverable has not been synthesized: {path.name}")
        citation_texts.append(body)

    offering_rows = _load_jsonl(root / "data" / "offering_catalog.jsonl")
    event_rows = _load_jsonl(root / "data" / "development_events.jsonl")
    for index, row in enumerate(offering_rows, start=1):
        required = {"business_area", "offering_name", "offering_type", "description", "evidence_refs"}
        if not required.issubset(row):
            raise OfficialSiteValidationError(f"offering row {index} is missing required fields")
        _validate_evidence_refs(row["evidence_refs"], by_alias, f"offering row {index}")
        citation_texts.extend(_evidence_strings(row["evidence_refs"]))
    for index, row in enumerate(event_rows, start=1):
        required = {"date", "event_type", "title", "summary", "affected_area", "materiality_reason", "evidence_refs"}
        if not required.issubset(row):
            raise OfficialSiteValidationError(f"development event row {index} is missing required fields")
        _validate_evidence_refs(row["evidence_refs"], by_alias, f"development event row {index}")
        citation_texts.extend(_evidence_strings(row["evidence_refs"]))
    for text in citation_texts:
        _validate_citations(text, by_alias)
    return {
        "quality": quality,
        "sources": sources,
        "counts": {
            "sources": len(sources),
            "prepared_sources": sum(source.status == "prepared" for source in sources),
            "offerings": len(offering_rows),
            "development_events": len(event_rows),
        },
    }


def verify_official_site_artifact(directory: str | Path) -> dict[str, Any]:
    root = Path(directory).resolve()
    try:
        manifest = json.loads((root / "official_site_manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise OfficialSiteValidationError(f"invalid official_site_manifest.json: {error}") from error
    if manifest.get("schema_version") != "research_foundry_official_site_manifest.v1":
        raise OfficialSiteValidationError("unsupported official-site manifest schema")
    plan = OfficialSitePlan.model_validate(manifest.get("plan"))
    result = validate_official_site_snapshot(
        root,
        plan=plan,
        run_id=str(manifest.get("run_id", "")),
        snapshot_id=str(manifest.get("snapshot_id", "")),
    )
    if manifest.get("research_ready") != result["quality"].research_ready:
        raise OfficialSiteValidationError("manifest quality status does not match quality report")
    if manifest.get("counts") != result["counts"]:
        raise OfficialSiteValidationError("manifest counts do not match snapshot")
    return manifest


def _load_sources(root: Path) -> list[SourceRecord]:
    return [SourceRecord.model_validate(row) for row in _load_jsonl(root / "sources.jsonl")]


def _load_quality(root: Path) -> QualityReport:
    try:
        return QualityReport.model_validate_json((root / "quality_report.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise OfficialSiteValidationError(f"invalid quality_report.json: {error}") from error


def _validate_preparation_health(root: Path, sources: list[SourceRecord]) -> None:
    try:
        state = json.loads((root / "crawl_state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise OfficialSiteValidationError(f"invalid crawl_state.json: {error}") from error
    reviews = state.get("coverage_reviews")
    if not isinstance(reviews, list) or not reviews or reviews[-1].get("decision") != "complete":
        raise OfficialSiteValidationError("snapshot has no final Agent coverage decision")
    final = reviews[-1]
    waivers = final.get("non_material_source_reasons", {})
    if not isinstance(waivers, dict):
        raise OfficialSiteValidationError("non-material source decisions are invalid")
    by_id = {source.source_id: source for source in sources}
    for source_id, reason in waivers.items():
        if source_id not in by_id or not isinstance(reason, str) or not reason.strip():
            raise OfficialSiteValidationError("non-material source decision is invalid")
    unresolved = [
        source.alias
        for source in sources
        if source.source_type in {"html", "pdf"}
        and (source.preparation_health or ("healthy" if source.status == "prepared" else "unprepared"))
        != "healthy"
        and source.source_id not in waivers
    ]
    if unresolved:
        raise OfficialSiteValidationError(
            f"material source preparation remains unhealthy: {unresolved[0]}"
        )
    assessments = final.get("coverage_assessment", [])
    if not isinstance(assessments, list):
        raise OfficialSiteValidationError("coverage assessment is invalid")
    for assessment in assessments:
        if not isinstance(assessment, dict) or assessment.get("status") != "covered":
            continue
        for source_id in assessment.get("evidence_source_ids", []):
            source = by_id.get(source_id)
            if source is None or source.preparation_health not in {None, "healthy"}:
                raise OfficialSiteValidationError(
                    f"covered area relies on unhealthy source: {source_id}"
                )


def _verify_index(root: Path) -> None:
    try:
        manifest = json.loads((root / "index/index_manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise OfficialSiteValidationError(f"invalid index manifest: {error}") from error
    if manifest.get("schema_version") != "research_foundry_official_site_index.v1":
        raise OfficialSiteValidationError("unsupported official-site index schema")
    files = manifest.get("files")
    counts = manifest.get("counts")
    if not isinstance(files, dict) or not isinstance(counts, dict):
        raise OfficialSiteValidationError("official-site index manifest is incomplete")
    for kind in ("sections", "chunks", "tables"):
        item = files.get(kind)
        if not isinstance(item, dict) or item.get("artifact_ref") != f"{kind}.jsonl":
            raise OfficialSiteValidationError(f"invalid index file metadata: {kind}")
        path = root / "index" / f"{kind}.jsonl"
        _verify_ref(root, f"index/{kind}.jsonl", str(item.get("sha256", "")))
        rows = len([line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()])
        if rows != item.get("row_count") or rows != counts.get(kind):
            raise OfficialSiteValidationError(f"index row count mismatch: {kind}")


def _verify_ref(root: Path, ref: str, expected_hash: str, expected_size: int | None = None) -> None:
    path = (root / ref).resolve()
    if root not in path.parents or not path.is_file():
        raise OfficialSiteValidationError(f"unsafe or missing artifact reference: {ref}")
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != expected_hash:
        raise OfficialSiteValidationError(f"artifact hash mismatch: {ref}")
    if expected_size is not None and len(content) != expected_size:
        raise OfficialSiteValidationError(f"artifact size mismatch: {ref}")


def _read_deliverable(path: Path) -> tuple[dict[str, Any], str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise OfficialSiteValidationError(f"missing deliverable: {path.name}") from error
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, flags=re.DOTALL)
    if not match:
        raise OfficialSiteValidationError(f"invalid deliverable frontmatter: {path.name}")
    try:
        metadata = yaml.safe_load(match.group(1))
    except yaml.YAMLError as error:
        raise OfficialSiteValidationError(f"invalid deliverable YAML: {path.name}") from error
    if not isinstance(metadata, dict):
        raise OfficialSiteValidationError(f"deliverable metadata must be an object: {path.name}")
    return metadata, match.group(2)


def _yaml_scalar(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        values = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, ValueError) as error:
        raise OfficialSiteValidationError(f"invalid JSONL: {path}") from error
    if not all(isinstance(value, dict) for value in values):
        raise OfficialSiteValidationError(f"JSONL rows must be objects: {path}")
    return values


def _evidence_strings(value: Any) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise OfficialSiteValidationError("evidence_refs must be a list of citation strings")
    return value


def _validate_evidence_refs(value: Any, sources: dict[str, SourceRecord], context: str) -> None:
    values = _evidence_strings(value)
    if not values:
        raise OfficialSiteValidationError(f"{context} must contain at least one evidence reference")
    for item in values:
        if not _CITATION.fullmatch(item.strip()):
            raise OfficialSiteValidationError(f"{context} contains an invalid evidence reference")
        _validate_citations(item, sources)


def _validate_citations(text: str, sources: dict[str, SourceRecord]) -> None:
    for alias, start, end in _CITATION.findall(text):
        source = sources.get(alias)
        if source is None:
            raise OfficialSiteValidationError(f"citation references unknown source: {alias}")
        if start or end:
            if not source.prepared_line_count:
                raise OfficialSiteValidationError(f"line citation references unprepared source: {alias}")
            first, last = int(start), int(end)
            if first < 1 or last < first or last > source.prepared_line_count:
                raise OfficialSiteValidationError(f"citation line range is invalid: {alias}:L{first}-L{last}")
