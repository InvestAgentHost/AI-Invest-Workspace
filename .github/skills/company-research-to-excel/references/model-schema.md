# model.json Schema Reference

This document describes the complete schema for `model.json`, the intermediate
specification consumed by `build_workbook.py`.  The assembler produces a bare
draft; the agent customizes it by adding formatting, growth rows, calculations,
checks, and links before building.

## Top-level structure

```json
{
  "company": { ... },
  "periods": { ... },
  "sheets": [ ... ]
}
```

## company

Company metadata displayed on Cover and sheet headers.

| Field | Type | Example |
|---|---|---|
| `name` | string | `"Uber Technologies, Inc."` |
| `ticker` | string | `"UBER"` |
| `currency` | string | `"USD"` |
| `units` | string | `"$ in millions except per-share data"` |
| `reporting_framework` | string | `"US GAAP"` |
| `fiscal_year_end` | string | `"December 31"` |
| `consolidation_scope` | string | `""` |
| `as_of_date` | string | `"2025-12-31"` |
| `model_date` | string | `"2026-09-08"` |

## periods

Controls the column layout on every statement sheet.

```json
{
  "annual": [
    {"label": "FY2020"},
    {"label": "FY2021"},
    {"label": "FY2022"},
    {"label": "FY2023"},
    {"label": "FY2024"},
    {"label": "FY2025"}
  ],
  "scrap_cols": 5,
  "quarterly": [
    {"label": "1Q2024"},
    {"label": "2Q2024"},
    {"label": "3Q2024"},
    {"label": "4Q2024"},
    {"label": "1Q2025"},
    {"label": "2Q2025"}
  ]
}
```

- **annual**: left block of columns.  Each entry has `"label"` and optional
  `"end"` (period end date).
- **scrap_cols**: number of grey scratch columns between annual and quarterly
  blocks.  Set to 0 if no quarterly data.
- **quarterly**: right block of columns.

## sheets

Array of sheet objects.  Two kinds:

### kind: "statement"

Statement sheets use the shared period column layout and contain typed rows.

```json
{
  "name": "Income Statement",
  "short": "IS",
  "kind": "statement",
  "tab_color": "1F4E79",
  "contents": true,
  "blocks": [ ... ]
}
```

| Field | Required | Description |
|---|---|---|
| `name` | yes | Full sheet name (max 31 chars after sanitization) |
| `short` | yes | Short code used in cross-sheet references (e.g., IS, BS, CF) |
| `kind` | yes | `"statement"` |
| `tab_color` | no | Hex color for the sheet tab |
| `contents` | no | If true, adds a CONTENTS hyperlink list at the top |
| `blocks` | yes | Array of block objects |

### kind: "table"

Free-form grid sheets (Cover, Sources).  Uses `table` array instead of
`blocks`.

```json
{
  "name": "Cover",
  "kind": "table",
  "col_widths": [28, 60],
  "tab_color": "1F4E79",
  "table": [
    [{"text": "Company Name", "bold": true}],
    [],
    ["Ticker", "UBER"]
  ]
}
```

## blocks

Each block is a titled section within a statement sheet, rendered with a
dark-navy header bar.

```json
{
  "title": "INCOME STATEMENT",
  "rows": [ ... ]
}
```

The builder auto-numbers blocks as "1. INCOME STATEMENT", "2. NON-GAAP
METRICS", etc.

## Row types

### input

Hardcoded values from filings.  Rendered in blue.

```json
{
  "id": "total_revenue",
  "label": "Total Revenue",
  "type": "input",
  "values": {"FY2020": 11139, "FY2021": 17455, "FY2022": 31877},
  "bold": true
}
```

### subtotal

Sum of child rows.  Rendered in black with a top border.

```json
{
  "id": "total_opex",
  "label": "Total Operating Expenses",
  "type": "subtotal",
  "children": ["cost_of_revenue", "research_dev", "sales_marketing", "general_admin"],
  "bold": true
}
```

### calc

Arbitrary formula.  Rendered in black.

```json
{
  "id": "gross_margin",
  "label": "  Gross Margin",
  "type": "calc",
  "expr": "{gross_profit}/{total_revenue}",
  "fmt": "pct",
  "memo": true
}
```

For quarterly-specific formulas, add `"expr_q"`:

```json
{
  "id": "annualized_rev",
  "label": "Annualized Revenue",
  "type": "calc",
  "expr": "{total_revenue}",
  "expr_q": "{total_revenue}*4",
  "fmt": "num"
}
```

