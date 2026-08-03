---
id: company-nokia-official-product-handbook-2026-07-25
type: company-product-handbook
title: Nokia 官网业务与产品手册
status: active
as_of: 2026-07-25
tickers: [NOKIA, NOK]
industries: [telecom-equipment, networking, optical, mobile-infrastructure]
tags: [official-website, product-catalog, primary-research]
---

# Nokia 官网业务与产品手册

> **时点**：2026-07-25  
> **证据范围**：Nokia 官网 547 个页面记录（546 个 HTTP 200）、5 份官方 PDF。  
> **阅读规则**：`官网事实` 是 Nokia 自述或官方财务披露；`分析判断` 是基于产品组合的归纳；`未披露` 表示官网没有公开可核实数值。营销页中的节省、性能和覆盖指标均是厂商口径，不等同于第三方测试或审计结果。

## 1. 结论先行

Nokia 已不是按“移动网络、网络基础设施、云与网络服务、Nokia Technologies”理解的旧结构。自 2026 年 1 月 1 日起，公司有两个主要经营分部：**Network Infrastructure** 和 **Mobile Infrastructure**；另设待处置的 **Portfolio Businesses**，以及独立孵化的 **Nokia Defense**。[O01]

| 报告层级 | 业务单元 | 本手册对应产品域 | 2026Q2 状态 |
|---|---|---|---|
| Network Infrastructure | Optical Networks | 光传输、相干光器件、光网络自动化 | 持续经营；AI/Cloud 需求主要受益域 |
| Network Infrastructure | IP Networks | 核心/边缘路由、数据中心交换、IP 自动化、DDoS | 持续经营 |
| Network Infrastructure | Fixed Networks | PON、铜线接入、ONT/OLT、接入控制、家庭 Wi-Fi | 持续经营，但 FWA CPE 已移出并列终止经营 |
| Mobile Infrastructure | Core Software | 分组核心、用户数据、语音、计费/策略、API、云运维 | 持续经营 |
| Mobile Infrastructure | Radio Networks | 基带、射频、Massive MIMO、小基站、Cloud/Open RAN、RAN 自动化 | 持续经营 |
| Mobile Infrastructure | Technology Standards | 标准必要专利、专利池/双边许可、多媒体技术 | 持续经营；现金流依赖 IP 授权 |
| Portfolio Businesses | Site Implementation and Outside Plant | 站点工程、外线部署 | 持续经营、战略待定 |
| Portfolio Businesses | Microwave Radio | Wavence 微波无线与 MSS | 持续经营、战略待定 |
| 终止经营 | Fixed Wireless Access CPE | FastMile 网关/室外接收器 | 已协议出售给 Inseego |
| 终止经营 | Enterprise Campus Edge | 私网/园区边缘组合 | 很可能出售 |
| 独立孵化 | Nokia Defense | Banshee、Talon、Mission-Safe Phone、军用网络方案 | 独立 go-to-market 与研发中枢 |

**官网事实。** 2026Q2，Network Infrastructure 净销售额 EUR 2.037bn、经营利润 EUR 166m；Mobile Infrastructure 分别为 EUR 2.680bn、EUR 310m；Portfolio Businesses 持续经营口径分别为 EUR 94m、约 EUR 0m。集团季度净销售额 EUR 4.815bn。[O02][O03]

**分析判断。** Nokia 的交付对象不是单一“电信设备”，而是五层栈：芯片/DSP 与光电器件 -> 网络设备 -> 网络操作系统 -> 控制/自动化软件 -> 设计部署和托管服务。客户采购通常是项目制软硬件组合，不能用官网某个机框或网关的单价推导合同价值。

## 2. 口径、商业模式与价格边界

### 2.1 官网 solution areas 不等于财务分部

官网导航列出 Autonomous Networks、Broadband Access、Core Networks、Data Center Networks、IP Networks、Microwave Transport、Multimedia Technologies、Network APIs、Network Security、Optical Networks、Radio Access Networks 等 solution areas。它们按客户问题组织，横跨上述报告分部。例如 Deepfield 既是 IP 产品又是安全产品；Network as Code 同时依赖核心网开放能力与开发者生态。

### 2.2 典型收费方式

| 形态 | 收费/成本驱动 | 官网公开程度 |
|---|---|---|
| 机框、线卡、射频、ONT/CPE | 按配置、端口/容量、频段、光模块、冗余、数量和服务期报价 | **未披露目录价、BOM、单位毛利** |
| 网络软件 | 永久许可或期限订阅，常按节点、容量、用户/会话、功能包和支持期 | Core SaaS 明确为订阅式；具体费率未披露 |
| 自动化/安全软件 | 软件许可/订阅 + 集成 + 运维；价值与受管设备、流量和模块相关 | 仅披露若干效益指标，未披露费率 |
| 专利许可 | 双边协议或专利池，按设备/品类/销量等合同条款收取 | 许可机制公开，具体客户费率通常保密 |
| 专业服务 | 设计、部署、优化、维护、托管，按项目范围和 SLA | 未披露标准人天价或项目价 |

**官网事实。** Core SaaS 是按需订阅，Nokia 负责预集成、投产、运营和维护。[O20] Mission-Safe Phone 被描述为“commercial smartphone 的成本水平”，但没有金额。[O129]

**未披露。** 本手册未发现 Nokia 官网对主流网络产品公开 MSRP、成交价、物料成本、安装成本或产品线毛利。所有此类栏目在结构化目录中记为“官网未披露/询价制”，不做市场价格反推。

## 3. Network Infrastructure

### 3.1 Fixed Networks

#### 3.1.1 光纤接入：PON、OLT 与 ONT

PON 的工作方式是局端 OLT 通过无源分光器共享一根馈线光纤连接多台用户侧 ONT。GPON、XGS-PON、25G PON 和 50G PON 可在同一外线基础设施共存，使运营商通过更换端点和增加波长升级，而不必重铺全部光纤。[O04][O05]

