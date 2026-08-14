# Report Publishing and Quality Standard

Use this reference after analysis and before handoff. It defines the minimum standard for a report intended for a professional investor who knows investing but not the issuer's industry. It is adaptive: use the universal spine plus only the business-model modules selected during routing.

## 1. Required architecture

Use `report-outline.md` as an adaptive spine, not a mandatory 23-chapter template. The first chapter is a short orientation: identity, history, legal/reporting boundary, segment map and the required one-sentence company summary. Put industry context before detailed operating conclusions when it clarifies the company; reorder around the production, asset, credit, pipeline or portfolio cycle when that is the company's economic object. Do not put a conclusion-first executive summary ahead of this orientation unless the user explicitly requests one.

## 2. Coverage standard

Before finalizing a full report, make a coverage matrix, table, or equivalent working check for every material segment, legal entity, product/contract type, statement exposure, capital-allocation action, strategic claim, material risk and valuation component. Each item must point to evidence, an analysis section, an acquisition-attempt reference where evidence is missing, the consequence of the gap, and a status of `covered`, `unavailable`, or `unresolved`. An item is `covered` only when the report analyzes its mechanism, quantitative anchor where available, counterargument/failure path and monitoring KPI. For a narrower user request, scale the check to the requested scope.

Minimum coverage includes:

- the relevant industry/competitive context with a concrete economic anchor (customer transaction, production batch, project, asset, loan, policy, pipeline or portfolio position);
- value chain or economic cycle, contract/asset/risk owner, product or output flow, money flow and capital path;
- each major business line's routed operating unit, revenue recognition, cost stack, capital occupation, cash timing and failure path;
- consolidated three statements, accounting policy, segment reconciliation, APM bridge, debt/lease, tax, impairment and working-capital exposures;
- growth, margins, returns, liquidity, leverage, cash conversion and capital intensity where defensible;
- management actions, incentives, governance, regulation, competition, strategy, capital allocation and monitoring KPIs;
- valuation components, market boundary, assumptions, route-appropriate scenario mechanics, sensitivity and double-count treatment where applicable.

## 3. Depth standard

Every major section should move through the following chain, adapted to the selected archetype:

```text
reported evidence -> mechanical bridge where applicable -> economic mechanism -> persistence/counterargument or probability/cycle assessment -> investment implication -> monitoring KPI
```

Do not accept generic labels such as “large market”, “strong moat”, “high quality”, “recurring revenue” or “good management” without identifying the scarce input, contract term, unit economics, capital requirement, quantified anchor or falsification condition. Distinguish company claims from independently verified facts. Where the company does not disclose a needed cohort, margin, churn, credit, claims, capex or cash metric, show an explicit unavailable row, reference the acquisition attempts required by `release-gates.md`, and explain the consequence. Honest unavailability proves a real evidence gap; it does not pass the affected analytical gate.

## 4. Layout and citation standard

- Use one H1 title, stable H2 chapter headings and H3 subsections; do not use heading levels only for visual size.
- Open each chapter with a short scope sentence. Use prose for causal explanation and tables for comparisons, reconciliations, scenarios and evidence status.
- Put assumptions before valuation outputs and reported tables before derived-metric commentary.
- Keep tables narrow enough to render in Markdown; split large tables by period or theme. Include units, period, scope, formula/definition and source ID in or immediately below every table.
- Cite material claims inline using `[Sxx]` IDs that resolve to the source index. For calculations use `[calc:...]` and list the input IDs and formula. For company claims use language such as “公司披露/管理层称”；for analyst judgments use “本报告判断”。
- Mark illustrative examples as illustrative. Never make an illustrative number look like company data.
- Use blockquotes for report scope, limitations or key definitions sparingly. Avoid marketing copy, unexplained acronyms, excessive bolding, decorative separators and dense unbroken paragraphs.
- Keep a balanced final synthesis: established facts, attractive economics, fragile assumptions, upgrade/downgrade evidence and unmodeled items. Do not repeat the full conclusion in every chapter.

