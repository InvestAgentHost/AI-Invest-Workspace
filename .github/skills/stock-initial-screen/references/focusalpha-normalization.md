# FocusAlpha → 批量引擎输入

用于 `references/batch-screen.md` 的 Step 1—2b。这是来源适配约定，不改变 v4.7.2 的评分公式。先保存完整响应，再按实际字段、原始文档及单位编写本轮可重跑的转换；不假定不同市场的返回结构一致。Fiscal.ai 停用，保留脚本只用于理解旧输入形状。

批量运行另须读 [valuation-reliability.md](valuation-reliability.md)，执行逐字段覆盖、source_attempts、可复用估值构建和交付检查。`main`金额仍为百万；规范化估值事件为完整币种金额，两者不要共用缩放。年度`dil`不能用于日市值。原始iXBRL的股类维度/IFRS扩展标签不能因companyfacts缺项而跳过。

## 查什么、从哪里查

| 需要的数据 | 优先检查的 FocusAlpha 工具 | 使用限制 |
|---|---|---|
| 公司及证券身份 | `search_companies`、`get_company` | 区分发行人、主上市地、ADR、股类和报价币种；覆盖池的历史 key 可保留 |
| SEC 公司三表 | `get_all_financials`，或 `get_income_statements`、`get_balance_sheets`、`get_cash_flow_statements` | 明确 annual / quarterly / ttm；默认少量行不能当作完整历史；金额按响应币种和单位转换 |
| 日本、韩国、台湾、大陆、香港 | 相应 `get_*_financials` 及披露工具 | 按实际工具说明确认报告口径；台湾累计数、港股半年报不能直接冒充单季数 |
| 财报原文与附注 | `get_filings`、`get_filing_items`、20-F notes、当地披露/报告分节工具 | 表格或附注缺失时再取监管、交易所、公司 IR 原文 |
| 持股、薪酬、管理层及会计事件 | `get_proxy_ownership`、`get_executive_compensation`、`get_insider_trades`、`get_8k_events` | 受益持股不等于排除期权及未归属奖励后的实持股，按脚注核对 |
| 历史价格、股本事件、市值 | `get_market_data` 的 `prices` / `splits` / `market_cap` | 按 listing、日期和价格基础过滤；逐页保留 `next_cursor`，直至耗尽 |
| 当前估值、预测 | `screen_companies` 的当前估值；`get_consensus` 的当期 estimates | 不是历史日频估值；前瞻数据与已披露事实分开 |

名称、参数及覆盖范围以本轮可见 MCP 说明为准；有疑问再查 `list_datasets` / `list_coverage` / `list_documents`。不因列出工具就扩大任务范围。

当前工具说明（2026-10-26）特别提示：`get_financial_metrics` 的八个估值字段恒为空，不用于拉历史估值；`get_market_data` 的价格历史始于 2018-09-01，市值历史始于 2025-07-14。使用时复核覆盖，不把工具的起始日当作公司上市日，不承诺十年历史一定齐全。可用历史较短时如实展示，不启用 Fiscal.ai 补齐。

## 年度财务：`raw/main*.json`

顶层为稳定 key → 公司数据，与 config 和覆盖池的 key 完全一致：

```json
{
  "NYSE_AAA": {
    "L": 2025,
    "cur": "USD",
    "cols": ["fy","rev","op","gp","am","imp","debt","eq","cash","gw","ia","cfo","capex","sbc","nicf","int","intInc","pt","tax","dil","cfoCont","cfoDisc","da"],
    "rows": [],
    "amSrc": "具体工具、原文及口径；缺失则写 none",
    "impSrc": "具体工具、原文及口径；缺失则写 none",
    "cfoSrc": "合并/持续经营范围及原文"
  }
}
```

每行按 cols 顺序排列，`fy` 为公司财年整数；其余金额和 `dil` 均为“百万”（dil 为百万股），报价和 CEO 薪酬/持股不按此缩放。按财年升序，保留计算窗口前一年的期初资产负债表及股数；`L` 是最后一个已披露完整财年。不同期间重复披露时明确采用哪个重述版本，不能按返回顺序盲目覆盖。

