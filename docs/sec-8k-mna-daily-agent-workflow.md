---
id: workflow-sec-8k-mna-daily-agent
type: workflow-design
title: SEC 8-K 并购重组事项每日 Agent 工作流
status: implementation-in-progress
as_of: 2026-07-28
workspace: .
---

# SEC 8-K 并购重组事项每日 Agent 工作流

## 1. 方案定位

本方案用于每天检查目标股票名单对应公司的 SEC Form 8-K / 8-K/A 公告，识别其中是否发布了并购、资产处置、业务重组、债务重组或交易终止等事项；若存在相关事项，则保存原始 SEC 文件，调用 LLM 进行有证据约束的事件分析，并生成每日可读报告。

本方案将确定性的元数据查询、候选筛选和状态管理交给 Python，将语义判断交给可切换的 LLM Provider，将每日触发交给 Codex“已安排”或 macOS `launchd`。只有被 Agent 明确判定为并购重组相关的 8-K 才会正式写入 `sources/`；无关和待复核 8-K 均不保存正文。Agent 不直接替代原始数据管道，也不把模型判断当作投资结论。

## 2. 落地路径确认

### 2.1 方案文档

本方案文件：

```text
docs/sec-8k-mna-daily-agent-workflow.md
```

选择 `docs/` 的原因是：这是 Workspace 级的架构和工具使用方案，不是某家公司或某个行业的研究结论。

### 2.2 运行入口和数据路径

```text
data/watchlists/sec_8k_targets.txt       默认股票名单
tools/sec_8k_mna/                         Python 采集、分析和报告工具
sources/providers/sec/8-k/<ticker>/                SEC 原始公告和附件
knowledge/indexes/sec-8k/                去重、运行状态和分类 JSON
research/sec_8k_mna_daily/               每日事件报告
.local/logs/sec8k/                              运行日志
```

默认执行入口规划为：

```text
tools/sec_8k_mna/cli.py daily
```

默认每日任务命令规划为：

```bash
python -m tools.sec_8k_mna.cli daily --lookback-hours 36
```

股票名单路径可通过配置覆盖，但默认使用 `data/watchlists/sec_8k_targets.txt`，避免把业务数据硬编码在工具代码中。

该工具的运行时要求为 Python 3.12。交互运行前应激活 Workspace `.venv`；本机定时任务可以在 Git 之外保存该设备的绝对解释器路径，但 tracked 文档和代码只保存相对约定。

`sources/` 和 `knowledge/` 使用 Workspace 的 `config.yaml` 路径映射。相关公告和状态使用以下逻辑路径，由各机器的配置解析实际数据根目录：

```text
sources/providers/sec/8-k/
knowledge/indexes/sec-8k/
```

工具代码、股票名单和每日报告仍在 AI Invest Workspace 内。其他机器应通过本机 `config.yaml` 决定对应的数据根目录，不应把本机绝对数据盘路径写入代码。

## 3. 目标与范围

### 3.1 本期目标

- 从目标股票名单解析 ticker 和可选 CIK。
- 查询每家公司最近 36 小时内提交的 `8-K` 和 `8-K/A` 元数据。
- 使用 SEC Item、标题和提交描述进行候选初筛，不归档全部 8-K。
- 仅对候选公告临时获取正文及关键附件，用于 LLM 判定。
- 只有 Agent 明确判定为相关的公告才正式保存正文和附件。
- 让 LLM 判断是否为并购重组事项，并返回结构化 JSON。
- 每个正面判断必须包含 SEC 原文证据、原始 URL 和置信度。
- 生成每日 Markdown 报告；没有相关事项时也生成“无相关事项”报告。
- 支持重复运行、失败重试和增量处理。

### 3.2 不在本期范围

- 不自动作出买入、卖出或估值结论。
- 不使用浏览器模拟登录 SEC。
- 不把无关 SEC 公告全文交给模型或写入 Workspace。
- 不自动执行交易或向外部平台发布投资建议。
- 不默认抓取 10-K、10-Q、代理声明、8-K 以外的所有 SEC 表单。
- 不把模型生成的摘要作为原始事实来源。

## 4. 事件定义

### 4.1 需要识别的事项

Agent 应识别以下类型：

