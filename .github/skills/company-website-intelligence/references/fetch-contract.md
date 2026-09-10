# Discover/fetch contract

This skill has no batch-crawling engine and no vendored code from
`company-deep-investment-research` — it never has read from or written to
that skill's directory, and doesn't now either. All fetching logic lives in
three small scripts under `scripts/`, built on the standard library plus
PyMuPDF (PDF → text) and PyYAML (topic-draft frontmatter parsing).

The center of gravity is reading, not crawling: `discover_urls.py` only
enumerates candidate URLs — it never fetches page bodies for content.
`fetch_page.py` fetches exactly one URL, on demand, when the Agent decides to
read it. There is no bulk fetch-all-URLs step and no HTML→Markdown cleaning
step anywhere — the Agent always reads the raw saved file directly.

## Source tier

Everything this capability fetches is the company's own website — Tier-3,
"the company's own claim." It is not independently verified. Every report
this skill produces must carry that caveat (see
[deliverable-contract.md](deliverable-contract.md)); official-site content is
supporting color, not a substitute for filings or independent reporting.

## Guardrails

- Domain whitelist (`official_domains` in `run_config.json`) enforced even
  through redirects — `site_fetch.fetch()`'s custom `HTTPRedirectHandler`
  rejects any redirect hop that leaves the whitelist, and the final URL is
  re-checked after the request completes. A redirect off-domain is refused,
  not followed.
- 1 request/second — `site_fetch.polite_sleep()` sleeps before every request;
  `discover_urls.py`/`fetch_page.py` call it once per HTTP request they make.
  Since the Agent invokes `fetch_page.py` once per page as a separate process,
  this is enough to keep the whole session near 1 req/s without any shared
  rate-limiter state.
- Response size cap (`max_bytes`, default 5 MB) enforced via both the
  `content-length` header (when present) and the actual streamed byte count.
- Financial-report / SEC-filing paths are always excluded — see
  `topics.EXCLUDED_PATH_KEYWORDS` / `topics.is_excluded_path()` (substring
  match against the URL: `10-k`, `sec-filing`, `annual-report`,
  `proxy-statement`, `edgar`, etc.). Filing content belongs to
  `company-deep-investment-research`'s `ten_k` capability — do not duplicate
  it here.

## `scripts/site_fetch.py` — shared helpers, no CLI

Both `discover_urls.py` and `fetch_page.py` import this module rather than
re-implementing URL handling:

- `normalize_domain(value)` / `normalize_url(value, base_url=None)` — IDNA
  host encoding, strips `utm_*`/`fbclid`/`gclid`/`mc_cid`/`mc_eid` tracking
  query params, collapses repeated `/` in the path, drops default ports.
- `is_approved_url(url, domains)` — true if the URL's host equals or is a
  subdomain of one of `domains`.
- `extract_approved_links(html, base_url, domains)` — same-domain `<a href>`
  targets from a page, via a small `HTMLParser` subclass; skips
  `mailto`/`tel`/`javascript`/`data` schemes.
- `sitemap_urls(xml, base_url, domains)` / `is_sitemap_index(xml)` —
  regex-based `<loc>...</loc>` extraction from sitemap XML, and a check for
  whether the document is a `<sitemapindex>` (nested sitemaps) vs a plain
  `<urlset>` (page URLs).
- `extract_title(html)` — pulls `<title>` text, used only as a topic-guess
  hint, not for any content cleaning.
- `fetch(url, *, approved_domains, max_bytes=5_000_000, ...)` — one GET via
  `urllib.request`, returns a `FetchedPage(requested_url, final_url,
  status_code, content_type, content)`. Raises `FetchError` if the URL or any
  redirect hop leaves the domain whitelist, or the response exceeds
  `max_bytes`. Retries with exponential backoff (`0.25 * 2**attempt`) on
  transient errors.
- `polite_sleep(min_interval_seconds=1.0)` / `sha256_hex(data)`.

## CLI: `scripts/discover_urls.py`

```
discover_urls.py --workspace <dir>
```

Reads `<dir>/run_config.json` (`{"target_name", "official_domains", "as_of"}`,
written in Phase 0). For each domain: tries `https://<domain>/sitemap.xml`
first (following one level of `<sitemapindex>` nesting, capped at 15 nested
files); if no sitemap is found, falls back to fetching the homepage and
extracting its same-domain nav links. Financial-report paths are dropped at
this stage and never enter the frontier. Writes `<dir>/urls.json`:

```json
[
  {
    "url": "https://acme.com/leadership",
    "discovered_via": "sitemap",
    "topic_guess": "leadership_and_governance",
    "status": "unvisited"
  }
]
```

`topic_guess` is `topics.guess_topic()`'s best-effort label from the URL
alone — a starting hint for the Agent, not authoritative.

## CLI: `scripts/fetch_page.py`

```
fetch_page.py <url> --workspace <dir> [--refetch]
```

Fetches exactly one URL. Rejects it up front if it matches
`topics.is_excluded_path()`. If the URL is already in `pages.jsonl`, prints
the existing record and does nothing (idempotent) unless `--refetch` is
passed. Otherwise: sleeps, fetches, saves the **raw, unmodified** bytes to
`<dir>/pages/<page_id>.<ext>` (`.html`/`.pdf`/`.txt`/`.bin` by content-type),
and for PDFs additionally extracts text via PyMuPDF to a sibling
`<page_id>.txt`. HTML is never cleaned or converted — read the `.html` file
directly. Appends one record to `<dir>/pages.jsonl`:

```json
{
  "page_id": "P0007",
  "url": "https://acme.com/leadership",
  "final_url": "https://acme.com/leadership",
  "fetched_at": "2026-09-10T12:00:00+00:00",
  "http_status": 200,
  "content_type": "text/html; charset=utf-8",
  "raw_path": "pages/P0007.html",
  "text_path": null,
  "byte_size": 48213,
  "sha256": "...",
  "topic_guess": "leadership_and_governance"
}
```

For HTML pages, also extracts same-domain links and appends any not already
in `urls.json` (skipping excluded paths) — this is how the frontier grows as
the Agent reads, instead of an upfront bulk crawl.

## CLI: `scripts/check_coverage.py`

```
check_coverage.py --workspace <dir> --topics-dir <dir>/topics
```

Read-only, advisory. Prints, per topic: pages visited (by `topic_guess`),
the topic draft's declared `coverage_status` (or "no draft"), and how many
unvisited frontier URLs still guess into that topic. Not a gate — the Agent
decides when a topic has enough material, this just informs that judgment.
See [deliverable-contract.md](deliverable-contract.md) for the topic draft
format and [depth-and-quality-gates.md](depth-and-quality-gates.md) for the
depth thresholds `validate_report.py` actually enforces.

## Citations

Every evidence reference in this skill's deliverables is a page id from
`pages.jsonl`: `[page_id]`, e.g. `[P0007]`. There's no line range — the Agent
read the whole raw page before writing the citation, so the citation just
needs to point at a real, recorded page. `validate_report.py` checks every
`[P####]` citation in a topic draft (or table row's `evidence_refs`) against
the set of `page_id`s in `<workspace>/pages.jsonl` and rejects unknown ones.
