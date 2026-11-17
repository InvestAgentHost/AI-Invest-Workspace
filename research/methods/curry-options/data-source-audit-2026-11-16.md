---
id: curry-options-data-source-audit-2026-11-16
type: source-audit
title: Curry 期权分析数据源核查
author: Codex
published_at: 2026-11-16
retrieved_at: 2026-11-16
as_of: 2026-11-16
status: incomplete-data-access
template: templates/source-note.md
---

# Curry 期权分析数据源核查

核查目标是判断：优先使用现有和免费数据，能否持续运行对 KotlinerBTC（Curry_TW）分析体系的复现。初始核查按没有券商行情账户开展；2026-11-16 用户补充已有正在使用的新加坡 IBKR 账户，因此新增 IBKR 候选，其账户类型和行情权限尚未核验。**目前已验证部分数据可以取得，但完整复现所需的数据链尚未通过验收。暂不创建分析 Skill。**

同日后续核查已从作者原文和配图确认主要指标口径，详见[作者方法核验](author-methodology-verification-2026-11-16.md)。数据供应商仍未确认。以下供应商访问结果保持原始核查结论，作者口径部分已据新证据更新。

**更新：** 后续已完成[一年历史回补、费用及 IBKR 衔接核查](historical-backfill-and-ibkr-bridge-2026-11-16.md)，新增 MarketData.app 实际历史链，ORATS、ThetaData、HistoricalData.net、Cboe 官方样本及具体价格，并发现 MarketData.app/ThetaData 的取消后数据留存限制。本页下表记录早期访问状态；供应商当前验证进度以该续篇为准，仍未购买或完成付费全年度验收。

## 可验证事实

