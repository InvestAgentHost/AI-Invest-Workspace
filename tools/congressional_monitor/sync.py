"""End-to-end House Clerk PTR discovery and preparation workflow."""

from __future__ import annotations

from pathlib import Path
import hashlib
from typing import Any, Iterable

from .house_download import download_ptr
from .house_index import read_house_index
from .ocr import assess_ocr_document, ocr_pdf
from .ptr_ocr import parse_and_validate_document


HOUSE_REPORT_URLS = {
    "P": "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{document_id}.pdf",
    "A": "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}/{document_id}.pdf",
}


def _find_existing(root: Path, year: str, document_id: str) -> Path | None:
    year_root = root / year
    direct = year_root / f"{document_id}.pdf"
    if direct.is_file():
        return direct
    matches = list(year_root.glob(f"**/{document_id}.pdf")) if year_root.is_dir() else []
    return matches[0] if matches else None


def _file_digest(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
    return size, digest.hexdigest()


def _text_layer_status(path: Path) -> dict[str, Any]:
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
    except ImportError:
        return {"available": False, "page_count": None, "text_characters": None, "ocr_required": True}
    try:
        document = fitz.open(path)
        with document:
            page_count = len(document)
            text_characters = sum(len(page.get_text("text")) for page in document)
        return {"available": True, "page_count": page_count, "text_characters": text_characters, "ocr_required": text_characters < 20}
    except Exception as exc:
        return {"available": False, "page_count": None, "text_characters": None, "ocr_required": True, "error": str(exc)}


def _as_sources(index_file: Path | str | Iterable[Path | str]) -> list[Path]:
    if isinstance(index_file, (str, Path)):
        return [Path(index_file)]
    return [Path(item) for item in index_file]


def _row_key(row: dict[str, Any]) -> str:
    return str(row.get("document_id") or "").strip()


def _report_kind(row: dict[str, Any]) -> str:
    return "amendment" if str(row.get("filing_type", "")).upper() in {"A", "AMENDMENT", "AMENDED"} else "original"


def sync_house_ptrs(index_file: Path | str | Iterable[Path | str], *, output_root: Path | str = "sources/providers/house-clerk", member: str | None = None, limit: int | None = None, download: bool = False, ocr: bool = False, pages: Iterable[int] | None = None, dpi: int = 220, filing_types: Iterable[str] = ("P", "A"), previous_state: dict[str, Any] | None = None, incremental: bool = False) -> dict[str, Any]:
    """Discover PTRs across one or more indexes and optionally download/OCR reports.

    ``previous_state`` is used only as an optimization: an unchanged local PDF
    reuses its text/OCR assessment during an incremental run. It never removes a
    report from the manifest or curated data.
    """

    sources = _as_sources(index_file)
    filing_types = tuple(str(item).strip().upper() for item in filing_types if str(item).strip())
    rows_by_id: dict[str, dict[str, Any]] = {}
    duplicate_index_rows = 0
    for source in sources:
        rows = read_house_index(source, filing_type=filing_types, member=member)
        for row in rows:
            key = _row_key(row)
            if key and key in rows_by_id:
                duplicate_index_rows += 1
                continue
            rows_by_id[key or f"row-{len(rows_by_id)}"] = row
    rows = list(rows_by_id.values())
    if limit is not None:
        if limit < 1:
            raise ValueError("limit must be positive")
        rows = rows[:limit]
    root = Path(output_root)
    previous_reports = (previous_state or {}).get("reports", {})
    results: list[dict[str, Any]] = []
    for row in rows:
        document_id, year = row["document_id"], row["year"]
        item: dict[str, Any] = {"index": row, "document_id": document_id, "year": year, "status": "discovered", "report_kind": _report_kind(row), "amends_report_id": row.get("amends_report_id") or None}
        item["lineage_status"] = "explicit_link" if item["amends_report_id"] else ("unlinked_amendment" if item["report_kind"] == "amendment" else "original")
        previous = previous_reports.get(str(document_id)) or previous_reports.get(f"{year}:{document_id}")
        path = _find_existing(root, year, document_id)
        if path:
            item["status"] = "existing"
            item["path"] = str(path)
            item["bytes"], item["sha256"] = _file_digest(path)
        elif download:
            try:
                filing_type = str(row.get("filing_type") or "P").upper()
                fetched = download_ptr(document_id, year, output_dir=root, url_template=HOUSE_REPORT_URLS.get(filing_type, HOUSE_REPORT_URLS["P"]))
                path = Path(fetched["path"])
                item.update({"status": "downloaded", "path": str(path), "sha256": fetched["sha256"], "bytes": fetched["bytes"]})
            except Exception as exc:
                item.update({"status": "download_failed", "error": str(exc)})
        unchanged = bool(incremental and previous and previous.get("sha256") and previous.get("sha256") == item.get("sha256") and previous.get("bytes") == item.get("bytes"))
        if path and path.is_file():
            if unchanged and previous.get("text_layer"):
                item["text_layer"] = previous["text_layer"]
                item["incremental_reused"] = ["text_layer"]
            else:
                item["text_layer"] = _text_layer_status(path)
            if ocr and item["text_layer"].get("ocr_required"):
                if unchanged and previous.get("status") == "review_ready" and any(key in previous for key in ("candidate_ids", "review_candidate_ids", "validated_candidate_ids")):
                    item["incremental_reused"] = item.get("incremental_reused", []) + ["ocr"]
                    item["candidate_summary"] = {key: previous.get(key) for key in ("candidate_ids", "review_candidate_ids", "validated_candidate_ids", "candidate_count", "review_count", "validated_count")}
                    # Preserve the operational state when OCR-derived candidates
                    # are reused from the previous incremental run.
                    item["status"] = "review_ready"
                else:
                    try:
                        ocr_result = ocr_pdf(path, page_numbers=pages, dpi=dpi)
                        item["ocr"] = assess_ocr_document(ocr_result)
                        item["parsed"] = parse_and_validate_document(ocr_result)
                        item["status"] = "review_ready"
                    except Exception as exc:
                        item.update({"status": "ocr_failed", "error": str(exc)})
        results.append(item)
    counts: dict[str, int] = {}
    for item in results:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    return {
        "index_file": str(sources[0]) if len(sources) == 1 else [str(source) for source in sources],
        "member": member,
        "limit": limit,
        "filing_types": sorted({str(item).upper() for item in filing_types}),
        "incremental": incremental,
        "duplicate_index_rows": duplicate_index_rows,
        "requested_count": len(rows),
        "counts": counts,
        "reports": results,
    }
