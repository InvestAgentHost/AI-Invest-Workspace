# FocusAlpha → 批量引擎输入

用于 `references/batch-screen.md` 的 Step 1—2b。这是来源适配约定，不改变 v4.11.4 的评分公式。先保存完整响应，SEC schema 优先使用包内原生转换器，再核对实际字段、原始文档与单位；不假定不同市场的返回结构一致。Fiscal.ai 停用；旧 Fiscal.ai 拉数脚本已退出活动技能，原件保存在上版备份。

批量运行另须读 [valuation-reliability.md](valuation-reliability.md)，执行逐字段覆盖、来源尝试、原生估值重建和交付检查。`main`金额仍为百万；规范化估值事件为完整币种金额，两者不要共用缩放。年度`dil`不能用于日市值。原始iXBRL的股类维度/IFRS扩展标签不能因companyfacts缺项而跳过。

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

原始响应的 null 保持原样。规范化年度 main 中保留未拆分字段的 null，让原生引擎按 v4.11.4 明列规则处理：收购无形资产摊销、商誉及无形资产减值、利息收入未拆出时按 0；持续经营 CFO 未单列时用总 CFO；和解负债缺流动部分时只计非流动部分并警示。只在这些分项使用默认值，并在来源台账和最终中文说明中列明。其他缺口继续补查并解释，不任意填零，也不再用旧 checked_build 或自建 bounds 修改评分。

facts 中修补值必须为可核实数字；未找到的年度直接省略，不写 null/unresolved/区间。收入、营业利润、资本等基础数据不可凭空补造。无法取得源数据时如实列示引擎的未评分原因及可用固定修补，不编辑引擎或输出评分。营业利润口径不符时采用 fact_brief_template.md §6 的 operating_profit_bridge：税前利润 + 净利息费用 − 面表单列非经营损益，金额为百万；收购摊销只按引擎加回一次。

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

从 FocusAlpha 数据计算日频历史时优先使用原生转换器与 rebuild_multiples.py；P/E 理论口径 = 当日同基础价格 ÷ 当时已披露最近四季稀释 GAAP EPS；EV/EBIT、EV/EBITDA 的分母也是当时可知的滚动利润。每个交易日只能使用此前已公开的数据，不能按报告期末直接生效。没有可核实的发布日期、历史股数、净债务或汇率时，不生成精确历史序列。

`close` 会追溯调整拆股和分拆，`close_as_traded` 是当日实际交易基础，`adj_close` 还含股息；估值要选与 EPS、股数一致的价格基础。ADR 比例、股类、拆股、分拆和币种均须逐项核对，不把总回报价拿来除 GAAP EPS。历史 EV 不能全程套用今天的净债务或股数。可用数据不足则保留 N/A 和历史长度，规则内的 stale-series / pe_now_override 修补须保留公式与原因。

## 同行及来源台账

同行使用相同 main 形状写入 `$U/raw/peers.json`。已有 `raw_extra/am_focusalpha.json` 只填尚未计入的摊销；和解债务写 `raw_extra/debt_like.json`，保持流动/非流动两部分及缺失原因，先检查是否已含在 debt。包内历史覆盖池和债务文件带原始来源，但不能据此推断已有最新数据。

`source_ledger.json` 每条至少记录：公司/稳定 key、字段或序列、期间、报价/披露时点、工具名及参数、获取时间、状态、缺口/回退原因、实际最终来源、原文 URL、本地原始响应、币种/单位、规范化与计算公式。Gangtise 观点另标 `source_type`（研报/纪要/生成摘要）及是否经原文核验。数字来源写进事实 evidence、各公司 measure_notes 和 page_text.sources；不把混合来源笼统称为 FocusAlpha。

归档保留台账和原始响应；HTML 交付时附可访问的台账路径/链接及实际数据源说明。脚本中的“normalized source data”只是中性占位，不能代替真实的逐项来源记录。

## 季度数据（v4.8—v4.11.4）

