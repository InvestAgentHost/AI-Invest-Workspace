# Deliverable contract

Two layers of output, both produced from the Agent's Phase 5 topic drafts by
`scripts/assemble_report.py`:

1. One structured Markdown report, `official_website_report.md`.
2. Four JSONL data tables under `data/`.

## Phase 2 input: one draft file per topic, written incrementally

There's no separate "synthesize" phase — the Agent appends to these files as
it reads each page in Phase 2, not in one final pass at the end. Before
running `assemble_report.py`, every enabled topic (see
[topic-taxonomy.md](topic-taxonomy.md) for the id list) must have
`<topics-dir>/<topic_id>.md`:

```markdown
---
coverage_status: covered
source_count: 4
---
## Key Facts
- Founded in 1998 in Austin, TX. [P0001]
- Headquartered in Austin, TX with offices in 6 countries. [P0001]
- ~4,200 employees as of 2026. [P0003]

## Notes
Any additional narrative context, contradictions between sources, or
material gaps worth flagging.
```

Frontmatter fields:

| Field | Values | Meaning |
|-------|--------|---------|
| `coverage_status` | `covered` \| `partial` \| `not_found` | Whether this topic has enough recorded material — set once, when the Agent decides (informed by `check_coverage.py`, see [fetch-contract.md](fetch-contract.md)) that it has read enough pages for this topic, or that the frontier has run dry. |
| `source_count` | integer | Distinct pages cited in this topic's body/rows. |

Body is free Markdown, but every factual bullet must end with a `[page_id]`
citation, e.g. `[P0007]` — `validate_report.py` checks every citation
resolves to a real page recorded in `<workspace>/pages.jsonl`, and (for
`covered` topics) counts bullets to enforce the depth threshold in
[depth-and-quality-gates.md](depth-and-quality-gates.md). Since the Agent
read the whole raw page directly before citing it, there's no line range to
track — the citation just needs to name a page that was actually fetched.

A **missing** draft file is treated by `assemble_report.py` as `not_found`,
but `validate_report.py` treats a missing file for a *required* topic as a
hard error — the Agent must explicitly write the file (even a short
`not_found` one) rather than silently skip a required topic.

## Phase 2 input: structured data tables

Five topics carry structured rows in addition to prose, appended as the
Agent reads each page (same incremental pattern as the topic drafts). Write
these directly as JSONL at `<data-dir>/<table>.jsonl` (one JSON object per
line, no manifest needed — `assemble_report.py` copies them into
`report/data/` as-is):

### `business_units.jsonl` (topic: `products_and_segments`)

One row per department/business line — **not** one row per individual
product. Two-layer model: the business unit *is* the atomic record, and its
products/services are listed as an attribute of that record.

| Field | Type | Notes |
|-------|------|-------|
| `unit_name` | string | Department/business line name, e.g. "Cloud Infrastructure" |
| `description` | string | What this unit does, its positioning, target market — 2-3 sentences |
| `key_products_or_services` | list[string] | Product/service names under this unit; list as many as the site discloses, not just one |
| `evidence_refs` | list[string] | `[page_id]` citations, non-empty |

### Body requirements for `products_and_segments`

The `key_products_or_services` list is a name index, not the depth itself —
the depth this topic needs to deliver lives in the topic draft's **body**.
For every row in `business_units.jsonl`, the body must have a matching
`### <unit_name>` subsection that drills down from the unit into its
individual products/services. For each product/service worth a mention,
cover:

- **What it does / how it works** — beyond the name, the actual
  functionality or mechanism.
- **Who it's for** — target customer segment or use case.
- **Commercial terms** — pricing or packaging model if the site discloses
  it; if it doesn't, write "Not disclosed" explicitly rather than omitting
  the point or guessing a number.

A small table (`Product/Service | What it does | Who it's for | Pricing`)
or a bullet list both work — the format isn't prescribed, but all three
kinds of information should be covered for each product that's more than a
one-line mention.

Every sentence still needs a `[page_id]` citation per the citation rule
above. When a sentence is the Agent's own synthesis across multiple pages
rather than something one page states outright, prefix it with
`**Inference:**` before the citation, so a reader can tell it apart from a
direct site claim.

