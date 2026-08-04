---
id: company-cellnex-official-website-handbook-2026-08-04
type: company-official-website-handbook
title: Cellnex Telecom 官网业务与产品手册
status: active
as_of: 2026-08-04
tickers: [BME:CLNX]
industries: [telecom-infrastructure, towerco, digital-infrastructure]
tags: [official-website, primary-research, product-catalog, company-research]
---

# Cellnex Telecom 官网业务与产品手册

> **时点**：2026-08-04  
> **证据范围**：Cellnex 官网 61 个 HTML 页面、7 份可读官方 PDF、1 份被 CDN 置换为 HTML 的不可用 PDF 响应。  
> **阅读规则**：`官网事实` 包括 Cellnex 官网及正式财务材料中的公司披露；`公司主张` 指尚未独立核验的市场地位、规模、性能或前景表述；`分析判断` 是基于上述证据的投资研究归纳；`未解决` 表示口径冲突或仍需其他文件核实。

## 1. 结论先行

Cellnex 的本质不是通信设备制造商，也不主要出售标准化“产品”。它是一个以长期合同经营共享通信基础设施的欧洲中立宿主（neutral host）：建设、购买或租用站址，向移动运营商提供塔桅、屋顶、机房、供电和接入条件；客户通常自行拥有和维护主动无线设备。Cellnex 同时经营室内/高密度覆盖、光纤与边缘机房、广播和关键通信等相邻基础设施服务。[O01][O03][O04]

正式财务口径分为四条业务线，而不是官网按客户场景展示的九类 Solutions：

| 报告业务线 | 核心交付 | FY2025 经营收入 | H1 2026 披露 | 研究定位 |
|---|---|---:|---:|---|
| Towers | 宏站、屋顶、特殊站址，共址、BTS、工程及站址服务 | EUR 3,221m | EUR 1,625m；有机增长 5.2% | **绝对核心**；收入与现金流主引擎 |
| DAS, Small Cells and RAN as a Service | 室内/密集区覆盖、RANaaS、PPDR、部分 O&M 和 IoT | EUR 272m | 报告收入约 EUR 128m；有机增长 4.5% | 邻近增长；室内连接是当前主要驱动 |
| Fiber, Connectivity and Housing Services | FTTT、传输/回传、专线、边缘数据中心 | EUR 234m | 报告收入约 EUR 109m；有机增长 7.8% | 增速较高但资产组合仍在调整 |
| Broadcast | 电视、广播、网络运维、媒体连接和 OTT 相关服务 | EUR 264m | 报告收入约 EUR 133m；有机增长 0.5% | 稳定、低增长的区域性业务 |

注：四条业务线收入之和不等于集团 EUR 4,418m FY2025 Operating Income，差额涉及能源 pass-through、成本转收费及其他经营收入；不能用分部简单加总替代法定报表口径。[O03]

**分析判断。** Cellnex 的核心经济飞轮是“先锁定锚定客户 -> 取得/建设站址 -> 在同一固定成本资产上增加第二、第三租户 -> 通过调价条款和工程服务增长 -> 以租约优化和运维效率扩大利润率”。现有站点加租户通常优于新建 BTS 的早期回报，因为新增共址可以复用塔桅、土地、供电和维护体系；但回报仍受剩余承载能力、改造资本开支、地租和许可制约。[O04][O06]

公司的战略阶段已经变化：2015-2022 年以低资金成本下的跨国并购和资产购买为主；自 2024 Capital Markets Day 起，重点转为有机共址、选择性 BTS、租约与运维优化、降低杠杆、保持投资级评级、提升自由现金流并扩大股东回报。H1 2026 的 EUR 301m FCF、较低 BTS 强度和全年 EUR 1bn 股东回报是这一转向的阶段性结果，而非旧式外延扩张的延续。[O06][O07][O09]

## 2. 证据边界与价格口径

官网没有公开站址租赁目录价、每 PoP 收费、每座塔的建设成本、DAS 节点报价、光纤每公里价格、机柜功率价格、分业务线利润率或单项目 IRR。商业条款通常通过 MSA（Master Service Agreement）、MLA（Master Lease Agreement）、项目合同或 SLA 协商。[O04][O05]

本手册不把以下指标视为可直接兑现的财务事实：

