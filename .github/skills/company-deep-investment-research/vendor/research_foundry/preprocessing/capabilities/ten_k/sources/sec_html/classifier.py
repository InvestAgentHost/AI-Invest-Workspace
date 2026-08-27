from __future__ import annotations

from pathlib import Path
from urllib.parse import urljoin

from .fetcher import SecFetcher
from .manifest import merge_manifest, parse_index_json, parse_submission_text
from .models import Classification, ClassificationResult, FilingManifest, ManifestDocument, SecReference
from .resolver import resolve_reference


def classify_target(value: str, accession: str | None = None, fetcher: SecFetcher | None = None) -> ClassificationResult:
    fetcher = fetcher or SecFetcher()
    reference = resolve_reference(value, accession)
    input_label = f"{value} {accession}".strip() if accession else value

    if reference.local_path:
        path = Path(reference.local_path)
        if path.suffix.lower() == ".pdf":
            return ClassificationResult(
                classification=Classification.NON_SEC_PDF,
                input=input_label,
                reason="Local PDF is not a SEC archive accession URL.",
                recommended_pipeline="manual_pdf_or_other_tool",
                reference=reference,
            )
        return ClassificationResult(
            classification=Classification.UNKNOWN_OR_UNSUPPORTED,
            input=input_label,
            reason="Local input is not a supported SEC filing reference or PDF.",
            recommended_pipeline="manual_review",
            reference=reference,
        )

    if not reference.urls:
        return ClassificationResult(
            classification=Classification.UNKNOWN_OR_UNSUPPORTED,
            input=input_label,
            reason="Input is a URL, but not a recognized SEC Archives accession URL.",
            recommended_pipeline="manual_review",
            reference=reference,
        )

    warnings: list[str] = []
    manifest: FilingManifest | None = None
    try:
        index_raw = fetcher.get_json_text(reference.urls.index_json_url)
        manifest = parse_index_json(index_raw, reference.urls.base_url, reference.urls.cik, reference.urls.accession)
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"index.json unavailable: {exc}")

    try:
        text_raw = fetcher.get_text(reference.urls.text_url)
        text_manifest = parse_submission_text(text_raw, reference.urls.base_url, reference.urls.cik, reference.urls.accession)
        manifest = merge_manifest(manifest, text_manifest) if manifest else text_manifest
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"complete submission text unavailable: {exc}")

    if not manifest:
        direct_doc = _direct_document_from_reference(reference)
        if direct_doc:
            manifest = FilingManifest(
                cik=reference.urls.cik,
                accession=reference.urls.accession,
                base_url=reference.urls.base_url,
                source="direct_url",
                documents=[direct_doc],
            )
        else:
            return ClassificationResult(
                classification=Classification.UNKNOWN_OR_UNSUPPORTED,
                input=input_label,
                reason="Could not read SEC index.json or complete submission text manifest.",
                recommended_pipeline="manual_review",
                reference=reference,
                warnings=warnings,
            )

    primary = manifest.primary_document()
    if primary is None:
        classification = Classification.SEC_NATIVE_TEXT_ONLY if manifest.header else Classification.UNKNOWN_OR_UNSUPPORTED
        pipeline = "sec_text_ingest" if classification == Classification.SEC_NATIVE_TEXT_ONLY else "manual_review"
        reason = "SEC manifest contains no primary HTML/XML/PDF candidate."
    elif primary.category == "html":
        classification = Classification.SEC_NATIVE_HTML
        pipeline = "html_dom_ingest"
        reason = "SEC manifest contains a primary HTML document."
    elif primary.category == "xml":
        classification = Classification.SEC_NATIVE_XML
        pipeline = "xml_structured_ingest"
        reason = "SEC manifest contains a primary XML document."
    elif primary.category == "pdf":
        classification = Classification.SEC_PDF_FALLBACK
        pipeline = "manual_pdf_or_other_tool"
        reason = "SEC manifest is PDF-only; native HTML preparation is unavailable for this source."
    elif primary.category == "text":
        classification = Classification.SEC_NATIVE_TEXT_ONLY
        pipeline = "sec_text_ingest"
        reason = "SEC manifest only exposes text as a primary source."
    else:
        classification = Classification.UNKNOWN_OR_UNSUPPORTED
        pipeline = "manual_review"
        reason = "SEC manifest primary document type is unsupported."

    return ClassificationResult(
        classification=classification,
        input=input_label,
        reason=reason,
        recommended_pipeline=pipeline,
        reference=reference,
        manifest=manifest,
        primary_document=primary,
        assets=manifest.assets,
        warnings=warnings,
    )


def _direct_document_from_reference(reference: SecReference) -> ManifestDocument | None:
    if not reference.filename or not reference.urls:
        return None
    from .manifest import categorize_filename, is_primary_candidate

    doc = ManifestDocument(
        filename=reference.filename,
        url=urljoin(reference.urls.base_url, reference.filename),
        category=categorize_filename(reference.filename),
    )
    doc.is_primary_candidate = is_primary_candidate(doc)
    return doc