### growth_yoy

Year-over-year growth of another row.  Renders `=cur/prior-1`.
- Annual columns: compares to previous annual column.
- Quarterly columns: compares to same quarter prior year (4 columns back).

```json
{
  "id": "rev_yoy",
  "label": "  YoY Growth",
  "type": "growth_yoy",
  "of": "total_revenue",
  "fmt": "pct",
  "memo": true
}
```

### growth_qoq

Quarter-over-quarter growth.  Renders `=cur/prev_quarter-1`.
- Annual columns: blank (QoQ not meaningful for annual data).
- Quarterly columns: compares to previous quarter.

```json
{
  "id": "rev_qoq",
  "label": "  QoQ Growth",
  "type": "growth_qoq",
  "of": "total_revenue",
  "fmt": "pct",
  "memo": true
}
```

### link

Cross-sheet reference.  Rendered in green.

```json
{
  "id": "rev_link",
  "label": "Revenue (from IS)",
  "type": "link",
  "ref": "IS:total_revenue"
}
```

The `ref` format is `"SHORT:row_id"` where SHORT is the target sheet's
`short` code.

### check

Verification row.  Expression should evaluate to ~0.  Rendered with
conditional formatting: red bold when |value| > 0.5.

```json
{
  "id": "bs_check",
  "label": "Balance Check (should be ~0)",
  "type": "check",
  "expr": "{total_assets}-{total_liabilities}-{total_equity}",
  "fmt": "num",
  "memo": true
}
```

Set `"expect_nonzero": true` for reconciliation rows that are informational
(rendered amber, not enforced by the verifier).

### spacer

Blank row for visual separation.

```json
{"type": "spacer"}
```

## Row-level options

These optional fields can be set on any row:

| Field | Type | Effect |
|---|---|---|
| `bold` | bool | Bold label and values |
| `indent` | int | Indent level (1 = one tab, 2 = two tabs) |
| `memo` | bool | Grey italic font (for calculated annotations) |
| `fmt` | string | Number format (see below) |
| `note` | string | Text in the collapsed note/source column B |
| `group` | bool | Row is collapsible (outline level 1) |
| `border_top` | bool | Thin grey top border |
| `min_label` | string | First period where this row has data |
| `max_label` | string | Last period where this row has data |

## Number formats

| Code | Renders as | Use for |
|---|---|---|
| `num` | `1,234` / `(1,234)` / `"-"` | Most financial data (default) |
| `num1` | `1,234.0` | Single-decimal precision |
| `ps` | `1,234.00` | Per-share data |
| `pct` | `12.3%` / `(12.3%)` | Margins, growth rates, percentages |
| `x` | `12.3x` | Multiples (P/E, EV/EBITDA) |
| `txt` | raw text | Text values |

## Expression syntax

Expressions appear in `calc` and `check` rows.  They are Python-like math
strings with token references:

| Token | Meaning | Example |
|---|---|---|
| `{row_id}` | Same sheet, same column | `{total_revenue}` |
| `{SHORT:row_id}` | Cross-sheet, same column | `{IS:total_revenue}` |
| `{row_id@-n}` | Same sheet, n columns back | `{total_revenue@-1}` |

Expressions support standard Python operators: `+`, `-`, `*`, `/`, `()`.

Examples:
- Gross margin: `{gross_profit}/{total_revenue}`
- FCF: `{cfo_total}+{capex_ppe}` (when capex is negative)
- Balance check: `{total_assets}-{total_liabilities}-{total_equity}`
- Revenue growth (manual): `{total_revenue}/{total_revenue@-1}-1`

## Complete example: adding growth and margin to IS

Starting from the draft (input rows only), insert after `total_revenue`:

```json
{"id": "rev_yoy", "label": "  YoY Growth", "type": "growth_yoy",
 "of": "total_revenue", "fmt": "pct", "memo": true},
{"id": "rev_qoq", "label": "  QoQ Growth", "type": "growth_qoq",
 "of": "total_revenue", "fmt": "pct", "memo": true}
```

After `gross_profit`:

```json
{"id": "gross_margin", "label": "  Gross Margin", "type": "calc",
 "expr": "{gross_profit}/{total_revenue}", "fmt": "pct", "memo": true}
```

After `operating_income`:

```json
{"id": "op_margin", "label": "  Operating Margin", "type": "calc",
 "expr": "{operating_income}/{total_revenue}", "fmt": "pct", "memo": true},
{"id": "oi_yoy", "label": "  YoY Growth", "type": "growth_yoy",
 "of": "operating_income", "fmt": "pct", "memo": true}
```

