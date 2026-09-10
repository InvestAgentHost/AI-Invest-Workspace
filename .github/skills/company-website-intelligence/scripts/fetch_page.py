#!/usr/bin/env python3
"""Fetch a single URL on demand and save it raw — no cleaning, no batching.

The Agent calls this once per page it decides to read (Phase 2). The script's
only job is the mechanical part: enforce the domain whitelist and the
financial-report exclusion, rate-limit, save the exact bytes, and record a
`pages.jsonl` entry plus any newly-discovered same-domain links. Reading the
saved file and deciding what's worth recording is the Agent's job, not this
script's — HTML is never converted to Markdown here.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import site_fetch  # noqa: E402
import topics  # noqa: E402

_EXTENSION_BY_CONTENT_TYPE = {
    "text/html": "html",
    "application/xhtml+xml": "html",
    "application/pdf": "pdf",
    "text/plain": "txt",
}


def _load_run_config(workspace: Path) -> dict:
    config_path = workspace / "run_config.json"
    if not config_path.exists():
        raise SystemExit(f"missing {config_path} — write it in Phase 0 before running fetch_page.py")
    return json.loads(config_path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _load_urls(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _content_type_extension(content_type: str) -> str:
    base = content_type.split(";", 1)[0].strip().lower()
    return _EXTENSION_BY_CONTENT_TYPE.get(base, "bin")


def _next_page_id(pages: list[dict]) -> str:
    return f"P{len(pages) + 1:04d}"


def fetch_page(url: str, workspace: Path, *, refetch: bool = False) -> dict:
    config = _load_run_config(workspace)
    domains = [site_fetch.normalize_domain(d) for d in config["official_domains"]]
    normalized_url = site_fetch.normalize_url(url)

    if topics.is_excluded_path(normalized_url):
        raise SystemExit(f"skipped (financial-report path excluded): {normalized_url}")

    pages_path = workspace / "pages.jsonl"
    pages = _read_jsonl(pages_path)
    if not refetch:
        for record in pages:
            if record["url"] == normalized_url:
                print(f"already fetched as {record['page_id']} -> {record['raw_path']} (use --refetch to force)")
                return record

    site_fetch.polite_sleep()
    response = site_fetch.fetch(normalized_url, approved_domains=domains)

    page_id = _next_page_id(pages)
    extension = _content_type_extension(response.content_type)
    pages_dir = workspace / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    raw_path = pages_dir / f"{page_id}.{extension}"
    raw_path.write_bytes(response.content)

    text_path = None
    title = ""
    if extension == "html":
        html = response.content.decode("utf-8", errors="replace")
        title = site_fetch.extract_title(html)
    elif extension == "pdf":
        import fitz  # PyMuPDF — imported lazily, only needed for PDFs

        document = fitz.open(stream=response.content, filetype="pdf")
        text = "\n\n".join(page.get_text() for page in document)
        text_path = pages_dir / f"{page_id}.txt"
        text_path.write_text(text, encoding="utf-8")

    record = {
        "page_id": page_id,
        "url": normalized_url,
        "final_url": response.final_url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "http_status": response.status_code,
        "content_type": response.content_type,
        "raw_path": str(raw_path.relative_to(workspace)),
        "text_path": str(text_path.relative_to(workspace)) if text_path else None,
        "byte_size": len(response.content),
        "sha256": site_fetch.sha256_hex(response.content),
        "topic_guess": topics.guess_topic(f"{normalized_url} {title}"),
    }
    with pages_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    urls_path = workspace / "urls.json"
    entries = _load_urls(urls_path)
    entries_by_url = {entry["url"]: entry for entry in entries}
    if normalized_url in entries_by_url:
        entries_by_url[normalized_url]["status"] = "fetched"

    if extension == "html":
        html = response.content.decode("utf-8", errors="replace")
        for link in site_fetch.extract_approved_links(html, response.final_url, domains):
            if link in entries_by_url or topics.is_excluded_path(link):
                continue
            new_entry = {
                "url": link,
                "discovered_via": f"page:{page_id}",
                "topic_guess": topics.guess_topic(link),
                "status": "unvisited",
            }
            entries_by_url[link] = new_entry
            entries.append(new_entry)

    urls_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--refetch", action="store_true", help="re-fetch even if this URL is already in pages.jsonl")
    args = parser.parse_args(argv)

    record = fetch_page(args.url, args.workspace, refetch=args.refetch)
    print(f"{record['page_id']}: {record['raw_path']} ({record['byte_size']} bytes, {record['content_type']})")
    if record.get("text_path"):
        print(f"  extracted text: {record['text_path']}")
    print("Read the saved file directly before recording anything — no cleaning has been applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
