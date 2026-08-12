# Financial and Valuation Reference

## Contents

1. Statement extraction
2. Derived metrics
3. Business-model-specific treatment
4. Earnings and cash quality
5. Valuation method selection and SOTP
6. Scenario returns and IRR
7. Valuation quality gates

## 1. Statement extraction

Display audited consolidated statements in reported row order before interpretation. Preserve signs, units, periods, parent/NCI scope, restated comparatives and printed-page locators. Build a mapping ledger before calculating.

Preferred reproducible calculation path when the Workspace calculator is available:

```bash
.venv/bin/python .github/skills/financial-statement-analysis/scripts/calculate_metrics.py \
  data/curated/companies/<market>/<ticker>-<slug>/<input>.json \
  --format markdown --strict --output /tmp/<slug>-metrics.md
```

Compare the output with the tracked metrics file and record any intentional change. If the calculator is unavailable, use another transparent reproducible method and record formulas, inputs and checks. Never turn blank/not disclosed into zero.

## 2. Derived metrics

Present separate tables, each with period, formula and applicability note.

### Profitability and returns

```text
revenue growth = current revenue / prior revenue - 1
gross margin = gross profit / revenue, only if cost of revenue is consistent
operating margin = operating profit / revenue
calculated EBITDA margin = (operating profit + D&A) / revenue
parent net margin = parent net income / revenue
consolidated net margin = consolidated net income / revenue
effective tax rate = income tax expense / profit before tax, only if meaningful
parent ROE = parent net income / average parent equity
consolidated ROE = consolidated net income / average total equity
ROA = consolidated net income / average total assets
asset turnover = revenue / average total assets
```

### Liquidity and leverage

```text
current ratio = current assets / current liabilities
cash-only ratio = cash and equivalents / current liabilities
equity ratio = total equity / total assets
debt/equity = gross interest-bearing debt / total equity
net debt ex leases = debt ex leases - cash - eligible liquid investments
net debt / pre-lease EBITDA = net debt ex leases / calculated EBITDA
EBIT interest coverage = operating profit / recurring net interest expense
CFO interest coverage = CFO / cash interest paid
```

Use eligible liquid investments only when liquidity, encumbrance, tax and strategic status are clear. Do not use a negative or near-zero EBITDA denominator as a meaningful leverage multiple.

### Cash conversion and capital intensity

```text
CFO margin = CFO / revenue
CFO / EBITDA = CFO / calculated EBITDA
CFO / net income = CFO / consolidated or parent net income with matching scope
cash flow after capex = CFO - reported PPE/intangible capex
capex intensity = capex / revenue
CFO / capex = CFO / capex
D&A / capex = D&A / capex
accrual ratio = (consolidated net income - CFO) / average total assets
shareholder cash coverage = (CFO - capex) / (dividends + buybacks)
```

### Working capital

Only calculate DSO/DIO/DPO/CCC when balances are economically clean and opening stocks are available:

```text
DSO = average trade receivables / revenue * 365
DIO = average inventory / cost of revenue * 365
DPO = average trade payables / cost of revenue * 365
CCC = DSO + DIO - DPO
```

For lenders, loan receivables are not ordinary trade receivables; for insurers, reserves and insurance contract balances need sector treatment. If mixed balances prevent a defensible ratio, show an unavailable-metrics row and explain why.

## 3. Business-model-specific treatment

Select only the overrides that match `business-model-routing.md`. Generic ratios are a cross-check, not a universal dashboard.

### Lenders / consumer finance

Prioritize loan growth, net interest margin, fee income, cost-to-income, NPL/30-90 day delinquency, stage migration, provisions, coverage, write-offs, recoveries, average earning assets, regulatory capital, liquidity and ROE/ROA. Do not use generic EBITDA, CFO margin or net debt/EBITDA as the primary valuation logic.

### Insurers

Separate agency income from underwriting. Prioritize insurance revenue/service result, combined ratio, loss ratio, renewal, claims, contractual service margin, acquisition cash-flow assets, solvency, investment yield, duration and asset-liability matching. Do not equate premiums with profit.

### Utility / infrastructure / contracted operations

Separate pass-through revenue, contracted/recurring revenue and merchant exposure. Track maintenance versus expansion capex, lease cash payments, contracted escalation, churn, renewal, receivables and debt matching. EBITDA without cash rent or capex is not FCF.

### Investment holding / conglomerate

Separate operating profit, financial income, equity-method income, fair value, dividend cash, disposal gains and OCI. Build an asset bridge by cash, direct listed securities, bonds, equity-method holdings, loans and Level 3 assets. Apply tax, liquidity, control and cross-holding discounts. Never call management's “look-through profit” distributable cash or statutory ROIC.

### Manufacturing / hardware

Prioritize volume, price/mix, utilization, yield, unit cost, inventory turns, receivables, backlog/installed base, warranty, maintenance and growth capex, and cash conversion. Separate cyclical operating leverage from structural margin change.

### Project / engineering / real estate

Prioritize backlog quality, award/win rate, progress, change orders, project margin, contract assets/liabilities, retention cash, guarantees, occupancy, rent, development capex, LTV and refinancing. Do not treat unbilled contract assets or development gains as distributable cash without a bridge.

### Software / platform / marketplace

Prioritize ARR or usage where disclosed, bookings/backlog, gross margin, retention, take rate, CAC/payback, R&D capitalization, deferred revenue, implementation costs and cash conversion. Do not invent cohorts when only aggregate revenue is disclosed.

### Resource / commodity

