# Congressional Monitor

面向 ChatGPT 终端工作流的美国国会议员交易申报分析工具。它读取 `data/curated/` 中已核验的 House Clerk PTR 快照，输出交易统计和可筛选明细。13F 参考网站不参与运行，网站只是可选的展示原型。

## 使用

从 Workspace 根目录运行：

```bash
# 总览：记录数、议员分布、方向、资产类型和高频证券
.venv/bin/python -m tools.congressional_monitor.cli summary

# 查看 Pelosi 的买入记录
.venv/bin/python -m tools.congressional_monitor.cli trades \
  --member pelosi-nancy --direction P

# 查看 BE 涉及的议员交易
.venv/bin/python -m tools.congressional_monitor.cli ticker BE

# 输出 JSON，便于 ChatGPT 后续分析或保存到 data/derived/
.venv/bin/python -m tools.congressional_monitor.cli ticker BE --json

# 根据明确披露的股数/期权合约数估算净变动
.venv/bin/python -m tools.congressional_monitor.cli positions --member CA11

# 一次生成交易、净变动、覆盖和质量摘要
.venv/bin/python -m tools.congressional_monitor.cli report \
  --member CA11 --from-date 2026-05-28 --to-date 2026-08-28 --json

# 查看数据覆盖和来源报告
.venv/bin/python -m tools.congressional_monitor.cli coverage --json

# 校验字段完整性和重复交易 ID
.venv/bin/python -m tools.congressional_monitor.cli check --json

# 对扫描型 PDF 的第 1 页调用 GLM OCR（Key 从 .env 读取）
.venv/bin/python -m tools.congressional_monitor.cli ocr \
  sources/providers/house-clerk/2026/khanna-8221322.pdf --pages 1 --json

# 检查 OCR 输出；发现风险时只进入复核队列，不会改写 curated 数据
.venv/bin/python -m tools.congressional_monitor.cli ocr-check \
  data/derived/congressional-monitor/ocr/<ocr-result>.json --json

# 按坐标解析候选交易，并把不确定行写入待复核队列
.venv/bin/python -m tools.congressional_monitor.cli ocr-parse \
  data/derived/congressional-monitor/ocr/<ocr-result>.json \
  --review-output data/derived/congressional-monitor/review/<report>.json --json

# 从 House Clerk 年度索引发现 PTR 文档（不自动下载）
.venv/bin/python -m tools.congressional_monitor.cli house-index \
  sources/providers/house-clerk/2025/2025FD.zip --filing-type P --json

# 生成复核决定模板；编辑 status 和字段后再应用
.venv/bin/python -m tools.congressional_monitor.cli ocr-review \
  data/derived/congressional-monitor/review/<report>.json \
  --template-output data/derived/congressional-monitor/review/<report>-decisions.json

# 将 approved 记录写入一个新的 curated 文件（不会覆盖已有文件）
.venv/bin/python -m tools.congressional_monitor.cli ocr-review \
  data/derived/congressional-monitor/review/<report>.json \
  --decisions data/derived/congressional-monitor/review/<report>-decisions.json \
  --output data/curated/congressional-reviewed-<year>.json

# 下载 House Clerk PTR 原件（不覆盖已有文件）
.venv/bin/python -m tools.congressional_monitor.cli house-download \
  <document-id> --year 2026 --json

# 端到端同步：发现报告、检查文本层；加 --download 才下载新 PDF
.venv/bin/python -m tools.congressional_monitor.cli sync \
  --year 2025 --member Pelosi --limit 20 --json

# 第二次及以后运行会读取状态并只报告变化；可自定义状态文件
.venv/bin/python -m tools.congressional_monitor.cli sync \
  --year 2025 --member Pelosi \
  --state-file data/derived/congressional-monitor/state/house-2025-pelosi.json \
  --json

# 多年度 House 全量同步；P=原始 PTR，A=修订/更正，默认两者都纳入
.venv/bin/python -m tools.congressional_monitor.cli sync \
  --year 2024 --year 2025 --incremental --download --json

# 只同步原始 PTR（例如不想在本轮处理修订）
.venv/bin/python -m tools.congressional_monitor.cli sync \
  --year 2025 --filing-types P --incremental --json

# 将 sync 清单批量转换为交易事件；扫描件只进入 OCR 队列
.venv/bin/python -m tools.congressional_monitor.cli house-parse \
  data/derived/congressional-monitor/sync/2025.json --json

# 对有效交易事件做统计并输出描述性提醒
.venv/bin/python -m tools.congressional_monitor.cli house-events \
  data/derived/congressional-monitor/parse/2025.json --json

# 分析议员群体行为；默认输出近 30/90 日，并自动计算议员重点级别
.venv/bin/python -m tools.congressional_monitor.cli behavior-report \
  data/derived/congressional-monitor/events/2025-2026-ocr.json \
  --windows 30,90 --member-profiles data/curated/congressional-member-profiles.json --top-n 50 \
  --output-md research/congressional-monitor/2025-2026-behavior-report.md --json

# 为 Agent 生成可断点续跑的复核批次（不自动批准、不改 curated）
.venv/bin/python -m tools.congressional_monitor.cli agent-review \
  data/derived/congressional-monitor/parse/2025-2026.json \
  --output-dir data/derived/congressional-monitor/agent-review/2025-2026 \
  --batch-size 50 --json

# 查看某年度所有有 PTR 申报的 House 议员（不指定 --member）
.venv/bin/python -m tools.congressional_monitor.cli house-index \
  sources/providers/house-clerk/2025/2025FD.zip --filing-type P --json

# 读取官方 Senate eFD JSON/CSV 导出并统一字段
.venv/bin/python -m tools.congressional_monitor.cli senate-efd \
  sources/providers/senate-efd/<export>.json --json

# 合并 House curated 与 Senate eFD，生成两院报告
.venv/bin/python -m tools.congressional_monitor.cli \
  --senate-file sources/providers/senate-efd/<export>.json \
  cross-report --from-date 2026-01-01 --json

# 追加已规范化的历史年度文件（相对 data/curated/）
.venv/bin/python -m tools.congressional_monitor.cli summary \
  --data-file congressional-members-2025.json
```

