资料截至 2026-11-05，文字修订于 2026-11-06。金额均为美元，财年与自然年按各项披露注明。

# 核心投资结论

**将 AI 需求转化为利润和现金的确定性，微软领先，AWS 与谷歌紧随其后，甲骨文更依赖项目兑现。** 微软既能卖算力，又能向原有软件客户收取 AI 费用，集团现金对扩建的覆盖也最强。AWS 已有规模化云利润，但亚马逊的建设与客户融资支出拖累现金回收。谷歌的集团现金覆盖优于亚马逊，TPU 与 Gemini 也提供降本空间，扩建和系统备货却同时占款。甲骨文已有项目毛利，后续现金改善最依赖按期验收、客户付款和建设节奏。上述判断衡量经营兑现能力，七家公司尚无可比的 AI 独立现金流披露。[^cross-invest-msft][^csp-cash][^cross-invest-goog][^cross-invest-orcl]

**三家新云中，CoreWeave 向专业 AI 云发展的商业进展最清晰，但平台化尚未证明能提高股东回报。** 其配套服务已经收费，CoreWeave、Nebius 的部分集群运营也获独立评测支持。产品增加并未消除设备折旧与融资负担，也不能直接带来 CSP 的客户黏性。Nebius 的短约高价最依赖供给紧张，IREN 的机房复用价值则取决于改造成本与后续客源。现阶段可认可集群运营和通电机房的价值，软件带动算力续约、轻资产扩张及供给宽松后的持续高回报仍待验证。[^neo-crwv-q2][^neo-crwv-call][^neo-clustermax][^neo-crwv-forge][^neo-nbis-q2][^neo-iren]

**若 2027–2028 年供给按计划释放，优势将从“提前拿到算力”转向“持续降低任务成本、获得稳定用量”。** 2027 年更可能先出现标准推理和小规模训练降价，Nebius 无保底短约先受冲击，IREN 未锁客新增设备更易同时遇到降价与闲置。到 2028 年，CoreWeave 进入续租的旧集群、甲骨文依赖单客的专用园区更需检验新价格下的回收能力。已验收保量合同能缓冲履约期内的压力，前沿训练与指定地区推理仍可能局部紧缺。[^neo-nbis-q2][^btl-iren-ramp][^btl-crwv-coverage][^plat-orcl-project]

**更持久的利润基础仍在微软、AWS 的客户与应用关系，以及谷歌在适配负载上的芯片和模型能力。** 低价算力可以被替代，企业的数据、权限与业务流程更难迁移。ASIC 的效率收益只有在单位成本降幅超过售价降幅、产能保持利用率时，才能成为持续利润。新云则必须靠更好的集群运营或更低的机房复用成本留住客户，并在续约降价后仍能覆盖运维、偿债和必要的设备更新支出。[^cross-msft-seats][^csp-amzn-ai][^asic-goog-cost][^neo-clustermax][^csp-project-debt]

# 亚马逊

AWS 的 AI 业务从出租计算资源延伸到模型开发和调用。EC2 提供服务器，SageMaker AI 托管模型开发，Bedrock 把模型能力直接交给企业应用。自研芯片贯穿这些服务，其回报取决于客户用量和单位服务成本。

### 计算基础设施与自研芯片

#### EC2 与 Graviton