| 产品线/产品 | 工作方式与关键数据 | 场景与客户 | 价格/成本 |
|---|---|---|---|
| Lightspan MF | 高容量机框式 OLT，面向多代 PON 汇聚 | 大型运营商局端、超大规模接入节点 | 未披露 |
| Lightspan FX-4/8/16 | 4/8/16 槽位；每槽 `2 x 100 Gb/s` 背板；插卡承载 GPON/XGS/25G/50G PON | 城域局端、住宅/企业/移动承载共网 | 未披露 |
| Lightspan DF-16GM/32GM | 1RU 固定式 OLT；GPON/XGS-PON/25G PON；官网称功耗较行业平均低 `>20%` | 边缘机房、分布式接入、空间/功耗受限站点 | 未披露 |
| Lightspan SF-8M | 密封式户外 OLT，可放在更靠近用户的外线环境 | 农村、低密度、远端部署 | 未披露 |
| 25G PON | 在现有 GPON/XGS-PON ODN 上叠加 25Gb/s 级能力 | 企业专线、移动 xHaul、住宅升级 | 未披露 |
| 50G PON | 下行 50Gb/s，上行 25/50Gb/s；面向更高带宽业务 | 数据中心接入、企业、未来移动承载 | 未披露 |
| Fiber ONT / XS-2437X-B | 将 PON 光信号终结为以太网/Wi-Fi；XS-2437X-B 属 XGS-PON 家庭网关 | 家庭和小企业 | 未披露 |
| 25G ONT / 50G ONT | 与 25G/50G OLT 配对，为企业或高端用户提供高速以太网交付 | 企业、基站、批发接入 | 未披露 |

来源：[O04]-[O08]。**分析判断。** OLT 的经济性主要由每端口用户数、分光比、上联容量、功耗和机房空间决定；ONT 的成本随 Wi-Fi 代际、以太网口速率和光学能力变化。官网的低功耗百分比不能直接换算客户 TCO，仍需电价、负载和生命周期。

#### 3.1.2 接入自动化与家庭网络

| 产品 | 原理/工作方式 | 典型工作场景 | 官网量化主张 |
|---|---|---|---|
| Altiplano Access Controller | 云原生 SDN 控制器，把多厂商接入设备抽象为统一意图、自动化工作流和开放接口 | 固网开通、变更、保障、跨代 PON 管理 | 日常运营节省 `25%-40%`，验证速度提高 `4x` [O09] |
| Altiplano Marketplace | 在 Altiplano 上分发 Nokia/第三方应用 | 按需扩展接入分析和自动化 | 未披露价格 [O10] |
| Lightspan OS | OLT 网络操作系统，将硬件生命周期与控制/应用解耦 | 开放接入、可编程运维 | 未披露 [O11] |
| Corteca | 家庭连接云平台，结合设备管理、Wi-Fi 优化、应用和运营商门户 | 运营商托管 Wi-Fi、家庭网络体验与增值业务 | 未披露 [O12] |
| Corteca Home Controller / Applications | 控制器进行家庭拓扑、故障和性能管理；应用提供家长控制/安全等功能 | 客服、主动保障、订阅增值服务 | 未披露 [O13] |
| Wi-Fi Beacon 24 | Wi-Fi 7 四频 mesh；最高 24Gb/s；10G WAN，1x10G + 2x2.5G LAN | 多千兆家庭、运营商托管 Wi-Fi | 未披露 [O14] |

#### 3.1.3 其他接入与服务

- **Gigabit Connect / G.fast / MoCA**：利用既有铜线或同轴的最后一段交付千兆级连接，适合多住户楼宇和重铺光纤困难的位置。[O15]
- **Aurelis Optical LAN**：以 PON 替代园区多级以太交换，减少中间有源设备和布线，服务酒店、校园、医疗、制造和公共部门。[O16]
- **Broadband Easy、Easy Connect、Health Index、ONT Easy Start**：覆盖宽带规划、安装、自动开通、健康评分和终端启动；其成本通常体现为软件/服务合同，官网未给费率。[O17]

### 3.2 IP Networks 与 Data Center Networks

#### 3.2.1 路由、交换和芯片

这些设备以 Nokia SR OS 或 SR Linux 转发 IP/MPLS、EVPN、以太网和分段路由流量；FP5/FPcx 是数据面处理基础。路由器面向运营商边缘/核心和数据中心网关，IXS/IXR 面向 AI 数据中心 leaf/spine fabric。[O30][O31]

| 产品 | 定位与关键数据 | 场景/客户 | 价格成本 |
|---|---|---|---|
| 7750 SR | 模块化业务路由器，最高约 `230 Tb/s` 全双工，支持 800GE/1.6T clear-channel | IP 核心、宽带边缘、数据中心网关、peering | 询价制；未披露单端口成本 [O32] |
| 7730 SXR | `3.6-5.6 Tb/s`，1GE-400GE，最多 256K queues | 汇聚、城域、企业边缘、移动承载 | 未披露 [O33] |
| 7705 SAR | 面向关键业务和移动 xHaul 的业务汇聚路由器 | 电力、交通、公共安全、基站 | 未披露 [O34] |
| 7210 SAS | 紧凑型以太/MPLS 接入与汇聚 | 企业接入、移动和批发业务 | 未披露 [O35] |
| 7215 IXS | 48x1G RJ45 + 4x1/10GE | 管理网、低速服务器接入、边缘机房 | 未披露 [O36] |
| 7220 IXR | 最高 `102.4 Tb/s`，支持 1.6TE | AI/云 leaf-spine、超大规模交换 | 未披露 [O37] |
| 7250 IXR | 最高 `460.8 Tb/s` | 超大规模 AI fabric 和数据中心互联 | 未披露 [O38] |
| FP5 | `6 Tb/s` 网络处理器，约 `0.1 W/Gb`，官网称比 FP4 节能 75% | 7750/相关平台的可编程转发、安全和遥测 | 芯片不公开单卖价格 [O39] |
| FPcx | 面向数据中心交换的可编程处理器系列 | EDA/SR Linux 数据中心 fabric | 未披露 [O31] |

#### 3.2.2 操作系统、自动化和安全分析

