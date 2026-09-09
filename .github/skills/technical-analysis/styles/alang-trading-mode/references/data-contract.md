# 数据与研究合同

## 数据来源

优先使用 Gangtise API/MCP；每次查询记录接口名称、查询时间、市场、证券代码、频率、时区和是否复权。若当前 MCP/脚本不提供分钟数据，应明确记录 `unavailable`，不得用日线插值伪装分钟行情。

原始响应保存到 `sources/providers/gangtise/alang-trading-mode/<日期>/`，派生表保存到 `data/derived/alang-trading-mode/<日期>/`。不要把供应商输出写入 `.github/skills/`。

## 最低字段

标的行情：`security_code`、`timestamp`、`open`、`high`、`low`、`close`、`volume`、`amount`（字段名可按 MCP 映射，但映射表必须随结果保存）。

板块/指数：`index_code` 或 `sector_code`、时间、收盘、成交额、涨跌幅、成分或口径说明。

交易日志：`signal_time`、`security_code`、`side`、`bucket`（`base`/`t`）、`planned_size`、`trigger`、`invalidation`、`assumed_fill`、`fees`、`slippage`、`status`。

## 时间与前视偏差

- A 股时间统一为 `Asia/Shanghai`；分钟 K 必须保留原始频率和交易时段，午休不填充虚假价格。
- 只用信号发生前已可见的数据计算量能、相对强弱和排名；收盘后报告不得反写盘中决策。
- 复权口径、停牌、涨跌停、成交量不足和缺失时段必须标记；缺失则状态为 `REVIEW`，不能静默丢弃。

## 可选研究代理（不是作者原始参数）

以下仅用于比较不同假设，必须在结果中显式标注：

- 板块相对强弱：过去 N 个交易日板块收益减去基准收益，N 由前测设定。
- 量能确认：当前成交额/过去 M 日同时间或全日均值；阈值由研究者设定并做敏感性分析。
- 强弱轮动：在同一板块候选中按流动性、相对强弱和事件风险排序，不把单日涨幅直接等同于“强”。
- T 收益：分别计算日内、隔日和小波段，扣除双边费用、滑点和无法成交的情形；底仓收益与 T 仓收益分开归因。

## 作者规则与代理参数登记

可直接按语录执行、无需另造数字的规则：日 K 判趋势、15 分钟做 T；MA144 作为牛熊分界；13 个交易日内未过买入底部 K 线高点或跌破波段低点 3% 未收回则止损；T 的观察窗口优先 09:45-10:00 与 14:00-14:30；突破后用突破日收盘价作保护线。

必须登记为 `MODEL_PROXY` 的实现项：

- “放量/缩量”的阈值（例如相对 20 日均量的倍数）；
- “板块强势”的排名窗口和前 N% 截止线；
- 黄线/白线在数据接口中的具体映射；
- 滑点、手续费、涨跌停无法成交和分批成交模型；
- 账户总仓位、单方向上限（语录中的 50%/30%/20%、60%～70%、75%+ 是不同情境示例，不是固定配方）。

## 输出结构

每个交易日输出一条状态记录和一份候选表，至少包含：

1. `market_state`：指数、成交额、风格与证据。
2. `sector_view`：板块阶段、相对强弱、量能判断、失效条件。
3. `candidate_plan`：标的、底仓/T 仓、触发与撤出条件、数据完整性。
4. `review_notes`：执行结果、成本变化、浮盈/已实现盈利、偏差分类。

任何结论若只有叙事而无行情验证，状态保持 `UNVERIFIED`；若只有量价代理而无明确规则对应，标记为 `MODEL_PROXY`。

## `plan_rotation.py` 输入约定

脚本目前使用日线代理生成可回测动作，三份 CSV 至少包含以下列：

- `benchmark_daily.csv`：`date,close,amount`，按日期升序，至少 60 个交易日。
- `sectors_daily.csv`：`date,sector,close,amount,breadth`。`breadth` 为当日板块上涨成分比例，范围应为 0～1。
- `stocks_daily.csv`：`date,symbol,sector,close,amount`；可额外包含 `is_st`、`halted` 供上游过滤。

脚本输出 `market_state.csv`、`sector_rank.csv` 和 `action_plan.csv`。这些动作是默认代理：`BUY_BASE` 只代表市场代理处于突破状态，`BUY_T` 代表反抽状态下的候选方向，`REDUCE_T` 代表不在前四强方向；仍需人工检查 15 分钟触发价、涨跌停和已有持仓后才能进入 `REVIEW`，绝不直接下单。