EC2 以云服务器实例提供计算容量，覆盖 Intel、AMD 和 Arm 架构，支持网站、数据库、高性能计算和 AI。客户按需使用时按秒或小时付费，通过 Savings Plans 承诺一定期限内的支出可换取折扣，Spot 则低价销售可中断的闲置容量。三种方式分别满足灵活使用、长期采购和容忍中断的需求，也帮助 AWS 提高收入可见度和容量利用率。[EC2 产品说明](https://aws.amazon.com/ec2/)

Graviton 是 AWS 自研的 Arm 通用 CPU，适用于兼容 Arm 的网站、数据库和数据处理等负载。它围绕 AWS 的服务器、网络和软件设计，通过更低的服务成本和 EC2 使用费回收研发投入，客户目前主要通过 AWS 云服务使用。[Graviton 产品说明](https://aws.amazon.com/cn/ec2/graviton/)

EC2 的“系列”区分用途与硬件，“规格”规定芯片、内存和网络配置，“实例”则是按规格启动的服务器。例如，`m8g.4xlarge` 表示 M 通用系列、第八代、Graviton CPU 和相应规格大小。常见后缀 `i`、`a` 分别代表 Intel、AMD，`d` 代表本地存储，`n` 代表网络及 EBS 优化，`b` 代表 EBS 优化，`z` 代表高主频，`metal` 代表裸金属。

| AWS 指南类别 | 主要系列 | 系列分支数 | 具体规格数 |
|---|---|---:|---:|
| 通用型 | M、T、Mac | 49 | 399 |
| 计算优化型 | C | 31 | 312 |
| 内存优化型 | R、X、U、Z | 56 | 443 |
| 存储优化型 | I、Im、Is、D、H | 14 | 105 |
| 加速计算型 | P、G、Gr、Trn、Inf、F、DL、VT | 29 | 92 |
| 高性能计算型 | Hpc | 5 | 10 |
| 上一代，单列 | A1、M1–M4、C1/C3/C4 等 | 14 | 55 |
| **按唯一名称去重合计** | | **198** | **1,416** |

统计依据为 AWS 各类实例指南，反映产品配置数量，各地区实际供应另受配额与容量限制。[通用型](https://docs.aws.amazon.com/ec2/latest/instancetypes/gp.html)、[计算优化型](https://docs.aws.amazon.com/ec2/latest/instancetypes/co.html)、[内存优化型](https://docs.aws.amazon.com/ec2/latest/instancetypes/mo.html)、[存储优化型](https://docs.aws.amazon.com/ec2/latest/instancetypes/so.html)、[加速计算型](https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html)、[高性能计算型](https://docs.aws.amazon.com/ec2/latest/instancetypes/hpc.html)、[上一代](https://docs.aws.amazon.com/ec2/latest/instancetypes/pg.html)

#### Trainium 与 Neuron

Trainium 是 AWS 面向训练和推理的 AI 加速器。客户可直接租用相关实例，也可通过 Bedrock 使用其算力。Anthropic、Decart、poolside、Databricks、Ricoh 等已有应用。各代官方性能指标的对照平台不同，不能据此推算 AWS 的统一成本降幅。[Trainium 产品说明](https://aws.amazon.com/cn/ai/machine-learning/trainium/)

| 代际 | 主要规格与官方比较 | 部署证据 |
|---|---|---|
| **Trainium1** | Trn1 训练成本较同类 EC2 实例最多低 50%。`trn1.2xlarge` 配 1 颗芯片，`trn1.32xlarge`、`trn1n.32xlarge` 各配 16 颗 | Capacity Blocks 仍支持 `trn1.32xlarge`，历史客户包括 Stockmark、理光。全球部署量未披露 |
| **Trainium2** | 芯片性能为初代 4 倍。Trn2 较 GPU 实例 P5e/P5en 性价比高 30%–40%。`trn2.3xlarge` 配 1 颗，`trn2.48xlarge`、`trn2u.48xlarge` 各配 16 颗，UltraServer 通过 NeuronLink 可连 64 颗 | 2026 年 2 月披露 140 万颗已“landed”，其中 Rainier 运行集群超过 50 万颗，供 Anthropic 训练 Claude。Trainium2 也承担 Bedrock 多数推理 |
| **Trainium3** | 3 纳米，单芯片 2.52 PFLOPS FP8、144 GB HBM3e、4.9 TB/s 内存带宽，分别约为 Trainium2 的 2 倍、1.5 倍和 1.7 倍。Gen1/Gen2 UltraServer 分别配 64/144 颗。相较 Trn2 UltraServer，最高性能、内存带宽和能效分别为约 4.4 倍、3.9 倍和超过 4 倍 | 2026 年 2 月已承担生产任务，8 月扩展至伦敦新增可用区。Uber 开始试验性训练部分模型。全球部署量未披露 |

上述“landed”不能全部视为已投入客户生产。系统规格也不代表全网装机量。Trainium3 支持 MXFP8、MXFP4 等格式，改善内存和计算配比，并针对密集型与专家并行负载优化，面向多模态、推理和视频任务。[Trn1 规格及案例](https://aws.amazon.com/ec2/instance-types/trn1/)、[Trn2 规格](https://aws.amazon.com/ec2/instance-types/trn2/)、[Trn3 架构](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/about-neuron/arch/neuron-hardware/trn3-arch.html)、[Capacity Blocks](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-capacity-blocks.html)、[Amazon 2025Q4 公告](https://ir.aboutamazon.com/news-release/news-release-details/2026/Amazon-com-Announces-Fourth-Quarter-Results/)、[伦敦扩容](https://aws.amazon.com/about-aws/whats-new/2026/08/aws-new-availability-zone-europe/)、[Uber 合作](https://press.aboutamazon.com/aws/2026/4/uber-scales-on-aws-to-help-power-millions-of-daily-trips-and-train-its-ai-models)

Neuron 是 Trainium 和 Inferentia 的配套软件栈，负责模型编译、训练推理、调优和监控。芯片的性能需要通过这套工具转化为实际任务效率，软件适配也影响客户迁移意愿。[Neuron 产品说明](https://aws.amazon.com/cn/ai/machine-learning/neuron/)

### 模型开发与调用

![AWS AI 服务架构](image-1.png)

| 服务 | 客户控制的范围 | 商业用途 |
|---|---|---|
| EC2 | 自行部署程序和训练、推理环境 | 按计算及配套资源使用付费 |
| SageMaker AI | 保留模型开发与定制，由 AWS 托管训练、部署等环节 | 把实验模型推进到生产，按使用的资源和服务付费 |
| Bedrock | 选择托管模型，接入企业数据并构建 Agent，也支持部分模型定制 | 按模型用量或预留吞吐购买能力，底层服务由 AWS 管理 |

SageMaker AI 和 Bedrock 的功能有所重叠，选择主要取决于客户希望控制多深的模型开发过程。企业可在本地发起 SageMaker 训练，也可从本地或 EC2 应用调用 Bedrock。AWS 因而既能收取底层资源费，又能从模型调用及配套数据服务获得收入。[^cross-aws-models]

![AWS 模型开发与应用服务](image-2.png)

### 增长目标与兑现条件

管理层在 2026Q3 提出，AWS 未来五至十年有望达到万亿美元年收入，并预计 2027、2028 年收入各增长超过 40%。这是管理层展望。兑现既要靠新集群交付，也要靠客户持续消耗算力，集团资本开支和订单规模不能直接换算为当期收入。[^btl-aws-q3]

# 微软

Azure 出售 GPU 服务器、模型调用和配套云服务，Microsoft 365 Copilot、GitHub Copilot 则把算力变成办公与开发软件，收入归入 Microsoft 365 商业云。**微软可以同时赚取资源费和软件费，后者的推理成本由微软承担。**[^plat-msft-scope]

### 计算基础设施

Azure 通用 VM 提供 Intel、AMD 和自研 Arm CPU。GPU 产品中，NC 面向推理和较小训练，ND 面向跨机通信密集的训练与推理，NV 主要服务图形和虚拟桌面。[^plat-msft-vm]

| 代表系列 | 单 VM 配置 | 适用任务 |
|---|---|---|
| NCads H100 v5 | 1 或 2 颗 H100 NVL | 从单卡起租，适合推理和较小训练 |
| ND H100 v5 | 8 颗 H100 | 机内 NVLink，跨机每 GPU 配 400 Gbps InfiniBand，支持大型训练 |
| ND MI300X v5 | 8 颗 AMD MI300X | 大显存方案，需要适配 AMD 软件栈 |
| ND GB300 v6 | 4 颗 B300、2 颗 Grace CPU | 切自 GB300 NVL72 机架，面向长上下文和高吞吐推理 |

以上为实例配置，实际采购受地区、配额和容量约束。机架总卡数与单台 VM 的卡数须分别统计。[^plat-msft-vm]

客户可按需购买，以 Reserved VM Instances 或 Savings Plan 换取适用的用量折扣，或用 Spot 承接可中断任务。折扣承诺本身不保证供应。支持 On-demand Capacity Reservation 的规格可在指定位置锁容量，闲置时仍须付费。[^plat-msft-buy]

Fairwater 把高密度机架、液冷与低延迟网络一起设计，减少跨机训练中的通信等待和故障损失。集群交付能力由供电、散热、网络和运维共同决定，GPU 数量只是其中一环。[^plat-msft-fairwater]

### 自研芯片与模型平台

| 产品 | 用途与商业化进展 |
|---|---|
| Cobalt 100 | Arm 通用 CPU，2024 年 10 月商用。2026 年 6 月披露覆盖 32 个区域，客户包括 Databricks、Snowflake |
| Cobalt 200 | 下一代 Arm CPU。Build 2026 披露部署覆盖十多个区域，面向客户的 VM 当时仍在预览 |
| 初代 Maia | 2023 年发布，面向模型训练和推理，未披露交付量 |
| Maia 200 | 推理加速器，配 216 GB HBM3e。已在爱荷华、亚利桑那州投产，2026 年 10 月披露承接 Copilot 等生产负载，计划年底前接入 GitHub Copilot 和 Foundry |
| Maia 300 | 计划 2027 年投产，目标为同等电力下比领先 GPU 系统多生成 40% 的 token |

产品状态和性能来自微软披露，Maia 全球装机量及独立收入未公布。Cobalt 通过 VM 直接收费，Maia 目前主要用于微软托管模型，配套 PyTorch 接口、Triton 编译器和优化组件。Maia 200 发布时称每美元性能较当时机队最新硬件高 30%，实际利润仍取决于迁移用量、适配费用、折旧和电费。[^plat-msft-silicon][^plat-msft-quarter]

| 客户需求 | 服务 | 收费方式 |
|---|---|---|
| 自建训练或推理环境 | Azure VM、AKS | 计算、磁盘、网络等资源费 |
| 训练、微调和部署自有模型 | Azure Machine Learning | 集群、托管端点及配套资源费 |
| 调用模型、接入数据并部署 Agent | Microsoft Foundry | 模型用量、预留处理能力和工具费 |
| 员工办公或编程 | Microsoft 365 Copilot、GitHub Copilot | 软件许可及适用用量费 |

客户从自建环境转向托管服务后，可减少模型部署和运维工作。Foundry 支持多家模型，切换模型时仍可保留 Azure 的数据连接、权限与部署环境。FY2027Q1 Foundry 客户超过 12 万家，收入为上年同期三倍以上，收入额和利润率未单列。[^plat-msft-platform][^plat-msft-quarter]

Foundry 按量部署通常按输入、输出 token 计费，微软降低单位推理成本即可改善毛利。支持 PTU 的模型也可预留吞吐，客户按预留单位和时间付费，部分闲置风险由客户承担，微软仍须提供约定性能。各模型单位成本未披露。[^plat-msft-platform]

### 规模、投入和利润

2026 年 9 月季 Azure 收入 331.65 亿美元，同比增长 48%，涵盖 GPU 和非 GPU 业务。集团商业剩余履约义务为 6,770 亿美元，约三成预计一年内确认。OpenAI 同时是算力客户和模型供应方，2026 年 4 月修订的协议保留 Azure 为主要云伙伴，也允许 OpenAI 使用其他云，订单增长仍伴随多云竞争。[^plat-msft-scope][^plat-msft-openai]

当季集团资本开支 452 亿美元，约四分之三为 CPU、GPU 等短寿命资产，其中现金购建固定资产 394 亿美元，其余包含新增融资租赁等。设备交付将推高后续折旧，交付推迟则延后收入。同期 Microsoft Cloud 毛利率降至 66%，但 Azure 产品毛利改善。整体下降部分来自毛利较低的 Azure 占比上升，无法据此判断 GPU、Foundry 或 Copilot 各自的盈利变化。[^plat-msft-quarter]

# 谷歌

Google Cloud 以 GCP 为主，兼有 Workspace 和 TPU 系统销售。**谷歌既能出租自营算力，也能向客户出售整套 TPU 系统，再通过 Gemini 获得模型与应用收入。** 出租看利用率，卖系统看备货、交付和回款，两者对现金的占用不同。[^plat-goog-10q][^btl-goog-q3]

### 计算基础设施与 TPU

Compute Engine 提供 Intel、AMD 和谷歌自研 Arm CPU，Axion 已用于 C4A。模型计算交给加速器后，数据准备、应用后端和调度仍需要 CPU，Axion 可通过改善这些负载的成本直接获得 VM 收入。[^plat-goog-compute]

| 代表规格 | 配置与用途 |
|---|---|
| `a3-highgpu-8g` | 8 颗 H100，适合已有 CUDA 软件栈的训练与推理 |
| `a4-highgpu-8g` | 8 颗 B200，面向更新一代 AI 负载 |
| `a4x-maxgpu-4g-metal` | 4 颗 B300 配 Grace CPU，GB300 裸金属规格 |
| Cloud TPU | 从少量芯片到大型 TPU slice，以兼容框架分布式运行 |

跨机任务还须匹配网络、存储和所在区域的容量。除按需、承诺用量和 Spot 外，Flex-start 允许任务等到所需 GPU 或 TPU 凑齐后启动。客户接受等待及相应运行限制，谷歌则能更灵活地填补容量空档。需要确定开工时间的任务可选择适用的预约产品。[^plat-goog-compute][^plat-goog-buy][^plat-goog-tpu]

TPU 既服务自家模型，也向外部客户开放。AI Hypercomputer 将加速器、互连、存储和调度整合，兼容 TPU 与 NVIDIA 方案。客户可用 JAX 或 PyTorch/XLA 接入 TPU，长期、稳定的适配负载更容易摊薄迁移和维护成本。[^plat-goog-tpu]

| TPU 代际 | 规格 | 商业化状态 |
|---|---|---|
| v5p | 每芯片 95 GiB HBM，单 Pod 标称 8,960 颗 | 已商用 |
| v6e Trillium | 每芯片 32 GiB HBM，单 Pod 标称 256 颗 | 已商用，覆盖训练与推理 |
| TPU7x Ironwood | 每芯片 192 GiB HBM，单 Pod 标称 9,216 颗 | 已商用，面向大型训练与推理 |
| TPU 8t、8i | 8t 面向预训练，单 Superpod 设计 9,600 颗，8i 侧重后训练与低延迟推理 | 已发布，产品页列为即将推出 |

Pod 规模属于系统规格，全球各代投产量未披露。Alphabet 在 2026Q3 称已有近 100 家 TPU 客户，Apple 正用最新一代 TPU 扩大预训练，Anthropic 通过谷歌及 Broadcom 获取 TPU。各客户的云租用与系统采购量未拆分。[^plat-goog-tpu][^btl-goog-q3]

### 模型平台与企业应用

| 客户需求 | 服务 | 收费方式 |
|---|---|---|
| 自行管理训练和推理 | Compute Engine、Cloud TPU、GKE | 计算、存储和网络费 |
| 托管训练、定制和部署 | 由 Vertex AI 扩展的 Gemini Enterprise Agent Platform | 训练、模型托管和运行资源费 |
| 调用模型、构建 Agent | 平台内 Gemini 等模型及 Agent 工具 | 模型用量、预留吞吐和工具费 |
| 员工直接使用 AI | Gemini Enterprise 员工端、Workspace | 许可、订阅及适用超额用量费 |

企业既可在 TPU 上运行自有模型，也可直接调用 Gemini。Agent 查询资料、保留状态和执行任务，还会带来搜索、数据库、存储与计算需求。谷歌已观察到这些配套消费，但未单列增量收入，不能把客户总支出增长全部归于模型调用。[^plat-goog-platform][^plat-goog-enterprise][^btl-goog-q3]

### TPU 系统销售与现金回收

自营算力需先购设备、建机房，投产后折旧，靠租价、利用率和运行效率回收。系统外售则把算力、存储、网络和软件一起交付，合同进入积压订单后先备货，再交付开票收款。2026Q3 备货已占用经营现金，系统硬件成本也推高集团营业成本。[^btl-goog-q3]

当季 Google Cloud 收入约 307 亿美元，同比增长 103%，营业利润率约 36.2%。GCP 是主要增长来源，TPU 系统销售已有明显贡献，管理层预计 2027 年进一步放量。公司未单列系统销售额、毛利或 TPU 出租利润，Cloud 利润率还受 Workspace 等业务影响。[^plat-goog-10q][^btl-goog-q3]

谷歌同时向第三方购买过渡算力，2026Q3 末开始上线，当季利润拖累尚小。自研芯片的降本效果仍受机房交付约束，自营产能接替外购容量越晚，支付给外部供应商的成本持续越久。[^btl-goog-q3]

# 甲骨文

甲骨文以 OCI 大集群争取模型公司和企业的算力订单，以数据库承接客户既有数据和应用需求。前者需要提前投入设备、机房和电力，后者可沿用企业原有架构，并通过跨云部署扩大销售。[^plat-orcl-delivery][^plat-orcl-data]

### 计算基础设施与集群交付

OCI 通用计算采用 Intel、AMD 和 Ampere Arm CPU，AI 集群主要使用 NVIDIA、AMD 加速器。Ampere 在这里是外部 CPU 供应商。甲骨文负责将芯片、网络、调度和运维整合成可交付容量。[^plat-orcl-shapes]

| 代表规格 | 每实例配置与用途 |
|---|---|
| `VM.GPU.A10.1` | 1 颗 A10，服务小规模推理和图形 |
| `BM.GPU.H100.8` | 8 颗 H100，可通过 RDMA 扩展训练 |
| `BM.GPU.B200.8` | 8 颗 B200，面向大型训练与推理 |
| `BM.GPU.GB300.4` | 4 颗 B300 配 Grace CPU，来自 Grace Blackwell 机架 |
| `BM.GPU.MI300X.8` | 8 颗 MI300X，适合兼容 AMD 软件栈的任务 |

VM 是虚拟机，BM 是客户独占物理服务器的裸金属实例。Supercluster 将多个裸金属节点通过 RDMA 相连，减少跨机通信等待。Blackwell Supercluster 公布的最高 131,072 颗 GPU 属于设计上限。[^plat-orcl-shapes][^plat-orcl-supercluster]

普通实例按用量购买，支持预约的规格在未使用时按常规价格的 85% 收费，启用后收全价。大型 AI 集群另签多年合同，约定容量、交付、验收和付款，公开零售价不能代表大客户成交条件。[^plat-orcl-buy][^plat-orcl-project]

OpenAI 已在 Abilene 使用甲骨文首批 GB200 机架训练和推理，双方另约定开发最多 4.5 GW 新增容量，仍须分期建设。FY2027Q1（截至 2026 年 8 月），甲骨文交付 850 MW 新增数据中心容量，自上一财季末向 AI 云客户交付逾 30 万颗 GPU。当季基础设施云收入 74 亿美元，同比增长 121%，新签 AI 云合同超过 300 亿美元。集团剩余履约义务 6,640 亿美元，约 13% 预计一年内确认。各项目利用率和单卡成交价未披露。[^plat-orcl-stargate][^plat-orcl-delivery][^plat-orcl-10q]

### 模型服务与跨云数据库

| 客户需求 | 服务 | 收费方式 |
|---|---|---|
| 自行训练和推理 | OCI Compute、Supercluster，可配 OKE 或 Slurm | 实例、专用容量及存储网络费 |
| 托管训练、微调和部署 | OCI Data Science | 训练任务与模型端点资源费 |
| 调用模型、构建 Agent | OCI Enterprise AI | 按字符或 token 等计费，也可按时间购买专用 AI 集群 |
| 检索企业数据、接入业务流程 | Oracle AI Database、AI Data Platform、Fusion AI Agent Studio | 数据库、数据处理和应用服务费 |

客户可从按量调用模型起步，需要稳定吞吐或微调时，再购买 Dedicated AI Clusters。模型调用的收入与毛利未单列。[^plat-orcl-models]

跨云数据库降低了客户购买 Oracle 服务的迁移成本。例如，Oracle AI Database@AWS 将 Exadata 放入指定 AWS 数据中心，客户通过 Marketplace 采购，符合条件的支出可计入 AWS 消费承诺。Azure、Google Cloud 也有同类服务。企业可保留原云应用，在附近用 Oracle 处理数据和向量检索，甲骨文因此无需先争取整套应用迁移。跨云分成和独立利润率未披露。[^plat-orcl-data]

AI Data Platform 与 Fusion AI Agent Studio 将 Agent 接入企业权限和财务、人力等流程，带来数据库、数据处理及软件销售机会，相关 AI 增量收入尚未拆分。[^plat-orcl-apps]

### 项目利润与资金安排

2026 年投资者日的 **1 GW、平均五年合同**示例，在签约后第二季度开始投入，第四季度首次交付，第八季度全部交付。公司称大型 AI 基础设施合同采用成本加成方式，实际条款与收益仍随项目变化。[^plat-orcl-project]

| 投入方式 | 前两年资本开支 | 满产年化收入 | 资金安排 |
|---|---:|---:|---|
| 甲骨文自筹 | 约 370 亿美元 | 约 160 亿美元 | 设备支出集中在前期 |
| 供应商融资 | 约 180 亿美元 | 约 160 亿美元 | 分期支付，资本开支含同期融资付款 |
| 客户自带硬件 | 约 60 亿美元 | 约 110 亿美元 | 甲骨文提供机房、集群技术和运维，设备投入及对应收入减少 |

自筹示例满产毛利率约 35%，已计折旧。公司所称约 28% 的 ROI，以年度税后经营利润加折旧除以累计资本开支，近似年度现金回收率，含设备本金回收，且未计土地和建筑购置。作为实际经营证据，甲骨文另披露 FY2026Q3 新交付 AI 容量毛利率为 32%，仅适用于当季该批容量。[^plat-orcl-project][^csp-oracle-ai]

**设备由谁购买、何时付款，直接决定甲骨文的前期现金缺口。** 预付款先改善现金，收入仍随服务交付确认。供应商融资推迟付款，客户自带硬件则同时缩小投入和收费范围。FY2027Q1 集团经营现金流约 231 亿美元，现金资本开支约 285 亿美元，说明项目产生毛利后，持续建设仍可能消耗更多现金。[^plat-orcl-10q][^csp-oracle-funding]

# 四家 CSP 横向对比

四家都能出租服务器、托管模型开发和提供推理服务，但优势落点不同。训练客户重视任务完工时间和总成本，推理客户还要比较模型质量、响应速度与数据接入。**微软最善于通过既有软件客户收取 AI 费用，AWS 的优势在云服务与自研芯片的规模，谷歌覆盖芯片、模型和系统销售，甲骨文则突出专用大集群与数据库。**

### 训练、推理和企业 AI 的竞争力

#### 大模型训练

AWS 和谷歌已将自研芯片用于前沿模型训练。Anthropic 的 Rainier 集群使用超过 50 万颗 Trainium2，证明 AWS 能以自研芯片支撑大规模真实任务，但训练收入和成本未单列，2027 年底走向云外仍是计划。谷歌除训练 Gemini 外，已有 Apple、Anthropic 等 TPU 客户，系统销售也已贡献收入。谷歌的变现路径更广，同时承担备货占款，训练与推理各自的收入、利润均未拆分。两家已证明外部客户愿意采用自研芯片，尚需验证跨客户推广后的实际成本与回报。[^cross-aws-rainier][^cross-aws-chip-q3][^btl-goog-q3][^cross-goog-orcl-tpu]

微软和甲骨文的直接证据集中在 GPU 大集群交付。微软 Fairwater 提前六周上线，带动收入提前确认，FY2027Q1 主要区域 GB300 从到货到上线的时间又环比缩短约 20%。甲骨文按大客户合同交付专用集群，管理层称 GPT-6 Astra 在 Abilene 训练。OCI 基础设施收入增长 121%，集团自由现金流仍为负，反映收入放量与持续建设同时发生。两家均未披露可比的单个训练项目回报。[^cross-msft-fairwater][^plat-msft-quarter][^cross-orcl-call][^plat-orcl-delivery][^plat-orcl-10q]

#### 推理

AWS 已把自研芯片用于规模化托管推理。Bedrock 多数推理运行在 Trainium 上，2026Q3 已达数十亿美元业务规模，token 用量约为上年同期 17 倍。Amazon 另称自研芯片当季为客户节省逾 20 亿美元，范围含 Graviton 和 Trainium，计算方法未披露。谷歌则以 TPU 同时服务自有产品和外部调用，2026Q3 自研模型 API 每分钟处理近 320 亿个 token，口径并非全部为 Cloud 付费用量。两家均已证明规模化运行能力，平台单位毛利仍缺少披露。[^cross-aws-rainier][^csp-amzn-ai][^cross-aws-chip-q3][^btl-goog-q3]

微软的证据主要体现为应用效率。FY2027Q1 Copilot 负载吞吐量环比提高逾 50%，Maia 200 在部分 Teams、Copilot 场景下每瓦 token 产出最高为对照 GPU 的 1.7 倍，尚不能换算成全 Azure 成本降幅。甲骨文已交付运行推理的专用容量，并提供模型调用，但未拆分训练、推理毛利和 API 收入。谷歌 TPU 8i 宣称较前代高 80% 的推理性价比，微软 Maia 300 和 OCI 2027 年引入 TPU 的收益，也都需待投产验证。[^plat-msft-quarter][^plat-msft-silicon][^plat-goog-tpu][^plat-orcl-stargate][^plat-orcl-models][^cross-goog-orcl-tpu]

#### 企业 AI

**微软的成品软件变现证据最明确。** FY2026Q4 Microsoft 365 Copilot 付费席位超过 3,000 万，下一季 Copilot 等高价产品及 GitHub Copilot 用量继续推动商业云每用户收入，Foundry 收入则为上年同期三倍以上。微软能在既有软件合同中销售 AI，也可承接企业自建应用，Copilot 独立利润尚未披露。[^cross-msft-seats][^plat-msft-quarter][^plat-msft-scope]

AWS 和谷歌更直接地受益于云客户扩大采购。2026Q3《财富》500 强在 Bedrock 的支出接近上年同期七倍。谷歌称，2025Q3 已使用 Gemini Enterprise 的客户，一年后在谷歌的支出超过原来的四倍。这些数据证明客户扩购，但模型、计算、数据库和网络的增量尚未分拆。[^csp-amzn-ai][^btl-goog-q3]

甲骨文依托数据库和核心业务流程进入企业 AI。FY2027Q1 多云数据库收入增长 353%，绝对金额未披露，已有客户可以继续在其他云上购买 Oracle。Fusion 与 AI Data Platform 提供了进一步销售 AI 的渠道，其增量收入仍待验证。[^cross-orcl-call][^plat-orcl-data][^plat-orcl-apps]

### 同款 GPU 的差距在交付和任务成本

| 厂商 | 单实例 8 颗 H100 的规格 | 集群与购买方式 |
|---|---|---|
| AWS | `p5.48xlarge` | EFA 跨机通信，适用地区可通过 Capacity Blocks 锁使用时段 |
| 微软 | ND H100 v5 | InfiniBand 跨机通信，用量折扣与容量预约分别购买 |
| 谷歌 | `a3-highgpu-8g` | 支持的规格可用 Flex-start，等待所需容量凑齐后开工 |
| 甲骨文 | `BM.GPU.H100.8` | 独占物理服务器，以 RDMA 组成 Supercluster，大集群按项目交付 |

规格与购买条件见各厂商文档。[^cross-aws-compute][^plat-msft-vm][^plat-msft-buy][^plat-goog-compute][^plat-goog-buy][^plat-orcl-shapes][^plat-orcl-supercluster]

相同卡时价下，网络等待、故障重跑和容量预约空档都会改变总账单。预约能减少开工等待，但不用的时段也可能收费，客户须在确定性与闲置成本之间权衡。有效比较应固定模型和训练目标，再看完工时间与总支出。四家同型号 GPU 的净采购价、实际成交价和同任务成本均缺少可比披露，目前无法排出统一的成本名次。大集群还要区分单节点规格与整组可用容量，客户能租到一台八卡服务器，并不意味着能在同一区域、同一时点获得数千台互联节点。

### 收费方式决定效率收益归谁

AWS 既租 Trainium，也通过 Bedrock 按模型用量或预留吞吐收费。微软除卖算力与 Foundry 服务，还能以软件许可回收 Copilot 的推理成本。谷歌多了 TPU 系统外售，硬件效率可转化为系统竞争力，但需承担库存和账期。甲骨文的大集群主要按容量合同交付，客户自带设备时，设备投入与相关收入一起减少，数据库则形成独立的收费来源。[^cross-aws-models][^plat-msft-platform][^btl-goog-q3][^plat-orcl-project][^plat-orcl-data]

按实际 GPU 时长收费，任务更快完成会先减少客户账单，云商需要把腾出的时间重新售出。按 token 收费，单位成本下降可直接改善毛利，前提是售价和质量不变。软件按席位收费时，更低的推理成本则让同一份订阅收入承载更多使用。因此，CSP 仍向客户提供 GPU 的同时，有动力将适配的托管推理转向自研芯片。[^cross-aws-models][^plat-msft-platform][^plat-msft-silicon]

### 云业务利润与 AI 项目回报

| 公司及季度 | 云收入 | 已披露利润率及范围 |
|---|---:|---|
| AWS，2026 年 9 月季 | 459.84 亿美元 | 分部营业利润率 38.7%，包括通用计算、存储和数据库等 |
| 微软，2026 年 9 月季 | Azure 331.65 亿美元 | Microsoft Cloud 毛利率 66%，还包括 Microsoft 365 商业云等 |
| 谷歌，2026 年 9 月季 | Google Cloud 307.09 亿美元 | 分部营业利润率 36.2%，包括 GCP、Workspace 和 TPU 系统销售 |
| 甲骨文，2026 年 8 月季 | 基础设施云 74 亿美元 | FY2026Q3 新交付 AI 容量毛利率 32%，仅对应特定批次 |

数据来自公司财报及管理层披露。AWS 和谷歌可比较云分部营业利润率，微软、甲骨文所列指标的范围与成本层级均不同。四家没有披露可直接比较的 AI 算力利润率或项目 IRR。[^csp-cash][^plat-msft-scope][^plat-msft-quarter][^plat-goog-10q][^plat-orcl-delivery][^csp-oracle-ai]

产品组合也会干扰判断。微软当季 Azure 产品毛利改善，Microsoft Cloud 整体毛利率却因 Azure 占比上升而下降。资本回报还受设备所有权、付款时间和合同期限影响，供应商融资推迟现金支出，客户自带设备则缩小运营商的业务范围。应将同一合同的收入、折旧后利润和全周期现金投入对应，才能比较项目回报。[^plat-msft-quarter][^plat-orcl-project]

### 投资判断与现金回收

**现有证据下，微软将 AI 需求转化为利润和现金的把握最大，AWS 的利润基础强于当前现金表现。** 微软拥有云与软件两类收费入口，集团现金也最能覆盖扩建。谷歌的现金覆盖好于亚马逊，但扩建与 TPU 备货同时占款。甲骨文收入和项目毛利已兑现，现金回收则最依赖交付与付款安排。[^plat-msft-quarter][^csp-amzn-ai][^btl-goog-q3][^plat-orcl-10q]

| 集团 | 最新季度末的过去四季 | 经营现金流（亿美元） | 现金购建固定资产（亿美元） | 差额（亿美元） |
|---|---|---:|---:|---:|
| 微软 | 2026 年 9 月末 | 1,958.8 | 1,359.2 | **+599.6**[^cross-invest-msft] |
| Alphabet | 2026 年 9 月末 | 1,795.5 | 1,598.0 | **+197.5**[^cross-invest-goog] |
| 亚马逊 | 2026 年 9 月末 | 1,683.0 | 2,151.9 | **−468.9**[^csp-cash] |
| 甲骨文 | 2026 年 8 月末 | 469.4 | 756.6 | **−287.2**[^cross-invest-orcl] |

差额统一以现金流量表的购建支出计算，用于衡量集团自我出资能力，各家均未披露 AI 单独现金流。融资租赁本金、客户融资及代供应商采购部件等需另行考虑。亚马逊自报 FCF 会先扣除资产出售回款和激励，与此表口径不同。[^cross-invest-msft][^csp-cash]

微软的商业剩余履约义务约三成预计一年内确认，Fairwater 提前投产及 Copilot 加购已帮助收入兑现。但 2026 年 9 月季集团折旧由上年同期 71 亿增至 111 亿美元，服务器部件采购和融资租赁也继续占用资金。软件业务提供建设期缓冲，AI 增量利润仍取决于 Azure 消费和 Copilot 收费能否覆盖新增折旧与推理成本。[^cross-invest-msft][^plat-msft-quarter][^cross-msft-fairwater]

AWS 已有较高分部利润和规模化 Bedrock 收入，亚马逊待确认长期承诺约 5,780 亿美元，加权平均剩余期限 6.1 年，收入确认仍取决于使用与履约。公司又为 Anthropic 安排了与算力交付挂钩的融资，扣除已投入部分后剩余额度 150 亿美元。客户关系同时带来云收入和资金需求，只有新增收费逐步超过后续建设与客户融资支出，利润才能更充分地转为现金。[^csp-cash][^csp-amzn-ai]

Google Cloud 积压订单约 5,608 亿美元，预计略超 55% 在两年内确认，包含 TPU 系统销售。2026Q3 Cloud 利润率升至 36.2%，但集团当季现金购建支出已超过经营现金流，2027 年资本开支预计仍显著增加。自营建设占用资本，系统销售占用库存，外购过渡算力又压低短期毛利。其现金改善取决于自营容量接替外购，以及系统交付后顺利回款。集团过去四季仍有正现金余量，最新单季却已出现购建缺口，因此既有现金基础与当前扩张压力需同时考虑。[^cross-invest-goog][^plat-goog-10q][^btl-goog-q3]

甲骨文 6,640 亿美元剩余履约义务中约 13% 预计一年内确认，订单转收入较慢。FY2027Q1 折旧由约 14 亿增至 32 亿美元，经营现金流又含约 114 亿美元带重大融资成分的客户预付款。仅剔除该项，当季经营现金流减现金资本开支的缺口便由约 54 亿扩大至 168 亿美元。预付款减轻垫资，也附带后续服务义务。公司预计 FY2028 下半年自由现金流转正，仍需交付、后续投入和融资安排共同兑现。[^plat-orcl-10q][^plat-orcl-project][^csp-oracle-funding]

### 供给宽松后的利润韧性

**同款 GPU 的紧缺溢价最容易消退，利用率下降会放大降价影响。** 以按实际用量收费的集群为例，假设计费利用率由 80% 降至 60%，固定折旧分摊到每个已售卡时便增加约 33%。若租价再降 10%，收入合计下降 32.5%。这是情景测算，四家尚无可比的 AI 集群计费利用率。已交付保量合同可以在履约期内缓冲降价，但可使用的设备闲置时通常仍须折旧。Amazon 曾将部分服务器和网络设备折旧年限由六年缩至五年，2025 年因此多计 14 亿美元折旧摊销。[^csp-asset-life][^cross-invest-msft]

微软的办公、编程和企业权限体系，AWS 的客户数据、应用与 Bedrock，均能提供算力之外的持续收费，长期利润韧性更有支撑。谷歌的 TPU 与 Gemini 有降本潜力，收益要由成本降幅超过售价降幅、扩建后保持利用率来验证。甲骨文的数据库关系和集群运营仍有价值，但专用园区更依赖大客户续租。评估四家的长期回报，应分别看软件加购、云用量、单位成本和续约现金，不能用新增订单额替代。[^cross-msft-seats][^csp-amzn-ai][^btl-goog-q3][^plat-goog-tpu][^plat-orcl-data][^plat-orcl-project]

# Neocloud

Neocloud 是专注 AI 算力的新兴云商，先投入 GPU、机房和集群系统，再通过出租容量及配套服务回收。其产品和客户通常比传统 CSP 集中。大客户自建与外购可以长期并存，OpenAI 同时采用多家云商和多种芯片，就是为加快部署并分散建设风险。[^neo-buyer]

收入稳定性主要取决于合同。保量客户在云商按约交付后，即使用不满也须付费，按需业务的空置则由云商承担。固定容量收费下，效率提升首先让客户多完成任务，按 token 收费时，云商才更直接地受益于单位成本下降。设备所有权、付款条件与计费方式共同决定回报。

### 向专业 AI 云发展的意义与边界

CoreWeave 管理层在 2026 年 9 月 8 日高盛会议上解释，大客户长约为公司争取了建设 AI 云、拓展客户的时间，未来部分合同可能不再续签。其方向是覆盖训练、推理和模型开发所需服务，让客户持续购买算力及配套产品，业务范围仍集中于 AI。这是一条减少对少数大额算力合同依赖的经营路线。[^neo-crwv-platform]

**平台化扩大了收费范围，也增加研发、销售和服务成本，能否多赚取决于新增收入能否覆盖这些投入。** 传统 CSP 已有相应产品，更完整的产品目录本身不构成优势。CoreWeave 的 Weights & Biases 提供模型实验跟踪与评估工具，仍支持其他云，使用工具不要求购买 CoreWeave 算力。因此，软件用户不能直接视为算力客户，更不能据此推定续约率或定价权提高。[^neo-crwv-forge]

### CoreWeave、Nebius、IREN

三家都在组织并交付 AI 算力。CoreWeave 以集群运营和配套服务拓展客户，Nebius 以大客户承接安排支持直接销售，IREN 则以自有电力和机房为基础。平台建设与资产投入各有侧重，收入稳定性和资本回收也因此不同。

#### CoreWeave 的运营优势与资产负担

2025 年末 CoreWeave 数据中心全部为租赁，自建项目仍在推进。超过 98% 的当年收入来自保量合同，微软贡献约 67%。长约帮助融资，客户集中及长期租金也限制了经营弹性。[^neo-crwv]

商业化已超出 GPU 出租。2026Q2 存储、CPU、网络和软件等 GPU 以外业务 ARR 超过 4 亿美元，托管推理也已按 token 变现，但软件收入和利润未单列。公司还以 Omni 向第三方硬件提供软件，已签首单，管理层预计 2027 年开始放量。该模式可减少自购设备，但具体收费、收入规模和利润尚未披露。[^neo-crwv-call][^neo-crwv-platform]

2026Q2 调整后 EBITDA 利润率 59%，计入折旧摊销后，调整后营业利润率仅 5%，GAAP 营业利润率为 −2%，另有净利息费用 6.4 亿美元。客户需求已经变现，设备消耗与融资成本仍大幅压低股东收益。[^neo-crwv-q2]

运营能力的证据包括 Anthropic 多年订单、ClusterMAX 最高档评级，以及一笔延续至 2029 年的 A100 合同。A100 案例说明旧型号仍有买家，具体设备批次、是否原客户续租、成交价和回报均未披露。[^neo-crwv-anthropic][^neo-clustermax][^neo-crwv-call]

CoreWeave 也受益于短缺溢价。2026 年 9 月部分三至六个月新约折合每兆瓦年化收入约 4,000 万美元。2025 年末经营租赁加权平均剩余期约 11 年，客户合同加权平均期约 5 年，两组合同口径不同，但说明机房租金可能跨过多轮客户租约。管理层称首约测算已考虑偿还设备层债务，实际回收仍须逐批核对。**供给宽松后的关键是续签收入能否覆盖剩余租金、运维和必要换卡。**[^neo-crwv-pricing][^neo-crwv][^neo-crwv-call]

#### Nebius 的直接客户、保底安排与短约定价

Nebius 同时销售大客户专用集群、按需资源、预留容量和 Token Factory 托管推理，各项收入与利润尚未完整拆分。2026 年 3 月的 Meta 协议包括五年 120 亿美元专用容量，自 2027 年初分批交付，另有指定集群的未售容量承接安排。Nebius 优先向第三方销售，剩余容量由 Meta 承接至投运满五年，潜在合同额最高 150 亿美元。它因此保留直接销售机会，并由大客户分担部分空置风险。150 亿美元是指定容量可能由 Meta 承接的上限，不能与同批容量的第三方销售重复计算。保底价与实际利润未披露，合同额也不足以说明直接销售比保底安排多赚多少。[^neo-nbis][^neo-nbis-meta]

2026 年 7 月公布的伙伴模式，由伙伴出资、持有并运营机房和硬件，Nebius 提供系统设计、软件和销售，收取许可费、分成或佣金。该模式减少设备垫资，若 Nebius 承诺采购伙伴容量，转售风险仍由自己承担。合作规模和利润尚未披露。[^neo-nbis-partner]

2026Q2 约 70% 的新签合同含预付款，可覆盖对应资本开支的 50%–60%。管理层测算，当季新合同收入覆盖相关资本开支及运行成本需 1 年 10 个月。这是包含未建成项目、基于预测成本的合同回收期，尚待实际交付和运行验证。[^neo-nbis-q2]

三家中，Nebius 对短缺定价的披露最直接。四笔大单的年合同额折合每兆瓦 2,000 万至 2,500 万美元，三至六个月短约等机会的年化报价则为 4,000 万至 5,000 万美元，第三季度初已签首单。设备和合同组合不同，无法直接计算溢价率，但公司明确将高价归因于客户急于开工。供给宽松后，无保底短单首先承压，Meta 安排仅保护指定容量。Reflection、Cohere 等直接客户能否续租、Token Factory 能否形成服务利润，将决定收入韧性。若降价同时伴随预付款减少，前期资金需求也会增加。[^neo-nbis-q2][^neo-nbis-meta][^neo-nbis-partner]

#### IREN 的自有机房与设备回收

IREN 持有土地、供电设施和数据中心，再采购 GPU 提供算力。自有机房减少外租支出，也承担建设、改造和闲置风险。2026 年 8 月微软验收 Childress 的 Horizon 1，这是四个各 50 MW IT 负载项目的首个，其 GB300 NVL72 部署通过 NVIDIA 测试，获 Exemplar Cloud 资格。部分指定 GPU 和专用空间按经营租赁处理，验收后计租，设备继续由 IREN 持有并折旧。[^neo-iren-delivery][^neo-iren]

托管云能力仍在补强。SemiAnalysis 在加拿大部分容量发现供电、网络和存储可靠性问题，评测未覆盖得州 Horizon 新项目。FY2026 AI 云收入占集团 18.2%，Mirantis 收购直到 8 月才完成。10 月与 Perplexity 的多年协议证明已有微软以外的直接客户，价格和投资覆盖未披露。[^neo-clustermax][^neo-iren][^neo-iren-perplexity]

微软五年合同最初总额约 97 亿美元，按批次预付 20%，相关设备预算约 58 亿美元。按年报融资承诺计算，资金安排如下。[^neo-iren-contract][^neo-iren]

| 微软项目设备资金 | 亿美元 |
|---|---:|
| 原定设备资本开支 | 58.00 |
| 微软预付款，97 × 20% | 19.40 |
| GPU 融资承诺 | 36.45 |
| 预付款与融资合计 | 55.85 |
| 相对设备预算缺口 | 2.15 |

全部按约到账和提款时，可覆盖原设备预算的 96.3%，机房等其他投入未包括在内。贷款有提款条件，款项按批次到位，预付款自各批服务期第 24 个月之后抵扣。96.3% 衡量已安排资金相对设备预算的覆盖，项目仍须以未来服务收入偿还本金、利息和运营支出。设备残值与首约后的续租风险继续由 IREN 承担。

2026 年 3 月 IREN 提前增购逾 5 万颗 B300，预计设备、网络等新增资本开支约 35 亿美元，以争取短缺期交付。租价回落后，已下单设备和机房成本不会同步下降。**IREN 更有持续性的资产是已通电机房，但跨代复用仍须证明改造成本可控且有新客户接手。** 首轮签约和验收已验证交付能力，尚不能证明下一轮设备投入的回报。[^neo-iren-b300][^neo-iren][^neo-iren-contract]

### Neocloud 与传统 CSP 的差异

同一份 AI 算力订单，两类云商都需按期交付，并以收费覆盖设备、机房和运营成本。传统 CSP 的优势来自既有客户、集团融资和适用任务上的自研芯片，头部新云则以交付与集群运营争取订单，也能凭高信用客户的长约融资。[^csp-silicon][^csp-amzn-ai][^neo-clustermax][^csp-project-debt]

#### 硬件采购与运营

同型号 NVIDIA GPU 的净采购价、返利和付款条件缺少可比披露，无法确认 CSP 的实际采购折扣。可验证的差异是 AWS、谷歌和微软已把部分任务转向自研芯片。Trainium2 和 Maia 200 均披露过约 30% 的性价比改善，但对照不同，也未计清迁移、研发和利用率影响。甲骨文仍主要集成第三方芯片，自研芯片对全成本的证据见后文。[^csp-silicon][^plat-goog-tpu][^plat-msft-silicon][^plat-orcl-shapes]

训练任务的成本取决于网络、存储和故障恢复。ClusterMAX 3.0 将 CoreWeave、Nebius 评为 Platinum，Google Cloud 为 Gold，支持头部新云在受测集群体验上的优势，不能外推为全公司成本排名。微软 GB300 上线时间缩短约 20%、Copilot 吞吐环比提升逾 50%，也说明传统 CSP 持续改善交付和运行效率。[^neo-clustermax][^plat-msft-quarter]

生产推理更依赖客户原有数据与应用位置。AWS 披露，企业倾向于就近部署推理，继而增加存储、网络等消费。多客户基础也有助于消化可共享容量，但专用长约、地区和芯片限制仍约束调度。新云要持续获得这类订单，需要更低任务成本、更可靠服务，或满足客户分散供应商的需求。[^csp-amzn-ai][^neo-buyer][^neo-crwv-anthropic]

#### 融资成本与现金使用

集团信用的差距已有发行证据。2025 年发行、同为 2030 年到期的美元高级无抵押债中，Alphabet 发行收益率为 4.129%，CoreWeave 平价发行票息为 9.25%。发行时点等条件不同，但反映当时融资成本的明显差距。传统 CSP 还能以既有现金流支持建设，不过上文已显示，微软尚有现金余量，亚马逊则已出现购建缺口。[^csp-corporate-debt][^cross-invest-msft][^csp-cash]

新云可用设备和客户合同抵押融资。CoreWeave DDTL 4.0 浮息部分为 SOFR 加 2.25 个百分点，2026 年 6 月末财报有效利率约 7%。项目回款须先满足偿债、运营储备和现金分配限制，剩余现金才可供集团调配。低风险客户合同能改善融资条件，却不会消除项目对现金的占用。[^csp-project-debt]

预付款与供应商融资主要改善付款节奏。IREN 向 Dell 买设备，微软预付服务费，设备仍由 IREN 持有。客户自带硬件或伙伴承担设备所有权时，运营商才相应减少设备投入与残值风险，也会少收对应收入。若同时承诺保底购买这些容量，仍须承担未售风险。[^neo-iren-contract][^neo-iren][^plat-orcl-project][^csp-oracle-funding][^neo-nbis-partner]

#### 利润与资本回报

甲骨文特定新交付 AI 容量的 32% 毛利率，与 CoreWeave 的 59% 调整后 EBITDA 利润率不可直接比较。后者计折旧摊销后仅剩 5% 调整后营业利润率，利息尚未扣除。AWS、Microsoft Cloud 又包含其他云与软件服务，目前没有同款 AI 服务、同成本口径的利润率排名。[^csp-oracle-ai][^neo-crwv-q2][^csp-cash][^plat-msft-quarter]

项目回报分两个阶段。首约内，应将合同回款扣除电费、租金、运维和追加投入，判断能否收回前期投资。续约阶段，再看旧设备的新租价和改造、换卡支出。若旧卡折旧已大部分计提，续租阶段的账面利润可能改善，仍须连同首轮投资与后续换卡评价全周期回报。股东回报还须计入出资、债务提款、还本付息及项目留存，无法由 EBITDA 或未折现收入差额替代。甲骨文约 28% 的项目 ROI 示例是满产年度现金回收近似值，且未计土地与建筑购置，与自建机房的新云比较时需补齐这些投入及时间差。[^neo-crwv][^csp-project-debt][^neo-iren][^plat-orcl-project]

#### 供给宽松后的竞争

谷歌已使用第三方过渡算力，并预计短期压低 Cloud 利润率。这类临时补缺订单最容易被 CSP 自建产能替代。同地区、同规格容量更充裕后，短约溢价和预付条件会减弱，保量合同只能保护约定履约期，续租时仍须按市场重新谈价。[^btl-goog-q3][^neo-crwv][^neo-nbis-q2][^neo-crwv-pricing]

**头部新云仍有长期承接专业 AI 项目的空间，盈利韧性则更看好传统 CSP。** CoreWeave、Nebius 的受测集群表现支持其运营能力，若能持续减少训练等待、故障重跑和部署工作，就有机会在缺卡溢价消失后留住客户。客户也可将数据与应用留在原云，仅外购部分算力。新云因此有获客空间，却仍面临比价，CSP 的客户关系、融资能力和适用任务上的自研芯片更难整体复制。[^neo-clustermax][^csp-amzn-ai][^csp-corporate-debt][^csp-silicon]

现有证据支持新云的局部运营优势，尚不支持其在供给宽松后普遍取得持续超额回报。平台化能否改善投资价值，应由同批容量的续约价、付费利用率及扣除运维、偿债和必要换卡后的现金验证，不能仅凭产品增加就上调长期回报判断。[^neo-crwv-call][^neo-iren][^csp-project-debt]

# 瓶颈与制约

**2027–2028 年，能排队、能换地区或芯片的算力更可能先宽松，前沿大规模训练和受地区、延迟约束的推理仍可能局部短缺。** 这一判断以机房、电力和设备大致按计划交付为前提。资本开支体现建设力度，只有完成联调、验收并可供客户使用的容量，才构成有效供给。

### 从资本投入到可用算力

电力首先要真正送达机房。购电协议还取决于电源投运、电网接入和变电站承载能力，IEA 将接网排队、输电建设及变压器、电缆交期列为制约。AWS 与 Talen 的核电协议满额 1,920 MW，却要逐步增加，预计最迟 2032 年才达到全量，不能全部计入近两年供给。[^btl-iea-grid][^btl-aws-power]

机房通电后，还须完成配电、冷却、机柜、存储和网络建设。旧机房的空余面积未必支持新一代高密度机架，微软 Fairwater 因此同时设计液冷与低延迟互连。甲骨文的项目时间表也将租赁开始和首次服务交付分开，租金可能先于收入发生。[^plat-msft-fairwater][^plat-orcl-project][^btl-orcl-rubin]

GPU 到货后，需要与显存、服务器、高速网络配套，完成联调和客户验收。微软 GB300 从到货到上线时间缩短约 20%，本身就能提前计费。投产后，内部模型和专用长约又先占去部分容量，剩余供给还要匹配新客户所需地区和机型。行业装机增加与公开市场更容易租到算力，时间上可能错开。购电功率、数据中心容量、IT 负载和 GPU 颗数也须保留各自口径，缺少散热、网络和设备配置时，不能将这些数字直接加总或换算为可售卡时。[^plat-msft-quarter][^btl-orcl-rubin][^plat-orcl-delivery]

### 四家 CSP 的已披露交付安排

#### AWS

2026Q3 维持全年集团现金资本开支 2,200 亿美元的预期，大部分投向 AWS，预计 2027 年继续显著增加。AWS 与 NVIDIA 计划在 2027–2028 年新增部署 200 万颗 GPU，覆盖 Blackwell Ultra、Rubin 和 Rubin Ultra，未拆年度、地区及客户锁定量。Trainium2、Trainium3 已有生产负载，管理层称新增容量上线后很快被使用，也提到内存等部件涨价。电力、机房和设备各自造成的交付缺口未量化。[^btl-aws-q3][^btl-aws-nvidia][^cross-aws-rainier][^csp-amzn-ai]

#### 微软

Fairwater 已投入使用，但部分原定第三方 GPU 服务延期至 FY2027 下半年，即 2027 年 1–6 月。2026 自然年资本开支预计约 1,700 亿美元，包含租赁开始时确认的融资租赁本金。后续支出加速既有延期容量因素，也包括 CPU、GPU、内存和存储新增投入，延期原因未按电力、施工和设备拆分。[^cross-msft-fairwater][^plat-msft-quarter]

Constellation 预计 Crane 核电项目 2027 年重启，仍需监管审批。Maia 300 也计划 2027 年开始部署，主要用于内部推理。两项计划分别改善电源与计算效率，微软尚未披露可转化为多少对外 Azure 容量。[^btl-msft-crane][^plat-msft-silicon]

#### 谷歌

2026 年集团资本开支指引为 1,950 亿至 2,050 亿美元，预计 2027 年显著增加。2026Q3 技术基础设施支出约 65% 为服务器与网络、35% 为数据中心。外购过渡算力在季末开始上线，四季度预计扩大使用，自营容量全面接替的日期未披露。[^btl-goog-q3]

得州 Meitner 将机房与新增电源共同建设，尚无投产日期。Kairos、TVA 首个先进核电项目计划从 2030 年供电，对 2027–2028 年帮助有限。设备方面，Rubin A5X 计划 2026 年 11 月商用，Ironwood 等 TPU 已可用，8t、8i 仍列为即将推出。2027 年预计放量的 TPU 系统外售应与 GCP 自营新增算力分别统计。[^btl-goog-power][^btl-goog-a5x][^btl-goog-q3][^plat-goog-tpu]

#### 甲骨文

FY2027Q1 已交付 850 MW 新增数据中心容量，自上一财季末向 AI 云客户交付逾 30 万颗 GPU。Rubin NVL72 于 2026 年 10 月 27 日宣布商用。Bloom 为甲骨文美国项目签约的首批 1.2 GW 现场燃料电池正在部署，计划持续至 2027 年，电源装机仍需经过机房和集群交付才能产生服务收入。[^plat-orcl-delivery][^btl-orcl-rubin][^btl-orcl-power]

OCI 计划 FY2027–FY2028，即 2026 年 6 月至 2028 年 5 月，增加约 7 GW 容量，已交付的 850 MW 包含在内。1 GW 项目示例从签约约半年后开始投入，约一年首次交付、两年全部交付，显示收入随批次逐步爬坡。大型项目优先满足既有合同，尚未披露可供新客户购买的容量。[^plat-orcl-project]

### 2027–2028 年供需判断

推理需求与硬件产出效率正在同时增长。AWS 2026Q3 披露推理贡献过半 AI 收入，Bedrock 用量约增至上年同期 17 倍。谷歌自研模型 API 每分钟处理近 320 亿个 token，微软 Copilot 吞吐量环比提升逾 50%。前两项体现使用量，后一项体现运行效率，均不能直接推导所需新增 GPU 数量。更高吞吐可以让现有设备承接新增请求，而更长上下文和更多模型调用也会消耗这部分效率收益。[^btl-aws-q3][^csp-amzn-ai][^btl-goog-q3][^plat-msft-quarter]

以下为按自然年的分析判断。新设备和软件优化扩大供给，ASIC 可接走部分适配推理。需求端，Agent 每项任务可能多次调用模型，单 token 成本下降也可能刺激使用。最终取决于有效产出增长与新增工作量哪一项更快。[^plat-msft-silicon][^btl-orcl-rubin][^btl-aws-q3]

| 工作负载 | 2027 年判断 | 2028 年判断 |
|---|---|---|
| **批量推理、常规微调和小规模训练** | 最可能先缓解。可排队，对地区和最新芯片依赖较低，成熟 GPU 与适配 ASIC 均可承接 | 新设备上线、成熟设备转用后，等待时间和短约价格更易下降 |
| **成熟一代大型训练集群** | 单机和小批容量先改善，整组同代 GPU 仍受园区网络与交付限制 | AWS、OCI 如按计划部署，新增容量及部分转出的 Blackwell 集群扩大选择，已锁定容量仍待合同或调度释放 |
| **前沿预训练和大规模后训练** | 首批 Rubin、新 TPU 仍需足量芯片及高速互连，跨园区也需专线，零散现货难以替代 | 高端供给增加，但新模型可能迅速吸收容量，最大规模集群与首发设备仍易紧张 |
| **实时长上下文及指定地区推理** | 长上下文占显存，实时请求需保留峰值余量，数据驻留和延迟要求限制换区 | 推理芯片和软件提高单位电力产出，若 Agent 调用更快增长，热门地区仍可能排队 |

供给是否宽松，需观察已送电并验收的容量、同地区同类实例的预约等待，以及新签短约价格。已被长约锁定的园区投产会增加行业装机，却未必立即增加现货。只看资本开支或采购量，容易高估新客户可获得的供给。

### 七家公司的订单、租价与闲置风险

下文以通用算力先宽松、前沿训练与特定地区推理仍偏紧为情景。“租价”指新签或续约价格，“付费利用率”指有客户承担费用的容量比例。保量合同下，设备实际运行率降低，收入仍可能维持，前提是交付和服务义务均已履行。

#### AWS

除上述 GPU 部署计划外，OpenAI 承诺使用约 2 GW Trainium 算力，涉及 Trainium3 和计划 2027 年开始交付的 Trainium4，未披露逐年消化量。[^btl-aws-openai]

**2027 年**大客户订单随集群交付转为收入，最新训练集群仍可获得大单，通用 GPU 短约先出现折扣。**2028 年**若两年部署兑现，成熟 GPU 租价压力加大，旧设备可转向批量推理与微调。Bedrock 和既有客户有助于吸收共享容量，Trainium 承接更多内部推理也可能释放 GPU，最终闲置风险集中在当地需求不足、用途又难调整的容量。专用集群仍依赖签约客户使用和付款。

#### 微软

部分外购容量将在 2027 年上半年补交，商业剩余履约义务约三成预计在 2026 年 9 月后的十二个月确认，后者还包括 Azure 以外产品。[^plat-msft-quarter][^plat-msft-scope]

**2027 年**新增 GPU 优先满足已有 Azure 和内部需求，普通实例的折扣空间增加，前沿训练与指定地区推理仍可能紧张。**2028 年**自建产能和 Maia 若顺利到位，最容易先被压价或缩量的是到期外购容量。微软能在适配的 Azure 与内部负载间调度设备，但地域错配仍会造成闲置，已锁定外购容量的付款义务仍按合同履行。

#### 谷歌

Google Cloud 订单预计略超一半在未来两年确认，包含 TPU 系统销售，尚无 GCP 分地区自营容量交付表。[^plat-goog-10q][^btl-goog-q3]

**2027 年**过渡采购先填近期缺口，自营 GPU、TPU 再承接增长。适配 TPU 的批量推理有更多选择，标准 GPU 面临比价，最新训练和低延迟推理仍需预约。**2028 年**如自营容量跟上，高价过渡采购最可能先收缩。Gemini 等内部产品有助于吸收 TPU，仍不能解决所有 GPU 和区域错配。系统外售增长也不能代替对云上可出租容量的判断。

#### 甲骨文

既定扩建以大客户合同为基础，首次交付至全部交付约一年的项目示例意味着订单逐步转收入。**2027 年**主要看分批验收，普通 GPU 新单先有价格竞争，大型集群的确定交付日期仍可能有溢价。机房、设备或验收延误则使支出先发生、计费后移，这与投产后找不到客户属于不同风险。[^plat-orcl-project][^plat-orcl-10q]

**2028 年**已交付长约继续支撑付费利用率，未锁客的新集群更易被压价。四家 CSP 中，甲骨文的专用园区对单个客户最敏感，一笔大订单改期或缩量后，同地区、同配置的替代买家可能难以及时补位。

#### CoreWeave

2026 年 6 月末预计约 41% 的剩余履约义务在 2028 年 6 月前确认。NVIDIA 对适用协议未售容量的承接义务延续至 2032 年，受交付、可用性和终止条款约束。高价短约及延续至 2029 年的 A100 合同并存，A100 租价未披露。[^btl-crwv-coverage][^neo-crwv-pricing][^neo-crwv-call]

**2027 年**保量合同和承接安排保护适用容量，新签短租更早承受 CSP 竞争。**2028 年**重点转向旧集群续租，客户可按同款 GPU 比价，运营优势需要转化为更低任务成本。若降价仍无法补足客户，无承接容量会同时面临利用率下降和租金刚性。公司未拆 2028 年到期容量，尚不能认定该年会集中承压。[^neo-crwv][^neo-clustermax]

#### Nebius

微软合同原定 2025–2026 年分批部署，基础期延续至 2031 年，2026Q2 已披露多批交付。Meta 专用订单自 2027 年初分批交付，另有指定集群承接安排。Nebius 计划 2027 年起每年部署超过 1 GW，同时用短约和竞价争取高价。[^btl-nbis-msft][^neo-nbis-meta][^neo-nbis-q2]

**2027 年**长约随验收计费，有承接的容量具备缓冲，无保底短约先失去紧缺溢价，及时降价可能维持使用量。**2028 年**持续扩建后的风险落在无保底新增容量和短约续租，直接客户及托管推理能否填满集群，决定利用率是否随租价一起下降。伙伴模式减少垫资，若 Nebius 保底采购，未售风险仍须承担。对于没有保底的自有容量，应同时观察价格和使用量，单价下降但集群更满，与价格、利用率一起下降，对回收期的影响明显不同。[^neo-nbis-partner]

#### IREN

Horizon 已有首批验收，其余容量原计划 2026 年底前分批交付。管理层称 2026 年容量基本售罄，并以 2027 年再交付约 500 MW IT 负载为目标。Perplexity 已签多年协议，新增机房和设备的逐批合同覆盖率尚未公布。[^btl-iren-ramp][^neo-iren-contract][^neo-iren-delivery][^neo-iren-perplexity]

**2027 年**微软项目按约交付后可计费，风险集中在先投产、后找客户的新 GPU，租价下降会同时延长回收期。**2028 年**若已通电机房能以有限改造承接下一代设备，仍可争取长单，单靠提前买卡的溢价则趋弱。应分别观察机房出租率与 GPU 付费利用率，机房有人使用也可能伴随部分设备闲置。[^neo-iren][^neo-iren-b300]

综合现有合同，2027 年应重点关注 IREN 尚未锁客的新增批次、Nebius 无保底短租，2028 年还需关注 CoreWeave 到期旧集群。AWS、微软和谷歌有更多内部或多客户负载，甲骨文专用项目更依赖单客接收。七家实际闲置率缺少可比披露，以上是风险判断。若 IREN 新增容量大多在投产前锁定保量客户，其闲置风险应相应下调。判断降价是否有效，仍要同时看签约覆盖与付费利用率。[^btl-crwv-coverage][^neo-nbis-meta][^btl-iren-ramp][^plat-orcl-project]

### 自研 ASIC 对成本与租价的影响

自研芯片最容易在量大、稳定且已适配的负载上降本。每瓦产出更多 token 只证明能效改善，全成本还需计入芯片服务器、网络机房、电力运维、研发和适配，并按实际产出分摊。比较时须控制模型质量、响应时间及相关工作负载，利用率会直接影响结果。

| 公司 | 生产状态 | 成本证据及边界 |
|---|---|---|
| **AWS** | Bedrock 多数推理已用 Trainium，Trainium3 已承接生产 | Decart 实时视频推理成本约为 GPU 方案一半，属于客户任务案例，费用范围未披露。Trainium2 约 30% 的性价比优势是另一口径。[^csp-silicon][^asic-aws-trn3] |
| **谷歌** | TPU 已训练并运行 Gemini | 2025 年 Gemini 服务单位成本下降 78%，来自模型、运行效率和利用率优化。计量单位、费用范围和 TPU 单独贡献未披露。[^cross-goog-orcl-tpu][^asic-goog-cost] |
| **微软** | Maia 200 已用于部分 Teams、Copilot 生产推理，Maia 300 计划 2027 年投产 | 最高 1.7 倍 token／瓦及性能／美元属于效率比较。另有单次代码扫描降本案例，未归因于 Maia。[^plat-msft-silicon][^plat-msft-quarter] |
| **甲骨文** | 已使用第三方加速器，计划 2027 年起引入谷歌 TPU | 尚无同类自研 AI 加速器投产或 OCI 使用 TPU 的生产单位成本披露。[^plat-orcl-shapes][^btl-orcl-rubin][^cross-goog-orcl-tpu] |

**四家均未公开可复核、同口径的每 token 全成本对比。** 谷歌提供了规模化服务成本下降的证据，AWS 提供特定任务成本案例，微软 Maia 主要体现生产能效。现有材料支持适配负载降本，但还不能量化 ASIC 相对 GPU 的普遍全成本优势。

若 CSP 将降本让利给客户，低价 API 会降低可迁移客户租 GPU 的意愿。ASIC 接走内部推理后，腾出的 GPU 如能对外出租，还会增加供给。新单与续约先受影响，已验收保量合同仍按约履行。折旧和机房租金短期固定，降价后增加的销量能否补回收入，将决定利润变化。

CoreWeave 的旧集群同时面对新设备和低价 API 竞争，依赖 GPU 工具链、定制部署的客户仍有需求。Cognition 已在其 Rubin 集群运行生产，证明新平台交付有客户价值，能否保住回报仍取决于新卡付费利用率与旧卡续价。[^asic-crwv-rubin][^btl-crwv-coverage]

Nebius 的 Token Factory 在 2026Q2 推理负载增至上季三倍以上，并引入模型与调度优化技术。同批 GPU 多产出 token 可降低成本，但托管推理也直接面对 CSP API 竞争。成本若降得比售价慢，用量增长仍可能伴随毛利率下降，其单位成本与毛利尚未披露。[^neo-nbis-q2][^asic-nbis-inference]

IREN 的现有微软项目受合同保护，Maia 扩大使用更先影响微软下一批 GPU 采购。尚未锁客就上架的设备，因此更容易同时遇到压价和闲置。电力与机房可争取新设备或新租户，能否补回原 GPU 投资仍取决于改造费用和新合同条件。[^neo-iren][^neo-iren-contract][^plat-msft-silicon]

[^plat-msft-scope]: 微软 [FY2027Q1 Form 10-Q](https://www.sec.gov/Archives/edgar/data/789019/000119312526436133/msft-20260930.htm)，产品及服务收入、商业剩余履约义务。
[^plat-msft-vm]: 微软 [VM 系列总览](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/overview)、[NCads H100](https://learn.microsoft.com/en-us/azure/virtual-machines/ncads-h100-v5)、[ND 系列](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/gpu-accelerated/nd-family)和 [ND GB300](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/gpu-accelerated/nd-gb300-v6-series)。
[^plat-msft-buy]: 微软 [Azure Savings Plan](https://azure.microsoft.com/en-us/pricing/offers/savings-plans/)、[VM 容量预约](https://learn.microsoft.com/en-us/azure/virtual-machines/capacity-reservation-overview)及 [Cobalt 商用公告所列购买方式](https://azure.microsoft.com/en-us/blog/azure-cobalt-100-based-virtual-machines-are-now-generally-available/)。
[^plat-msft-fairwater]: 微软 [Azure AI superfactory 架构说明](https://blogs.microsoft.com/blog/2025/11/12/infinite-scale-the-architecture-behind-the-azure-ai-superfactory/)，2025-11-12。
[^plat-msft-silicon]: 微软 [第一代 Maia 与 Cobalt 发布](https://blogs.microsoft.com/blog/2023/11/15/microsoft-ignite-2023-ai-transformation-and-the-technology-driving-change/)、[Cobalt 100 商用](https://azure.microsoft.com/en-us/blog/azure-cobalt-100-based-virtual-machines-are-now-generally-available/)、[Build 2026 部署说明](https://news.microsoft.com/build-2026-live-blog?live-feed-entry-id=4990)、[Cobalt 200 预览及客户](https://azure.microsoft.com/en-us/blog/new-azure-cobalt-200-vms-deliver-50-performance-improvement-fully-optimized-for-modern-agentic-ai-workloads/)、[Maia 200 规格及工具链](https://blogs.microsoft.com/blog/2026/01/26/maia-200-the-ai-accelerator-built-for-inference/)和 [2026-10-12 Maia 200／300 进度](https://blogs.microsoft.com/blog/2026/10/12/microsoft-to-expand-azure-maia-system-to-multi-gigawatt-deployments/)。
[^plat-msft-platform]: 微软 [Azure Machine Learning](https://learn.microsoft.com/en-us/azure/machine-learning/overview-what-is-azure-machine-learning?view=azureml-api-2)、[Foundry 产品说明](https://learn.microsoft.com/en-us/azure/ai-foundry/what-is-foundry?preserve-view=true&view=foundry)、[Foundry 定价](https://azure.microsoft.com/en-us/pricing/details/ai-foundry/)和 [PTU 计费](https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/provisioned-throughput-billing)。
[^plat-msft-quarter]: 微软 [FY2027Q1 官方电话会](https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1)及[本地纪要](transcripts/MSFT_2027Q1_EarningsCall.md)，2026-10-28。涵盖第三方容量、资本开支及 Copilot 吞吐量，Microsoft Cloud 范围包含 Azure、Microsoft 365 商业云等。
[^plat-msft-openai]: 微软 [与 OpenAI 的修订协议说明](https://blogs.microsoft.com/blog/2026/04/27/the-next-phase-of-the-microsoft-openai-partnership/)，2026-04-27。
[^plat-goog-10q]: Alphabet [2026Q3 Form 10-Q](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000084/goog-20260930.htm)，分部业绩及 Google Cloud 收入变动。
[^plat-goog-compute]: Google Cloud [Axion C4A 商用](https://cloud.google.com/blog/products/compute/first-google-axion-processor-c4a-now-ga-with-titanium-ssd)和 [GPU 实例规格](https://docs.cloud.google.com/compute/docs/gpus/)。
[^plat-goog-buy]: Google Cloud [AI Hypercomputer 容量和购买方式](https://docs.cloud.google.com/ai-hypercomputer/docs/consumption-models)。
[^plat-goog-tpu]: Google Cloud [TPU 产品页](https://cloud.google.com/tpu)、[Ironwood 与前代规格对照](https://docs.cloud.google.com/tpu/docs/tpu7x)和 [Next 2026 AI 基础设施公告](https://cloud.google.com/blog/products/compute/ai-infrastructure-at-next26/)。
[^plat-goog-platform]: Google Cloud [Gemini Enterprise Agent Platform 发布说明](https://cloud.google.com/blog/products/ai-machine-learning/the-new-gemini-enterprise-one-platform-for-agent-development)和[平台定价](https://cloud.google.com/products/gemini-enterprise-agent-platform/pricing)。
[^plat-goog-enterprise]: Google Cloud [Gemini Enterprise 许可及使用费](https://docs.cloud.google.com/gemini/enterprise/docs/manage-costs-overview)和 [Workspace 企业版](https://workspace.google.com/enterprise/)。
[^plat-orcl-10q]: Oracle [FY2027Q1 Form 10-Q](https://www.sec.gov/Archives/edgar/data/1341439/000119312526389274/orcl-20260831.htm)，现金流量表及收入确认附注。
[^plat-orcl-delivery]: Oracle [FY2027Q1 业绩公告，SEC 附件](https://www.sec.gov/Archives/edgar/data/1341439/000119312526387905/orcl-ex99_1.htm)，2026-09-10，基础设施收入、新签合同和交付。MW 沿用数据中心容量口径。
[^plat-orcl-shapes]: Oracle [OCI 实例规格表](https://docs.oracle.com/en-us/iaas/Content/Compute/References/computeshapes.htm)。
[^plat-orcl-supercluster]: Oracle [Supercluster 架构](https://blogs.oracle.com/cloud-infrastructure/first-principles-zettascale-oci-superclusters)及 [GPU 产品说明](https://www.oracle.com/cloud/compute/gpu/)。
[^plat-orcl-buy]: Oracle [OCI Capacity Reservations](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/reserve-capacity.htm)，适用范围和计费。
[^plat-orcl-stargate]: OpenAI [2025-07-22 Stargate 合作及 Abilene 投产进度](https://openai.com/index/stargate-advances-with-partnership-with-oracle/)和 [2025-09-23 新站点公告](https://openai.com/index/five-new-stargate-sites/)。
[^plat-orcl-models]: Oracle [OCI GPU 软件支持](https://www.oracle.com/cloud/compute/gpu/)、[Data Science](https://docs.oracle.com/en-us/iaas/Content/data-science/using/home.htm)、[OCI Enterprise AI](https://www.oracle.com/artificial-intelligence/generative-ai/generative-ai-service/)及[模型计费](https://docs.oracle.com/en-us/iaas/Content/generative-ai/pay-on-demand.htm)。
[^plat-orcl-data]: Oracle [多云数据库](https://www.oracle.com/cloud/multicloud/)、[Oracle AI Database@AWS 部署及购买](https://docs.oracle.com/en-us/iaas/Content/database-at-aws/oaaws-overview.htm)和 [Exadata 服务计费与云消费承诺](https://www.oracle.com/engineered-systems/exadata/database-service/faq/)。
[^plat-orcl-apps]: Oracle [AI Data Platform](https://www.oracle.com/ai-data-platform/)及 [企业应用与 AI 产品公告](https://www.oracle.com/news/announcement/ai-world-oracle-reinvents-enterprise-computing-for-the-ai-era-with-openai-2026-10-27/)。
[^plat-orcl-project]: Oracle [2026-10-28 投资者日 CFO 材料](https://s23.q4cdn.com/440135859/files/doc_downloads/2026/10/Oracle-Investor-Day-Meeting/vFinal/2026-Investor-Day-CFO-presentation.pdf)，第 8、14、18、24 页。分别涉及新增容量、1 GW 项目、融资与剩余建设计划。项目收益为管理层示例，供应商融资方案的资本开支含同期融资付款。
[^cross-aws-rainier]: Amazon [2025Q4 业绩公告](https://ir.aboutamazon.com/news-release/news-release-details/2026/Amazon-com-Announces-Fourth-Quarter-Results/)，2026-02-05。Rainier 的投运与 Anthropic 训练用途，以及当时 Bedrock 在 Trainium 上的推理负载。
[^cross-aws-chip-q3]: Amazon [2026Q3 自研芯片披露](https://www.aboutamazon.com/news/company-news/amazon-custom-chips-demand-q3-2026-earnings)，公司对 Trainium 云外部署的时间计划。
[^cross-msft-fairwater]: Microsoft [FY2026Q3 业绩会](https://www.microsoft.com/en-us/Investor/events/fy-2026/earnings-fy-2026-q3)，Fairwater 上线进度及收入确认影响。
[^cross-msft-seats]: Microsoft [FY2026Q4 业绩会](https://www.microsoft.com/en-us/Investor/events/fy-2026/earnings-fy-2026-q4)，Microsoft 365 Copilot 付费席位及软件收入。
[^cross-goog-orcl-tpu]: Google Cloud 与 Oracle [在 OCI 部署 TPU 的联合公告](https://cloud.google.com/blog/products/infrastructure/bringing-google-tpus-to-oracle-cloud-infrastructure)，说明已运行的 Gemini 工作负载及计划自 2027 年起部署的 OCI 容量。
[^cross-orcl-call]: Oracle FY2027Q1 业绩会管理层发言，见 [2026-09-10 业绩公告及回放入口](https://investor.oracle.com/investor-news/news-details/2026/Oracle-Announces-Q1-Results-Driven-by-Triple-Digit-Growth-in-Cloud-Infrastructure-Revenues/default.aspx)与[本地业绩会纪要](transcripts/ORCL_2027Q1_EarningsCall.md)。GPT-6 Astra 训练地点和多云数据库收入增速均为管理层披露，已用 FocusAlpha (retrieve) 对照同场发言。
[^cross-aws-compute]: AWS [EC2 P5 规格](https://aws.amazon.com/ec2/instance-types/p5/)和 [Capacity Blocks for ML](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-capacity-blocks.html)。
[^cross-aws-models]: AWS [Trainium 产品说明](https://aws.amazon.com/ai/machine-learning/trainium/)、[Bedrock 定价](https://aws.amazon.com/bedrock/pricing/)及 [Amazon 2026Q1 芯片业务披露](https://www.aboutamazon.com/news/company-news/amazon-ceo-andy-jassy-amazon-chips-business-q1-2026-earnings)。
[^cross-invest-msft]: 微软 [FY2026 Form 10-K](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)及 [FY2027Q1 Form 10-Q](https://www.sec.gov/Archives/edgar/data/789019/000119312526436133/msft-20260930.htm)。过去四季按 FY2026 全年加最新季度减上年同期计算。季报另披露折旧、融资租赁和协助购入服务器部件相关的现金流及资产。
[^cross-invest-goog]: Alphabet [2025 Form 10-K](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm)、[2026Q3 Form 10-Q](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000084/goog-20260930.htm)和 [2026Q3 业绩公告，SEC 附件](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000080/googexhibit991q32026.htm)。过去四季按 2025 全年加 2026 年前九个月减 2025 年前九个月计算。
[^cross-invest-orcl]: 甲骨文 [FY2026 Form 10-K](https://www.sec.gov/Archives/edgar/data/1341439/000119312526277521/orcl-20260531.htm)及 [FY2027Q1 Form 10-Q](https://www.sec.gov/Archives/edgar/data/1341439/000119312526389274/orcl-20260831.htm)。过去四季按 FY2026 全年加最新季度减上年同期计算。经营现金流按财报原口径，包含带重大融资成分的客户预付款。
[^neo-crwv-anthropic]: CoreWeave [2026-04-10 Anthropic 多年协议公告](https://investors.coreweave.com/news/news-details/2026/CoreWeave-Announces-Multi-Year-Agreement-With-Anthropic/)。
[^neo-crwv-pricing]: CoreWeave [2026-09-17 新签短约定价公告](https://investors.coreweave.com/news/news-details/2026/CoreWeave-Continues-to-Contract-New-Compute-Capacity-at-Higher-Prices/default.aspx)。每兆瓦价格为合同收入年化后除以相关集群的用电需求。
[^neo-iren-perplexity]: IREN [2026-10-30 与 Perplexity 的多年合作公告](https://iren.com/resources/blog/perplexity-and-iren-powering-fast-trustworthy-ai-at-scale)。
[^neo-iren-b300]: IREN [2026-03-04 扩充 B300 设备采购公告](https://iren.com/resources/news/iren-expands-ai-cloud-capacity-to-150000-gpus)。资本开支为公告时预计金额。
[^neo-buyer]: OpenAI [2026-03-31 基础设施组合说明](https://openai.com/index/accelerating-the-next-phase-ai/)、[2026-04-29 基础设施合作说明](https://openai.com/index/building-the-compute-infrastructure-for-the-intelligence-age/)。
[^neo-crwv]: CoreWeave [2025 Form 10-K](https://www.sec.gov/Archives/edgar/data/1769628/000176962826000104/crwv-20251231.htm)，Item 1、Item 2、收入及客户集中度披露。
[^neo-crwv-call]: CoreWeave [2026Q2 官方电话会记录](https://s205.q4cdn.com/133937190/files/doc_financials/2026/q2/CRWV-US-CORRECTED-TRANSCRIPT-CoreWeave-Q2-2026-Earnings-Call-11August2026.pdf)，第 4—5 页、第 7—8 页及第 17 页。ARR 合计包含存储、CPU、网络和软件，非当年已实现收入。Omni 放量时间为管理层预期。
[^neo-crwv-platform]: CoreWeave [高盛会议纪要](transcripts/CRWV_20260909_Conference.md)，Michael Intrator 关于长约争取转型时间、AI 服务范围及 Omni 的英文发言，原文件第 143—159、185、203—219 行。会议为美国时间 2026-09-08，文件按香港日期命名，日期见[公司参会公告](https://investors.coreweave.com/news/news-details/2026/CoreWeave-to-Participate-in-the-Goldman-Sachs-Communacopia--Technology-Conference/default.aspx)。已用 FocusAlpha（retrieve）交叉核对，发言归属以本地英文纪要为准。
[^neo-crwv-forge]: CoreWeave [Weights & Biases 与 Forge 产品说明](https://www.coreweave.com/companies/weights-and-biases)，2026-11-06 核验。公司明确 Weights & Biases 继续支持其他基础设施供应商，使用该工具无须迁入 CoreWeave 算力。
[^neo-crwv-q2]: CoreWeave [2026Q2 业绩公告及非 GAAP 调整表，SEC 附件](https://www.sec.gov/Archives/edgar/data/1769628/000176962826000362/coreweave2q26earningspress.htm)。
[^neo-nbis]: Nebius [2025 Form 20-F](https://www.sec.gov/Archives/edgar/data/1513845/000110465926052948/nbis-20251231x20f.htm)，Item 4、Item 5 及收入确认附注。
[^neo-nbis-meta]: Nebius [2026-03-16 Form 6-K](https://www.sec.gov/Archives/edgar/data/1513845/000110465926027886/tm268879d1_6k.htm)。150 亿美元为指定未售容量的潜在合同额，仍须满足交付、服务要求。不可与同一容量的第三方销售重复计算。
[^neo-nbis-partner]: Nebius [2026-07-15 基础设施伙伴模式公告](https://nebius.com/newsroom/nebius-introduces-business-model-to-scale-ai-cloud-globally-through-infrastructure-partnerships)。收费方式还包括承诺容量安排，公司称已达成初步合作。
[^neo-nbis-q2]: Nebius [2026Q2 股东信](https://assets.nebius.com/assets/a6ecfd85-a6cb-4967-8ef7-9a25bd261f9c/SHLQ226.pdf)，第 2—4 页及脚注。70%为合同数量占比。回收期按收入确认口径和预测成本计算，未将预付款提前计作收入，非股东 IRR。
[^neo-iren-delivery]: IREN [2026-08-13 Horizon 1 验收公告](https://www.globenewswire.com/news-release/2026/08/13/3344413/0/en/iren-delivers-horizon-1-to-microsoft-and-achieves-nvidia-exemplar-cloud-status-on-gb300-nvl72.html)，验收及 NVIDIA 测试资格均为公司披露。
[^neo-clustermax]: SemiAnalysis [ClusterMAX 3.0，2026-09-23](https://newsletter.semianalysis.com/p/clustermax-30-the-industry-standard)，方法及相关公司章节。评测针对托管集群，其结论仅适用于受测集群的运营表现。
[^neo-iren]: IREN [2026 Form 10-K](https://www.sec.gov/Archives/edgar/data/1878848/000187884826000052/iren-20260630.htm)，收入、期后收购及 Note 23、26。AI 收入占比按 128,795 ÷ 707,007 = 18.2%（原表均为千美元）。GPU 融资承诺按 15.45 + 21 = 36.45 亿美元。项目有现金分配限制和特定母公司担保。
[^neo-iren-contract]: IREN [2025-11-03 Form 8-K](https://www.sec.gov/Archives/edgar/data/1878848/000114036125040072/ef20058139_8k.htm)，微软及 Dell 协议。58 亿美元为最初设备预算。预付款自各批次服务期第 24 个月之后抵扣。资金覆盖率按 55.85 ÷ 58 = 96.3%。97 − 58 = 39，均为未折现总额比较。
[^csp-silicon]: 公司披露见 [Amazon 2026Q1 芯片业务说明](https://www.aboutamazon.com/news/company-news/amazon-ceo-andy-jassy-amazon-chips-business-q1-2026-earnings)、[微软 Maia 200 公告](https://blogs.microsoft.com/blog/2026/01/26/maia-200-the-ai-accelerator-built-for-inference/)、[Google Cloud Next 2026 公告](https://cloud.google.com/blog/products/compute/ai-infrastructure-at-next26/)。各厂商比较基准不同。
[^csp-amzn-ai]: Amazon [2026Q3 CEO 关于 AWS 和 AI 的说明](https://www.aboutamazon.com/news/company-news/aws-growth-ai-demand-q3-2026-earnings)，客户数据、配套需求及 AI 利润率部分。
[^csp-corporate-debt]: Alphabet [2025-04-28 SEC 定价文件](https://www.sec.gov/Archives/edgar/data/1652044/000119312525100802/d806252dfwp.htm)、CoreWeave [2025-05-21 定价公告](https://investors.coreweave.com/news/news-details/2025/CoreWeave-Announces-Upsize-and-Pricing-of-2000-million-of-Senior-Notes/default.aspx)。比较历史发行投资者收益率，发行日期、赎回及流动性条件仍有差别，非当前利差或全部融资成本。
[^csp-project-debt]: CoreWeave [2026Q2 Form 10-Q，Note 10](https://www.sec.gov/Archives/edgar/data/1769628/000176962826000366/crwv-20260630.htm)、[DDTL 4.0 推介材料](https://s205.q4cdn.com/133937190/files/doc_presentations/2026/Mar/2026-03-DDTL-4-Overview.pdf)，第 3—4 页。推介的固定定价参考约 5.9%，与财报有效利率口径不同。现金储备覆盖约三个月债务、对冲及运行支出。
[^csp-cash]: 微软 [截至 2026-09-30 的 SEC 季报](https://www.sec.gov/Archives/edgar/data/789019/000119312526436133/msft-20260930.htm)、Amazon [同期 SEC 季报](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000040/amzn-20260930.htm)。现金流均为集团口径，微软现金购建支出不含新增融资租赁的全部义务。Amazon FCF 为经营现金流减扣除销售及激励后的固定资产购置。AWS 利润率按 17,773 ÷ 45,984 计算。
[^csp-oracle-funding]: Oracle [2026-10-28 投资者日公告](https://investor.oracle.com/investor-news/news-details/2026/Oracle-Investor-Day-2026-Accelerating-Value-Creation/default.aspx)，融资安排部分。
[^csp-oracle-ai]: Oracle CEO [2026-03-24 官方说明](https://blogs.oracle.com/ceo/from-the-q3-earnings-call)，当季交付 AI 容量的管理层毛利率口径，非 OCI 审计分部利润率。
[^csp-asset-life]: Amazon [2025 Form 10-K，Note 1](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm)，部分服务器和网络设备使用年限调整，非全部 GPU 的统一经济寿命。
[^asic-aws-trn3]: AWS [Trainium3 商用公告](https://www.aboutamazon.com/news/aws/trainium-3-ultraserver-faster-ai-training-lower-cost)，包括 Bedrock 生产负载及 Decart 视频推理案例。
[^asic-goog-cost]: Alphabet [2025Q4 官方电话会](https://abc.xyz/investor/events/event-details/2026/2025-Q4-Earnings-Call-2026-Dr_C033hS6/default.aspx)，Sundar Pichai 关于 Gemini 服务单位成本的说明。
[^asic-crwv-rubin]: CoreWeave [2026-09-30 Rubin 生产部署公告](https://investors.coreweave.com/news/news-details/2026/CoreWeave-Delivers-NVIDIA-Vera-Rubin-NVL72-Performance-at-Production-Scale-Starting-With-Cognition/default.aspx)，Cognition 的生产负载及吞吐量测试。
[^asic-nbis-inference]: Nebius [2026-05-12 推理技术公告](https://nebius.com/newsroom/nebius-welcomes-clarifai-s-core-team-and-licenses-inference-ip-to-strengthen-nebius-token-factory)，包括 Clarifai 核心团队加入及推理技术授权。
[^btl-aws-openai]: AWS 与 OpenAI [2026-02-27 合作公告](https://press.aboutamazon.com/2026/2/openai-and-amazon-announce-strategic-partnership)，Trainium 容量承诺及 Trainium4 预计开始交付时间。
[^btl-crwv-coverage]: CoreWeave [2026Q2 Form 10-Q](https://www.sec.gov/Archives/edgar/data/1769628/000176962826000366/crwv-20260630.htm) 收入附注及 [2025-09-09 Form 8-K](https://www.sec.gov/Archives/edgar/data/1769628/000176962825000047/crwv-20250909.htm) 的 NVIDIA 未售容量承接安排。剩余履约义务确认比例与付费利用率分别衡量。
[^btl-nbis-msft]: Nebius [2025-09-08 Form 6-K](https://www.sec.gov/Archives/edgar/data/1513845/000110465925088312/tm2525580d1_6k.htm)，Microsoft 合同原定部署批次和基础合同期。
[^btl-iren-ramp]: IREN [FY2026 业绩公告，SEC 附件](https://www.sec.gov/Archives/edgar/data/1878848/000187884826000051/irenreportsfy26results.htm)及[本地 FY2026Q4 业绩会纪要](transcripts/IREN_2026Q4_EarnignsCall.md)。约 500 MW 是管理层的 IT 负载交付目标。机房交付后，GPU 还要经过安装、测试和验收。
[^btl-iea-grid]: IEA [《Energy and AI》执行摘要](https://www.iea.org/reports/energy-and-ai/executive-summary)，电网接入、输电及电力设备交期。
[^btl-aws-power]: Talen Energy [亚马逊购电协议扩展公告](https://ir.talenenergy.com/node/8671/pdf)，满额功率及交付爬坡计划。
[^btl-aws-q3]: Amazon [2026Q3 业绩公告](https://ir.aboutamazon.com/news-release/news-release-details/2026/Amazon-com-Announces-Third-Quarter-Results/)和[本地业绩会纪要](transcripts/AMZN_2026Q3_EarningsCall.md)，现金资本开支与训练、推理需求见管理层发言。
[^btl-aws-nvidia]: AWS 与 NVIDIA [2026-08-26 联合公告](https://press.aboutamazon.com/aws/2026/8/aws-and-nvidia-to-deliver-2-million-additional-gpus-and-next-generation-infrastructure-for-agentic-and-physical-ai)，部署计划及 GPU 代际。
[^btl-msft-crane]: Constellation [Crane Clean Energy Center 项目页](https://www.constellationenergy.com/about/locations/crane-clean-energy-center.html)，供电安排、预计重启时间和审批。
[^btl-goog-q3]: Alphabet [2026Q3 官方电话会](https://abc.xyz/investor/events/event-details/2026/2026-Q3-Earnings-Call-2026-Ujou16CTw9/default.aspx)及[本地纪要](transcripts/GOOG_2026Q3_EarningsCall.md)，2026-10-28。涵盖 TPU 客户及系统销售、资本开支、过渡容量和模型 API 用量。过渡容量供应商及价格未披露，原文已归档。
[^btl-goog-power]: Google [得州 Meitner 电源及数据中心项目](https://blog.google/innovation-and-ai/infrastructure-and-cloud/global-network/meitner-energy-center/)及 [Kairos／TVA 核电项目](https://blog.google/company-news/outreach-and-initiatives/sustainability/google-first-advanced-nuclear-reactor-project-with-kairos-power-and-tennessee-valley-authority/)。
[^btl-goog-a5x]: NVIDIA [2026-10-21 Google Cloud A5X 公告](https://blogs.nvidia.com/blog/google-cloud-vera-rubin-infrastructure/)，正文将正式商用安排在次月。
[^btl-orcl-rubin]: NVIDIA 与 Oracle [2026-10-27 Rubin 商用及扩张公告](https://nvidianews.nvidia.com/news/nvidia-and-oracle-expand-nvidia-vera-rubin-to-multi-gigawatt-scale-and-bring-nvidia-vera-cpu-to-oracle-cloud-infrastructure)。
[^btl-orcl-power]: Bloom Energy [2026-04-13 甲骨文现场发电合作公告](https://investor.bloomenergy.com/press-releases/press-release-details/2026/Bloom-Energy-and-Oracle-Expand-Strategic-Partnership-to-Deploy-up-to-2-8-GW-to-Accelerate-AI-Infrastructure-Build-Out/default.aspx)，首批签约部署与长期合作上限分列。

原始资料及核对记录见[三家新云资料](../../../sources/industries/CSP/neocloud-operating-evidence/2026-11-05/source-index.json)、[CSP 与新云比较](../../../sources/industries/CSP/csp-neocloud-comparison/2026-11-05/source-index.json)及[云平台与供需资料](../../../sources/industries/CSP/platform-chapters/2026-11-05/source-index.json)。
