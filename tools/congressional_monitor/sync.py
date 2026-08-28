"""End-to-end House Clerk PTR discovery and preparation workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .house_download import download_ptr
from .house_index import read_house_index
from .ocr import assess_ocr_document, ocr_pdf
from .ptr_ocr import parse_and_validate_document


def _find_existing(root: Path, year: str, document_id: str) -> Path | None:
    year_root = root / year
    direct = year_root / f"{document_id}.pdf"
    if direct.is_file():
        return direct
    matches = list(year_root.glob(f"**/{document_id}.pdf")) if year_root.is_dir() else []
    return matches[0] if matches else None


def _text_layer_status(path: Path) -> dict[str, Any]:
    try:
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


def sync_house_ptrs(index_file: Path | str, *, output_root: Path | str = "sources/providers/house-clerk", member: str | None = None, limit: int | None = None, download: bool = False, ocr: bool = False, pages: Iterable[int] | None = None, dpi: int = 220) -> dict[str, Any]:
    """Discover PTRs and optionally download/OCR a bounded set of reports."""

    source = Path(index_file)
    rows = read_house_index(source, filing_type="P", member=member)
    if limit is not None:
        if limit < 1:
            raise ValueError("limit must be positive")
        rows = rows[:limit]
    root = Path(output_root)
    results: list[dict[str, Any]] = []
    for row in rows:
        document_id, year = row["document_id"], row["year"]
        item: dict[str, Any] = {"index": row, "document_id": document_id, "year": year, "status": "discovered"}
        path = _find_existing(root, year, document_id)
        if path:
            item["status"] = "existing"
            item["path"] = str(path)
        elif download:
            try:
                fetched = download_ptr(document_id, year, output_dir=root)
                path = Path(fetched["path"])
                item.update({"status": "downloaded", "path": str(path), "sha256": fetched["sha256"], "bytes": fetched["bytes"]})
            except Exception as exc:
                item.update({"status": "download_failed", "error": str(exc)})
        if path and path.is_file():
            item["text_layer"] = _text_layer_status(path)
            if ocr and item["text_layer"].get("ocr_required"):
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
    return {"index_file": str(source), "member": member, "requested_count": len(rows), "counts": counts, "reports": results}
