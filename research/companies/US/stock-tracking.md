# 公司投资逻辑跟踪入口

当前索引版本：2026-11-03-v3。下列保留原四家公司与后续接入历史，PEP及MNST研究条目见文末。各公司研究日期、成功覆盖点和调度独立记录，不代表已检查截至本日的全部最新信息。

| 公司 | 独立规则 | 当前保留基线 | 模型边界 |
|---|---|---|---|
| ADSK | [rules.md](ADSK-autodesk/tracking/rules.md) | [2026-10-21.md](ADSK-autodesk/tracking/baselines/2026-10-21.md) | 逻辑信号；不依赖 Excel |
| KO | [rules.md](KO-coca-cola/tracking/rules.md) | [2026-10-21.md](KO-coca-cola/tracking/baselines/2026-10-21.md) | 指定 KO_model.xlsx 只读；修改先汇报、讨论并取得明确许可 |
| LIN | [rules.md](LIN-linde/tracking/rules.md) | [2026-10-21.md](LIN-linde/tracking/baselines/2026-10-21.md) | 逻辑信号；不接估值模型 |
| MCD | [rules.md](MCD-mcdonalds/tracking/rules.md) | [2026-10-21.md](MCD-mcdonalds/tracking/baselines/2026-10-21.md) | 指定底稿只读；修改先汇报、讨论并取得明确许可 |

执行方法：[stock-thesis-tracking](../../../.github/skills/stock-thesis-tracking/SKILL.md)。在 Workspace 内调用 `$stock-thesis-tracking` 并指定公司规则或本清单。无需 Excel 写权限即可完成逻辑跟踪；材料不全时保留缺口，不为“接通”而修复原件。

## 基线来源和状态

本地恢复依据：先前只读材料梳理任务 `01a158b8-c178-73cc-87ed-8d1a7082800a` 的 `read_only_review/tracking_framework_review.zh-CN.md`，检查日 2026-10-20，SHA256 `e2a92ee31412b1fae72b2c0032d7f859aca5f52231bd36ccf05a45baf0423a57`；各公司基线列出其所据原研究路径与本次只读指纹。该产物的检查范围和缺口继续有效；本次未重做全量分析。公司报告中的数值不因摘录进入规则而升级为官方已核实值。

用户已确认四公司逻辑主线、正反证跟踪、重要事件才单独提醒、其他入日报，以及 Excel 变更的人机参与边界。未确认统一数值阈值、夜间重大提醒或模型自动写权限。保留旧基线，后续批准形成新版本，不覆盖现有判断以消除反证。

## 独立调度与规则同步

据父线程 2026-10-21 状态同步：独立的公开信息日报任务已启用，从 **2026-10-22 起每天 UTC+8 08:30（Asia/Shanghai，UTC 00:30）** 向主聊天交付。该状态由父线程报告，本地安装任务未另行检查/修改 automation。

本地 Skill 是手动研究和新公司接入入口；定时日报由正式 automation 独立执行、使用同一份已确认逻辑，不依赖 Mac 在线。**云端不会因本地安装而自动调用此 Skill，也不能据此声称读取了最新本地 Word/Excel、手工参数、历史台账或规则修改。** 本地未建立 cron、launchd 或其他后台服务。夜间重大提醒未获确认。

规则同步锚点为 `2026-10-21-v1`：后续每次修改公司命题、权限或重要反证，都在人工决定记录中注明版本和差异，并向父线程交付需要同步的规则文本，由其核对独立 automation。未获同步结果前标“调度规则同步待核对”，不可写自动同步完成。定时运行的公开信息历史与本地研究历史分别记录覆盖和交付状态，合并前核对窗口与事件去重。


## 2026-10-26 扩展至七家公司

当前索引版本：**2026-10-26-v1**。以上为原四家公司初始化记录，规则和 2026-10-21 基线保持原文；本次仅追加 OTLY、COCO 和伦敦 CCH。三家均处于**初筛后跟踪**，动作状态统一为**跟踪**；采用分析师 2026-10-26 周会判断，不因接入启动深度研究。CCH 独立位于 UK 目录，不能混同美股 KO。

| 公司/市场 | 独立规则 | 当前保留基线 | 周会重点与资源 | 模型边界 |
|---|---|---|---|---|
| OTLY / US Nasdaq ADS | [rules.md](OTLY-oatly/tracking/rules.md) | [2026-10-26.md](OTLY-oatly/tracking/baselines/2026-10-26.md) | 事件驱动；后续业绩、修复持续性、展期/再融资、潜在资产处置及股东权益。保留 2026-10-21 排除历史；当前跟踪。 | Word/Excel 只读，不建立模型运行依赖 |
| COCO / US | [rules.md](COCO-vita-coco/tracking/rules.md) | [2026-10-26.md](COCO-vita-coco/tracking/baselines/2026-10-26.md) | 持续跟踪重要经营变化和重大事件；后续安排深度研究资源，本次不启动。 | Word 只读，无新增模型 |
| CCH / UK 伦敦 | [rules.md](../UK/CCH-coca-cola-hbc/tracking/rules.md) | [2026-10-26.md](../UK/CCH-coca-cola-hbc/tracking/baselines/2026-10-26.md) | 等待价格回落及 CCBA 事件落地；当前不投入增量资源，实质变化后复评优先级；价格阈值未设。 | Word 只读，旧估值不转自动阈值 |

