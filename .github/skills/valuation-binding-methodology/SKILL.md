---
name: valuation-binding-methodology
description: Use for evidence-bound company valuation in the AI Invest Workspace, especially when converting audited financial statements, operating KPIs, analyst judgments, and scenario assumptions into formula-driven 5-year/2-year IRR outputs, valuation tables, and a traceable valuation memo. Apply for Cellnex and other infrastructure companies where recurring cash flow, leverage, leases, CapEx, and shareholder returns must be separated.
---

# Valuation Binding Methodology

## Purpose and scope

Use this skill to turn a company's evidence set into an auditable valuation. The output must show assumptions before conclusions and must distinguish reported facts, analyst adjustments, and model-generated inferences.

This skill owns:

1. selection and documentation of valuation anchors;
2. low/base/high assumptions for 5-year and differentiated 2-year horizons;
3. the formula-driven IRR calculation and solver guardrails;
4. traceability between source data, assumptions, calculations, tables, and memo prose.

It does not replace the financial-statement-analysis skill, industry research, business-model analysis, accounting judgment, or report publishing. Read the financial-statement-analysis skill first when valuation uses annual-report statements.

## Workspace adaptation

The source project version refers to formal Stage 05/06 artifacts. This Workspace has no mandatory Stage 05/06 runtime contracts. Use the following local equivalents:

| Formal concept | Workspace equivalent |
|---|---|
| adjudication evidence | report's sourced facts, explicit analyst judgments, unresolved questions, and `来源审计` sheet |
| run context | valuation date, share price/market cap, currency, consolidation perimeter, and scenario horizon recorded in the memo/workbook |
| valuation input packet | `估值输入` or `估值情景` worksheet/table with source IDs and rationale |
| parameter decision | low/base/high assumption table with adopted, adjusted, or unavailable status |
| valuation artifacts | valuation sheets in the clean workbook plus a Markdown valuation memo |

Never invent missing runtime files or pretend that a third-party source is an adjudication artifact. If a required anchor is unavailable, label it unavailable and explain the consequence.

## Required evidence and read order

Before setting assumptions, read in this order:

1. the latest audited consolidated income statement, balance sheet, and cash-flow statement;
2. the issuer's APM reconciliation and debt/lease/CapEx notes;
3. the clean workbook's `披露财务数据`, `经营KPI`, `衍生指标`, and `来源审计` sheets;
4. the research report sections on industry demand/supply, business model, management, risks, and unresolved evidence gaps;
5. current market data used for the valuation date (price, shares, market cap, net debt), with an original URL and as-of date.

For every input, record value, unit, period, source locator, evidence type, and rationale. Use repository-relative paths in tracked outputs. Do not use raw report prose as a substitute for audited statements when a statement line is required.

## Required model inputs

At minimum define or explicitly mark unavailable:

- `future_pe`
- horizon-specific net-income CAGR (`future_ni_cagr_5y`; use a separate 2-year CAGR field)
- `fcf_conversion`
- `payout_ratio` and the buyback inclusion policy
- `base_net_income`
- `current_market_cap`

For infrastructure companies also disclose, even when not direct solver parameters:

- recurring levered FCF / EBITDAaL and FCF definitions;
- net debt including/excluding leases and the matching denominator;
- maintenance, expansion, BTS, and remedy CapEx;
- shares outstanding and any planned buyback/dividend policy;
- perimeter, restatement, FX, and discontinued-operation treatment.

Do not use negative statutory net income as the base for this positive-NI P/E solver. If normalized earnings are needed, build them explicitly from reported lines and disclose every adjustment; otherwise mark the P/E/IRR model pending and use a separate cash-flow valuation only if requested.

## Baseline and scenario discipline

For estimated parameters:

1. start from numeric historical anchors in the audited statements, APMs, KPI sheet, or clearly dated market data;
2. decompose the anchor into operating drivers (organic revenue, tenancy/PoP, ARPT, escalators, margin, CapEx, interest, tax, and share count where relevant);
3. map evidence-backed judgments to directional adjustments;
4. apply explicit penalties or wider ranges for downgraded judgments, rejected claims, concentration, leverage, refinancing, churn, or disclosure gaps;
5. enforce low/base/high monotonicity and state when a scenario intentionally violates a normal policy band.

Recommended anchors:

