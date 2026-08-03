---
id: company-nasdaq-intc
type: company
title: Intel
status: active
as_of: 2026-07-22
tickers: [INTC]
industries: [semiconductors, CPUs, foundry, advanced-packaging]
tags: [Intel Foundry, 18A, 14A, EMIB, Foveros, STCO, Xeon]
---

# Intel

## 研究结论

本底稿基于 `sources/publishers/substack/damnnang` 的 87 篇可访问归档文章，重点覆盖 2026-03-16 至 2026-05-05 的三篇 Intel 直接研究文章，并补充相关的 foundry、CPU 和先进封装文章。Damnang 的核心框架是：Intel 的重估分三阶段，先验证 Xeon/数据中心产品修复，再验证 EMIB/Foveros 先进封装的外部变现，最后才是外部客户、良率、14A 和 foundry 亏损收窄带来的重估。

截至本底稿日期，第一阶段被部分验证，第二阶段有较强的产业逻辑但客户收入仍需核实，第三阶段仍未被充分证明。因此，INTC 更像一项以 foundry 可行性为核心的高波动转型期权，而不是已经完成反转的 CPU 公司。

## 核心逻辑

### 1. Foundry 的关键不是节点宣传，而是积累飞轮

Damnang 的判断是，TSMC 的护城河来自 PDK/IP 生态、model-to-hardware correlation、BKM（best known methods）、良率学习、客户规模和持续利用率的复合积累。Intel 18A 即使完成内部产品爬坡，也不能自动证明外部客户愿意在其上 tape-out 并承诺量产。

原文强调的结构性难点包括：TSMC 有长期客户和跨设计类型的数据，Intel Foundry 的外部客户量很小，因而在移动 AP、AI 加速器、网络芯片等多样设计上的过程数据更少；较成熟的 IP 也不能从 TSMC 直接无摩擦移植到 Intel 18A。这个判断是对 foundry 进入壁垒的分析，不等同于 Intel 18A 当前良率或商业客户数量的独立证实。

### 2. 18A 是内部产品验证，18A-P 和 14A 才是外部 foundry 验证

文章称 18A 已进入量产爬坡，Panther Lake 和 Clearwater Forest 是关键内部产品，但公开良率不足，且外部客户量仍未达到能够证明 foundry 模式的程度。18A-P 被视为面向外部客户的真正考验；14A 则是更大的远期分水岭，Intel 的资本投入需要与客户承诺绑定。

Damnang 提到的潜在客户包括 Apple、NVIDIA、Microsoft 和 AWS；其中 Apple/NVIDIA 的外部 foundry 量产并非本文档中已确认的正式订单，必须单独核验。Tesla/ Terafab 被视为 14A 的信誉事件或潜在锚定客户，但合同规模、资本分担、产能保证和量产时间尚不清楚。

### 3. 先进封装可能是 Intel 获客的低门槛入口

EMIB 解决横向 chiplet 互连，Foveros 解决垂直堆叠，二者组合形成 Intel 所称的 3.5D 路线。Damnang 的判断是，在 NVIDIA CoWoS 供给紧张、美国本土先进封装需求上升的环境下，Intel 可能先通过封装与测试服务建立客户关系，再把 wafer process 订单带入 18A/14A。

这条路径的优势是客户可以继续把最敏感的 compute die 放在 TSMC，同时把 I/O die、封装或部分测试交给 Intel，迁移风险低于直接把整颗先进芯片换到新 foundry。风险是 EMIB 从演示、评估到大批量、稳定良率和可持续收入之间仍有验证距离。

### 4. STCO 是 Intel 的差异化叙事，但不是单一技术护城河

STCO（system technology co-optimization）在文章中被描述为把晶体管、封装、异构器件、内存、电源、光学 I/O、UCIe/chiplet 标准和系统架构共同优化。Intel 的 IDM 结构理论上可以把内部 Xeon/客户端产品产生的 process、package 和 system data 反馈到下一代设计，再以 PDK、设计套件和封装规则向外部客户提供。

这是一种系统能力假设，而非已经实现的商业护城河。真正的验证是外部客户是否愿意为这种整合能力付费，以及 Intel 能否把内部经验转化成可重复、可交付、不会与客户利益冲突的 foundry 服务。

## 业务与财务观察

- Damnang 在《The Real Game Behind Terafab》中引用 2025 年 Intel Foundry 收入约 178 亿美元、经营亏损约 103 亿美元、外部客户收入约 3.07 亿美元；这意味着外部收入约占 foundry 收入 1.7%。这些数字应以 Intel 2025 年年报复核。
- 《Intel Foundry: A Last Chance》引用 2025 年第四季度 foundry 收入 45 亿美元、经营亏损 25 亿美元，并指出 Intel 自身披露的外部客户规模风险。该文与其他文章出现了 2024 年第四季度亏损约 22.6 亿美元的数字，期间口径不同，不能直接拼接成连续序列。
- 《Intel’s Real Moat》记录 Q1 2026 总收入 136 亿美元、非 GAAP EPS 0.29 美元、非 GAAP 毛利率 41.0%、DCAI 收入 51 亿美元同比增长 22%，同时记录 GAAP EPS 为负 0.73 美元及 Q2 非 GAAP EPS 指引 0.20 美元、毛利率指引 39.0%。这些是文章转述的公司数据，需回到季度公告确认。
- Damnang 认为 Q1 DCAI 强劲表现可能包含供应紧张导致的旧产品释放或一次性因素，不能简单外推。

