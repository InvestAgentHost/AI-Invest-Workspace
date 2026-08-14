# Full-Report Release Contract

## Contents

1. Scope and status vocabulary
2. Required full-report artifacts
3. Evidence sufficiency and acquisition attempts
4. Gate contracts
5. Benchmark calibration
6. Minimum PARTIAL deliverable
7. Independent release review
8. Deterministic validation

## 1. Scope and status vocabulary

Apply this contract to full-company deep research, skill evaluations, and any request described as complete, comprehensive, deep, end-to-end, institutional, or comparable to a mature report. Scale it down only when the user explicitly requests a narrower output.

Use these statuses consistently:

| Status | Meaning |
|---|---|
| `PASS` | All mandatory sub-gates for the requested scope pass. No material conclusion depends on an unbounded critical gap. |
| `PASS WITH LIMITATION` | The gate passes, but a non-critical limitation is visible and does not change the requested conclusion. |
| `PARTIAL` | Useful analysis exists, but at least one mandatory sub-gate fails or a critical gap can change a requested conclusion. |
| `BLOCKED` | The requested output cannot be produced responsibly without new evidence, authority, or user input. |
| `n.a.` | The field is economically irrelevant to the routed business. |
| `unavailable` | The field is relevant, but the required acquisition attempts did not produce reliable evidence. |
| `unresolved` | Evidence exists but conflicts, is ambiguous, or cannot yet be adjudicated. |

Do not use `PARTIAL` as permission to shorten evidence-supported sections. A partial report is a complete analysis of what can be established plus a bounded account of what cannot.

## 2. Required full-report artifacts

Maintain these artifacts or equivalent clearly identified sections. They may be combined when that improves readability, but every field must remain inspectable.

| Artifact | Required content |
|---|---|
| research context | issuer, security, legal/reporting perimeter, periods, accounting, units, as-of dates, requested output, preliminary route |
| source index | source ID, title, issuer/publisher, original URL, local path, dates, page/table locator, extraction method, usability |
| evidence ledger | material claim, evidence type, source/locator, contradiction, adopted treatment, confidence |
| acquisition-attempt log | research question, source category checked, query/page, result, rejection or access failure, next step |
| route and operating-unit map | every material segment's archetype, economic unit, workflow, revenue, cost, capital, cash, risk, KPIs and valuation route |
| coverage matrix | material topic, evidence, report section, status, acquisition-attempt reference, consequence of gap |
| financial input and output | normalized source-linked data, reconciliation output, derived metrics and unavailable rows |
| valuation packet | method decision, market boundary, component bridge, assumptions, scenarios, sensitivities, double-count review, pending fields |
| release review | gate decisions, benchmark calibration if applicable, findings, corrections, remaining limitations and release decision |

A coverage matrix row is not `covered` merely because the report mentions the topic. `covered` requires a mechanism, a quantitative anchor when available, a counterargument or failure path, and a monitoring KPI for material conclusions.

## 3. Evidence sufficiency and acquisition attempts

### 3.1 Source-category matrix

For full-company research, cover or explicitly disposition each category:

1. audited/statutory financial and legal disclosure;
2. latest interim and material subsequent events;
3. operating, product, technology, customer or asset evidence;
4. strategy, capital allocation, debt and investor Q&A/APM evidence;
5. governance, incentives and related-party evidence;
6. current market boundary where valuation is in scope;
7. independent industry, regulatory, customer, supplier or competitor evidence used for triangulation.

Official issuer and regulator sources remain primary. For industry structure, competition, market boundaries or disputed company claims, obtain at least one relevant non-issuer source category unless the user prohibits it, the topic is immaterial, or logged attempts fail. Without it, Gate B2 cannot be `PASS`.

### 3.2 Critical KPI exhaustion rule

Do not mark a route-critical KPI `unavailable` after checking only one filing or one page. Before doing so, check and log, where relevant:

- latest audited filing and notes;
- latest interim filing and notes;
- latest official results presentation, prepared remarks, Q&A or transcript;
- relevant official product, technology, customer, asset or regulatory page;
- one independent or counterparty source category when it could corroborate the metric.

