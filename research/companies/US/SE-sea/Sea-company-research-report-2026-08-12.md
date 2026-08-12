---
title: Sea Limited 公司基础研究报告
as_of: 2026-08-12
company: Sea Limited
ticker: SE
accounting: US GAAP
currency: USD million unless stated
---

# Sea Limited 公司基础研究报告

## 一、结论与研究边界

Sea 已从“Garena 供血、Shopee 和金融扩张”的亏损集团，转变为三个核心分部均实现法定盈利、集团现金生成快速增强的平台。2022 年是效率转向，2023 年首次实现年度净利润，2024-2025 年增长重新加速；2025 年收入 US$22.938bn、经营利润 US$1.985bn、净利润 US$1.611bn、经营现金流 US$5.025bn。Shopee 的法定分部利润由 2021 年亏损 US$2.767bn 转为 2025 年盈利 US$581m，是质量最重要的变化。

当前最值得研究的矛盾是 Monee：贷款和利润快速扩大，FY2025 consumer/SME principal 增至 US$9.2bn，2026Q2 达 US$11.1bn；>90 天 NPL 仍为 1.0%-1.1%。稳定 NPL 与高速增量并存，现有公开数据尚不能证明完整信用周期下的损失率。集团净现金充足，但受限现金、存款、托管款和监管实体现金不应视为同一自由资金池。

本报告以 2026-08-12 为截止日，使用 Sea 官网/API、FY2021-FY2025 20-F、同期结果公告/演示/电话会记录以及 2026Q2 最新材料。法定数字与 issuer APM 严格分开；所有材料为公司来源，尚未完成竞争对手、监管数据库和产业链交叉验证。

## 二、公司与商业模式

Sea Limited 是开曼注册、NYSE 上市的外国私人发行人，经营主体遍布东南亚、台湾、拉丁美洲等市场。三条业务线的商业逻辑不同：

| 分部 | 价值主张 | 收入来源 | 主要投入/风险 |
|---|---|---|---|
| Shopee | 为消费者和商户提供交易、发现、支付、物流和履约平台 | 交易费、广告、物流/增值服务、部分自营销售 | 补贴、营销、物流、内容治理与激烈竞争 |
| Monee | 在数字生态中提供支付、钱包、信贷、银行、保险与财富服务 | 利息、信贷和支付费用、银行费用、保费和佣金 | 信用损失、资金与监管资本、牌照和数据合规 |
| Garena | 开发/发行游戏并运营用户、社区和电竞 | 虚拟道具及游戏服务 | Free Fire 集中、产品周期、第三方授权与平台渠道 |

协同主要发生在用户入口、商户、支付、本地运营和数据层；资本与风险必须分开看。Shopee 流量能降低 Monee 获客成本，但也可能放大同一消费周期的相关性；Garena 的内容现金流能支持集团投资，但内容生命周期不是长期合约。

## 三、五年法定三表

以下均为 US GAAP、合并口径、USD million。2021-2022 优先采用 FY2023 20-F 的最新比较列，2023-2025 采用 FY2025 20-F。完整原始行、来源标签和页码见 `data/curated/companies/US/SE-sea/sea-financial-statements-2021-2025.csv`；映射见 `sea-financial-mapping-ledger.csv`。

### 3.1 利润表摘要

| USD m | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| Revenue | 9,955 | 12,450 | 13,064 | 16,820 | 22,938 |
| Gross profit | 3,896 | 5,185 | 5,834 | 7,205 | 10,244 |
| Operating income (loss) | (1,583) | (1,488) | 225 | 662 | 1,985 |
| Income (loss) before tax | (1,715) | (1,501) | 432 | 779 | 2,281 |
| Net income (loss) | (2,043) | (1,658) | 163 | 448 | 1,611 |
| Parent-attributable income (loss) | (2,047) | (1,651) | 151 | 444 | 1,578 |

来源：`sources/companies/US/SE-sea/official-website/2026-08-12/raw/pdfs/Sea-FY2023-Form-20-F.pdf` 与 `Sea-FY2025-Form-20-F.pdf`，F-11 至 F-12。

### 3.2 资产负债表摘要

