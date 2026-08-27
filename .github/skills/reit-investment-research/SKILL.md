---
name: reit-investment-research
description: Build or refresh evidence-backed research on real estate investment trusts (REITs), including property portfolios, rent and lease structures, occupancy, WALE and expiry walls, NPI-to-DI-to-DPU bridges, leverage and refinancing, acquisitions/disposals/developments, NAV/cap-rate/DDM valuation, scenario analysis, and 2-3 year total returns. Use when the user asks to research, compare, value, rank, or underwrite a REIT, property trust, data-centre REIT, industrial REIT, retail REIT, office REIT, logistics REIT, or a mixed real-estate portfolio. Do not use for a simple share-price lookup, a generic company summary, or a standalone ratio without a REIT cash-flow and asset context.
---

# REIT Investment Research

## Objective

研究 REIT 时，把不动产资产、租约现金流、信托层费用、资本结构和单位持有人回报连成一条可核验的经济链：

```text
资产 / 可出租面积 / 可交付 MW
→ 出租率与租约
→ 租金、服务费和成本转嫁
→ NPI
→ 利息、管理费、税项和储备
→ distributable income（DI）
→ DPU / NAV / 总回报
```

默认面向“对该 REIT 不熟悉、但具备基本投资知识”的读者。解释概念时用白话，展示数字时优先使用表格；不得把 headline yield 当作完整投资结论。

这是一个独立 skill：可以在没有 `company-investment-research`、`financial-statement-analysis` 或估值插件时单独执行。其他技能可作为可选工具，但不得替代本 skill 的资产、租约、NPI/DI/DPU、资本结构和估值闭环。

## Non-negotiable rules

- Read repository `AGENTS.md` before writing. Preserve existing user changes and never overwrite raw sources.
- Record research as-of date, price as-of date, fiscal year-end, reporting currency, unit scale, accounting framework, consolidation scope, ownership/JV boundary and period comparability.
- Use the latest audited annual report as the anchor, then add interim results, operating updates, presentations/earnings-call materials, regulatory filings, market data and independent market sources as needed.
- Separate `资料事实`, `公司指引/管理层表述`, `分析计算`, `模型假设`, `分析判断` and `未解决问题`. Put a page/table/URL locator beside material claims.
- Never invent occupied area, MW, customer names, lease terms, reversion, tenant concentration, cap rates, NAV or market prices. Use `未披露`/`无法计算` with a reason.
- Distinguish same-store operating growth from acquisitions, disposals, development/AEI, fit-out, JV, FX, accounting reclassification and unit-count changes.
- Use weighted-average units for DPU calculations; do not substitute end-period units without explaining the difference.
- Treat REIT accounting profit, fair-value gains and disposal gains as different from recurring distributable cash.
- Use at least two valuation lenses and show assumptions before outputs. For mixed portfolios, use segment-level SOTP/NAV rather than one portfolio multiple.
- State downside conditions and monitoring KPIs. A recommendation without a falsifiable trigger is incomplete.

## Workflow

### 1. Scope and evidence inventory

Resolve issuer, ticker, exchange, legal vehicle, sponsor/manager, fiscal year, currency, unit class and valuation date. Build a source inventory with local path, original URL, document date, access date, printed/PDF page, table/note and extraction status. Keep externally acquired files under `sources/`; put rebuildable extracts under the target's `data/` and respect `.gitignore`.

Read the latest annual report before relying on a quarterly presentation. If a price or market-cap input is historical, label it as historical rather than calling it “current”.

### 2. Classify the REIT and choose the economic anchor

Classify the portfolio as data centre, industrial, logistics, retail, office, residential, healthcare, hospitality, infrastructure-like real estate or mixed. Select the anchor unit:

| 类型 | 经济锚点 |
|---|---|
| 数据中心 | 可交付/已上线 MW、机柜/容量、租户 fit-out、互联和电力 |
| 工业/物流 | NLA、租户、续租面积、租金/平方英尺、土地年限 |
| 商场 | 可出租面积、客流、销售额、租户销售生产率、租金结构 |
| 办公 | 面积、租户、楼层、租金、空置和到期墙 |
| 酒店/住宿 | 客房数、入住率、ADR、RevPAR、管理/租赁模式 |
| 混合型 | 为每个重大分部单独设锚点，再做集团桥接 |

### 3. Explain the asset and lease engine

For every material asset or segment, describe: location and supply constraint; delivery state (`shell & core`, `powered shell`, `fully-fitted`); customer shape (`colocation`, `single tenant`, `hyperscale`, multi-tenant); lease cost responsibility (`triple-net`, `double-net`, `gross`, utilities pass-through); lease term, escalation and renewal mechanics; required maintenance/growth capex; and the failure path from vacancy to DPU.

Always distinguish:

