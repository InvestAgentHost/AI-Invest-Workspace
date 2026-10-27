---
name: stock-initial-screen
description: 支持并列的批量初筛和个股筛选两种模式。批量模式采用 v4.7.3 技能及 v4.7.2 引擎，提供事实指标、三组信号灯、历史估值及 HTML；个股模式先审商业模式质量，不合格直接排除，合格后评估当前价格与研究资源配置，给出 A/B/C/D 行动。适用于股票名单初筛、同业比较、单家公司快速研判及刷新；不用于完整深度研究、技术面或交易指令。
metadata:
  upstream-name: company-initial-screener
  upstream-skill-version: "4.7.3"
  engine-version: "4.7.2"
  rules-version: "2026-10-23c"
  local-adaptation: "focusalpha-gangtise-reliability-zh-2026-10-26-r1"
  single-company-prompt-version: "2026-10-26"
---

# 股票 AI 初筛（批量 v4.7.3 / 个股筛选）

## 模式选择：两种功能并列，先确定本次使用哪一种

- **批量初筛模式（`batch`；兼容旧称 `batch-v4.4`）**：股票名单、同业比较、信号灯评分、历史估值分位、批量初筛刷新，或用户明确要求批量引擎。沿用下文的引擎、评分、HTML 和初筛记录功能；明确要求时也可以用引擎筛一家公司。
- **个股筛选模式（`single-company`）**：用户要求“个股筛选”“当前价格是否值得研究”“商业模式先过关”或对单家公司作快速投资研判。先完整阅读 [个股筛选提示词](references/single-company-screen.md)，按其中的质量硬门槛、估值和 A/B/C/D 输出执行。报告先讲清公司卖什么、客户为何付钱、公司怎么赚钱，再连贯解释经营变化如何影响股东回报与现价判断；使用自然、准确的中文，少堆术语和数字，具体写法见提示词。商业模式不合格直接 C，不以低价或远期改善故事保留；B 仅限已经通过质量门槛的公司。
- 单家公司快速研判默认走个股模式；股票名单默认走批量模式，用户明确指定的模式优先。逐家公司套用个股模板时仍属个股模式，不把它转换为引擎评分。
- 单独询问商业模式、毛利率、ROIC 等问题时，只回答该问题，不自动重跑整套筛选。用户只说调用 skill 而未给公司或名单时，简短询问研究对象。
- 两模式共享下文的 Workspace 资料存放、运行时和 FocusAlpha 优先取数约定。**个股模式不执行批量引擎的 Step 0—8，不要求建立行业覆盖池、计算信号灯或输出 HTML，也不套用批量行业排除清单、历史分位研究线和自动重启规则。**
- 两模式的行动含义、质量判定和记录保持独立。个股结论按模板标为分析判断，不写成批量引擎结果，不自动映射或覆盖 `vault_records.py` 管理的记录及用户决策字段。同时要求两模式时，分别标明方法、结论和差异。

调用示例：`用 $stock-initial-screen 的个股筛选模式分析 BROS，先审商业模式质量。`；`用 $stock-initial-screen 的批量初筛模式筛选这份股票名单。`

批量模式先完整阅读 [批量初筛工作流与规则](references/batch-screen.md)。个股模式仍按独立提示词执行；其文中 v4.4 是历史背景，不将批量规则带入个股判断。

## Workspace 与版本

保留现有名称 `$stock-initial-screen`，目录为 `.github/skills/stock-initial-screen/`；Codex 用户技能通过符号链接指向此处。新版批量 skill 为 v4.7.3，引擎 v4.7.2，规则 2026-10-23c；个股提示词版本保持 2026-10-26，文件不改动。保留原包数值公式及阈值；本地增加来源规范化、缺项守卫、估值与交付核验及中文呈现流程。