| 列 | 含义及注意事项 |
|---|---|
| rev / op / gp | 营业收入、营业利润、毛利，保持合并和持续经营范围可比 |
| am / imp | 收购无形资产摊销；商誉及无形资产减值。勿把合并 D&A、软件摊销、固定资产减值当成这两项 |
| debt | **包含租赁的有息债务总额**。核对原始 total debt 是否已含租赁，避免再次添加；和解负债由独立 debt_like 路径加入，勿双计 |
| eq / cash / gw / ia | 总股东权益、现金及等价物、商誉、无形资产净额；不要把含商誉的无形资产总额再加一遍 |
| cfo / capex / sbc | 经营现金流、资本支出、股份支付；capex 支出为负，sbc 成本为正；持续经营修补走 cfoCont / facts |
| nicf | 现金流表起点净利润，供同行摊销按财年匹配；不与归母/合并口径混用 |
| int / intInc / pt / tax | 毛利息支出（正）、利息收入、税前利润、所得税费用 |
| dil | 稀释加权平均股数，百万股；不是期末股数，不直接拿来重建每日市值 |
| cfoCont / cfoDisc / da | 披露的持续/终止经营现金流；折旧及摊销合计 |

未披露保留 null，0 只用于核实为零的值。引擎部分运算会把缺口按零处理，转换者须在 build 前检查重要输入：能够影响结论的缺口应先补原文；无法补齐时明确标记相关结果无法核实，不能仅凭添加 `measure_gaps` 或 `measure_notes` 就声称已阻止评分（这两个字段只解释已缺失的分数或添加文字）。不交付由缺口误算得出的确定分数和行动结论。按批量规则保留缺项造成的区间和开放信号灯。

## 日频估值：`raw/pe.json` 和 `raw/ev.json`

```json
{
  "NYSE_AAA": {
    "d": "251023,251024",
    "r": "18.1,18.3",
    "price": 100.0,
    "mcap": 1000000000.0,
    "fwd": null,
    "ttm": 18.3,
    "cur": "USD"
  }
}
```

以上是 pe.json 的形状示例，数值仅演示输入。`d` 为升序的 YYMMDD，以逗号分隔；`r` 为同长度日频 P/E，缺值留空，不补 0。`price` 为每股报价，`mcap` 为**报价币种的完整金额（不是百万）**，`fwd` 仅当前前瞻 P/E，`ttm` 为当前 GAAP TTM P/E。最新价格、市场值和 P/E 的日期、股数基础及潜在不一致写入台账；不能用不同 listing 的响应拼接。

```json
{
  "NYSE_AAA": {
    "ebit": {"d": "251023,251024", "r": "20.1,20.3"},
    "ebitda": {"d": "251023,251024", "r": "14.1,14.3"},
    "tev": {"d": "251023,251024", "r": "1200,1210"},
    "px": {"d": "251023,251024", "r": "100,101"},
    "pxCur": "USD",
    "pxListing": "NYSE_AAA"
  }
}
```

ev.json 的 `tev` 为**百万报价币种**，`px` 为每股价格；其余两项为倍数。各序列按自身日期成对排序，保留真实缺口。

如需从 FocusAlpha 数据计算日频历史：P/E = 当日同基础价格 ÷ 当时已披露最近四季稀释 GAAP EPS；EV/EBIT、EV/EBITDA 的分母也是当时可知的滚动利润。每个交易日只能使用此前已公开的数据，不能按报告期末直接生效。没有可核实的发布日期、历史股数、净债务或汇率时，不生成精确历史序列。

`close` 会追溯调整拆股和分拆，`close_as_traded` 是当日实际交易基础，`adj_close` 还含股息；估值要选与 EPS、股数一致的价格基础。ADR 比例、股类、拆股、分拆和币种均须逐项核对，不把总回报价拿来除 GAAP EPS。历史 EV 不能全程套用今天的净债务或股数。可用数据不足则保留 N/A 和历史长度，规则内的 stale-series / pe_now_override 修补须保留公式与原因。

## 同行及来源台账

同行使用相同 main 形状写入 `$U/raw/peers.json`。已有 `raw_extra/am_focusalpha.json` 只填尚未计入的摊销；和解债务写 `raw_extra/debt_like.json`，保持流动/非流动两部分及缺失原因，先检查是否已含在 debt。包内历史覆盖池和债务文件带原始来源，但不能据此推断已有最新数据。

`source_ledger.json` 每条至少记录：公司/稳定 key、字段或序列、期间、报价/披露时点、工具名及参数、获取时间、状态、缺口/回退原因、实际最终来源、原文 URL、本地原始响应、币种/单位、规范化与计算公式。Gangtise 观点另标 `source_type`（研报/纪要/生成摘要）及是否经原文核验。数字来源写进事实 evidence、各公司 measure_notes 和 page_text.sources；不把混合来源笼统称为 FocusAlpha。

归档保留台账和原始响应；HTML 交付时附可访问的台账路径/链接及实际数据源说明。脚本中的“normalized source data”只是中性占位，不能代替真实的逐项来源记录。
