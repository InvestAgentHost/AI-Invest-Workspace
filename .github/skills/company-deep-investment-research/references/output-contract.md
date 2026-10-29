# Output Contract

## 1. Required files

At minimum, a full-company package contains the following. Keep the main report at the
company directory root; the rebuildable context, ledgers, validation records,
and release-support files belong under the company-local `data/` directory,
which is ignored by Git:

```text
research/companies/<market>/<ticker>-<slug>/
  <report>.md
  data/
    research-context.md
    source-index.md
    evidence-ledger.md
    acquisition-attempt-log.md
    coverage-matrix.md
    validation-log.md
    release-review.md
```

Use `data/curated/` for small normalized inputs, mappings, metrics, and meeting-minute digests. Keep raw external material and large rebuildable artifacts under the source/data policy chosen for the workspace.

## 2. Report architecture

For a full written report, use one H1 title, stable H2 chapters, and H3 subsections. Each chapter opens with a concise conclusion that establishes its question and scope. A chat-only chapter follows the agreed report structure without generating a separate report or artifact. The default spine is:

1. Company identity and research boundary
2. Industry/economic context and competitive structure
3. Business model and operating units
4. Fundamental statements and accounting bridge
5. Derived fundamentals and balance-sheet economics
6. Capital allocation, management, and governance
7. Strategy, competition, advantages, and limits
8. Risk, stress paths, and monitoring
9. Valuation and shareholder return
10. Evidence gaps, limitations, balanced synthesis, and release status

Insert only relevant route modules. Do not add empty chapters to imitate another company.

