---
name: valuation-binding-methodology
description: Build, audit, or update an evidence-bound company valuation from historical disclosures and operating drivers through fiscal-year forecasts, cash and share-count constraints, shareholder IRR or DCF, and a traceable analyst handoff. Use when deep research reaches valuation or subsequent results require refreshing an existing valuation workbook and its assumptions.
---

# 估值推导与持续更新

本 skill 负责预测假设、情景、估值方法与公式、现金和股数约束，以及估值核验、交付和后续跟踪。公司业务、行业和会计分析由相关研究 skill 负责；历史实际数据、历史衍生指标及其数据质量由 [company-research-to-excel](../company-research-to-excel/SKILL.md) 负责。平台 spreadsheet 能力执行 Excel 文件操作。

复用已完成的历史底稿；新增或修改的估值 sheet 与历史底稿共用其 [style-profile.json](../company-research-to-excel/assets/style-profile.json)，具体格式继承见本 skill 的 [workbook contract](references/workbook-contract.md)。历史底稿 skill 只保留估值转交和文件衔接，不另行维护预测与估值规则。

## 入口与边界

- **初次推导**：读取现有原始资料、底稿、报告和分析师决定，按下列流程形成可复算的模型与交接记录。
- **持续更新**：先读 [tracking-contract.md](references/tracking-contract.md)，恢复上一轮投资逻辑、预测版本、人工锁定参数与更新规则，再更新依赖链。
- **核查**：只读审计，除非用户同时授权修复。不以检查模型为由改写用户参数。
- **遗留模型迁移**：先读 [model-contract.md](references/model-contract.md) 的版本迁移规则，不悄悄改变现有计算约定。

尊重本次任务范围与已有授权。常规更新在已授权范围内继续；新资料不足、预测待决与重大投资逻辑转变分别列示，不把所有更新都变成批准流程。本 skill 不授权交易、外发消息、云上传或创建定时任务。

## 推导流程

1. **接续研究**：确认估值日、财年、币种、单位、权益口径、业务边界、最新实际期、原始资料与产物路径。提取投资主线、反证、未决问题和已批准假设。正式披露是历史数据来源；报告只提供研究判断和决策背景。
2. **补齐历史**：复用已核验的历史底稿，依 [research-workflow.md](references/research-workflow.md) 检查完整年度窗口及连续近期季度，只补估值所需缺项。10-K／10-Q 数据补充遵循历史底稿 skill 的来源和复核要求；指引与预测单独标识，保留重述与口径变化。可比口径下 Q4=全年−前三季度适用于可加总流量。
3. **先完成当前财年**：剩余季度逐项预测，与已披露季度相加得到完整财年基期。先摆历史数值，再讨论假设；不用 TTM 与年结日并列维护两套正式预测。
4. **逐年推导未来**：公司自身经营驱动→收入与成本→经营利润→利息、税及其他损益→归母净利润。先预测驱动和年度数值，再计算 CAGR；不为凑目标 CAGR 反推经营假设。
5. **现金与股数闭环**：独立推导 FCF、现金分红、发行与回购、净缩股、债务与其他必要现金用途。资本支出的现金时点不等于损益摊销时点。
6. **估值计算**：先选择适用方法。盈利公司默认采用直接退出 PE、分红现金流、净缩股的股东回报模型；标准 FCFF/FCFE DCF、SOTP 等另按匹配口径计算。依 [model-contract.md](references/model-contract.md) 固定定义、日期与公式。
7. **校验与交付**：实际数据→假设→推导→估值→报告一致。交付当前模型、EPS、关键敏感性、所需回报对应买入价、资金约束及尚未解决的问题。报告以观点与推导链为主，附必要表格；遵循用户指定的对话/文件交付方式。

## 底稿要求

创建或修改工作簿前读 [workbook-contract.md](references/workbook-contract.md)。

- `Valuation Driver Build` 或等效推导 sheet：**预测在左，历史数值在右，同一指标对齐**。剩余季度和未来年度预测都必须有可读的历史参考，不以来源链接代替数值。
- 顺序：剩余季度→本财年全年基期→未来年度→现金与股数约束→估值输入；详细解释、索引和溯源统一放最后。
- `Year-End Valuation` 或等效估值 sheet：链接已采用参数，逐年计算利润、股数、EPS、分红与退出价值，不重复硬编码。
- 字体、字号、配色、数字格式及行高沿用共享样式配置；按内容增加高度，不另设更小字号或更低行高。明确实际/预测/输入/公式，在正常缩放下检查实际版面。
- 修改已有工作簿时保留人工输入与未涉及 sheet、格式、公式及原生功能。不得从过期中间数据整本重建覆盖用户修改。

## 持续接管的最小记录

采用 [tracking-contract.md](references/tracking-contract.md) 与 [handoff-template.json](assets/handoff-template.json)。它是字段骨架，不是预测样例；不得把空值当作零，也不得直接交付未填模板。

记录方法版本、业务主线与重审触发条件、数据定义、历史锚点、依赖/公式、已采用数值、来源定位、人工决策、更新策略、Excel 映射、上一版预测和验证状态。已有等效台账可复用，不重复创建同类文件。

稳定 metric ID 表示经济含义；单元格地址只是可变的展示映射。先检测用户在 Excel 的修改，将其纳入已采用输入，再更新；不能被后台记录静默覆盖。

## 确定性核验工具

通过 Workspace `.venv` 执行：

```text
.venv/bin/python .github/skills/valuation-binding-methodology/scripts/valuation_checks.py calculate <model-input.json>
.venv/bin/python .github/skills/valuation-binding-methodology/scripts/valuation_checks.py validate <handoff.json>
.venv/bin/python -m unittest discover -s .github/skills/valuation-binding-methodology/scripts -p 'test_*.py'
```

`calculate` 独立复算直接 PE/净缩股的日期现金流及资金预算；输入契约见 model reference。`validate` 检查交接记录的关键字段、来源、依赖和右侧历史映射。它们不抓取数据、不修改 Excel、不代替会计判断、图形检查或标准 DCF 实现。缺失必要现金用途时输出 `PARTIAL`，不得称资金已闭环。

## 发布条件

- **PASS**：重要数据和假设可追溯；实际表、推导表、估值表与报告一致；独立计算、资金约束及版面验收通过。
- **PARTIAL**：可计算，但存在重要未验证判断、未披露现金用途或其他实质缺口；明确结果的适用边界。
- **BLOCKED**：核心口径或必需输入缺失/矛盾，使对应结果不成立；其余研究仍可继续。

“可计算”只说明输入满足公式条件，不说明参数合理、资金可行或研究已完成。不可将参考公司的分部、策略、数值、合同期限或现金安排带入新公司。
