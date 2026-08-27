"""SEC EDGAR native HTML acquisition and immutable Prepared package publication."""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Callable
import uuid

from research_foundry.preprocessing.bindings import load_ten_k_sec_html_v1
from research_foundry.preprocessing.contracts import PreparedSourcePackage, TenKSecHtmlRequest
from research_foundry.preprocessing.capabilities.ten_k.prepared_markdown import (
    TEN_K_PREPARED_MARKDOWN_SCHEMA_V1,
)
from research_foundry.preprocessing.capabilities.ten_k.prepared_markdown import (
    validate_prepared_markdown,
)
from research_foundry.preprocessing.verification import verify_ten_k_sec_html_package
from research_foundry.runtime.artifacts import publish_bytes, publish_directory

from .classifier import classify_target
from .fetcher import SecFetcher, validate_sec_user_agent
from .html_to_markdown import extract_html_to_markdown
from .manifest import manifest_to_dict
from .models import Classification


class SecHtmlExecutionError(RuntimeError):
    """Raised when a SEC native HTML filing cannot be prepared safely."""


def execute_sec_html(
    request: TenKSecHtmlRequest,
    *,
    output_root: str | Path,
    fetcher: SecFetcher | None = None,
    event_sink: Callable[[dict[str, Any]], None] | None = None,
) -> Path:
    """Fetch one SEC native HTML filing and publish a verified psp package."""

    binding = load_ten_k_sec_html_v1()
    if request.source_type != binding.source_type or request.source_method != binding.source_method:
        raise SecHtmlExecutionError("request does not select the SEC HTML binding")
    try:
        user_agent = validate_sec_user_agent(request.input.user_agent or "")
    except ValueError as error:
        raise SecHtmlExecutionError(str(error)) from error
    fetcher = fetcher or SecFetcher(user_agent=user_agent)
    classification = classify_target(
        request.input.reference,
        request.input.accession,
        fetcher=fetcher,
    )
    if classification.classification != Classification.SEC_NATIVE_HTML:
        raise SecHtmlExecutionError(
            f"SEC reference is {classification.classification.value}; "
            f"expected SEC_NATIVE_HTML ({classification.reason})"
        )
    primary = classification.primary_document
    if primary is None or not primary.url:
        raise SecHtmlExecutionError("SEC manifest has no primary HTML URL")

    package_root = Path(output_root).expanduser().resolve()
    package_root.mkdir(parents=True, exist_ok=True)
    package_id = f"psp_{uuid.uuid4().hex}"
    final_directory = package_root / package_id
    created_at = datetime.now(timezone.utc)
    warnings = list(classification.warnings)
    if event_sink:
        event_sink({"event": "sec_html_classified", "classification": classification.classification.value})

    try:
        with tempfile.TemporaryDirectory(prefix=f".{package_id}.", dir=package_root) as staging_name:
            staging = Path(staging_name)
            extraction_root = staging / "extraction"
            html_text = fetcher.get_text(primary.url)
            extraction = extract_html_to_markdown(
                html_text,
                primary.url,
                extraction_root,
                filing_metadata={
                    "cik": classification.reference.cik if classification.reference else None,
                    "accession": classification.reference.accession if classification.reference else None,
                    "filename": primary.filename,
                    "filing_type": classification.manifest.header.get("conformed submission type")
                    if classification.manifest
                    else "10-K",
                },
                fetcher=fetcher,
                download_assets=request.input.download_assets,
            )
            markdown_bytes = _canonical_markdown(extraction.markdown)
            validate_prepared_markdown(markdown_bytes)

            raw_paths: list[tuple[str, str, bytes, str]] = [
                ("primary_html", "raw/source.html", html_text.encode("utf-8"), "text/html"),
            ]
            if classification.reference and classification.reference.urls:
                urls = classification.reference.urls
                for role, ref, media_type in (
                    ("index_json", urls.index_json_url, "application/json"),
                    ("submission_text", urls.text_url, "text/plain"),
                ):
                    try:
                        raw_paths.append((role, f"raw/{role}.txt" if role == "submission_text" else "raw/index.json", fetcher.get_text(ref).encode("utf-8"), media_type))
                    except Exception as error:  # noqa: BLE001
                        warnings.append(f"optional SEC {role} was not preserved: {error}")

            raw_inputs: list[dict[str, Any]] = []
            for role, ref, data, media_type in raw_paths:
                identity = publish_bytes(data, staging / ref)
                raw_inputs.append({
                    "role": role,
                    "artifact_ref": ref,
                    "sha256": identity.sha256,
                    "byte_size": identity.byte_size,
                    "media_type": media_type,
                })

            prepared_identity = publish_bytes(markdown_bytes, staging / "prepared" / "document.md")
            document_json = json.dumps(extraction.document, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
            document_json_identity = publish_bytes(document_json, staging / "prepared" / "document.json")
            xbrl_json = json.dumps(extraction.xbrl_metadata, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
            xbrl_identity = publish_bytes(xbrl_json, staging / "prepared" / "xbrl_metadata.json")
            cleaning_report_json = json.dumps(
                extraction.cleaning_report, ensure_ascii=False, indent=2, sort_keys=True
            ).encode("utf-8") + b"\n"
            cleaning_report_identity = publish_bytes(
                cleaning_report_json, staging / "prepared" / "cleaning_report.json"
            )

            assets_source = extraction_root / "assets"
            if assets_source.is_dir():
                shutil.copytree(assets_source, staging / "prepared" / "assets")
            failed_assets = [asset for asset in extraction.assets if asset.get("download_error")]
            if failed_assets:
                warnings.append(f"{len(failed_assets)} SEC image asset(s) could not be downloaded")
            if not request.input.download_assets and extraction.assets:
                warnings.append("SEC image assets were not downloaded by request")

            request_bytes = _canonical_json_bytes(request.model_dump(mode="json", by_alias=True, exclude_none=True))
            request_identity = publish_bytes(request_bytes, staging / "request.json")
            pipeline_manifest = {
                "schema_version": "ten_k_sec_html_pipeline_manifest.v1",
                "stage1_pipeline": request.stage1_pipeline,
                "binding_key": binding.source_binding_key,
                "binding_version": binding.version,
                "source": manifest_to_dict(classification.manifest) if classification.manifest else None,
                "primary_document": primary.__dict__,
                "source_url": primary.url,
                "raw": [{"role": role, "artifact_ref": ref, "sha256": item["sha256"], "byte_size": item["byte_size"]} for (role, ref, _, _), item in zip(raw_paths, raw_inputs, strict=True)],
                "prepared": {
                    "sha256": prepared_identity.sha256,
                    "byte_size": prepared_identity.byte_size,
                    "line_count": len(markdown_bytes.decode("utf-8")[:-1].split("\n")),
                    "block_count": len(extraction.document.get("blocks", [])),
                    "asset_count": len(extraction.assets),
                    "xbrl_metadata_count": len(extraction.xbrl_metadata),
                    "cleaning_report_sha256": cleaning_report_identity.sha256,
                },
                "created_at": created_at.isoformat().replace("+00:00", "Z"),
            }
            manifest_identity = publish_bytes(_canonical_json_bytes(pipeline_manifest), staging / "pipeline_manifest.json")
            package = PreparedSourcePackage.model_validate({
                "schema_version": "prepared_source_package.v1",
                "prepared_source_package_id": package_id,
                "source": {
                    "type": binding.source_type,
                    "method": binding.source_method,
                    "binding_key": binding.source_binding_key,
                    "binding_version": binding.version,
                    "stage1_pipeline": request.stage1_pipeline,
                },
                "request_ref": "request.json",
                "request_sha256": request_identity.sha256,
                "raw_inputs": raw_inputs,
                "prepared_outputs": [
                    {"role": "document", "artifact_ref": "prepared/document.md", "sha256": prepared_identity.sha256, "byte_size": prepared_identity.byte_size, "format": "markdown", "schema": TEN_K_PREPARED_MARKDOWN_SCHEMA_V1},
                    {"role": "document_json", "artifact_ref": "prepared/document.json", "sha256": document_json_identity.sha256, "byte_size": document_json_identity.byte_size, "format": "json", "schema": "urn:research_foundry:schema:ten_k_sec_html_blocks:v1"},
                    {"role": "xbrl_metadata", "artifact_ref": "prepared/xbrl_metadata.json", "sha256": xbrl_identity.sha256, "byte_size": xbrl_identity.byte_size, "format": "json", "schema": "urn:research_foundry:schema:ten_k_xbrl_metadata:v1"},
                    {"role": "cleaning_report", "artifact_ref": "prepared/cleaning_report.json", "sha256": cleaning_report_identity.sha256, "byte_size": cleaning_report_identity.byte_size, "format": "json", "schema": "urn:research_foundry:schema:ten_k_html_cleaning_report:v1"},
                ],
                "pipeline_manifest_ref": "pipeline_manifest.json",
                "pipeline_manifest_sha256": manifest_identity.sha256,
                "warnings": warnings,
                "created_at": created_at,
            })
            publish_bytes(_canonical_json_bytes(package.model_dump(mode="json", by_alias=True, exclude_none=True)), staging / "prepared_source_package.json")
            verify_ten_k_sec_html_package(staging, expected_package_id=package_id)
            publish_directory(staging, final_directory)
    except Exception as error:
        if isinstance(error, SecHtmlExecutionError):
            raise
        raise SecHtmlExecutionError(str(error)) from error
    return final_directory


def _canonical_markdown(value: str) -> bytes:
    normalized = value.replace("\r\n", "\n").replace("\r", "\n").strip("\n") + "\n"
    return normalized.encode("utf-8")


def _canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
