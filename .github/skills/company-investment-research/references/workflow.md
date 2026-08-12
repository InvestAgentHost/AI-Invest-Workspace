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

Do not advance silently when a gate fails.

### Gate A: evidence ready

- material claims have traceable source records and raw/local paths resolve where material was acquired;
- latest audited statements and key notes are identified;
- as-of date and units are written;
- evidence gaps are recorded.

### Gate B: industry intelligible

- primary and secondary business-model archetypes are recorded for every material segment, with the economic unit and excluded modules stated;
- a professional investor unfamiliar with the industry can explain the relevant economic object or cycle (customer transaction, product, project, asset, loan, policy, resource, pipeline or portfolio), who controls it, who pays or funds it, and who bears loss;
- demand/utilization, production/supply, credit/claims, regulatory, pipeline or portfolio drivers are separated according to the selected archetype;
- the relevant supply constraints, competitive bottlenecks or risk constraints are concrete rather than abstract market adjectives;
- route-appropriate KPIs and failure paths are defined.

### Gate C: operating model coherent

- every major business line has an operating unit;
- revenue, profit, cash and capital occupation are connected;
- recurring, one-off, cyclical, finance, insurance, platform, project, resource, pipeline and investment economics are separated where relevant;
- claims of channel reuse, scale economies, network effects, cost advantage, IP, underwriting or moat have verification indicators.

### Gate D: financial statements reconcile

- assets = liabilities + equity within disclosed rounding;
- cash-flow subtotals and cash bridge reconcile;
- parent/NCI profit and equity attribution reconcile;
- restated comparatives, signs, periods, units and perimeter are consistent;
- APMs remain separate from statutory numbers.

### Gate E: valuation bound

- market boundary and shares are sourced and timestamped;
- a valuation anchor appropriate to the selected archetype is defined (normalized earnings, cash flow, NAV, rNPV, reserve value or another explicit basis);
- low/base/high assumptions are monotonic and explained when scenarios are requested;
- SOTP components do not double count assets, debt, interest, or cash when SOTP/NAV is selected;
- unavailable outputs are labeled pending rather than fabricated.

## 5. Reuse and refresh rules

- If an existing official snapshot is current and complete, reuse it and record the reuse decision.
- If the user asks to improve analysis rather than refresh sources, do not re-crawl by default; inspect and rewrite the report using the existing evidence set.
- If a user explicitly says an existing skill is early-stage or not to be used, do not import its report structure or conclusions. You may reuse raw artifacts if they are in scope and provenance is intact.
- Never let a precedent report's headings become a mechanical template. Transfer its reasoning sequence and writing discipline, then adapt to the target company's economics.
