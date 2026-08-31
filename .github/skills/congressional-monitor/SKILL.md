---
name: congressional-monitor
description: Analyze U.S. congressional STOCK Act PTR transaction disclosures from the AI Invest Workspace. Use when the user asks about a member's trades, a security bought or sold by members, congressional trading patterns, historical transaction summaries, or disclosed quantity/position-change estimates.
---

# Congressional Monitor

Use the Workspace terminal tool as the execution layer. The user should be able to ask in natural language; run the command yourself and return the result rather than asking the user to execute a script.

Workspace root: `.`

## Decide the analysis

- A broad behavior question such as “最近哪些股票被议员集中买入” maps to
  `behavior-report`; use `summary` or `trades` only for raw counts/details.
- A member question maps to `member` or `trades --member`.
- A ticker/security question maps to `ticker`.
- A question about net additions, reductions, or inferred holdings maps to `positions`.
- A request for a complete answer package for one member/period maps to `report`.
- A question about what data is loaded or whether it is safe to analyze maps to `coverage` or `check`.
- Apply transaction date, direction (`P` purchase/取得, `S` sale/转出, `E` exchange), and asset type (`ST`, `OP`, `AB`, `OT`) filters when the user specifies them.

## Run

From the Workspace root, use the canonical interpreter and JSON output:

```bash
.venv/bin/python -m tools.congressional_monitor.cli summary --json
.venv/bin/python -m tools.congressional_monitor.cli trades --member <member-or-district> --json
.venv/bin/python -m tools.congressional_monitor.cli ticker <TICKER> --json
.venv/bin/python -m tools.congressional_monitor.cli positions --member <member-or-district> --json
.venv/bin/python -m tools.congressional_monitor.cli report --member <member-or-district> --json
.venv/bin/python -m tools.congressional_monitor.cli coverage --json
.venv/bin/python -m tools.congressional_monitor.cli check --json
.venv/bin/python -m tools.congressional_monitor.cli ocr <pdf-path> --pages 1,2 --json
.venv/bin/python -m tools.congressional_monitor.cli ocr-check <ocr-json> --json
.venv/bin/python -m tools.congressional_monitor.cli ocr-parse <ocr-json> --review-output <review-json> --json
.venv/bin/python -m tools.congressional_monitor.cli house-index <YYYYFD.zip> --member <name-or-district> --json
.venv/bin/python -m tools.congressional_monitor.cli ocr-review <review-json> --template-output <decisions-json>
.venv/bin/python -m tools.congressional_monitor.cli ocr-review <review-json> --decisions <decisions-json> --output data/curated/<reviewed-file>.json
.venv/bin/python -m tools.congressional_monitor.cli house-download <document-id> --year <year> --json
.venv/bin/python -m tools.congressional_monitor.cli sync --year <year> --member <name-or-district> --json
.venv/bin/python -m tools.congressional_monitor.cli house-parse <sync-manifest.json> --json
.venv/bin/python -m tools.congressional_monitor.cli house-events <house-parse.json> --json
.venv/bin/python -m tools.congressional_monitor.cli behavior-report <house-events.json> --windows 30,90 --members <member1,member2> --output-md <report.md> --json
.venv/bin/python -m tools.congressional_monitor.cli agent-review <house-parse.json> --output-dir <review-dir> --json
.venv/bin/python -m tools.congressional_monitor.cli agent-review <review-dir>/manifest.json --decisions <decisions.json> --output <curated-output.json>
# 多年度 House 全量增量同步
.venv/bin/python -m tools.congressional_monitor.cli sync --year 2024 --year 2025 --incremental --download --json
.venv/bin/python -m tools.congressional_monitor.cli senate-efd <export.json> --json
.venv/bin/python -m tools.congressional_monitor.cli --senate-file <export.json> cross-report --json
```

Use `--from-date YYYY-MM-DD`, `--to-date YYYY-MM-DD`, `--direction P|S|E`, and `--asset-type ST|OP|AB|OT` as needed. Use `--data-file <path>` (repeatable) when the user asks to include a curated historical-year file. Relative data-file paths are resolved under `data/curated`.

Read the JSON output and write the answer in Chinese unless the user asks for another language. Do not expose environment variables, credentials, or machine-specific absolute paths.

