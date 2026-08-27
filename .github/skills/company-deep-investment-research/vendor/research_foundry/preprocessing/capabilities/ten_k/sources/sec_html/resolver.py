from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

from .models import SecReference, SecUrls

SEC_ARCHIVE_RE = re.compile(
    r"https?://(?:www\.)?sec\.gov/Archives/edgar/data/(?P<cik>\d+)/(?P<compact>\d{18})(?:/(?P<filename>[^?#]+))?",
    re.IGNORECASE,
)
ACCESSION_DASHED_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")
ACCESSION_COMPACT_RE = re.compile(r"^\d{18}$")


def normalize_cik(cik: str | int) -> str:
    text = str(cik).strip()
    if not text.isdigit():
        raise ValueError(f"CIK must be numeric: {cik!r}")
    return text.lstrip("0") or "0"


def accession_to_compact(accession: str) -> str:
    text = str(accession).strip()
    if ACCESSION_DASHED_RE.match(text):
        return text.replace("-", "")
    if ACCESSION_COMPACT_RE.match(text):
        return text
    raise ValueError(f"Invalid SEC accession number: {accession!r}")


def accession_to_dashed(accession: str) -> str:
    compact = accession_to_compact(accession)
    return f"{compact[:10]}-{compact[10:12]}-{compact[12:]}"


def build_sec_urls(cik: str | int, accession: str) -> SecUrls:
    cik_norm = normalize_cik(cik)
    compact = accession_to_compact(accession)
    dashed = accession_to_dashed(accession)
    base = f"https://www.sec.gov/Archives/edgar/data/{cik_norm}/{compact}/"
    return SecUrls(
        cik=cik_norm,
        accession=dashed,
        accession_compact=compact,
        base_url=base,
        index_json_url=base + "index.json",
        text_url=base + dashed + ".txt",
        index_html_url=base + dashed + "-index.htm",
    )


def resolve_reference(value: str, accession: str | None = None) -> SecReference:
    """Resolve a URL, local path, or CIK+accession pair into a SEC reference."""
    value = str(value).strip()
    if accession is not None:
        urls = build_sec_urls(value, accession)
        return SecReference(
            cik=urls.cik,
            accession=urls.accession,
            accession_compact=urls.accession_compact,
            urls=urls,
        )

    match = SEC_ARCHIVE_RE.match(value)
    if match:
        cik = normalize_cik(match.group("cik"))
        compact = match.group("compact")
        urls = build_sec_urls(cik, compact)
        return SecReference(
            cik=urls.cik,
            accession=urls.accession,
            accession_compact=urls.accession_compact,
            filename=match.group("filename"),
            source_url=value,
            urls=urls,
        )

    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"}:
        return SecReference(source_url=value)

    path = Path(value)
    return SecReference(local_path=str(path), filename=path.name if path.name else None)


def is_sec_archive_url(value: str) -> bool:
    return bool(SEC_ARCHIVE_RE.match(value.strip()))