| USD m | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| Cash and equivalents | 9,248 | 6,030 | 2,811 | 2,405 | 4,159 |
| Short-term investments | 911 | 864 | 2,548 | 6,215 | 6,413 |
| Current assets | 15,135 | 12,688 | 11,774 | 16,858 | 23,249 |
| Total assets | 18,756 | 17,003 | 18,883 | 22,625 | 29,371 |
| Financial debt ex leases | 3,576 | 3,458 | 3,368 | 3,007 | 1,844 |
| Lease liabilities | 678 | 1,027 | 1,080 | 1,104 | 1,487 |
| Current liabilities | 7,176 | 6,936 | 8,169 | 11,296 | 14,681 |
| Total liabilities | 11,332 | 11,192 | 12,186 | 14,148 | 16,723 |
| Total equity | 7,424 | 5,811 | 6,698 | 8,478 | 12,648 |

来源同上，F-7 至 F-10。债务为分析映射：短期/长期 borrowings 与 convertible notes 合计，不含经营租赁。

### 3.3 现金流摘要

| USD m | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| CFO | 209 | (1,056) | 2,080 | 3,277 | 5,025 |
| CFI | (3,767) | (2,429) | (5,804) | (5,041) | (4,409) |
| CFF | 7,402 | 400 | 366 | 1,684 | 1,623 |
| PPE + intangible capex | 807 | 976 | 258 | 322 | 524 |
| Cash flow after capex | (599) | (2,032) | 1,821 | 2,956 | 4,500 |

来源同上，F-14 至 F-15。`Cash flow after capex = CFO - PPE/intangible capex` 是分析计算，不是公司定义 FCF。

现金流量表期末现金包括受限现金，资产负债表 cash and equivalents 不包括。五年独立桥已经勾稽为零；2022 还包括 US$13.227m held-for-sale cash。见 `sea-cash-reconciliation-2021-2025.csv`。

## 四、派生指标（先表后分析）

### 4.1 盈利与回报

| 指标 | 2021 | 2022 | 2023 | 2024 | 2025 | 公式/说明 |
|---|---:|---:|---:|---:|---:|---|
| Revenue growth | - | 25.1% | 4.9% | 28.8% | 36.4% | 当年收入/上年收入-1 |
| Gross margin | 39.1% | 41.7% | 44.7% | 42.8% | 44.7% | 毛利/收入 |
| Operating margin | -15.9% | -12.0% | 1.7% | 3.9% | 8.7% | 经营利润/收入 |
| Consolidated net margin | -20.5% | -13.3% | 1.2% | 2.7% | 7.0% | 合并净利润/收入 |
| Parent ROE | n/a | -25.2% | 2.4% | 5.9% | 15.1% | 归母利润/平均归母权益；2021 缺期初值 |

### 4.2 流动性与杠杆

| 指标 | 2021 | 2022 | 2023 | 2024 | 2025 | 公式/说明 |
|---|---:|---:|---:|---:|---:|---|
| Current ratio | 2.11x | 1.83x | 1.44x | 1.49x | 1.58x | 流动资产/流动负债 |
| Cash-only ratio | 1.29x | 0.87x | 0.34x | 0.21x | 0.28x | 不含受限现金和短期投资 |
| Net debt ex leases | (6,583) | (3,436) | (1,991) | (5,614) | (8,729) | 债务-现金-短期投资；负数为净现金 |
| Equity ratio | 39.6% | 34.2% | 35.5% | 37.5% | 43.1% | 权益/资产 |

这些是集团会计视角，不是 Monee 的监管流动性或资本充足率。现金、短期投资、受限现金、存款负债与托管款分属不同经济池，不能据此断言所有现金可自由上划。

### 4.3 现金转换与资本强度

| 指标 | 2021 | 2022 | 2023 | 2024 | 2025 | 公式/说明 |
|---|---:|---:|---:|---:|---:|---|
| CFO margin | 2.1% | -8.5% | 15.9% | 19.5% | 21.9% | CFO/收入 |
| Capex intensity | 8.1% | 7.8% | 2.0% | 1.9% | 2.3% | PPE+无形资产购买/收入 |
| Cash-after-capex margin | -6.0% | -16.3% | 13.9% | 17.6% | 19.6% | (CFO-capex)/收入 |
| CFO/capex | 0.26x | -1.08x | 8.05x | 10.19x | 9.58x | CFO/资本开支 |

