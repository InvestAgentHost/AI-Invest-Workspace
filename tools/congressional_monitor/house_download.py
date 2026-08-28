"""Controlled House Clerk PTR PDF downloader."""

from __future__ import annotations

import hashlib
from pathlib import Path
import time
from typing import Any


DEFAULT_URL_TEMPLATE = "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{document_id}.pdf"


def download_ptr(document_id: str, year: int | str, *, output_dir: Path | str = "sources/providers/house-clerk", url_template: str = DEFAULT_URL_TEMPLATE, timeout_seconds: int = 60, max_retries: int = 2, max_bytes: int = 25 * 1024 * 1024) -> dict[str, Any]:
    """Download one official PTR PDF without overwriting an existing file."""

    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("requests is required for House Clerk downloads") from exc
    document_id = str(document_id).strip()
    year = str(year).strip()
    if not document_id.isdigit() or not year.isdigit():
        raise ValueError("document_id and year must be numeric")
    destination = Path(output_dir) / year / f"{document_id}.pdf"
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite existing PTR PDF: {destination}")
    url = url_template.format(year=year, document_id=document_id)
    response = None
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, stream=True, timeout=timeout_seconds, headers={"User-Agent": "AI-Invest-congressional-monitor/1.0"})
        except requests.RequestException as exc:
            if attempt >= max_retries:
                raise RuntimeError(f"House Clerk download failed: {exc}") from exc
            time.sleep(2**attempt)
            continue
        if response.status_code not in {429, 500, 502, 503, 504} or attempt >= max_retries:
            break
        response.close()
        time.sleep(2**attempt)
    assert response is not None
    if response.status_code >= 400:
        response.close()
        raise RuntimeError(f"House Clerk returned HTTP {response.status_code} for {url}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    size = 0
    try:
        with destination.open("xb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                size += len(chunk)
                if size > max_bytes:
                    raise RuntimeError(f"PTR PDF exceeds max size of {max_bytes} bytes")
                digest.update(chunk)
                handle.write(chunk)
    except Exception:
        if destination.exists():
            destination.unlink()
        raise
    finally:
        response.close()
    return {"document_id": document_id, "year": year, "url": url, "path": str(destination), "bytes": size, "sha256": digest.hexdigest()}
