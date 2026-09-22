---
name: derived-financial-analysis
description: Compute and append company-specific derived financial-analysis tables (asset structure, net cash, working capital, cash-flow attribution, yearly/interval/growth factor tables, and charts) into an already-built company workbook, using agent judgment per company rather than a shared calculator script — account structures vary too much across companies for one rigid schema to hold up. Does not replace company-research-to-excel (build the base IS/BS/CF workbook there first) or financial-statement-analysis (use that calculator instead when the user needs a fully audited, reconciliation-checked ratio set).
---

# Derived Financial Analysis

Take a company whose income statement, balance sheet, and cash-flow statement are
already assembled — in a workbook, in JSON, or simply gathered earlier in the
conversation — and produce the second layer of analysis: multi-year structural and
attribution tables that no single generic formula covers well across companies,
because their account structures diverge too much. Compute every number by direct
reasoning against that company's actual reported line items. Do not build or invoke
a shared calculation script — the judgment of what maps to what, and how to handle
what's missing, is the point of this skill.

## When to use this

Use after a company's three statements are already available, when the ask is to
produce: asset-structure composition, a multi-year net-cash position, working
capital and its trend, a cash-flow attribution bridge, or CAGR/interval growth
tables — the kind of output pack an equity analyst builds before writing narrative
conclusions.

Do not use this to build the base workbook. Run `company-research-to-excel` first if
the company has no assembled IS/BS/CF workbook yet.

Do not use this in place of `financial-statement-analysis` when the user wants a
fully audited ratio set with a reconciliation trail (mapping ledger, evidence
objects, `--strict` validation). That skill's calculator is more rigorous for
standard profitability/liquidity/leverage/returns ratios — reuse its
[metric-catalog.md](../financial-statement-analysis/references/metric-catalog.md)
definitions where they overlap (margins, ROIC, DSO/DIO/DPO) rather than
redefining them here. This skill's job is the tables that calculator does not
produce: asset structure, net cash, cash-flow attribution, and interval/growth
factor sets.

## Ground rules carried over from statement-mapping discipline

Even without a calculator enforcing them, keep these rules from
[statement-mapping.md](../financial-statement-analysis/references/statement-mapping.md):

- Never convert a missing or not-disclosed value to zero. Mark it `n/d` and exclude
  it from sums that would otherwise be silently wrong; footnote what's excluded.
- Enter magnitudes as positive (assets, debt, revenue, capex, dividends) and flows as
  signed (profits, cash-flow subtotals) — stay consistent with the source statement's
  own sign, not a mechanical convention.
- When a filing restates a prior year, use the restated comparative for trend tables
  and keep the originally reported value in a footnote, not silently overwritten.
- Do not blend an issuer-defined APM (adjusted EBITDA, company-defined FCF, adjusted
  net debt) into a statutory-basis table without labeling it as issuer-defined.
- If a mapping is genuinely ambiguous for this company, say so in the table's notes
  column rather than guessing silently.

## Core formula set

Compute using the company's own consolidated, as-reported figures. Substitute
sector-appropriate variants (e.g., a bank's earning assets instead of PP&E, a REIT's
NOI instead of operating profit) by judgment; do not force an industrial template
onto a financial or asset-light business.

### Growth and CAGR

```
YoY growth        = current / prior - 1
CAGR(n years)     = (ending / beginning)^(1/n) - 1
```

Compute CAGR only over positive, comparable endpoints. If a series crosses zero or
restates its basis mid-window, break it into sub-windows rather than reporting one
misleading multi-year rate. Standard growth-factor set: revenue, cost of
goods/services, operating profit, net income (consolidated and parent, if they
diverge materially), normalized EBIT, cash earnings.

### Profitability building blocks

```
EBIT               = operating profit (as reported), adjusted only for a disclosed,
                     bridgeable one-off (impairment, disposal gain/loss) — footnote
                     every adjustment
EBITDA             = EBIT + depreciation & amortization
Normalized tax rate = a multi-year average cash or effective tax rate, not one
                     outlier year
NOPAT              = EBIT x (1 - normalized tax rate)
Cash earnings       = net income + D&A + other material non-cash items (impairment,
                     stock comp, deferred tax) - footnote each add-back
```

