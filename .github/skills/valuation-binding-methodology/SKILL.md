---
name: valuation-binding-methodology
description: Build or update Profit Forecast and Valuation Model worksheets when company research asks for earnings forecasts (作出盈利预测), a DCF model (搭建DCF模型), or a valuation refresh. Use fiscal-year operating drivers and the analyst-approved cash-dividend plus exit-P/FCF model, with three saved cases, cash/share checks and an editable-workbook handoff.
---

# 盈利预测与估值模型

本 skill 执行 [公司深度投研估值模块](../company-deep-investment-research/references/valuation-and-shareholder-return.md)，统一维护两表布局、计算和更新规范。历史实际数据归 [company-research-to-excel](../company-research-to-excel/SKILL.md)；平台 spreadsheet 能力操作文件。新旧 sheet 共用历史底稿的 [style-profile.json](../company-research-to-excel/assets/style-profile.json)。

## 入口与范围

- “作出盈利预测”创建或更新 `Profit Forecast`。只要求预测时交付逐年利润、CAGR 和估值接口即可。
- “搭建DCF模型” / “进入估值环节”复用或补齐预测，交付 `Profit Forecast` 与 `Valuation Model`，包含悲观、基准、乐观三情景。
- “更新预测/估值”先读 [tracking-contract.md](references/tracking-contract.md)，保留最新 Excel 的手动输入与已采用决定。
- 核查默认只读；修复依用户授权执行。本 skill 不授权交易、外发或后台调度。

## 统一方法

自 2026-10-30 起采用 `dividend-pfcf-net-shares-v3`，来自用户上传估值 Excel 及已认可的 PEP 实施：**现金分红现值＋第五年退出 P/FCF 股权价值现值**。正式标注“股东现金流折现：分红＋退出 P/FCF”，不能把它称作标准永续 FCFF/FCFE DCF。

公式、日期、转换率与股数符号仅维护于 [model-contract.md](references/model-contract.md)，旧方法只保留该文件中的迁移说明。用户明确指定不同方法时遵从；本口径不适用时说明原因及建议，不静默换模型，不强造正利润。其他方法不作为并行默认模板维护。

## 执行

1. 恢复现有研究、最新实际期、财年、币种/单位、估值日和利润口径；先识别人工修改，不从过期参数重建覆盖。
2. 读 [research-workflow.md](references/research-workflow.md)：按披露频率形成完整基年，依公司经济机制选择预测单元、指标和驱动，推导未来五年，每年单列；五年后给长期参考。先年度路径后 CAGR。
3. 读 [workbook-contract.md](references/workbook-contract.md)：同指标历史数值在预测右侧；一套经营预测配三情景利润快照及可恢复驱动，保持当前实时路径与已保存情景清楚分离。共同基础变化后刷新全部情景。
4. 按 model contract 计算股数、股息、FCF 与退出价值，核查分红/回购覆盖及完整资金用途；资料不全不得宣称资金闭环。
5. 在底稿内写使用方法和实际单元格映射，核验公式、参数扰动、快照捕获/恢复、过期提示与中文版面。完整估值交付两表；保留未涉及数据与原生功能。
6. 复用现有台账交接，记录采用输入、情景版本、证据及限制，详见 tracking contract；不额外堆叠同类记录。

## 核验与交付

通过 Workspace `.venv` 运行：

```text
.venv/bin/python .github/skills/valuation-binding-methodology/scripts/valuation_checks.py calculate <one-case-input.json>
.venv/bin/python .github/skills/valuation-binding-methodology/scripts/valuation_checks.py validate <handoff.json>
.venv/bin/python -m unittest discover -s .github/skills/valuation-binding-methodology/scripts -p 'test_*.py'
```

`calculate` 只实现本次 P/FCF 方法，逐情景独立复算；旧方法输入拒算，不自动转换。`validate` 检查接管记录、情景和右侧历史映射，不能代替来源与实际 Excel 检查。字段骨架见 [handoff-template.json](assets/handoff-template.json)。

交付说明日期、基期、方法、利润口径、假设依据、三情景结果、敏感性和未决问题。`PASS` 须证据、计算、相关现金约束及版面通过；重要缺项为 `PARTIAL`，使结果不成立的口径/输入缺失为 `BLOCKED`。参考公司的分部、参数和结论不成为新公司的默认值。
