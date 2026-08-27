使用 `$company-deep-investment-research` 为【公司名 / ticker】执行阶段 4 五年财务重建。若目标是快速重建或补齐时序表格，也可以直接使用 `prompts/04-financial-series-reconstruction.zh-CN.md` 的语言快捷指令。

默认覆盖 FY2021-FY2025，并补充最新 10-Q。先呈现合并利润表、资产负债表、现金流量表原始口径，再建立标准化输入、映射台账、重述/重分类桥、分部桥和 APM 桥。优先使用 Workspace 财务计算器并运行 strict；显示利润率、回报率、流动性、杠杆、营运资本、现金转换和资本强度表。

缺少可靠来源或分母时使用 unavailable/not meaningful，不得把空白变成零。每个重大变动都要给出报表事实、机械桥、经济驱动、持续性判断、投资含义和监测指标。