- 2024 CMD 的 `EUR 110bn+ CPI` backlog 是管理层估计，依赖续约等假设，不是不可撤销订单；正式年报说明 backlog 包含固定 escalator，但不包含未来通胀调整，部分合同在特定条件下可较短通知取消。[O05][O06]
- 官网所称约 `130,000 sites` 包含计划 BTS 和 pending operations，不等同于截至时点已投入运营且完全拥有的塔数。[O10]
- 官网的客户案例证明交付形态，但不自动证明项目价格、利润率、独占性或可复制性。
- 官网声称卫星直连终端将补充而非替代地面网络，属于公司技术判断，并非独立行业结论。[O07]

## 3. 公司身份与经营版图

Cellnex 于 2015 年由 Abertis 通信部门分拆并上市，总部和主要办公室位于西班牙。官网称其在 10 个欧洲国家经营：丹麦、法国、意大利、波兰、葡萄牙、西班牙、瑞典、瑞士、荷兰和英国。[O01][O02]

| 国家 | TIS 页面列示站址（含计划 BTS / pending operations） | 主要官网信号 |
|---|---:|---|
| 法国 | 28,455 | 最大站址市场；Nexloop 光纤持续部署 |
| 意大利 | 22,842 | 首个国际市场；塔站和 DAS 规模较大 |
| 波兰 | 20,391 | 塔站、RANaaS、PPDR 和光纤均有经营 |
| 英国 | 13,610 | 塔站及大量 Small Cells / indoor nodes |
| 西班牙 | 8,769 | 总部市场；广播、关键通信、光纤和 IoT 较强 |
| 葡萄牙 | 6,800 | 塔站与 IoT 网络 |
| 瑞士 | 6,118 | 塔站；Sunrise 长期 BTS 伙伴关系 |
| 瑞典 | 5,177 | CK Hutchison 资产来源 |
| 荷兰 | 4,298 | 高塔、广播与数据中心 |
| 丹麦 | 1,881 | CK Hutchison 资产来源 |

上述数字合计低于 `130k` 头条指标，原因至少包括计划建设和交易/运营口径；不应把两者写成同一个“当前塔数”。年报还记录近年处置 Nordics、奥地利、爱尔兰及 Towerlink France 等资产，说明当前战略强调组合质量而非国家数量最大化。[O02][O10]

## 4. 商业模式

### 4.1 收入如何形成

Towers 收入主要由四部分组成：[O04]

1. **Annual base fee**：锚定客户和次级租户按站址、设备、占用空间、容量等支付基础服务费。
2. **Escalator**：基础费按 CPI/RPI、通胀指标或固定比例调整。2024 CMD 称约 65% 收入与 CPI 挂钩（多数有 cap），约 35% 使用 1%-2% 固定 escalator，多数合同 floor 为 0%；这是 2024 公司口径，当前组合仍需逐合同更新。[O06]
3. **Co-location**：在已有资产上增加第三方租户、PoP 或设备，通常带来较高增量利润。
4. **Engineering and special projects**：5G 改造、站点配置、设计、安装、去站和能源韧性等形成单独履约义务或资本开支回收。

客户一般按月或按季付款。锚定客户合同期限长，常有自动延期；2024 CMD 披露 16 个 anchors 的平均合同期（含续约）约 31 年。H1 2026 的实例包括 Vodafone Spain 约 2,000 个现有 PoP 续约十年，以及 Sunrise 新增 300 个 BTS 站点，原 MSA 为 `20+10+10` 年并在此后转为无固定期限。[O06][O08]

### 4.2 成本与资本开支

主要成本包括地租、能源、税费、维护和修理。大部分土地或屋顶通过第三方租约、转租或其他合同控制；Cellnex 通过买地、续租、重新议价和租金资本化/预付降低长期 lease cash-out。[O04][O17]

资本开支至少应区分：

- **Maintenance capex**：维持站址、安全、供电和可用性。
- **Expansion capex**：为现有站点新增租户、承载能力或功能。
- **BTS capex**：为锚定客户建设新站，前期占用现金，随着交付完成和后续共址才能改善资产效率。
- **Remedies / decommissioning**：监管救济、网络整合或重复站址拆除。

**分析判断。** BTS 是增长与现金流之间的关键张力：它锁定长期锚定收入并扩大站址网络，但在初期拉低 tenancy ratio、推高资本开支；共址则利用既有固定成本资产。H1 2026 FCF 加速部分来自 BTS 强度下降，不能简单归因于收入增长。[O07][O09]

### 4.3 经营杠杆及其限制

同一站址增加租户时，塔桅、土地、供电接入、NOC 和部分维护成本可复用，因此存在经营杠杆。H1 2026 tenancy ratio 升至 `1.63x`，净 PoP 同比增长 `4.9%`；gross growth `5.7%` 中共址贡献 `3.6%`、BTS `1.8%`，churn 为 `-0.6%`。[O07]