Record blocked access and absence explicitly. If a category does not exist or is economically irrelevant, state that instead of fabricating a search. A critical KPI remains a gate failure even after exhaustive attempts; the attempt log establishes honest unavailability, not analytical completeness.

### 3.3 Stop/continue decision

After each acquisition pass, record:

```text
question -> evidence required -> categories checked -> result ->
materiality of remaining gap -> continue / stop as unavailable / escalate
```

Continue when the missing evidence could materially change the economic mechanism, valuation component, or requested conclusion and a reasonable untried source path remains.

## 4. Gate contracts

Report every sub-gate. A parent gate cannot be `PASS` when a mandatory sub-gate is `PARTIAL` or `FAIL`.

### Gate A: evidence

**A1 Provenance integrity**

- identity, accounting, periods, units and perimeter are resolved;
- material sources have IDs, URLs/local paths and locators;
- raw evidence and acquisition failures are preserved.

**A2 Evidence sufficiency**

- the source-category matrix is complete for the requested scope;
- route-critical KPI attempts satisfy the exhaustion rule;
- contradictory evidence is retained and adjudicated;
- evidence is broad enough to analyze, not merely identify, each material segment.

Traceability alone passes A1, not A2.

### Gate B: industry and external context

**B1 Economic intelligibility**

- an unfamiliar investor can explain the economic unit, participants, decision event, product/service flow, money flow, capital path and failure path;
- demand, supply/capacity, bottlenecks, substitutes, regulation and cycle position are concrete.

**B2 Triangulation**

- material issuer claims about market, competition, customers, technology or advantage are tested against permitted non-issuer or counterparty evidence;
- market-share or leadership claims remain company claims unless independently verified.

An issuer-only industry chapter cannot receive B2 `PASS`.

### Gate C: operating model

**C1 Segment coverage**

- every material segment and group bridge has a complete operating-unit record;
- legal/perimeter changes and internal transactions are reconciled.

**C2 Economic closure**

- at least one representative unit/cycle is followed from trigger through delivery, revenue, cost, capital occupation, cash and failure;
- each material segment has route-specific KPIs with values, `n.a.`, `unavailable` or `unresolved` states;
- unavailable critical KPIs reference acquisition attempts and downgrade the gate;
- major movement analysis follows evidence -> mechanical bridge -> driver -> persistence -> implication -> monitoring KPI.

A route table without a narrated unit/cycle does not pass C2.

### Gate D: financial analysis

**D1 Reconciliation integrity**

- balance sheet, cash bridge and parent/NCI attribution reconcile;
- units, signs, periods, restatements and perimeter are consistent;
- APMs remain separate from statutory values.

**D2 Analytical coverage**

- reported statements appear before derived interpretation;
- segment bridge, accounting policy, debt/lease, tax, impairment/restructuring, working capital and APM/earnings-quality bridges are covered or explicitly unavailable after attempts;
- route-relevant metrics are shown in separate readable tables;
- material movements have evidence-backed economic explanations.

Arithmetic correctness passes D1 only. It cannot compensate for missing D2 analysis.

### Gate E: valuation

**E1 Method and boundary validity**

- the selected method fits the routed economics;
- market price, shares, currency, dilution and date are sourced;
- earnings/cash/NAV anchors have valid ownership, lease and perimeter matching;
- invalid methods are rejected explicitly.

**E2 Model completeness**

- each material component is modeled or shown as a pending component in a complete bridge;
- assumptions precede results and trace to facts, judgments or explicit model assumptions;
- low/base/high scenarios and sensitivities are directionally coherent;
- SOTP double-count, debt/cash/NCI/lease, dilution and payout checks pass;
- pending valuation identifies exact evidence and calculation needed to complete it.

A table of directional assumptions without component formulas or a pending bridge does not pass E2.

### Gate R: release quality

**R1 Coverage/depth**

