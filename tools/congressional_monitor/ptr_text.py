"""Conservative parser for text-layer House PTR PDFs."""

from __future__ import annotations

from datetime import date
import hashlib
from pathlib import Path
import re
from typing import Any

from .security_map import amount_range_candidates, ticker_candidates


OWNER_CODES = {"DC", "JT", "SP", "DP", "O", "S", "J"}
DATE_RE = re.compile(r"(?<!\d)(\d{1,2})/(\d{1,2})/(\d{2,4})(?!\d)")
AMOUNT_RE = re.compile(r"\$[\d,]+(?:\.\d{2})?\s*-\s*\$[\d,]+(?:\.\d{2})?")
ASSET_RE = re.compile(r"(?P<asset>.+?)\s*\[(?P<asset_type>ST|OP|AB|OT)\]", re.IGNORECASE | re.DOTALL)
CODE_RE = re.compile(r"\n\s*(?P<code>[PSE])(?:\s*\(partial\))?\s*\n", re.IGNORECASE)
DESCRIPTION_RE = re.compile(r"(?:Description|Dʇʕʅʔʋʒʖʋʑʐ):\s*(?P<description>.*?)(?=\n(?:Comments|Location|Filing ID|Initial Public|Certification|Digitally Signed)|\n\* For|$)", re.IGNORECASE | re.DOTALL)
TICKER_RE = re.compile(r"\(([A-Z]{1,6})\)")


def _normalize_date(value: str) -> str | None:
    match = DATE_RE.search(value)
    if not match:
        return None
    month, day, year = (int(match.group(i)) for i in range(1, 4))
    year += 2000 if year < 100 else 0
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def _text_from_pdf(path: Path) -> str:
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("PyMuPDF is required for text-layer PTR parsing") from exc
    try:
        document = fitz.open(path)
        with document:
            return "\n".join(page.get_text("text") for page in document)
    except Exception as exc:
        raise RuntimeError(f"cannot read PTR PDF: {path}: {exc}") from exc


def _owner_chunks(text: str) -> list[tuple[str, str]]:
    lines = text.splitlines()
    starts = [(index, line.strip()) for index, line in enumerate(lines) if line.strip().upper() in OWNER_CODES]
    chunks: list[tuple[str, str]] = []
    for position, (start, owner) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        chunk = "\n".join(lines[start + 1:end])
        if "[ST]" in chunk or "[OP]" in chunk or "[AB]" in chunk or "[OT]" in chunk:
            chunks.append((owner.upper(), chunk))
    return chunks


def _quantity(description: str) -> tuple[float | None, str | None]:
    match = re.search(r"([\d,]+(?:\.\d+)?)\s+shares?", description, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(",", "")), "shares"
    match = re.search(r"([\d,]+(?:\.\d+)?)\s+(?:call\s+options?|put options?|puts?|options?)", description, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(",", "")), "contracts"
    return None, None


def parse_text_layer_pdf(path: Path | str, *, source_sha256: str | None = None, report: dict[str, Any] | None = None, minimum_probability: float = 1.0) -> dict[str, Any]:
    """Parse text-layer rows into candidates with the same review schema as OCR."""

    source = Path(path)
    text = _text_from_pdf(source)
    digest = source_sha256 or hashlib.sha256(source.read_bytes()).hexdigest()
    candidates: list[dict[str, Any]] = []
    for row_number, (owner, chunk) in enumerate(_owner_chunks(text), start=1):
        asset_match = ASSET_RE.search(chunk)
        code_match = CODE_RE.search(chunk)
        if not asset_match or not code_match:
            continue
        asset = " ".join(asset_match.group("asset").split())
        asset_type = asset_match.group("asset_type").upper()
        dates = [_normalize_date(value.group(0)) for value in DATE_RE.finditer(chunk)]
        dates = [value for value in dates if value]
        amounts = [" ".join(value.group(0).split()) for value in AMOUNT_RE.finditer(chunk)]
        description_match = DESCRIPTION_RE.search(chunk)
        description = " ".join((description_match.group("description") if description_match else "").split()) or None
        ticker_options = ticker_candidates(asset)
        ticker_match = TICKER_RE.search(asset)
        if ticker_match and not any(item.get("ticker") == ticker_match.group(1) for item in ticker_options):
            ticker_options = [{"ticker": ticker_match.group(1), "issuer": asset, "match": "explicit"}] + ticker_options
        quantity, quantity_unit = _quantity(description or "")
        candidate = {
            "candidate_id": f"{digest[:12]}-text-r{row_number:03d}",
            "page": None,
            "row_y": None,
            "owner_code": owner,
            "asset_name": asset,
            "asset_type_candidates": [asset_type],
            "ticker_candidates": ticker_options,
            "transaction_date": dates[0] if dates else None,
            "notification_date": dates[1] if len(dates) > 1 else None,
            "transaction_codes": [code_match.group("code").upper()],
            "amount_columns": [],
            "amount_range_candidates": amounts or [],
            "average_probability": minimum_probability,
            "description": description,
            "quantity": quantity,
            "quantity_unit": quantity_unit,
            "raw_text": chunk.strip(),
        }
        issues: list[str] = []
        if len(ticker_options) != 1:
            issues.append("ticker_ambiguous")
        if len(amounts) != 1:
            issues.append("amount_range_ambiguous")
        candidate["issues"] = issues
        candidate["review_required"] = bool(issues)
        candidate["valid_for_analysis"] = not issues
        candidate["valid_for_curated"] = not issues
        candidate["status"] = "review" if issues else "validated_candidate"
        candidates.append(candidate)
    result = {
        "source_file": str(source),
        "source_sha256": digest,
        "source_type": "text_layer",
        "page_count": None,
        "reports": {key: (report or {}).get(key) for key in ("document_id", "year", "report_kind", "amends_report_id", "lineage_status") if (report or {}).get(key) is not None},
        "pages": [{"page": None, "candidates": candidates, "review_queue": [item for item in candidates if item["review_required"]], "validated_candidates": [item for item in candidates if item["valid_for_analysis"]]}],
        "review_queue": [item for item in candidates if item["review_required"]],
        "validated_candidates": [item for item in candidates if item["valid_for_analysis"]],
    }
    return result