筛选参数：`--member`、`--ticker`、`--from-date`、`--to-date`、`--direction P|S|E`、`--asset-type ST|OP|AB|OT`。`member` 命令也可以把 `pelosi-nancy`、姓名或选区作为位置参数传入。`--data-file` 可重复，用于追加历史年度或其他已规范化的 JSON 文件。

`positions` 输出的是按议员、ticker、资产类型聚合的“已披露数量净变动估计”。只有原始说明中明确出现股数或期权合约数的记录才计入；金额区间不能反推出股数。结果包含未知数量记录数和 `partial`/`complete_for_explicit_quantities` 标记，不代表真实当前持仓。

## GLM OCR

将 Key 放入 Workspace 根目录的本地 `.env`（该文件不纳入 Git）：

```text
GLM_OCR_API_KEY=填写你的 key
GLM_OCR_BASE_URL=https://open.bigmodel.cn/api/
GLM_OCR_TOOL_TYPE=hand_write
GLM_OCR_LANGUAGE_TYPE=ENG
GLM_OCR_PROBABILITY=true
```

工具只对扫描页面调用 OCR；每页结果按源文件 SHA-256、页码和 DPI 缓存到 `data/derived/congressional-monitor/ocr/`。当前官方 OpenAPI 文档列出的 `tool_type` 枚举为 `hand_write`；如 GLM 账户文档提供打印体工具类型，可通过 `GLM_OCR_TOOL_TYPE` 覆盖。OCR 输出必须经过 PTR 字段校验和人工抽查后，才能进入 curated 数据。

`ocr-check` 会读取 OCR JSON，检查页面平均置信度、低置信度文本块以及 PTR 表头、日期、金额区间和交易方向信号。它只生成质检结果，不会把 OCR 文本当作交易事实。

## 数据边界

当前快照包含 Pelosi 的 3 份 2026 PTR，以及 Gottheimer、Salazar、Crenshaw 各自当前载入的报告。工具分析的是延迟的交易申报事件，不是全体议员目录，也不是完整实时持仓。补充历史数据时，先将每份报告规范化为同一字段并通过 `--data-file` 加载，再按交易日计算净变动。House 全量同步可重复传入 `--year`，跨年度按文档 ID 和交易指纹去重；A 类型修订报告保留为独立报告，只有存在明确 `amends_report_id` 时才建立替代关系，无法显式关联的修订会标记为 `unlinked_amendment`。

状态化同步会在 `data/derived/congressional-monitor/state/` 保存可重建的 JSON 快照，并在同步结果的 `changes` 中输出新增报告、内容变化、运行状态变化和 OCR 候选变化。使用 `--incremental` 时，未变化 PDF 会复用文本层和已完成 OCR 元数据，避免 House 全量批处理重复识别。状态文件不属于 curated 数据，也不会改变交易分析结果。

`house-parse` 生成的结果保存在 `data/derived/congressional-monitor/parse/`，包括报告解析状态、OCR 队列、待复核候选、可分析交易和修订后的有效交易视图。`house-events` 只对有效交易做统计和描述性提醒，不把提醒解释为内幕信息或交易动机。

`behavior-report` 是议员行为分析层。它默认只输出近 30/90 日窗口，优先保证监控时效性；需要历史背景时可显式加 `--include-full-period`，也可用 `--windows` 自定义。历史数据仍用于判断“首次出现”和计算当前窗口相对于前一同长度窗口的变化。工具按 ticker 汇总买入/卖出议员数、交易数、参与率、披露覆盖率、方向性议员净差、重复买入、首次出现、明确数量净变化、金额区间等级、党派/两院覆盖，并按启发式行为分数排序；同时输出近期议员画像、自动重点级别（领导职务、委员会职务、媒体关注度、近 90 日交易活跃度、历史覆盖度）、买卖变动众数和窗口对比趋势。`--members` 可指定重点议员，只影响画像部分，不改变群体统计；`--member-profiles` 可提供可审计的议员元数据 JSON。行为分数只用于发现群体性增持、群体性减持、重复买入、新群体关注和跨党派/跨院收敛等线索，不是收益预测或买卖建议。PTR 不披露完整当前持仓，因此“参与率/披露覆盖率”不能解释为真实组合仓位比例；金额仍保持法定区间。

提供 `--output-md` 时会生成面向分析师阅读的 Markdown 报告，包含执行摘要、各窗口榜单、趋势变化、议员画像、信号解释、数据边界和复核优先级；JSON 仍作为机器可读中间产物。

Markdown 报告会在股票代码旁显示公司/发行人名称，并为重点证券增加所属领域和一句业务概览。已知公司的概览来自本地可审计映射；未收录证券只做名称级粗略归类或明确标注待核验，不用于估值或公司研究结论。

`agent-review` 将待复核候选拆成带原始文本/坐标证据的 JSON 批次，并提供固定的 `approved`、`rejected`、`needs_more_evidence` 决定格式。Agent 输出决定后，可用同一命令的 `--decisions` 和 `--output` 应用；应用仍经过 `ocr-review` 的必填字段、代码、日期、金额区间和重复 ID 校验。