### Capex, OCF, FCF, and conversion

```
Capex (total)       = capex_ppe + capex_intangibles when both are disclosed
                     separately; otherwise use the reported total and note that the
                     split is unavailable
FCF                = CFO - total capex
OCF conversion      = CFO / net income  (or CFO / EBITDA when net income is
                     unhelpful, e.g., near zero or loss-making)
FCF conversion      = FCF / net income
Interval conversion = sum(CFO or FCF over N years) / sum(net income over same N
                     years) — use for a trailing window (e.g. 3 or 5 years) or the
                     full available window, chosen by what the data supports; state
                     the window explicitly in the table
```

### Net cash, invested capital, and returns

```
Net cash            = cash & equivalents + short-term investments considered
                     readily available - total interest-bearing debt (all
                     maturities, include finance leases only if the company
                     capitalizes them as debt-like)
Invested capital     = total interest-bearing debt + lease liabilities (if leases
                     sit inside NOPAT) + total equity - excess cash and
                     non-operating investments
Operating ROIC      = NOPAT / average invested capital
Full-capital ROIC   = NOPAT / average (invested capital + excess cash) — use when
                     the user wants a return measure unadjusted for the company's
                     cash policy
```

Document which invested-capital bridge was used; it will not match every data
provider's convention and does not need to.

### Asset structure

Bucket the balance sheet's asset side into groups that reflect *this company's* own
disclosure, not a fixed 11-line template. A reasonable starting set — drop or merge
buckets that this company doesn't disclose separately, and add a bucket for anything
material that doesn't fit:

```
Cash & equivalents
Short-term investments / marketable securities
Receivables (trade + other, note if combined)
Inventory
Other current assets
Property, plant & equipment (net)
Right-of-use / lease assets
Goodwill
Other intangible assets
Equity-method / long-term investments
Other non-current assets
```

Each yearly column must reconcile to reported total assets. If it doesn't within
rounding, find the gap before publishing the table.

### Working capital

```
Operating current assets      = current assets - cash & equivalents - short-term
                               investments (exclude anything non-operating/financial)
Operating current liabilities = current liabilities - short-term debt - current
                               portion of long-term debt
Net working capital           = operating current assets - operating current
                               liabilities
```

Skip this table (or replace with a one-line note) when the business model makes NWC
not meaningful — e.g., a company with negligible inventory/receivables relative to
its balance sheet, or a financial institution where "working capital" is not an
economically meaningful concept.

### Cash-flow attribution

Build a bridge from operating cash generation to the change in cash, covering at
minimum:

```
Net income (or CFO starting point, state which)
+/- Depreciation & amortization
+/- Working capital change
+/- Other non-cash operating items
= Cash flow from operations
- Capex (PP&E + intangibles)
= Free cash flow
- Dividends paid
- Buybacks (net of issuance if the company nets them)
+/- Net debt issuance / (repayment)
+/- Acquisitions / divestitures (net cash paid or received)
+/- Other investing items
+/- Other financing items
+/- FX effect on cash
= Net change in cash
```

Adapt line items to what the company actually reports (add a "net share issuance"
line if material, drop "acquisitions" if there were none, etc.), but the bridge must
net to the company's own reported change in cash for the year — this is a hard
reconciliation check, not a rounding nicety.

## Required output pack

Produce these tables (and matching charts) for every fiscal year the base workbook
already covers. Use the workbook's existing fiscal-year labels verbatim (`FY2025`,
not `2025`, if that's the house convention already in use).

1. **Asset Structure** — yearly $ and % columns per bucket above, reconciled to
   total assets; stacked column chart of the % mix over time.
2. **Net Cash** — yearly cash-like assets, total debt, net cash/(net debt); line
   chart of the net cash trend.
