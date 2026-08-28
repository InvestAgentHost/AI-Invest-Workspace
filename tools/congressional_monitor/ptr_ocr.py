"""Layout-aware candidate extraction and validation for OCR'd PTR tables."""

from __future__ import annotations

from datetime import date
import re
from typing import Any, Iterable

from .ocr import assess_ocr_page
from .security_map import amount_range_candidates, ticker_candidates


DATE_RE = re.compile(r"(?<!\d)(\d{1,2})\s*[/.-]\s*(\d{1,2})\s*[/.-]\s*(\d{2,4})(?!\d)")
CHECK_RE = re.compile(r"^(?:x|×|✓|v)$", re.IGNORECASE)
OWNER_CODES = {"DC", "JT", "SP", "DP", "O", "S", "J"}

# Coordinates are in the provider's rendered-image space (220 DPI by default).
# PTR templates keep these columns stable; broad bins tolerate small scan shifts.
TYPE_COLUMNS = ((560, 655, "P"), (655, 705, "S"), (705, 760, "E"))
AMOUNT_COLUMNS = (
    (1180, 1265, "A"), (1265, 1345, "B"), (1345, 1420, "C"),
    (1420, 1490, "D"), (1490, 1570, "E"), (1570, 1645, "F"),
    (1645, 1725, "G"), (1725, 1805, "H"), (1805, 1890, "I"),
    (1890, 1970, "J"), (1970, 2050, "K"), (2050, 2160, "L"),
)


def _blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("words_result") or []
    return [item for item in rows if isinstance(item, dict) and isinstance(item.get("location"), dict)]


def _center(block: dict[str, Any]) -> tuple[float, float]:
    location = block["location"]
    return (float(location.get("left", 0)) + float(location.get("width", 0)) / 2, float(location.get("top", 0)) + float(location.get("height", 0)) / 2)


def _probability(block: dict[str, Any]) -> float | None:
    probability = block.get("probability")
    if isinstance(probability, dict) and probability.get("average") is not None:
        return float(probability["average"])
    return None


def _cluster_rows(blocks: Iterable[dict[str, Any]], tolerance: float = 18) -> list[list[dict[str, Any]]]:
    clusters: list[list[dict[str, Any]]] = []
    for block in sorted(blocks, key=lambda item: (_center(item)[1], _center(item)[0])):
        y = _center(block)[1]
        if not clusters or y - sum(_center(item)[1] for item in clusters[-1]) / len(clusters[-1]) > tolerance:
            clusters.append([block])
        else:
            clusters[-1].append(block)
    return clusters


def _normalize_date(value: str) -> str | None:
    match = DATE_RE.search(value.replace("O", "0").replace("I", "1"))
    if not match:
        return None
    month, day, year = (int(match.group(index)) for index in range(1, 4))
    year += 2000 if year < 100 else 0
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def _column_for_x(x: float, columns: tuple[tuple[int, int, str], ...]) -> str | None:
    for left, right, label in columns:
        if left <= x < right:
            return label
    return None


def _is_checkmark(block: dict[str, Any]) -> bool:
    return bool(CHECK_RE.match(str(block.get("words", "")).strip()))


def _is_data_row(cluster: list[dict[str, Any]]) -> bool:
    for block in cluster:
        x, _ = _center(block)
        text = str(block.get("words", "")).strip()
        if 180 <= x <= 700 and len(text) >= 8 and not DATE_RE.search(text):
            return True
    return False


def _asset_type_candidates(asset_name: str | None) -> list[str]:
    text = str(asset_name or "").upper()
    candidates: list[str] = []
    if re.search(r"\b(?:CALL|PUT|OPTION|WARRANT|CONTRACT)S?\b", text):
        candidates.append("OP")
    if re.search(r"\b(?:CMN|COMMON|ORDINARY|CLASS\s+[ABC])\b", text):
        candidates.append("ST")
    if re.search(r"\b(?:BOND|NOTE|TREASURY|MUNICIPAL)\b", text):
        candidates.append("AB")
    return list(dict.fromkeys(candidates))


