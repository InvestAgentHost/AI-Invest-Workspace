"""GLM OCR adapter and page-level PDF OCR helpers.

The provider receives rendered page images, never the user's environment or
credentials. OCR responses are cached by source hash and page so retries do
not repeatedly consume API quota.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import mimetypes
import os
import re
from pathlib import Path
import tempfile
import time
from typing import Any, Iterable


DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/"


class OCRError(RuntimeError):
    """Raised for configuration, transport, or provider response errors."""


DATE_PATTERN = re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{1,2}-\d{1,2})\b")
AMOUNT_RANGE_PATTERN = re.compile(r"\$?\s*[\d,]+\s*(?:-|–|—|to)\s*\$?\s*[\d,]+", re.IGNORECASE)
PTR_HEADER_PATTERN = re.compile(r"periodic\s+transaction\s+report|transaction\s+report", re.IGNORECASE)
TABLE_HEADER_PATTERN = re.compile(r"full\s+asset|date\s+of\s+transaction|type\s+of\s+transaction|amount\s+of\s+transaction", re.IGNORECASE)
TRANSACTION_CODE_PATTERN = re.compile(r"\b(?:P|S|E|purchase|sale|exchange)\b", re.IGNORECASE)


@dataclass(frozen=True)
class GLMOCRConfig:
    api_key: str
    base_url: str = DEFAULT_BASE_URL
    tool_type: str = "hand_write"
    language_type: str = "ENG"
    probability: bool = True
    timeout_seconds: int = 60
    max_retries: int = 2

    @classmethod
    def from_env(cls) -> "GLMOCRConfig":
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass
        return cls(
            api_key=os.environ.get("GLM_OCR_API_KEY", "").strip(),
            base_url=os.environ.get("GLM_OCR_BASE_URL", DEFAULT_BASE_URL).strip(),
            tool_type=os.environ.get("GLM_OCR_TOOL_TYPE", "hand_write").strip(),
            language_type=os.environ.get("GLM_OCR_LANGUAGE_TYPE", "ENG").strip(),
            probability=os.environ.get("GLM_OCR_PROBABILITY", "true").lower() not in {"0", "false", "no"},
            timeout_seconds=int(os.environ.get("GLM_OCR_TIMEOUT_SECONDS", "60")),
            max_retries=int(os.environ.get("GLM_OCR_MAX_RETRIES", "2")),
        )

    def validate(self) -> None:
        if not self.api_key:
            raise OCRError("GLM_OCR_API_KEY is not configured; add it to the local .env before OCR")
        if not self.base_url:
            raise OCRError("GLM_OCR_BASE_URL is empty")


class GLMOCRClient:
    def __init__(self, config: GLMOCRConfig | None = None):
        self.config = config or GLMOCRConfig.from_env()
        self.config.validate()

    def ocr_image(self, image_path: Path | str) -> dict[str, Any]:
        """Submit one image and return the provider response plus plain text."""

        try:
            import requests
        except ImportError as exc:
            raise OCRError("requests is required for GLM OCR") from exc
        path = Path(image_path)
        if not path.is_file():
            raise OCRError(f"OCR image not found: {path}")
        endpoint = self.config.base_url.rstrip("/") + "/paas/v4/files/ocr"
        mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
        data = {
            "tool_type": self.config.tool_type,
            "language_type": self.config.language_type,
            "probability": "true" if self.config.probability else "false",
        }
        response = None
        for attempt in range(self.config.max_retries + 1):
            try:
                with path.open("rb") as handle:
                    response = requests.post(
                        endpoint,
                        headers={"Authorization": f"Bearer {self.config.api_key}"},
                        files={"file": (path.name, handle, mime_type)},
                        data=data,
                        timeout=self.config.timeout_seconds,
                    )
            except requests.RequestException as exc:
                if attempt >= self.config.max_retries:
                    raise OCRError(f"GLM OCR request failed: {exc}") from exc
                time.sleep(2**attempt)
                continue
            if response.status_code not in {429, 500, 502, 503, 504} or attempt >= self.config.max_retries:
                break
            time.sleep(2**attempt)
        assert response is not None
        try:
            payload = response.json()
        except ValueError as exc:
            raise OCRError(f"GLM OCR returned non-JSON HTTP {response.status_code}") from exc
        if response.status_code >= 400 or payload.get("status") == "failed" or payload.get("error"):
            message = payload.get("error", {}).get("message") if isinstance(payload.get("error"), dict) else payload.get("message")
            raise OCRError(f"GLM OCR rejected request (HTTP {response.status_code}): {message or 'unknown provider error'}")
        words = payload.get("words_result") or []
        payload["text"] = "\n".join(str(item.get("words", "")) for item in words if item.get("words"))
        probabilities = [item.get("probability", {}).get("average") for item in words if isinstance(item.get("probability"), dict) and item.get("probability", {}).get("average") is not None]
        payload["average_probability"] = sum(probabilities) / len(probabilities) if probabilities else None
        return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ocr_words(payload: dict[str, Any]) -> list[dict[str, Any]]:
    words = payload.get("words_result")
    return [item for item in words if isinstance(item, dict)] if isinstance(words, list) else []


def assess_ocr_page(payload: dict[str, Any], *, low_probability: float = 0.80, review_probability: float = 0.90) -> dict[str, Any]:
    """Assess OCR completeness and confidence without interpreting rows as trades.

    This is deliberately a review gate: signals indicate what was found, while
    ``review_required`` prevents uncertain OCR from entering curated data.
    """

    words = _ocr_words(payload)
    text = str(payload.get("text") or "\n".join(str(item.get("words", "")) for item in words))
    probabilities = [
        item.get("probability", {}).get("average")
        for item in words
        if isinstance(item.get("probability"), dict) and item.get("probability", {}).get("average") is not None
    ]
    average = payload.get("average_probability")
    if average is None and probabilities:
        average = sum(probabilities) / len(probabilities)
    low_blocks = []
    for item in words:
        probability = (item.get("probability") or {}).get("average") if isinstance(item.get("probability"), dict) else None
        if probability is not None and probability < low_probability:
            low_blocks.append({"words": item.get("words", ""), "probability": probability, "location": item.get("location")})
    signals = {
        "ptr_header": bool(PTR_HEADER_PATTERN.search(text)),
        "table_headers": bool(TABLE_HEADER_PATTERN.search(text)),
        "date_candidates": DATE_PATTERN.findall(text),
        "amount_range_candidates": AMOUNT_RANGE_PATTERN.findall(text),
        "transaction_code_candidates": TRANSACTION_CODE_PATTERN.findall(text),
    }
    issues: list[str] = []
    if str(payload.get("status", "succeeded")).lower() not in {"succeeded", "success", "ok"}:
        issues.append("provider_status_not_success")
    if not words:
        issues.append("no_text_blocks")
    if average is None:
        issues.append("missing_probability")
    elif average < review_probability:
        issues.append("low_page_average_probability")
    if low_blocks:
        issues.append("low_confidence_blocks")
    if not signals["ptr_header"]:
        issues.append("ptr_header_not_detected")
    if not signals["table_headers"] and signals["ptr_header"]:
        issues.append("table_headers_not_detected")
    if signals["table_headers"] and not signals["date_candidates"]:
        issues.append("no_date_candidate")
    return {
        "page": payload.get("page"),
        "source_sha256": payload.get("source_sha256"),
        "average_probability": average,
        "word_block_count": len(words),
        "low_confidence_block_count": len(low_blocks),
        "low_confidence_blocks": low_blocks,
        "signals": signals,
        "issues": issues,
        "review_required": bool(issues),
        "status": "review" if issues else "pass",
    }


def assess_ocr_document(payload: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Assess a single OCR page or the multi-page result returned by ``ocr_pdf``."""

    page_payloads = payload.get("pages") if isinstance(payload.get("pages"), list) else [payload]
    assessments = [assess_ocr_page(item, **kwargs) for item in page_payloads if isinstance(item, dict)]
    return {
        "source_file": payload.get("source_file"),
        "source_sha256": payload.get("source_sha256") or next((item.get("source_sha256") for item in page_payloads if isinstance(item, dict)), None),
        "page_count": payload.get("page_count", len(assessments)),
        "review_required": any(item["review_required"] for item in assessments),
        "pages": assessments,
    }


