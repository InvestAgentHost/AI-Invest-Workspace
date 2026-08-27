"""Independent verification of published SEC HTML source packages."""

from pathlib import Path
import json
from typing import Any

from research_foundry.runtime import hash_file
from research_foundry.preprocessing.contracts import PreparedSourcePackage, TenKSecHtmlRequest
from research_foundry.preprocessing.capabilities.ten_k.prepared_markdown import (
    LEGACY_TEN_K_SEC_HTML_MARKDOWN_SCHEMA_V1,
    MarkdownValidationError,
    accepted_document_schemas,
    validate_prepared_markdown,
)


class PreparedSourcePackageVerificationError(ValueError):
    """Raised when a prepared source package cannot prove its integrity."""


def verify_ten_k_sec_html_package(
    package_directory: Path | str,
    *,
    expected_package_id: str | None = None,
) -> PreparedSourcePackage:
    """Verify the immutable package emitted by the SEC HTML pipeline."""

    root = Path(package_directory).expanduser().resolve()
    try:
        package = PreparedSourcePackage.model_validate_json(
            (root / "prepared_source_package.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError) as error:
        raise PreparedSourcePackageVerificationError(
            f"invalid PreparedSourcePackage: {error}"
        ) from error
    if package.prepared_source_package_id != (expected_package_id or root.name):
        raise PreparedSourcePackageVerificationError(
            "package identity does not match its immutable directory"
        )
    identity = (
        package.source.source_type,
        package.source.method,
        package.source.binding_key,
        package.source.binding_version,
        package.source.stage1_pipeline,
    )
    if identity != ("10k", "sec_edgar_html", "ten_k.sec_edgar_html", 1, "10k_sec_html_v1"):
        raise PreparedSourcePackageVerificationError(
            "package does not identify the SEC HTML pipeline"
        )

    request_path = _verified_ref(root, package.request_ref, package.request_sha256, None)
    manifest_path = _verified_ref(
        root, package.pipeline_manifest_ref, package.pipeline_manifest_sha256, None
    )
    try:
        request = TenKSecHtmlRequest.model_validate_json(
            request_path.read_text(encoding="utf-8")
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise PreparedSourcePackageVerificationError(
            f"invalid SEC HTML package metadata: {error}"
        ) from error
    if manifest.get("schema_version") != "ten_k_sec_html_pipeline_manifest.v1":
        raise PreparedSourcePackageVerificationError("unknown SEC HTML pipeline manifest schema")
    if request.stage1_pipeline != package.source.stage1_pipeline:
        raise PreparedSourcePackageVerificationError("request and package pipeline differ")

    primary_html = _one_role(package.raw_inputs, "primary_html")
    document = _one_role(package.prepared_outputs, "document")
    cleaning_report = _optional_role(package.prepared_outputs, "cleaning_report")
    if primary_html.media_type != "text/html":
        raise PreparedSourcePackageVerificationError("SEC primary raw artifact is not HTML")
    if document.format != "markdown" or document.schema_ref not in accepted_document_schemas(
        LEGACY_TEN_K_SEC_HTML_MARKDOWN_SCHEMA_V1
    ):
        raise PreparedSourcePackageVerificationError(
            "SEC prepared document does not use the HTML Markdown contract"
        )
    if document.schema_ref == "urn:research_foundry:schema:ten_k_prepared_markdown:v1" and cleaning_report is None:
        raise PreparedSourcePackageVerificationError(
            "canonical SEC Markdown packages require a cleaning report"
        )

    html_path = _verified_ref(root, primary_html.artifact_ref, primary_html.sha256, primary_html.byte_size)
    document_path = _verified_ref(root, document.artifact_ref, document.sha256, document.byte_size)
    cleaning_path = (
        _verified_ref(root, cleaning_report.artifact_ref, cleaning_report.sha256, cleaning_report.byte_size)
        if cleaning_report is not None
        else None
    )
    try:
        html_text = html_path.read_text(encoding="utf-8")
        prepared_text = validate_prepared_markdown(document_path.read_bytes())
    except (OSError, ValueError, MarkdownValidationError) as error:
        raise PreparedSourcePackageVerificationError(
            f"invalid SEC HTML artifact: {error}"
        ) from error
    if not html_text.lstrip().startswith("<"):
        raise PreparedSourcePackageVerificationError(
            "SEC primary HTML artifact is not recognizable HTML"
        )
    if cleaning_report is not None:
        if cleaning_report.schema_ref != "urn:research_foundry:schema:ten_k_html_cleaning_report:v1":
            raise PreparedSourcePackageVerificationError(
                "SEC cleaning report does not use its declared schema"
            )
        try:
            report = json.loads(cleaning_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise PreparedSourcePackageVerificationError(
                f"invalid SEC cleaning report: {error}"
            ) from error
        if report.get("schema_version") != "ten_k_html_cleaning_report.v1":
            raise PreparedSourcePackageVerificationError("unknown SEC cleaning report schema")
        if report.get("generic_rules_only") is not True:
            raise PreparedSourcePackageVerificationError(
                "SEC cleaning report does not prove generic rules"
            )

    line_count = len(prepared_text[:-1].split("\n"))
    prepared_manifest = manifest.get("prepared", {})
    if (
        prepared_manifest.get("sha256") != document.sha256
        or prepared_manifest.get("byte_size") != document.byte_size
        or prepared_manifest.get("line_count") != line_count
    ):
        raise PreparedSourcePackageVerificationError(
            "SEC prepared identity does not match pipeline manifest"
        )
    if cleaning_report is not None and prepared_manifest.get("cleaning_report_sha256") != cleaning_report.sha256:
        raise PreparedSourcePackageVerificationError(
            "SEC cleaning report identity does not match pipeline manifest"
        )
    return package


def _verified_ref(
    root: Path, artifact_ref: str, expected_sha256: str, expected_size: int | None
) -> Path:
    relative = Path(artifact_ref)
    if relative.is_absolute() or ".." in relative.parts:
        raise PreparedSourcePackageVerificationError(
            f"artifact ref escapes package: {artifact_ref}"
        )
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise PreparedSourcePackageVerificationError(
            f"artifact ref is missing or unsafe: {artifact_ref}"
        )
    identity = hash_file(path)
    if identity.sha256 != expected_sha256:
        raise PreparedSourcePackageVerificationError(
            f"artifact hash mismatch: {artifact_ref}"
        )
    if expected_size is not None and identity.byte_size != expected_size:
        raise PreparedSourcePackageVerificationError(
            f"artifact size mismatch: {artifact_ref}"
        )
    return path


def _one_role(items: tuple[Any, ...], role: str) -> Any:
    matches = [item for item in items if item.role == role]
    if len(matches) != 1:
        raise PreparedSourcePackageVerificationError(
            f"package must contain exactly one {role!r} artifact"
        )
    return matches[0]


def _optional_role(items: tuple[Any, ...], role: str) -> Any | None:
    matches = [item for item in items if item.role == role]
    if len(matches) > 1:
        raise PreparedSourcePackageVerificationError(
            f"package must contain at most one {role!r} artifact"
        )
    return matches[0] if matches else None