def parse_ptr_page(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract conservative transaction candidates from one OCR page.

    The parser emits raw evidence and ambiguity flags. It intentionally does not
    map amount letters to dollar ranges because the range legend can be clipped
    or misread by OCR.
    """

    blocks = _blocks(payload)
    candidates: list[dict[str, Any]] = []
    for row_number, cluster in enumerate(_cluster_rows(blocks), start=1):
        if not _is_data_row(cluster):
            continue
        asset_blocks = []
        owner_blocks = []
        dates: list[str] = []
        type_codes: list[str] = []
        amount_columns: list[str] = []
        for block in cluster:
            x, _ = _center(block)
            text = str(block.get("words", "")).strip()
            normalized_date = _normalize_date(text)
            if normalized_date and 900 <= x <= 1200:
                dates.append(normalized_date)
            if x < 190 and text:
                owner_blocks.append(text)
            if 180 <= x <= 700 and len(text) >= 8 and not DATE_RE.search(text):
                asset_blocks.append(text)
            if _is_checkmark(block):
                type_code = _column_for_x(x, TYPE_COLUMNS)
                if type_code:
                    type_codes.append(type_code)
                amount_column = _column_for_x(x, AMOUNT_COLUMNS)
                if amount_column:
                    amount_columns.append(amount_column)
        asset = " ".join(dict.fromkeys(asset_blocks)).strip() or None
        dates = list(dict.fromkeys(dates))
        type_codes = list(dict.fromkeys(type_codes))
        amount_columns = list(dict.fromkeys(amount_columns))
        probabilities = [value for value in (_probability(item) for item in cluster) if value is not None]
        candidates.append({
            "candidate_id": f"{str(payload.get('source_sha256') or 'ocr')[:12]}-p{int(payload.get('page') or 0):03d}-r{row_number:03d}",
            "page": payload.get("page"),
            "row_y": round(sum(_center(item)[1] for item in cluster) / len(cluster), 1),
            "owner_code": owner_blocks[0] if owner_blocks else None,
            "asset_name": asset,
            "asset_type_candidates": _asset_type_candidates(asset),
            "ticker_candidates": ticker_candidates(asset),
            "transaction_date": dates[0] if dates else None,
            "notification_date": dates[1] if len(dates) > 1 else None,
            "transaction_codes": type_codes,
            "amount_columns": amount_columns,
            "amount_range_candidates": amount_range_candidates(amount_columns),
            "average_probability": sum(probabilities) / len(probabilities) if probabilities else None,
            "raw_blocks": cluster,
        })
    return {
        "page": payload.get("page"),
        "source_sha256": payload.get("source_sha256"),
        "ocr_quality": assess_ocr_page(payload),
        "candidates": candidates,
    }


def validate_ptr_candidate(candidate: dict[str, Any], *, minimum_probability: float = 0.90) -> dict[str, Any]:
    """Validate one candidate and return issues without mutating it."""

    issues: list[str] = []
    if not candidate.get("asset_name"):
        issues.append("missing_asset_name")
    if len(candidate.get("asset_type_candidates") or []) != 1:
        issues.append("asset_type_ambiguous")
    if not candidate.get("transaction_date"):
        issues.append("missing_or_invalid_transaction_date")
    if len(candidate.get("transaction_codes") or []) != 1:
        issues.append("transaction_direction_ambiguous")
    if len(candidate.get("amount_columns") or []) != 1:
        issues.append("amount_range_ambiguous")
    probability = candidate.get("average_probability")
    if probability is None or probability < minimum_probability:
        issues.append("low_candidate_probability")
    result = dict(candidate)
    result["issues"] = issues
    result["review_required"] = bool(issues)
    result["valid_for_curated"] = not issues
    result["status"] = "review" if issues else "validated_candidate"
    return result


def parse_and_validate_page(payload: dict[str, Any], *, minimum_probability: float = 0.90) -> dict[str, Any]:
    parsed = parse_ptr_page(payload)
    validated = [validate_ptr_candidate(item, minimum_probability=minimum_probability) for item in parsed["candidates"]]
    parsed["candidates"] = validated
    parsed["review_queue"] = [item for item in validated if item["review_required"]]
    parsed["validated_candidates"] = [item for item in validated if item["valid_for_curated"]]
    return parsed


def parse_and_validate_document(payload: dict[str, Any], *, minimum_probability: float = 0.90) -> dict[str, Any]:
    pages = payload.get("pages") if isinstance(payload.get("pages"), list) else [payload]
    results = [parse_and_validate_page(page, minimum_probability=minimum_probability) for page in pages if isinstance(page, dict)]
    return {
        "source_file": payload.get("source_file"),
        "source_sha256": payload.get("source_sha256") or next((item.get("source_sha256") for item in pages if isinstance(item, dict)), None),
        "page_count": payload.get("page_count", len(results)),
        "pages": results,
        "review_queue": [item for page in results for item in page["review_queue"]],
        "validated_candidates": [item for page in results for item in page["validated_candidates"]],
    }
