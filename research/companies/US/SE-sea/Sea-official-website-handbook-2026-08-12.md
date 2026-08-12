---
title: Sea Limited 官网研究手册
as_of: 2026-08-12
company: Sea Limited
ticker: SE
---

# Sea Limited 官网研究手册

## 结论先行

Sea 官网不能用“页面数”衡量研究深度。主站是低页面密度的 Next.js 外壳，业务事实、季度材料和治理文件主要经公开 API 与 issuer CDN 提供。本次证据集覆盖 23 个 HTML、6 个 API 快照和 34 份 PDF（1,467 页），包括 FY2021-FY2025 20-F、五年业绩公告/演示/电话会记录/信息图、2026Q2 最新材料及五份治理文件。它足以支撑公司基础研究，但不替代竞争格局、监管数据库和渠道访谈等独立验证。[来源总表](../../../../sources/companies/US/SE-sea/official-website/2026-08-12/README.md)

最重要的公司画像是：Sea 不是单一互联网平台，而是三种经济模型共处的集团。Shopee 是交易、广告和履约平台；Monee 是支付、存款与快速扩张的信贷业务；Garena 是以 Free Fire、自研和第三方发行构成的数字内容业务。三者共享用户、支付、流量和本地运营能力，但资本占用、监管边界和风险完全不同，分析时不能用一个“生态协同”概念替代分部拆解。[20-F](../../../../sources/companies/US/SE-sea/official-website/2026-08-12/text/pdfs/Sea-FY2025-Form-20-F.txt)

## 证据范围与读法

| 层级 | 数量 | 用途 | 主要限制 |
|---|---:|---|---|
| 官网 HTML | 23 | 公司、产品、IR、董事、治理、ESG、安全入口 | 多数内容为概览；管理层 URL 跳首页 |
| 公开 API | 6 | 年报、季度材料、新闻与媒体资源的官方映射 | API 是数据层，不等于独立事实核验 |
| Form 20-F | 5 份 / 1,135 页 | US GAAP 三表、附注、分部、治理与风险 | 外国私人发行人不发 10-K/10-Q |
| 业绩材料 | 24 份 | FY2021-FY2025 及 2026Q2 的 KPI、APM、管理层表述 | adjusted EBITDA 等为 issuer-defined |
| 治理 PDF | 5 份 | 委员会、董事会、道德规范 | 不能替代治理有效性的独立评价 |

证据分类见 `sources/companies/US/SE-sea/official-website/2026-08-12/evidence-ledger.csv`。网站排名与战略表述均按“公司口径”处理；分析判断与未解决问题单列。所有 PDF 有 URL、SHA-256、页数和文本路径，见同目录 `pdf-manifest.jsonl`。

## 公司、组织与历史

