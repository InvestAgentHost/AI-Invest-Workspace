使用 `$company-deep-investment-research` 重建【公司名 / ticker / 市场】的多年财务时序表。

## 默认含义

除非我另行指定，按最近五个已审计财年加最新 10-Q 执行；默认重建：

- 合并利润表、资产负债表、现金流量表；
- 关键 Note 表格：债务、租赁、养老金、商誉/无形资产、存货、应收/应付、分部、所得税和股东权益；
- 原始披露表格、标准化年度序列、映射台账、重述/重分类桥和验证结果。

## 语言快捷指令

以下说法应直接路由到本提示词：

- “重建【公司】最近五年三表时序数据。”
- “把【公司】的债务、养老金和商誉 Note 跨年拼起来。”
- “只提取原始报表和 Note 表格，不做估值。”
- “重跑财务时序并检查重述、单位、符号和三表勾稽。”
- “在已有数据基础上补齐缺失年份，并保留原始值。”

若用户指定了财年、报表或 Note 范围，以用户指定为准；若只指定“财务数据”，先采用上述默认范围。

## 执行要求

1. 先确认公司身份、CIK、财年结束日、会计准则、报告货币、单位、合并范围、历史窗口和当前已有来源。缺少身份或窗口时，只提出最小必要确认，不开始猜测。
2. 检查 `sources/companies/<market>/<company-id>/sec/` 是否已有对应 10-K/10-Q。缺失时使用 bundled ResearchFoundry 的 SEC HTML 流程获取；保留原始 HTML，不覆盖同名文件。
3. 对每份 filing 建立或读取表格索引，定位报表和 Note 表格。保留报表原始行序、列标题、期间、单位、空白与零、括号负号、脚注标记、续表关系及来源定位。
4. 先输出逐 filing 的原始表格，再建立标准化字段。标准化不能只靠标签相似度，必须结合表头、报表上下文、脚注、合计公式和 XBRL/Note 证据。
5. 对每个标准化字段写入来源元数据：`source_id`、filing/accession、财年或期间、原始标签、单位、转换、状态、行号/页码定位、置信度和可比性说明。
6. 生成跨年 mapping ledger。遇到重述、重分类、行名变化、单位变化、符号变化、终止经营、分部变更或合并范围变化时，保留原始值并生成 `restatement_bridge`，不得静默覆盖。
7. 执行验证：资产 = 负债 + 权益、现金流量表现金桥、净利润与归母/NCI、Note 与主表、分部与合并收入/利润、期初期末余额和跨年期间一致性。不能可靠验证的项目标记 `unavailable` 并记录原因。
8. 使用 Workspace 财务计算器的 `--strict` 模式生成可审计派生指标；任何 APM、公司自定义口径和分析推导均与 GAAP/IFRS 原始值分开。

## 交付物

在 `data/curated/companies/<market>/<company-id>/` 下生成或更新：

```text
raw_statements/<statement>.csv
raw_notes/<note>.csv
statement_mapping_ledger.csv
note_mapping_ledger.csv
restatement_bridge.csv
financial_timeseries.csv
financial_metrics_input_strict.json
financial_reconstruction_validation.json
```

同时更新研究包中的证据台账、覆盖矩阵、采集记录和验证日志。所有 CSV/JSON 必须可解析；所有表格必须能回溯到本地来源和精确定位。

## 输出边界

先报告：来源覆盖、已重建表格、缺失表格、重述/口径冲突、验证结果和 `PASS`/`PARTIAL` 状态，再给出时序数据路径。不要把 Company Facts 的单一标签序列冒充完整 Note 表格；不要把未披露、空白和零混为一谈；不要为了通过勾稽而填补或猜测数据。