3. **Working Capital** — yearly operating current assets, operating current
   liabilities, NWC, and NWC as % of revenue; line chart of the NWC trend. Omit per
   the guidance above if not meaningful for this company.
4. **Cash-Flow Attribution** — the full bridge table above for every year available;
   a stacked/waterfall chart of the latest year's composition.
5. **Yearly Factor Table** — one column per year, one row per metric: revenue,
   revenue growth, gross margin (if identifiable), operating margin, EBITDA margin,
   effective tax rate, net margin, NOPAT, invested capital, operating ROIC,
   full-capital ROIC, asset turnover, net cash/(net debt), FCF, FCF margin, OCF
   conversion, FCF conversion, dividend per share, buybacks, payout ratio
   (dividends+buybacks / net income or FCF — state which), cash earnings, cash
   earnings per share, diluted shares outstanding.
6. **Interval Factor Table** — the same conversion-style metrics summed/averaged
   over trailing windows the data actually supports (e.g. trailing 3-year and
   trailing 5-year, plus the full window) rather than single-year snapshots:
   cumulative OCF conversion, cumulative FCF conversion, cumulative payout ratio,
   cumulative dividends + buybacks vs. cumulative FCF.
7. **Growth Factor Table** — CAGR over the full available window (and one shorter
   window, e.g. trailing 5 years, if the full window is long enough that a shorter
   comparison is informative) for: revenue, cost of goods/services, operating
   profit, net income, normalized EBIT, cash earnings.

If a table cannot be built defensibly (a required input is genuinely not
disclosed), include it with an explicit "not disclosed" note rather than omitting it
silently — matching `financial-statement-analysis`'s own quality gate.

## Writing into the workbook

There is no existing tool anywhere in this Workspace for opening an already-built
`.xlsx` and appending sheets to it — `company-research-to-excel`'s
`build_workbook.py` always rebuilds a fresh workbook from `model.json`. This skill
does not add that as a generalized library; instead, write a short one-off Python
snippet per run:

```python
import openpyxl
wb = openpyxl.load_workbook(SOURCE_XLSX)   # the already-built workbook
# create_sheet for each table above; do not touch existing sheets
wb.save(OUTPUT_XLSX)                        # a new filename — never overwrite SOURCE_XLSX
```

Always save to a new filename (e.g. `<original-name>_derived.xlsx`, or a versioned
copy) so the source workbook produced by `company-research-to-excel` is never at
risk of corruption or accidental data loss. If the base workbook is later
regenerated (e.g., a data correction), these appended sheets must be reproduced
against the new copy — this is a known limitation, not a blocker.

Match `company-research-to-excel`'s house style from
[workbook-contract.md](../company-research-to-excel/references/workbook-contract.md):
Arial font, 14pt sheet titles, thin structural borders around headers/totals,
accounting number format with parenthesized negatives, 1-decimal percentages,
2-decimal per-share figures, blue font for hardcoded reported numbers and black for
labels/formulas, frozen panes on the header area, and a Sources note for anything
pulled from outside the base workbook. Use `openpyxl.chart` (already a Workspace
dependency via `build_workbook.py`) for the required charts.

Give this skill's sheets their own tab color, `BF8F00` (gold), to visually separate
them from `company-research-to-excel`'s IS/BS/CF (navy), Operating
Metrics/Segments/Geography (green), and Derived Metrics (purple) sheets — these are
an independently-appended layer, not part of that skill's own model.

## Quality gates before delivery

- Every asset-structure column reconciles to reported total assets.
- Every cash-flow attribution column nets to the company's own reported change in
  cash for that year.
- No table silently converted a missing input to zero — use an explicit `n/d`.
- Every table states its fiscal years, currency, and unit scale.
- Every CAGR and interval figure states its window explicitly.
- Any issuer-defined APM used anywhere is labeled as such, separate from
  analyst-calculated figures.
- Tables are delivered before narrative interpretation, and any conclusion in prose
  explicitly points back to a cell/row in one of these tables.