Prioritize reserves/resources, grade, production, recovery, realized price, cash cost/AISC or equivalent, cost curve, sustaining versus growth capex, reclamation and commodity sensitivity. Normalize across the cycle; do not value a peak price as maintainable.

### Pharma / biotech

Prioritize pipeline stage, trial endpoints, probability of success, indication, market access, patent/lifecycle, milestone/royalty economics, R&D spend, cash runway and financing/dilution. Use rNPV or scenario analysis where appropriate; do not apply mature-company EBITDA multiples to pre-revenue assets.

### Real estate / REIT

Prioritize occupancy, rent growth, leasing spreads, tenant concentration, WALE where relevant, property NOI, cap rate, NAV, LTV, debt maturity, development/redevelopment capex and AFFO/FFO definitions. Treat property revaluation gains separately from recurring cash income.

## 4. Earnings and cash quality

For every important change use:

```text
reported fact
  -> mechanical bridge from statement rows
  -> economic driver: price / volume / mix / perimeter / FX / working capital / financing / tax / one-off
  -> persistence: recurring / cyclical / transitory / accounting-only / financing-driven / unresolved
  -> investment implication
```

For APMs:

- show the issuer's bridge exactly and label it issuer-defined;
- identify which excluded items are non-cash but recurring, recurring cash, non-recurring cash, accounting/perimeter, or financing/tax;
- never add back ordinary CAC, maintenance, rent, claims, credit loss or growth capital merely because management excludes it from an APM;
- keep growth investment versus maintenance investment unresolved when cohort or capex split is unavailable.

For a multi-segment or mixed business group, select the bridge that matches the segments. One possible bridge is:

```text
consolidated net income
  -> operating segment profit by route
  -> financing / underwriting / investment income after its own costs
  -> inventory / contract cost / loan receivable / reserves / development investment
  -> maintenance capex, interest, tax and shareholder distributions
```

## 5. Valuation method selection and SOTP

Choose the primary method before setting assumptions:

| Business model | Default primary lens | Use with caution |
|---|---|---|
| Mature cash-generative operations | DCF/FCF, EV/EBIT or EV/EBITDA | EBITDA where maintenance capex/rent is material |
| High-growth software/platform | DCF, EV/revenue or EV/FCF cross-check | Revenue multiples without retention/margin evidence |
| Lender/insurer | P/E, P/B, residual income, embedded value | Generic EBITDA/FCF |
| Asset owner/REIT/infrastructure | NAV/SOTP, DCF, FFO/AFFO, EV/EBITDAaL | EBITDA without capex/debt matching |
| Resource/commodity | NAV, cycle-normalized FCF, EV/EBITDA | Peak-price single-year earnings |
| Pharma/biotech | rNPV, milestone scenarios, SOTP | Mature-company multiples for pre-revenue assets |
| Heterogeneous group | SOTP/NAV bridge | One conglomerate multiple |

If no method is defensible, state valuation pending rather than forcing a template.

Use SOTP when segments have different risk, capital intensity, accounting and cash timing:

```text
equity value
= operating businesses
+ lender / insurer equity value
+ direct listed securities after tax/liquidity discount
+ equity-method holdings at validated market/book value after discount
+ cash and eligible liquid bonds
- interest-bearing debt, leases and supplier financing
- latent tax, NCI and holding-company costs
```

For operating businesses select a normalised after-tax operating profit or maintainable FCF and state whether CAC is maintenance or growth. For lenders use normalized net profit or risk-adjusted book equity. For insurers use underwriting and investment components separately. For investment assets use security-level market values where available, not a management aggregate alone.

## 6. Scenario returns and IRR

When a P/E-style earnings solver is economically appropriate, use the following inputs for 5-year and, when decision-relevant, differentiated 2-year low/base/high scenarios:

| Input | Rule |
|---|---|
| `base_net_income` | positive, normalized and ownership-consistent; otherwise use the selected method or mark P/E solver pending |
| horizon CAGR | derived from operating/financial drivers, not blind historical CAGR |
| `fcf_conversion` | fixed convention, e.g. cash available at terminal date / net income |
| `payout_ratio` | state dividends-only or dividends+buybacks; do not mix |
| `future_pe` | historical/peer/sector evidence or explicit analyst assumption |
| `current_market_cap` | price × diluted shares or sourced market cap with date/currency |

For horizon `H` under the P/E/FCF-conversion method:

```text
NI_t = NI_base * (1 + CAGR)^t
Terminal Value = NI_H * FCF_conversion * Future_PE
Dividend_t = NI_t * Payout
Market Cap = Terminal Value / (1+IRR)^H + sum(Dividend_t/(1+IRR)^t)
```

Guardrails:

- market cap, base earnings and future P/E must be positive;
- use the same currency and monetary unit throughout;
- distinguish 2-year catalysts (guidance, refinancing, asset sales, buybacks) from 5-year structural assumptions;
- show structured failure when a root does not exist;
- do not call an IRR a target price or recommendation;
- show sensitivity to earnings CAGR, conversion, payout, terminal multiple, leverage, capex and share count.

## 7. Valuation quality gates

- Does SOTP double count securities already embedded in equity-method income or cash?
- Are loans valued after expected credit losses and funding costs?
- Are insurance reserves and solvency capital treated as real obligations?
- Are leases and supplier financing included consistently with the earnings denominator?
- Are dividends and buybacks handled under one explicit payout convention?
- Is the market snapshot dated and independently distinguishable from fiscal accounts?
- Are assumptions labeled as facts, analyst judgments or model inferences?
- Does the report state what would cause an upgrade and a downgrade?
