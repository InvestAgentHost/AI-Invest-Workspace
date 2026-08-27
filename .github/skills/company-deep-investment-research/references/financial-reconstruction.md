# Financial Reconstruction and Derived Metrics

## 1. Reported statements first

Extract the latest audited consolidated balance sheet, income statement, and cash-flow statement in reported row order before interpreting them. Preserve currency, units, signs, period type, consolidated versus parent/NCI scope, continuing versus discontinued operations, and reported/restated/reclassified status.

Use a normalized JSON input compatible with the Workspace calculator. Object values should carry source metadata:

```json
{
  "period_order": ["FY2021", "FY2022"],
  "periods": {
    "FY2021": {
      "values": {
        "revenue": {"value": 100.0, "source_label": "Revenue", "statement": "income", "source": "S001", "page": "72", "status": "reported"}
      }
    }
  }
}
```

Run, when present:

```bash
.venv/bin/python .github/skills/financial-statement-analysis/scripts/calculate_metrics.py \
  data/curated/companies/<market>/<ticker>-<slug>/<input>.json \
  --format markdown --include-missing --strict \
  --output data/curated/companies/<market>/<ticker>-<slug>/metrics.md
```

The exact interpreter and path may differ on a colleague's machine; discover the repository root rather than hardcoding it.

## 2. Mapping ledger

Map each canonical field to exact source rows, transformation, economic scope, confidence, and comparability note. Use subtotal equations and footnotes, not label similarity alone. Keep issuer APMs such as adjusted EBITDA or company FCF separate from calculated EBITDA and CFO minus capex.

## 3. Required reconciliation checks

- Assets equal liabilities plus equity within disclosed rounding.
- Cash-flow subtotals bridge to change in cash, including FX and scope effects.
- Consolidated profit reconciles to parent and NCI attribution where disclosed.
- Restated comparatives take precedence in the current analytical series; original values remain documented.
- Blank, not disclosed, zero, and not applicable remain distinct.
- Debt excluding leases is matched with a pre-lease denominator; debt including leases uses a compatible after-lease denominator.
- ROE uses ownership-consistent income and equity.

## 4. Derived metrics

Present visible tables before narrative, grouped by profitability/returns, liquidity/leverage, working capital, and cash/capital intensity. Select metrics by route; do not fill a dashboard mechanically.

```text
revenue growth = current revenue / prior revenue - 1
operating margin = operating profit / revenue
calculated EBITDA = operating profit + D&A
net debt ex leases = short debt + long debt - cash - eligible liquid investments
cash after capex = CFO - PPE/intangible capex
CFO margin = CFO / revenue
CFO / net income = CFO / matching-scope net income
capex intensity = capex / revenue
DSO = average trade receivables / revenue * 365
DIO = average inventory / cost of revenue * 365
DPO = average trade payables / cost of revenue * 365
CCC = DSO + DIO - DPO
```

Only calculate DSO/DIO/DPO/CCC when balances are economically clean and opening stocks are available. Use `unavailable` or `not_meaningful` with the reason when denominators or source rows do not support a defensible metric.

## 5. Driver analysis

For every material change use:

```text
reported fact -> mechanical bridge -> price/volume/mix/perimeter/FX/
working-capital/financing/tax/one-off driver -> persistence assessment
-> investment implication -> monitoring KPI
```

Do not infer a driver from statements alone when notes, filings, or operating evidence do not support it. Label the point as a hypothesis and state what would confirm it.
