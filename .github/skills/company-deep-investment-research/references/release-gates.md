# Release Gates

Use a clean second pass after drafting. The final status cannot exceed the weakest mandatory gate.

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
- **D2 Derived analysis:** profitability, liquidity, leverage, working capital, capex, cash conversion, debt/lease, tax, impairment, and route-specific metrics are shown before narrative or marked unavailable.

## E. Valuation

- **E1 Method/boundary:** selected method fits the route; market price, share count, currency, perimeter, debt, leases, and date are valid.
- **E2 Model completeness:** assumptions precede results; component bridge, scenarios, sensitivities, double-count checks, and shareholder-return convention are explicit.

## R. Release

- **R1 Coverage/depth:** every `covered` matrix row is analyzed; unsupported rows are not hidden by a generic disclaimer.
- **R2 Benchmark integrity:** a reference report, if used, affected method only; no reference-company facts, assumptions, or numbers leaked into the target report.
- **R3 Independent review:** validators, parser/calculator checks, Markdown checks, and a clean review pass are recorded. Layout or rendering checks are performed where relevant.

## Status rules

| Status | Meaning |
|---|---|
| `PASS` | All mandatory gates pass and no material unresolved evidence remains that invalidates the requested conclusion. |
| `PARTIAL` | The minimum deliverable is complete, but a material evidence, calculation, or valuation gap remains and its consequence is explicit. |
| `BLOCKED` | A required identity, source, calculation, or authorization is missing such that a safe minimum deliverable cannot be produced. |

Never delete an evidence gap or weaken a gate merely to obtain `PASS`.
