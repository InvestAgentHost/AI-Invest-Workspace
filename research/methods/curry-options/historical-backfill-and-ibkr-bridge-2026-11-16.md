---
id: curry-options-historical-backfill-2026-11-16
type: source-audit
title: 一年历史期权回补：可获取来源、费用与 IBKR 衔接
author: Codex
published_at: 2026-11-16
retrieved_at: 2026-11-16
as_of: 2026-11-16
status: samples-verified-paid-access-not-tested
template: templates/source-note.md
---

# 一年历史期权回补：可获取来源、费用与 IBKR 衔接

## 内容摘要

**历史期权链可以买到，也存在实际可下载的样本；但“订阅一个月，下载后取消，再交给 IBKR”并非每家都允许。** 本轮检查了官方价格、接口、真实样本、取样时刻及数据留存条款。没有购买、注册账户、调用付费凭据、连接用户 IBKR 或联系供应商。

研究判断：若目标是回补后主要由 IBKR 更新，优先考虑 ORATS 的有限标的 API 回补；其公开条款允许终止后保留已提供材料作内部使用。HistoricalData.net 的一次性文件更便宜、留存权明确，但本轮只有旧年份样本，最近一年连续性尚未验收。ThetaData 适合作为持续订阅的历史及当前分析源。MarketData.app 可低成本取得原始链，但历史 IV/Greeks 为空，而且取消付费后必须删除付费下载的数据。

**没有任何一家通过“目标股票最近一年逐日完整下载 + 与用户 IBKR 实盘行情重叠验证”的最终验收。** 下文明确区分供应商承诺、公开样本实测和分析判断；这些供应商也都尚未被证实是 KotlinerBTC 本人使用的数据商。

## 可验证事实：价格、权限及交付

以下为核查日官方个人/单用户价格，美元，未计税费、汇兑、专业或商业用途附加授权。月费采用按月付款价格；一次性文件购买与月费分列。

