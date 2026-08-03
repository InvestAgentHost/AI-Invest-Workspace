"""SEC 8-K candidate detection, LLM classification, and source archiving.

The module intentionally uses only the Python standard library. It queries SEC
submission metadata first and keeps candidate filing text transient until the
LLM returns a high-confidence, evidence-backed relevant classification.
"""

from __future__ import annotations

import hashlib
import html
from html.parser import HTMLParser
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import time
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

SEC_TICKER_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data"
MNA_ITEMS = {"1.01", "1.02", "2.01", "2.05", "8.01", "9.01"}
KEYWORDS = (
    "merger",
    "acquisition",
    "business combination",
    "tender offer",
    "definitive agreement",
    "agreement and plan of merger",
    "divestiture",
    "sale of assets",
    "restructuring",
    "reorganization",
    "strategic alternatives",
    "change of control",
)
EXHIBIT_PREFIXES = ("EX-2", "EX-10", "EX-99")
SKIP_HTML_TAGS = {"script", "style", "svg", "noscript", "template"}
_LAST_SEC_REQUEST_AT = 0.0


class WorkflowError(RuntimeError):
    """An expected workflow failure suitable for reporting to the caller."""


class FilingTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._parts: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        tag = tag.lower()
        if tag in SKIP_HTML_TAGS:
            self._skip_depth += 1
        if tag in {"p", "div", "section", "article", "li", "tr", "h1", "h2", "h3", "h4", "br"}:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in SKIP_HTML_TAGS and self._skip_depth:
            self._skip_depth -= 1
        if tag in {"p", "div", "section", "article", "li", "tr", "h1", "h2", "h3", "h4"}:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        value = data.strip()
        if value:
            self._parts.append(value)

    def text(self) -> str:
        value = html.unescape(" ".join(self._parts))
        value = re.sub(r"[ \t\f\v]+", " ", value)
        value = re.sub(r" *\n *", "\n", value)
        value = re.sub(r"\n{3,}", "\n\n", value)
        return value.strip()


@dataclass
class RuntimeConfig:
    workspace_root: Path
    watchlist_path: Path
    sources_root: Path
    knowledge_root: Path
    report_root: Path
    state_path: Path
    classifications_root: Path
    logs_root: Path
    temp_root: Path
    sec_user_agent: str
    provider: str
    model: str
    api_key: str
    base_url: str
    timeout_seconds: float = 45.0
    retries: int = 2
    sec_request_delay: float = 0.15
    max_document_chars: int = 160000
    json_mode: bool = True


@dataclass
class FilingMetadata:
    ticker: str
    cik: str
    company_name: str
    accession_number: str
    filing_date: str
    acceptance_datetime: str
    form: str
    items: str
    primary_document: str
    primary_description: str

    @property
    def accession_no_dashes(self) -> str:
        return self.accession_number.replace("-", "")

    @property
    def archive_directory_url(self) -> str:
        return f"{SEC_ARCHIVES_URL}/{int(self.cik)}/{self.accession_no_dashes}/"

    @property
    def filing_url(self) -> str:
        return urljoin(self.archive_directory_url, self.primary_document)

    def as_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class Classification:
    is_relevant: bool
    review_status: str
    category: List[str]
    transaction_type: str
    status: str
    company: str
    counterparties: List[str]
    target_or_asset: str
    consideration: Dict[str, Any]
    sec_items: List[str]
    effective_date: Optional[str]
    evidence: List[Dict[str, str]]
    confidence: float
    uncertainties: List[str]
    provider: str
    model: str
    prompt_version: str = "sec-8k-mna-v1"
    generated_at: str = field(default_factory=lambda: utc_now())

    @property
    def archive_allowed(self) -> bool:
        return self.is_relevant and self.review_status == "high_confidence" and bool(self.evidence)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def local_date() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()


def atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(value)
    temporary.replace(path)


