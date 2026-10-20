# Historical Derived Metrics

Read the coordinating research skill's
[financial reconstruction rules](../../company-deep-investment-research/references/financial-reconstruction.md),
especially sections 4.1 and 6.5. Those definitions own the economics; this
reference explains how to implement them in the historical workbook.

## Selection and ownership

Choose the metrics that explain the issuer, rather than a target number of
ratio rows. Link reported inputs from IS/BS/CF and relevant notes. Keep an
issuer-disclosed metric separate from an analyst-calculated counterpart even
when they have similar names. Do not import calculated Markdown values as facts.

| Family | Useful measures | Essential boundary |
|---|---|---|
| Profitability | Gross/operating/net margins, revenue/profit YoY | Same scope and period; negative comparison base is not an ordinary growth rate |
| Cash conversion | OCF/net income, OCF/revenue, capex/OCF, FCF | Same cash-flow interval; capex sign and PPE/intangible scope explicit |
| Liquidity | Cash, eligible liquid investments, interest-bearing debt, net cash | Debt and cash components mapped, restricted funds treated explicitly |
| Working capital | Operating CA/CL, NWC, NWC/revenue, turnover days | Remove financing/transaction items by economic nature; use average clean stocks |
| Returns | Operating IC, average IC, NOPAT, operating ROIC, IC turnover | Match earnings interval and capital dates; avoid nested-asset double deductions |
| Shareholder flows | Dividends, repurchases, issuance, net share change, SBC | Differentiate cash repurchases from actual net dilution/shrinkage |

Use FCF = OCF − capital expenditure when capex is recorded positive. If the raw
cash-flow capex is a negative outflow, link it to a sign-normalized positive
capex owner with its source explanation, then subtract; never subtract it twice.
Acquisitions, asset-sale proceeds and ordinary capex are separate cash uses.

## Operating IC / operating ROIC

Implement the agreed asset-side definition, with an auditable deduction mapping:

```text
Operating IC = total assets − investment assets − cash assets
Average operating IC = (opening operating IC + closing operating IC) / 2
NOPAT = operating income − actual reported income tax expense
Operating ROIC = NOPAT / average operating IC
Operating IC turnover = revenue / average operating IC
```

Classify all identifiable investment/cash assets, including relevant components
inside other assets, insurance assets, restricted cash and held-for-sale groups.
Do not assume those balances are zero when undisclosed. Securities totals may
already include cash/other investments: retain an overlap/deduplication bridge.
This is not equity + debt − cash, and does not subtract operating liabilities.
Goodwill, trademarks, PP&E, tax deposits and ROU assets are retained under the
agreed definition unless the authoritative research rules say otherwise.

NOPAT uses the actual tax expense under this reporting convention; it is not
precisely allocated operating tax. Do not add equity-method income into its
operating-income numerator. Any alternative return definition is separately
labeled, never silently substituted.

Annual average capital needs the previous fiscal year-end. Latest interim ROIC
uses TTM NOPAT with current and one-year-ago capital, not half-year earnings
divided by annual capital. Derive TTM additive flows as last FY + current YTD −
prior-year matching YTD only after verifying period and scope. Missing inputs
make the result unavailable; do not annualize by multiplying by two/four.

## Operating working capital / turnover

Operating CA excludes cash and identifiable financial/nonoperating current assets;
operating CL excludes interest-bearing current debt and identifiable
nonoperating obligations. Inspect transaction payables, contingent consideration,
held-for-sale balances, taxes and leases before classification. Keep original,
supported adjustments and adjusted values traceable; do not call the result
fully pure when relevant components are undisclosed.

```text
NWC = operating current assets − operating current liabilities
NWC / revenue = ending NWC / matching annual or TTM revenue
DSO = average trade receivables / matching revenue × covered days
DIO = average inventories / matching COGS × covered days
DPO = average trade payables / matching COGS × covered days
CCC = DSO + DIO − DPO
```

Use clean trade payables, not a broad accrued-expenses total. Explain COGS as a
purchase-cost proxy when purchases are not disclosed. Opening stock and actual
period days matter, including 52/53-week years. End-of-period NWC changes need
not equal cash-flow working-capital changes after transactions, FX and noncash
items; do not force a false reconciliation.

## Default model implementation

Use explicit cross-sheet references and row IDs for each input and deduction.
Compute TTM/period-specific results using expr_by_period or dedicated rows with
cell_meta derivation inputs/reason. Use exact period labels for capital anchors
when preceding-column semantics would be ambiguous. A formula-generated result
is calculated, even if an analyst expects it to match a management disclosure.
These fields belong to the bundled model interface. Another authoring route can
use equivalent native Excel formulas with the same definitions, dependencies,
period anchors and missing-value safeguards.

Show first-period n.a./unavailable with a reason when the opening stock is absent.
Missing source inputs cannot be replaced by zero, guessed industry ratios or an
IFERROR wrapper that masks an underlying data defect.