三家周会历史： [OTLY](OTLY-oatly/tracking/decisions.md)、[COCO](COCO-vita-coco/tracking/decisions.md)、[CCH](../UK/CCH-coca-cola-hbc/tracking/decisions.md)。报告指纹、报告日期与财务覆盖缺口见各自基线；仅做接入，不冒充已检查最新公开信息。现有 `company.yaml` 的 `watchlist`/`initial-screen-follow-up` 与上述状态一致，本次保留未提交公司档案和历史结论。

### 当前统一运行和云端同步记录

七家公司均沿用 **每日 08:30 UTC+8（Asia/Shanghai，UTC 00:30）**，生成后发送至原主聊天；重要事件在当次交付中单列，**无额外夜间或盘中提醒**。本次不创建或修改任何自动化、cron、launchd 或软件。原四家命题、基线及 Excel 审批边界继续有效，新增三家同样不获底稿写权限。

父线程 2026-10-26 告知已将原云日报扩展为七家公司，保留原调度与四家规则；本地记录“父线程已更新”，并未直接核对 automation 配置、实际运行或发送结果。本地规则版本 `2026-10-26-v1`；云端不能据此声称读取了本地报告、模型或台账。

可同步/复核的简短差异：OTLY 跟踪经营修复、债务展期/再融资、潜在资产处置与股东权益，历史排除仅作旧判断；COCO 持续记录重要经营与重大事件，深度研究待资源；伦敦 CCH 等价格回落与 CCBA 落地，无已设价格阈值、当前不投入增量资源，实质变化后提优先级复评。CCH 报价 GBX/GBp 为便士，换 GBP 除以 100，不把报告 £42–43 建议采用为阈值。三家未补做外部扫描，未设数值或自动投资结论；仅按成功覆盖范围报告，没有取得证据记待补/待验证。

## 2026-11-02 PEP 深度研究完成后接入

| 公司/市场 | 独立规则 | 保留基线 | 跟踪范围与权限 |
|---|---|---|---|
| PEP / US Nasdaq | [rules.md](PEP-pepsico/tracking/rules.md) | [2026-11-02.md](PEP-pepsico/tracking/baselines/2026-11-02.md) | 北美食品/饮料修复、国际增长质量、现金回报与资本配置、改革治理；报告及底稿只读，模型变更需具体授权 |

PEP主报告与Elliott补充研读见[归档索引](PEP-pepsico/archive.md)，后续研究采用已有报告判断、[跟踪规则](PEP-pepsico/tracking/rules.md)与保留基线。当前来源覆盖及旧事件去重线索见[2026-11-03接续记录](PEP-pepsico/tracking/history/2026-11-03-continuation.md)，研究与模型边界见[decisions.md](PEP-pepsico/tracking/decisions.md)。不新增价格阈值或自动交易条件。

PEP于2026-11-03纳入原合并日报，当前跟踪池为ADSK、KO、LIN、MCD、OTLY、COCO、伦敦CCH、MNST、PEP，共九家公司。沿用每日北京时间08:30、原交付位置、既有提醒及正式新业绩独立分析规则。PEP财报、指引及持仓先查SEC和权威网络来源，历史FocusAlpha记录保留；报告及Excel继续只读。

## 2026-11-03 MNST 初研归档与跟踪接入

| 公司/市场 | 独立规则 | 保留基线 | 当前判断与权限 |
|---|---|---|---|
| MNST / US NASDAQ | [rules.md](MNST-monster-beverage/tracking/rules.md) | [2026-11-03.md](MNST-monster-beverage/tracking/baselines/2026-11-03.md) | **初筛后跟踪；暂不深研，主要等待估值回落。** 无已确认数值阈值；原 Word／Excel 及历史结论只读。 |

用户于 2026-11-03 明确要求归档 MNST 初研报告，并在归档后加入既有每日跟踪任务。沿用已有 [MNST 公司目录](MNST-monster-beverage/README.md) 和管理层研究，不重复建公司；上传原件已原样归入 `sources/companies/US/MNST-monster-beverage/user-provided/2026-11-03/MNST.docx`，原惯例收件入口使用相对符号链接。报告 SHA256、不同财务覆盖期及历史估值口径缺口见 [materials.md](MNST-monster-beverage/materials.md)；接收日不是报告日期，不把旧场景转为现行买点。

**MNST 于 2026-11-03 已接入既有合并日报**，沿用每日北京时间 08:30（Asia/Shanghai，UTC 00:30）和新业绩独立分析规则；平时轻量跟踪估值与实质变化，不自动启动深研，无额外盘中／夜间提醒。采用状态及权限见 [人工决定记录](MNST-monster-beverage/tracking/decisions.md)。
