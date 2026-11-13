---
name: valuation-binding-methodology
description: Build or update Profit Forecast and Valuation Model worksheets for earnings forecasts, a DCF model, or a valuation refresh. Use issuer-specific fiscal drivers, one live three-case selector, dividends and next-fiscal-year forward P/FCF at exit, with cash/share checks and an editable workbook.
---

# 盈利预测与估值模型

本 skill 执行 [公司深度投研估值模块](../company-deep-investment-research/references/valuation-and-shareholder-return.md)，维护两表布局、计算和更新规范。新建模型从 [GGG 版式通用模板](assets/forecast-valuation-template.xlsx) 起步。历史实际数据复用 [company-research-to-excel](../company-research-to-excel/SKILL.md) 的核验底稿。

## 入口与范围

- “作出盈利预测”创建或更新 `Profit Forecast`。只要求预测时交付逐年利润、CAGR 和估值接口即可。
- “搭建DCF模型” / “进入估值环节”复用或补齐预测，交付 `Profit Forecast` 与 `Valuation Model`，包含悲观、基准、乐观三情景。
- “更新预测/估值”先读 [tracking-contract.md](references/tracking-contract.md)，保留最新 Excel 的手动输入与已采用决定。
- 核查默认只读；修复依用户授权执行。本 skill 不授权交易、外发或后台调度。

## 统一方法

采用 `dividend-forward-pfcf-net-shares-v4`，正式标注“股东现金流折现（分红＋次年远期 P/FCF）”。退出价值采用退出次年可比 FCF，并按退出日期折现。

公式、日期、转换率与股数符号仅维护于 [model-contract.md](references/model-contract.md)，旧方法只保留该文件中的迁移说明。用户明确指定不同方法时遵从；本口径不适用时说明原因及建议，不静默换模型，不强造正利润。其他方法不作为并行默认模板维护。

## 执行

1. 恢复现有研究、最新实际期、财年、币种/单位、估值日和利润口径；先识别人工修改，不从过期参数重建覆盖。
2. 按 [research-workflow.md](references/research-workflow.md) 形成完整基年，选择公司经营驱动，推导持有期逐年利润及退出次年 FCF。先建年度路径再算 CAGR。
3. 按 [workbook-contract.md](references/workbook-contract.md) 将可比历史放在预测右侧。一个下拉框联动两页，三档分别维护可编辑假设。共享输入变化后复算三档，版本记录存工作簿外。
4. 按 model contract 计算股数、股息、FCF 与退出价值，核查分红/回购覆盖及完整资金用途；资料不全不得宣称资金闭环。
5. 写明实际输入单元格，核验三情景、分红现值、退出价、XIRR、敏感性和资金约束。按 [交付清理](references/workbook-contract.md#交付清理) 检查最终保存文件。保留既有底稿中未涉及的数据和功能。
6. 复用现有台账交接，记录采用输入、情景版本、证据及限制，详见 tracking contract；不额外堆叠同类记录。

## 核验与交付

通过 Workspace `.venv` 运行：

```text
.venv/bin/python .github/skills/valuation-binding-methodology/scripts/valuation_checks.py calculate <one-case-input.json>
.venv/bin/python .github/skills/valuation-binding-methodology/scripts/valuation_checks.py validate <handoff.json>
.venv/bin/python .github/skills/valuation-binding-methodology/scripts/valuation_checks.py inspect-workbook <delivered.xlsx>
.venv/bin/python -m unittest discover -s .github/skills/valuation-binding-methodology/scripts -p 'test_*.py'
```

`calculate` 只实现本次 P/FCF 方法，逐情景独立复算；旧方法输入拒算，不自动转换。`validate` 检查接管记录、情景和右侧历史映射，不能代替来源与实际 Excel 检查。字段骨架见 [handoff-template.json](assets/handoff-template.json)。

`inspect-workbook` 默认检查文件中已有的两张预测/估值页。单页任务加 `--sheet "Valuation Model"` 或 `--sheet "Profit Forecast"`。检查器定位隐藏行列、快照遗留和已缓存的公式错误，人工核验版面及公式重算。

交付说明日期、基期、方法、利润口径、假设依据、三情景结果、敏感性和未决问题。`PASS` 须证据、计算、相关现金约束及版面通过；重要缺项为 `PARTIAL`，使结果不成立的口径/输入缺失为 `BLOCKED`。参考公司的分部、参数和结论不成为新公司的默认值。
