# 采集尝试记录

| ID | 日期 | 研究问题 | 来源类别/路由 | 结果 | 下一步 |
|---|---|---|---|---|---|
| A01 | 2026-08-25 | 五年审计收入、利润、资产和现金流 | 监管/SEC 10-K FY2021-FY2025 | completed；prepared 包均 completed | 以 `document.md` 为权威，semantic index 仅检索 |
| A02 | 2026-08-25 | 产品、技术、战略和发展事件 | 公司官网 snapshot | partial；19 个健康来源，旧入口 404、3 个外链排除 | 后续补 IR/电话会和 2026 更新页面 |
| A03 | 2026-08-25 | BKR.O 市场边界 | Gangtise security/quote | completed；解析 BKR.O，251 交易日，最新 2026-08-24 | 补第二行情源以降低单源风险 |
| A04 | 2026-08-25 | 五年 Gangtise 财务和估值交叉核验 | Gangtise financial/valuation | partial；每表单期，估值未找到数据 | 不作为五年主表/估值倍数，回到 SEC |
| A05 | 2026-08-25 | 油服竞争结构与周期 | SEC Halliburton/SLB 10-K | completed；营收、分部、服务/数字业务可抽取 | 补市场份额和价格数据 |
| A06 | 2026-08-25 | IET 电力/燃机服务竞争 | SEC GE Vernova 10-K | completed；设备/服务收入、RPO、Gas Power 可抽取 | 补严格可比公司倍数 |
| A07 | 2026-08-25 | LNG、天然气和价格背景 | EIA STEO | completed；LNG 出口和 Henry Hub 摘要 | 需要更长历史序列时再取 EIA API |
| A08 | 2026-08-25 | 氢能项目进度及障碍 | IEA Global Hydrogen Review 2025 | completed；>200 个已承诺低排放项目，成本/基础设施/监管障碍 | 补项目级合同证据 |
| A09 | 2026-08-25 | CCUS 价值链和技术用途 | IEA CCUS in Clean Energy Transitions | completed；四类减排/移除应用 | 补政策和项目 FID 数据 |
| A10 | 2026-08-25 | 2026 Q1 经营、订单、现金流和组合动作 | 用户提供的业绩电话会转录 | completed；本地中英双语转录可检索 | 用 2026 Q1 10-Q/业绩公告核对 GAAP 与 APM |
| A11 | 2026-08-25 | 2026 Q2 经营、Chart 交割、指引和协同 | 用户提供的业绩电话会转录 | completed；本地中英双语转录可检索 | 用 2026 Q2 10-Q 核对第三分部、债务和协同实现 |
| A12 | 2026-08-25 | OFSE/IET 业务边界与 Horizon 战略 | 用户提供的 Bernstein 42nd SDC 转录 | completed；本地中英双语转录可检索 | 补独立市场份额、服务绑定率和项目级证据 |
| A13 | 2026-08-25 | 北美 AI 数据中心负荷、firm power、并网与监管约束 | DOE、IEA、NARUC 官网联网检索 | completed；提取 DOE/EPRI、IEA、NERC/NARUC 关键数字与机制 | 补区域级电力价格、RTO/ISO interconnection queue 和客户项目级合同 |
| A14 | 2026-08-25 | Baker Hughes Power Systems 产品与数据中心适配 | Baker Hughes 官网 BRUSH/NovaLT 页面及 IR 搜索结果 | completed；确认发电机、同步调相机、燃机、控制和生命周期服务映射 | 补 Power Systems 分部历史收入、订单拆分和服务附件率 |
| A15 | 2026-08-25 | 更新估值市场边界 | Gangtise quote refresh | completed；BKR.O 2026-08-24 close 61.985 美元；估值接口仍未找到 BKR 数据 | 补第二行情源和 Chart 交割后 10-Q；SOTP 倍数暂采用透明分析假设 |