- every material coverage row is supported or correctly downgraded;
- evidence-supported topics have sufficient explanatory resolution for a professional investor;
- a partial status has not been used to omit analysis that available evidence supports.

**R2 Benchmark calibration**

- when a benchmark is named or explicitly selected, structural diagnostics are recorded and material depth variance is justified section by section;
- no facts, assumptions or target-specific structure are copied from the benchmark.

**R3 Independent review and publishing**

- a clean second-pass review challenges gate statuses and coverage claims;
- deterministic checks, rendering and Git checks pass;
- the release decision matches the weakest mandatory sub-gate.

## 5. Benchmark calibration

Use a benchmark only when the user names it or the research context explicitly selects a permitted mature report. Do not search target-company prior research when independence rules forbid it. Prefer a non-target-company benchmark for explanatory resolution and publishing discipline.

Before drafting, record:

- benchmark path and permission basis;
- user audience and scope differences;
- chapter count, subsection count, table count, source-ID breadth and word count as diagnostics, not quotas;
- qualitative patterns to transfer: terminology onboarding, unit-level explanation, statement depth, counterarguments, monitoring and source placement;
- target-specific modules that must differ.

After drafting, compare the same diagnostics. If the candidate is below 50% of the benchmark in at least three of subsection count, table count, unique cited source IDs and word count, treat it as a material depth variance. Gate R2 fails unless `release-review.md` explains, section by section, why the requested scope and economics justify the variance. Passing numeric ratios never proves quality.

## 6. Minimum PARTIAL deliverable

A full-company `PARTIAL` report must still include:

1. complete identity, period, accounting and evidence boundaries;
2. source-category and acquisition-attempt results;
3. industry/economic cycle with triangulation status;
4. detailed operating-unit analysis for every evidence-supported material segment;
5. reported three statements and all defensible financial bridges/metrics;
6. capital allocation, governance, competition, risks and monitoring;
7. a complete valuation architecture with modeled and pending components, not merely a disclaimer;
8. exact failed sub-gates, consequences and next evidence/calculation steps;
9. source index, reproducibility paths and release review.

Missing evidence may make a conclusion pending. It does not justify replacing supported chapters with a short summary.

## 7. Independent release review

After the draft is complete, perform a separate review pass using the report, source index, coverage matrix and validation outputs as the review packet. Do not rely on the writer's memory of intent.

The reviewer must answer:

1. Which `covered` rows are only mentioned rather than analyzed?
2. Which `unavailable` rows lack acquisition-attempt evidence?
3. Can an unfamiliar analyst narrate one representative unit/cycle and cash path for every material route?
4. Does each major conclusion contain mechanism, quantitative anchor, counterargument and monitoring KPI?
5. Are D1 reconciliation and D2 analytical depth rated separately?
6. Does the valuation contain a complete bridge even where components are pending?
7. Does benchmark variance reveal omitted explanation rather than legitimate scope differences?
8. Is the declared release status no better than the weakest mandatory sub-gate?

Record findings and corrections in `release-review.md` or an equivalent section. Use a separate agent only when available and authorized; otherwise do a clean second pass in the same task.

## 8. Deterministic validation

Run `.github/skills/company-investment-research/scripts/validate_research_release.py` for full reports when the required artifacts exist. The script checks structure, source-ID resolution, required artifact presence, Markdown fences, coverage status vocabulary, release-review status and optional benchmark diagnostics.

For a declared full report, the validator applies conservative anti-summary floors of 4,000 language-neutral word units, 8 H2 chapters, 24 H3 subsections, 12 Markdown tables and 10 unique cited source IDs. A word unit is one Latin/alphanumeric word or two CJK characters, rounded up. These are rejection floors, not quality targets: exceeding them does not make a report complete, while falling below them means the output must be narrowed and labelled accordingly rather than released as full-company deep research. Benchmark calibration and qualitative gates remain controlling above the floors.

The script is a guardrail, not a quality oracle. A mechanical pass cannot override a failed qualitative gate. A strict failure must be fixed or recorded as a failed release sub-gate; do not simply rerun without strict mode.
