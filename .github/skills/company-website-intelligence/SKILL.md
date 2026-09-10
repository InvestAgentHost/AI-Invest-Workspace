---
name: company-website-intelligence
description: Read a company's official website(s) page-by-page and produce a structured, topic-organized intelligence report (Markdown + JSONL data tables) whose primary focus is a clear breakdown of the company's departments/business units and their products — the kind of detail annual reports don't spell out — plus concise indexes of leadership, news, strategy, IR documents, customers, and contacts, each claim cited to the exact page it came from.
---

# Company Website Intelligence

You are producing the report an analyst starts a company's public-facing
story from — not another financial model, and not a re-scrape of SEC filings.

This skill has no crawling engine and no batch pipeline. The scripts do only
the mechanical parts — enumerate candidate URLs, fetch one page's raw bytes
on demand, tally coverage — and never clean, summarize, or index page content.
**You** read every page you decide is worth reading, in full, and record what
matters as you go. Breadth across the fixed topic taxonomy is a discipline you
apply while reading, checked mechanically only at the end (see
[topic-taxonomy.md](references/topic-taxonomy.md) and
[depth-and-quality-gates.md](references/depth-and-quality-gates.md)) — there
is no coverage-review gate blocking you mid-run the way a batch crawler would
have one.

This skill is fully independent of `company-deep-investment-research` — it
has no vendored code from it and never reads or writes anything under
`.github/skills/company-deep-investment-research/`.

---

## Source rules

| Tier | Source | Permitted use |
|------|--------|---------------|
| 3 | Company's own official website(s) (`official_domains`) | The company's own public statements — not independently verified. Use for products, leadership, news, strategy, contacts, and an IR *document index* only. |
| **Excluded** | Financial report / 10-K / SEC filing pages | Always excluded (`topics.EXCLUDED_PATH_KEYWORDS`, enforced in `discover_urls.py`/`fetch_page.py`). Filing content belongs to `company-deep-investment-research`'s `ten_k` capability — do not duplicate it here. |
| **Not fetched** | Third-party coverage, analyst notes | Out of scope for this skill entirely. |

Every report produced by this skill carries an explicit Tier-3 caveat in its
header (see [deliverable-contract.md](references/deliverable-contract.md)) —
official-site content is the company's own framing and must be cross-checked
before being treated as independently confirmed fact.

## Inputs

| Input | Required | Notes |
|---|---|---|
| Company name | yes | `target_name` |
| Official domain(s) | yes | `official_domains` — supports multiple sub-brand domains |
| As-of date | yes | `as_of`, ISO date |
| Enabled topics | no | All 8 topics in [topic-taxonomy.md](references/topic-taxonomy.md) — all mandatory, no optional topics |
| Workspace root | yes | Where the run's working files live, e.g. `outputs/company-website-intelligence-<date>/` |

If the official domain is ambiguous (multiple regional sites, a rebrand, a
holding-company vs. product-brand split), **ask the user** which domain(s) to
treat as official before starting — don't guess and silently under-cover the
company.

---

## Workflow

### Phase 0 — Scope

1. Identify the company, its official domain(s), and today's `as_of` date.
2. Read [topic-taxonomy.md](references/topic-taxonomy.md) — all 8 topics are
   mandatory, no per-engagement opt-in/out.
3. Create the workspace directory, e.g. `outputs/company-website-intelligence-<date>/`,
   with `topics/` (Phase 2 drafts), `data/` (Phase 2 JSONL tables),
   `report/` (Phase 4 output). `pages/`, `pages.jsonl`, and `urls.json` are
   created by the scripts themselves.
4. Write `<workspace>/run_config.json`:
   ```json
   {"target_name": "Acme Corporation", "official_domains": ["acme.com"], "as_of": "2026-09-10"}
   ```

### Phase 1 — Discover

```bash
python3 .github/skills/company-website-intelligence/scripts/discover_urls.py \
  --workspace <workspace>
```

Enumerates candidate URLs only — sitemap first, homepage nav links as a
fallback — into `<workspace>/urls.json`. It does not fetch any page's content
for reading. Skim the per-topic count it prints; if a whole topic area has
zero candidates (e.g. no `/leadership` or `/about` path at all), keep that in
mind for Phase 2 — you may need to look harder or eventually declare that
topic `not_found`.

### Phase 2 — Read & Record (THIS IS THE CORE STEP)

Loop through `<workspace>/urls.json`'s `unvisited` entries, picking whichever
URL seems most likely to advance a topic that still needs material:

1. Fetch it:
   ```bash
   python3 .github/skills/company-website-intelligence/scripts/fetch_page.py \
     <url> --workspace <workspace>
   ```
   This saves the raw, unmodified response to `<workspace>/pages/<page_id>.html`
   (or `.pdf` + an extracted `.txt`), records it in `pages.jsonl`, and appends
   any newly-discovered same-domain links to `urls.json` — the frontier grows
   as you read, instead of being fully enumerated up front.