| 产品 | 工作原理 | 客户价值/场景 | 官网数据 |
|---|---|---|---|
| SR OS | 面向业务路由器的统一 NOS，提供 IP/MPLS、EVPN、QoS、遥测和高可用 | 电信、云、关键行业 WAN | 未披露价格 [O40] |
| SR Linux | 开放、模型驱动、流式遥测的 Linux NOS | 数据中心和自动化运维 | 未披露 [O41] |
| Event-Driven Automation (EDA) | Kubernetes 微服务；意图、数字孪生和事件驱动事务；支持多厂商 | AI 数据中心 fabric 的设计、校验、部署、变更 | 官网称运营工作量最高降低 40% [O42] |
| Network Services Platform (NSP) | 统一控制 IP、光和微波多厂商网络；路径计算、业务编排、保障闭环 | 运营商和大型企业广域网 | 全球 `1,000+` 运营商部署 [O43] |
| Deepfield Secure Genome | 对互联网端点/前缀做云和威胁分类，小时级更新 | 流量工程、DDoS 识别 | 覆盖 `5bn+` IPv4/IPv6 地址，`100+` ML 规则 [O44] |
| Deepfield Defender / Genome Shield | 秒级检测攻击并生成缓解策略，经 Nokia 或第三方路由器在网内清洗 | 运营商自防护或 DDoS-as-a-Service | 具体订阅和清洗成本未披露 [O45] |
| 7750 DMS | 专用缓解系统，将恶意流量在网络中丢弃/过滤 | 大规模 DDoS 防护 | 未披露 [O46] |

**分析判断。** EDA 与 NSP 不完全替代：EDA 聚焦数据中心 fabric 的快速、事务化变更；NSP 覆盖 IP/光/微波 WAN 的跨域服务编排。Deepfield 的优势在于把流量可见性和路由器内缓解结合，减少把全部流量牵引到独立清洗中心的需求，但实际节省取决于峰值攻击、链路和许可模型。

### 3.3 Optical Networks

#### 3.3.1 传输系统

光传输系统把客户侧以太网/OTN 信号映射到相干波长，经 ROADM、放大器和光纤传送；DSP 补偿色散和噪声，线路系统进行波长复用、路由与功率控制。[O60]

| 产品族 | 形态/能力 | 场景 | 价格成本 |
|---|---|---|---|
| 1830 PSS | PSS-4II/8/16II/32/HC；分组、OTN 与 WDM 传输/交换 | 城域到长途骨干 | 未披露 [O61] |
| 1830 GX | 数据中心互联平台；`100G-1.2T/波长`、`9.6T/架`、最高 `100T/纤` | AI/云 DCI、开放线路系统 | 未披露 [O62] |
| 1830 PSI-M | 模块化相干 DCI/传输 | 空间受限机房和开放光网络 | 未披露 [O63] |
| FlexILS / PSD / PSS-PSI-L | 开放光线路、放大、ROADM 和光层分界 | 多厂商相干光、城域/长途线路系统 | 未披露 [O64] |
| 1830 PSS-x | P-OTN 交换 | OTN 汇聚、传统业务迁移 | 未披露 [O65] |
| 1830 TPS / ONE | 时间敏感分组与光网络延伸 | 移动承载、工业和边缘 | 未披露 [O66] |
| 1830 XTM/XTC/XT、7090/7100/7300、mTera | Infinera 并购带来的城域、长途、海缆和 DCI 系列 | 既有 Infinera 客户及多代网络 | 官网仍列示；生命周期和迁移政策需逐项目确认 [O67] |

#### 3.3.2 相干光引擎、DSP 与器件

| 产品 | 原理与指标 | 典型场景 | 商业边界 |
|---|---|---|---|
| ICE6 / ICE7 | 高波特率相干光引擎，集成 DSP、光前端和系统算法 | 城域、长途、海缆 | 模块/系统报价未披露 [O68] |
| ICE-X 100/400 | 可插拔相干光；最大约 1,500km | 路由器直插、DCI、coherent routing | 未披露 [O69] |
| ICE-X 800 | 3nm CMOS；800G 超过 1,700km；QSFP-DD800/OSFP | IP-over-DWDM、AI 数据中心互联 | 未披露 [O70] |
| ICE-D | 面向数据中心内部的单片 InP PIC 光互联 | GPU/AI scale-out 网络 | 官网称连接功耗最高降低 75%；未披露量产单价 [O71] |
| PSE-V / PSE-6s | Nokia 自研相干 DSP/光子业务引擎 | 1830 系统的线路侧相干处理 | 不单独披露价格 [O72] |
| Tahoe 800G DSP | 3nm、200G-800G、最高 135GBaud | 商用相干模块 | B2B 芯片/模块价格未披露 [O73] |
| WA'A 400G DSP | 100/200/400G、最高 71GBaud | 边缘/城域可插拔相干光 | 未披露 [O74] |
| ICTR TROSA / CSTAR | 集成发射接收光子子组件 | 相干模块与系统集成 | 未披露 [O75] |

#### 3.3.3 光网络软件

- **WaveSuite**：覆盖服务开通、健康分析、带宽按需和网络运营；官网宣称网络运营成本最高降 56%、新服务运营成本最高降 90%。这些是用例/模型结果，不是 Nokia 分部成本披露。[O76]
- **Transcend Network Automation Suite**：Infinera 来源的多层网络规划、设计、控制和保障套件；收购后与 Nokia 光网络组合并存。[O77]
- **安全光网络/量子安全**：1830 SMS、加密线路和量子安全迁移方案保护传输中数据；成本取决于加密端点、密钥管理和升级范围，官网未披露。[O78]

## 4. Mobile Infrastructure

### 4.1 Core Software

核心网位于无线/固定接入与互联网、IMS、企业业务之间：鉴权并保存用户资料，建立会话，选择用户面路径，执行策略和计费，并向应用开放网络能力。Nokia 的 5G Core 支持 2G/3G/4G/5G、固定接入与 IMS 的统一演进。[O20]

