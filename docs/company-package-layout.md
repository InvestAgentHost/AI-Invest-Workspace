# 公司研究资料包目录规范

本规范适用于所有公司，不预设行业、商业模式或估值方法。公司 ID 使用稳定的 ASCII 形式：`<TICKER>-<slug>`，市场使用 `US`、`CN` 等交易市场标识。

## 目录层级

```text
sources/companies/<market>/<company-id>/
├── inbox/                  # 已确认归档前的原始资料收件区
├── sec/                    # SEC/交易所申报和公告
├── ir/                     # 公司 IR、演示、投资者日
├── transcripts/            # 业绩会和会议纪要
├── sellside/               # 外部机构研报
└── user-provided/          # 用户上传的原始 Word/PDF/Excel

research/companies/<market>/<company-id>/
├── data/
│   ├── inbox/              # 用户研究期间的便利收件区
│   ├── context/            # 研究上下文、报告索引和资料用途
│   ├── evidence/           # 来源和证据台账
│   ├── valuation/          # 估值决策和参数更新记录
│   └── monitoring/         # 后续实际-预测差异和跟踪记录
└── outputs/
    ├── reports/            # 研究报告交付版本
    ├── workbooks/          # 当前底稿/模型
    └── valuation-snapshots/ # 按估值日保留的完整工作簿快照

data/curated/companies/<market>/<company-id>/
├── financials/
├── operating/
└── valuation/              # Agent 接管所需的已采用结构化参数

data/derived/companies/<market>/<company-id>/
├── financials/
├── operating/
└── valuation/<as-of>/      # 可重建计算结果和校验结果
```

## 收件与归档原则

用户可以直接把资料放进 `research/.../data/`，不必预先分类。研究期间 Agent 原地读取，不移动、重命名或覆盖。研究交付时生成归档计划，列出文件、哈希、建议目标路径、已知引用和风险，并询问用户。

只有用户确认后才执行归档。归档使用哈希比较，拒绝覆盖同名异内容文件；移动前更新来源索引或保留兼容指针。未确认的原始资料仍留在收件区。

Word 研究报告有两种身份：用户上传的原报告属于 `sources/.../user-provided/`，用于恢复研究上下文；Agent 生成的交付报告属于 `research/.../outputs/reports/`。报告不能替代 SEC/公司披露作为历史实际数据来源。

## 可维护性要求

- `research/data/context/context-pack.md` 记录报告、底稿和关键资料的用途、日期与哈希。
- `data/curated/.../valuation/handoff.json` 是 Agent 接管入口；`adopted-inputs.json` 保存已采用参数。
- `research/data/valuation/` 保存人类可读的决策和更新日志。
- `data/derived/.../valuation/<as-of>/` 保存每次计算、偏差和校验结果。
- `outputs/valuation-snapshots/<as-of>/` 保存用户可打开的完整 Excel 版本。
- 原始文件不覆盖；同名新版本使用日期、披露期或稳定后缀。

## 工具入口

初始化新公司：

```text
.venv/bin/python .github/skills/company-deep-investment-research/scripts/init_company_research.py \
  --workspace-root . --issuer "Issuer" --ticker TICKER --market US --slug issuer
```

生成待确认归档计划（只读）：

```text
.venv/bin/python .github/skills/company-deep-investment-research/scripts/archive_company_materials.py \
  --workspace-root . --market US --company-id TICKER-issuer
```

执行归档必须显式提供用户确认后的 mapping 文件和 `--apply`；脚本没有默认移动或删除行为。
