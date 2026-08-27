"""Confirmed SEC HTML plan and full acquisition-to-index execution."""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from research_foundry.preprocessing.capabilities.ten_k.indexing import materialize_index
from research_foundry.preprocessing.capabilities.ten_k.sources.sec_html.fetcher import SecFetcher, validate_sec_user_agent
from research_foundry.preprocessing.capabilities.ten_k.sources.sec_html.pipeline import (
    execute_sec_html,
)
from research_foundry.preprocessing.capabilities.ten_k.sources.sec_html.classifier import classify_target
from research_foundry.preprocessing.capabilities.ten_k.sources.sec_html.models import Classification
from research_foundry.preprocessing.contracts import TenKSecHtmlRequest
from research_foundry.runtime.run_records import RunRecord, create_run, write_run_record
from research_foundry.runtime.workspace import Workspace


class SecHtmlPlanError(ValueError):
    """Raised when a SEC HTML plan is ambiguous or not confirmed."""


def build_sec_html_plan(
    *,
    reference: str,
    accession: str | None,
    target_name: str,
    workspace_root: str | Path,
    fiscal_year: int | None,
    user_agent: str,
    confirmed: bool,
    download_assets: bool = True,
    fetcher: SecFetcher | None = None,
) -> dict[str, Any]:
    """Resolve a SEC reference and produce a user-confirmable plan."""

    try:
        user_agent = validate_sec_user_agent(user_agent)
    except ValueError as error:
        raise SecHtmlPlanError(str(error)) from error
    request = TenKSecHtmlRequest.model_validate({
        "schema_version": "stage1_request.v1",
        "source_type": "10k",
        "source_method": "sec_edgar_html",
        "stage1_pipeline": "10k_sec_html_v1",
        "input": {
            "reference": reference,
            "accession": accession,
            "user_agent": user_agent,
            "download_assets": download_assets,
        },
    })
    classifier = classify_target(reference, accession, fetcher=fetcher or SecFetcher(user_agent=user_agent))
    warnings = list(classifier.warnings)
    if classifier.classification != Classification.SEC_NATIVE_HTML:
        return {
            "schema_version": "research_foundry_ten_k_sec_html_plan.v1",
            "status": "needs_confirmation",
            "reason": f"reference classified as {classifier.classification.value}; {classifier.reason}",
            "request": request.model_dump(mode="json"),
            "target_name": target_name,
            "workspace_root": str(Path(workspace_root).expanduser().resolve()),
            "fiscal_year": fiscal_year,
            "classification": classifier.to_dict(),
            "warnings": warnings,
        }
    resolved_year = fiscal_year or _infer_fiscal_year(classifier)
    if resolved_year is None:
        warnings.append("fiscal year could not be inferred from SEC metadata; supply --fiscal-year")
    status = "ready" if confirmed and resolved_year is not None else "needs_confirmation"
    return {
        "schema_version": "research_foundry_ten_k_sec_html_plan.v1",
        "status": status,
        "request": request.model_dump(mode="json"),
        "target_name": target_name,
        "workspace_root": str(Path(workspace_root).expanduser().resolve()),
        "fiscal_year": resolved_year,
        "classification": classifier.to_dict(),
        "warnings": list(dict.fromkeys(warnings)),
    }


def execute_sec_html_plan(plan: dict[str, Any], *, fetcher: SecFetcher | None = None) -> RunRecord:
    """Execute one confirmed SEC HTML plan and immediately build its index."""

    if plan.get("schema_version") != "research_foundry_ten_k_sec_html_plan.v1":
        raise SecHtmlPlanError("unsupported SEC HTML plan schema")
    if plan.get("status") != "ready":
        raise SecHtmlPlanError("SEC HTML plan requires confirmation or has unresolved ambiguity")
    request = TenKSecHtmlRequest.model_validate(plan["request"])
    workspace = Workspace.from_path(plan["workspace_root"])
    workspace.ensure_layout()
    record = create_run(workspace.root, "ten_k_sec_html", plan)
    record.warnings.extend(plan.get("warnings", []))
    target = _safe_component(str(plan["target_name"]))
    year = int(plan["fiscal_year"])
    year_root = workspace.artifacts / "ten_k" / target / f"FY{year}"
    output_manifest_path = year_root / "output_manifest.json"
    if output_manifest_path.is_file():
        record.items.append({"fiscal_year": year, "status": "skipped", "reason": "output_manifest already exists"})
        record.status = "completed"
        record.finished_at = datetime.now(timezone.utc)
        write_run_record(workspace.root, record)
        return record

    item: dict[str, Any] = {"fiscal_year": year, "status": "running", "reference": request.input.reference}
    record.items.append(item)
    write_run_record(workspace.root, record)
    try:
        package_path = execute_sec_html(request, output_root=year_root, fetcher=fetcher)
        index_result = materialize_index(package_path)
        output_manifest = {
            "schema_version": "research_foundry_ten_k_filing_output.v1",
            "target_name": str(plan["target_name"]),
            "fiscal_year": year,
            "source": {
                "reference": request.input.reference,
                "accession": request.input.accession,
            },
            "package_path": str(package_path.relative_to(year_root)),
            "index_path": str(index_result.index_directory.relative_to(year_root)),
            "package_id": package_path.name,
            "pipeline": request.stage1_pipeline,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        output_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        output_manifest_path.write_text(json.dumps(output_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        item.update(status="completed", package_path=str(package_path), index_path=str(index_result.index_directory))
    except Exception as error:  # noqa: BLE001
        item.update(status="failed", error=str(error))
    record.status = "completed" if item["status"] == "completed" else "completed_with_failures"
    record.finished_at = datetime.now(timezone.utc)
    write_run_record(workspace.root, record)
    return record


def _infer_fiscal_year(classifier: Any) -> int | None:
    values: list[str] = []
    if classifier.manifest:
        values.extend(str(value) for key, value in classifier.manifest.header.items() if "period" in key or "year" in key)
    if classifier.primary_document:
        values.append(classifier.primary_document.filename)
    years = {int(value) for value in re.findall(r"(?<!\d)(20\d{2})(?!\d)", " ".join(values))}
    return next(iter(years)) if len(years) == 1 else None


def _safe_component(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "._-" else "_" for char in value.strip())
    if not cleaned:
        raise SecHtmlPlanError("target_name must contain a filesystem-safe character")
    return cleaned