| 产品线 | 主要产品 | 工作方式 | 客户/场景 | 价格 |
|---|---|---|---|---|
| 分组核心 | Cloud Packet Core、Cloud Mobile Gateway、Cloud Mobility Manager | 控制面处理注册/移动性/会话；用户面转发流量，支持分布式边缘部署 | 运营商 4G/5G SA、FWA、企业切片 | 未披露；容量/会话/节点相关 [O21] |
| 用户数据 | Subscriber Data Management、HSS、One-NDS、Shared Data Layer、AAA | 统一保存身份、订阅、鉴权和策略数据，供核心网功能实时调用 | 多制式用户融合、漫游、固移融合 | 未披露 [O22] |
| 语音/通信 | Cloud Native Communication Suite/IMS、SBC、TAS、VoLTE、VoWiFi、Vo5G | IMS 建立多媒体会话；SBC 控制边界；TAS 提供电话业务 | 关闭 2G/3G 语音、5G 语音、企业通信 | 未披露 [O23] |
| 变现 | Converged Charging、Policy Controller | 实时/离线计费与策略联动，按套餐、质量和事件控制服务 | 预付/后付、切片、API 和差异化连接 | 未披露 [O24] |
| 信令 | Cloud Signaling Director 等 | 在 Diameter/HTTP2 等信令域路由、保护和互通 | 漫游、跨代核心网、信令安全 | 未披露 [O25] |
| API 暴露 | Network Exposure Function (NEF) | 将位置、质量、号码验证等网络能力以受控 API 暴露 | 开发者、金融反诈、媒体、车联网、无人机 | 未披露 [O26] |
| 云运维 | Cloud Operations Manager | 生命周期管理、部署、升级、告警与资源编排 | 电信云核心网运维 | 未披露 [O27] |
| Core SaaS | 以上核心能力的托管订阅形态 | Nokia 负责预集成、上线、运营和维护，客户按需订阅 | 希望降低自建复杂度的运营商 | 订阅费率未披露 [O20] |

**分析判断。** 核心网软件的边际交付成本低于硬件，但电信级验证、云基础设施、跨代互通、数据主权和 24x7 SLA 形成较高实施与持续支持成本。官网没有按产品拆分 ARR、许可收入或毛利，不能据“云原生/SaaS”直接套用通用 SaaS 毛利。

### 4.2 Radio Networks

RAN 将终端无线信号经天线/射频单元转换为数字基带，再由基带执行调制编码、调度、MIMO 波束赋形和移动性相关处理；前传/中传/回传连接分布式站点与核心网。[O80]

| 产品族 | 产品/规格 | 工作方式和场景 | 成本/价格 |
|---|---|---|---|
| AirScale Baseband | 容量卡、控制与传输单元 | 多制式基带池化；软件升级支持 5G-Advanced/后续演进 | 按站点、容量和软件功能报价，未披露 [O81] |
| Macro RRH | Doksuri、Osprey Remote Radio Heads | 射频收发与功放靠近天线，降低馈线损耗；宏覆盖 | Doksuri 官网称能效提高 `>30%`、重量最高降 25% [O82] |
| Massive MIMO | Habrok、Osprey 32TRX/64TRX | 有源天线用多通道波束赋形提高覆盖与频谱效率 | 城市 5G 宏站；未披露价格 [O83] |
| Indoor/Small cells | Kolibri indoor/outdoor/strand、Shikra mmWave/RRH、Smart Node/femtocell | 低功率小覆盖补盲或室内容量；毫米波提供高容量短距覆盖 | 企业、家庭、街道、场馆；未披露 [O84] |
| IPAA+ | 无线与天线集成平台 | 在有限塔位/天面内整合多频段升级 | 城市宏站改造；未披露 [O80] |
| ReefShark | 自研基带 SoC | 加速 Layer 1/基带处理并改善功耗/尺寸 | AirScale 内部平台；不公开单卖价 [O85] |
| anyRAN | Cloud RAN、Open RAN、Cloud AI-RAN | 将基带功能部署到云平台，支持 Nokia/第三方硬件和 O-RAN 接口 | 运营商云化、供应商解耦、AI 与 RAN 共平台 | 集成成本高度依部署而定 [O86] |
| 安装系统 | AirScale installation system | 预连接/机械与数字化工具减少现场步骤 | 批量站点建设和改造 | 官网称安装时间最高减少 70% [O87] |

#### RAN 运维软件

- **MantaRay SMO**：跨开放/传统 RAN 的服务管理与编排，承载 rApps、配置、保障和生命周期管理。[O88]
- **MantaRay Network Management / SON**：集中网管和自组织网络，进行参数优化、邻区和容量管理。[O88]
- **MantaRay AutoPilot**：以数据、AI 和闭环策略自动处理拥塞、节能和性能问题；官网称可达 TM Forum Autonomous Networks Level 4。一个高负载案例中 cell utilization 改善 30%，不应外推到所有网络。[O89]

### 4.3 Technology Standards

该业务单元的“产品”主要不是网络设备，而是专利组合、标准贡献和可授权技术。价值链是：研发/标准化 -> 形成标准必要专利或实施专利 -> 与设备厂商双边许可或进入专利池 -> 收取许可费。[O01][O90]

#### 4.3.1 专利许可产品线

| 许可领域 | 被许可产品/客户 | 权利与工作方式 | 价格 |
|---|---|---|---|
| Mobile devices | 手机、平板和蜂窝终端厂商 | 许可 Nokia 2G-5G/后续蜂窝标准必要专利 | 合同费率未公开 [O91] |
| Automotive | 车厂、T1/连接模块供应商 | 车辆蜂窝连接相关 SEP，可经专利池或双边安排 | 未披露 [O92] |
| IoT | 消费/工业物联网设备商 | 按蜂窝连接标准和设备品类授权 | 未披露 [O93] |
| Consumer electronics | 电视、流媒体和联网消费设备商 | 视频、连接和多媒体专利 | 未披露 [O94] |
| Video services | 流媒体与视频服务提供商 | 视频编码/传输实施专利许可 | 未披露 [O95] |
| Gaming | 游戏设备、平台和服务商 | 视频、多媒体、低时延和连接相关专利 | 未披露 [O96] |

**官网事实。** Nokia 将标准必要专利许可解释为创新投入、标准贡献与许可回报构成的循环。[O97] **分析判断。** 该业务收入受续约时点、销量、诉讼和合同组合影响，不能用网络设备出货量解释；许可费不是 Nokia 替客户生产产品的成本。

#### 4.3.2 多媒体技术与开发组件

