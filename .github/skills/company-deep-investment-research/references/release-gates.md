# Release Gates

Use a clean second pass after drafting. The final status cannot exceed the weakest mandatory gate.

These are full-package release gates. For chapter-by-chapter collaboration, apply
the relevant evidence, calculation and writing checks to the requested module;
do not treat unrequested valuation work as a chapter blocker. For a balance-sheet
module, use the [chapter completion criteria](financial-reconstruction.md#67-交付前的完成判定).

## A. Scope and provenance

- **A1 Identity/boundary:** issuer, security, CIK, fiscal periods, accounting, units, currency, consolidation, and as-of date are explicit.
- **A2 Provenance:** material claims and inputs have source IDs, resolvable paths or URLs, locators, and source type; raw artifacts are preserved.

## B. Evidence and routing

- **B1 Sufficiency:** required filing, interim, IR, transcript, industry, and market categories are acquired or honestly dispositioned.
- **B2 Routing:** every material segment, revenue type, legal boundary, and capital path has a mechanism, evidence status, and failure path.

## C. Analytical coverage

- **C1 Industry/operations:** material conclusions contain a causal chain, quantitative anchor where available, counterargument, and monitoring KPI.
- **C2 Risk/strategy:** claims, advantages, risks, and management actions are separated and linked to statement lines, cash, and falsification conditions.

## D. Fundamentals

- **D1 Reconciliation:** three statements, segment bridges, attribution, cash bridge, units, signs, restatements, and APM separation reconcile.
- **D2 Derived analysis:** relevant profitability, liquidity, leverage, working capital, capex, cash conversion, debt/lease, tax, impairment, and route-specific metrics appear in tables or the permitted annotated asset-structure figure before detailed interpretation, or are marked unavailable. An opening conclusion may precede the evidence.
- **D3 Balance-sheet chapter:** where included, explains material historical capital-allocation changes, covers relevant annual and recent data, uses defensible operating working capital, and presents a reconciled asset structure without redundant visuals; follow section 6 of `financial-reconstruction.md`.

## E. Valuation

- **E1 Method/boundary:** selected method fits the route; market price, share count, currency, perimeter, debt, leases, and date are valid.
- **E2 Model completeness:** `Profit Forecast` derives the current-year base and five individual future years; history is visible beside the forecasts. A full valuation also delivers `Valuation Model` under the approved dividend/exit-P/FCF contract, with three saved annual profit paths, restorable drivers, consistent snapshot versions, applicable sensitivities and cell-specific usage instructions. An explicitly requested method exception is documented. Separate dividend/buyback coverage from complete funding and verify capture/restore behavior; a forecast-only request does not require a valuation sheet.

## R. Release

- **R1 Coverage/depth:** every `covered` matrix row is analyzed; unsupported rows are not hidden by a generic disclaimer.
- **R2 Benchmark integrity:** a reference report, if used, affected method only; no reference-company facts, assumptions, or numbers leaked into the target report.
- **R3 Independent review:** validators, parser/calculator checks, Markdown checks, and a clean review pass are recorded. Layout or rendering checks are performed where relevant.
- **R4 Requested charts:** the saved figure answers the analytical question, reconciles to the source data and passes the [chart checks](research-charting.md#核验与交付), including actual Simplified Chinese face/glyph validation and visual inspection at intended reading size. A successful export or bounds check alone cannot pass this gate; only requested/current deliverables remain in the output directory.

## Status rules

| Status | Meaning |
|---|---|
| `PASS` | All mandatory gates pass and no material unresolved evidence remains that invalidates the requested conclusion. |
| `PARTIAL` | The minimum deliverable is complete, but a material evidence, calculation, or valuation gap remains and its consequence is explicit. |
| `BLOCKED` | A required identity, source, calculation, or authorization is missing such that a safe minimum deliverable cannot be produced. |

Never delete an evidence gap or weaken a gate merely to obtain `PASS`.
