# 自选股股票池 API（Open API · stock-pool）

## 简介

通过 Gangtise Open API 读取终端**自选股股票池**列表及池内证券明细。脚本 **`scripts/stockpool.py`**。

- **getPoolList**：当前用户全部股票池 `poolId` / `poolName`（**不消耗积分**）。
- **getStockList**：按 `poolIdList` 取 `securityCode` / `securityName`（**不消耗积分**）；`["all"]` 为全部池合并去重证券。

## 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `-m` / `--mode` | 否 | `search` \| `get`（默认 `search`）。 |
| `-k` / `--keyword` | 否 | 股票池名称或 ID 子串过滤（`search`）。 |
| `-l` / `--limit` | 否 | `search` 列出/过滤的股票池数量上限（默认 100）。 |
| `--pool` | 视模式 | 池 ID 或名称，逗号分隔。仅字母数字与逗号时视为 ID 直接 `get`；否则 `search`，**唯一完全匹配**时自动 `get`。 |
| `--pool-file` | 视模式 | CSV 含 `pool_id` 或 `poolId`（提供后自动 `get`）。 |
| `--all` | 否 | `get` 使用 `poolIdList=["all"]`（提供后自动 `get`）。 |

\* `mode=get` 时须 `--pool`、`--pool-file` 或 `--all` 之一。

## 模式说明

| 模式 | 接口 | 说明 |
|------|------|------|
| `search` | getPoolList | 列股票池，可 `-k` 过滤（默认）。 |
| `get` | getStockList | 按 ID 或 `--all` 取证券；提供 ID/名称参数时自动进入。 |

## 调用示例

```bash
python3 scripts/stockpool.py -m search
```

```bash
python3 scripts/stockpool.py -m search -k 自选股 -l 20
```

```bash
python3 scripts/stockpool.py --pool 808477293,808477294
```

```bash
python3 scripts/stockpool.py --pool 自选股
```

```bash
python3 scripts/stockpool.py --all
```

## 返回说明

- **成功**：CSV 写入 `workspace/gangtise/stockpool/`（`stockpool_pools_*.csv`、`stockpool_stocks_*.csv`）。
- **列**：`pool_id`, `pool_name`；`security_code`, `security_name`（多池已按代码去重）。
- **search 成功**：消息末尾提示可通过 `--pool-file` 读取 CSV 再 `get`。
- **失败**：未授权、无股票池、无匹配、池内无证券等。

## 与 gangtise-data 衔接

将 `stockpool_stocks_*.csv` 的 `security_code` 列传给 `gangtise-data` 的 `--securities-file` 拉行情、财务等。
