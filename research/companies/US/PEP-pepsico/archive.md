# PEP 研究归档

归档日：2026-11-02（Asia/Hong_Kong）；资料核对：2026-11-03。研究基本完成，报告、底稿、来源和后续跟踪所需资料统一编目。归档不表示已买入或改变原投资结论。



## 阅读入口

| 角色 | Workspace 路径 | 版本与处理 |
|---|---|---|
| 主报告 | [PEP.docx](outputs/reports/2026-11-02/PEP.docx) | 原样复制用户提供版本；Word 元数据最后修改于 2026-10-30，不能将归档日解释为内容全面更新日 |
| Elliott 补充研读 | [研读报告](outputs/elliott-review-20261030/PEP_Elliott_Review_2026-10-30.docx) | 上传件与现有文件逐字节相同，复用现有文件，不另存副本 |
| 财务、预测与估值底稿 | [PEP_model.xlsx](outputs/company-research-to-excel/PEP_model.xlsx) | 原位置保留，只读核对；采用已保存三情景，未保存、重算写回或更新参数 |
| 后续跟踪 | [规则](tracking/rules.md)、[保留基线](tracking/baselines/2026-11-02.md)、[人工决定](tracking/decisions.md) | 承接报告判断；原始文件和底稿默认只读 |
| 原始证据 | `sources/companies/US/PEP-pepsico/` | 原件保持不变；Elliott 原 PDF 在 `investor-presentations/elliott-2025/` |
| 图表与专题 | [索引](outputs/README.md) | 沿用已有当前版，不新增图片、重打包或重复报告 |

上述链接以本公司研究目录为起点。用户桌面的两份原文件保持原样，不移动、不删除。

## 补充外资研报

2026-11-03接收；以下日期以PDF封面为准，均与原文件名前缀日期不同。五份文件可正常读取，哈希彼此不同，未发现与现有公司PDF完全相同的文件；原件暂留`data/inbox/`，未移动或重命名。本轮仅完成元数据、首页与可读取性核对，未形成五份研报的完整对比分析。

| 机构 | 报告日期 | 页数 | 首页主题 | 原文件 |
|---|---|---:|---|---|
| 汇丰 HSBC | 2026-10-09 | 8 | 北美饮料需求、渠道与数字化问题 | [PDF](<data/inbox/20261015-汇丰控股-百事(PEP.O)：PepsiCo (PEP US) Hold No real fix in sight for PBNA.pdf>) |
| 瑞银 UBS | 2026-10-08 | 15 | Q3业绩初评与全年指引变化 | [PDF](<data/inbox/20261015-瑞银-百事(PEP.O)：PepsiCo Inc_ Organic Sales Come In Stronger, But ‘26 EPS Guidance Moves Lower.pdf>) |
| TD Cowen / TD Securities | 2026-10-09 | 12 | 北美定价、销量及战略透明度 | [PDF](<data/inbox/20261015-道明证券-百事(PEP.O)：Ongoing Weakness in North America Drives Guidance Cut.pdf>) |
| RBC Capital Markets | 2026-10-09 | 10 | 再特许经营选择与2027年恢复节奏 | [PDF](<data/inbox/20261016-加拿大皇家银行-百事(PEP.O)：PEP EPS Aftermath - Moving Closer to Refranchising  Tough Choices Need to be Made; Sector Perform.pdf>) |
| 杰富瑞 Jefferies | 2026-10-12 | 12 | CFO交流：运营模式、定价和再投入 | [PDF](<data/inbox/20261019-杰富瑞金融-百事(PEP.O)：A Longer Pour w_Management; 3Q Update & Fireside Recap.pdf>) |

来源ID、原题和SHA-256见`data/source-index.md`的S114—S118。研报中的预测、目标价与观点属于各机构在报告时点的判断，不能直接当作当前公司指引、市场共识或本研究已采用参数；尚未提供原始下载URL。

## 补充机构模型

2026-11-03接收[高盛PEP_model.xlsx](<data/inbox/高盛PEP_model.xlsx>)，工作簿内公司标识为PepsiCo / PEP、机构标识为Goldman Sachs，共34张工作表。主要包含`Summary Model`、`Quarterly Earnings`、六个现行分部、三表及债务/利息/股数、`Valuation`和`DCF`；汇总模型可见实际列至2026Q3，预测列延伸至2028年。部分历史分部和专题仍沿用旧结构，不能直接拼接成同口径时序。

