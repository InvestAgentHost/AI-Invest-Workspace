#!/usr/bin/env python3
"""Discover candidate URLs on the official domain(s) — sitemap first, homepage
navigation links as a fallback. Writes `<workspace>/urls.json`, the frontier
the Agent works through page-by-page in Phase 2 (see fetch_page.py).

This script does not fetch page bodies for reading — it only enumerates
candidate URLs. Reading and recording each page's content is the Agent's job.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import site_fetch  # noqa: E402
import topics  # noqa: E402

_MAX_SITEMAP_FILES = 15


def _load_run_config(workspace: Path) -> dict:
    config_path = workspace / "run_config.json"
    if not config_path.exists():
        raise SystemExit(f"missing {config_path} — write it in Phase 0 before running discover_urls.py")
    return json.loads(config_path.read_text(encoding="utf-8"))


def _discover_from_sitemap(domain: str, domains: list[str]) -> tuple[list[str], str] | None:
    sitemap_url = f"https://{domain}/sitemap.xml"
    try:
        response = site_fetch.fetch(sitemap_url, approved_domains=domains)
    except site_fetch.FetchError:
        return None
    xml = response.content.decode("utf-8", errors="replace")

    if site_fetch.is_sitemap_index(xml):
        nested = site_fetch.sitemap_urls(xml, sitemap_url, domains)[:_MAX_SITEMAP_FILES]
        pages: list[str] = []
        for nested_url in nested:
            site_fetch.polite_sleep()
            try:
                nested_response = site_fetch.fetch(nested_url, approved_domains=domains)
            except site_fetch.FetchError:
                continue
            nested_xml = nested_response.content.decode("utf-8", errors="replace")
            for page_url in site_fetch.sitemap_urls(nested_xml, nested_url, domains):
                if page_url not in pages:
                    pages.append(page_url)
        return pages, "sitemap"

    pages = site_fetch.sitemap_urls(xml, sitemap_url, domains)
    return pages, "sitemap"


def _discover_from_homepage(domain: str, domains: list[str]) -> tuple[list[str], str]:
    homepage_url = f"https://{domain}/"
    response = site_fetch.fetch(homepage_url, approved_domains=domains)
    html = response.content.decode("utf-8", errors="replace")
    links = site_fetch.extract_approved_links(html, response.final_url, domains)
    return [homepage_url, *links], "homepage_links"


def discover(workspace: Path) -> list[dict]:
    config = _load_run_config(workspace)
    domains: list[str] = [site_fetch.normalize_domain(d) for d in config["official_domains"]]

    entries: list[dict] = []
    seen: set[str] = set()

    def _add(url: str, discovered_via: str) -> None:
        try:
            normalized = site_fetch.normalize_url(url)
        except ValueError:
            return
        if normalized in seen or topics.is_excluded_path(normalized):
            return
        seen.add(normalized)
        entries.append(
            {
                "url": normalized,
                "discovered_via": discovered_via,
                "topic_guess": topics.guess_topic(normalized),
                "status": "unvisited",
            }
        )

    for domain in config["official_domains"]:
        site_fetch.polite_sleep()
        result = _discover_from_sitemap(domain, domains)
        if not result or not result[0]:
            result = _discover_from_homepage(domain, domains)
        pages, via = result
        for url in pages:
            _add(url, via)

    return entries


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    args = parser.parse_args(argv)

    entries = discover(args.workspace)
    output_path = args.workspace / "urls.json"
    output_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    by_topic: dict[str | None, int] = {}
    for entry in entries:
        by_topic[entry["topic_guess"]] = by_topic.get(entry["topic_guess"], 0) + 1

    print(f"wrote {output_path} ({len(entries)} candidate url(s))")
    for topic_id, count in sorted(by_topic.items(), key=lambda item: (item[0] is None, item[0])):
        print(f"  - {topic_id or '(unclassified)'}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