| 分类 | 说明 |
| --- | --- |
| `m_and_a` | 收购、合并、业务合并、要约收购、私有化交易 |
| `divestiture` | 出售子公司、业务线、重大资产或处置交易 |
| `operational_restructuring` | 裁员、关停、退出业务、组织重组及相关费用 |
| `capital_structure_restructuring` | 债务重组、资本结构调整、再融资安排 |
| `transaction_termination` | 并购、资产处置或重大协议终止、取消或失败 |
| `not_relevant` | 与并购重组无实质关系的 8-K |
| `needs_review` | 有潜在线索但证据不足，需人工复核 |

### 4.2 交易状态

对相关事件再标注状态：

- `announced`：已公告或已签署协议，尚未完成。
- `completed`：已完成收购、出售或合并交割。
- `terminated`：协议终止、交易取消或未获批准。
- `ongoing`：交易或重组正在执行。
- `uncertain`：原文不能确认状态。

## 5. SEC 采集策略

### 5.1 数据源

使用 SEC EDGAR 公开接口和 Archives 文件：

```text
公司 ticker / CIK 映射：SEC company tickers 数据
公司提交记录：data.sec.gov/submissions/CIK##########.json
原始提交索引：www.sec.gov/Archives/edgar/data/...
```

每次请求必须携带清晰的 `User-Agent`，包含应用名称和联系邮箱，并遵守 SEC 的请求频率限制。遇到 403、429 或网络错误时采用退避重试，不绕过限制。

### 5.2 只归档相关公告

每日任务首先只读取 SEC submissions 元数据中的 `form、filingDate、acceptanceDateTime、items、primaryDocument、primaryDocDescription、accessionNumber`。这一步不会把 8-K 正文写入 `sources/`。

只有满足以下条件之一时，才临时获取主文档或附件进行判断：

- Item 命中并购重组相关项；
- `primaryDocDescription` 或提交元数据命中候选关键词；
- 同一 accession 尚未判定，且需要补充正文证据。

候选正文和附件可以在内存或受控临时目录中短暂存在，但不进入 `sources/`。LLM 返回结果后：

- `high_confidence`：保存原文、关键附件和分类 JSON；
- `needs_review`：只保留 accession、SEC URL、提交元数据和分类 JSON，删除临时正文和附件，不写入 `sources/`；
- `not_relevant`：删除临时正文和附件，只保留最小化的 accession、判定状态、时间和错误信息；
- 获取或分析失败：不伪造结论，保留重试所需的 accession 和失败状态，不保存无关原文。

因此，`sources/providers/sec/8-k/` 只包含 Agent 已明确判定为并购重组相关的 8-K，不包含当天所有 8-K 的镜像，也不包含待复核公告正文。

### 5.3 股票名单格式

默认文件：

```text
data/watchlists/sec_8k_targets.txt
```

最小格式为每行一个 ticker：

```text
# US listed companies to monitor
AAPL
MSFT
NOK
```

后续可扩展为 CSV，支持 `ticker、company_name、cik、exchange、enabled` 字段。若 CIK 已知，应优先使用明确 CIK，避免同名公司或 ticker 映射变化造成误抓。

### 5.4 时间窗口

默认使用最近 36 小时窗口，而不是只筛选本地日历日期。原因是 Workspace 位于 Asia/Shanghai，美国提交时间与中国日期存在时差，且部分公告会在美国交易日收盘后提交。

报告日期使用 Workspace 本地时区 `Asia/Shanghai`，同时保留 SEC 的 `filingDate` 和 `acceptanceDateTime`。每条公告的事实时间以 SEC 元数据为准。

### 5.5 候选初筛

优先筛选以下 SEC Item：

| Item | 初筛含义 |
| --- | --- |
| `1.01` | 重大确定性协议，常见并购、合资和重组协议 |
| `1.02` | 重大协议终止，可能是并购失败或交易取消 |
| `2.01` | 完成资产收购或处置 |
| `2.05` | 退出、关停、裁员及重组成本 |
| `8.01` | 其他重大事项，可能包含交易公告 |
| `9.01` | 附件和财务信息，常包含交易协议或新闻稿 |

辅助关键词包括：

```text
merger
acquisition
business combination
tender offer
definitive agreement
agreement and plan of merger
divestiture
sale of assets
restructuring
reorganization
strategic alternatives
change of control
```

关键词只能用于候选扩大和排序，不能单独决定分类。

### 5.6 附件策略

命中候选后临时获取主文档和相关附件，优先包括：

- `Exhibit 2.1`：合并协议或收购协议。
- `Exhibit 2.2`：资产出售或交易协议。
- `Exhibit 10.1`：重大交易协议。
- `Exhibit 99.1`：交易公告、新闻稿和投资者说明。

