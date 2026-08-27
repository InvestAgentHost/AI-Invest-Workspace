# Valuation and Shareholder Return

## 1. Select the method before the result

Choose the lens that matches the routed economics:

| Route | Primary lens | Caution |
|---|---|---|
| Mature cash-generative operations | DCF/FCF, EV/EBIT, EV/EBITDA | EBITDA can overstate value when maintenance capex, rent, or working capital is material. |
| Heterogeneous group | SOTP/NAV bridge | Do not use one multiple across different risk and capital profiles. |
| Lender/insurer | P/E, P/B, residual income, embedded value | Generic EBITDA/FCF is usually invalid. |
| Asset/infrastructure owner | NAV/SOTP, DCF, FFO/AFFO, EV/EBITDAaL | Match leases, debt, maintenance capex, and contracted/merchant cash. |
| Resource/commodity | NAV, cycle-normalized FCF, EV/EBITDA | Do not value peak-price earnings as maintainable. |
| Pharma/biotech | rNPV and milestone scenarios | Do not apply mature-company multiples to pre-revenue assets. |

If no method is defensible, state valuation pending rather than inventing precision.

## 2. SOTP bridge

Show components, scope, method, normalized metric, multiple or DCF assumptions, source IDs, and status:

```text
operating segment values
+ validated investment assets or excess cash
- corporate costs and holding-company leakage
- interest-bearing debt
- lease liabilities when included in the denominator boundary
- pensions, supplier financing, latent tax, NCI, and other obligations
= equity value
/ diluted shares at valuation date
= per-share value (only when inputs are valid)
```

Use after-tax normalized EBIT/EBITDA/FCF only when maintenance versus growth investment is understood. Keep company APMs separate from analyst calculations.

## 3. Scenario inputs

For 5-year and, when decision-relevant, differentiated 2-year low/base/high cases, disclose:

```text
base_net_income | horizon CAGR | FCF conversion | payout ratio |
future PE or other terminal multiple | current market cap |
net debt/lease boundary | diluted shares | valuation date/currency
```

Anchor assumptions to audited statements, operating evidence, dated market data, and explicit analyst judgment. Do not use a loss-year CAGR, one-year spike, or unverified denominator.

## 4. IRR and payout conventions

For horizon `H` under a positive-NI P/E/FCF-conversion solver:

```text
NI_t = NI_base * (1 + CAGR)^t
Terminal Value = NI_H * FCF_conversion * Future_PE
Dividend_t = NI_t * Payout
Market Cap = Terminal Value/(1+IRR)^H + sum(Dividend_t/(1+IRR)^t)
```

Choose exactly one buyback policy per output:

- **Cash-return convention:** treat dividends plus buybacks as shareholder cash; terminal share count is unchanged for the return calculation.
- **Per-share accretion convention:** reduce diluted shares for repurchases; count dividends as cash return; do not also add repurchase cash to payout.

Never combine the two. If market cap, normalized positive earnings, or future multiple is unavailable or non-positive, emit a structured pending result instead of an IRR.

## 5. Sensitivities and decision use

Show sensitivity to the actual value drivers: organic growth, price/mix, margin, FCF conversion, payout, terminal multiple, leverage, capex, pension/lease treatment, and diluted shares. State what evidence would upgrade or downgrade the valuation and which assumptions are unresolved.
