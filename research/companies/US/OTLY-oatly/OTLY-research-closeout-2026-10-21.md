---
type: company-research-closeout
company_id: US-OTLY-oatly
ticker: OTLY
as_of: 2026-10-21
status: archived
decision: excluded
decision_origin: analyst-confirmed
investment_horizon: approximately-two-years
---

# Oatly（OTLY）研究结论与归档

## 分析师确认的结论

**近两年内基本无投资价值，当前排除，结束本轮研究并保存完整资料。**

结论来自分析师2026-10-21的明确指示；用户报告开篇结论为“排除”。判断窗口为自本次归档起未来约两年，不设自动到期提醒或自动重启研究。此项是投资筛选决策，未由Agent补造目标价、收益率或估值参数。

## 结论依据与保留的反向证据

以下为用户报告观点的归纳，不代替对财报原件的逐项核验。段落定位对应S148的`OTLY.paragraphs.txt`，不是Word页码。

- 历史扩产与资本配置失误造成减值、退出成本和资本消耗。定位：P003、P035–P079。
- 轻资产生产、供应链和费用调整已经改善经营基础；收入、品牌表现和毛利修复是需要保留的正面证据。定位：P004、P107–P114、P122–P185。
- 经营修复尚未充分转化为持续营业盈利和股东现金回报。定位：P183–P185、P213–P217；既有费用分析另见`data/derived/companies/US/OTLY-oatly/operating-analysis-20261021/operating-expenses-analysis.json`。
- 报告认为，历史债务和利息负担仍然沉重，2028年主要债务到期前可能需要结合资产处置、展期或再融资解决。定位：P005–P006、P203–P223。这是报告判断；没有把出售中国业务或再融资视为已经完成。

## 归档报告与底稿

| 用途 | Workspace相对路径 | 归档身份 |
|---|---|---|
| 用户报告归档原件 | `sources/companies/US/OTLY-oatly/user-provided/research-reports/2026-10-21/OTLY.docx` | S148，原样复制并校验SHA-256 |
| 用户报告查阅副本 | `research/companies/US/OTLY-oatly/outputs/workbooks/OTLY.docx` | 保留用户上传位置，内容与归档原件相同 |
| 报告文本定位 | `sources/companies/US/OTLY-oatly/user-provided/research-reports/2026-10-21/OTLY.paragraphs.txt` | 保留正文段落序号；不替代原稿中的图表 |
| 历史Excel | `research/companies/US/OTLY-oatly/outputs/company-research-to-excel/OTLY_model.xlsx` | 保留当前版本及原有格式、公式 |
| Excel归档快照 | `sources/companies/US/OTLY-oatly/artifacts/archives/2026-10-21/OTLY_model.xlsx` | 与当前底稿逐字节一致，供未来版本变化后恢复 |
| 原始财报、官网及补充资料 | `sources/companies/US/OTLY-oatly/` | 原件及清洗层保留，来源登记共148项 |
| 复算、证据与验证记录 | `data/derived/companies/US/OTLY-oatly/` | 可重建计算和历史核验保留 |
| 研究上下文与证据台账 | `research/companies/US/OTLY-oatly/data/` | 历史记录不清空，追加归档决定 |

Word原件SHA-256：`909d17230d8a56f1908daad3ce734ba38b6d1583cad0be17e4c5318cf995d082`。

Excel归档时SHA-256：`96e5e67a82413e7a23cce42fadefcdfd1080d87802f537562cc4cdaace92e4bc`。

## 归档边界与已知问题

- 本次执行资料归档、报告原样保全、索引和文件完整性校验；未改写Word、更新Excel或重跑完整财务及图表审计。
- 原始资料覆盖FY2021–FY2025和2024Q3–2026Q2；本次未新增财报抓取，不将归档日冒充所有资料的发布日期。
- 保留此前官网访问、部分来源仅为网页文本表示，以及同店、促销、纯价格、真实利用率和费用归因等证据缺口。既有准备材料的PARTIAL状态不因归档而改为PASS。
- 原报告P134仍有“FY25年产能5.95亿……产能利用率60%”表述。既有核验中594.9百万升是产量，集团约1000百万升为年末燕麦基成品当量技术能力；两者相除仅为诊断比值。原稿原样保留，恢复研究或对外使用前应处理这一已知口径问题。
- 详细文件清单、大小、哈希及校验结果保存在`sources/companies/US/OTLY-oatly/artifacts/archives/2026-10-21/`；不覆盖2026-10-20的历史采集清单。

## 后续恢复研究的备忘

以下是Agent整理的重新评估条件，未设自动监控：债务期限和利息负担出现实质改善；潜在资产处置的对价、到账及资金用途明确；持续营业盈利和现金创造有多期证据；新增融资对普通股东的稀释与剩余权益价值可以清晰评估。发生变化后，应从本次结论和旧证据重新核对，而不是自动沿用排除结论。

## 来源

- 分析师在当前会话中的2026-10-21归档指示。
- S148：用户上传的`OTLY.docx`及其原样归档副本。
- 既有来源登记、证据台账、财报底稿和经营计算，入口见[资料目录](materials.md)。
