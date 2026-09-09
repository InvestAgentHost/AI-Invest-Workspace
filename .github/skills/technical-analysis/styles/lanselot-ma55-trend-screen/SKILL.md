---
name: lanselot-ma55-trend-screen
description: 蒸馏并实践兰斯洛t的趋势股 15 分钟 MA55 承接战法，使用人工确认趋势的候选池和分钟 K 线生成可审计候选，不执行交易。适用于 A 股技术选股、复盘与前测；不用于自动下单或把主观趋势判断伪装成量化事实。
---

# 兰斯洛t 15 分钟 MA55 趋势承接

本子 skill 属于 [技术分析总 skill](../../SKILL.md)，可独立选择，不要求先执行其他流派。

## 目的与边界

本 skill 将 NGA 用户兰斯洛t（UID `67142257`）在 2026-09-08 的回复转成可复盘的候选筛选流程。核心并不是全市场机械找金叉，而是：先由分析者确认某标的是有趋势的票，再等待 15 分钟 MA55 附近的承接或击穿后的第一根红 K。

只产出 `REVIEW` 候选、输入数据、参数和规则命中证据。不要自动下单，不要把结果写成投资建议或胜率承诺。作者没有给出“有趋势”的定量定义、统一止损、仓位、滑点或持有期；这些必须保持为空，或在前测方案中单独、明确地设定为分析者假设。

先阅读 [原帖蒸馏与证据边界](references/source-distillation.md) 和 [案例选股审计](references/example-selection-audit.md)。在接入数据或运行筛选前，阅读 [数据与前测合同](references/data-contract.md)。

## 原帖规则

以下是作者明确表达的规则，不添加参数：

1. 前置条件是分析者认为该股有趋势；强趋势可能在触及 15 分钟 MA55 前便反弹。
2. 在 15 分钟 MA55 附近承接；若已击穿，等 MA55 附近的第一根 15 分钟红 K 作为买点。
3. 触及 MA55 后，分时开始转向即可试探性参与；作者个人也可能在该根 15 分钟红 K 走到一半或盘面拐头时参与。这是盘中主观执行，不能从已收盘 K 线无偏复现。
4. 用 15 分钟 MA55 承接的仓位，在上方 15 分钟 MA233 附近做 T、减一部分，除非该笔是加仓。

## 案例中观察到的均线结构（待验证代理）

在雅克科技、德明利的 2026-09-08 图形案例中，用户复核到一种更具体的结构：15 分钟 MA55 向上，MA233 向下；MA233 位于价格上方、接近最高的一组慢速均线，构成反弹压力和 T 位。该结构可以作为候选优先级和历史重放的观察字段，但目前只有少数案例支持，不能升级为作者明确的必要条件。

重放时至少记录：`ma55_slope`、`ma233_slope`、`ma233_above_close`、收盘价距 MA233 的百分比，以及 MA55 上穿/接近 MA233 的状态。分别报告满足和不满足该结构时的结果，检验它是否比单纯“有趋势 + MA55 承接”提供增量信息。

脚本把第 2 条做成收盘后、可审计的 `hold_at_ma55` 与 `break_reclaim_ma55` 候选。它故意不把第 3 条的盘中“红 K 走到一半”标成无偏回测买价。

## 实践流程

1. 建立候选池，而不是对全市场假装扫 15 分钟信号。每个候选必须由分析者填写 `trend_eligible` 和 `trend_note`；日线多头排列、产业逻辑或人工图形判断可以是证据，但不能自动等同于作者的“有趋势”。
2. 从 Gangtise 获取候选的 A 股分钟 K。现有 `gangtise-data` 的 `minute` 仅支持指定 A 股，不支持 `--all-market`。必须通过 Workspace 包装器运行，不直接调用 vendored 脚本：

```bash
.venv/bin/python tools/gangtise/run.py \
  --output-subdir providers/gangtise/lanselot-ma55 \
  data quote.py --type minute --securities 002409.SZ,603986.SH \
  -sd "2026-09-01 09:30:00" -ed "2026-09-09 15:00:00"
```

   使用 Gangtise MCP 时也遵守同一数据合同：保存原始分钟数据到 `sources/providers/gangtise/lanselot-ma55/`，而非 `.github/`；记录数据查询时点、标的、时区与原始频率。港美股不应伪装为此 A 股实现的有效输入。
3. 从原始 CSV 重采样 15 分钟、计算收盘价 SMA55/SMA233，并把候选池人工趋势标签合入。生成文件写入被忽略的 `data/derived/`：

```bash
.venv/bin/python .github/skills/technical-analysis/styles/lanselot-ma55-trend-screen/scripts/screen_15m_ma55.py \
  --minute-csv sources/providers/gangtise/lanselot-ma55/quote_example.csv \
  --candidates-csv data/curated/lanselot-ma55-candidates.csv \
  --output-dir data/derived/lanselot-ma55/2026-09-09
```

4. 审阅每个 `REVIEW`：原始 K 线覆盖是否完整、该标的的趋势理由、MA55 是否真的被触及、是否先有向下击穿、红 K 是否为击穿后的首根确认，以及 MA233 是否位于入场上方。缺少其中任一证据就排除或记录为待人工复核。
5. 前测必须按事件逐笔记录：信号时点、可成交假设、手续费和滑点、减仓规则、失败条件、最高/收盘收益、以及样本外期间。不得引用作者两天、20 只样本的自述为策略有效性证明。

## 输出解释

- `break_reclaim_ma55`：先有收盘落在 MA55 下方，随后在可配置窗口内第一次以红 K 收回并接近 MA55。它是最贴近作者原话的收盘确认代理。
- `hold_at_ma55`：红 K 在 MA55 附近且收于其上，但未观察到待确认的近期击穿；只表示“碰到就弹”的历史形态，不是追涨许可。
- `manual_trend_eligible`：唯一允许从 `REVIEW` 升为 `QUALIFIED_FOR_REVIEW` 的字段，来自候选池人工判断，不由脚本推断。
- `ma233` / `ma233_above_close`：做 T 参考，不是保证目标价；没有完整 233 根 15 分钟 K 时必须显示不可用。

变更触及定义、击穿窗口、趋势代理、出场或执行价时，先复制一次基线参数，在新的输出目录进行前测；不要覆盖旧结果。