Prefer `report` for a member-and-period request because it returns the filtered
transactions, quantity net-change estimates, coverage, and quality status in a
single response. Run `coverage` before answering a broad “all members” question;
state the actual loaded coverage instead of implying national completeness. If
`check` reports `ok: false`, lead with the data-quality issue and do not present
derived totals as fully validated.

For a scanned PDF or an explicitly requested OCR operation, use `ocr`. It
renders pages locally and sends only selected page images to the GLM OCR
endpoint. The Key must already be present in the local `.env` as
`GLM_OCR_API_KEY`; never ask the user to paste it into chat or print it. If the
Key is absent, report that OCR is not configured and continue with any
text-layer analysis that remains possible.

After OCR, use `ocr-check` on the JSON output or page cache. It is a review gate,
not a transaction importer: report low-confidence blocks, PTR/table/date/amount
signals and missing-field risks. Do not add OCR candidates to curated data until
the relevant rows have been manually or independently validated.

Use `ocr-parse` after the quality check to rebuild conservative row/column
candidates from OCR coordinates. It emits `validated_candidates` only when
asset type, transaction date, exactly one P/S/E direction, exactly one amount
column, and confidence pass; all others go to `review_queue`. Use
`--review-output` to persist that queue under `data/derived/`.

OCR candidates include conservative ticker aliases and the House Clerk A-J statutory amount-range mapping. Treat these as review prefill signals, not issuer identity proof; unknown names remain blank.

Use `house-index` on an official House Clerk annual `YYYYFD.zip` to discover
new PTR document IDs. This is an index/discovery step; it does not download or
curate PDFs automatically. Preserve the ZIP under `sources/` and fetch/parse
individual reports only after review. `filing_type=P` is an original PTR;
`filing_type=A` is an amendment/correction and must remain a separate source
report until an explicit original-report link is available.

Use `house-download` to fetch one discovered PTR PDF. It writes under `sources/providers/house-clerk/<year>/`, verifies SHA-256, limits response size, retries transient failures, and refuses to overwrite an existing file. It does not add the PDF to curated data.

Use `sync` to run the end-to-end preparation flow. It reads one or more annual
indexes (`--year` and `--index-file` may be repeated), de-duplicates repeated
document IDs across years, finds existing or new PTR PDFs, optionally downloads
them with `--download`, and marks text-layer/OCR requirements. It includes P and
A filings by default; narrow with `--filing-types P` when needed. Add `--ocr`
only for a bounded member or `--limit`; the resulting manifest and review
candidates are written under `data/derived/congressional-monitor/sync/` and
never mutate curated data.

`sync` is stateful. It stores a compact snapshot under
`data/derived/congressional-monitor/state/` (or `--state-file`) and adds a
`changes` section to each JSON result. `new_reports` means report IDs absent
from the previous comparable run; `changed_reports` means source/index/content
metadata changed; `status_changes` tracks operational transitions separately;
`new_candidates` tracks OCR candidate IDs. A first run marks the selected scope
as new. Do not interpret a bounded `--limit` run as evidence that omitted
reports were removed.

Add `--incremental` to reuse text-layer and completed OCR metadata when the local
PDF SHA-256 and byte count are unchanged. This avoids repeating OCR in a House
wide batch while preserving the report in the manifest. The state key is the
House document ID (not the annual index year), so a report copied into multiple
annual indexes is compared only once. Amendment rows without an explicit
`amends_report_id` are labeled `unlinked_amendment`; they are not silently
treated as replacements.

Use `house-parse` on a sync manifest to convert text-layer PDFs into normalized
analysis-ready events. It writes a derived JSON containing raw report results,
validated/review candidates, an OCR queue, quality metrics, and an effective
trade view. It never promotes rows to curated data. Use `house-events` on that
JSON for counts by member/security/direction and descriptive alerts such as new
reports, unlinked amendments, a member's first observed ticker, and securities
appearing for multiple members in the supplied window.