After `net_income`:

```json
{"id": "net_margin", "label": "  Net Margin", "type": "calc",
 "expr": "{net_income}/{total_revenue}", "fmt": "pct", "memo": true},
{"id": "ni_yoy", "label": "  YoY Growth", "type": "growth_yoy",
 "of": "net_income", "fmt": "pct", "memo": true}
```

## Analytics patterns

These blocks are added by the agent during Phase 4 customization.  Each
pattern shows the rows to insert and where they go.

### EPS & Share Count (IS sheet, after net income)

```json
{"type": "spacer"},
{"id": "basic_eps", "label": "Basic EPS", "type": "input",
 "values": {"FY2024": 4.75, "FY2025": 4.97}, "fmt": "ps", "bold": true},
{"id": "diluted_eps", "label": "Diluted EPS", "type": "input",
 "values": {"FY2024": 4.56, "FY2025": 4.81}, "fmt": "ps", "bold": true},
{"id": "eps_yoy", "label": "  YoY Growth", "type": "growth_yoy",
 "of": "diluted_eps", "fmt": "pct", "memo": true},
{"id": "waso_basic", "label": "Weighted Avg Shares — Basic", "type": "input",
 "values": {"FY2024": 2074, "FY2025": 2023}, "fmt": "num"},
{"id": "waso_diluted", "label": "Weighted Avg Shares — Diluted", "type": "input",
 "values": {"FY2024": 2160, "FY2025": 2089}, "fmt": "num"}
```

### Non-GAAP bridge (IS sheet, separate block or after EPS)

The bridge reconciles GAAP net income to the company's non-GAAP metric (e.g.,
Adjusted EBITDA).  Include the company's own reconciliation items:

```json
{"title": "NON-GAAP RECONCILIATION", "rows": [
  {"id": "ni_bridge", "label": "Net income (from above)", "type": "link",
   "ref": "IS:net_income", "bold": true},
  {"id": "add_interest", "label": "Interest expense, net", "type": "input",
   "values": {...}, "indent": 1},
  {"id": "add_tax", "label": "Provision for income taxes", "type": "input",
   "values": {...}, "indent": 1},
  {"id": "add_da", "label": "Depreciation and amortization", "type": "input",
   "values": {...}, "indent": 1},
  {"id": "add_sbc", "label": "Stock-based compensation", "type": "input",
   "values": {...}, "indent": 1},
  {"id": "add_restructuring", "label": "Restructuring charges", "type": "input",
   "values": {...}, "indent": 1},
  {"id": "adj_ebitda", "label": "Adjusted EBITDA", "type": "input",
   "values": {...}, "bold": true},
  {"id": "adj_ebitda_margin", "label": "  Adjusted EBITDA Margin", "type": "calc",
   "expr": "{adj_ebitda}/{IS:total_revenue}", "fmt": "pct", "memo": true},
  {"id": "adj_ebitda_yoy", "label": "  YoY Growth", "type": "growth_yoy",
   "of": "adj_ebitda", "fmt": "pct", "memo": true},
  {"id": "nongaap_check", "label": "Bridge Check (should be ~0)", "type": "check",
   "expr": "{ni_bridge}+{add_interest}+{add_tax}+{add_da}+{add_sbc}+{add_restructuring}-{adj_ebitda}",
   "fmt": "num", "memo": true, "expect_nonzero": true}
]}
```

The check uses `"expect_nonzero": true` because the bridge often has small
rounding differences or unlisted adjustment items — amber, not red.

### Working capital analytics (BS sheet, after balance check)

Only add if the company has inventory and receivables.  Use `expr_q` for
quarterly columns where the denominator should be one quarter's revenue (≈91
days), not full-year:

```json
{"type": "spacer"},
{"id": "wc_dso", "label": "Days Sales Outstanding", "type": "calc",
 "expr": "{accounts_receivable}/{IS:total_revenue}*365",
 "expr_q": "{accounts_receivable}/{IS:total_revenue}*91",
 "fmt": "num1", "memo": true},
{"id": "wc_dio", "label": "Days Inventory Outstanding", "type": "calc",
 "expr": "{inventories}/{IS:cost_of_revenue}*365",
 "expr_q": "{inventories}/{IS:cost_of_revenue}*91",
 "fmt": "num1", "memo": true},
{"id": "wc_dpo", "label": "Days Payable Outstanding", "type": "calc",
 "expr": "{accounts_payable}/{IS:cost_of_revenue}*365",
 "expr_q": "{accounts_payable}/{IS:cost_of_revenue}*91",
 "fmt": "num1", "memo": true},
{"id": "wc_ccc", "label": "Cash Conversion Cycle", "type": "calc",
 "expr": "{wc_dso}+{wc_dio}-{wc_dpo}", "fmt": "num1", "memo": true}
```

