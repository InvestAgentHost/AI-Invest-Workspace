# Research Workflow Reference

## Contents

1. Scope and evidence set
2. Source intake and provenance
3. Evidence ledger
4. Stage gates
5. Reuse and refresh rules

## 1. Scope and evidence set

Resolve before drafting:

| Field | Required decision |
|---|---|
| Issuer | Legal name, ticker, market, reporting entity |
| Time | As-of date, latest complete fiscal year, interim period cut-off |
| Accounting | IFRS/GAAP/JGAAP, consolidated versus parent-only, continuing/discontinued operations |
| Units | Currency, million/billion convention, per-share basis, FX treatment |
| Evidence | Official filings, IR presentations/Q&A, official website, market-data timestamp |
| Output | Report path, structured data paths, source index, unresolved-question list |

Never mix a parent-only statement, preliminary release, market snapshot, and audited consolidated statement without labeling the difference.

## 2. Source intake and provenance

Before downloading material, record an environment check in `validation-log.md`: network or browser access, an HTTP/download path, PDF text extraction, PDF page rendering, a CSV/JSON or spreadsheet parser, and a usable Python runtime. If a preferred capability is missing, use the fallback in [source-acquisition-and-pdf.md](source-acquisition-and-pdf.md), record the limitation, and mark the affected gate `PARTIAL` rather than silently skipping it.

Use a bounded, purpose-driven official-source set. Prioritize evidence that can answer the current research questions; do not collect material merely because it belongs to a familiar document category:

1. latest audited annual consolidated financial statements and the latest comparative filing;
2. statutory annual report/securities report and segment/accounting notes;
3. results presentation, APM reconciliation, Q&A/transcript, debt and capital-allocation appendices;
4. official company pages for identity, history, products, strategy, governance, ESG, privacy and organization;
5. current market data only for the valuation boundary, with URL and timestamp.

Preserve externally acquired files under `sources/companies/<market>/<ticker>-<slug>/`. Do not overwrite an earlier snapshot with a new crawl. Write durable conclusions under `research/companies/<market>/<ticker>-<slug>/`. Put small, rebuildable tables under `data/curated/` or `data/derived/` according to `AGENTS.md`.

For every material source used in a conclusion, preserve enough provenance to let another analyst find and inspect it:

```text
[Sxx] title | issuer/original URL | local path | document date | printed/page locator | access/as-of date | usability notes
```

If a PDF is unreadable, blocked, translated inconsistently, or has a sign/column ambiguity, preserve the original and mark the limitation. Do not substitute an unverified copy. For the full crawl, search, download, extraction, OCR, rendering and table-reconciliation sequence, read [source-acquisition-and-pdf.md](source-acquisition-and-pdf.md).

## 3. Evidence ledger

Build the ledger before prose. Every material claim gets one of these types:

| Type | Meaning | Writing treatment |
|---|---|---|
| Official fact | Directly reported in an official filing/page | State directly and cite source/page |
| Company claim | Management, marketing, ranking, forecast, market-share, or IR assertion | Attribute explicitly; do not upgrade to fact |
| Analyst calculation | Deterministic formula from sourced inputs | Show formula and inputs |
| Analyst judgment | Reasoned synthesis or interpretation | Signal judgment and explain evidence |
| Model assumption | Forward scenario parameter or discount | Show assumption, rationale, and sensitivity |
| Unresolved | Missing, contradictory, inaccessible, or unverified evidence | Keep visible with next validation step |

Keep contradictions in a separate section. Examples: management versus statutory revenue, different segment-profit definitions, current market data versus fiscal-year accounts, cash-flow sign errors, and different share-count definitions.

## 4. Stage gates

Do not advance silently when a gate fails. For a full-company report, apply the complete contract in [release-gates.md](release-gates.md) and report every sub-gate. A parent gate inherits the weakest mandatory sub-gate; do not average a failure away.

### Gate A: evidence

**A1 Provenance integrity** requires traceable source records, current audited statements/key notes, as-of dates, units, raw/local paths and recorded gaps.

**A2 Evidence sufficiency** requires the full source-category matrix, an acquisition-attempt log for critical questions, retained contradictions, and enough operating evidence to analyze rather than merely identify every material segment. A narrow but well-indexed filing packet passes A1 only.

### Gate B: industry and external context

**B1 Economic intelligibility** requires routed archetypes, a concrete economic object/cycle, participants, product/service and money flows, demand/supply or risk constraints, route KPIs and failure paths.

**B2 Triangulation** requires permitted non-issuer, regulatory, customer, supplier or competitor evidence for material industry/competition claims. If the user forbids it or logged attempts fail, mark B2 `PARTIAL`; do not promote issuer claims to independent facts.

### Gate C: operating model

**C1 Segment coverage** requires a complete operating-unit record and group bridge for every material business line.

**C2 Economic closure** requires at least one representative unit/cycle carried through trigger, delivery, revenue, cost, capital occupation, cash and failure, plus route-specific KPI states and evidence-backed movement bridges. A route table alone does not pass C2. A critical `unavailable` KPI must reference acquisition attempts and normally makes C2 `PARTIAL`.

### Gate D: financial analysis

**D1 Reconciliation integrity** requires balance-sheet, cash and parent/NCI reconciliations; consistent periods, units, signs, perimeter and restatements; and separation of APMs from statutory values.

**D2 Analytical coverage** separately requires reported statements before interpretation, segment and APM bridges, debt/lease, tax, impairment/restructuring, working-capital and route-relevant metric analysis, plus economic explanations for material movements. Arithmetic correctness cannot pass D2.

### Gate E: valuation

**E1 Method and boundary validity** requires a route-appropriate method, timestamped market/share/dilution inputs, valid ownership/lease/perimeter matching and explicit rejection of invalid methods.

**E2 Model completeness** requires a complete component bridge, formulas or pending formulas, source-linked assumptions, coherent scenarios/sensitivities and double-count/debt/cash/NCI/lease/dilution checks. Directional assumptions without a model or pending component bridge do not pass E2.

### Gate R: release

**R1 Coverage/depth** tests whether every `covered` row is actually analyzed and whether `PARTIAL` was used to omit supported work.

**R2 Benchmark calibration** applies when a permitted benchmark is selected. Material structural variance requires a section-by-section explanation, not a generic scope disclaimer.

**R3 Independent review/publishing** requires a clean second-pass review, deterministic validation, rendering/layout inspection and a release status no better than the weakest sub-gate.

## 5. Reuse and refresh rules

- If an existing official snapshot is current and complete, reuse it and record the reuse decision.
- If the user asks to improve analysis rather than refresh sources, do not re-crawl by default; inspect and rewrite the report using the existing evidence set.
- If a user explicitly says an existing skill is early-stage or not to be used, do not import its report structure or conclusions. You may reuse raw artifacts if they are in scope and provenance is intact.
- Never let a precedent report's headings become a mechanical template. Transfer its reasoning sequence and writing discipline, then adapt to the target company's economics.
