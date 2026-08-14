# Source Acquisition and PDF Evidence Decisions

This reference supplies decision rules for an agent-led evidence intake on a clean computer. It is not a fixed scraper or parser specification: select the appropriate tools and depth for the issuer, source format, language, access conditions and user scope. Use repository-relative paths and preserve originals; `sources/` is ignored external material and `research/` contains durable conclusions.

## 1. Environment check and tool choice

Before research, inspect the available environment and record the chosen approach in `validation-log.md`:

| Capability | Preferred path | Fallback | Required result |
|---|---|---|---|
| Internet/website | browser connector or HTTPS client | user-provided snapshot | URL, status, access timestamp |
| PDF text | `pdftotext`, `pdfplumber`, or bundled PDF capability | OCR after rendering | extracted text plus page map |
| PDF layout | Poppler page rendering or PDF capability | manual page inspection | visual confirmation of tables, signs and footnotes |
| Structured data | XBRL/HTML parser, `pandas`, JSON | hand-built CSV with source rows | reproducible input and parse check |
| Calculations | Workspace calculator with `--strict` | small documented worksheet | formulas, inputs and output log |

The listed paths are examples, not required installations. Choose a suitable available tool, and use a manual or lighter fallback when appropriate. Missing capabilities do not justify silently skipping intake or validation: mark the affected gate `PARTIAL` and state what evidence could not be verified.

## 2. Official website and disclosure discovery

Resolve the canonical official domains from the issuer's filing or stock-exchange profile. Discover and inspect pages relevant to the research question, respecting robots, rate limits, access restrictions and language variants. A full crawl is not required when a current, sufficient snapshot exists. Do not treat a search-result snippet as evidence.

When the number of pages or documents makes a manifest useful, create `sources/companies/<market>/<ticker>-<slug>/web/manifest.csv` with:

```text
source_id,url,canonical_url,title,language,section,accessed_at,http_status,local_path,sha256,content_type,notes
```

Consider, where available and relevant:

1. corporate identity, history, organization, subsidiaries and governance;
2. business/segment/product pages and customer-facing terms;
3. strategy, medium-term plans, targets, policy and capital allocation;
4. IR landing pages, financial highlights, results, presentations, Q&A and archive pages;
5. sustainability, regulatory, privacy and risk pages when financially material;
6. market-data or shareholder pages used only to establish a dated valuation boundary.

For each material page save the raw HTML or a clearly labelled text snapshot. Preserve the original URL, access date, language and content hash when practical. Record redirects, blocked pages, dynamic content, translated inconsistencies and pages that were discovered but not captured. Do not overwrite an earlier snapshot with a new crawl; add an access-date suffix or a new manifest row.

## 3. Online search and source hierarchy

Start with issuer, regulator, local-language disclosure systems, official IR archives and exchange filings; expand to independent market/industry sources only where useful. Design queries from the legal name, ticker, fiscal year, document type, material segment and risk topic, including local-language variants. The exact query set should follow the company's structure and the user's question rather than a fixed checklist.

Log the search date, query, engine/database, selected result, rejection reason for important rejected results, and final source ID in a source note or `source-index.md` when a formal index is useful. Prefer the latest audited consolidated filing; use presentations and website pages to explain operations, not to override audited figures. Use third-party sources for industry context, price/market checks or contradiction detection only, and label them as such.

## 4. Announcement and PDF evidence handling

For every material PDF or downloadable announcement, choose the appropriate level of handling:

1. preserve the original file without editing it; keep the issuer filename when safe and add a stable date/hash suffix on collision;
2. record the URL, document date, access date, language, file metadata and source ID to the degree practical;
3. identify whether it is audited, statutory, preliminary, presentation, Q&A, appendix or third-party;
4. extract text or inspect the rendered page using a method appropriate to the file; retain extracted text as a rebuildable artifact, never as a replacement for the original;
5. extract only the tables and pages needed for the research question, preserving row order, labels, units, signs, blank versus zero, comparative/restated status and note references;
6. visually verify pages when columns, signs, footnotes, charts, OCR or translations could affect meaning;
7. reconcile totals, subtotals, signs, period labels, scope and cross-footing for every number used in the report;
8. record OCR use, unreadable pages, translation uncertainty, table failures and unresolved values in the evidence ledger.

Printed page numbers and PDF page numbers can differ. Record both when they differ. A number without a page/table locator is not research-grade evidence.

## 5. Evidence packet before prose

Do not draft the relevant sections until the evidence packet contains, or explicitly marks unavailable, the sources needed for the selected archetype and user question. A full-company report will usually consider:

- latest authoritative consolidated financial disclosure and relevant comparative periods;
- statutory/accounting/segment/debt/lease/risk notes relevant to the selected model;
- operating, strategy, guidance, Q&A and announcement materials that can change the thesis;
- official identity/history/product/organization pages when needed for the company boundary;
- current dated price, share-count and market-cap inputs only when absolute valuation is requested;
- source manifest, source index, evidence ledger and unresolved-question list for the work performed.

If local-language and English materials disagree, preserve both and resolve using the hierarchy in the main skill. Never translate away a material qualification. If a source category is irrelevant to the issuer or scope, record it as `n.a.` rather than collecting it mechanically.

## 6. Acquisition-attempt log and honest unavailability

For full-company research, maintain an acquisition-attempt log for route-critical questions. The log may live in `validation-log.md` or a separate artifact, but the coverage matrix must be able to reference it.

Use fields equivalent to:

```text
attempt_id, research_question, criticality, source_category, query_or_page,
accessed_at, result, selected_source_id, rejection_or_failure, next_step
```

Do not mark a critical KPI `unavailable` after checking only the annual report. Check or explicitly disposition the latest interim notes, official presentation/Q&A or transcript, relevant operating/product/technology pages, and one independent/counterparty category where corroboration is possible. Record access blocks and genuine non-existence instead of silently omitting the category.

The attempt log does not create a presumption that the evidence is sufficient. It proves that the gap is real. Apply the gate downgrade and minimum `PARTIAL` requirements in [release-gates.md](release-gates.md) when the missing evidence can change a requested conclusion.