封面`Cover!H21`虽标为Date Published，实际公式为`TODAY()`；其缓存和文件保存日期不能证明模型真实发布日期，版本日期暂记未确认。该原件包含24个外部链接部件；只读抽查见`DCF!H17`缓存为`#DIV/0!`，并且`DCF!B6`明确注明DCF不是该模型目标价的依据。这里只记录原件状态，未修复、重算或刷新外部链接，也未采用其估值结果。

来源ID为S119，指纹及定位见`data/source-index.md`。原件暂留inbox，未移动、改名或另存副本；自有研究底稿仍是上方`outputs/company-research-to-excel/PEP_model.xlsx`，两者独立。本轮完成结构及元数据核对，尚未做预测差异、口径和公式的全面比较。

## 文件指纹

SHA-256：

| 文件 | 字节数 | SHA-256 |
|---|---:|---|
| 主报告 | 22,033,718 | `275ba1bd35f85129c93656d8a16f67175a92db0256f07c003004f129031b7ad7` |
| Elliott 研读报告 | 713,141 | `822d79434650c51ae2bae6365b8273f44adba935833533b0d38e9169d220c107` |
| 当前底稿 | 432,627 | `4f350c89b0b54e57d145d5c12669cc2b2b2aba412fa13c168851833887368f11` |

两份 Word 的 ZIP 完整性检查通过。主报告归档副本与来源哈希相同；Elliott 上传件与原有 Workspace 版本哈希相同。没有进行 Word 排版重制或全页重新审稿。

## 保留的研究结论

主报告“结论”认为，价值基础是 Frito-Lay 的品牌和配送网络、国际特许饮料的盈利能力；回报的关键是北美需求与利润能否同时修复。国际增长可以缓冲北美弱势，不能代替北美恢复。并购减值、资产利用和薪酬问责是反证，不能因 Elliott 参与而忽略。

报告采用温和利润增长与分红支撑回报，对大幅利润率修复保持克制。估值判断保留原研究时点；当前股价、当日预期回报和交易动作未在本次归档中更新。Elliott 研读报告的改革收益是待检验情景，不自动替代底稿假设。

## 核对结果与未决事项

- **归档核对通过。** 已核对原件、去重、路径及指纹；原件和 Excel 内容不变。归档 Word 及临时 Excel 所有权文件已在公司 `.gitignore` 中排除，未改动根目录既有用户变更。既有已跟踪的 Excel/Elliott Word 沿用仓库历史，本次不新增二进制文件入 Git，也不提交 Git。
- **估值算术抽查通过。** 从当前底稿只读读取三情景利润路径，独立复算五年 CAGR 和研究日折现价，与缓存结果一致；两张预测/估值表缓存未发现 Excel 错误值。这是抽查，不是整本底稿重新审计或 Excel 引擎重算。记录位于 `data/derived/companies/US/PEP-pepsico/archive-2026-11-02/readonly-checks.json`。
- **实时路径与基准快照不同。** `Profit Forecast` 当前对应乐观路径，实时五年归母利润 CAGR 为 4.13%；估值表基准快照为 3.03%。已保存快照不会随实时预测自动刷新。跟踪必须区分两者。
- **历史价格不能当作现价。** 底稿参考价为 2026-10-28 的 132.63 美元；报告“134美元”是其叙述采用的历史近似价。保留差异，不把任何一项写成 2026-11-02 现价。要求 15% 回报时的约108美元基准估值是旧模型结果，不是已批准自动交易阈值。
- **薪酬措辞需要纠偏。** 主报告“薪酬计划”首段仍称两项“考核门槛”严重未达；应理解为目标未达。其后段落已明确，现有证据不足以认定发奖违规。后续引用应遵循后一判断；本次没有改写原 Word。
- **估值资金用途闭环仍为 PARTIAL。** 底稿的分红和粗略回购覆盖检查不能替代完整并购、债务偿还、再投资与现金用途预算。当前原件的模型版本不同于旧估值记录的哈希，本次以实际文件指纹和读取值为准，未用旧中间文件覆盖。
- **本次仅做接入核验。** 查验了 FocusAlpha 文件索引/指引/事件入口及若干 SEC 原文，不声称完成截至归档日的全量新闻扫描。外部覆盖边界和待补来源见跟踪基线；不能将初始资料准备的 PASS 延伸为全份研究独立审核通过。

## 跨设备保存

Git 保存归档索引、规则及研究文字；主报告、图表、来源和重建记录等被忽略材料仍需手工转移。最低应一并转移本公司 `outputs/`、`sources/companies/US/PEP-pepsico/`；需要重建图表时再带上 `data/derived/companies/US/PEP-pepsico/`。本次没有创建 ZIP、上传云盘或引入自动同步。
