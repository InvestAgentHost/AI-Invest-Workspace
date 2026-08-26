# Hubbell 来源索引（阶段 0 计划及初始 intake）

研究截止日：2026-08-26。原始外部材料放在 `sources/companies/US/HUBB-hubbell/`（该目录不纳入 Git）。除特别说明外，报告引用使用 `[Sxx]`。

| ID | 来源类别/目标 | 日期或访问日 | 原始 URL/入口 | 计划本地路径 | 阶段 0 状态/用途 |
|---|---|---|---|---|---|
| S01 | FY2025 Form 10-K | 2026-02-12 | https://www.sec.gov/Archives/edgar/data/48898/000162828026007500/hubb-20251231.htm | `sources/companies/US/HUBB-hubbell/sec/10-k-2025/hubb-20251231.htm`; prepared `document.txt` | captured；SHA-256 `85e73cc028ddc76978ccc7ee6ba6711fa1984f4a4851a31e23fdab5497385d2a`; 主审计来源，pp.1-32,49-54,88-109 |
| S02 | FY2024 Form 10-K | 2025-02-13 | https://www.sec.gov/Archives/edgar/data/48898/000162828025005311/hubb-20241231.htm | `sources/companies/US/HUBB-hubbell/sec/10-k-2024/hubb-20241231.htm`; prepared `document.txt` | captured；SHA-256 `922209d5ed2d273b8940457417db04790c0b0bcc27869e148478f43527637f49`; 比较期/口径 |
| S03 | FY2023 Form 10-K | 2024-02-08 | https://www.sec.gov/Archives/edgar/data/48898/000162828024003792/hubb-20231231.htm | `sources/companies/US/HUBB-hubbell/sec/10-k-2023/hubb-20231231.htm`; prepared `document.txt` | captured；SHA-256 `8c656425a90fd07e311f6c51409afc935b69e78f17fcd0f1243473decb5cdc31`; |
| S04 | FY2022 Form 10-K | 2023-02-09 | https://www.sec.gov/Archives/edgar/data/48898/000162828023002875/hubb-20221231.htm | `sources/companies/US/HUBB-hubbell/sec/10-k-2022/hubb-20221231.htm`; prepared `document.txt` | captured；SHA-256 `642f4fb894717be3843bfb31b6a7841f2b86e8989da443cf981843787656b0fb`; |
| S05 | FY2021 Form 10-K | 2022-02-11 | https://www.sec.gov/Archives/edgar/data/48898/000162828022002255/hubb-20211231.htm | `sources/companies/US/HUBB-hubbell/sec/10-k-2021/hubb-20211231.htm`; prepared `document.txt` | captured；SHA-256 `355f8ca49b635ebb6e22a04cc3a0a45c8149eb65fcc72e037777b7e395d18f7e`; |
| S06 | Latest Form 10-Q (quarter ended 2026-06-30) | 2026-07-29 | https://www.sec.gov/Archives/edgar/data/48898/000162828026050405/hubb-20260630.htm | `sources/companies/US/HUBB-hubbell/sec/10-q-2026q2/hubb-20260630.htm`; prepared `document.txt` | captured；SHA-256 `ac7ee1a9d58a93cc5700df132064d23db4f9b674b25aee540e8a86b25fc381e7`; 最新中期财务、分部、并购和风险 |
| S07 | SEC company submissions metadata | accessed 2026-08-26 | https://data.sec.gov/submissions/CIK0000048898.json | `sources/companies/US/HUBB-hubbell/metadata/sec-submissions-2026-08-26.json` | captured；身份/申报目录，非财务替代来源 |
| S08 | Hubbell Investor Relations home | accessed 2026-08-26 | https://investor.hubbell.com/ (redirects to Hubbell IR) | `sources/companies/US/HUBB-hubbell/metadata/ir-home-2026-08-26.html` | captured；入口发现，待抓取 IR 页面 |
| S09 | IR SEC filings archive | 2026-08-26 | https://hubbell.gcs-web.com/financial-information/sec-filings | `sources/.../ir/sec-filings/` | partial；动态归档返回空响应，SEC 申报作为替代 |
| S10 | IR events/presentations and earnings releases | 2026-08-26 | https://hubbell.gcs-web.com/events-and-presentations/upcoming-events | `sources/.../ir/events/` | partial；动态归档返回空响应；会议纪要由用户上传并以 S29-S31 补充 |
| S11 | IR press releases | 2026-08-26 | https://hubbell.gcs-web.com/news-releases | `sources/companies/US/HUBB-hubbell/ir/ir-news.html` | partial；动态页面空响应，优先使用 SEC 8-K exhibits |
| S12 | Hubbell 2025 annual report/proxy PDF | 2026 | https://investor.hubbell.com/ar2025/docs/HUBB031_COMBO_2026_Full_Combo_Bookmarked.pdf | `sources/companies/US/HUBB-hubbell/official/annual-report-2025.pdf`; prepared `annual-report-2025.txt` | captured；PDF 186 页，pdftotext layout 提取；官网版治理/产品叙述，财务主源仍为 SEC |
| S13 | Hubbell business/product pages | accessed 2026-08-26 | https://www.hubbell.com/ | `sources/.../official/pages/` | partial；官方应用和产品主张已由年报/10-Q覆盖，动态产品页面不完整 |
| S14 | Utility/grid independent context | accessed 2026-08-26 | DOE/EIA/FERC/NERC、州公用事业委员会等 | `sources/.../independent/` | partial；DOE/EIA 可用，NERC/FERC 入口阻断 |
| S15 | Data-center electricity independent context | accessed 2026-08-26 | IEA/EIA/DOE/NERC/ISO-RTO/监管资料 | `sources/.../independent/` | partial；DOE/IEA/EIA 可用，监管资料缺口保留 |
| S16 | Electrical/industrial construction independent context | accessed 2026-08-26 | Census/ISM/industry bodies/competitor filings | `sources/.../independent/` | partial；公司和宏观需求资料可用，独立份额/价格 unavailable |
| S17 | Dated market boundary | 2026-08-26 | NYSE/SEC/IR or independent quote source | `sources/.../market/` | partial；Yahoo 价格和 SEC 股本可用，第二行情源受阻 |
| S18 | Gangtise security/quote/financial (if authorized) | 2026-08-26 | https://open-platform.gangtise.com/ | `sources/.../market/gangtise/` | unavailable；未验证授权，未调用；不影响 SEC 主表 |
| S19 | Earnings call/transcript (official or licensed) | 2026-08-26 | IR event archive / transcript source | `sources/companies/US/HUBB-hubbell/ir/transcripts/` | partial/unavailable；官方/授权全文仍未取得；用户上传会议纪要已另列 S29-S31 |
| S20 | Q2 2026 earnings release (8-K Exhibit 99.1) | 2026-07-28 | https://www.sec.gov/Archives/edgar/data/48898/000162828026049934/exhibit991_07282026.htm | `sources/companies/US/HUBB-hubbell/sec/8-k-2026q2/exhibit991_07282026.htm`; prepared `exhibit991.txt` | captured；官方业绩/指引与 non-GAAP 定义，管理层主张需与 10-Q 勾稽 |
| S21 | U.S. DOE: Clean Energy Resources to Meet Data Center Electricity Demand | accessed 2026-08-26 | https://www.energy.gov/oe/clean-energy-resources-meet-data-center-electricity-demand | `sources/companies/US/HUBB-hubbell/independent/doe-data-center-demand.html`; prepared text | captured；独立机制证据：数据中心负荷、区域集中、firm power、并网/电网扩建 |
| S22 | IEA Energy and AI: Energy demand from AI | accessed 2026-08-26 | https://www.iea.org/reports/energy-and-ai/energy-demand-from-ai | `sources/companies/US/HUBB-hubbell/independent/iea-energy-and-ai.html`; prepared text | captured；独立情景：2024-2030 数据中心用电约 15% CAGR、美国增量约 240 TWh；情景而非 Hubbell 收入 |
| S23 | EIA Short-Term Energy Outlook (electricity/data-center discussion) | accessed 2026-08-26 | https://www.eia.gov/outlooks/steo/ | `sources/companies/US/HUBB-hubbell/independent/eia-electricity-2025.html`; prepared text | captured；独立电力需求/天然气和区域预测；需注明预测时点 |
| S24 | EIA Electricity in the United States explainer | accessed 2026-08-26 | https://www.eia.gov/energyexplained/electricity/electricity-in-the-us.php | `sources/companies/US/HUBB-hubbell/independent/eia-electricity-transmission.html`; prepared text | captured；电力系统/输配电背景，网页存在动态导航噪声 |
| S25 | NERC reliability assessment landing page | accessed 2026-08-26 | https://www.nerc.com/pa/RAPA/ra/Pages/default.aspx | `sources/companies/US/HUBB-hubbell/independent/nerc-ltra-2025.html` | partial；Cloudflare/安全页阻断，未采用具体数字 |
| S26 | FERC electric transmission landing page | accessed 2026-08-26 | https://www.ferc.gov/electric-transmission | `sources/companies/US/HUBB-hubbell/independent/ferc-transmission.html` | partial；Cloudflare/安全页阻断，未采用具体数字 |
| S27 | HUBB dated quote snapshot | 2026-08-25 close; retrieved 2026-08-26 | https://query1.finance.yahoo.com/v8/finance/chart/HUBB?range=5d&interval=1d | `sources/companies/US/HUBB-hubbell/market/yahoo-hubb-2026-08-26.json`; curated `market_snapshot.csv` | captured；独立行情源，$464.19 close；需与 SEC 股本、稀释和股息口径匹配 |
| S28 | HUBB second quote attempt (Stooq) | 2026-08-26 | https://stooq.com/q/d/l/?s=hubb.us&i=d&d1=20260825&d2=20260825 | `sources/companies/US/HUBB-hubbell/market/stooq-hubb-2026-08-25.html` | failed/blocked；返回 JavaScript verification page，无行情数据，不用于估值 |
| S29 | User-uploaded 2026Q1 earnings call minutes | 2026-04-30 | User-provided local file | `research/companies/US/HUBB-hubbell/data/artifacts/transcripts/Hubbell_Incorporated/2026-04-30_earnings_call_trn_db054571312ff8ef/`；raw SHA-256 `737a4a0c6231ff619d44c166a1a6067b71a99e46f6ea0c98854894d007bf5b99` | published；raw transcript，44 markers，partial；逐轮 speaker labels and bilingual text preserved |
| S30 | User-uploaded 2026Q2 earnings call minutes | 2026-07-14 | User-provided local file | `research/companies/US/HUBB-hubbell/data/artifacts/transcripts/Hubbell_Incorporated/2026-07-14_earnings_call_trn_92340a915dfb6d99/`；raw SHA-256 `a4ba66bbf0380fa22002226b32b165aee053cbdc5debef0a4a01ba6c2da2e215` | published；raw transcript，62 markers，partial；逐轮 speaker labels and bilingual text preserved |
| S31 | User-uploaded Wells Fargo conference minutes | 2026-06-09 | User-provided local file | `research/companies/US/HUBB-hubbell/data/artifacts/transcripts/Hubbell_Incorporated/2026-06-09_conference_trn_fa815dc6b9f96d36/`；raw SHA-256 `a4c0698da32c8d4d191f87bbb129fbc251136052195f98a5bada49e52d0fc198` | published；raw transcript，41 markers，partial；conference metadata and Q&A preserved |

## 证据使用规则

- S01-S06 优先用于法律边界、三表、分部、会计、债务/租赁、风险和股本；若比较列发生重分类，保留原始列并记录采用规则。
- S08-S13 是公司主张或官方再发布材料，不替代审计数据；官网主张尽量用 S14-S16 或客户/竞争者资料交叉验证。
- S14-S16 仅支撑行业机制和竞争背景，不外推 Hubbell 市占率、订单或利润。
- S17-S18 仅建立 valuation boundary；分红与回购按一个一致口径进入 IRR。
- 所有下载文件需记录 URL、文件日期、访问日期、内容类型、页码/表格定位、提取方法和 usability；失败或阻断保留在采集日志。
