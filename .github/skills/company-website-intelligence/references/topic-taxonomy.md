# Topic taxonomy

This is the breadth contract for the whole skill. `scripts/topics.py` is the
executable source of truth (imported by `discover_urls.py`, `fetch_page.py`,
`assemble_report.py`, `validate_report.py`); this file is the human-readable
mirror — keep them in sync if you adjust the taxonomy.

## Why a fixed taxonomy

This skill has no crawling engine that forces topic coverage as a hard gate —
Phase 2 has the Agent read pages and decide, page by page, what's worth
recording and where it belongs. The taxonomy's job is to keep that judgment
aligned across a whole run: every recorded fact lands under one of 8 fixed
topic ids, so a report always has the same shape and `validate_report.py` can
check that no required topic was silently skipped (see
[depth-and-quality-gates.md](depth-and-quality-gates.md) — every topic needs
a draft file, even a short `not_found` one).

`topics.guess_topic()` gives `discover_urls.py`/`fetch_page.py` a best-effort
label for a URL, purely as a hint the Agent can use to pick what to read next
(see [fetch-contract.md](fetch-contract.md)) — it is not authoritative. The
Agent's own reading of a page's actual content decides which topic file(s) it
gets recorded into, including recording the same page's content into more
than one topic if it's genuinely relevant to both.

## The 8 topics

All 8 are mandatory — there is no optional-topic mechanism. `esg_and_
sustainability` and `careers_and_culture` were considered and deliberately
dropped from the taxonomy (not made optional) as out of scope for this
skill's intended use.

| # | `topic_id` | Title | Structured table | Notes |
|---|-----------|-------|-------------------|-------|
| 1 | `products_and_segments` | Business Units & Products | `business_units.jsonl` | **The report's primary focus** — one row per department/business line, its products/services listed as an attribute. Annual reports/10-Ks rarely spell this out; the official website often does |
| 2 | `company_overview` | Company Overview | — | History, mission, HQ, scale |
| 3 | `leadership_and_governance` | Leadership & Governance | `leadership.jsonl` | Board + exec team |
| 4 | `news_and_announcements` | News & Announcements | `timeline.jsonl` (`category=news_and_announcements`) | |
| 5 | `strategy_partnerships_ma` | Strategy, Partnerships & M&A | `timeline.jsonl` (`category=strategy_partnerships_ma`) | Shares the table with #4, split by `category` |
| 6 | `ir_documents_index` | Investor Relations Documents Index | `ir_documents.jsonl` | Index only (title/type/url) — do **not** re-scrape filing bodies, that's the `ten_k` capability's job in `company-deep-investment-research` |
| 7 | `customers_and_case_studies` | Customers & Case Studies | — | |
| 8 | `contact_and_global_presence` | Contact & Global Presence | — | |

Topics #2-#8 are kept as concise indexes — the depth investment goes into #1.

Financial-report / SEC-filing pages are permanently excluded from discovery
and fetching via `topics.EXCLUDED_PATH_KEYWORDS` (a plain substring filter on
the URL — `10-k`, `sec-filing`, `annual-report`, `proxy-statement`, `edgar`,
etc., see [fetch-contract.md](fetch-contract.md)). This boundary is what
keeps this skill from overlapping with `company-deep-investment-research`'s
`ten_k` capability.

## Adjusting the taxonomy

The taxonomy is data, not hardcoded control flow — to add/remove/rename a
topic, edit the `TOPICS` tuple in `scripts/topics.py` (and this table) and
nothing else needs to change: `discover_urls.py`, `fetch_page.py`,
`assemble_report.py`, `validate_report.py`, and `check_coverage.py` all
derive from it. Two things to preserve if you do this:

- Never remove the `EXCLUDED_PATH_KEYWORDS` financial-report exclusion.
- If you rename a `topic_id` that's used as a `timeline.jsonl` `category`
  value, update both topics that reference it.