Use `behavior-report` for the congressional behavior analysis layer. It accepts
the effective-trade JSON from `house-parse` or the event JSON from
`house-events`, evaluates 30/90-day windows by default and returns ticker
behavior rankings, recent member profiles, buy/sell change
modes, and recent-versus-prior changes. Metrics include buy/sell member counts,
directional member balance, buy participation rate, disclosed member coverage,
repeat buying, first-time attention, explicit quantity net change, amount-band
levels, and party/chamber convergence when available. Use `--members` to focus
the member profile on important legislators without removing them from group
statistics. Its heuristic score is a
screening aid for disclosed behavior, not a return forecast, proof of intent, or
buy/sell recommendation. PTR participation and coverage ratios are not actual
portfolio allocation because PTR does not disclose complete current holdings.
When the user asks for a deliverable, always pass `--output-md` and return the
Markdown report path; keep the JSON as a rebuildable intermediate artifact.
Use `--include-full-period` only when a historical background view is explicitly
requested; the default report should remain focused on current behavior.
The member profile section computes an explainable priority level from
leadership, committee role, media attention, recent trading activity, and
historical coverage. Pass `--member-profiles <json>` when official member
metadata is available; missing role/media dimensions are reported explicitly.
The Markdown report must show the ticker together with its issuer/company name
and include a short, non-valuation business overview for the highlighted
securities. Use the local company-context mapping when available; otherwise
label name-based classification or missing context explicitly.

Use `agent-review` to create resumable review batches for remaining candidates.
Each packet carries report context and raw evidence with a fixed decision schema.
An Agent may return `approved`, `rejected`, or `needs_more_evidence`; only
complete approved rows pass the existing review validation when applied. Packet
preparation does not call an LLM and does not mutate curated data.

Use `ocr-review` to close the OCR loop. Without `--decisions`, it creates an
editable template with `approved`, `rejected`, or `needs_more_evidence` states.
With decisions, it promotes only complete approved rows to a new curated JSON;
it refuses incomplete fields, invalid codes/dates/amount ranges, duplicate IDs,
and overwriting an existing output. Keep the review audit and rejected rows.

House annual indexes expose all members with PTR filings in that year, not a
complete current officeholder roster. Use `house-index` without `--member` for
the full annual filer coverage.

Use `senate-efd` with an official Senate eFD JSON/CSV export saved under
`sources/providers/senate-efd/`. It normalizes common eFD field names to the
same transaction schema and preserves the original source file. The public eFD
search site may block automated requests, so do not claim live Senate coverage
unless an export was actually supplied.

Use `--senate-file` before any analysis subcommand to merge one or more eFD
exports with the curated House snapshot. `cross-report` then reports coverage
by chamber, recent trades, and securities appearing in both chambers. It is a
co-occurrence statistic, not evidence of coordination or intent.

## Interpretation rules

1. Treat PTR rows as official transaction-disclosure facts: transaction date, filing date, report ID, direction code, asset type, owner code, and statutory amount range.
2. Treat `positions` output as a disclosed quantity net-change estimate. It only counts explicit share or option-contract quantities parsed from the report description. `partial` means at least one quantity is missing; `complete_for_explicit_quantities` means all rows in that group had explicit quantities, not that the real portfolio is complete.
3. Never infer an exact dollar amount from an amount range, opening balance, current holding, intent, political knowledge, or illegal insider information.
4. Keep stock shares and option contracts separate. Do not net options against common shares.
5. Preserve unknown quantities, exchange events, owner codes, and filing delays. Explain that PTR is delayed and does not disclose the complete portfolio, short positions, cash, or every derivative.
6. Separate source facts from analyst judgment. If discussing why a trade may have occurred, label it as a hypothesis and do not present it as a fact from the filing.

## Coverage and missing data

The current curated snapshot is a small, auditable sample: Nancy Pelosi's 2026 reports plus selected reports for Josh Gottheimer, Maria Elvira Salazar, and Daniel Crenshaw. It is not a complete House or Senate directory. If a requested member or year is absent, say so explicitly and do not substitute a different member. A scan PDF that cannot be reliably parsed must remain excluded until OCR and validation are complete.

When historical files are available, include them with `--data-file`, check that trade IDs are deduplicated, and state the resulting date range. Do not claim that historical holdings have been reconstructed unless the relevant reports and explicit quantities are present.

## Response shape

For a normal query, give:

- the result in one sentence;
- the key counts or rows, with transaction and filing dates separated;
- official report IDs/links when useful;
- a short data-boundary note when the user could confuse a PTR event with a current holding.

For comparative questions, show both the raw transaction counts and the known quantity net-change estimate. For a missing-data request, explain the coverage gap and the next data source needed (House Clerk annual reports or Senate eFD) instead of fabricating an answer.