但经营杠杆并非无条件成立：

- 地租和运营成本可能无 cap，而客户调价可能有 cap，出现通胀错配。
- MNO 合并、RAN sharing、主动设备整合或去站会带来 churn。
- 新租户可能需要加固、供电升级或许可，新增收入并非零成本。
- 能源 pass-through 降低能源价格风险，但 pass-through 收入也会扭曲表面收入与利润率比较。
- 收入集中于少数 MNO；2024 CMD 称前三大客户约占收入 48%，正式年报亦将客户集中列为信用风险。[O03][O06]

## 5. 四条业务线与核心产品

### 5.1 Towers：核心产品不是“塔”，而是长期站址服务

| 产品/服务 | 交付内容 | 客户价值 | 收费边界 |
|---|---|---|---|
| Macro tower co-location | 在共享宏站安装客户主动设备 | 避免自建、缩短部署、共享固定成本 | MSA/MLA 基础费 + escalator + 新 PoP |
| Rooftops & special sites | 城市屋顶、高塔及独特位置 | 密集区或农村覆盖 | 站址/设备/空间/容量相关，未公开单价 |
| Build-to-Suit | 按锚定客户需求建设新站 | 覆盖扩展和快速 4G/5G 部署 | 长期合同；项目 IRR 未披露 |
| Build-to-Fit / site adaptation | 对站点承载、供电和配置进行改造 | 容纳新增设备或技术代际 | 项目费或合同内服务费 |
| Engineering / works / installation | 设计、研究、施工、调试 | 一站式部署和改造 | 独立履约义务，费率未披露 |
| Decommissioning / rationalisation | 拆除重复站点并迁移到共享站点 | 并网后降本和资产优化 | 合同协商；去站预付款可能递延摊销 |
| NOC / operations | 24x7 监控能源、安全、告警和可用性 | SLA 和连续运营 | 通常嵌入服务合同 |
| Energy resilience | 电池、备用电源和能源管理 | 断电韧性和监管合规 | 资本开支与服务费未披露 |

Cellnex 正把“纯共址”扩展为 `site as a service`：除物理位置外，将绿色能源、韧性、高带宽连接、工程和运维组合交付。其竞争力来自站址密度、许可与业主关系、MNO 长约和多租户管理，而非自研无线基站设备。[O10]

### 5.2 DAS、Small Cells 与 RANaaS

DAS 和 Small Cells 是宏站的补充。DAS 将多个分布式天线连接到共同信号源，Small Cell 则以低功率节点解决局部覆盖和容量；典型场景包括体育场、机场、医院、购物中心、办公楼、地铁、隧道和历史城区。Cellnex 提供许可、设计、部署、调试、运维和质量保障，并以中立宿主方式让多家 MNO 共用系统。[O11]

FY2025 年报披露约 `15,509 antenna nodes`，官网公司简介则称 `+7,500 DAS nodes and Small Cells installed`，详细产品页逐国列示的节点又采用不同范围。三个指标的对象、时间和统计层级不一致，暂不合并。[O01][O03][O11]

RANaaS 在波兰把主动发射和传输服务叠加在被动塔站之上；公司表示先巩固波兰，再考虑扩大地域。PPDR/mission critical 包括 TETRA、LTE 和 5G 私网的设计、工程、运行和维护，服务公共安全、交通和海事救援。西班牙官网称有 19 项关键通信、1,300 多个基站和 98,000 多名用户，属于公司规模披露。[O15]

IoT/Smart Services 在年报中归入这条业务线的 Other Services。官网展示从传感器、Sigfox/LoRaWAN 网络，到 SmartConnectivity、SmartBrain 和 SmartSolutions 的端到端栈；但未披露独立收入、ARR 或利润率，因此投资分析上应视为小型邻近业务，而不是与 Towers 同级的核心平台。[O16]

### 5.3 Fiber、Connectivity 与 Housing

该业务线包括：

- **FTTT**：以光纤连接宏站，为 5G 和高容量回传提供基础。
- **Backhaul / transmission**：在网络节点之间用光纤、微波或卫星传输数据。
- **Enterprise leased lines**：向运营商、公共部门、企业及农村客户提供专线。
- **Edge data centres / housing**：按客户选择组合机柜空间、能源、连接、冷却、安全和运维，以 Tier 1-4 SLA 管理。[O12][O13]

