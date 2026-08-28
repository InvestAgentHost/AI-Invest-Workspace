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

当前快照包含 Pelosi 的 3 份 2026 PTR，以及 Gottheimer、Salazar、Crenshaw 各自当前载入的报告。工具分析的是延迟的交易申报事件，不是全体议员目录，也不是完整实时持仓。补充历史数据时，先将每份报告规范化为同一字段并通过 `--data-file` 加载，再按交易日计算净变动。下一步数据层应接入 House Clerk 全量年度 ZIP、Senate eFD、OCR、增量同步和去重；在此基础上再增加定时报告与告警。
