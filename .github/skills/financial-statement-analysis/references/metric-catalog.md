# Metric Catalog and Economic Logic

## Contents

1. Selection rules
2. Growth and common-size analysis
3. Profitability
4. Liquidity
5. Solvency and leverage
6. Cash conversion and capital intensity
7. Returns and turnover
8. Working capital
9. Earnings quality and APMs

## 1. Selection rules

For every metric record: formula, period, exact inputs, unit, ownership scope, lease scope, source status, and interpretation limits. Prefer a small set of decision-useful metrics over a large mechanically populated dashboard.

Use average stocks for flow/stock ratios:

```text
average balance = (opening balance + closing balance) / 2
```

If the opening balance is unavailable, do not silently use the closing balance. Either omit the metric or label it `closing-balance proxy`.

## 2. Growth and common-size analysis

| Metric | Formula | Economic question | Main caution |
|---|---|---|---|
| Revenue growth | current revenue / prior revenue - 1 | Is the economic top line expanding? | Separate organic, FX, acquisition, disposal, and accounting effects. |
| Profit growth | current profit / prior profit - 1 | Is profit scaling with revenue? | Percentage growth is not meaningful when either value crosses zero or the base is near zero. |
| CAGR | `(ending / beginning)^(1/years) - 1` | What is the smoothed multi-year growth rate? | Requires positive, comparable endpoints and correct elapsed years. |
| Common-size asset share | asset line / total assets | Where is capital invested? | Carrying values reflect accounting history, not market value. |
| Common-size cost share | cost line / revenue | Which costs absorb revenue? | Nature-of-expense and function-of-expense presentations are not directly comparable. |

When a base is negative or zero, show the absolute change and explain the sign transition rather than reporting a percentage.

## 3. Profitability

| Metric | Formula | Economic logic | Do not use when |
|---|---|---|---|
| Gross margin | gross profit / revenue | Pricing and direct delivery economics before overhead | Gross profit/cost of revenue is not consistently identifiable. |
| Operating margin | operating profit / revenue | Profit after operating costs, before financing and tax | `Operating profit` includes material non-operating items without a bridge. |
| Calculated EBITDA margin | (operating profit + D&A) / revenue | Pre-financing, pre-tax operating cash proxy before working capital and capex | D&A or operating profit scope differs; never call it adjusted EBITDA. |
| Reported adjusted EBITDA margin | adjusted EBITDA / issuer-defined denominator | Management's recurring operating performance view | Definition/reconciliation is missing or changes across years. |
| EBITDAaL margin | EBITDAaL / matching revenue | Operating performance after ordinary lease payments | Lease definition or revenue perimeter is unclear. |
| Parent net margin | parent net income / revenue | Earnings available to parent shareholders per unit of revenue | Revenue and parent income have different consolidation scope. |
| Consolidated net margin | consolidated net income / revenue | Group-wide earnings including NCI | Comparing directly with parent-only equity returns. |
| Effective tax rate | income tax expense / income before tax | Accounting tax burden | Pretax income is negative/near zero or tax contains large one-offs. |

Bridge operating margin changes through revenue, direct costs, staff, other operating expense, D&A, impairment, disposals, and perimeter effects. Bridge net margin further through interest, FX/fair value, associates, tax, discontinued operations, and NCI.

## 4. Liquidity

| Metric | Formula | Economic logic | Main caution |
|---|---|---|---|
| Current ratio | current assets / current liabilities | Balance-sheet coverage of near-term obligations | Ignores timing, committed facilities, and cash generation; inspect held-for-sale classification. |
| Quick ratio | quick assets / current liabilities | Coverage without relying on inventory/prepaids | Construct quick assets explicitly; do not assume all current financial assets are liquid. |
| Cash-only ratio | cash and equivalents / current liabilities | Immediate cash coverage | Restricted cash and overdraft presentation can distort it. |
| CFO/current liabilities | CFO / average current liabilities | Annual operating cash generation relative to short-term obligations | A flow/stock indicator, not a maturity schedule. |

Low current ratios can be normal in businesses with predictable collections, negative working capital, or committed credit. They still require debt-maturity and facility analysis.

## 5. Solvency and leverage

| Metric | Formula | Economic logic | Matching rule |
|---|---|---|---|
| Equity ratio | total equity / total assets | Accounting loss-absorption cushion | Use consolidated equity and assets. |
| Debt/equity ex leases | gross debt ex leases / total equity | Financial debt relative to book capitalization | Use parent equity instead only if debt is parent-only. |
| Gross debt/assets | gross debt / total assets | Portion of accounting asset base funded by interest-bearing obligations | State whether leases are included. |
| Net debt ex leases | debt ex leases - cash - eligible liquid investments | Debt remaining after immediately available liquidity | Do not net restricted or strategic assets. |
| Net debt incl leases | debt plus leases - cash - eligible liquid investments | Broader fixed-obligation burden | Pair with an after-lease earnings denominator. |
| Net debt/EBITDA | net debt ex leases / pre-lease EBITDA | Debt load relative to pre-lease earnings capacity | Numerator and denominator must share lease/perimeter treatment. |
| Net debt incl leases/EBITDAaL | net debt incl leases / EBITDAaL | Lease-adjusted fixed obligations relative to after-lease earnings | Use only when EBITDAaL definition is verified. |
| EBIT interest coverage | operating profit / net interest expense | Accounting operating earnings coverage of recurring interest | Strip FX, fair value, and refinancing items from interest when possible. |
| CFO interest coverage | CFO / cash interest paid | Cash coverage of interest | Check whether interest paid is already included in CFO. |

