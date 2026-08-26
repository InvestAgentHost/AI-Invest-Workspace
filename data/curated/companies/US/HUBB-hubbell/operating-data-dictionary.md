# Hubbell 运营数据字典（初版）

本文件定义后续运营表字段及证据状态。空白表示尚未抽取，不等于零。

| 字段 | 定义/单位 | 适用路由 | 主要来源 | 状态 |
|---|---|---|---|---|
| segment_net_sales | 报告分部净销售额，百万美元 | 两分部 | 10-K/10-Q Note 20/11 | covered（FY2021-FY2025；2026H1见 operating_current.csv） |
| segment_operating_income | 报告分部经营利润，百万美元 | 两分部 | 10-K/10-Q segment tables | covered（FY2021-FY2025；2026H1见 operating_current.csv） |
| organic_sales_growth | 公司 non-GAAP 有机增长，百分比 | 两分部 | MD&A/8-K | partial（年度方向及 2026H1 已披露；完整五年拆分 unavailable） |
| price_volume_mix | 管理层价格、量、组合方向；不自行拆分 | 制造/硬件 | MD&A/电话会 | partial（公司方向性披露；未取得完整电话会桥接） |
| backlog_firm | 期末认为 firm 的 backlog，百万美元 | 项目/制造 | 10-K/10-Q MD&A | partial（FY2024-FY2025；2026Q2 未单独更新） |
| contract_assets_liabilities | 合同资产/负债，百万美元 | 定制/服务 | Revenue note | covered（披露机制；产品级余额不完整） |
| inventory_receivables_payables | 期末营运资本，百万美元 | 制造/分销 | 资产负债表/附注 | covered（五年年末及 2026-06-30 合并余额） |
| segment_capex | 分部资本开支（若披露），百万美元 | 制造 | Segment note | covered（FY2023-FY2025；2026H1） |
| warranty_accrual | 保修计提/实际索赔，百万美元 | 制造 | Commitments/risk note | unavailable（未见可复核的完整系列） |
| data_center_direct_revenue | 明确归属于数据中心的收入 | 数据中心拆分 | 10-K/10-Q/IR/客户资料 | unavailable until checked |
| data_center_grid_indirect | 数据中心负荷推动电网投资的机制证据 | 行业/间接受益 | DOE/IEA/NERC/独立资料 | partial（DOE/IEA/EIA；NERC/FERC 受阻） |
| data_center_building_indirect | 建筑、配电和工业电气间接受益 | 行业/间接受益 | 10-K/独立资料 | partial（应用市场证据；不可归属收入） |
