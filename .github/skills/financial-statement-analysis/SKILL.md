---
name: financial-statement-analysis
description: Extract consolidated balance sheets, income statements, and cash-flow statements from annual or interim filings; reconcile restatements and presentation changes; map reported line items to economically consistent canonical fields; calculate auditable derived financial metrics; present them in analyst-readable tables before interpretation; and explain what drives the results. Use for company fundamental research, multi-year statement analysis, accounting-quality review, liquidity/leverage/profitability/cash-conversion analysis, or any request to calculate ratios from original PDF, HTML, XBRL, Excel, or Markdown financial disclosures.
---

# Financial Statement Analysis

Build financial analysis from the issuer's reported statements upward. Preserve the source presentation, make every normalization explicit, calculate deterministically, and separate facts from interpretation. Always expose the derived metrics in tables before narrative analysis so an analyst can inspect the numbers directly.

## Load the right references

Read these files before doing the corresponding work:

- Read [references/statement-mapping.md](references/statement-mapping.md) before extracting or normalizing line items.
- Read [references/metric-catalog.md](references/metric-catalog.md) before selecting or interpreting metrics.
- Read [references/input-schema.md](references/input-schema.md) before using the calculator.
- Read [references/sector-overrides.md](references/sector-overrides.md) when the issuer is a bank, insurer, REIT, infrastructure/utility company, marketplace, SaaS company, commodity producer, or other business for which generic ratios can mislead.

## 1. Establish the evidence set

1. Resolve the legal entity, consolidation scope, fiscal year end, reporting framework, currency, unit scale, and period length.
2. Prefer audited consolidated financial statements over summaries, presentations, data portals, or third-party databases.
3. Locate the balance sheet, income statement, cash-flow statement, accounting policies, segment note, debt note, lease note, tax note, and issuer APM reconciliations.
4. Record a human-verifiable locator for every source: local Workspace-relative path or original URL, document title, reporting date, printed page, PDF page when different, note/table title, and access/as-of date when time-sensitive.
5. Use the PDF capability when the source is PDF. Inspect rendered pages when columns, signs, footnotes, continuation pages, or multi-level headers affect meaning; text extraction alone is not sufficient evidence of layout.
6. Use a structured parser for XBRL/HTML and the spreadsheet capability for Excel sources. Preserve the issuer's presentation and footnotes even when structured tags are available.

Do not treat a parent-company-only statement, preliminary results release, or investor presentation as the consolidated statutory statement unless the source explicitly says so.

## 2. Extract the three statements before calculating

Display the reported statements first, in their original row order. Preserve:

- original-language label and an optional translated label;
- reported value, parentheses/minus sign, currency, and unit;
- period type: instant, full year, half year, quarter, or year to date;
- consolidated versus parent-only scope;
- continuing versus discontinued operations;
- reported, restated, reclassified, or pro-forma status;
- source document and page locator.

Represent `0`, missing, not disclosed, and not applicable separately. Never convert a blank cell into zero.

For multi-year analysis, use the latest audited comparative presentation for each adjacent pair when a later filing restates or reclassifies the prior year. Preserve the originally reported value in a reconciliation note rather than silently overwriting it.

## 3. Build a mapping ledger

Map source rows to canonical fields only after reading the row label, statement position, note definition, and subtotal relationships. Follow [references/statement-mapping.md](references/statement-mapping.md).

For each canonical field, record:

| Field | Required content |
|---|---|
| canonical key | Calculator key or a clearly named custom key |
| source rows | Exact labels and values that compose it |
| transformation | Sum, subtraction, sign normalization, reclassification, or none |
| economic scope | What the field includes and excludes |
| confidence | High, medium, or low |
| comparability note | Restatement, policy, perimeter, FX, or classification issue |

Never use label similarity alone. `Operating income`, for example, may mean revenue for one issuer and operating profit for another. Use the subtotal equation and notes to determine its role.

Do not combine statutory figures with issuer APMs. Store `adjusted_ebitda_reported`, `ebitdaal_reported`, and `fcf_company_reported` separately from calculated EBITDA or cash flow after capex. Preserve the issuer's reconciliation and definition.

## 4. Choose economically valid metrics

Select metrics based on the business model and available evidence; do not fill a standard dashboard mechanically.

Use these matching rules:

- Match consolidated net income with average total equity; match parent-attributable net income with average parent-attributable equity.
- Match debt excluding leases with pre-lease EBITDA; match debt including leases with an after-lease denominator such as EBITDAaL when the definition is verified.
- Use average balance-sheet stocks with period income or cash flows for return and turnover ratios.
- Use revenue only when it is economically revenue. Do not substitute a bank's total operating income or an insurer's gross premiums without a sector-specific rationale.
- Treat gross margin as unavailable unless cost of revenue or gross profit is identifiable on a consistent basis.
- Treat negative or near-zero denominators as a signal that a ratio may be not meaningful, not as permission to produce an extreme multiple.
- Keep reported APM ratios separate from analyst-calculated IFRS ratios.