| 技术/产品 | 工作原理与参数 | 应用场景 | 商业状态 |
|---|---|---|---|
| IVAS codec | 3GPP 空间语音编解码；13.2-512kbps，算法时延 32-38ms；支持 mono/stereo/multichannel/object/SBA/MASA；IMS/VoLTE/VoNR，经 RTP 传音频和空间元数据 | 沉浸式通话、会议、XR、工业远程协作 | 标准技术；许可/SDK 价格未披露 [O98] |
| Immersive Voice platform | 麦克风输入经降噪和空间分析转 MASA，IVAS 编码传输，接收端用空间 AEC 和渲染重建声场 | 一对一/多人通话、会议、XR、任务关键通信 | 官网定位为 test/evaluation platform [O99] |
| Client SDK / Mixer SDK | 在终端采集、编码、渲染；服务端混合多方空间音频 | 设备厂商、通信应用和会议平台集成 | 未披露 [O99] |
| MASA / OMASA | Metadata-Assisted Spatial Audio 及开放实现，用元数据描述空间声场 | 低复杂度空间音频采集和传输 | 规范/实现许可边界见具体协议 [O100] |
| MPEG-I immersive audio | MPEG 沉浸式音频标准相关技术 | XR、广播、点播和互动媒体 | 未披露 [O101] |
| OZO Audio / OZO Playback | 终端空间音频采集、降噪、聚焦和回放算法 | 手机、相机、消费电子 | B2B 技术许可，费率未披露 [O102] |
| RXRM | Real-time eXtended Reality Multimedia，将多传感器 360/空间内容通过网络实时传输和远程呈现 | 工业监控、远程操作、赛事/媒体、公共安全 | 未披露 [O103] |
| Nokia 5G 360 Camera | 多摄像头、麦克风和 5G 上行的一体式工业相机，现场拼接/传输 360 内容 | 恶劣环境远程检查、态势感知、直播 | 未披露 [O104] |

## 5. Portfolio Businesses 与终止经营

### 5.1 Microwave Radio：Wavence

微波回传把基站/企业侧以太网信号转换为射频，经点到点天线在微波或 E-band 传输，再转回以太网/光口接入 IP/光网络。相较铺设新光纤，部署更快、地形适应性更强，但容量和可用性受频谱、距离、天线、降雨和视距影响。[O110]

| 产品线 | 产品/方式 | 场景与指标 | 状态/价格 |
|---|---|---|---|
| Microwave radio | UBT full-outdoor radio family | 室外一体化，避免波导损耗；可直连 5G 基站省去站点路由器 | Portfolio Businesses；未披露价格 [O110] |
| Urban E-band | Wavence E-band | 城市基站、企业和关键业务，最高 `20Gb/s` | 视降雨/距离设计；未披露 [O110] |
| Long-haul | 高功率/多频段 Wavence | 海岛、海上、山区、农村，官网称长距最高 `10Gb/s` | 未披露 [O110] |
| Microwave Service Switch | MSS family、MSS-400 | 从尾站到多方向、多频段干线聚合，提供分组交换、同步、保护和安全 | 未披露 [O110] |
| AI/automation | Wavence 内嵌流量/环境感知、动态功率、睡眠、预测维护和故障检测 | 节能和少人值守运维 | 官网称节能 25% [O110] |

客户案例包括秘鲁 HeyTu、迪拜 du、澳大利亚 PTA、北美关键通信服务商和铁路客户；这些证明部署类型，不代表所有客户的性能结果。[O110]

### 5.2 Site Implementation and Outside Plant

该业务负责站点实施和外线工程，工作通常包括勘察设计、许可/施工协调、站点安装集成、光纤外线建设、测试验收和维护。[O01] 它的收入更偏项目/服务，成本由当地人工、土建、材料、许可、地理密度和分包结构驱动。官网未找到独立产品清单、标准报价或单独利润数据；截至时点仍在 Portfolio Businesses 持续经营口径，战略去向待定。[O02]

### 5.3 已列终止经营的两项业务

| 业务 | 仍可见产品 | 2026-07-25 财务/交易状态 | 使用时注意 |
|---|---|---|---|
| Fixed Wireless Access CPE | FastMile Gateway 2/3/4/6/7/12、CBRS gateways；4G/5G Receivers 5G14-B/5G16-A/B/5G19-A/5G26-A/7；mmWave Receiver | Nokia 已同意出售给 Inseego，Q2 起列终止经营 [O02] | 官网产品页存在不等于 Nokia 长期保留该业务 |
| Enterprise Campus Edge | Digital Automation Cloud、MX Industrial Edge、private wireless、工业设备/应用生态 | Nokia 认为达成出售协议高度可能，Q2 起列终止经营 [O02] | 应与仍属核心分部的 IP/光/安全企业方案区分 |

FastMile 的代表性参数：Gateway 12 为 8Rx、最高 8dBi、Wi-Fi 7；Receiver 7 为 18dBi、四载波聚合、2.5G PoE；mmWave Receiver 为 26dBi、360 度视场，官网称在适当农村环境可超过 10km。[O111][O112][O113]

**财务事实。** 若 Q2 未将两项业务列为终止经营，季度净销售额会高 EUR 66m、可比经营利润会低 EUR 13m。[O02] 这不是两项业务完整收入/利润披露，不能据此计算年度规模或估值。

## 6. Nokia Defense

Nokia Defense 是独立孵化单元，以美国 Nokia Federal Solutions 为基础，为美国、芬兰及盟国提供基于 Nokia 固网和移动基础设施的 defense-grade 方案。[O01][O120]

### 6.1 网络方案

- **Tactical communications**：在人员、车辆和临时指挥点间自组/自愈网络，覆盖视距与超视距连接。[O121]
- **Private wireless for permanent installations**：在基地、船厂和仓储部署专用 4G/5G，承载语音、视频、传感器和自动化。[O122]
- **Mission-critical WAN / data center networking / optical LAN**：用 IP/MPLS、数据中心 fabric 和 PON 连接基地、云和用户。[O123]
- **Quantum-safe network solutions**：加密和迁移控制，用于长期敏感信息保护。[O124]

### 6.2 战术终端与无线电