## 估值前提

这里暂不建立目标价。按文章框架，市场定价可拆成三层：

1. 产品修复：Xeon 6、DCAI 增长和毛利率恢复。
2. 封装期权：EMIB、Foveros 和外部先进封装客户信号。
3. Foundry 重估：外部 14A 客户、良率和 foundry 亏损收窄。

文章的判断是，股价已经较充分反映第一层，并开始反映第二层，第三层仍未证实。这个判断高度依赖文章发布时点，不能直接作为 2026-07-22 的市场估值结论。

## 关键假设

- 18A 内部产品能够形成可靠的量产和良率数据。
- 18A-P 的 PDK、IP 和客户支持能按计划成熟。
- EMIB/Foveros 能从客户评估进入稳定的规模化封装收入。
- 至少一个大型外部客户能对 14A 提供可验证的量产承诺，且随后有第二个客户。
- foundry 亏损随着利用率、良率和外部收入提升而收窄，而不是收入增长伴随结构性闲置成本继续扩大。
- Intel 可以在与 NVIDIA、AMD、hyperscaler 合作时维持可信的客户隔离和知识产权防火墙。

## 风险与反证

- TSMC 的 N2/A16 继续推进，Intel 的 PowerVia/背面供电差异缩小；Intel 的窗口取决于在 TSMC 追上前锁定客户，而不是 TSMC 永远做不到。
- Samsung SF2/SF2P、TSMC Arizona 和其他美国本土产能削弱 Intel 的地缘和第二供应源溢价。
- 18A 的良率、PDK、IP 验证或交付延迟，导致外部客户继续留在 TSMC。
- Terafab 只是合作/信誉声明，而不是包含 wafer volume、capex 分担和 capacity guarantee 的正式合同。
- Q1 2026 DCAI 增长若主要是一次性供给效应，产品修复阶段可能不持久。
- Intel 的 IDM/系统能力也带来客户冲突：它既可能服务客户，又在 CPU、加速器或系统层与客户竞争。

## 待验证问题

- 2026-07-22 前后 Intel 的 18A、18A-P 和 14A 实际良率、量产进度与客户资格状态。
- 外部 foundry 收入的真实金额、客户构成、重复性和毛利率，而不是内部产品收入。
- EMIB/Foveros 的已签订单、封装产能、单位经济性和 NVIDIA/Google/Apple 等传闻的正式确认程度。
- Tesla/Terafab 是否有正式商业合同、目标节点、量产时间、资本结构和产能承诺。
- Xeon 6 设计赢单是否转化为实际出货、ASP、市场份额和持续 DCAI 增长。
- Intel 14A 是否采用客户承诺驱动的资本纪律，以及 2027-2028 时间表是否仍然成立。

## 来源

直接研究：

- [Intel Foundry: A Last Chance](https://damnang2.substack.com/p/intel-foundry-a-last-chance)；本地归档：`sources/publishers/substack/damnnang/normalized/markdown/intel-foundry-a-last-chance.md`；正文日期 2026-03-16。
- [EMIB: Intel Foundry's Best Hope](https://damnang2.substack.com/p/emib-intel-foundrys-best-hope)；本地归档：`sources/publishers/substack/damnnang/normalized/markdown/emib-intel-foundrys-best-hope.md`；正文日期 2026-03-19。
- [Intel’s Real Moat That Nobody Talks About: STCO](https://damnang2.substack.com/p/intels-real-moat-that-nobody-talks)；本地归档：`sources/publishers/substack/damnnang/normalized/markdown/intels-real-moat-that-nobody-talks.md`；正文日期 2026-05-05。

补充研究：

- [The Age of the TSMC Bottleneck](https://damnang2.substack.com/p/the-age-of-the-tsmc-bottleneck)：foundry 切换成本、PDK/IP、良率飞轮和 Intel 获客窗口。
- [The Real Game Behind Terafab](https://damnang2.substack.com/p/the-real-game-behind-terafab)：Tesla/Terafab 对 Intel credibility、封装和 foundry 客户获取的含义。
- [Why the CPU Is the Bottleneck in the Agentic AI Era](https://damnang2.substack.com/p/why-the-cpu-is-the-bottleneck-in)：Xeon、x86 生态和 agentic AI 对 CPU 需求的判断。
- [Why Advanced Packaging is the New Frontier of the AI Era](https://damnang2.substack.com/p/why-advanced-packaging-is-the-new)：EMIB、Foveros、PowerVia 和封装生态的产业背景。

数据质量备注：归档的三篇直接研究文章均标记为 `is_accessible: true`，并有非空 Markdown/纯文本内容。其 JSON/Markdown frontmatter 中的 `published_at` 被统一记录为 `2026-05-06T17:36:58.955Z`，与正文显示日期不一致；本文已按正文日期和原始 URL引用，后续应修复或绕过该元数据字段。
