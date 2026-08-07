# Calculator Input Schema

## Minimal structure

```json
{
  "entity": "Example Company plc",
  "currency": "EUR",
  "scale": "million",
  "period_order": ["2023", "2024", "2025"],
  "periods": {
    "2023": {
      "period_length_months": 12,
      "values": {
        "revenue": 1000.0,
        "operating_profit": 120.0,
        "net_income_consolidated": 70.0,
        "net_income_parent": 65.0,
        "total_assets": 2500.0,
        "parent_equity": 900.0,
        "total_equity": 980.0,
        "current_assets": 500.0,
        "current_liabilities": 400.0,
        "cash_and_equivalents": 150.0,
        "short_term_debt": 100.0,
        "long_term_debt": 700.0,
        "cfo": 180.0,
        "capex_total": 110.0
      }
    }
  }
}
```

Bare numbers are accepted for scratch calculations. Research-grade inputs should use evidence objects.

## Evidence object

```json
{
  "value": 4418.346,
  "source_label": "Operating income",
  "statement": "income_statement",
  "source": "research/companies/ES/CLNX-cellnex/CLNX2025.pdf",
  "page": "printed p.5",
  "status": "reported",
  "mapping": "Services + other operating income",
  "confidence": "high"
}
```

Required for `--strict`:

- `value`
- `source_label`
- `statement`
- `source`
- `page`
- `status`

Recommended:

- `mapping`
- `confidence`
- `note`

Allowed `status` examples: `reported`, `restated`, `reclassified`, `calculated`, `issuer_apm`, and `pro_forma`. Keep originally reported and restated values as separate evidence records outside the calculator input when both matter; feed the selected comparable value to the calculator.

## Canonical keys

### Income statement and APMs

```text
revenue
revenue_ex_pass_through
cost_of_revenue
gross_profit
operating_profit
depreciation_amortization
ebitda_reported
adjusted_ebitda_reported
ebitdaal_reported
net_interest_expense
income_before_tax
income_tax_expense
net_income_consolidated
net_income_parent
net_income_nci
```

### Balance sheet

```text
cash_and_equivalents
liquid_investments
trade_receivables
inventory
quick_assets
current_assets
ppe
right_of_use_assets
goodwill
intangible_assets
total_assets
short_term_debt
long_term_debt
current_lease_liabilities
noncurrent_lease_liabilities
trade_payables
current_liabilities
total_liabilities
parent_equity
nci
total_equity
gross_financial_debt_company_reported
net_financial_debt_company_reported
```

The last two fields are issuer-defined debt APMs. Preserve the issuer reconciliation and do not substitute them for debt assembled from the statutory balance sheet.

### Cash flow and issuer cash APMs

```text
cfo
cfi
cff
capex_ppe
capex_intangibles
capex_total
interest_paid
lease_payments
acquisitions_paid
asset_disposal_proceeds
dividends_paid
buybacks
cash_begin
cash_end
net_change_cash
fx_cash_effect
other_cash_effect
rlfcf_company_reported
fcf_company_reported
```

If `capex_total` is absent, the calculator may add `capex_ppe` and `capex_intangibles` only when both are provided. If one component is missing, it does not assume zero.

## Sign conventions

- Enter revenue, assets, debt, leases, equity, receivables, inventory, payables, D&A, capex, interest paid, dividends, and buybacks as positive magnitudes.
- Enter profits and cash-flow subtotals as signed values.
- Enter tax expense as a positive expense and tax benefit as negative.
- Enter `net_interest_expense` as positive when expense exceeds income.
- Enter `fx_cash_effect` and `other_cash_effect` with their cash-reconciliation signs.

Keep the raw statement table separately with its original signs. The normalized JSON is a formula interface, not a replacement for the source record.

## Optional metadata

At the top level:

```json
{
  "reporting_framework": "IFRS",
  "fiscal_year_end": "2025-12-31",
  "consolidation_scope": "consolidated",
  "sector": "digital infrastructure",
  "as_of_date": "2026-08-07",
  "notes": ["2024 comparative is restated in the 2025 filing"]
}
```

At the period level:

```json
{
  "period_length_months": 12,
  "end_date": "2025-12-31",
  "comparability": "comparable",
  "notes": ["Continuing operations only"]
}
```

The calculator warns when adjacent periods have different lengths. Do not annualize interim values without an explicit, economically defensible method.

## Statement reconciliation keys

Provide these keys to activate deterministic checks:

- `total_assets`, `total_liabilities`, `total_equity`
- `net_income_consolidated`, `net_income_parent`, `net_income_nci`
- `cash_begin`, `cash_end`, `net_change_cash`
- `cfo`, `cfi`, `cff`, `fx_cash_effect`, `other_cash_effect`
- `cash_end`, `cash_and_equivalents`

Cash-flow ending cash can differ from balance-sheet cash because of overdrafts, held-for-sale cash, or scope classifications. When it does, keep both values and add a reconciliation note rather than forcing equality.

## Command examples

```bash
.venv/bin/python .github/skills/financial-statement-analysis/scripts/calculate_metrics.py input.json
```

```bash
.venv/bin/python .github/skills/financial-statement-analysis/scripts/calculate_metrics.py input.json --format json --include-missing --output /tmp/metrics.json
```

```bash
.venv/bin/python .github/skills/financial-statement-analysis/scripts/calculate_metrics.py input.json --strict
```