- `future_pe`: historical company PE distribution only when positive, comparable earnings exist; otherwise use peer/sector evidence and label the substitution;
- net-income CAGR: historical normalized earnings decomposition, never a blind CAGR from a loss year;
- `fcf_conversion`: interval anchor such as FCF / normalized earnings or RLFCF / EBITDAaL, with the exact convention fixed across scenarios;
- `payout_ratio`: interval payout anchor, explicitly stating whether dividends, buybacks, or both are included;
- `base_net_income`: latest normalized positive earnings or a clearly defined cash-flow proxy; keep currency and unit identical to market cap;
- `current_market_cap`: price × diluted shares at a stated date, or a sourced market-cap figure.

For Cellnex, do not call `RLFCF / assets`, `EBITDAaL / assets`, or similar ratios ROIC. A true ROIC requires tax-normalized operating profit and invested capital. Prefer an explicit FCF/EV or FCF-yield framework when statutory net income remains negative, and show the P/E model as unavailable rather than forcing it.

## Scenario structure

Produce:

1. primary 5-year low/base/high scenarios;
2. companion 2-year low/base/high scenarios differentiated by near-term catalysts, refinancing, CapEx commitments, asset disposals, and capital-allocation constraints.

Each horizon should expose the same five solver parameters: `base_ni`, `cagr`, `fcf_conv`, `payout`, and `future_pe`; `current_market_cap` is a boundary input shared by scenarios. Do not mechanically copy 5-year assumptions into 2-year assumptions.

## IRR formula contract

For horizon `H`:

\[
NI_t = NI_{base}(1+CAGR)^t, \quad t=1,\ldots,H
\]

\[
Terminal\ Value = NI_H \times FCF_{conversion} \times PE_{future}
\]

\[
Dividend_t = NI_t \times Payout
\]

\[
MKT = \frac{Terminal\ Value}{(1+IRR)^H} + \sum_{t=1}^{H}\frac{Dividend_t}{(1+IRR)^t}
\]

Map equation variables consistently:

| Equation | Input field |
|---|---|
| `PE_future` | `future_pe` |
| `Cagr_future` | horizon-specific CAGR |
| `FCF_conversion` | `fcf_conversion` |
| `Payout` | `payout_ratio` |
| `NI_base` | `base_net_income` |
| `MKT` | `current_market_cap` |

## Solver guardrails

Before solving:

- `current_market_cap > 0`;
- `base_net_income > 0` for the P/E solver;
- `future_pe > 0`;
- all monetary inputs use the same currency and unit;
- decimals are stored as decimals, not percent strings;
- default root interval is `[-0.99, 5.0]`.

If no root exists, emit a structured scenario failure and explain the conflicting assumptions. Never fabricate an IRR. If market cap or normalized positive earnings are unavailable, mark the relevant result pending.

## Output requirements

At minimum create or update:

1. `估值输入` / `估值情景` table or worksheet;
2. `IRR_5Y` and `IRR_2Y` tables with low/base/high results or structured failures;
3. `估值备忘录.md` (or an equivalent report section).

Every output must include:

- all five parameters by scenario and the market-cap boundary input;
- 5-year versus 2-year IRR comparison;
- equation and unit context;
- top sensitivity drivers;
- source IDs/paths and evidence type for each assumption;
- explicit treatment of buybacks and dividends;
- uncertainty, unavailable data, policy-band exceptions, and unresolved questions.

For spreadsheet outputs, use the spreadsheet skill: formulas must remain auditable, inputs and derived metrics must be separated, source URLs/paths must be visible, and render all modified sheets before finalizing. Do not overwrite raw source workbooks; create a clean valuation version or add clearly named valuation sheets.

## Hard rules

1. Do not treat rejected or unresolved judgments as positive valuation drivers.
2. Do not mix statutory figures and issuer APMs without labeling the bridge.
3. Do not mix payout conventions across scenarios.
4. Do not report naked IRR numbers; always show assumptions and the equation context.
5. Do not use a single-year spike, loss-year CAGR, or unverified denominator as a normal growth anchor.
6. Do not present a P/E-derived value when normalized positive earnings are unavailable.
7. Do not silently change perimeter, restatement status, currency, or lease treatment.
8. Keep source facts, analyst judgments, and model inferences visibly separate.
9. Report sensitivity to the parameters that actually drive value: earnings/CAGR, conversion, payout, terminal multiple, leverage, CapEx, and share count.
10. Preserve a human-auditable trail from each output cell or paragraph back to the source locator and assumption rationale.