| 来源 | 费用 | 官方历史能力及取得方式 | 本轮实际取得 | 对本任务的关键限制 |
| --- | --- | --- | --- | --- |
| [MarketData.app](https://www.marketdata.app/pricing/) | Starter **30/月**；年付页面等效 **12/月**，需要全年承诺；Free **0** | Starter 5 年历史、10,000 credits/日；Free 1 年、100 credits/日。注册取得 token，通过历史 chain API 下载 | 无认证 AAPL 官方演示接口，取得 2025-11-17、2026-06-15、2026-11-13 完整到期日链 | 历史 IV/Delta 等全部为空；必须自行计算；停止付费须删除付费原始数据 |
| [ThetaData](https://www.thetadata.net/pricing/) | Options Value **40/月**；Standard **80/月** | Value 含报价和 OI；Standard 增加历史 IV、一阶 Greeks。注册订阅，运行 v3 Theta Terminal，通过本地 REST 接口请求；Standard 期权历史始于 2016-01-01 | 下载官方样本包，解析 SPY/SPXW 的 2025-08-19 EOD；未调用付费 Greeks API | 样本 EOD 文件不含 IV/OI，须从对应端点获取；协议终止后的清除条款不支持默认作一次性买断 |
| [Alpha Vantage](https://www.alphavantage.co/premium/) | Premium **49.99/月起**，75 requests/分钟、无每日总量上限 | `HISTORICAL_OPTIONS`，官方说明自 2008 年起，按股票与日期返回历史链；需 Premium key | 官方 IBM demo 的 2026-11-13 和 2017-11-15 数据，均有 IV/Greeks/OI | 样本没有对应标的价格、精确快照时刻；IV 模型及停止订阅后长期留存权未核清 |
| [ORATS API](https://orats.com/data-api) | Delayed API **199/月**，20,000 requests/月 | 历史 strikes/near-EOD 自 2007 年起；账户 API token。回补历史不需要购买 Live 档 | 下载官方 2024-01-03 全市场样本，确有 NVDA、MU、ORCL 及近端周到期 | 取收盘前 14 分钟；IV/Greeks 有自有曲面处理；其标的参考值不是实际股价 |
| [ORATS 历史文件](https://orats.com/near-eod-data) | 全历史 **599 一次性**；后续文件 **99/月**另选 | 历史通过 S3 下载，购买后开放 14 天；无须 AWS 账户。官方称全库约 500 GB | 与上一行同一类 near-EOD 样本 | 若仅补少量股票一年，购买全市场全历史往往过量；时间和模型问题相同 |
| [HistoricalData.net](https://historicaldata.net/options.html) | 最近 1 年 **160 一次性**，含 1 个月更新；全历史 **580**；后续更新 **68/月** | 支付后提供 CSV 下载链接；官方称覆盖至 2026-11-13，包含报价、标的价格、IV/Greeks/OI | 下载 2022 年下半年样本，含 127 个交易日文件；抽读 3 日 | 最近一年目标标的未实测；README 标记历史档案与持续采集在 2026-08-06 交接，报价时刻字段覆盖不一致 |
| [Cboe DataShop](https://datashop.cboe.com/option-eod-summary) | 计算器实测：NVDA 一年含计算字段 **250**；NVDA/MU/ORCL 三只 **750**；三只不含计算字段 **453** | 自 2012 年起；按股票、日期、计算字段购买 EOD 文件 | 下载官方 2023-08-25 样本；调用公开页面的只读报价计算接口，未加入购物车 | IV/Greeks 只在 15:45 快照提供；少量股票成本也明显高于月度 API |

Cboe 报价区间统一设为 **2025-11-13 至 2026-11-13**，按日文件、股票个别选择；三只含计算字段扩到 **2025-10-13 至 2026-11-13**，计算器返回 **930 美元**。上述是页面配置报价，不是最终结账价或已购买订单。原始请求参数与响应均已留存。

Alpha Vantage 的 49.99 美元来自官方 Premium 页面月付选项实际 HTML，而非搜索摘要；不把年费选项或促销月均价当成月付价格。Theta 的权限以[订阅表](https://thetadata.net/docs/Articles/Getting-Started/Subscriptions.html)及[EOD Greeks 端点](https://thetadata.net/docs/operations/option_history_greeks_eod.html)交叉核验，不能因为免费 EOD 可取就推断免费有 IV/OI。

### 取消订阅后能否继续使用

| 来源 | 官方文本及对方案的影响 |
| --- | --- |
| MarketData.app | [条款](https://www.marketdata.app/terms/)“When You Must Delete the Data”明确：不再保有付费计划时，删除付费期间下载的数据及备份；付费试用同样适用。免费层下载数据可在账户有效时保留。衍生数据另受交易所定义与协议约束，不能默认把逐合约 IV 或 Rank 文件视为任意可保留的豁免。**30 美元是月费，不是一年历史原始链的买断价。** |
| ThetaData | [Subscriber Agreement](https://www.thetadata.net/subscriber-agreement)第 8(c)、8(e)要求协议结束后停止使用并清除数据，且衍生作品也纳入清除要求；[服务条款](https://www.thetadata.net/terms-and-conditions)另规定订阅到期/终止时授权结束。**不能按 80 美元一次性买断来设计。** |
| ORATS | [公开条款](https://orats.com/terms-conditions)第 6.3 允许结束后保留已提供 Materials 作内部使用；第 9.1 另有至少 30 日通知及初始期限规定。可作为短期回补候选，但不能保证总账单必定只有一个月，实际订购时须核对适用订单、取消生效日和任何产品补充条款。 |
| HistoricalData.net | [FAQ](https://historicaldata.net/faq.html)明确：停止更新订阅不影响已下载文件在所购许可下的使用权；一年档含的更新不自动续费。最直接符合“买历史、后续自采”的计费形态。 |
| Alpha Vantage / Cboe | 本轮没有取得足以确认此次产品终止后留存范围的全部适用订单条款；不把“没找到删除文字”写成永久使用授权。Cboe 已取得的是报价和样本。 |

## 样本实测与数据质量

以下数量均来自本轮对相应供应商原始响应/CSV 的本地解析，不是供应商宣传的完整性保证。

### MarketData.app：原始链可读，历史 Greeks 确实为空

使用官方允许公开演示的 AAPL，调用 `/v1/options/chain/AAPL/?date=YYYY-MM-DD&expiration=all`。**必须显式请求 `expiration=all`，默认只取下一月度到期**，会漏掉本任务最需要的短端周合约。[接口说明](https://www.marketdata.app/docs/api/options/chain/)

| 日期 | 合约行数 | 到期日数 | 最近到期日 | 非空 IV | OI/标的价格 | bid > ask |
| --- | ---: | ---: | --- | ---: | --- | ---: |
| 2025-11-17 | 2,698 | 20 | 11-21、11-28、12-05 | 0 | 全部有值 | 0 |
| 2026-06-15 | 3,698 | 26 | 06-15、06-17、06-18 | 0 | 全部有值 | 0 |
| 2026-11-13 | 3,440 | 24 | 11-13、11-16、11-18 | 0 | 全部有值 | 3 |

官方明确历史 `date=` 请求的 `iv/delta/gamma/theta/vega` 在所有套餐均为空。升级套餐不能补出历史 Greeks。OI 是 D−1 交易日结算、在 D 日开盘前可见的数值；其他字段按 D 日收盘快照，不能把同一行 OI 当成 D 日交易后才产生的持仓量。

历史请求按每 1,000 个期权合约计 1 credit，实时/延迟链则按合约计费；不能套用实时计费估算历史回补。本轮三个日期均有近端到期，但还没有逐股票、逐日验收一整年。

### Alpha Vantage：现成 IV/Greeks，但缺关键重算输入

IBM 官方 demo 最新样本为 2026-11-13，2,222 行、20 个到期日；2017-11-15 样本 998 行、14 个到期日。两份均包含 IV、Delta、Gamma、Theta、Vega、Rho、OI、bid/ask，均有很近的到期日。没有 `underlyingPrice` 或精确快照时间字段。不能用其他时刻股价悄悄补齐后声称复现了原 IV。[历史接口说明](https://www.alphavantage.co/documentation/#historical-options)

### ThetaData：报价文件已落地，付费模型数据未实测

官方样本包的 SPY EOD 有 8,768 行，SPXW EOD 有 16,052 行，日期为 2025-08-19。报价文件含到期、行权价、方向、成交量和 bid/ask，不含 IV/Greeks/OI；不能将已下载样本等同于已打通 Standard 的所有端点。

官方 EOD Greeks 文档显示 Standard 可用，并输出计算所用 `underlying_price`。默认采用期权收盘 NBBO 中价和标的收盘价；EOD 报告较晚生成，样本 `created` 也晚于常规收盘，**不能把生成时间直接当成 16:00 同步快照**。若需严格对应 IBKR，优先验收同刻历史报价/Greeks 端点。

Theta 同时有普通 Black–Scholes 和 American binomial 路线，不能笼统写成所有端点都是同一模型；其默认利率、分红、DTE 约定需固定在配置中。[模型说明](https://thetadata.net/docs/Articles/Data-And-Requests/Option-Greeks.html)

### ORATS：目标股票与周到期真实存在

2024-01-03 官方 sample 共 716,822 行、5,787 个 ticker；每行是同一行权价的 Call/Put 对，不是单个期权合约。NVDA、MU、ORCL 分别为 2,570、691、578 行；三只均包含 01-05、01-12、01-19 等到期日。文件含两侧报价、OI、不同报价位置 IV、平滑 IV、Greeks、利率与分红输入。

官方说明取收盘前 14 分钟，常规交易日为 15:46 ET。`stkPx` 和 `spot_px` 都是期权平价推导的参考值，**都不能当作真实股价**。Greeks 的 Delta 列为 Call Delta，Put Delta 按其定义为 Call Delta 减 1。SMV 平滑值与 bid/mid/ask IV 要分列，不能混用。[字段与时刻说明](https://orats.com/near-eod-data)

### HistoricalData.net 与 Cboe：文件可取，仍有边界

HistoricalData.net 旧样本包含 KO、TSLA、SPY、SPX/SPXW；本轮抽读 2022-07-01、09-30、12-30，分别为 34,898、36,298、31,028 行。存在空 IV/Greeks 和对应 `iv_flag`，应按原因保留，不能填零。其说明给出 American Leisen–Reimer 101 步及 European Black-76、利率/远期推导规则，但旧文件没有 `quote_time`；最近一年跨 2026-08-06 采集方式交接，须另取交接前后目标股票样本。网站说明同一模型贯穿历史，不等于本轮已经验证连续性。[方法](https://historicaldata.net/methodology.html)

Cboe 2023-08-25 样本解析出 32,672 个合约，含 15:45 与 EOD 两组报价；IV/Greeks 属于 15:45。不能拿 EOD 价格去核对 15:45 IV 并把差异全归为模型问题。[产品字段说明](https://datashop.cboe.com/option-eod-summary)

## 与当前研究的关系：怎样接上 IBKR

### 需要回补的是逐日合约链，不是平台现成 IV Rank

按照[作者方法核验](author-methodology-verification-2026-11-16.md)，需要重建 14D 50 Delta IV、最近两个合资格周到期的 25 Delta Put/Call IV 差，以及另一个 14D 30 Delta 相关性输入。各平台自己的“IV Rank”期限和聚合方式未必相同，不能直接购买该汇总字段代替。

研究建议回补约 13 个月：一年排名窗口之外留出交易日、相关性和缺失补查缓冲。这里的 13 个月是实施建议，不是作者规定。HistoricalData.net 一年包从购买日倒推，不能默认覆盖“截至最后交易日的一整年再加缓冲”；其日期 manifest 需先确认，13 个月需求也不能套用 160 美元包的价格。

### 技术上可以衔接，数值上不能直接拼接

可靠路线是：**历史供应商原始 bid/ask + 同刻标的价格 → 固定的本地 IV/Delta 计算 → 指标；未来 IBKR 原始 bid/ask + 同刻标的价格 → 同一套计算 → 同一指标。** 供应商 IV 与 IBKR `modelGreeks` 留作校验列，不在切换日直接替换成主序列。

| 必须统一的项目 | 实施与验收要求 |
| --- | --- |
| 合约身份 | 以日期、标的、到期、行权价、Call/Put、乘数、交割及调整状态匹配；不能只靠 ticker 或把 IBKR conId 当跨供应商标识。拆股调整合约单独处理 |
| 时间 | ORATS 对齐距收盘 14 分钟；Cboe 对齐 15:45；MarketData 对齐其 EOD 快照。使用 America/New_York，处理夏令时、半日市、产品不同收盘时间；时刻未确定的来源先标记不可比 |
| 原始行情 | 保存 bid/ask、规模、时间戳、标的价和 OI 的可见时间；剔除或标记 crossed quote、零买价、极宽价差及陈旧报价。不能使用最后成交价无条件替代中价 |
| 模型 | 同一个美式/欧式模型、利率、分红、日数、到期时刻和误差容限贯穿历史与未来。ORATS 的平价标的值若被采用，也必须未来同法推导，不能切换为 IBKR 实际股价却不重算 |
| Delta/期限 | 25/30/50 Delta 取点、方向和插值保持一致；14D 用总方差插值；Skew 最近两个周到期按 DTE ≥ 1 过滤，0DTE 不混入；作者尚未披露的细节写作研究假设 |
| OI | 按实际公布时间与对应结算交易日分别记录。不同供应商的日期标签要核查；不能一律前移一天或把迟到 OI 用于当时不可见的判断 |

ORATS 不提供实际股价会增加输入工作：要么严格复现其远期/平价输入，要么补同期实际标的价格，历史和未来全部重算。IBKR 股票历史与期权历史的能力不同，可另验收股票历史报价能否补充此输入，本轮没有调用账户验证。[IBKR 历史限制](https://www.interactivebrokers.com/docs/tws-api/doc/md/market-data-limitations)

建议先用 NVDA、MU、ORCL 做 20–30 个交易日双源重叠，覆盖周到期切换及至少部分事件日；这是研究建议，不是已完成测试。比较原始报价、25/30/50 Delta IV、14D IV、Skew 和 Rank，并保留差异分布。是否可切换应看是否改变排序/判断及差异成因，不先拍一个统一容差。异常或缺失不前向填充成“正常新数据”。

### IBKR 采集规模仍需控制

IBKR [官方行情说明与此前核查](data-source-audit-2026-11-16.md)显示，初始通常 100 路行情且与 TWS 共用，不等于可同时订阅 100 条完整链。若观察几十只股票，在某一秒同步拉全链会超过初始容量。可提前订阅与更新目标 Delta 附近合约，缩小首批标的、保留前后时间窗，或增加并发额度。没有完成容量验证前，不能承诺 IBKR 可等价替代全市场同刻快照。

按新加坡[官方非专业行情价](https://www.interactivebrokers.com.sg/en/pricing/market-data-pricing.php)，OPRA 1.50/月，加股票 A/B/C 各 1.50/月，合计 **6/月**；这是行情费基准，未计税费、减免及可能的额外行情路数。用户现有账户具体权限尚未核验。

## 研究判断：成本对应的可行路线

1. **目标是有限股票回补后转 IBKR：优先验证 ORATS Delayed API。** 199 美元/月有明确历史 strikes 能力，样本已覆盖目标股票近端到期，公开条款有内部留存依据。以“50 只股票 × 250 个交易日”作为纯预算假设，按一股票一交易日一请求约 12,500 次，低于 20,000 次/月；具体 endpoint、重试和重复验证仍须实测。不要保证一个月一定下载完并取消；30 日通知、双源重叠可能产生第二个月费用。599 美元全市场文件用于更大范围需求。
2. **希望尽快运行、接受长期行情月费：ThetaData Standard 80/月更省计算准备。** 历史和后续一直使用同一供应商 IV 体系，IBKR 用于观察和交叉验证。若后来转 IBKR，自有模型和条款问题仍需处理；不能把持续月费省略成一次性 80 美元。
3. **愿意自算 IV、重视低月费：MarketData.app 30/月可以评估。** 原始报价、OI 和标的价确已取得；但需维护订阅才能保有付费原始链。若等未来 IBKR 自采满一年后再退出，旧历史逐步退出窗口，技术上可行；这是有持续费用和模型开发工作的过渡方案。年付页面等效 12/月意味着 144/年，全年承诺与按月 30 美元的灵活性不同。
4. **只想购买文件：HistoricalData.net 160 美元一年包值得做进一步样本验收，但暂不直接采购。** 买断留存和字段齐全是优点；最近目标链、交接日期一致性、一年包的精确边界都尚未实测。Cboe 是价格已查明的替代，三只一年含 Greeks 为 750 美元。

这轮已把来源、价格和衔接限制查到可比较程度；仍待付费账号/订单后验证的是最近一年完整性、实际吞吐、目标字段质量、账户适用条款，以及 IBKR 重叠差异。分析 Skill 和采集器继续保持未实施。

## 引用位置与复核材料

外部原文和样本统一在 `sources/providers/options-backfill/audit-20261116/`，目录忽略 Git；文件原文不因解析而覆写。以下路径均相对 Workspace 根目录。

| 材料 | 文件 |
| --- | --- |
| MarketData AAPL 三个日期完整链 | `md-aapl-all-20251117.json`、`md-aapl-all-20260615.json`、`md-aapl-all-20261113.json`，同名 metadata 记录 URL |
| Alpha Vantage IBM 官方演示 | `av-ibm-latest.raw`、`av-ibm-20171115.raw`，对应 metadata |
| Theta 官方样本 | `theta-sample.zip`，内部 `td_sample/OPTION/SPY/SPY_eod.csv`、`td_sample/OPTION/SPXW/SPXW_eod.csv`；未执行供应商代码 |
| ORATS 官方样本 | `orats-sample.zip`，下载地址见 `orats-sample.metadata.json` |
| HistoricalData 官方样本 | `hd-sample.zip`，内含 README、LICENSE、日期文件；未执行附带脚本 |
| Cboe 官方样本 | `cboe-sample.raw`（实际为 ZIP） |
| Cboe 配置报价 | `cboe-price-*-request.json` 与 `cboe-price-*-response.raw`；只调用页面 attribute-change 报价，不提交订单 |
| 价格和许可原文 | `marketdata-pricing.html`、`md-terms.html`、`theta-pricing.html`、`theta-agreement.html`、`alpha-premium.html`、`orats-api.html`、`orats-near-eod.html`、`orats-terms.html`、`historicaldata-options.html`、`hd-faq.html`、`cboe-eod.html` |
| 字段/模型原文 | `md-chain.html`、`theta-subscriptions.html`、`theta-greeks.html`、`theta-greeks-eod.html`、`hd-methodology.html` |
| 样本统计（可重建） | `data/derived/curry-options/backfill-sample-audit-2026-11-16.json` |

涉及用户账户、付费权限和最终完整性的问题均没有用公开 demo 推断为已经完成。