| 产品 | 工作方式/规格摘要 | 场景 | 价格 |
|---|---|---|---|
| Banshee 4G Mobile Radio | 车载/移动 4G 战术蜂窝节点，快速形成宽带覆盖 | 车队、临时基地、应急和战场 | 未披露 [O125] |
| Banshee Flex Radio | 可携/可快速部署的战术宽带节点 | 任务编组和覆盖延伸 | 未披露 [O126] |
| Banshee Tactical Radio | 战术专网无线电，与终端和 IP 网络互通 | 受争议环境的语音/视频/数据 | 未披露 [O127] |
| Talon PUC | 2.4GHz ISM 中档 MANET；设备间自组、自愈；可桥接 Banshee、蜂窝、SATCOM/BLOS；典型续航最高 16h，radio 113.5g | 主网失效时保持手机、传感器、ATAK 等连接 | 官网称 low-cost，但无金额 [O128] |
| Mission-Safe Phone / Pro / Ultra | 加固 OS、加密存储、MIL-STD-810H、IP68；6.32 英寸；4500mAh/典型 1000 cycles；270g；4G/5G | 国防和公共安全的任务关键智能终端 | 官网称商业智能手机成本水平，无售价 [O129] |
| Biometric Monitoring System | 穿戴传感器采集生命体征并经战术网络回传 | 人员健康、热应激和任务态势 | 未披露 [O130] |

## 7. 跨域软件、安全、API 与服务

这些是官网 solution area，而非第三个主要财务分部；实际收入归属 Core Software、IP、Optical、Radio 或服务组织。

| 产品域 | 组件 | 工作方式与场景 | 来源 |
|---|---|---|---|
| Autonomous Networks Fabric | Fabric + AN Apps | 汇聚网络数据、模型和策略，应用执行闭环保障/优化 | [O140] |
| Digital Operations Center | Orchestration Center、Assurance Center、Unified Inventory | 以统一资源模型把订单、编排、库存、告警和保障连接起来 | [O141] |
| 切片/流程 | Core Slice Controller、RAN Slice Controller、FlowOne、Mediation、Customer Journey Orchestration | 跨核心/RAN 建切片，将订单转工作流，采集/转换使用数据并优化客户旅程 | [O142] |
| Network as Code | Network as Code platform、Network Exposure Platform、NEF | 将运营商能力转为开发者 API，执行鉴权、策略、计量和合作伙伴聚合 | [O143] |
| NetGuard XDR | Cybersecurity Dome、Certificate Lifecycle Manager、Certificate Manager、EDR、Identity Access Manager | 汇聚遥测检测响应，管理证书/身份/端点 | [O144] |
| Quantum-safe | 网络发现、加密、密钥和迁移方案 | 盘点密码资产并迁移到抗量子方案 | [O145] |
| 专业服务 | 设计、部署、优化、维护、托管、安全服务 | 降低客户集成和运维负担；按项目/SLA | [O146] |

## 8. 客户、工作场景与采购单元

| 客户群 | 主要问题 | 常见组合 |
|---|---|---|
| 电信运营商 | 接入升级、移动覆盖、核心云化、网络自动化、变现 | Lightspan/ONT + Altiplano；AirScale + Core + MantaRay；7750/NSP + 1830/WaveSuite |
| AI 与云提供商 | GPU 集群 fabric、数据中心内/间互联、高速网关、自动化 | 7220/7250 IXR + SR Linux/EDA；ICE-D；1830 GX/ICE-X；7750 SR |
| 关键行业 | 高可用 WAN、私网、低时延、旧协议迁移、安全 | 7705/7730/7750、光传输、Wavence、NetGuard、量子安全 |
| 国防/公共安全 | 主权供应、加固终端、自组网、受争议环境通信 | Banshee、Talon、Mission-Safe、私网、WAN/数据中心/光 LAN |
| 设备与服务厂商 | 实施蜂窝/视频/音频标准，避免专利侵权 | Mobile/Auto/IoT/Video 专利许可、IVAS/OZO SDK |

**分析判断。** Nokia 的竞争力在跨层组合和既有运营商入口；风险也来自组合复杂、集成周期长、客户资本开支和产品迁移。Infinera 产品并入后，同类光平台并存，客户需要核实具体 SKU 的生命周期、软件路线图与备件政策。

## 9. 风险、矛盾证据与待确认事项

1. **网页仍在线 vs. 财务终止经营**：FastMile 和 Enterprise Campus Edge 页面仍可访问，但官方财务公告已列终止经营；本手册以财务状态为准，同时保留产品事实。[O02]
2. **营销上限 vs. 可交付性能**：距离、容量、节能和运营成本下降均依配置和环境；未发现独立第三方验证。
3. **产品族不等于可下单 SKU**：官网常以 family/solution 命名，具体线卡、频段、区域认证和 EOS/EOL 状态需 RFQ 时确认。
4. **Infinera 重叠组合**：1830 与 7090/7100/7300/mTera 等页面并存，官网未在所有页面统一披露合并后的长期路线图。
5. **价格与单位经济性空白**：官网无目录价、折扣、BOM、安装人天或产品级毛利；任何精确估值需要合同、渠道报价或管理层进一步披露。
6. **Portfolio Businesses 去向**：Microwave Radio 与 Site Implementation/Outside Plant 的最终处置方向截至 2026-07-25 尚未公布。

## 10. 原始来源索引

### 公司结构与财务

