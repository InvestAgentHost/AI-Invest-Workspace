# Hubbell 覆盖矩阵（阶段 0 及初始 intake）

状态词：`covered`、`partial`、`planned`、`unavailable`、`unresolved`、`n.a.`。阶段 0 只锁定问题和证据路径，不把 planned 当作已覆盖。

| 研究问题 | 当前状态 | 计划证据 | 采集尝试 | 预期限制/影响 |
|---|---|---|---|---|
| 法律实体、市场、会计范围 | covered | S01-S07 | A01,A07 | SEC 身份、CIK、市场、财年和报告实体已确认；合并子公司、NCI、终止经营附注仍需细化 |
| FY2021-FY2025 合并三表 | covered | S01-S05 | A07,A09b | 标准化三表、单位、资产负债表和母公司/NCI 勾稽已通过 strict calculator；2023 FIFO 限制显式记录 |
| 最新 2026 Q2 财务与风险 | covered | S06、S20、S30 | A08,A08b,A15 | 10-Q、8-K 与 Q2 会议纪要已核对；中期未经审计且有季节性，单独存入 operating_current.csv |
| Utility Solutions 边界与经济单元 | partial | S01-S13、S29-S31 | A07,A09,A14,A15 | 分部产品、收入确认、五年利润/资产/capex/backlog 和管理层订单信号已覆盖；产品线利润和客户拆分 unavailable |
| Electrical Solutions 边界与经济单元 | partial | S01-S13、S29-S31 | A07,A09,A14,A15 | 终端市场、渠道、五年利润/资产/capex 和数据中心管理层暴露已覆盖；产品线利润和渠道库存 unavailable |
| Corporate/Other、债务、租赁、养老金、商誉 | partial | S01-S06 | A07,A08 | 债务、养老金、商誉已检查；租赁负债和潜在税项尚未汇总进估值桥 |
| 价格/量/组合、存货、应收、资本开支、现金转换 | partial | S01-S06、S29-S30、结构化数据 | A07-A09b,A14,A15 | 年度与 2026H1 已抽取；会议纪要补充价格/产能/订单主张，完整价格/量桥和渠道库存仍 unavailable |
| 美国电网升级、输配电、变电站和可靠性 | partial | S21-S26 | A10,A10b | DOE/EIA 机制资料已取得；NERC/FERC 入口阻断，可靠性/监管数字待替代来源 |
| 工业/商业电气需求与竞争 | partial | S01、S06、竞品/独立资料 | A09,A12 | 终端应用和竞争因素有公司披露；独立市场份额/价格数据 unavailable |
| AI 数据中心直接产品/收入 | partial | S01-S13、S20-S22、S31 | A09,A11、A15 | SEC 未单列收入；S31 管理层估计 Electrical 约 10% 收入来自数据中心、NSI 约 10%，但期间/产品/客户/毛利不可复核，不能用整个分部/TAM代替 |
| 数据中心负荷增长的电网间接受益 | partial | S21-S23、S29-S31 | A10a,A10b,A15 | DOE/IEA/EIA 与管理层订单/BTM 机制支持；不等于 Hubbell 订单/收入 |
| NERC/FERC 可靠性与输电监管数字 | unresolved | S25-S26 | A10b | 官网安全页阻断；需替代公开报告或继续保留缺口 |
| 建筑、配电、工业电气间接受益 | partial | S01、S21-S23 | A09,A11,A12 | 应用市场机制已覆盖；不可归属收入与订单缺失 |
| 分红、回购、股本和股东 IRR | partial | S01-S06、S17-S18 | A13,A13a | Yahoo 价格及 SEC 股本/回报已入表；第二行情源受阻、稀释股数待补 |
| SOTP/EV/EBITDA/FCF 方法有效性 | partial | S01-S06、S17 + valuation refs | A07,A13a | 分部利润、净债务和双算规则透明；租赁/潜在税项/独立倍数待补 |
| 证据缺口与证伪条件 | covered | 全部台账 | A07-A13a | 缺口、影响、证伪条件和发布状态已记录 |
