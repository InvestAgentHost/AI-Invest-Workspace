# Baker Hughes 经营分析底表说明

文件：`data/curated/companies/US/BKR-baker-hughes/operating_timeseries.csv`

## 口径

- 金额单位为百万美元；财年截至 12 月 31 日。
- FY2021-FY2022 的分部经营利润仍是 operating income before tax 口径；FY2023-FY2025 使用 segment EBITDA。本表没有把两种利润口径混在收入字段中，利润比较仍引用 `financial_timeseries.csv` 的 `segment_profit_basis`。
- FY2023 10-K Note 16 将 2021-2022 IET 产品线重述为新产品线结构，因此 2021-2025 产品收入序列采用 FY2023 10-K 的重述比较列；`iet_controls_musd` 单列，因为 Controls 于 2023 年 4 月出售。
- 2021-2025 的 OFSE 产品线收入均为 SEC Note 16/对应比较列；OFSE 订单只在分部层面披露。
- 订单是年度确认的 orders，RPO 是期末剩余履约义务，不等同于未来收入或无条件采购承诺。
- `contract_revenue_excess_assets_musd` 是收入超过开票的合同资产；`contract_deferred_assets_musd` 还包括递延存货成本及履约/取得合同成本；`contract_liabilities_musd` 是 progress collections and deferred income。
- 2021-2022 的分部资产、折旧摊销和资本开支采用当期双分部重述口径；2023-2025 采用最新 10-K 的双分部表。

## 主要来源

| 数据块 | 来源 |
|---|---|
| OFSE/IET 产品线收入、2021-2022 重述 | S03: Note 16, p.84；S02: Note 16, pp.86-87；S01: Note 16, pp.88-92 |
| 订单与 RPO | S04: pp.52-54, 86-89；S03: pp.52-54, 84-90；S02: pp.55-56, 86-91；S01: pp.35-40, 88-92 |
| 合同资产、合同负债 | S05-S01: Note 6-7 |
| 分部资产、D&A、资本开支 | S04: pp.86-89；S03: pp.84-86；S02: pp.90-91；S01: pp.90-93 |

## 不可比与限制

2021 年原始报告仍采用四分部；2022 年起重组为 OFSE/IET。产品线收入可以通过 FY2023 的重述列形成序列，但产品线利润、产品线资产和产品线资本开支没有完整五年披露，因此第三章只在披露范围内进行产品线定量分析，不推导未披露的产品线利润率或 ROIC。2026 年 Chart 交割、PSI 出售和 Cactus 合资属于交易后边界，未混入本表历史数据。