只有分类结果为 `high_confidence` 时，才将原始 HTML、附件和标准化 Markdown 写入 `sources/`，并保留 SEC URL。`needs_review` 只进入索引和日报，不写入原始来源目录。标准化过程不得覆盖原始下载内容。

## 6. Python 工具设计

建议模块结构：

```text
tools/sec_8k_mna/
  __init__.py
  cli.py                    命令行入口
  config.py                 路径、时区和环境配置
  watchlist.py              股票名单和 ticker/CIK 解析
  sec_client.py             SEC API、限速和重试
  candidate_filter.py       Item、关键词和提交元数据初筛
  filing_inspector.py       候选正文/附件临时获取和清理
  archive.py                仅归档相关公告和附件
  classifier.py             Provider 路由、LLM 调用和 JSON 校验
  report.py                 每日报告生成
  state.py                  accession 去重和失败状态
  tests/
```

执行命令规划：

```bash
# 只检查候选元数据，不下载正文、不调用 LLM
python -m tools.sec_8k_mna.cli candidates --lookback-hours 36

# 一次性执行完整流程
python -m tools.sec_8k_mna.cli daily --lookback-hours 36

# 验证 SEC 候选与配置，不写入文件、不调用 LLM
python -m tools.sec_8k_mna.cli daily --lookback-hours 36 --dry-run
```

Python 进程应采用部分成功策略：某一个 ticker、公告或 LLM 请求失败时，记录错误并继续处理其他对象；候选正文只有在分类为明确相关后才正式归档。临时文件必须在成功判定为无关、待复核或最终失败后清理。

## 7. LLM Agent 分析设计

### 7.1 Provider 抽象

LLM 层必须与 SEC 采集层解耦，通过统一接口调用不同 Provider：

```python
class LLMProvider:
    def classify_filing(self, *, metadata, documents) -> dict:
        """Return schema-validated event classification."""
```

首期支持两个 Provider：

| Provider | 用途 | 接入方式 |
| --- | --- | --- |
| `deepseek` | 直连 DeepSeek API | 使用 DeepSeek API 的兼容接口、独立 API key 和可配置 model |
| `aigocode` | 通过 Aigocode 中转接入 GPT | 使用 Aigocode 的 OpenAI-compatible base URL、API key 和 GPT model |

Provider 选择通过配置或环境变量完成，不能把 Provider、模型和 endpoint 硬编码在业务逻辑中。每次分类结果记录 `provider、model、prompt_version`，不记录 API key。

### 7.2 Provider 配置

建议使用未提交的本地环境变量或 `.env`，并提供不含密钥的示例配置：

```text
SEC_USER_AGENT=AI-Invest-SEC8K/1.0 contact@example.com

LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=

AIGOCODE_API_KEY=
AIGOCODE_BASE_URL=
AIGOCODE_MODEL=
```

其中 `AIGOCODE_BASE_URL` 和 `AIGOCODE_MODEL` 按 Aigocode 账户及其 OpenAI-compatible 文档配置，不在代码中猜测或固定。两种 Provider 都应通过统一的 Chat Completions-compatible 请求适配器发送消息和 JSON schema；如果某个 Provider 对结构化输出参数支持不同，差异只允许存在于 Provider adapter 内。

Provider 文档：