- **[O01]** [2025-11-19 新战略与经营模式](https://www.nokia.com/about-us/news/releases/2025/11/19/nokia-announces-new-strategy-evolution-of-its-operating-model-new-long-term-financial-target-strategic-kpis-and-changes-to-its-group-leadership-team/)
- **[O02]** [Nokia Corporation Report for Q2 and Half Year 2026](https://www.nokia.com/newsroom/nokia-corporation-report-for-q2-and-half-year-2026/)
- **[O03]** [终止经营重列公告](https://www.nokia.com/newsroom/nokia-provides-recast-comparative-financial-information-reflecting-the-presentation-of-fixed-wireless-access-cpe-and-enterprise-campus-edge-businesses-as-discontinued-operations/)

### Fixed Networks

- **[O04]** [Lightspan FX](https://www.nokia.com/broadband-access/gigabit-fiber/lightspan-fx-fiber-olt/)；**[O05]** [Lightspan DF](https://www.nokia.com/broadband-access/gigabit-fiber/lightspan-df-fiber-olt/)；**[O06]** [Lightspan MF](https://www.nokia.com/broadband-access/gigabit-fiber/lightspan-mf-fiber-olt/)；**[O07]** [Lightspan SF-8M](https://www.nokia.com/broadband-access/gigabit-fiber/lightspan-sf-8m-sealed-fiber-olt/)
- **[O08]** [Fiber ONT](https://www.nokia.com/broadband-access/in-home-connectivity/fiber-ont/)；[25G ONT](https://www.nokia.com/broadband-access/in-home-connectivity/fiber-ont/25g-ont/)；[XS-2437X-B](https://www.nokia.com/broadband-access/in-home-connectivity/fiber-ont/ont-xs-2437x-b/)
- **[O09]** [Altiplano Access Controller](https://www.nokia.com/broadband-access/network-automation/altiplano-access-controller/)；**[O10]** [Altiplano Marketplace](https://www.nokia.com/broadband-access/network-automation/altiplano-marketplace/)；**[O11]** [Lightspan OS](https://www.nokia.com/broadband-access/network-automation/lightspan-operating-system/)
- **[O12]** [Corteca](https://www.nokia.com/broadband-access/in-home-connectivity/corteca/)；**[O13]** [Corteca Home Controller](https://www.nokia.com/broadband-access/in-home-connectivity/corteca/home-controller/)；**[O14]** [Home Wi-Fi](https://www.nokia.com/broadband-access/in-home-connectivity/home-wi-fi/)
- **[O15]** [Broadband access](https://www.nokia.com/broadband-access/)；**[O16]** [Aurelis Optical LAN](https://www.nokia.com/broadband-access/aurelis-optical-lan/)；**[O17]** [Broadband network services](https://www.nokia.com/broadband-access/services/)

### IP、数据中心与安全

- **[O30]** [IP Networks](https://www.nokia.com/ip-networks/)；**[O31]** [Data center fabric](https://www.nokia.com/data-center-networks/data-center-fabric/)
- **[O32]** [7750 SR](https://www.nokia.com/ip-networks/7750-service-router/)；**[O33]** [7730 SXR](https://www.nokia.com/ip-networks/7730-sxr/)；**[O34]** [7705 SAR](https://www.nokia.com/ip-networks/7705-service-aggregation-router/)；**[O35]** [7210 SAS](https://www.nokia.com/ip-networks/7210-service-access-system/)
- **[O36]** [7215 IXS](https://www.nokia.com/data-center-networks/data-center-fabric/7215-interconnect-system/)；**[O37]** [7220 IXR](https://www.nokia.com/data-center-networks/data-center-fabric/7220-interconnect-router/)；**[O38]** [7250 IXR](https://www.nokia.com/data-center-networks/data-center-fabric/7250-interconnect-router/)
- **[O39]** [FP5](https://www.nokia.com/ip-networks/fp-network-processor-technology/fp5/)；**[O40]** [SR OS](https://www.nokia.com/ip-networks/service-router-operating-system-nos/)；**[O41]** [SR Linux](https://www.nokia.com/ip-networks/service-router-linux-NOS/)
- **[O42]** [EDA](https://www.nokia.com/data-center-networks/data-center-fabric/event-driven-automation/)；**[O43]** [NSP](https://www.nokia.com/ip-networks/network-services-platform/)
- **[O44]** [Deepfield Genome](https://www.nokia.com/ip-networks/deepfield/genome/)；**[O45]** [Deepfield Defender](https://www.nokia.com/ip-networks/deepfield/defender/)；**[O46]** [7750 DMS](https://www.nokia.com/ip-networks/deepfield/7750-defender-mitigation-system/)

### Optical Networks

- **[O60]** [Optical Networks](https://www.nokia.com/optical-networks/)；**[O61]** [1830 PSS](https://www.nokia.com/optical-networks/1830-photonic-service-switch/)；**[O62]** [1830 GX](https://www.nokia.com/optical-networks/1830-global-express/)；**[O63]** [1830 PSI-M](https://www.nokia.com/optical-networks/1830-psi-m/)
- **[O64]** [FlexILS](https://www.nokia.com/optical-networks/1830-flexible-intelligent-line-system/)；[PSD](https://www.nokia.com/optical-networks/1830-photonic-service-demarcation/)；[PSS/PSI-L](https://www.nokia.com/optical-networks/1830-pss-psi-l-optical-line-systems/)
- **[O65]** [1830 PSS-x](https://www.nokia.com/optical-networks/1830-pss-x-p-otn-switching/)；**[O66]** [1830 TPS](https://www.nokia.com/optical-networks/1830-time-sensitive-packet-switch-tps/)；[1830 ONE](https://www.nokia.com/optical-networks/1830-optical-network-extender/)
- **[O67]** [1830 XTM](https://www.nokia.com/optical-networks/1830-express-transport-metro/)；**[O68]** [ICE6](https://www.nokia.com/optical-networks/ice6/)；[ICE7](https://www.nokia.com/optical-networks/ice7/)
- **[O69]** [ICE-X 100G/400G](https://www.nokia.com/optical-networks/icex-100g-400g-pluggable-coherent-optics/)；**[O70]** [ICE-X 800G](https://www.nokia.com/optical-networks/icex-800g-zr-zr-plus/)；**[O71]** [ICE-D](https://www.nokia.com/optical-networks/ice-d-intra-datacenter/)
- **[O72]** [PSE-6s](https://www.nokia.com/optical-networks/pse-6s/)；**[O73]** [Tahoe DSP](https://www.nokia.com/optical-networks/coherent-digital-signal-processors/)；**[O74]** [WA'A DSP](https://www.nokia.com/optical-networks/coherent-digital-signal-processors/)；**[O75]** [ICTR TROSA](https://www.nokia.com/optical-networks/ictr-trosa/)
- **[O76]** [WaveSuite](https://www.nokia.com/optical-networks/wavesuite/)；**[O77]** [Transcend](https://www.nokia.com/optical-networks/transcend-network-automation-suite/)；**[O78]** [1830 SMS](https://www.nokia.com/optical-networks/1830-security-management-server-sms/)

### Core、Radio 与 Technology Standards

- **[O20]** [Core Networks](https://www.nokia.com/core-networks/)；**[O21]** [Cloud Packet Core](https://www.nokia.com/core-networks/cloud-packet-core/)；**[O22]** [Subscriber Data Management](https://www.nokia.com/core-networks/subscriber-data-management/)
- **[O23]** [VoLTE/VoWiFi](https://www.nokia.com/core-networks/voice-over-lte-volte-and-voice-over-wifi-vowi-fi-core/)；[Vo5G](https://www.nokia.com/core-networks/voice-over-5g-vo5g-core/)；**[O24]** [Converged Charging](https://www.nokia.com/core-networks/converged-charging/)；[Policy](https://www.nokia.com/core-networks/policy-control-function/)
- **[O25]** [Cloud Signaling Director](https://www.nokia.com/core-networks/cloud-signaling-director/)；**[O26]** [NEF](https://www.nokia.com/core-networks/network-exposure-function/)；**[O27]** [Cloud Operations Manager](https://www.nokia.com/core-networks/cloud-operations-manager/)
- **[O80]** [Radio Access](https://www.nokia.com/radio-access/)；**[O81]** [AirScale baseband](https://www.nokia.com/radio-access/baseband/)；**[O82]** [Macro RRH](https://www.nokia.com/radio-access/macro-radios/)；**[O83]** [Massive MIMO](https://www.nokia.com/radio-access/macro-radios/massive-mimo/)
- **[O84]** [Small cells](https://www.nokia.com/radio-access/small-cells/)；**[O85]** [ReefShark](https://www.nokia.com/mobile-networks/ran/reefshark/)；**[O86]** [anyRAN](https://www.nokia.com/radio-access/anyran/)；**[O87]** [Services for mobile networks](https://www.nokia.com/mobile-networks/services/)
- **[O88]** [MantaRay SMO](https://www.nokia.com/mobile-networks/ran-operations/mantaray-smo/)；**[O89]** [MantaRay AutoPilot](https://www.nokia.com/mobile-networks/ran-operations/mantaray-autopilot/)
- **[O90]** [Licensing](https://www.nokia.com/licensing/)；**[O91]** [Mobile devices](https://www.nokia.com/licensing/patents/mobile-devices/)；**[O92]** [Automotive](https://www.nokia.com/licensing/patents/automotive/)；**[O93]** [IoT](https://www.nokia.com/licensing/patents/IoT/)
- **[O94]** [Consumer electronics](https://www.nokia.com/licensing/patents/consumer-electronics/)；**[O95]** [Video services](https://www.nokia.com/licensing/patents/video-services/)；**[O96]** [Gaming](https://www.nokia.com/licensing/patents/gaming/)；**[O97]** [SEP licensing explained](https://www.nokia.com/licensing/virtuous-circle-innovation/)
- **[O98]** [IVAS codec](https://www.nokia.com/multimedia/audio/technology-and-standards/ivas-codec/)；**[O99]** [Immersive Voice platform](https://www.nokia.com/multimedia/audio/immersive-voice/platform/)；**[O100]** [MASA/OMASA](https://www.nokia.com/multimedia/audio/technology-and-standards/masa-and-omasa/)
- **[O101]** [MPEG-I](https://www.nokia.com/multimedia/audio/technology-and-standards/mpeg-i-immersive-audio/)；**[O102]** [OZO](https://www.nokia.com/multimedia/audio/technology-and-standards/ozo-audio-ozo-playback/)；**[O103]** [RXRM](https://www.nokia.com/multimedia/rxrm/)；**[O104]** [5G 360 Camera](https://www.nokia.com/multimedia/rxrm/5g-360-camera/)

### Portfolio、Defense 与跨域平台

- **[O110]** [Wavence Microwave Transport](https://www.nokia.com/microwave-transport/)；**[O111]** [FastMile Gateway 12](https://www.nokia.com/broadband-access/in-home-connectivity/fastmile-fwa/5g-gateway-12/)；**[O112]** [FastMile Receiver 7](https://www.nokia.com/broadband-access/in-home-connectivity/fastmile-fwa/5g-receiver-7/)；**[O113]** [FastMile mmWave](https://www.nokia.com/broadband-access/in-home-connectivity/fastmile-fwa/5g-mmwave-fwa/)
- **[O120]** [Nokia Defense](https://www.nokia.com/defense/)；**[O121]** [Tactical communications](https://www.nokia.com/defense/tactical-communications-solutions/)；**[O122]** [Permanent private wireless](https://www.nokia.com/defense/private-wireless-communications-for-permanent-installations/)
- **[O123]** [Mission-critical WAN](https://www.nokia.com/defense/mission-critical-wan-for-defense/)；[Data center networking for defense](https://www.nokia.com/defense/data-center-networking-for-defense/)；[Optical LAN for defense](https://www.nokia.com/defense/optical-lan-for-defense/)；**[O124]** [Quantum-safe defense](https://www.nokia.com/defense/quantum-safe-network-solutions-for-defense/)
- **[O125]** [Banshee 4G Mobile Radio](https://www.nokia.com/defense/tactical-communications-solutions/banshee-4g-mobile-radio/)；**[O126]** [Banshee Flex](https://www.nokia.com/defense/tactical-communications-solutions/banshee-flex-radio/)；**[O127]** [Banshee Tactical](https://www.nokia.com/defense/tactical-communications-solutions/banshee-tactical-radio/)
- **[O128]** [Talon PUC](https://www.nokia.com/defense/tactical-communications-solutions/talon-puc/)；**[O129]** [Mission-Safe Phone](https://www.nokia.com/defense/tactical-communications-solutions/mission-safe-phone/)；**[O130]** [Biometric Monitoring](https://www.nokia.com/defense/tactical-communications-solutions/biometric-monitoring-system/)
- **[O140]** [Autonomous Networks Fabric](https://www.nokia.com/autonomous-networks/fabric/)；**[O141]** [Digital Operations Center](https://www.nokia.com/autonomous-networks/digital-operations-center/)；**[O142]** [Autonomous Networks](https://www.nokia.com/autonomous-networks/)
- **[O143]** [Network as Code](https://www.nokia.com/programmable-networks/network-as-code/)；**[O144]** [NetGuard XDR](https://www.nokia.com/cybersecurity/xdr/)；**[O145]** [Quantum-safe networks](https://www.nokia.com/industries/quantum-safe-networks/)；**[O146]** [Services for mobile networks](https://www.nokia.com/mobile-networks/services/)

## 11. 数据伴随文件

可筛选产品目录见 [`data/curated/companies/US/NOK-nokia/nokia-product-catalog-2026-07-25.csv`](../../../../data/curated/companies/US/NOK-nokia/nokia-product-catalog-2026-07-25.csv)。CSV 每行保留分部、业务单元、产品线、产品、状态、原理/形态、场景、客户、关键参数、价格边界和原始 URL。