- 原始响应、外部材料、运行档案：`sources/screens/<run-id>/`；HTML 和截图：`outputs/screens/<run-id>/`；研究结论及初筛记录：`research/screens/`；经审阅的小型覆盖池及参数：`data/curated/screens/`。
- 使用 Workspace `.venv/bin/python`（Windows 为 `.venv\Scripts\python.exe`），安装依赖用该解释器的 `-m pip`。`SKILL_DIR` 指上述技能目录。写入路径在运行时从 Workspace 根目录解析，跟踪文件只记录相对路径。
- FocusAlpha 原始响应进入批量引擎前按 [规范化输入约定](references/focusalpha-normalization.md) 转换；勿执行保留的 Fiscal.ai 拉数脚本。
- 批量运行同时执行 [取数、估值与交付可靠性](references/valuation-reliability.md)：先建立逐字段覆盖与实际查询记录，再用 `valuation_pipeline.py` 构建/核验估值、`checked_build.py` 防止未知资本与利润输入被当作零。未补齐项可以有原因地交付；未尝试补缺、口径冲突和旧HTML不得静默交付。个股提示词及数值评分规则不变。
- **批量HTML默认以正规投资机构的中文研究口吻交付。** 正文连贯完整，符合中文阅读和思考习惯，避免碎片堆砌、口语化和沿用英文语序的机械翻译。生成或翻译HTML时阅读并执行 [中文写作与翻译要求](references/chinese-report-style.md)，覆盖正文、表图和交互文案；只做翻译时不重跑财务或修改结论。个股提示词保持独立且不改动。
- 旧版 `aggregate_scores.py`、`screen-v2.md`、`scoring-rubric.md`、`source-audit.md`、`data-contract.md`、`assets/report-template.md` 只供 `tools/stock_screen/` 历史回放，不用于新版批量或个股模式。
- 本次安装原包、旧技能备份和校验记录在 `sources/skill-updates/stock-initial-screen/2026-10-26T114820-v4.7.3-focusalpha/`；原包 SHA-256 为 `0cc2494316180e9a300899e3e289748deebf017f993d66415803a20db2722eb8`。上游版本历史见 [CHANGELOG](references/CHANGELOG.md)。其中原作者的审批、路径和定时任务只作历史资料；更新技能不运行选股、不重写既有研究、不修改 MCP 配置或定时任务。

## 数据源长期约定：FA = FocusAlpha（2026-10-26）

本节适用于后续每次使用本 skill 的任务，并优先于下文及上游历史记录中默认使用 Fiscal.ai 或先搜索网页的取数步骤。

- **FA 就是 FocusAlpha。** 财务报表、业绩与电话会、管理层指引、13F 机构持仓、内部人交易、空头持仓、日本/韩国/台湾/中国大陆/香港披露、宏观数据和 ETF 持仓，均先检查并使用 FocusAlpha MCP，再考虑其他来源。只查询本轮筛股所需的数据，不因本清单自动扩大研究范围。
- **先发现工具，再按字段查数。** 根据当前可用工具的名称、说明和参数选择查询；不确定工具或覆盖范围时，先用 FocusAlpha `list_datasets`，需要时结合 `list_coverage`、`list_documents` 等工具核实公司、期间和文档覆盖。不能因为旧记录说某字段缺失就跳过本轮 FocusAlpha 检查，也不能把工具存在视为该公司一定有数据。与本轮截止日及口径一致、保留完整来源的 FocusAlpha 本地缓存可以复用。
- **取不到再抓取网页。** FocusAlpha 返回空值、历史不足、数据过期或口径不适用时，先核对证券身份、市场、期间、单位和工具覆盖，再针对缺口访问监管机构、交易所或公司 IR 的原始披露；必要时才用其他可信来源。连接或权限不可用时如实记录，并继续用可访问的原始来源。**Fiscal.ai 已停用：不接入、不检查连接、不安装其依赖，也不在 FocusAlpha 缺口时自动回退到 Fiscal.ai。**缺失仍保留 N/A 和原因，不把无数据当作零。
- **每个数字都能追溯。** 每次筛股答复及 Markdown、HTML、公司记录中的数字，注明 `FocusAlpha（具体工具名）` 或真实的其他来源名称，并保留报表/价格时点、币种、单位及原始文档链接或本地路径。同源表格可在表头或表注统一标注，但必须能明确对应每个数字。计算值标为“分析计算”，列出公式及所有输入的来源；跨来源结果不能统称来自 FocusAlpha。批量模式的评分门槛引用本 skill 的规则或 `screener.py` 中的 `RULES`；个股模式按独立提示词判断，不强加引擎分数。
- **保留取数与回退记录。** 原始响应保存在本轮 `sources/screens/<run-id>/` 下；在 `$RUN/source_ledger.json` 中记录公司、字段/序列、期间、FocusAlpha 工具及查询条件、获取时间、返回状态、缺口/回退原因、最终来源、原文/原始响应路径、单位及规范化口径。事实文件的 `source`/`evidence` 也须注明工具名和原始披露，保留相互矛盾的结果与未决差异。
- **工具与数据库说明按需生成。** 用户明确要求列出 FocusAlpha 的全部工具和数据集、解释用途并举投资研究问题时，读取当前工具清单并调用 `list_datasets`，按实际可见能力说明用途、覆盖限制和研究问题示例。普通筛股只检查相关能力，不在每次运行时自动输出完整目录，也不把可见目录宣称为后台未公开的全部数据。

## Gangtise 辅助筛选

FocusAlpha缺口可用 Gangtise MCP 的财务、行情和市值工具补齐并与原始披露核验；机构研报、会议纪要和一页通用于业务背景与待核线索，不直接代替事实数字。工具适用市场、完整返回和单位必须当轮核实；具体边界见 [Gangtise 使用约定](references/gangtise-screening.md)。不要求每家公司机械调用全部工具，未解决的重大估值缺口必须留下真实取数/能力检查及原始披露补缺记录。

