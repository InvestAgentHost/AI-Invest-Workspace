---
name: technical-analysis
description: 统一入口的 A 股技术分析工作流，按需路由到狼大趋势轮动或兰斯洛 15 分钟 MA55 承接流派；支持市场状态、板块、个股、T 交易、复盘与历史验证，不自动下单。
---

# A股技术分析总 Skill

本 skill 是技术分析总入口，两套流派的完整子 skill 均在本目录的 `styles/` 下。先尊重用户指定的流派；未指定时按问题选择对应子 skill。不要默认加载全部流派，也不要把不同流派的局部信号自动拼成一套新策略。

目录结构：

```text
technical-analysis/
├── SKILL.md
├── references/routing-matrix.md
└── styles/
    ├── alang-trading-mode/
    │   ├── SKILL.md
    │   ├── references/（含原始 PDF）
    │   └── scripts/
    └── lanselot-ma55-trend-screen/
        ├── SKILL.md
        ├── references/
        └── scripts/
```

任务选择详见 [路由矩阵](references/routing-matrix.md)。

## 子 Skill 路由

### 狼大趋势轮动

路径：[alang-trading-mode](styles/alang-trading-mode/SKILL.md)

适用于：市场见底、反抽/反弹、反弹方向、趋势阶段、仓位、BASE/T、止盈止损、每日复盘和事件应对。涉及这些问题时，读取该子 skill 的相关主题及 [cross-theme-audit.md](styles/alang-trading-mode/references/cross-theme-audit.md)；该审计仅约束狼大流派。

### 兰斯洛 MA55 承接

路径：[lanselot-ma55-trend-screen](styles/lanselot-ma55-trend-screen/SKILL.md)

适用于：已有趋势候选股的 15 分钟 MA55 承接、击穿后的第一根红 K、MA233 压力/T 参考和分钟数据筛选。独立使用时遵循自身的趋势资格和数据合同，不强制先运行狼大模块。

## 联合分析（仅明确要求时）

先分别给出两派结论，标明各自前提和缺失信息。比较不等于组合；只有用户明确要求组合方案时，才可提出以下衔接作为 `MODEL_PROXY`，不能归为任何一派的原始规则。

```text
狼大：市场状态 -> 板块方向 -> 总仓位权限
                    |
兰斯洛：趋势候选 -> 15分钟MA55承接 -> MA233压力/T参考
                    |
组合方案：另定退出、复盘、历史验证
```

组合方案必须另行写明冲突如何处理、采用谁的仓位和退出规则。未完成这些定义时只输出两派各自的观察结果，不生成混合交易指令。

## 共享约束

- 周期、趋势资格、仓位和退出规则归各子 skill 所有，不把某派的状态枚举或均线条件变成所有流派的门槛。
- 原始行情、分钟数据和供应商响应遵守各子 skill 的数据合同，写入 `sources/`；派生结果写入 `data/derived/`。
- 未明确量化的放量、缩量、强势、同步和趋势资格必须标记 `MODEL_PROXY`。
- 任何策略只生成可审计候选或计划，不自动下单；区分原始表述、分析者推断和 `MODEL_PROXY`，不把格式检查当策略有效性验证。
- 原始语料 PDF 随狼大子 skill 保存在 [alang-self-reliance.pdf](styles/alang-trading-mode/references/alang-self-reliance.pdf)。

## 输出模式

每次输出明确标注 `style`：`alang`、`lanselot_ma55` 或 `combined`，并列出使用的子 skill、市场权限、触发条件、失效条件、仓位边界和数据完整性。没有足够数据时不得给出确定性买卖结论。
