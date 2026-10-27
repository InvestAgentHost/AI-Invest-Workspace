# Semantic Layout Planning

Plan economic ownership before exporting. topic_hint is advisory; read original
headings, row labels, units, scope, period grain and definition changes.

## Routing

| Owner | Content |
|---|---|
| IS | Consolidated reported income, share/EPS detail and formula bridges |
| BS | Consolidated reported balances and directly linked composition checks |
| CF | Reported cash flows, cash reconciliation; YTD/discrete kept distinct |
| SEG | Reportable-segment revenue/profit/assets/capex with eliminations/Corporate |
| GEO | Products/services/countries/regions, with each reporting axis separate |
| OP | Official volumes, pricing, utilization, units, customers and other KPIs |
| DM | Formula-linked profitability, cash conversion, liquidity, NWC and returns |
| Note schedules | Material debt/investments/intangibles/acquisitions/tax/SBC details |

These are choices, not a required sheet inventory beyond the requested statements.
Combine short related notes; split long or incompatible schedules. More tabs and
more ratios do not mean a more complete workbook. Preserve source-native order
within statements and use economically sensible order for supporting sections.

## From source axes to visible groups

Choose the reader's grouping before mapping display rows. Store region/account
identity and scope in the model keys; put the chosen group in a block title or
visible subheading and the remaining account/region in the short row label.
Keep the scope identity when shortening labels. A flattened extraction key is
not a worksheet design.

The bundled builder does not infer hierarchy from concatenated labels. Supply
properly grouped blocks, or use an equivalent authoring route when an additional
subheading level is needed. Repeated source tables should feed comparable
period panels; a native non-period axis still needs a designed header hierarchy.
The [workbook contract](workbook-contract.md#reading-hierarchy) owns the approved
regional/account patterns and their visual acceptance criteria. Do not require
another planning file solely to express them.

## Comparability and deduplication

- Choose original/recast precedence based on filed versions and document it.
  A curated panel may organize data but does not outrank original filings.
- Same text label does not prove the same measure. Scope, unit, currency, GAAP/
  non-GAAP, continuing/discontinued perimeter and definition must match.
- Treat business-line, geography and reportable-segment views as separate axes.
  Do not sum crossing views or interpret their unmatched difference as a new
  business without an official cross-classification.
- Distinguish official growth attribution from an analyst calculation. Keep
  official organic growth separate from volume/price arithmetic.
- Give each economically comparable fact one calculation owner and link repeated
  presentations. Retain independently reported totals/components for source-based
  reconciliation; matching numbers do not justify merging different scopes,
  intervals or cash definitions.
- A complete face statement uses all in-scope lines; economically immaterial
  detail may be a collapsed block rather than omitted without a disposition.

## Layout-plan contract

Select financial source views rather than requiring a disposition for every
collected HTML layout/header table. Source metadata and the workbook model
already describe placement; a separate layout JSON is optional. If used, place
each SELECTED view once. Financial exclusions/version replacements need reasons.

~~~json
{
  "sheets": [{
    "name": "Income Statement",
    "sections": [{
      "title": "Consolidated income",
      "table_ids": ["IS_2024", "IS_2025_RECAST"],
      "note": "Units/scope/periods are inherited from shared source views"
    }]
  }],
  "excluded_tables": [{"table_id": "IS_2025_ORIGINAL", "reason": "Superseded by selected recast view IS_2025_RECAST"}]
}
~~~

validate_layout.py checks optional selected-view placement only, never data
correctness. Keep economic metadata in shared source mappings rather than repeat
it in each layout section. Explain source tables not represented by periods
(e.g. maturity schedules) in native non-period table sections; those numeric
tables still require source evidence and verification before release.