2. **Read the saved file directly** (`Read`/`grep` on the `.html` or `.txt`) —
   no cleaning has been applied, so `<img alt="...">` text, captions,
   `data-*` attributes, and structured data are all still there. This matters
   most for `products_and_segments`: product pages are usually image+caption
   layouts, and reading the raw HTML means nothing gets lost before you see it.
   `products_and_segments` (Business Units & Products) is this report's
   primary focus — it's the reason analysts read this report instead of just
   the 10-K, since annual reports rarely lay out departments and what each
   one actually sells this clearly. When picking the next URL to fetch, bias
   toward anything that looks like it maps a department/business line to its
   products before spending budget on the other 7 topics. When you write this
   topic up, structure the body as one `### <unit_name>` subsection per
   business unit and drill down into each notable product/service (what it
   does, who it's for, pricing — write "Not disclosed" if the site doesn't
   say), tag your own cross-page inferences as `**Inference:**` so they read
   as distinct from direct site claims, and use the Notes section for
   caveats like the site's departments not matching how the company reports
   financial segments — see
   [deliverable-contract.md](references/deliverable-contract.md) for the
   full spec and a worked example.
3. Decide what's worth recording, and append it immediately (don't defer to a
   later synthesis pass):
   - `<workspace>/topics/<topic_id>.md` — Key Facts bullets, each ending in
     `[page_id]` (e.g. `[P0007]`). See
     [deliverable-contract.md](references/deliverable-contract.md) for the
     frontmatter/body format.
   - For the 5 topics with a structured table, also append a row to the
     matching file under `<workspace>/data/`.
   - A single page can feed more than one topic if it genuinely contains
     material for both — decide by content, not by the page's `topic_guess`.
4. Repeat until, across all 8 topics, you judge coverage sufficient or the
   frontier has run dry — there's no batch-size limit or hard gate forcing
   you to stop or continue at any particular point.

Depth matters more than page count: every bullet/row needs a real `[page_id]`
citation, and each topic has a minimum depth threshold before it can be
marked `covered` — see
[depth-and-quality-gates.md](references/depth-and-quality-gates.md). If the
site genuinely has thin material for a topic, mark it `partial` or
`not_found` rather than padding it.

### Phase 3 — Check coverage (advisory, not a gate)

```bash
python3 .github/skills/company-website-intelligence/scripts/check_coverage.py \
  --workspace <workspace> --topics-dir <workspace>/topics
```

Prints, per topic: pages read, the topic draft's current `coverage_status`,
and how many unvisited candidate URLs still guess into it. Use this to decide
whether to go back to Phase 2 for a specific topic before moving on — it's a
judgment aid, not something that blocks progress on its own.

### Phase 4 — Assemble

```bash
python3 .github/skills/company-website-intelligence/scripts/assemble_report.py \
  --topics-dir <workspace>/topics --data-dir <workspace>/data \
  --output-dir <workspace>/report \
  --company "<Company Name>" --domain <official-domain> --as-of <YYYY-MM-DD>
```

Produces `<workspace>/report/official_website_report.md` (table of contents +
per-topic sections, with inline table previews for the 5 topics that have
structured data) and `<workspace>/report/data/*.jsonl`.

### Phase 5 — Validate

```bash
python3 .github/skills/company-website-intelligence/scripts/validate_report.py \
  --workspace <workspace> --topics-dir <workspace>/topics --data-dir <workspace>/data
```

Fails (non-zero exit) if: a required topic has no draft file at all, a topic
claims `covered` without meeting its depth threshold, or any citation
references a `page_id` that isn't in `pages.jsonl`. If it fails, go back to
Phase 2 — never hand-edit the report to make validation pass.

### Phase 6 — Deliver

Send the user `<workspace>/report/official_website_report.md` and the
`data/*.jsonl` files (`SendUserFile`), plus a short coverage summary (topics
covered / partial / not_found, and why any gaps exist).

---

## Expected report structure

See [topic-taxonomy.md](references/topic-taxonomy.md) for the full list.
Sections appear in this fixed order so every report has the same shape:

1. Business Units & Products (+ `business_units.jsonl`) — the primary focus,
   deepened well beyond the other topics; one row per department/business
   line with its products/services listed on that row
2. Company Overview
3. Leadership & Governance (+ `leadership.jsonl`)
4. News & Announcements (+ `timeline.jsonl`, `category=news_and_announcements`)
5. Strategy, Partnerships & M&A (+ `timeline.jsonl`, `category=strategy_partnerships_ma`)
6. Investor Relations Documents Index (+ `ir_documents.jsonl`)
7. Customers & Case Studies
8. Contact & Global Presence

Topics 2-8 are meant to stay concise indexes — don't spend equal reading
budget on them.

## Operating rules

1. Resolve the company's official domain(s). If ambiguous, ask the user.
2. Build the workspace and `run_config.json` (Phase 0).
3. Run the full pipeline: Discover → Read & Record (the core loop) → Check
   coverage → Assemble → Validate → Deliver.
4. If Phase 5 validation fails, fix the underlying gap (read more pages,
   more careful recording) and re-run from Phase 2 — do not patch the
   assembled report directly.
5. Never fetch or cite pages under the financial-report exclusion; that's
   `company-deep-investment-research`'s `ten_k` capability's job.
6. Always read a fetched page's raw content yourself before recording
   anything from it — no script summarizes or cleans a page for you.

## Boundaries

- Never read from or write to `.github/skills/company-deep-investment-research/`.
- Do not invent facts. Every bullet and every table row needs a real citation
  that `validate_report.py` can resolve to a recorded page.
- Do not mark a topic `covered` to satisfy the depth gate — mark it honestly
  and let `partial`/`not_found` stand if the site doesn't have the material.
- Do not re-scrape or duplicate SEC filing content — the IR topic is an index
  (title/type/link) only.
- Do not bulk-fetch every discovered URL "just in case" — fetch a page when
  you've decided it's worth reading, not before.