`raw/quarters.json`：稳定 key → `{kind:"quarterly",cur,src,impSrc,cols,rows}`；cols 为 `["fy","q","end","earn","rev","gp","op","imp","ni"]`。fy/q 是财年及季度整数，end 是该季度期末，earn 是真实公开日期，金额为百万报告币。ni 是归属于普通股股东的净利润。每行是单季数据，不能把半年或九个月累计数冒充单季；保存转换公式和源数。E1/E3 仅使用截止日已公开的季度；年度减值与季度减值的对账由原生引擎处理。每个 key 的 src 写明具体工具、原始响应和口径。

`raw/qbs.json`：稳定 key → `{kind:"quarterly balance sheet",src,cols,rows}`；cols 为 `["fy","q","end","avail","debt","cash","dil"]`。avail 是实际公开日期；debt 含租赁且不得重复添加；cash 及 dil 分别为百万报告币与百万稀释股数，保留 weighted-average 的实际含义。等价的 `--bs-quarters` CSV 列为 `avail_date,debt_m,cash_m,diluted_shares_m`。缺少季度净债务/股数时原生脚本使用年度值，必须披露近似限制。

E2 来自 facts.guidance：保留 checked 日期、每次 prior/current、日期、metric、period、kind（level/growth）及原文来源。不同计量单位与增长率指引不可合并；无资料与无调整不同。客户/产品集中及 channel 写入 facts.business，并按原生事实模板的 schema 执行。

## v4.11.4 原生转换路线（优先于上文手动 schema 示例）

年度 get_all_financials（annual，limit 至少 12）完整分页 → build_rows_focusalpha.py → raw/main_fa.json；季度利润 → build_quarters_focusalpha.py → raw/quarters.json；季度资产负债表与利润 → build_qbs_focusalpha.py → raw/qbs.json；prices/splits → build_prices_focusalpha.py → scratch/px_<T>.csv；最后 rebuild_multiples.py 生成日频倍数。全部输入保存原始完整响应、查询参数和来源台账。mcp_call.py 只在已配置连接可用时直接调用；完整 MCP 连接工具响应也可以原样落盘，禁止手工重抄。

年度 not_comparable 数据全部保留并在 basis_note 说明，不能为追求同口径而直接删去旧年。重述断点、处置和并购由原生窗口规则及事实核验处理。转换器按 source_filed_at 选择同期间更新值；历史基线重建前先按基线截止日隔离已公开响应，避免后来重述覆盖早先数据。

年度 fye 来自最新报表期末。两个季度转换器都显式传 --fye-month，尤其 build_qbs 默认 12，不自动读取年度 fye。1—5 月年结采用“期末年份减一”的引擎 FY 命名，必须与事实文件一致；52/53 周及年结变更另核对，不改脚本凑结果。

价格用 close_as_traded，按 restates_per_share=true 的后续拆股调整；不以 close 或 adj_close 替换，因为其可能含分拆/股息调整。--symbol 必填，过滤同公司不同上市地。网页补早期历史需同拆股基础、至少 20 个重叠日且中位差异不超过 1%；留存未采纳文件及拒绝原因。转换后每一天的价格来源写在 CSV。

原生年度 debt=total_debt（缺失时 long_term_debt_incl_current）+operating_lease_liability，am 使用现金流 amortization（全部无形资产）；必须核对租赁是否重复、短债是否遗漏、摊销是否需 acquired-only 修补，不能自动认定精确。原生季度 earn/avail 使用 source_filed_at，保留相对业绩公告的时点差。

新 config 的 data_route 明确写本地 FocusAlpha 原生路线与依据，run_meta 和 HTML 会显示它；不能沿用作者的个人审批措辞或把混合来源全部归为 FocusAlpha。跨路线对比至少核对 as_of、engine/rules、实际源、窗口与同行池；来源变更归为 data 原因，不解释成经营变化。原生记录未必单独存储 data_route，比较时同时读取两轮 config/run_meta。