计算器完整输出及逐项公式见 `sea-financial-metrics-2021-2025.md`。严格模式的资产负债与利润归属检查全部通过。

## 五、分部与经营 KPI

### 5.1 法定经营分部利润

| USD m | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| Shopee | (2,767) | (2,013) | (550) | (139) | 581 |
| Monee | (640) | (277) | 490 | 658 | 973 |
| Garena | 2,500 | 1,971 | 1,178 | 979 | 1,184 |
| Other | (178) | (252) | (57) | (44) | (91) |

来源：FY2023 与 FY2025 20-F Segment Reporting；完整收入与 margin 见 `sea-segment-financials-2021-2025.csv`。

### 5.2 KPI 与 issuer APM

| 指标 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| Shopee GMV (US$bn) | 62.5 | 73.5 | 78.5 | 100.5 | 127.4 |
| Shopee orders (bn) | 6.1 | 7.6 | 8.2 | 10.9 | 13.9 |
| Shopee adjusted EBITDA (US$bn) | (2.6) | (1.7) | (0.214) | 0.156 | 0.881 |
| Garena bookings (US$bn) | 4.6 | 2.8 | 1.8 | 2.1 | 2.9 |
| Garena adjusted EBITDA (US$bn) | 2.8 | 1.3 | 0.921 | 1.199 | 1.656 |
| Monee adjusted EBITDA (US$bn) | (0.617) | (0.229) | 0.550 | 0.712 | 1.018 |

以上 APM 来自各年度 Results，不与法定分部利润混用。2026Q3 起 Garena adjusted EBITDA 将排除 deferred revenue 及相关成本净变化，历史序列出现定义断点。

## 六、阶段性驱动

### 2022：效率转向而非盈利完成

收入增长 25.1%，但经营亏损仍为 US$1.488bn、CFO 为负 US$1.056bn。重要变化是集团从不计代价扩张转向成本纪律；Shopee 和 Monee 亏损收窄，但 Garena bookings 从 US$4.6bn 降至 US$2.8bn，原有供血能力显著下降。

### 2023：利润和现金流拐点

收入只增 4.9%，经营利润却转正至 US$225m，CFO 增至 US$2.080bn。Shopee 法定亏损缩至 US$550m，Monee 转为 US$490m 盈利。改善不仅来自收入增长，更来自费用控制、补贴优化和资本开支骤降；因此 2023 是盈利模型被验证的第一年，但增长仍弱。

### 2024-2025：增长再加速并形成经营杠杆

收入增速升至 28.8% 和 36.4%，经营利润率从 3.9% 升至 8.7%，CFO margin 从 19.5% 升至 21.9%。2025 Shopee 首次录得 US$581m 法定分部利润，Monee 与 Garena 也贡献近 US$1bn 或以上分部利润。现金后资本开支达到 US$4.5bn，资产负债表净现金扩大。

## 七、Monee 信贷与资金

| USD m，除注明 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| Statutory net loans | 1,530 | 2,075 | 2,485 | 4,161 | 7,964 |
| Allowance for credit losses | 98 | 239 | 322 | 449 | 842 |
| Group credit-loss provision | 117 | 514 | 634 | 777 | 1,373 |
| Deposits payable | 466 | 1,316 | 1,706 | 2,712 | 3,798 |
| Escrow/advances | 1,545 | 1,862 | 2,199 | 2,498 | 3,097 |
| Consumer/SME principal (US$bn) | n.d. | n.d. | n.d. | 5.1 | 9.2 |
| >90-day NPL | n.d. | n.d. | n.d. | 1.2% | 1.1% |

贷款扩张速度快于拨备费用增长的简单比较并不足以得出改善结论，因为期末余额、平均余额、核销和贷款 vintage 不同。2025 gross write-offs 约 US$993m，贷款损失准备升至 US$842m；应继续追踪新增批次在 6-18 个月后的表现。off-book channeling 贷款虽不在集团资产负债表本金中，平台仍承担运营、声誉和潜在合作方风险。

## 八、地区收入

