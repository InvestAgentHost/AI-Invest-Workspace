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
/ applicable diluted equity share count (with current outstanding shares separately identified)
= per-share value (only when inputs are valid)
```

Use after-tax normalized EBIT/EBITDA/FCF only when maintenance versus growth investment is understood. Keep company APMs separate from analyst calculations.

## 3. Forecasts, model and handoff

Read [valuation-binding-methodology](../../valuation-binding-methodology/SKILL.md). It owns the calculation contract and the reusable forecast/update workflow; do not maintain a second equation here.

Build remaining-quarter forecasts into a full fiscal-year base, then derive future annual profits from business drivers. Forecasts must have same-metric numeric historical anchors on their right. Begin with a defensible base case; unapproved low/high cases may remain blank. Extract CAGR after annual profit forecasts rather than forcing a target growth rate.

Under the default shareholder-return route, use direct exit PE × terminal earnings, cash dividends only, and a separately modelled net share-count path. FCF conversion is a cash-feasibility constraint, not an extra multiplier on direct PE. Distinguish current outstanding shares, period-end forecast shares and weighted diluted EPS shares. Use actual valuation/payment dates, including the residual current fiscal year.

For non-PE routes, match cash flow, discount rate, terminal assumptions and EV-to-equity bridge to the business. Do not force positive-NI valuation on losses or peak-cycle earnings.

## 4. Decision use

Show sensitivities to actual drivers and terminal valuation, with cash, debt and dilution constraints. Persist adopted assumptions, evidence, analyst decisions, forecast vintages and thesis-review triggers using the valuation skill's handoff contract. Follow Workspace report-delivery preferences; do not create extra narrative files or edit personal Word documents without authorization.