## 5. Necessary depth and non-redundancy standard

Write for a professional investor who understands accounting, valuation, and risk but does not yet know the industry. Plain language should reduce decoding effort without reducing analytical depth. Define unfamiliar technical and industry terms at first use; do not explain standard investment concepts unless their issuer-specific meaning differs.

There is no preferred report length, chapter count, paragraph length, or compression ratio. A complex business may require extensive explanation of product technology, physical or digital architecture, demand formation, supply constraints, operating workflows, regulation, contract mechanics, accounting, capital intensity, and valuation. Keep that detail whenever removing it would prevent the reader from understanding causality, distinguishing economic models, evaluating evidence, or identifying a failure path.

The editing objective is not brevity. It is that every passage advances the reader's understanding. Use these rules heuristically:

- Give each chapter a primary analytical responsibility. A chapter may be long and multi-layered when its subject is complex, but another chapter should not perform the same job again.
- Start from a concrete economic object or event when it resolves abstraction, then explain every necessary causal layer. Use additional examples when they reveal genuinely different economics; do not repeat near-identical examples after the mechanism is clear.
- A mechanism may reappear only when the new section adds evidence, another causal layer, a different segment, a new financial-statement consequence, a counterargument, or a changed time horizon. A brief cross-reference is enough otherwise.
- Use tables for real comparison, reconciliation, or classification. Prose should explain patterns, exceptions, mechanisms, and implications rather than recite every cell.
- Prefer precise declarative language, quantified anchors, and explicit qualifications. Avoid rhetorical padding, promotional adjectives, and repeated chapter previews or conclusions.
- Preserve contradictions, unavailable evidence, technical nuance, accounting bridges, counterarguments, sensitivities, and failure conditions. These are analytical depth, not verbosity.

Run two separate passes. The depth pass asks whether the report fully explains the business and all decision-relevant complexity. The non-redundancy pass asks whether any paragraph merely repeats a definition, example, mechanism, table, or conclusion without adding information. Delete or merge only the second category; never use the non-redundancy pass as a mandate to shorten necessary analysis.

After routing and drafting from target-company evidence, optionally read `quality-calibration-cellnex.md`. Compare the target report's causal clarity, depth, evidence boundaries, and non-redundancy. Never make the report resemble Cellnex in headings, sector concepts, KPIs, valuation, or length merely to pass calibration.

## 6. Final rendering and automated checks

Run, as available, Markdown link checks, YAML/CSV/JSON parsers, PDF/page visual checks, the financial calculator in strict mode and `git diff --check`. For a full report, also run `.github/skills/company-investment-research/scripts/validate_research_release.py --full-report --strict` with the source index, evidence ledger, coverage matrix, acquisition-attempt log, validation log and release review. When a permitted benchmark is selected, pass it to the validator and record the structural diagnostics and any section-by-section depth-variance justification. Render or preview the Markdown and inspect for broken tables, clipped wide tables, missing headings, orphaned citations, unbalanced code fences, unescaped pipe characters and inconsistent units. Check that every source ID resolves and every cited local path exists. Record commands and results in `validation-log.md`.

After corrections, perform a clean release-review pass against the draft, source index, evidence ledger, coverage matrix and validation outputs. Record A1, A2, B1, B2, C1, C2, D1, D2, E1, E2, R1, R2 and R3 separately, challenge every `covered` and critical `unavailable` row, and set the release decision no better than the weakest mandatory sub-gate. The writer's recollection is not a substitute for this review packet.

The handoff must state the report path, source packet scope, as-of date, derived-data paths, limitations, tests run and Git status. A report may claim completion only when all mandatory gates pass. Otherwise label it `PARTIAL`, identify the failed sub-gates and exact next evidence/calculation required, and still deliver every evidence-supported element in the minimum `PARTIAL` contract in `release-gates.md`. `PARTIAL` is a completion-status qualifier, not permission to replace supported analysis with a short summary.