- [DeepSeek API 文档](https://api-docs.deepseek.com/zh-cn/api/deepseek-api)
- [Aigocode OpenAI-compatible API 文档](https://docs.aigocode.com/docs/api/openai-compatible)

默认不自动在两个 Provider 之间切换，以免同一公告得到不一致结果。可以配置显式的失败备用顺序，例如 `deepseek -> aigocode`，但每次切换必须写入日志和分类元数据。

### 7.3 输入

发送给 LLM 的内容应包含：

- ticker、公司名称、CIK。
- SEC form、Item、filing date、acceptance time。
- 主文档正文。
- 相关 Exhibit 的正文或提取文本。
- SEC 原始 URL 和本地来源路径。

仅将确定性筛选后的候选提交给选定 Provider，避免将明显无关公告送入模型。候选中最终被判定为无关的 8-K 会在分析后清理，不会归档保存。

### 7.4 约束提示

Agent 必须遵守：

- 只能根据提供的 SEC 文本判断。
- 不得凭标题推测交易性质。
- 不得编造交易金额、交易对手或完成日期。
- 每个 `is_relevant=true` 或 `needs_review` 判断必须引用原文。
- 无法确认时使用 `uncertain`，并列出缺失信息。
- 将原文事实和模型推断分开。
- 只返回符合 schema 的 JSON，不返回自由格式长文。

### 7.5 结构化输出

建议 schema：

```json
{
  "is_relevant": true,
  "review_status": "high_confidence",
  "category": ["m_and_a"],
  "transaction_type": "merger",
  "status": "announced",
  "company": "Example Corp",
  "counterparties": ["Target Corp"],
  "target_or_asset": "Target Corp",
  "consideration": {
    "summary": "cash and stock",
    "amount": null,
    "currency": null,
    "source_confirmed": false
  },
  "sec_items": ["1.01", "8.01", "9.01"],
  "effective_date": null,
  "evidence": [
    {
      "quote": "...",
      "section": "Item 1.01",
      "source_url": "https://www.sec.gov/Archives/..."
    }
  ],
  "confidence": 0.96,
  "uncertainties": []
}
```

程序必须在写入前校验 JSON schema。模型返回无效 JSON 时重试；多次失败后将该候选标记为 `analysis_failed`，清理临时正文和附件，不将未确认的公告写入 `sources/`。

## 8. 文件和状态契约

### 8.1 相关公告原文

只有 `high_confidence` 的公告允许写入以下路径：

```text
sources/providers/sec/8-k/<ticker>/<filing_date>_<accession>.md
```

Frontmatter 至少包含：

```yaml
type: sec-filing
form: 8-K
ticker: NOK
cik: "0000891480"
filing_date: 2026-07-28
acceptance_datetime: 2026-07-28T15:30:00.000Z
accession_number: 0000000000-26-000001
sec_url: https://www.sec.gov/Archives/edgar/data/...
retrieved_at: 2026-07-28T...
content_sha256: ...
```

### 8.2 分类结果

规划路径：

```text
knowledge/indexes/sec-8k/classifications/<accession>.json
```

该文件是可重建的模型产物，必须记录：

- source path（仅对已归档的相关公告）；
- source content hash；
- model 和 prompt version；
- generated_at；
- 完整结构化分类结果。

### 8.3 运行状态

规划路径：

```text
knowledge/indexes/sec-8k/state.json
```

状态按 accession number 记录，不使用标题作为唯一键。状态可以记录所有已检查 accession，但不保存无关公告正文。至少包含：

```json
{
  "schema_version": 1,
  "last_success_at": "2026-07-28T00:00:00Z",
  "processed": {
    "0000000000-26-000001": {
      "source_hash": "...",
      "classification_status": "completed",
      "updated_at": "2026-07-28T..."
    }
  }
}
```

## 9. 每日报告

规划路径：

```text
research/sec_8k_mna_daily/YYYY-MM-DD.md
```

报告结构：

```markdown
# SEC 8-K 并购重组事项日报 - 2026-07-28

## 执行信息

- 覆盖股票数量：
- 查询窗口：
- SEC 元数据中发现的新增 8-K 数量：
- 候选公告数量：
- 正式归档公告数量：
- LLM 分析数量：
- 失败数量：

## 高置信度并购或重组事项

## 待人工复核事项

## 交易终止或失败事项

## 经营性重组事项

## 无关公告统计

## 来源与证据
```

每个事件至少列出 ticker、事件类型、状态、交易对手、对价或重组费用、SEC Item、证据摘录、原始 URL，以及在已归档时的本地来源路径。没有正面事项时仍生成日报，并明确写出“本窗口内未发现高置信度并购重组事项”；此时不应创建任何无关 8-K 原文文件。

## 10. 每日调度

### 10.1 首选：Codex“已安排”

在当前 Workspace 创建每日重复任务，执行环境选择本地项目，计划时间默认设为每天 07:30（Asia/Shanghai）。任务提示应要求 Agent 运行脚本，而不是让 Agent 每天重新设计采集逻辑：

```text
在当前 AI Invest Workspace 的本地环境中运行：

python -m tools.sec_8k_mna.cli daily --lookback-hours 36

读取并执行当前工作流，不要直接凭模型记忆判断 SEC 事项。
完成后报告：覆盖的 ticker 数量、新增 8-K 数量、高置信度并购重组事项、待人工复核事项、失败数量，以及日报文件路径。
如果脚本失败，报告错误和日志路径，不要编造事件。
```

前置条件：

- 定时任务必须绑定当前 Workspace 项目。
- 本地执行环境需要访问 SEC 网络。
- `SEC_USER_AGENT` 和 LLM API key 必须在定时任务环境中可读取。
- 日志目录和目标目录需要可写。
- 先用一次短延时测试任务验证权限、网络和密钥，再启用每日任务。

### 10.2 备用：macOS `launchd`

如果“已安排”受本地睡眠、权限或产品环境影响，可以使用 `launchd` 直接运行同一条 Python 命令。两种调度器不应同时启用生产任务，避免重复调用；备用调度器应先保持停用。

## 11. 可靠性和安全性

- 所有外部请求设置超时、指数退避和最大重试次数。
- SEC 429/403 不能通过提高并发或切换来源绕过。
- 使用锁文件或进程锁，防止两个每日任务并行处理同一窗口。
- 原始文件写入采用临时文件加原子替换，避免半成品。
- 已经确认相关并完成归档的 SEC 原文，即使后续摘要失败也必须保留并进入待重试队列；无关和待复核候选的临时正文不得进入 `sources/`。
- LLM 摘要失败不影响下一只股票处理。
- API key 只从环境变量或本地未跟踪配置读取，不写入代码、Markdown、日志和定时任务提示。
- 不提交凭据、浏览器 profile、日志、state 和大型生成数据库。
- 生成的分类和日报必须能通过来源路径追溯到 SEC 原文。

## 12. 测试和验收标准

### 12.1 自动化测试

至少覆盖：

1. ticker 到 CIK 的解析。
2. `8-K` 和 `8-K/A` 过滤。
3. 36 小时窗口和时区转换。
4. Item 1.01、2.01、2.05、8.01、9.01 的识别。
5. accession number 幂等去重。
6. merger、asset sale、operational restructuring 和无关 8-K fixture。
7. LLM 无效 JSON、超时和空证据处理。
8. DeepSeek 和 Aigocode Provider adapter 的请求、鉴权错误、超时和 schema 解析测试。
9. SEC 单个 ticker 失败时其他 ticker 仍能完成。
10. 无相关事项时仍生成日报，且不生成无关 8-K 原文文件。

### 12.2 上线验收

- 手动执行一次完整流程成功。
- 使用一个 ticker 的 live smoke test 能保存 SEC 原文和 URL。
- 同一命令连续运行两次不会重复下载或重复调用 LLM。
- 正面事件的 JSON 必须包含证据摘录和 source URL。
- 运行失败时日志明确；已归档的相关原文不丢失，未分类的无关候选不落盘，任务不会假报成功。
- Codex“已安排”测试任务能在目标 Workspace 生成测试日报。
- 完成一次人工核对，确认模型结论与 SEC 原文一致。

## 13. 实施顺序

### Phase 1：确定性采集

- 创建 `data/watchlists/sec_8k_targets.txt`。
- 实现 SEC client、CIK 解析、36 小时查询和 accession 去重。
- 实现候选正文和附件的临时获取、清理，以及仅对明确相关公告的原文归档。
- 完成 fixture 测试。

### Phase 2：候选筛选和 LLM 分类

- 实现 Item、关键词和 Exhibit 初筛。
- 实现严格 JSON schema 和 evidence 校验。
- 保存分类结果和 prompt/model 版本。
- 对高置信度、待复核和无关事项分类。

### Phase 3：日报和调度

- 生成 `research/sec_8k_mna_daily/` 日报。
- 在 Codex“已安排”中设置本地每日任务。
- 完成短周期测试和失败重试验证。

### Phase 4：通知和维护

- 根据需要增加邮件、Slack 或 Codex 任务结果通知。
- 增加历史回填和手动重跑命令。
- 定期检查 SEC schema、LLM prompt 和模型版本变化。

## 14. 未决配置

本方案已给出默认路径，但正式实施前需要固定以下配置：

- 股票名单是否使用默认路径 `data/watchlists/sec_8k_targets.txt`。
- 每日运行时间是否为 07:30（Asia/Shanghai）。
- 默认 LLM Provider 是 `deepseek` 还是 `aigocode`。
- LLM 使用的实际 model ID；DeepSeek 和 Aigocode 可分别配置。
- DeepSeek API endpoint 和 Aigocode OpenAI-compatible base URL。
- SEC User-Agent 中使用的联系邮箱。
- 仅在 Codex 中报告，还是同时发送邮件或 Slack。
- 是否抓取 8-K 的全部附件，还是只保存 2.x、10.x、99.x 附件。
