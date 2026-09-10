# Depth and quality gates

Default thresholds enforced by `scripts/validate_report.py`. These are
starting points, not fixed law — a 3-person startup's website will not have
10 leadership bios. Adjust per engagement by editing `min_key_facts` in
`scripts/topics.py`'s `TOPICS` tuple, and note the adjustment in the Phase 6
delivery summary so the reader knows the bar was lowered/raised on purpose.

## Per-topic minimum depth (`min_key_facts` in `scripts/topics.py`)

| Topic | Default threshold | Unit |
|-------|-------------------|------|
| `products_and_segments` | 4 | `business_units.jsonl` rows (one row per department/business line) |
| `company_overview` | 3 | Key Facts bullets |
| `leadership_and_governance` | 3 | `leadership.jsonl` rows |
| `news_and_announcements` | 3 | `timeline.jsonl` rows (`category=news_and_announcements`) |
| `strategy_partnerships_ma` | 2 | `timeline.jsonl` rows (`category=strategy_partnerships_ma`) |
| `ir_documents_index` | 3 | `ir_documents.jsonl` rows |
| `customers_and_case_studies` | 2 | Key Facts bullets |
| `contact_and_global_presence` | 2 | Key Facts bullets |

`products_and_segments` is this report's primary focus (see
[topic-taxonomy.md](topic-taxonomy.md)) — the row-count threshold above is
only a floor. The real depth requirement is per-row richness, not enforced
mechanically but expected in every row you write (same convention as
`leadership.jsonl`'s "1-2 sentence" `bio_summary` guidance, which also isn't
length-checked): each unit's `description` should say what it does and who
it's for, and `key_products_or_services` should list as many
officially-disclosed products/services as that unit actually has — not one
entry just to clear the threshold.

The depth also has to show up in the topic's **body**, not just in
`business_units.jsonl`'s rows: each unit needs a matching `### <unit_name>`
subsection that drills into its products/services individually — what each
one does, who it's for, and pricing/commercial terms (write "Not disclosed"
explicitly when the site doesn't say, rather than skipping the point). See
[deliverable-contract.md](deliverable-contract.md) for the full body
structure and a worked example. This is, like the rest of this section,
documentation-level guidance that `validate_report.py` does not mechanically
check (the same convention as `leadership.jsonl`'s "1-2 sentence"
`bio_summary` guidance) — there is no new validation code behind it.

The other 7 topics stay at their existing thresholds and index-level depth;
there's no need to deepen them to match.

A topic marked `coverage_status: covered` (see
[deliverable-contract.md](deliverable-contract.md)) but below its threshold is
a **validation error**, not a warning — it means the Agent over-claimed. If
the site genuinely doesn't have enough material, mark the topic `partial` (or
`not_found`) instead; that's an honest, passing outcome.

## Citation/evidence requirements

- Every Key Facts bullet and every structured-table row must end with at
  least one `[page_id]` citation, e.g. `[P0007]`.
- `validate_report.py` checks every citation against the set of `page_id`s
  recorded in `<workspace>/pages.jsonl` — an unknown page id is always a hard
  error, regardless of coverage status.
- A `covered` topic with prose (no table) and zero citations anywhere in its
  body is a hard error even if the bullet count meets the threshold — text
  without citations is not evidence.

## Source health

There is no separate "cleaning may have lost content" concern in this
skill's pipeline: `fetch_page.py` never converts HTML to Markdown or strips
anything, and the Agent always reads the raw saved file
(`<workspace>/pages/<page_id>.html`, or the PyMuPDF-extracted `.txt` for a
PDF) directly before recording anything from it. Whatever the Agent judges
worth citing, it judged from the actual page content — including `<img
alt="...">` text, captions, and structured data that a Markdown-cleaning step
would have dropped. `products_and_segments` is a good example of the case
this was designed for: product pages are often image+caption layouts, and
reading the raw HTML directly means nothing there gets lost before the Agent
ever sees it.

If a fetch genuinely failed (non-2xx status, or `fetch_page.py` raised
`FetchError`), that page simply isn't in `pages.jsonl` and can't be cited —
treat any topic that depended on it as `partial` and, if the material seems
important, look for another URL that covers the same ground.

## No optional topics

All 8 topics in `scripts/topics.py` are mandatory. `validate_report.py` fails
the run if any topic has no draft file at all — silently dropping a topic is
not allowed, but explicitly writing `not_found` for it is.
