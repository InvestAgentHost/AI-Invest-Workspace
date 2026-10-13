# 交接与持续更新

## 最小记录

复用现有台账；需要新增时，已采用小配置/决策放 data/curated/companies/<market>/<company-id>/valuation/，快照/校验放 data/derived/companies/<market>/<company-id>/valuation/<as-of>/，原件在 sources/companies/，交付底稿沿用 research 输出路径。仓库相对路径，不把公司数据放工具目录。遵循对话/文件交付要求，不擅改个人 Word。

[handoff-template.json](../assets/handoff-template.json) 是字段骨架，可拆四份或嵌入已有台账：

1. 配置：公司、版本、财年、单位、估值日/实际期、资料/产物、投资逻辑、反证与重审阈值。
2. 指标/参数：稳定 ID、定义/范围、公式/依赖、历史窗口、数值证据、逐期采用值、Excel 映射、更新规则。
3. 人工决策：日期、建议、采用值、原因、适用期、是否锁定、重审条件。Excel 手改也要记，不能只记聊天批准。
4. 更新/验证：前版快照、新源、实际对旧预测偏差、参数变化、估值归因、检查和未决问题。

来源路径、URL、披露/访问日、定位、hash 可引用已有索引，不重复全套事实。指标 ID 拥有语义，地址只属可变映射。

### 字段填写约定

模板中的 metrics 对象是单项骨架，按公司真实指标增减；空数组需要按以下记录填入：

- sources：id、path、locator、content_date、access_date、url 或 provider_reference、evidence_type（source_fact/company_claim/guidance/third_party）；hash/覆盖限制尽量引用既有台账。管理层指引仍是前瞻证据，不能标成已实现事实。
- history：period、value、disclosure_status（reported/calculated/unavailable/n.a.）、source_ids；calculated 还须 formula。数值单位和范围继承 metric；缺失 value=null，真实零 value=0。
- adopted：period、value、status（adopted/pending/unavailable）、decision_id、evidence_ids。已采用值与对应 decision.values 必须一致；待决/缺失不用零占位。
- decisions：id、metric_id、date、origin（analyst/chat/workbook/authorized_ai）、values（期间→采用值）、reason、locked、review_condition。记录 AI 建议可加 proposed_values，保留与采用值的差异。
- history_window：annual_periods、quarter_periods 为选定完整窗口的期别列表；选择理由和季节性上年同期覆盖另外记录。
- forecast_layout：section（remaining_quarters/future_years）、sheet、row、forecast_columns（Excel从1起列号）、history_cells；每个 history_cell 含 period、column、actual_sheet、actual_cell。每个块列全选定历史，行由本 block.row 指定，同指标对齐。
- workbook_mapping：sheet、section、period、cell、role（actual/input/formula/output）。详细映射在索引区，主预测区不堆内部 ID。
- updates：as_of、previous_snapshot_path、new_source_ids、actual_vs_forecast、input_changes、valuation_attribution、review_triggers_hit、checks、unresolved。actual_vs_forecast 保留原预测版本、实际数值、差异与原因；checks 记录计算、证据、工作簿保真、版面各自状态。

核验器检查记录结构与预测右侧映射声明，不直接打开原始来源或 Excel；真正发布前必须检查声明与实际文件一致。初次构建 previous_snapshot_path 可为空，后续更新必须有旧快照。validation.status 不能只因结构检查通过就升级为研究 PASS。

已采用输入唯一有效版本：推荐结构化 adopted 层→Excel 链接。用户手改 Excel 时先检测差异，登记 workbook-origin 决策并同步 adopted 层，不用旧记录改回。不能实现链接时保留双向映射/差异检查，不宣称自动同步。

## 更新策略

重要指标选择一类，声明规则、阈值、来源：

- actual_or_formula：新实际/明确依赖自动更新，重述保留桥。
- guidance_rule：按已确认指引规则调整，保留条件；指引口径变更重新判断。
- analyst_review：对照新证据提出调整与影响；已有授权允许研究判断更新则继续并留痕。
- locked：保持采用值，禁止静默覆盖。实际仍照常更新；锁定假设失效列待决，不扭曲实际迎合假设。

无外部项目正式阶段产物时用现有底稿/报告恢复。恢复不了标 unresolved，不伪造批准记录。

## 每轮流程

1. 检查工作簿、手动修改、旧决定、前版快照、业务边界；保留可恢复版本。
2. 取本轮披露、纪要、市场数据，记录截止日与原始来源，不覆盖旧源。
3. 实际替换预测并保留旧预测，算金额/比率误差及经营原因，不只比 EPS。
4. 复核未实现季度与未来年度的驱动、指引、行业假设；只更新受影响依赖。
5. 重算全年利润、现金、股份、EPS、估值；滚期不跳过过渡现金流。
6. 独立计算、来源/版面验收，同步报告需变动处或交付文本，记录 PASS/PARTIAL/BLOCKED。

区分市场、实际业绩、预测、时间滚动、方法口径的估值变化。按固定顺序替换归因时记录顺序及交互残差，不当作唯一因果贡献。

## 重审

阈值由公司风险设定，不统一套涨跌幅。商业模式/边界改变、利润机制失效、资本强度/融资约束持续跃迁、会计质量/治理风险变化、长期需求竞争前提失效，可能触发投资逻辑重审。

保留旧模型比较，说明哪条前提失效、可以继续查什么、需重新决定什么；不无条件沿用旧 PE/转换率/增长。普通季度波动与预期内周期不是重大转变，不重复问已授权步骤。

本 skill 是执行方法，不是后台调度器。用户另行要求监控才接产品自动化，不额外装 cron、上传或发消息。
