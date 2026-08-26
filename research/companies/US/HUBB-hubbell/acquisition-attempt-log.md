# Hubbell 采集尝试记录（阶段 0）

| ID | 日期 | 研究问题 | 来源类别/路由 | 结果 | 选定来源 | 失败/限制与下一步 |
|---|---|---|---|---|---|---|
| A01 | 2026-08-26 | 发行人身份、CIK、申报历史、最新 10-Q | SEC submissions API | completed；HTTP 200，确认 CIK 0000048898、NYSE:HUBB、FY2025 10-K 和 2026-06-30 10-Q | S07 | 后续下载并保存五年 10-K、最新 10-Q 正文和附件 |
| A02 | 2026-08-26 | Hubbell IR 入口及官方材料发现 | investor.hubbell.com / Hubbell GCS-Web | completed；HTTP 200，发现 SEC filings、events/presentations、news releases、2025 annual report PDF 入口 | S08 | 后续抓取页面与 PDF，记录动态内容/重定向 |
| A03 | 2026-08-26 | 网络/下载能力 | curl（含 SEC User-Agent） | completed with escalation；沙箱内代理失败，升级联网后 SEC/IR 均 HTTP 200 | n.a. | 正式抓取继续使用合规 User-Agent、限速和 provenance；若后续阻断保留原始错误 |
| A04 | 2026-08-26 | PDF 文本/页面验证 | `pdfinfo` 可用；`pdftotext`、pdfplumber、pypdf 未发现 | partial | n.a. | 优先 SEC HTML/XBRL；PDF 用可用的替代解析/浏览器渲染，必要时标记 PDF 页码验证缺口 |
| A05 | 2026-08-26 | 结构化解析与计算 | `.venv/bin/python`、pandas、requests、BeautifulSoup 可用 | completed | n.a. | 使用标准化 CSV/JSON 和透明公式；先检查 `financial-statement-analysis` skill 是否可用 |
| A06 | 2026-08-26 | Gangtise 授权与行情/财务交叉核验 | `.github/skills/gangtise-*` 与 `tools/gangtise/run.py` | pending | n.a. | 检查环境变量/授权后再调用；缺授权则记录不可用，不影响 SEC 主表 |
| A07 | 2026-08-26 | FY2021-FY2025 audited statements and notes | SEC 10-K HTML/XBRL | completed；5 份 HTML HTTP 200，已保存 index.json、原文哈希并生成 BeautifulSoup 文本抽取 | S01-S05 | 需继续提取三表、分部附注和逐项页码/表格定位；PDF 视觉验证工具受限 |
| A08 | 2026-08-26 | 最新中期财务、分部、债务、风险 | 2026 Q2 10-Q + 8-K | completed；10-Q HTML HTTP 200，已保存原文哈希并生成文本抽取 | S06 | 需与 FY2025 口径对照，标注季节性、重分类及后续 8-K |
| A08b | 2026-08-26 | Q2 2026 业绩、指引和 non-GAAP 定义 | SEC 8-K Exhibit 99.1 | completed；HTTP 200，已保存 exhibit 与文本抽取 | S20 | 指引为前瞻性公司主张；需区分 GAAP/调整后指标并与 10-Q 核对 |
| A08c | 2026-08-26 | 2025 年报官网版 PDF | IR annual report PDF | completed；HTTP 200，186 页，`pdfinfo`/`pdftotext -layout` 可用 | S12 | 页面视觉渲染可后续抽查；SEC HTML 是财务主源 |
| A09a | 2026-08-26 | IR 动态归档页面 | Hubbell GCS-Web SEC filings/events/news/investor kit | partial；多次 HTTP/2、HTTP/1.1 返回空响应 | S08、S11 | 依赖 SEC 申报及 8-K 展品；保留失败，不宣称 IR archive 覆盖 |
| A09b | 2026-08-26 | 五年标准化财务输入与衍生指标 | SEC Company Facts JSON + prepared filings | completed；生成 `data/curated/.../financial_analysis/financial_timeseries.csv`（135 行）和 `financial_metrics.csv`（75 行） | S01-S07 | 仍需逐表人工抽样、分部表和现金流/终止经营口径复核；未运行 strict calculator |
| A09 | 2026-08-26 | 分部产品、客户、订单/积压、资本占用 | 10-K/10-Q segment notes + IR | completed/partial | S01、S06、S20 | 分部产品、客户类别、backlog、资产和 capex 已提取；产品线利润、利用率、渠道库存和数据中心收入未披露 |
| A10 | 2026-08-26 | 电网升级与输配电独立证据 | DOE/EIA/FERC/NERC/州监管 | completed/partial | S21-S23、S25-S26 | DOE/IEA/EIA 已选用；NERC/FERC 安全页阻断，未采用未核验数字 |
| A11 | 2026-08-26 | 数据中心负荷增长及三层受益映射 | DOE/IEA/EIA/NERC/ISO-RTO + Hubbell | completed/partial | S01、S06、S20-S23 | 三层机制已写入报告；直接收入/毛利/订单不可得，不把 TAM 资本化 |
| A12 | 2026-08-26 | 工业/商业电气与竞争结构 | Hubbell 10-K/10-Q 与可访问独立资料 | completed/partial | S01、S06、S21-S23 | 终端应用、竞争因素和需求驱动已覆盖；独立市场份额/价格数据 unavailable |
| A13 | 2026-08-26 | 市场价格、股本、分红和回购 | dated quote + 10-K/10-Q equity notes | completed/partial | S01、S06、S27 | Yahoo 价格、SEC 股本/分红/回购已入表；价格与股本非同日，稀释和第二行情源缺口保留 |
| A10a | 2026-08-26 | 数据中心负荷、firm power、区域约束 | DOE、IEA、EIA 官网 | completed；DOE/IEA/EIA HTML HTTP 200，已保存原文及文本抽取 | S21-S23 | 预测存在情景和时点差异；只支撑行业机制，不推导公司收入 |
| A10b | 2026-08-26 | NERC/FERC 可靠性和输电监管材料 | NERC/FERC 官网 | partial；安全页阻断 | S25-S26 | 不采用其未核验数字；后续可用 PDF/公开报告替代并记录 |
| A14 | 2026-08-26 | 五年分部收入、利润、backlog、资产和 capex | FY2025 Note 20、FY2023/22 comparatives | completed；生成 `data/curated/.../operating_timeseries.csv`（43 行） | S01-S05 | 2023 分部资产使用 FIFO-recast 管理口径，合并资产负债表保留原始/可比限制 |
| A13a | 2026-08-26 | 日期化市场价格和估值边界 | Yahoo Finance chart API + SEC S06 cover/S01 balance sheet | completed；2026-08-25 NYSE close $464.19；52.832571m shares at 2026-07-23；生成 `market_snapshot.csv` | S27、S01、S06 | Yahoo 与 SEC 股本日期不同；估值用价格日 + 最近股本并明确稀释/回购敏感性 |
| A13b | 2026-08-26 | 独立第二行情源交叉核验 | Stooq daily CSV endpoint | failed/blocked；返回 JavaScript verification page（HTTP 200，无行情数据） | n.a. | 响应保存为 `sources/companies/US/HUBB-hubbell/market/stooq-hubb-2026-08-25.html`；不作为价格证据，Yahoo 保持唯一可用行情源 |
| A15 | 2026-08-26 | 用户上传会议纪要清洗、引用化和发布 | ResearchFoundry transcripts（user_upload） | completed；3 次 run 均通过 plan/run/prepare/publish/inspect，生成 44/62/41 个 T 标记 | S29-S31 | 原始文件保持不变；coverage partial，双语文本和 ASR/翻译不确定内容保留；管理层主张与 SEC 数据分层使用 |
