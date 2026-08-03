#!/usr/bin/env python3
"""Crawl a bounded set of public website pages with provenance metadata."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import threading
import time
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


USER_AGENT = "AI-Invest-Research/1.0 (public website research)"
SKIP_TAGS = {"script", "style", "svg", "noscript", "template"}


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._parts: list[str] = []
        self.title = ""
        self.description = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            values = {key.lower(): value or "" for key, value in attrs}
            if values.get("name", "").lower() == "description":
                self.description = values.get("content", "").strip()

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False
        if tag in {"p", "div", "section", "article", "li", "tr", "h1", "h2", "h3", "h4", "br"}:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        value = data.strip()
        if not value:
            return
        if self._in_title:
            self.title = f"{self.title} {value}".strip()
        self._parts.append(value)

    def text(self) -> str:
        value = html.unescape(" ".join(self._parts))
        value = re.sub(r"[ \t\f\v]+", " ", value)
        value = re.sub(r" *\n *", "\n", value)
        value = re.sub(r"\n{3,}", "\n\n", value)
        return value.strip() + "\n"


def read_sitemap_urls(paths: Iterable[Path]) -> list[str]:
    urls: list[str] = []
    for path in paths:
        root = ET.parse(path).getroot()
        for element in root.iter():
            if element.tag.endswith("loc") and element.text:
                urls.append(element.text.strip())
    return urls


def select_urls(
    urls: Iterable[str],
    base_url: str,
    include_roots: set[str],
    exclude_prefixes: tuple[str, ...],
    seeds: Iterable[str],
) -> list[str]:
    base = urlparse(base_url)
    selected = set(seeds)
    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or parsed.netloc != base.netloc:
            continue
        path = parsed.path.strip("/")
        root = path.split("/", 1)[0] if path else ""
        if root not in include_roots:
            continue
        if any(path == prefix or path.startswith(prefix + "/") for prefix in exclude_prefixes):
            continue
        selected.add(url)
    return sorted(selected)


def load_manifest(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    records: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            records[record["url"]] = record
    return records


def write_manifest(path: Path, records: dict[str, dict]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for url in sorted(records):
            handle.write(json.dumps(records[url], ensure_ascii=False, sort_keys=True) + "\n")
    temporary.replace(path)


def crawl_one(url: str, output_dir: Path, timeout: float, retries: int) -> dict:
    url_id = hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]
    raw_relative = f"raw/pages/{url_id}.html"
    text_relative = f"text/pages/{url_id}.txt"
    raw_path = output_dir / raw_relative
    text_path = output_dir / text_relative
    last_error = ""
    for attempt in range(retries + 1):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
            with urlopen(request, timeout=timeout) as response:
                body = response.read()
                status = getattr(response, "status", 200)
                headers = response.headers
                final_url = response.geturl()
            raw_path.write_bytes(body)
            decoded = body.decode("utf-8", errors="replace")
            parser = TextExtractor()
            parser.feed(decoded)
            with text_path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(parser.text())
            return {
                "url": url,
                "final_url": final_url,
                "status": status,
                "content_type": headers.get("Content-Type", ""),
                "etag": headers.get("ETag", ""),
                "last_modified": headers.get("Last-Modified", ""),
                "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "sha256": hashlib.sha256(body).hexdigest(),
                "bytes": len(body),
                "title": parser.title,
                "description": parser.description,
                "raw_path": raw_relative,
                "text_path": text_relative,
                "error": "",
            }
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            last_error = f"{type(error).__name__}: {error}"
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
    return {
        "url": url,
        "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": 0,
        "error": last_error,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--sitemap-glob", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--include-root", action="append", default=[])
    parser.add_argument("--exclude-prefix", action="append", default=[])
    parser.add_argument("--seed-url", action="append", default=[])
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--refresh", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "raw" / "pages").mkdir(parents=True, exist_ok=True)
    (args.output_dir / "text" / "pages").mkdir(parents=True, exist_ok=True)
    sitemap_paths = sorted(Path().glob(args.sitemap_glob))
    urls = select_urls(
        read_sitemap_urls(sitemap_paths),
        args.base_url,
        set(args.include_root),
        tuple(prefix.strip("/") for prefix in args.exclude_prefix),
        args.seed_url,
    )
    manifest_path = args.output_dir / "manifest.jsonl"
    records = load_manifest(manifest_path)
    pending = [url for url in urls if args.refresh or records.get(url, {}).get("status") != 200]
    print(f"Selected {len(urls)} URLs; fetching {len(pending)}; cached {len(urls) - len(pending)}")
    lock = threading.Lock()
    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(crawl_one, url, args.output_dir, args.timeout, args.retries): url
            for url in pending
        }
        for future in concurrent.futures.as_completed(futures):
            record = future.result()
            with lock:
                records[record["url"]] = record
                completed += 1
                if completed % 25 == 0 or completed == len(pending):
                    write_manifest(manifest_path, records)
                    failures = sum(1 for item in records.values() if item.get("status") != 200)
                    print(f"Completed {completed}/{len(pending)}; failures {failures}", flush=True)
    write_manifest(manifest_path, records)
    failures = [item for item in records.values() if item.get("status") != 200 and item["url"] in urls]
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
