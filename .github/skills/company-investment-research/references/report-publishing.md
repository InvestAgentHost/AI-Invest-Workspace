# Report Publishing and Quality Standard

Use this reference after analysis and before handoff. It defines the minimum standard for a report intended for a professional investor who knows investing but not the issuer's industry. It is adaptive: use the universal spine plus only the business-model modules selected during routing.

## 1. Required architecture

Use `report-outline.md` as an adaptive spine, not a mandatory 23-chapter template. The first chapter is a short orientation: identity, history, legal/reporting boundary, segment map and the required one-sentence company summary. Put industry context before detailed operating conclusions when it clarifies the company; reorder around the production, asset, credit, pipeline or portfolio cycle when that is the company's economic object. Do not put a conclusion-first executive summary ahead of this orientation unless the user explicitly requests one.

## 2. Coverage standard

Before finalizing a full report, make a coverage matrix, table, or equivalent working check for every material segment, legal entity, product/contract type, statement exposure, capital-allocation action, strategic claim, material risk and valuation component. Each item must point to evidence, an analysis section, and a status of `covered`, `unavailable`, or `unresolved`. An unavailable item must explain why the missing disclosure matters. For a narrower user request, scale the check to the requested scope.

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

Do not accept generic labels such as “large market”, “strong moat”, “high quality”, “recurring revenue” or “good management” without identifying the scarce input, contract term, unit economics, capital requirement, quantified anchor or falsification condition. Distinguish company claims from independently verified facts. Where the company does not disclose a needed cohort, margin, churn, credit, claims, capex or cash metric, show an explicit unavailable row and explain the consequence.

## 4. Layout and citation standard

- Use one H1 title, stable H2 chapter headings and H3 subsections; do not use heading levels only for visual size.
- Open each chapter with a short scope sentence. Use prose for causal explanation and tables for comparisons, reconciliations, scenarios and evidence status.
- Put assumptions before valuation outputs and reported tables before derived-metric commentary.
- Keep tables narrow enough to render in Markdown; split large tables by period or theme. Include units, period, scope, formula/definition and source ID in or immediately below every table.
- Cite material claims inline using `[Sxx]` IDs that resolve to the source index. For calculations use `[calc:...]` and list the input IDs and formula. For company claims use language such as “公司披露/管理层称”；for analyst judgments use “本报告判断”。
- Mark illustrative examples as illustrative. Never make an illustrative number look like company data.
- Use blockquotes for report scope, limitations or key definitions sparingly. Avoid marketing copy, unexplained acronyms, excessive bolding, decorative separators and dense unbroken paragraphs.
- Keep a balanced final synthesis: established facts, attractive economics, fragile assumptions, upgrade/downgrade evidence and unmodeled items. Do not repeat the full conclusion in every chapter.

## 5. Final rendering and automated checks

Run, as available, Markdown link checks, YAML/CSV/JSON parsers, PDF/page visual checks, the financial calculator in strict mode and `git diff --check`. Render or preview the Markdown and inspect for broken tables, clipped wide tables, missing headings, orphaned citations, unbalanced code fences, unescaped pipe characters and inconsistent units. Check that every source ID resolves and every cited local path exists. Record commands and results in `validation-log.md`.

The handoff must state the report path, source packet scope, as-of date, derived-data paths, limitations, tests run and Git status. A report may claim completion only when all mandatory gates pass; otherwise label it `PARTIAL` and list the exact next evidence required.