Sea 2009 年创立于新加坡，上市主体 Sea Limited 注册于开曼群岛，在 NYSE 以 `SE` 交易，按 US GAAP、美元和日历年报告。集团通过子公司及 VIE 在东南亚、台湾、拉丁美洲等市场经营。2015 年推出 Shopee，2019 年进入拉丁美洲；SeaMoney 后更名为 Monee。[官网](https://www.sea.com/) [FY2025 20-F](https://cdn.sea.com/investor/AR2025/Z9KxpcxWs2jjxakikkr3/2026-04-17%20-%20Form%2020-F.pdf)

法律与经营边界需要分开：上市主体是控股公司；本地牌照、银行、支付、信贷、游戏发行和商城运营由不同实体承载；部分受外资限制的业务通过 VIE 合同控制。FY2025 VIE 收入低于集团收入 3%，规模不大不代表法律风险为零。

## 三个平台与变现地图

| 平台 | 核心产品 | 主要变现 | 关键经营量 | 主要风险 |
|---|---|---|---|---|
| Shopee | Marketplace、广告、物流/履约、直播/联盟、部分自营 | 交易费、广告费、增值服务、商品销售 | GMV、订单、单均 GMV、变现率、adjusted EBITDA | 竞争补贴、物流净额列报、监管与假货 |
| Monee | 钱包、支付、消费/SME 信贷、银行、保险与财富 | 利息、信贷/支付/银行费用、保费与佣金 | 贷款本金、NPL、拨备、存款、adjusted EBITDA | 信用周期、牌照、资本/流动性、资金隔离 |
| Garena | Free Fire、自研、第三方发行、电竞与社区 | 虚拟道具销售及游戏运营 | Bookings、QAU、付费用户、付费率 | Free Fire 集中、内容生命周期、第三方授权 |

更细的 14 类业务目录见 `data/curated/companies/US/SE-sea/sea-business-catalog-2026-08-12.csv`。

## Shopee

Shopee 是移动优先的买卖双方平台，提供支付、物流、履约、广告及卖家工具。FY2025 GMV 为 US$127.4bn、订单 13.9bn、adjusted EBITDA US$881m；用 GMV/订单粗算单均 GMV 约 US$9.2。法定分部利润从 2021 年亏损 US$2.767bn 改善为 2025 年盈利 US$581m，证明效率改善已经进入 US GAAP 分部口径，而非只存在于 APM。[FY2025 Results](../../../../sources/companies/US/SE-sea/official-website/2026-08-12/text/pdfs/results/Sea-FY2025-Results.txt)

2026Q2 Shopee GMV US$38.3bn、订单 4.2bn、收入 US$5.6bn、adjusted EBITDA US$255.4m；核心 marketplace 收入增长 65.6%，物流相关 value-added services 收入下降 9.0%，公司解释为 shipping subsidies 的净额列报增加。这里的收入增速包含会计展示变化，不能直接当作 take-rate 的同口径跃升。

## Monee

Monee 是本研究最需要单独建模的部分。FY2025 consumer/SME loans principal 为 US$9.2bn，其中 on-book US$8.2bn、off-book US$1.0bn；>90 天 NPL 为 1.1%。同期法定净贷款 US$7.964bn、贷款损失准备 US$842m、信用损失拨备费用 US$1.373bn、存款负债 US$3.798bn。结果公告和资产负债表的贷款口径不同，不能互换。

2026Q2 贷款本金进一步升至 US$11.1bn，NPL 为 1.0%。NPL 稳定是正面信号，但贷款高速扩张会产生 seasoning 问题；公开资料尚不足以完成逐国 vintage、roll-rate、监管资本和期限错配分析。结构化底稿见 `sea-monee-credit-funding-2021-2025.csv`。

## Garena

Garena 同时拥有自研 Free Fire 和第三方游戏发行。FY2025 bookings US$2.9bn、adjusted EBITDA US$1.656bn；Q4 QAU 633.3m、付费用户 58.0m。2026Q2 bookings US$763.5m、QAU 666.3m、付费用户 68.1m，Free Fire 日活仍超过 100m（公司口径）。

需建立 APM 断点：从 2026Q3 起，Garena adjusted EBITDA 不再包含 deferred revenue 及相关成本净变化，公司会把该变化作为补充数据披露。因此 2026Q3 以后与历史 adjusted EBITDA 的比较必须重列或桥接，不能直接连线。

## 地区与协同边界

FY2025 收入中，东南亚（不含新加坡）US$14.379bn、拉美 US$5.533bn、新加坡 US$793m、亚洲其他地区 US$2.006bn。2021-2022 把新加坡纳入东南亚，2023-2025 才拆分，结构化数据保留这一断点。

三平台可共享获客、本地团队、支付与商户关系；但不能假定 Shopee 流量必然转化为低风险贷款，也不能把 Garena 的高利润视为永久补贴其他业务的稳定资金。真正应追踪的是各分部法定利润、Monee 信贷成本和集团现金生成，而不是抽象协同叙事。

## 治理与风险

Sea 公布审计、薪酬、治理与提名委员会章程、治理准则和商业道德准则。董事会职责包括财务报告监督、重大交易、CEO 与高管评价、继任计划和年度自评。[治理页](https://www.sea.com/investor/corporategovernance)

股权控制是核心治理风险：Class B 每股 15 票，Class A 每股 1 票；截至 2026-03-31，创始人 Forrest Li 约控制 57.6% 投票权。Sea 同时是美国规则下的 foreign private issuer，因此不承担美国本土发行人相同的 10-Q、8-K 与代理披露义务。

## 待验证清单

- Monee 各国牌照、监管资本、存款集中度、资金成本、期限与 vintage 损失。
- Shopee 按国家的 GMV、订单、真实变现率、补贴与物流单位经济性。
- Garena 在 Free Fire 之外的新作贡献、授权到期与内容集中度。
- 2026Q3 Garena adjusted EBITDA 新旧定义桥。
- 官网管理层页重定向导致的完整高管名单缺口。

## 主要来源索引

1. [Sea 官网](https://www.sea.com/)
2. [FY2025 20-F](https://cdn.sea.com/investor/AR2025/Z9KxpcxWs2jjxakikkr3/2026-04-17%20-%20Form%2020-F.pdf)
3. [FY2025 Results](https://cdn.sea.com/investor/4Q2025/JcKns4LaJC8bxcQdJwXz/2026.03.03%20Sea%20Fourth%20Quarter%20and%20Full%20Year%202025%20Results.pdf)
4. [2026Q2 Results](https://cdn.sea.com/investor/2Q2026/wFBC39MbqnfLb3MGY6LP/2026.08.11%20Sea%20Second%20Quarter%202026%20Results.pdf)
5. [2026Q2 Transcript](https://cdn.sea.com/investor/2Q2026/wFBC39MbqnfLb3MGY6LP/2026.08.11%20Sea%20Second%20Quarter%202026%20Earnings%20Call%20Transcript.pdf)
6. [治理页](https://www.sea.com/investor/corporategovernance)