| USD m | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| Southeast Asia incl. Singapore | 6,317 | 8,321 | - | - | - |
| Singapore | - | - | 506 | 659 | 793 |
| Southeast Asia excl. Singapore | - | - | 8,673 | 11,115 | 14,379 |
| Latin America | 1,851 | 2,044 | 2,194 | 3,276 | 5,533 |
| Rest of Asia | 1,394 | 1,727 | 1,496 | 1,591 | 2,006 |
| Rest of world | 393 | 357 | 194 | 178 | 228 |

2021-2022 与 2023-2025 的东南亚口径不同；合并 Singapore 后才可作趋势比较。拉美 2023-2025 增长约 2.5 倍，是地域增量的重要来源，但公开分部表未提供对应利润。

## 九、2026Q2 最新状态

2026Q2 集团收入 US$7.788bn，同比增长 48.1%。Shopee GMV US$38.3bn、订单 4.2bn、adjusted EBITDA US$255m；Monee 收入 US$1.4bn、adjusted EBITDA US$288m、贷款本金 US$11.1bn、NPL 1.0%；Garena bookings US$763.5m、adjusted EBITDA US$429.8m、QAU 666.3m、付费用户 68.1m。

管理层称对 Shopee 2026 年达到 US$1bn adjusted EBITDA 乐观，这是前瞻性公司口径，不是审计结果。2026Q2 还执行 US$416.8m 回购；需要同时观察资本回报、贷款扩张和未来内容投入，而不能只看短期 EPS。

## 十、治理、VIE 与披露结构

Forrest Li 是董事长兼 CEO，并通过每股 15 票的 Class B 股控制约 57.6% 投票权（2026-03-31）。集中控制提高长期决策一致性，也削弱普通 ADS 持有人对重大交易、董事选举和控制权变更的影响。

Sea 通过 VIE 处理部分外资限制业务；FY2025 VIE 收入低于 3%，但合同控制不等同直接持股。公司作为 foreign private issuer，不需要像美国本土发行人一样提交 10-Q/8-K，这正是本研究同步保存季度公告、电话会记录与年度 20-F 的原因。

## 十一、主要风险、反证与待验证问题

- **Monee 信用风险：** NPL 低可能是真实风控，也可能受高增量分母和较年轻 vintage 影响；需补逐国 vintage、核销回收和监管资本。
- **Shopee 竞争：** 盈利已转正，但市场份额、补贴、物流净额列报和营销投入可能使利润对竞争强度敏感。
- **Garena 集中：** Free Fire 仍是核心，Palworld Online、Monster Hunter Outlanders 等新品尚不能证明组合多元化成功。
- **APM 可比性：** Garena adjusted EBITDA 从 2026Q3 改定义，必须桥接。
- **治理：** 创始人投票控制与 FPI 披露豁免降低外部股东制衡。
- **地域/监管：** 多币种、多牌照、数据、内容、电商和金融规则可能限制现金上划与业务协同。

反证条件包括：Monee NPL/核销在贷款增速放缓后显著上升；Shopee 为守份额重回大额亏损；Garena bookings 再度结构性下滑；经营现金流改善主要来自存款/托管款或短期营运资本而非持续利润。

## 十二、数据与来源索引

- 官网手册：`research/companies/US/SE-sea/Sea-official-website-handbook-2026-08-12.md`
- 原始快照：`sources/companies/US/SE-sea/official-website/2026-08-12/`
- 证据台账：`sources/companies/US/SE-sea/official-website/2026-08-12/evidence-ledger.csv`
- 五年三表：`data/curated/companies/US/SE-sea/sea-financial-statements-2021-2025.csv`
- 严格计算器输出：`data/curated/companies/US/SE-sea/sea-financial-metrics-2021-2025.md`
- 分部/KPI/地区/Monee：同目录 `sea-segment-financials-2021-2025.csv`、`sea-operating-kpis-2021-2025.csv`、`sea-geographic-revenue-2021-2025.csv`、`sea-monee-credit-funding-2021-2025.csv`
- 主要原始文件：FY2023/FY2025 20-F、FY2021-FY2025 Results、2026Q2 Results 与 Transcript，均见 PDF manifest。
