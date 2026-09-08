# Semantic Layout Planning

Create an internal plan that maps every selected bundle `table_id` to a worksheet and section before authoring. The collector's `topic_hint` is advisory; inspect titles, headers, row labels, units, periods, and source context before accepting it.

Each planned section must remain a wide panel in Excel: identifying columns for metric/item names stay on the left, and reporting periods run chronologically from left to right. Stacking multiple sections on one worksheet does not change this orientation.

## Default topic routing

| Worksheet | Put here |
|---|---|
| `Financials` | Consolidated income statement, balance sheet, cash flow statement, statement-level reconciliations, and directly related per-share/share-count panels |
| `Segments` | Reportable-segment revenue, profit/loss, assets, capex, eliminations, and segment KPIs tied to the same segment definition |
| `Products & Geography` | Revenue or volume by product/service, geography/region/country, customer type, channel, or end market |
| `Operating KPIs` | Orders, backlog, bookings, units, volume, pricing, users, subscribers, utilization, capacity, stores, employees, and other non-statement operating series |
| `Capital & Returns` | Capex, working capital, dividends, repurchases, share counts, capital allocation, and return-related actuals |
| `Debt & Liquidity` | Debt instruments, maturities, facilities, interest rates, covenant/liquidity tables, cash and investments, and lease liabilities when material |
| `Assets & Intangibles` | PP&E, inventory, goodwill, intangible assets, impairment, acquisitions, and rollforwards |
| `Tax & Shares` | Tax components/rate reconciliation, stock compensation, options/RSUs, equity rollforwards, and EPS detail |
| `Other Notes` | Material note panels that do not fit a clearer economic schedule |

These are routing options, not mandatory tabs. For example, three small debt, lease, and share tables can live as sections under `Capital & Returns`; a dense debt maturity schedule merits `Debt & Liquidity`.

## Consolidation rules

- Prefer a maintained normalized/curated panel over duplicate tables extracted from individual filings. Export both only when the user requests source-native tables or the second table preserves a different basis that matters.
- Several annual and quarterly extracts for the same statement should become one section only when the cleaned data already establish compatible labels, units, periods, and restatement precedence. Otherwise preserve separate sections and label the comparability break.
- Keep consolidated, segment, parent-only, discontinued-operations, pro-forma, and issuer-adjusted panels distinct. Similar row labels do not make them comparable.
- Put a note table beside its economic owner: debt detail with liquidity, goodwill by segment with assets/intangibles, deferred revenue with products/revenue, stock compensation with shares. Do not put every note in one undifferentiated sheet.
- Preserve source row order within each panel. Reorder complete panels on a worksheet to follow economic logic: headline statement first, then disaggregation, then rollforward/reconciliation, then supporting KPI.
- Stack sections vertically with two blank rows. Use side-by-side placement only for two small complementary tables with the same periods and no risk of reading rows across the wrong table.

## Density decisions

- Up to about 60 populated rows: combine closely related sections freely.
- About 60-140 rows: combine only when sections share the same reader and period structure; add internal section links if useful.
- Above about 140 rows, more than 20 period columns, or materially different column structures: split into a dedicated worksheet.
- A single large statement or note schedule may own a worksheet. This is a readability decision, not a mechanical one-table rule.

## Plan shape

Keep the plan as a temporary JSON object or in-memory structure:

```json
{
  "sheets": [
    {
      "name": "Segments",
      "sections": [
        {"title": "Segment revenue and profit", "table_ids": ["T004", "T007"]},
        {"title": "Segment operating KPIs", "table_ids": ["T009"]}
      ]
    }
  ]
}
```

Validate that the union of all `table_ids` equals the selected bundle IDs exactly once. The plan does not authorize merging or calculating new source values.