For an existing report, keep its accepted sequence. Operating working capital,
turnover efficiency and asset structure belong with the balance-sheet discussion
when that is the agreed structure; do not repeat them in separate derived-analysis
chapters. Follow the [balance-sheet completion criteria](financial-reconstruction.md#67-交付前的完成判定)
before declaring that module complete or proposing the next one.

A cash-flow chapter also follows the [cash-flow completion method](financial-reconstruction.md#7-现金流章节累计流向与股东现金回报). Include the agreed history's cumulative cash sources/uses, dividends, repurchase spending, actual net share shrink and cash coverage before declaring it complete; later capital-allocation or valuation chapters do not replace these historical checks.

When the report includes a company-history chapter, write it as a dated narrative per [company-history-chapter.md](company-history-chapter.md): no tables, from founding to the present, external research required for early history.

## 3. Writing and tables

- Distinguish reported facts, analyst calculations, and judgments; support judgments with source facts and traceable calculations, and label assumptions/unresolved items visibly.
- Apply the [logic-led research-writing requirements](../../../../docs/research-interaction-protocol.md#研究写作以逻辑为主线), including chat-only chapter drafts. Organize prose around material economic drivers and causal relationships; use data as evidence, scale detail to its importance, and preserve necessary counterevidence and comparability notes. Complete historical tables do not require year-by-year commentary.
- For a balance-sheet chapter, apply [the balance-sheet chapter method](financial-reconstruction.md#6-资产负债表章节分析与写作). Select material rows from a complete evidence base, explain the historical capital-allocation sequence, and integrate operating working capital, applicable turnover metrics and asset composition. The default asset visual is one amount-stacked chart with total assets and segment percentage annotations; do not require a second percentage chart or duplicate composition table when the first chart already serves the comparison. Keep the full grouping data auditable in the base.
- Use tables for statement rows, segment bridges, route cards, KPIs, scenarios, sensitivities, coverage, and evidence status.
- Include period, unit, scope, formula/definition, and source ID in or immediately below every table.
- In charts, retain material numerical labels through repositioning, callouts or aligned value rows rather than silently hiding them to avoid overlap. Distinguish disclosed rounded zeros from unavailable values and mark zero-height contributions when they matter. Label secondary-axis units clearly. For interval CAGRs, state the start/end periods and use the number of growth intervals, not the number of annual observations.
- For Chinese charts, explicitly select a Simplified Chinese font and region-specific face (for example PingFang SC or Noto Sans CJK SC). A generic Unicode font, a successful font-family lookup, or a TTC collection path alone does not establish the intended Chinese glyph forms. Verify the actual font file used by all visible text, check glyph coverage, and visually inspect saved titles, labels and footnotes at readable size. Embed fonts or convert SVG text to outlines so the delivered result preserves the verified glyphs; text-bounds checks alone do not constitute font review.
- For executive incentives, first map each plan's recipient, grant cohort, performance period, payment period, metrics and payout denominator (cash amount, share count or award value). Present annual bonuses, completed multi-year awards, new grant designs and metric-definition bridges separately, or in explicitly bounded panels that cannot imply a shared formula. A company financial-target summary is not automatically the CEO's full scorecard. Distinguish zero growth from zero incentive score; disclose missing weights, payout curves and board adjustments rather than reverse-engineering an unexplained award. Do not transplant other executives' formulas to the CEO or infer exact scores from rounded published results.
- For an incentive-design comparison, explain the instruments and vesting conditions in plain language and identify the grant-value denominator. A hypothetical allocation of each USD100 can make a plan's composition clear. Keep grant mix, disclosed compensation amounts and governance indicators in separate figures; define SEC CAP as a valuation-based measure rather than cash received. Prefer fewer, larger labels over a compressed dashboard when the reader cannot interpret the original chart.
- When evaluating an incentive redesign, distinguish stock-price exposure from performance-based vesting. Compare total target grant cost and the value of each component, show a clearly labeled weak-performance scenario when useful, and check retirement/termination exceptions before treating service vesting as a firm retention period. Assess performance modifiers on the component to which they apply; do not equate paying entirely in stock with having all awards subject to performance thresholds or with eliminating shareholder cost.
- For a business-segment operating chapter, lead the main reading sequence with revenue and operating-profit amounts, their own growth rates, interval CAGRs, and profit margins over the comparable history and latest actual period. Volume, growth-attribution and capital-spending charts supplement this financial view; they do not replace it. Each figure must identify its metric, unit, time scope, series and color meanings without relying on surrounding prose. If colors encode growth versus decline of the same metric, say so in the legend. Review the saved figure for labels hidden by other annotations as well as labels clipped at its edges.
- For financial and operating time-series tables, including chat-only drafts, apply the [table requirements in the interaction protocol](../../../../docs/research-interaction-protocol.md#收入与利润表格的默认展示要求): default to fiscal years or quarters as chronological columns and metrics or businesses as row labels. Adapt orientation and grouping to improve clarity, visual balance and comparison; a single-period segment comparison may place businesses in rows and KPIs in columns rather than becoming a long single-column table. Clearly distinguish annual, discrete-quarter and year-to-date periods. For revenue and profit, default to one cell containing `amount (YoY)`, with metric labels such as `Revenue (YoY)` or `Operating profit (YoY)`; keep shares, margins and growth contributions as distinct metrics in rows or columns as the layout warrants. Show each listed item's own YoY, including every geography, segment, business category, and cross-classification rather than only the consolidated total. Preserve numeric cells and formulas in the underlying Excel data; combine them only in the presentation layer. Conceptual comparison tables may follow their subject rather than a time axis.
- In Chinese narrative, follow the [amount-unit convention](../../../../docs/research-interaction-protocol.md#正文金额采用中文习惯单位): express monetary amounts naturally in 万 or 亿 where appropriate, preserving currency and meaningful precision (e.g., USD 761 million → 7.61亿美元; USD 60 million → 6000万美元 or 0.6亿美元). Keep tables in their original source or workbook units and numeric scale.
- Cite material claims inline with `[Sxxx]`, `[T####]`, or `[calc:...]`.
- Use plain declarative language. Avoid promotional labels without a mechanism and falsification condition.
- Preserve contradictions, unavailable metrics, accounting nuance, and negative evidence.

## 4. Handoff checklist

Before declaring release, list source scope, dates, assumptions, unresolved questions, derived-data paths, tests, validator output, Git status, and final `PASS`/`PARTIAL`/`BLOCKED` decision. State explicitly whether the report is suitable for investment use or only for further research.