H1 2026 有机增长 `7.8%`，公司归因于法国 Nexloop 持续部署；但同一期间法国数据中心处置被从 pro-forma 基数中剔除。官网列示荷兰 24 个、法国 100 多个、西班牙 4 个数据中心位置，与处置后的当前经济权益范围需要再核实。[O07][O13]

### 5.4 Broadcast

Broadcast 包含电视和广播信号分发、网络运行维护、媒体内容连接以及 OTT 相关服务，主要位于西班牙和荷兰。FY2025 Operating Income 为 EUR 264m；H1 2026 有机增长仅 `0.5%`，公司称近期续约支撑温和增长。[O03][O07][O14]

**分析判断。** 广播业务可复用高塔、供电、监控和维护能力，现金流可能较稳定，但受传统地面广播成熟度约束，增长性显著低于 Towers、DAS 和光纤。官网没有披露合同剩余期限、客户集中度或单独 EBITDAaL。

## 6. 客户、渠道与典型应用

| 客户群 | 主要需求 | Cellnex 交付 | 代表性官网证据 |
|---|---|---|---|
| MNO | 宏覆盖、容量、5G、韧性和降本 | 共址、BTS、工程、去站、能源、FTTT | Vodafone Spain 续约；Sunrise BTS；Telefónica 电池项目 [O08] |
| 其他运营商/宽带商 | 站址和传输 | 塔站、光纤、专线、机房 | TIS、Fiber 页面 [O10][O12] |
| 地铁/铁路/机场 | 隧道和大型交通枢纽连续覆盖 | DAS、Small Cells、关键通信、光纤 | Grand Paris Express 16/17 号线覆盖 40 个车站和隧道 [O19] |
| 场馆/商业地产/医院 | 室内多运营商覆盖 | DAS、Small Cells、NOC/SLA | Tour Alto、Meliá/Sanitas、机场案例 [O20][O22] |
| 政府与应急机构 | 高可用、保密、群组通信和视频 | TETRA/LTE/5G PPDR、IoT | SIRESP 和 Mission Critical 页面 [O15][O21] |
| 广播机构 | 全国/区域信号与高可用运维 | DTT、广播、NOC、媒体连接 | Broadcast 页面 [O14] |
| 地主/屋顶业主 | 资产变现 | 买地、长租、续约、租金资本化 | Landlords 页面 [O17] |

`Ready to Connect` 是站址发现和商业转化的数字入口，不是独立财务分部。它可以缩短客户选址和内部销售流程，但官网未披露使用量、转化率或独立收入。[O27]

## 7. 公司战略

### 7.1 从并购平台转向运营与资本纪律

2024 CMD 明确把历史阶段描述为以 inorganic growth 为主，并提出新的重点：[O06]

- Towers 继续保持约 80% 的核心收入权重。
- 通过共址和选择性 BTS 实现有机 PoP 增长。
- 将新建需求尽可能转化为可共址的资产，而非只满足单租户 BTS。
- 优化地租、维护、采购、供应商和工作流。
- 控制 BTS 资本开支，释放 FCF。
- 去杠杆并维持至少两家机构的投资级评级。
- 在满足回报门槛后进行股东分配或选择性投资。

H1 2026 已体现这套顺序：管理层强调项目级回报和税后无杠杆 IRR，FCF 从 H1 2025 的 EUR 19m 增至 EUR 301m，同时宣布 2026 年合计 EUR 1bn 股东回报。[O07][O09]

### 7.2 增长优先级

1. **已有塔站共址与 5G 改造**：资本效率最高的自然增长来源。
2. **选择性 BTS**：以长期锚定合同扩大网络，但更严格审查项目回报。
3. **网络韧性**：电池、备用能源和气候适应带来新合同机会。
4. **Indoor / DAS / Small Cells**：数据流量增长与宏站难覆盖场景推动部署。
5. **FTTT 与传输**：为塔站和 5G 提供相邻基础设施，提高客户黏性。
6. **PPDR、IoT、Edge**：利用既有站址、NOC 和客户关系，但独立商业规模仍小或未披露。
7. **组合管理**：出售非核心地域或资产，将资本转向高回报项目和股东分配。

### 7.3 战略风险