Skip DIO/DPO for pure-software or platform companies with no inventory.

### FCF analytics (CF sheet, after section totals)

```json
{"type": "spacer"},
{"id": "fcf", "label": "Free Cash Flow", "type": "calc",
 "expr": "{cfo_total}+{capex_ppe}", "bold": true, "fmt": "num"},
{"id": "fcf_yoy", "label": "  YoY Growth", "type": "growth_yoy",
 "of": "fcf", "fmt": "pct", "memo": true},
{"id": "capex_pct", "label": "  Capex % of Revenue", "type": "calc",
 "expr": "0-{capex_ppe}/{IS:total_revenue}", "fmt": "pct", "memo": true},
{"id": "fcf_margin", "label": "  FCF Margin", "type": "calc",
 "expr": "{fcf}/{IS:total_revenue}", "fmt": "pct", "memo": true},
{"id": "fcf_conversion", "label": "  FCF Conversion", "type": "calc",
 "expr": "{fcf}/{IS:net_income}", "fmt": "pct", "memo": true},
{"id": "cf_check", "label": "Cash Walk Check (should be ~0)", "type": "check",
 "expr": "{cfo_total}+{cfi_total}+{cff_total}+{fx_effect}-{net_change_in_cash}",
 "fmt": "num", "memo": true}
```

Check capex sign convention: if capex is reported as negative (outflow), use
`+` in the FCF formula; if positive, use `-`.  The `0-{capex_ppe}` in capex %
flips the sign so the percentage reads as a positive number.

### BS Detail sheet pattern

A separate sheet (`short: "BSD"`, `"contents": true`) for disaggregated
footnote data.  One block per face line, components as grouped rows:

```json
{
  "name": "BS Detail",
  "short": "BSD",
  "kind": "statement",
  "tab_color": "1F4E79",
  "contents": true,
  "blocks": [
    {
      "title": "GOODWILL BY SEGMENT",
      "rows": [
        {"id": "gw_mobility", "label": "Mobility", "type": "input",
         "values": {...}, "indent": 1, "group": true},
        {"id": "gw_delivery", "label": "Delivery", "type": "input",
         "values": {...}, "indent": 1, "group": true},
        {"id": "gw_freight", "label": "Freight", "type": "input",
         "values": {...}, "indent": 1, "group": true},
        {"id": "gw_total", "label": "Total Goodwill", "type": "subtotal",
         "children": ["gw_mobility", "gw_delivery", "gw_freight"], "bold": true},
        {"id": "gw_check", "label": "Check vs Face (should be ~0)",
         "type": "check", "expr": "{gw_total}-{BS:goodwill}",
         "fmt": "num", "memo": true}
      ]
    }
  ]
}
```

`"group": true` makes component rows collapsible in Excel.

### Segment tie-out (Segments sheet)

Segment revenue must tie to IS total revenue:

```json
{"id": "seg_mobility_rev", "label": "Mobility Revenue", "type": "input",
 "values": {...}},
{"id": "seg_delivery_rev", "label": "Delivery Revenue", "type": "input",
 "values": {...}},
{"id": "seg_freight_rev", "label": "Freight Revenue", "type": "input",
 "values": {...}},
{"id": "seg_total_rev", "label": "Total Segment Revenue", "type": "subtotal",
 "children": ["seg_mobility_rev", "seg_delivery_rev", "seg_freight_rev"],
 "bold": true},
{"id": "seg_rev_check", "label": "vs IS Revenue (should be ~0)",
 "type": "check", "expr": "{seg_total_rev}-{IS:total_revenue}",
 "fmt": "num", "memo": true}
```

Use `min_label`/`max_label` if segment definitions changed mid-window (e.g.,
a segment was created or merged).

## Tab colors (house style)

| Sheet type | Color |
|---|---|
| Core financial statements (IS, BS, CF) | `1F4E79` (dark navy) |
| Operating / segment sheets | `548235` (forest green) |
| Derived metrics | `7030A0` (purple) |
| Cover | `1F4E79` |