If EBITDA or EBITDAaL is negative or close to zero, do not report a leverage multiple as meaningful. Show debt and cash directly.

## 6. Cash conversion and capital intensity

| Metric | Formula | Economic logic | Main caution |
|---|---|---|---|
| CFO margin | CFO / revenue | Operating cash generated per unit of revenue | IFRS interest/tax classification and working-capital swings matter. |
| CFO/EBITDA | CFO / EBITDA | Conversion after cash interest, tax, and working capital depending on classification | Match EBITDA definition; one-year working-capital changes can dominate. |
| CFO/net income | CFO / net income | Accrual earnings conversion | Mark not meaningful when net income is non-positive or near zero. |
| Cash flow after capex | CFO - capex_total | Cash remaining after reported PPE/intangible purchases | This is not automatically the issuer's FCF and includes financing-classification effects. |
| Cash-flow-after-capex margin | cash flow after capex / revenue | Residual cash per unit of revenue | Asset sales are excluded; acquisitions are excluded unless stated. |
| Capex intensity | capex_total / revenue | Cash reinvestment burden | Distinguish maintenance, growth, customer-funded, and acquisition capex. |
| CFO/capex | CFO / capex_total | Internal funding coverage of capital purchases | A lower capex year can improve the ratio without better operations. |
| D&A/capex | D&A / capex_total | Rough comparison of accounting consumption and cash reinvestment | Asset age, purchase accounting, leases, and intangibles distort it. |

Always analyze asset-disposal proceeds separately. Disposal cash can fund deleveraging but is not recurring operating cash generation.

## 7. Returns and turnover

| Metric | Formula | Economic logic | Ownership/perimeter rule |
|---|---|---|---|
| ROA | consolidated net income / average total assets | Accounting return on the full consolidated asset base | Use consolidated income with consolidated assets. |
| Parent ROE | parent net income / average parent equity | Return attributable to parent shareholders | Do not divide by equity including NCI. |
| Consolidated ROE | consolidated net income / average total equity | Return for all equity holders | Keep separate from parent ROE. |
| Asset turnover | revenue / average total assets | Revenue generated per unit of assets | Carrying values and acquisitions affect comparability. |
| Invested-capital turnover | revenue / average invested capital | Revenue productivity of operating capital | Define invested capital consistently. |
| ROIC | normalized NOPAT / average invested capital | After-tax operating return on debt and equity capital | Requires a defensible normalized tax rate and operating/non-operating split. |

Recommended invested capital bridge:

```text
invested capital = interest-bearing debt
                 + lease liabilities if leases are in NOPAT
                 + total equity
                 - excess cash and non-operating investments
```

`NOPAT = normalized operating profit * (1 - normalized cash tax rate)`. Do not use a negative or one-off effective tax rate mechanically. Document all normalization.

Negative ROA/ROE is economically interpretable, but percentage changes in a negative return usually are not.

## 8. Working capital

Use averages and a consistent day count, normally 365 for annual periods:

```text
DSO = average trade receivables / revenue * days
DIO = average inventory / cost of revenue * days
DPO = average trade payables / cost of revenue * days
cash conversion cycle = DSO + DIO - DPO
```

Use credit sales rather than total revenue when disclosed. Use purchases rather than cost of revenue for DPO when available. State that DPO based on cost of revenue is an approximation. Do not calculate these metrics when receivables/payables include large non-operating balances or cost of revenue is unavailable.

Reconcile CFO working-capital changes with balance-sheet movements. Differences can arise from acquisitions, disposals, FX, non-cash changes, taxes, capex payables, and held-for-sale reclassification.

## 9. Earnings quality and APMs

| Metric/bridge | Formula | Interpretation |
|---|---|---|
| Accrual ratio | (consolidated net income - CFO) / average total assets | More positive accruals can indicate weaker cash backing, but classification and growth investment matter. |
| CFO versus net income bridge | net income + non-cash items + working capital + cash classification differences | Explains why cash and accounting profit diverge. |
| Reported APM bridge | IFRS starting point + issuer adjustments | Shows management's definition and recurring/non-recurring judgments. |
| Shareholder cash coverage | cash flow after capex / (dividends + buybacks) | Tests whether distributions are internally funded before acquisitions/debt changes. |

Classify adjustments rather than accepting them automatically:

- non-cash but recurring: share compensation, recurring D&A;
- non-recurring but cash: restructuring, litigation, transaction fees;
- recurring and cash: maintenance, ordinary leases, routine customer acquisition;
- accounting/perimeter: impairment, disposal gains, loss of control, discontinued operations;
- financing/tax: refinancing fees, FX, deferred tax, tax settlements.

An adjustment can improve comparability without disappearing economically. Explain both the accounting exclusion and the cash or capital consequence.