- MNO 合并、频谱共享、RAN sharing 和站点去重可能降低 PoP。
- 前三大客户占比较高，续约和信用状况重要。
- 长期客户合同与地租合同的通胀 cap 不对称可能侵蚀利润。
- 高杠杆和再融资成本会压缩资本配置空间；FY2025 仍有 23% 债务为浮动利率。
- BTS 建设、许可、供应链和业主谈判存在延期与超支风险。
- D2D 卫星、频谱效率提升和网络架构变化可能减少部分偏远覆盖需求；公司认为只会补充地面网络，仍需独立验证。
- DAS、Edge、IoT 与主动 RAN 的经营模型不同于被动塔站，可能没有同样的固定成本杠杆和合同久期。

## 8. 治理与 ESG

官网披露董事会中独立董事占 67%、女性占 42%；公司治理入口还覆盖审计与风险、提名薪酬与可持续发展以及资本配置等委员会。2025 年公司治理 PDF 链接在本次抓取中返回 HTML 响应，因此未用该文件补充细节。[O23]

Sustainability Master Plan 2030 把目标组织为 Resilient infrastructures、Climate action、Customer focus & Business conduct、People first。官网目标包括：[O18][O26]

- 2030 年 Scope 1/2 绝对排放较 2020 年降低 70%。
- 2025-2030 年使用 100% renewable electricity。
- 2030 年覆盖 82% 供应商和客户排放的 SBT。
- 与客户约定 5,000 个使用锂离子电池的站点。
- 所有高/极高气候风险站点具有适应计划。
- 100% 资本配置决策考虑 ESG 标准。

这些是公司目标，不是截至 2026-08-04 全部已经完成的结果；需要年度审验数据确认进度。

## 9. 矛盾、待验证事项与研究含义

### 9.1 需要保留的口径差异

| 主题 | 口径 A | 口径 B | 处理方式 |
|---|---|---|---|
| 站址 | 官网称约 130k，含计划 BTS 和 pending operations | TIS 各国列示合计较低 | 不称为“当前拥有 130k 座塔” |
| DAS/Small Cells | 公司简介 `+7,500 nodes and Small Cells` | FY2025 年报约 15,509 antenna nodes | 统计对象可能不同，不合并 |
| Edge DC | 官网仍列法国 100+ locations | H1 2026 pro-forma 剔除 French Data Centers disposal | 当前资产边界待核实 |
| Backlog | 2024 CMD `EUR 110bn + CPI` | 年报定义依赖续约假设且部分合同可取消 | 视为管理层估计，不是订单余额 |
| 业务分类 | 官网按技术/行业场景展示 | 财务报告按四条业务线 | 投资分析以财务业务线为主 |

### 9.2 投资研究含义

**分析判断。** 对 Cellnex 最重要的监控指标不是“塔数”本身，而是净 PoP 增长、共址/BTS 构成、tenancy ratio、churn、收入 escalator、lease cash-out、BTS 强度、RLFCF/FCF、杠杆与客户续约。单纯增加塔数可能稀释短期资产利用率；在既有站点增加租户才更直接体现共享基础设施的经济性。

第二个关键是把核心 Towers 与相邻业务分开估值。DAS/Small Cells、光纤和 PPDR 能增强客户关系并承接流量增长，但 Edge、IoT、RANaaS 和 Broadcast 的资本密度、合同久期及竞争结构不同，不能机械套用核心塔站倍数。

### 9.3 后续验证问题

1. 2026 年底实际运营站址、在建 BTS、PoP 和 tenancy ratio 的统一口径。
2. 前五大客户收入占比、各主 MSA 到期/续约窗口与去站保护条款。
3. 2025-2027 剩余 BTS 承诺、年度现金资本开支和新签项目 IRR 门槛。
4. CPI cap、fixed escalator 与地租 escalator 的国家级错配。
5. French Data Centers、O&M Spain 及其他处置后的四条业务线可比基数。
6. DAS、Fiber、PPDR、IoT 和 Edge 的独立 EBITDAaL、资本回报和合同久期。
7. EUR 1bn 2026 股东回报后净债务/EBITDAaL 和评级缓冲。
8. MNO 合并、Open RAN、D2D satellite 和频谱效率对站址需求的净影响。

## 10. 来源索引