- `WALE` (weighted average remaining lease term) from payback period;
- `occupancy` from leased capacity, commissioned capacity and revenue-producing capacity;
- `reversion` on leases signed/renewed from the growth rate of the whole portfolio;
- `freehold` or long land tenure from low capital expenditure;
- `signed capacity` from in-service capacity and recognized revenue.

Read [reit-metrics-and-formulas.md](references/reit-metrics-and-formulas.md) when calculating or explaining these terms.

### 4. Reconstruct operating history and the volume-price bridge

Build a multi-period table for gross property income, property expenses, NPI, DI and DPU. Then split changes into:

```text
收入 / NPI / DI 变化
= 同店租金与升级
+ 出租率、面积或 MW 变化
+ 收购和全年化
+ 开发、AEI、fit-out 完工
- 处置、失租和空置
± JV、汇率、会计边界和单位数
```

If the issuer does not publish a like-for-like bridge, do not manufacture a precise price/volume contribution. Present what is known, mark the residual and explain which KPI would resolve it.

### 5. Trace NPI to DPU and test capital structure

Use the bridge `gross property income - property expenses = NPI`; `NPI + JV/other income - interest - manager fees - tax - reserves/adjustments = DI`; `DI ÷ weighted-average units = DPU`. Show NPI margin and DI/NPI, and separate recurring DI from disposal gains, fair-value gains and one-off adjustments.

Analyze aggregate leverage, ICR, WACD, fixed/hedged debt, debt maturity wall, debt currency, distributions hedged/natural hedge, undrawn facilities, covenant headroom, refinancing and unit issuance/buyback. Run at least one rate, occupancy and cap-rate stress case.

### 6. Analyze capital allocation and growth

Review acquisitions, disposals, developments, AEI, capex, asset recycling, JV/ROFR transactions, debt repayment, equity issuance, unit buybacks and distribution policy. For each transaction calculate, where evidence permits:

```text
每单位增厚 = 交易后 DI ÷ 交易后单位数 - 交易前 DI ÷ 交易前单位数
交易价值创造 = 稳定化 NPI - 被处置 NPI - 新增利息 - 发行稀释 - 资本开支/交易成本
```

Do not treat sponsor pipeline or ROFR as realized growth. Check external valuation, stabilised yield, lease quality, capex and pro-forma DPU.

### 7. Select valuation methods and scenarios

Use forward DPU yield for stable recurring distributions; two-stage DDM for normalized multi-year distributions; NAV/cap-rate for property values; SOTP for mixed portfolios; and EV/NPI only as a cross-check with consistent asset and debt boundaries. Read [reit-metrics-and-formulas.md](references/reit-metrics-and-formulas.md) for method limits.

Show base, downside and upside assumptions before value outputs. For a requested 2-3 year return, calculate both cash distributions and terminal price:

```text
总回报 = 期末价格 - 买入价格 + 累计现金分派
年化总回报 = ((期末价格 + 累计分派) / 买入价格)^(1/n) - 1
```

Use local currency for each security. Do not combine SGD and USD returns without an explicit FX assumption.

### 8. Assemble, review and publish

Use [reit-report-template.md](references/reit-report-template.md) as the default spine, adapting sections to the asset type. Tables come before narrative conclusions. End with ranking or recommendation only after operating, capital and valuation evidence is shown. Include an evidence boundary and unresolved questions.

Before delivery:

- run `git diff --check`;
- verify arithmetic, units, signs, periods and weighted-average units;
- verify every source ID/local path resolves;
- check that downside assumptions reduce DPU/value and upside assumptions increase them;
- check for double counting of JV, cash, debt, NCI, leases and disposal gains in NAV/SOTP;
- state whether the output is `COMPLETE` or `PARTIAL`, why, and what would change the view.

## Default output contract

Produce a Markdown report with:

1. research conclusion and risk-adjusted ranking;
2. scope, dates, currencies and evidence boundary;
3. REIT economic route explained in plain language;
4. business, geography and asset portfolio;
5. lease structure, WALE, expiry wall, occupancy and tenant quality;
6. volume-price and time-series operating analysis;
7. gross revenue → NPI → DI → DPU bridge;
8. capex, acquisitions, disposals, JV and capital allocation;
9. leverage, interest, hedging and refinancing;
10. growth forecast with explicit assumptions;
11. valuation cross-checks and scenario table;
12. 2-3 year total-return calculation when requested;
13. risks, falsification triggers and monitoring dashboard;
14. sources, methods and unresolved data gaps.

Use a table whenever three or more figures are being compared. Mark all analyst-generated figures as calculations or assumptions. Avoid repeating the same conclusion in operations, risks and final synthesis without adding new evidence.

## References

- [reit-metrics-and-formulas.md](references/reit-metrics-and-formulas.md): REIT KPI definitions, formulas, valuation methods and failure modes.
- [reit-report-template.md](references/reit-report-template.md): Markdown report outline, tables and conclusion contract.
- [reit-source-checklist.md](references/reit-source-checklist.md): source hierarchy, provenance and evidence-quality checks.