def atomic_write_json(path: Path, value: Dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            os.environ.setdefault(key, value.strip().strip('"').strip("'"))


def configured_data_roots(workspace_root: Path) -> Tuple[Path, Path]:
    """Read the two optional roots from the workspace's simple config.yaml.

    The workspace helper normally uses PyYAML. This collector must also run in
    a bare Python environment, so it only parses the two scalar values it owns.
    """
    sources_root = workspace_root / "sources"
    knowledge_root = workspace_root / "knowledge"
    config_path = workspace_root / "config.yaml"
    if not config_path.is_file():
        return sources_root, knowledge_root
    in_paths = False
    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if re.match(r"^paths\s*:\s*$", stripped):
            in_paths = True
            continue
        if in_paths and not raw_line.startswith((" ", "\t")):
            in_paths = False
        if not in_paths or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        value = value.strip().strip('"').strip("'")
        if not value:
            continue
        path = Path(value)
        resolved = path if path.is_absolute() else workspace_root / path
        if key.strip() == "sources":
            sources_root = resolved
        elif key.strip() == "knowledge":
            knowledge_root = resolved
    return sources_root, knowledge_root


def load_runtime_config(
    workspace_root: Path,
    config_path: Optional[Path] = None,
    dotenv_path: Optional[Path] = None,
    provider_override: Optional[str] = None,
    watchlist_override: Optional[Path] = None,
) -> RuntimeConfig:
    load_dotenv(dotenv_path or workspace_root / ".env")
    raw: Dict[str, Any] = {}
    if config_path:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise WorkflowError(f"Config must be a JSON object: {config_path}")

    sources_root, knowledge_root = configured_data_roots(workspace_root)
    provider = (provider_override or os.getenv("LLM_PROVIDER") or raw.get("llm_provider") or "deepseek").lower()
    if provider not in {"deepseek", "aigocode"}:
        raise WorkflowError("LLM provider must be 'deepseek' or 'aigocode'")

    provider_values = raw.get("providers", {}).get(provider, {}) if isinstance(raw.get("providers"), dict) else {}
    prefix = provider.upper()
    default_base = "https://api.deepseek.com" if provider == "deepseek" else ""
    api_key = os.getenv(f"{prefix}_API_KEY", "")
    base_url = os.getenv(f"{prefix}_BASE_URL") or str(provider_values.get("base_url", default_base))
    model = os.getenv(f"{prefix}_MODEL") or str(provider_values.get("model", ""))

    watchlist_value = watchlist_override or raw.get("watchlist_path") or "data/watchlists/sec_8k_targets.txt"
    report_value = raw.get("report_root") or "research/sec_8k_mna_daily"
    logs_value = raw.get("logs_root") or ".local/logs/sec8k"
    timeout = float(raw.get("timeout_seconds", os.getenv("SEC8K_TIMEOUT_SECONDS", "45")))
    retries = int(raw.get("retries", os.getenv("SEC8K_RETRIES", "2")))
    request_delay = float(raw.get("sec_request_delay", os.getenv("SEC8K_REQUEST_DELAY", "0.15")))
    max_chars = int(raw.get("max_document_chars", os.getenv("SEC8K_MAX_DOCUMENT_CHARS", "160000")))
    json_mode = str(raw.get("json_mode", os.getenv("LLM_JSON_MODE", "true"))).lower() not in {"0", "false", "no"}

    return RuntimeConfig(
        workspace_root=workspace_root,
        watchlist_path=workspace_root / Path(watchlist_value),
        sources_root=sources_root,
        knowledge_root=knowledge_root,
        report_root=workspace_root / Path(report_value),
        state_path=knowledge_root / "indexes" / "sec-8k" / "state.json",
        classifications_root=knowledge_root / "indexes" / "sec-8k" / "classifications",
        logs_root=workspace_root / Path(logs_value),
        temp_root=workspace_root / ".local" / "cache" / "sec-8k",
        sec_user_agent=os.getenv("SEC_USER_AGENT") or str(raw.get("sec_user_agent", "")),
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=base_url.rstrip("/"),
        timeout_seconds=timeout,
        retries=retries,
        sec_request_delay=max(0.0, request_delay),
        max_document_chars=max_chars,
        json_mode=json_mode,
    )


def validate_sec_config(config: RuntimeConfig) -> None:
    if not config.sec_user_agent:
        raise WorkflowError("SEC_USER_AGENT is required for SEC requests and must include a contact email")


def validate_live_config(config: RuntimeConfig) -> None:
    validate_sec_config(config)
    if not config.api_key:
        raise WorkflowError(f"{config.provider.upper()}_API_KEY is required for LLM classification")
    if not config.base_url:
        raise WorkflowError(f"{config.provider.upper()}_BASE_URL is required")
    if not config.model:
        raise WorkflowError(f"{config.provider.upper()}_MODEL is required")


def read_watchlist(path: Path) -> List[str]:
    if not path.is_file():
        raise WorkflowError(f"Watchlist not found: {path}")
    tickers: List[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        ticker = re.split(r"[\s,]+", line, maxsplit=1)[0].upper()
        if not re.fullmatch(r"[A-Z0-9.\-]+", ticker):
            raise WorkflowError(f"Invalid ticker in {path}: {ticker}")
        tickers.append(ticker)
    if not tickers:
        raise WorkflowError(f"Watchlist contains no tickers: {path}")
    return sorted(set(tickers))


def request_bytes(url: str, headers: Dict[str, str], timeout: float, retries: int) -> bytes:
    last_error: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            request = Request(url, headers=headers)
            with urlopen(request, timeout=timeout) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            last_error = error
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
    raise WorkflowError(f"Request failed for {url}: {type(last_error).__name__}: {last_error}")


def request_json(url: str, headers: Dict[str, str], timeout: float, retries: int) -> Dict[str, Any]:
    try:
        value = json.loads(request_bytes(url, headers, timeout, retries).decode("utf-8"))
    except json.JSONDecodeError as error:
        raise WorkflowError(f"Invalid JSON returned by {url}: {error}") from error
    if not isinstance(value, dict):
        raise WorkflowError(f"Expected JSON object from {url}")
    return value


def sec_headers(user_agent: str) -> Dict[str, str]:
    return {
        "User-Agent": user_agent,
        "Accept": "application/json, text/html, text/plain;q=0.9, */*;q=0.8",
    }


def sec_request_bytes(config: RuntimeConfig, url: str) -> bytes:
    global _LAST_SEC_REQUEST_AT
    remaining = config.sec_request_delay - (time.monotonic() - _LAST_SEC_REQUEST_AT)
    if remaining > 0:
        time.sleep(remaining)
    try:
        return request_bytes(url, sec_headers(config.sec_user_agent), config.timeout_seconds, config.retries)
    finally:
        _LAST_SEC_REQUEST_AT = time.monotonic()


def company_ticker_map(config: RuntimeConfig) -> Dict[str, Dict[str, str]]:
    try:
        raw = json.loads(sec_request_bytes(config, SEC_TICKER_URL).decode("utf-8"))
    except json.JSONDecodeError as error:
        raise WorkflowError(f"Invalid JSON returned by {SEC_TICKER_URL}: {error}") from error
    result: Dict[str, Dict[str, str]] = {}
    for item in raw.values():
        if not isinstance(item, dict):
            continue
        ticker = str(item.get("ticker", "")).upper()
        cik = str(item.get("cik_str", ""))
        if ticker and cik.isdigit():
            result[ticker] = {
                "cik": cik.zfill(10),
                "company_name": str(item.get("title", ticker)),
            }
    return result


def sec_timestamp(value: str, fallback_date: str) -> datetime:
    if re.fullmatch(r"\d{14}", value or ""):
        return datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return datetime.strptime(fallback_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def recent_filings_for_company(
    config: RuntimeConfig,
    ticker: str,
    cik: str,
    company_name: str,
    cutoff: datetime,
) -> List[FilingMetadata]:
    url = SEC_SUBMISSIONS_URL.format(cik=cik)
    try:
        raw = json.loads(sec_request_bytes(config, url).decode("utf-8"))
    except json.JSONDecodeError as error:
        raise WorkflowError(f"Invalid JSON returned by {url}: {error}") from error
    recent = raw.get("filings", {}).get("recent", {})
    if not isinstance(recent, dict):
        return []
    forms = recent.get("form", [])
    if not isinstance(forms, list):
        return []
    filings: List[FilingMetadata] = []
    for index, form in enumerate(forms):
        if form not in {"8-K", "8-K/A"}:
            continue
        def pick(name: str) -> str:
            values = recent.get(name, [])
            return str(values[index]) if isinstance(values, list) and index < len(values) else ""

        filing_date = pick("filingDate")
        accepted = pick("acceptanceDateTime")
        if not filing_date or sec_timestamp(accepted, filing_date) < cutoff:
            continue
        accession = pick("accessionNumber")
        primary = pick("primaryDocument")
        if not accession or not primary:
            continue
        filings.append(
            FilingMetadata(
                ticker=ticker,
                cik=cik,
                company_name=company_name,
                accession_number=accession,
                filing_date=filing_date,
                acceptance_datetime=accepted,
                form=str(form),
                items=pick("items"),
                primary_document=primary,
                primary_description=pick("primaryDocDescription"),
            )
        )
    return filings


def filing_is_candidate(filing: FilingMetadata) -> bool:
    item_values = {item.strip() for item in re.split(r"[,;]", filing.items) if item.strip()}
    metadata = f"{filing.primary_description} {filing.primary_document}".lower()
    return bool(item_values & MNA_ITEMS) or any(keyword in metadata for keyword in KEYWORDS)


def split_submission_documents(raw_text: str) -> List[Tuple[str, str, str]]:
    documents: List[Tuple[str, str, str]] = []
    for block in re.split(r"<DOCUMENT>", raw_text, flags=re.IGNORECASE)[1:]:
        doc_type = re.search(r"<TYPE>\s*([^\n<]+)", block, flags=re.IGNORECASE)
        filename = re.search(r"<FILENAME>\s*([^\n<]+)", block, flags=re.IGNORECASE)
        text_match = re.search(r"<TEXT>(.*?)(?:</DOCUMENT>|\Z)", block, flags=re.IGNORECASE | re.DOTALL)
        if doc_type and text_match:
            documents.append((doc_type.group(1).strip(), filename.group(1).strip() if filename else "", text_match.group(1)))
    return documents


def html_to_text(value: str) -> str:
    parser = FilingTextExtractor()
    parser.feed(value)
    text = parser.text()
    return text or re.sub(r"\s+", " ", value).strip()


def fetch_candidate_documents(config: RuntimeConfig, filing: FilingMetadata) -> Tuple[str, List[Dict[str, str]]]:
    full_submission_url = urljoin(filing.archive_directory_url, f"{filing.accession_number}.txt")
    raw = sec_request_bytes(config, full_submission_url)
    raw_text = raw.decode("utf-8", errors="replace")
    blocks = split_submission_documents(raw_text)
    selected: List[Dict[str, str]] = []
    for doc_type, filename, body in blocks:
        normalized_type = doc_type.upper()
        is_primary = normalized_type in {"8-K", "8-K/A"}
        is_exhibit = normalized_type.startswith(EXHIBIT_PREFIXES)
        if is_primary or is_exhibit:
            selected.append({
                "type": doc_type,
                "filename": filename,
                "text": html_to_text(body),
            })
    if not selected:
        selected = [{"type": filing.form, "filename": filing.primary_document, "text": html_to_text(raw_text)}]
    return raw_text, selected


def clamp_documents(documents: Sequence[Dict[str, str]], max_chars: int) -> List[Dict[str, str]]:
    remaining = max_chars
    output: List[Dict[str, str]] = []
    for document in documents:
        if remaining <= 0:
            break
        text = document["text"].strip()
        clipped = text[:remaining]
        output.append({"type": document["type"], "filename": document["filename"], "text": clipped})
        remaining -= len(clipped)
    return output


def classification_system_prompt() -> str:
    return """You classify SEC Form 8-K filings for merger and restructuring events.

Return only one JSON object. Use only the filing material supplied by the user.
Do not infer facts that are not stated. A filing is relevant only for: merger,
acquisition, business combination, tender offer, divestiture, operational
restructuring, capital structure restructuring, or termination of such a
transaction. Workforce reductions, exit activities, or impairment are relevant
only when the filing describes a material restructuring action.

Use review_status high_confidence only when evidence explicitly supports the
classification. Use needs_review when the filing may be relevant but the text
does not establish the facts. Every high_confidence or needs_review result must
include one or more short verbatim evidence quotes with a section and source_url.

Required JSON keys: is_relevant, review_status, category, transaction_type,
status, company, counterparties, target_or_asset, consideration, sec_items,
effective_date, evidence, confidence, uncertainties.

Use Simplified Chinese for every human-readable value in the JSON, including
transaction_type, status, company, counterparties, target_or_asset,
consideration.summary, and uncertainties. For a relevant filing, category must
contain one or more Chinese labels selected from: 并购, 资产剥离, 业务重组,
资本结构重组, 要约收购. Express monetary amounts in Chinese units, such as
"19亿美元" rather than "$1.9 billion". Keep evidence.quote as an exact
verbatim quote from the filing in its original language, and keep SEC item
numbers, dates, legal entity names, tickers, and source URLs unchanged.
"""


def classification_user_prompt(filing: FilingMetadata, documents: Sequence[Dict[str, str]]) -> str:
    document_text = "\n\n".join(
        f"--- Document type: {item['type']}; filename: {item['filename']} ---\n{item['text']}"
        for item in documents
    )
    return (
        "SEC filing metadata:\n"
        + json.dumps(filing.as_dict(), ensure_ascii=False, indent=2)
        + f"\nSEC source URL: {filing.filing_url}\n\nFiling documents:\n{document_text}"
    )


def parse_json_content(value: str) -> Dict[str, Any]:
    cleaned = value.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise WorkflowError(f"LLM response was not valid JSON: {error}") from error
    if not isinstance(parsed, dict):
        raise WorkflowError("LLM response must be a JSON object")
    return parsed


def normalize_classification(raw: Dict[str, Any], filing: FilingMetadata, provider: str, model: str) -> Classification:
    is_relevant = bool(raw.get("is_relevant", False))
    review_status = str(raw.get("review_status", "not_relevant"))
    if review_status not in {"high_confidence", "needs_review", "not_relevant"}:
        review_status = "needs_review" if is_relevant else "not_relevant"
    evidence_raw = raw.get("evidence", [])
    evidence: List[Dict[str, str]] = []
    if isinstance(evidence_raw, list):
        for item in evidence_raw:
            if isinstance(item, dict) and str(item.get("quote", "")).strip():
                evidence.append({
                    "quote": str(item.get("quote", "")).strip(),
                    "section": str(item.get("section", "")).strip(),
                    "source_url": str(item.get("source_url") or filing.filing_url).strip(),
                })
    confidence_raw = raw.get("confidence", 0)
    try:
        confidence = max(0.0, min(1.0, float(confidence_raw)))
    except (TypeError, ValueError):
        confidence = 0.0
    if review_status == "high_confidence" and (not is_relevant or not evidence or confidence < 0.75):
        review_status = "needs_review" if evidence else "not_relevant"
        is_relevant = review_status != "not_relevant"
    return Classification(
        is_relevant=is_relevant,
        review_status=review_status,
        category=[str(item) for item in raw.get("category", []) if str(item).strip()] if isinstance(raw.get("category"), list) else [],
        transaction_type=str(raw.get("transaction_type", "")),
        status=str(raw.get("status", "uncertain")),
        company=str(raw.get("company") or filing.company_name),
        counterparties=[str(item) for item in raw.get("counterparties", []) if str(item).strip()] if isinstance(raw.get("counterparties"), list) else [],
        target_or_asset=str(raw.get("target_or_asset", "")),
        consideration=raw.get("consideration", {}) if isinstance(raw.get("consideration"), dict) else {},
        sec_items=[str(item) for item in raw.get("sec_items", []) if str(item).strip()] if isinstance(raw.get("sec_items"), list) else [],
        effective_date=str(raw["effective_date"]) if raw.get("effective_date") else None,
        evidence=evidence,
        confidence=confidence,
        uncertainties=[str(item) for item in raw.get("uncertainties", []) if str(item).strip()] if isinstance(raw.get("uncertainties"), list) else [],
        provider=provider,
        model=model,
    )


def call_provider(config: RuntimeConfig, filing: FilingMetadata, documents: Sequence[Dict[str, str]]) -> Classification:
    payload: Dict[str, Any] = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": classification_system_prompt()},
            {"role": "user", "content": classification_user_prompt(filing, documents)},
        ],
        "temperature": 0,
    }
    if config.json_mode:
        payload["response_format"] = {"type": "json_object"}
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "AI-Invest-SEC8K/1.0",
    }
    url = f"{config.base_url}/chat/completions"
    last_error: Optional[Exception] = None
    for attempt in range(config.retries + 1):
        try:
            request = Request(url, data=body, headers=headers, method="POST")
            with urlopen(request, timeout=config.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
            content = response_payload["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise WorkflowError("LLM response content was not text")
            return normalize_classification(parse_json_content(content), filing, config.provider, config.model)
        except (HTTPError, URLError, TimeoutError, OSError, KeyError, IndexError, json.JSONDecodeError, WorkflowError) as error:
            if isinstance(error, HTTPError):
                detail = error.read().decode("utf-8", errors="replace").strip()[:1000]
                if detail:
                    detail = detail.replace(config.api_key, "[REDACTED]")
                    error = WorkflowError(f"HTTP {error.code}: {detail}")
            last_error = error
            if attempt < config.retries:
                time.sleep(1.5 * (attempt + 1))
    raise WorkflowError(f"{config.provider} classification failed: {type(last_error).__name__}: {last_error}")


def load_state(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {"schema_version": 1, "processed": {}}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise WorkflowError(f"Invalid state file {path}: {error}") from error
    if not isinstance(state, dict):
        raise WorkflowError(f"State file must be a JSON object: {path}")
    state.setdefault("schema_version", 1)
    state.setdefault("processed", {})
    return state


def source_paths(config: RuntimeConfig, filing: FilingMetadata) -> Tuple[Path, Path]:
    directory = config.sources_root / "providers" / "sec" / "8-k" / filing.ticker
    stem = f"{filing.filing_date}_{filing.accession_number}"
    return directory / f"{stem}.txt", directory / f"{stem}.md"


def archive_relevant(
    config: RuntimeConfig,
    filing: FilingMetadata,
    raw_submission: str,
    documents: Sequence[Dict[str, str]],
    classification: Classification,
) -> Tuple[Path, Path, str]:
    raw_path, markdown_path = source_paths(config, filing)
    digest = hashlib.sha256(raw_submission.encode("utf-8")).hexdigest()
    atomic_write_text(raw_path, raw_submission)
    frontmatter = {
        "type": "sec-filing",
        "form": filing.form,
        "ticker": filing.ticker,
        "company_name": filing.company_name,
        "cik": filing.cik,
        "filing_date": filing.filing_date,
        "acceptance_datetime": filing.acceptance_datetime,
        "accession_number": filing.accession_number,
        "sec_url": filing.filing_url,
        "retrieved_at": utc_now(),
        "content_sha256": digest,
        "classification_status": classification.review_status,
    }
    yaml_lines = ["---"] + [f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in frontmatter.items()] + ["---", ""]
    sections = ["# SEC {form} - {ticker} - {date}".format(form=filing.form, ticker=filing.ticker, date=filing.filing_date), ""]
    sections += ["## Provenance", "", f"- SEC filing: {filing.filing_url}", f"- Raw submission: {raw_path.name}", ""]
    for document in documents:
        sections += [f"## {document['type']} {document['filename']}", "", document["text"], ""]
    atomic_write_text(markdown_path, "\n".join(yaml_lines + sections))
    return raw_path, markdown_path, digest


def classification_path(config: RuntimeConfig, filing: FilingMetadata) -> Path:
    return config.classifications_root / f"{filing.accession_number}.json"


def save_classification(
    config: RuntimeConfig,
    filing: FilingMetadata,
    classification: Classification,
    source_markdown: Optional[Path],
    content_sha256: Optional[str],
) -> Path:
    payload = {
        "source_metadata": filing.as_dict(),
        "source_url": filing.filing_url,
        "source_path": str(source_markdown) if source_markdown else None,
        "content_sha256": content_sha256,
        "classification": classification.as_dict(),
    }
    path = classification_path(config, filing)
    atomic_write_json(path, payload)
    return path


def report_events_for_date(config: RuntimeConfig, report_date: str) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    if not config.classifications_root.is_dir():
        return events
    for path in sorted(config.classifications_root.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            classification = payload.get("classification", {})
            generated_at = str(classification.get("generated_at", ""))
            generated_date = datetime.fromisoformat(generated_at).astimezone(ZoneInfo("Asia/Shanghai")).date().isoformat()
        except (AttributeError, OSError, ValueError, json.JSONDecodeError):
            continue
        if generated_date != report_date or classification.get("review_status") not in {"high_confidence", "needs_review"}:
            continue
        metadata = payload.get("source_metadata", {})
        if not isinstance(metadata, dict) or not isinstance(classification, dict):
            continue
        events.append({
            "filing": {**metadata, "filing_url": payload.get("source_url", "")},
            "classification": classification,
            "source_path": payload.get("source_path"),
        })
    return events


def report_markdown(date: str, summary: Dict[str, Any], events: Sequence[Dict[str, Any]]) -> str:
    lines = [f"# SEC 8-K 并购重组事项日报 - {date}", "", "## 执行信息", ""]
    for label, value in (
        ("覆盖股票数量", summary["tickers"]),
        ("查询窗口", summary["window"]),
        ("新增 8-K 元数据数量", summary["filings"]),
        ("候选公告数量", summary["candidates"]),
        ("LLM 分析数量", summary["analyzed"]),
        ("正式归档公告数量", summary["archived"]),
        ("待人工复核数量", summary["needs_review"]),
        ("失败数量", summary["failures"]),
    ):
        lines.append(f"- {label}: {value}")
    lines += ["", "## 高置信度并购或重组事项", ""]
    relevant = [event for event in events if event["classification"]["review_status"] == "high_confidence"]
    reviews = [event for event in events if event["classification"]["review_status"] == "needs_review"]
    if not relevant:
        lines.append("本窗口内未发现高置信度并购重组事项。")
    for event in relevant:
        append_event(lines, event)
    lines += ["", "## 待人工复核事项", ""]
    if not reviews:
        lines.append("无。")
    for event in reviews:
        append_event(lines, event)
    return "\n".join(lines) + "\n"


def append_event(lines: List[str], event: Dict[str, Any]) -> None:
    metadata = event["filing"]
    classification = event["classification"]
    lines += [f"### {metadata['ticker']} - {classification['transaction_type'] or '未分类事项'}", ""]
    lines += [
        f"- 状态: {classification['status']}",
        f"- 分类: {', '.join(classification['category']) or '未提供'}",
        f"- 交易对手: {', '.join(classification['counterparties']) or '未披露'}",
        f"- 标的/资产: {classification['target_or_asset'] or '未披露'}",
        f"- 置信度: {classification['confidence']:.2f}",
        f"- SEC URL: {metadata['filing_url']}",
    ]
    consideration = classification.get("consideration", {})
    if consideration.get("summary"):
        lines.append(f"- 对价/费用: {consideration['summary']}")
    for evidence in classification.get("evidence", []):
        lines.append(f"> {evidence.get('quote', '')}")
    if classification.get("uncertainties"):
        lines.append(f"- 待核实: {'; '.join(classification['uncertainties'])}")
    lines.append("")


def run_daily(
    config: RuntimeConfig,
    lookback_hours: int,
    dry_run: bool,
    retry_failed: bool,
    accessions: Optional[Sequence[str]] = None,
    reclassify: bool = False,
) -> Dict[str, Any]:
    validate_sec_config(config)
    if not dry_run:
        validate_live_config(config)
    tickers = read_watchlist(config.watchlist_path)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    state = load_state(config.state_path)
    processed = state["processed"]
    ticker_map = company_ticker_map(config)
    accession_filter = set(accessions or [])
    candidates: List[FilingMetadata] = []
    summary: Dict[str, Any] = {
        "tickers": len(tickers), "window": f"last {lookback_hours} hours ending {utc_now()}",
        "filings": 0, "candidates": 0, "analyzed": 0, "archived": 0, "needs_review": 0, "failures": 0,
    }
    failures: List[str] = []
    for ticker in tickers:
        mapped = ticker_map.get(ticker)
        if not mapped:
            failures.append(f"{ticker}: CIK mapping not found")
            continue
        try:
            filings = recent_filings_for_company(config, ticker, mapped["cik"], mapped["company_name"], cutoff)
        except WorkflowError as error:
            failures.append(f"{ticker}: {error}")
            continue
        summary["filings"] += len(filings)
        for filing in filings:
            if accession_filter and filing.accession_number not in accession_filter:
                continue
            previous = processed.get(filing.accession_number, {})
            previous_status = previous.get("classification_status") if isinstance(previous, dict) else None
            if previous_status and not reclassify and not (retry_failed and previous_status in {"analysis_failed", "request_failed"}):
                continue
            if filing_is_candidate(filing):
                candidates.append(filing)
    summary["candidates"] = len(candidates)
    if dry_run:
        return {"summary": summary, "candidates": [filing.as_dict() for filing in candidates], "failures": failures}

    events: List[Dict[str, Any]] = []
    for filing in candidates:
        try:
            raw_submission, documents = fetch_candidate_documents(config, filing)
            classification = call_provider(config, filing, clamp_documents(documents, config.max_document_chars))
            summary["analyzed"] += 1
            source_markdown: Optional[Path] = None
            digest: Optional[str] = None
            if classification.archive_allowed:
                _, source_markdown, digest = archive_relevant(config, filing, raw_submission, documents, classification)
                summary["archived"] += 1
            elif classification.review_status == "needs_review":
                summary["needs_review"] += 1
            if classification.review_status in {"high_confidence", "needs_review"}:
                save_classification(config, filing, classification, source_markdown, digest)
                events.append({
                    "filing": {**filing.as_dict(), "filing_url": filing.filing_url},
                    "classification": classification.as_dict(),
                    "source_path": str(source_markdown) if source_markdown else None,
                })
            processed[filing.accession_number] = {
                "classification_status": classification.review_status,
                "is_relevant": classification.is_relevant,
                "checked_at": utc_now(),
                "filing_date": filing.filing_date,
                "source_url": filing.filing_url,
            }
        except WorkflowError as error:
            summary["failures"] += 1
            failures.append(f"{filing.ticker} {filing.accession_number}: {error}")
            processed[filing.accession_number] = {
                "classification_status": "analysis_failed",
                "checked_at": utc_now(),
                "filing_date": filing.filing_date,
                "source_url": filing.filing_url,
                "error": str(error),
            }
    summary["failures"] = len(failures)
    state["last_success_at"] = utc_now()
    atomic_write_json(config.state_path, state)
    report_date = local_date()
    report_events = report_events_for_date(config, report_date)
    report_path = config.report_root / f"{report_date}.md"
    atomic_write_text(report_path, report_markdown(report_date, summary, report_events))
    config.logs_root.mkdir(parents=True, exist_ok=True)
    atomic_write_json(config.logs_root / f"{report_date}.json", {"summary": summary, "failures": failures, "events": report_events})
    return {"summary": summary, "report_path": str(report_path), "events": report_events, "failures": failures}