| 来源 | 验证程度 | 已确认能力 | 对本任务的限制 |
| --- | --- | --- | --- |
| FocusAlpha | 调用 `list_datasets`；调用 `get_market_data` 获取 NVDA 日线 | 股价日线可取；目录提供财报、指引、公司日历等背景数据 | 当前目录没有历史期权链、逐合约 IV 或波动率曲面。`get_risk_stats` 的股票与基准相关性不能替代收益率与 IV 变化的相关性 |
| [DoltHub options](https://www.dolthub.com/repositories/post-no-preference/options) | 无账户 SQL API 实测成功，已保存原始响应 | 历史合约 bid、ask、IV（字段名 `vol`）、Delta 等 Greeks；抽取 NVDA、MU、ORCL | 不含成交量、持仓量、标的价格和报价时刻；期限经过筛选，并非完整期权链；跨一年连续覆盖尚未验证 |
| [OnclickMedia](https://www.onclickmedia.com/About) | 无账户日期索引成功；期权链尚未取到 | NVDA、MU、ORCL 的可用日期列表均列到 2026-10-19 | 文档和报价页面显示维护，期权文档片段 HTTP 401；日期索引不证明期权链当前可读取，也不证明 IV/OI 完整 |
| [ThetaData Free](https://thetadata.net/docs/Articles/Getting-Started/Subscriptions.html) | 官方权限表核查；没有账户，未调用数据 | 免费层列出历史期权 EOD 报价 | 免费层不含历史 IV、Greeks、OI；需要注册和认证。介绍写一年历史，权限表另列更早起始日，实际权限需账户实测 |
| [Cboe 延迟报价页](https://www.cboe.com/delayed_quotes/nvda/quote_table) | 延迟 JSON 曾实测返回；随后核查页面限制 | 当前期权快照包含 IV、Delta、OI | 不提供本任务所需的免费历史回补；页面明确禁止自动提取，因此不采用该网页接口作为采集管线 |
| Yahoo Finance | 期权接口实测 HTTP 401 | 本次没有取得可用响应 | 不能认定已具备可持续访问，也未验证历史链能力 |
| [OptionsDX](https://www.optionsdx.com/product/nvda-option-chains/) | 产品页及字段说明核查 | 可下载历史期权样本和部分旧年份数据 | NVDA 产品页所列年份为 2016–2023，不覆盖本任务最近一年；[字段表](https://www.optionsdx.com/option-chain-field-definitions/)未列 OI，免费文件也需结账流程 |
| [Alpha Vantage](https://www.alphavantage.co/documentation/#historical-options) | 官方 IBM 历史示例成功返回；权限文档核查 | 示例包含 IV、Greeks、OI | `HISTORICAL_OPTIONS` 是 Premium 功能；成功调用 demo 不等于免费取得任意股票和日期 |
| [ORATS](https://orats.com/docs/historical-data-api) | 官方文档核查，未认证调用 | 文档列出历史合约、曲面相关数据、IV Rank 等 | 需要付费凭据；尚未做样本验收。其 underlying 参考值来自期权平价推导，实际股价仍应另取 |
| [IBKR Singapore](https://www.interactivebrokers.com.sg/en/trading/ib-api.php) | 用户确认已有账户；官方文档核查，未登录或调用账户 API | 可通过 TWS/IB Gateway 获取当前期权报价、模型 IV 与 Greeks，适合验证后持续采集 | 需核验 PRO、资金及行情授权；已到期期权与期权 EOD 历史不提供，无法单独回补一年短期期权指标 |

以上“文档核查”均不等于数据接入成功。没有因为产品名称包含 options、IV 或 historical，就将其记为可用主源。

### DoltHub 抽样结果

来源：DoltHub `post-no-preference/options`，`option_chain` 表。2026-11-13 单日查询结果如下，查询上限为 1,000 行，实际返回 556 行：

| 标的 | 返回合约行数 | 到期日数量 | 最近到期日 |
| --- | ---: | ---: | --- |
| NVDA | 154 | 4 | 2026-11-27 |
| MU | 212 | 4 | 2026-11-27 |
| ORCL | 190 | 4 | 2026-11-27 |

同一来源对 2025-11-17、2026-06-15、2026-06-16，以及 2026-11-02 至 2026-11-12 的若干交易日查询也返回了这三个标的。但这些是抽样，不能据此宣称最近一年逐日完整。

期限缺口会影响固定期限指标。例如 DoltHub 在 2026-11-03 返回的 ORCL 最近到期日为 2026-11-20，相距 17 个自然日；若目标指标需要 14 日期限，当天没有更短端可以夹住目标期限进行插值。直接外推会增加模型假设。2026-11-13 的 NVDA 样本另有一条 bid 大于 ask，后续必须剔除或标记。

字段 `vol` 是隐含波动率，不是成交量。持仓量字段缺失意味着无法从此表计算逐日持仓量变化。另一个 `volatility_history` 表虽然有 `iv_current` 等汇总字段，但未确认其期限、Delta 和聚合方法，不能直接认作博主的 IV 序列。跨一年查询该表本次超时，未把超时判为无历史数据。

原始响应：`sources/providers/dolthub/options/audit-20261116T023516Z/`。每个响应保留 SQL；初始请求 URL 见 `manifest.json`。公共查询入口为 `https://www.dolthub.com/api/v1alpha1/post-no-preference/options/master?q=<URL编码SQL>`。仓库随附 CC BY-SA 4.0 许可，后续衍生数据应保留来源与许可信息；上游报价采集及计算过程尚未核清。

### OnclickMedia 可访问与不可访问的边界

来源：OnclickMedia 的 `backtest` 服务日期查询。NVDA、ORCL 日期列表始于 2008-01-02，MU 始于 2013-01-02，均止于 2026-10-19。在本次研究区间 2025-11-16 至 2026-11-16 中，各列出 231 个日期；这只是索引数量，不是成功下载的期权链天数。

已验证入口例：`https://backtest.onclickmedia.com/?ticker=NVDA&list=date`。向同一根路径加 `date` 参数仅返回 API 用法说明，没有返回期权链。它不是已验证的期权链下载接口。

网站 About 页自述免费、无需密钥、数据来自 Yahoo 和其他公开渠道；但本次实际访问 `/doc-options` 返回 HTTP 401，`/documentation` 和报价页面显示维护。About 页还写回测数据截止 2026-03-05，与日期索引返回的较晚日期不一致。因此应以接口样本验收为准，不能直接采信网站宣传的覆盖和开放程度，也不把网站所述前端模拟期权价格当作真实历史报价。

原始响应及网页快照：`sources/providers/onclickmedia/audit-20261116/`。

### IBKR 新加坡现有账户：门槛与历史缺口

核查日期 2026-11-16；以下是官方文档能力，尚未在用户账户实测。

- [API 行情要求](https://www.interactivebrokers.com/docs/general/market-data-subscriptions/market-data-requirements)列明：真实 IBKR PRO 账户、账户内至少 500 美元且另有足够金额支付订阅费、相应行情订阅，并启用 API 行情访问。新加坡[价格页](https://www.interactivebrokers.com.sg/en/pricing/market-data-pricing.php)将个人账户的 500 美元或等值门槛定义为账户净资产要求，不是额外开户费。
- [TWS API 本身免费](https://www.interactivebrokers.com/support/faq/content/tws-api-free-download-29091390)；行情收费另计。新加坡价格页的非专业用户月费：OPRA L1 为 1.50 美元，股票 Network A、B、C 各 1.50 美元。按此相加，OPRA 加一个股票网络为 3 美元/月，OPRA 加 A/B/C 为 6 美元/月；未计适用税费或佣金减免，最终以账户可订阅报价和身份分类为准。专业用户不适用这些价格。OPRA 的佣金减免条款见同页，不将表内示例视为所有组合的统一减免规则。
- [Options & Greeks](https://www.interactivebrokers.com/docs/tws-api/doc/md/option-greeks)明确要求同时订阅期权与标的行情才能取得 Greeks；API 返回的 IV 来自 TWS 模型。仅订 OPRA、或在手机中看到免费股票报价，不足以证明 API 的全部字段可用。用 IBKR 值复现作者指标仍需核对模型、取点和取样时刻。
- [Market Data API Acknowledgement](https://www.interactivebrokers.com/docs/general/market-data-subscriptions/compliance-requirements-for-api-market-data/market-data-api-acknowledgement)需在 Client Portal → Settings → Market Data Subscriptions 中开启并签署。采用 TWS API 路线还需要运行并登录 TWS 或 IB Gateway、启用接口；研究用途可保留 Read-Only API。参见[官方安装配置课程](https://www.interactivebrokers.com/campus/trading-lessons/installing-configuring-tws-for-the-api/)。
- 新加坡价格页列出初始 100 路并发行情，TWS 与 API 共享。期权链会占用多路合约订阅，因此采集需筛选并分批；这不是可以一次订阅 100 条完整期权链。
- [TWS 历史数据限制](https://www.interactivebrokers.com/docs/tws-api/doc/md/market-data-limitations)明确不提供已到期期权和期权 EOD 历史数据。官方另有逐合约历史下载 FAQ，但不能据此推断可以取得过期链，也不能把 FAQ 中通用的日线/IV 请求示例当成每个期权合约均可返回的保证。

研究判断：IBKR 可作为从现在开始采集的优先验证候选；回补作者一年期 IV Rank、Skew Rank 所需的历史周到期期权链仍需其他来源。先核验现有行情订阅，再以少量标的检查双边报价、IV、Delta、到期日和日期一致性。没有开通订阅或连接用户账户。

本轮官方网页留存及获取状态：`sources/providers/ibkr/curry-audit-20261116/manifest.json`。

## 博主观点与原始资料的边界

同日后续取得作者长文、配图及相关讨论串，已确认 IV Rank 的输入是 14 天固定期限、50 Delta、总方差插值的 IV；Skew 的主口径是 25 Delta Put IV 减 Call IV，并取最近两个周到期、DTE ≥ 1 的均值；相关性则另用 14 天、30 Delta 序列与 15 对有效观测。排名图使用一年日期窗口，图上数字与 min–max 归一化吻合。供应商、部分取点和清洗细节、Skew 纵轴单位歧义及 Percentile 精确算法仍未确认。证据和原始链接见[作者方法核验](author-methodology-verification-2026-11-16.md)。

搜索所得 [ORCL 期权图表解读](https://finlab-research.pages.dev/research/orcl-options-chart-reading-report/orcl-options-chart-reading-report)出现 14D 50-Delta IV、Skew Slope、ΔOI、RR/BF 等术语，但页面是第三方 Howard 的个人学习笔记。它们只能作为待核查的数据需求，不能全部写成博主已经确认的标准体系，也不能用第三方解释补造作者公式。

## 与后续实施的关系

**研究判断：目前已能制定主要指标的数据验收条件，不足以交付“已忠实复现、可持续更新”的 Skill。** 主要定义已取得作者证据，供应商及精确实现的剩余问题仍需补证；按用户要求继续暂停接入和 Skill 编写。

| 任务 | 当前结论 |
| --- | --- |
| 股票日线、价格技术背景 | 可接入 FocusAlpha（`get_market_data`） |
| 财报、指引、事件背景 | FocusAlpha 目录有相应工具；应按具体案例取数核验 |
| 最近部分日期的 IV/Delta 结构 | DoltHub 已有可读样本，可做明确标注口径的探索 |
| 与作者同口径的 IV Rank、Skew Rank、收益率与 ΔIV 相关性 | 主要期限、Delta、窗口已核验；精确实现与同口径连续历史尚未验收 |
| 14 日固定期限曲面 | DoltHub 抽样存在短端缺口，不能默默外推补齐 |
| 最近两个周到期 Skew | 作者要求已经确认；DoltHub 抽样的较远期限链不能满足该要求 |
| ΔOI 及按持仓量划分的结构图 | DoltHub 缺字段；其他免费来源尚未实测补齐 |
| 免费、无需账户、每日持续更新的完整系统 | 未找到已经通过本次验收的组合 |

FocusAlpha 加 DoltHub 只保留为局部探索的候选，不作为作者体系的接入方案。若以后注册免费数据账户，可进一步实测 ThetaData EOD，并评估自行反解 IV 的误差；免费层仍不能补齐 OI。ORATS、Alpha Vantage 等付费产品只列为候选，没有购买或注册。上述候选均不是已经证实的作者行情来源。

完整实施前需要同时满足：作者原文与公式可追溯；实际样本包含目标期限及 Delta、连续历史和所需 OI；价格与期权数据的日期、复权方式和取样时刻可以对齐。数据缺失时输出缺失状态，不以实际波动率、市场 Beta 或其他供应商的汇总 IV 冒充目标指标。

## 引用位置

- FocusAlpha 原始工具响应：`sources/providers/focusalpha/curry-source-audit-20261116/dataset_catalog.json`、`market_data_nvda.json`。
- DoltHub 原始查询结果：`sources/providers/dolthub/options/audit-20261116T023516Z/`。
- OnclickMedia 原始响应：`sources/providers/onclickmedia/audit-20261116/`。
- 外部原始资料均位于 Git 忽略的 `sources/`；本核查结论位于 `research/`。没有创建 Skill、定时任务或付费订阅。