Read [references/metric-catalog.md](references/metric-catalog.md) for formulas, numerator/denominator logic, and failure modes. Apply [references/sector-overrides.md](references/sector-overrides.md) before calculating generic metrics for special sectors.

## 5. Calculate with an audit trail

Create a normalized JSON file following [references/input-schema.md](references/input-schema.md), then run:

```bash
.venv/bin/python .github/skills/financial-statement-analysis/scripts/calculate_metrics.py INPUT.json --format markdown
```

Use `--include-missing` when auditing coverage and `--strict` when statement reconciliations and source metadata must pass. The calculator accepts bare numbers for scratch work but object values with source metadata are required for research-grade output.

Never replace the script's formulas with mental arithmetic for final figures. If a needed metric is not implemented, calculate it transparently in a small reproducible worksheet or extend the script and test the change.

## 6. Present the derived metrics before analysis

Always include visible derived-metric tables in the research output before discussing what the metrics mean. A prose-only financial analysis is incomplete even when the calculations were performed correctly. For a full three-statement analysis, provide separate tables for profitability/returns, balance-sheet liquidity/leverage, and cash-flow/capital intensity; one mixed dashboard does not satisfy this requirement. A single table is sufficient only when the user's scope is genuinely narrow.

The table must include:

- metric name;
- every comparable period analyzed;
- unit or ratio scale;
- formula or a concise numerator/denominator definition;
- applicability or comparability note when the metric is adjusted, issuer-defined, not meaningful, or unavailable.

Group a large metric set into readable profitability, liquidity/leverage, returns/turnover, and cash-conversion tables rather than compressing everything into one oversized table. Keep issuer APMs visibly separate from analyst-calculated IFRS-derived metrics. Show `n.m.`, `not calculable`, or an equivalent explicit state with the reason; never omit a decision-useful metric silently or replace missing evidence with zero.

Use the deterministic calculator output as the source for displayed values. Narrative analysis must follow the tables and explicitly reference the relevant metrics and periods. If no requested metric can be calculated defensibly, still provide an unavailable-metrics table explaining the missing evidence.

## 7. Analyze drivers, not just direction

For every important change, move through this chain:

1. **Reported fact:** identify the statement rows and magnitude of change.
2. **Mechanical bridge:** show which rows reconcile the movement.
3. **Economic driver:** connect the movement to price, volume, mix, perimeter, FX, working capital, asset intensity, financing, tax, or one-offs.
4. **Persistence judgment:** classify the driver as recurring, cyclical, transitory, accounting-only, financing-driven, or unresolved.
5. **Investment implication:** explain what it changes about growth quality, margins, liquidity, leverage, reinvestment needs, or shareholder cash generation.

Do not infer a business cause from the statements alone when the notes or operating disclosures do not support it. Mark the point as an analyst hypothesis and state what evidence would confirm it.

## 8. Produce the research output

Use this order unless the user requests another structure:

1. Scope, accounting basis, units, periods, and comparability decisions.
2. Consolidated balance sheet in original row order.
3. Consolidated income statement in original row order.
4. Consolidated cash-flow statement in original row order.
5. Mapping/reconciliation notes and issuer APM inputs.
6. Derived metric table with formula labels.
7. Profitability and operating-leverage analysis.
8. Balance-sheet, liquidity, and leverage analysis.
9. Cash conversion, working capital, and capital-intensity analysis.
10. Three-year or multi-period conclusions, limitations, and unresolved questions.

Separate source facts, analyst calculations, and analyst judgments. Cite the source beside the relevant table or claim, not only in a bibliography.

## Quality gates

Before delivery, confirm all of the following:

- Assets reconcile to liabilities plus equity, subject only to disclosed rounding.
- Cash-flow subtotals reconcile to the change in cash, including FX and scope effects.
- Parent and NCI attribution reconcile to consolidated profit when disclosed.
- Units, signs, periods, and consolidation scope are consistent.
- Restated comparatives take precedence and original values remain documented.
- No missing value was converted to zero.
- Every ratio has a named formula, source inputs, and applicability decision.
- Lease treatment is consistent between numerator and denominator.
- ROE uses ownership-consistent income and equity.
- APMs remain labeled as issuer-defined and are not presented as IFRS.
- At least one analyst-readable derived-metric table appears before narrative analysis and includes periods, units, and formula labels.
- A full three-statement analysis contains separate balance-sheet and cash-flow metric tables rather than only one mixed ratio table.
- Narrative conclusions explicitly connect back to the displayed metrics rather than replacing the tables.
- Material movements have evidence-backed drivers or are marked unresolved.

Stop and report the limitation rather than manufacture a metric when the source does not support a defensible mapping.