Use the topic's `## Notes` section (see the format above) for caveats that
don't fit a single unit's subsection — most usefully for
`products_and_segments`: a mismatch between how the site frames its
departments/business lines (navigation/marketing structure) and how the
company is understood to report its financial segments (that's out of this
skill's scope — see `topic-taxonomy.md` — but worth flagging so a reader
doesn't map one onto the other), stale pages for discontinued/divested
products still live on the site, or marketing claims that couldn't be
corroborated elsewhere on the site.

Example (fictional company, illustrating the structure only):

```markdown
---
coverage_status: covered
source_count: 5
---
## Key Facts
- Organized into three go-to-market business units as of the current site: Cloud Infrastructure, Data Platform, and Professional Services. [P0002]

## Business Units

### Cloud Infrastructure
Sells compute and storage capacity to mid-market and enterprise customers. [P0002]

| Product/Service | What it does | Who it's for | Pricing |
|---|---|---|---|
| Acme Compute | On-demand virtual machines with autoscaling. [P0011] | Enterprises running variable-load workloads. [P0011] | Not disclosed. [P0011] |
| Acme Object Storage | S3-compatible object storage with cross-region replication. [P0012] | Teams needing durable storage for unstructured data. [P0012] | Usage-based, priced per GB/month. [P0012] |

**Inference:** Cloud Infrastructure appears to be the largest of the three units based on page count and homepage prominence, though the site doesn't disclose revenue by unit. [P0002][P0011]

### Data Platform
...

## Notes
The site's three business units don't map cleanly onto how the company is typically covered in financial press, which usually references two segments — worth cross-checking against filings before treating this breakdown as a reporting-segment split. [P0002]
```

### `leadership.jsonl` (topic: `leadership_and_governance`)

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | |
| `title` | string | |
| `role_type` | string | `"board"` or `"executive"` |
| `bio_summary` | string | 1-2 sentences |
| `evidence_refs` | list[string] | |

### `timeline.jsonl` (topics: `news_and_announcements`, `strategy_partnerships_ma` — shared)

| Field | Type | Notes |
|-------|------|-------|
| `date` | string | ISO date or best-known granularity, e.g. `"2026-03"` |
| `category` | string | Must equal the owning topic's id: `news_and_announcements` or `strategy_partnerships_ma` |
| `title` | string | |
| `summary` | string | |
| `evidence_refs` | list[string] | |

### `ir_documents.jsonl` (topic: `ir_documents_index`)

Index only — titles/types/links, not re-scraped filing bodies (the `ten_k`
capability in the original skill owns filing content; see
[topic-taxonomy.md](topic-taxonomy.md)).

| Field | Type | Notes |
|-------|------|-------|
| `document_title` | string | |
| `document_type` | string | e.g. "10-K", "Proxy Statement", "Earnings Presentation" |
| `url` | string | |
| `evidence_refs` | list[string] | Citation for where the link/title was found |

## Phase 4 output: `official_website_report.md`

Produced by `assemble_report.py`. Structure:

```
# <Company> — Official Website Intelligence Report
- As of: <date>
- Domains crawled: <domains>
- Source tier: Tier-3 (company's own public statements...)

## Table of Contents
1. Business Units & Products
2. Company Overview
...

## 1. Business Units & Products
**Coverage:** covered (7 sources)
<topic body>

### Data table: `business_units.jsonl`
| description | evidence_refs | key_products_or_services | unit_name |
|---|---|---|---|
... (first 20 rows, full file at data/business_units.jsonl)

## 2. Company Overview
**Coverage:** covered (4 sources)
<topic body>
```

Table topics get an inline preview (first 20 rows) rendered under their
section for readability, plus the full JSONL copied to `report/data/` — this
is the direct fix for "not intuitive": a reader sees a real table, not a
promise that data exists somewhere.

## Phase 6: delivery

No packaging/publish step — there's no vendored engine and no immutable-
snapshot primitive to invoke. Once Phase 5 (`validate_report.py`) passes,
send the user `report/official_website_report.md` and `report/data/*.jsonl`
directly (`SendUserFile`), plus a short coverage summary (which topics are
`covered`/`partial`/`not_found`, and why any gaps exist).