def render_pdf_pages(pdf_path: Path | str, output_dir: Path | str, dpi: int = 220) -> list[Path]:
    """Render PDF pages to PNG using the bundled PyMuPDF runtime."""

    try:
        import fitz
    except ImportError as exc:
        raise OCRError("PyMuPDF is required to render scanned PDF pages") from exc
    source = Path(pdf_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    scale = dpi / 72
    pages: list[Path] = []
    try:
        document = fitz.open(source)
    except Exception as exc:
        raise OCRError(f"cannot open PDF for OCR: {source}") from exc
    with document:
        for index, page in enumerate(document, start=1):
            target = destination / f"page-{index:03d}.png"
            if not target.exists():
                pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
                pixmap.save(target)
            pages.append(target)
    return pages


def _page_numbers(value: Iterable[int] | None, total: int) -> list[int]:
    pages = sorted(set(value or range(1, total + 1)))
    if not pages or pages[0] < 1 or pages[-1] > total:
        raise OCRError(f"page selection must be between 1 and {total}")
    return pages


def ocr_pdf(
    pdf_path: Path | str,
    *,
    client: GLMOCRClient | None = None,
    page_numbers: Iterable[int] | None = None,
    dpi: int = 220,
    cache_dir: Path | str | None = None,
) -> dict[str, Any]:
    """OCR selected pages, caching each response by PDF hash and page number."""

    source = Path(pdf_path)
    if not source.is_file():
        raise OCRError(f"PDF not found: {source}")
    active_client = client or GLMOCRClient()
    root = Path(cache_dir) if cache_dir else Path("data/derived/congressional-monitor/ocr")
    source_hash = _sha256(source)
    with tempfile.TemporaryDirectory(prefix="congressional-ocr-") as temporary:
        images = render_pdf_pages(source, temporary, dpi=dpi)
        selected = _page_numbers(page_numbers, len(images))
        pages: list[dict[str, Any]] = []
        for number in selected:
            cache_file = root / f"{source_hash}-p{number:03d}-d{dpi}.json"
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            if cache_file.exists():
                payload = json.loads(cache_file.read_text(encoding="utf-8"))
                payload["cached"] = True
            else:
                payload = active_client.ocr_image(images[number - 1])
                payload.update({"source_sha256": source_hash, "page": number, "dpi": dpi, "cached": False})
                cache_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            pages.append(payload)
    return {"source_file": str(source), "source_sha256": source_hash, "page_count": len(images), "pages": pages}