- **[O01]** Cellnex, What we do: <https://www.cellnex.com/about-cellnex/what-we-do/>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/text/pages/ba1dcd59f9baa9c5a043.txt`
- **[O02]** Cellnex Global: <https://www.cellnex.com/about-cellnex/cellnex-global/>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/text/pages/e145a2e9d2275b61eccb.txt`
- **[O03]** Integrated Annual Report 2025: <https://www.cellnex.com/app/uploads/2026/03/Informe-Anual-Integrado-2025_EN_Optimized.pdf>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/raw/pdfs/Cellnex-Integrated-Annual-Report-2025.pdf`
- **[O04]** Integrated Annual Report 2025, Towers revenue model and costs: 同 [O03]。
- **[O05]** Integrated Annual Report 2025, contracted revenue definition: 同 [O03]。
- **[O06]** Capital Markets Day 2024: <https://www.cellnex.com/app/uploads/2024/03/Cellnex-CMD-vDEF_Presented.pdf>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/raw/pdfs/Cellnex-CMD-2024.pdf`
- **[O07]** H1 2026 results release: <https://www.cellnex.com/news/cellnex-h1-2026-results/>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/text/pages/b9cd28155c6b8d1a6ddc.txt`
- **[O08]** H1 2026 Results presentation: <https://www.cellnex.com/app/uploads/2026/07/Cellnex-Results-Q2-2026.pdf>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/raw/pdfs/Cellnex-H1-2026-Results.pdf`
- **[O09]** H1 2026 backup: <https://www.cellnex.com/app/uploads/2026/07/Cellnex-H1-2026-Backup.pdf>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/raw/pdfs/Cellnex-H1-2026-Backup.pdf`
- **[O10]** Telecom Infrastructure Services: <https://www.cellnex.com/technology/tis/>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/text/pages/64b78db1cc3bbc76da17.txt`
- **[O11]** DAS & Small Cells: <https://www.cellnex.com/technology/das-small-cells/>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/text/pages/3731cae360a18f442c92.txt`
- **[O12]** Fibre: <https://www.cellnex.com/technology/fiber/>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/text/pages/b5cabf969bb14790082f.txt`
- **[O13]** Datacentres: <https://www.cellnex.com/technology/edge-datacentres/>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/text/pages/fe2139ab2df19b0d3d08.txt`
- **[O14]** Broadcast: <https://www.cellnex.com/technology/broadcast/>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/text/pages/25a9c1017cfeb1702e29.txt`
- **[O15]** Mission Critical: <https://www.cellnex.com/solutions/mission-critical/>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/text/pages/0fb84140dfbdda9f6adb.txt`
- **[O16]** IoT & Smart Services: <https://www.cellnex.com/technology/smart-iot/>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/text/pages/c1d2a2069fef845ce91c.txt`
- **[O17]** Landlords: <https://www.cellnex.com/landlords/>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/text/pages/b3cff1686ea23e12d4c8.txt`
- **[O18]** Sustainability: <https://www.cellnex.com/sustainability/>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/text/pages/fc8ddd6d1e6585b7f59a.txt`
- **[O19]** Grand Paris Express use case: <https://www.cellnex.com/use-cases/grand-paris-express-metro-lines-16-17/>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/text/pages/373b42df915ccba9eeba.txt`
- **[O20]** Tour Alto use case: <https://www.cellnex.com/use-cases/seamless-connectivity-for-up-to-4700-daily-users-at-the-tour-alto-building/>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/text/pages/d194172ad8b1a33454f9.txt`
- **[O21]** SIRESP use case: <https://www.cellnex.com/use-cases/siresp/>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/text/pages/c7749f89ff5638c48066.txt`
- **[O22]** Malpensa and Linate airports use case: <https://www.cellnex.com/use-cases/malpensa-and-linate-airports/>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/text/pages/3b01911c004013e9d06f.txt`
- **[O23]** Corporate Governance: <https://www.cellnex.com/investor-relations/corporate-governance/>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/text/pages/7368246caced39ab997d.txt`
- **[O24]** Fixed Income: <https://www.cellnex.com/investor-relations/fixed-income/>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/text/pages/bcdec2292968d8d6daff.txt`
- **[O25]** Equity Story 2026: <https://www.cellnex.com/app/uploads/2026/04/Cellnex-Equity-Story-26.pdf>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/raw/pdfs/Cellnex-Equity-Story-2026.pdf`
- **[O26]** Environment: <https://www.cellnex.com/sustainability/environment/>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/text/pages/4fb8a0d5b750b575451e.txt`
- **[O27]** Ready to Connect: <https://www.cellnex.com/ready-to-connect/>；本地：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/text/pages/9ea4d2139731be5be3fd.txt`

## 11. 关联文件

- 结构化业务目录：`data/curated/companies/ES/CLNX-cellnex/cellnex-business-catalog-2026-08-04.csv`
- 官网快照说明：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/README.md`
- 证据台账：`sources/companies/ES/CLNX-cellnex/official-website/2026-08-04/evidence-ledger.csv`
