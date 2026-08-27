# REIT 资料与证据清单

## 1. 来源优先级

1. 最新审计年报及财务报表/附注；
2. 最新中期、季度业绩稿和监管申报；
3. 官方投资者演示、业绩会纪要、租赁或交易公告；
4. 发起人/管理人正式公告；
5. 监管机构、规划/电力机构、行业协会和独立市场研究；
6. 券商、新闻和数据平台（仅作交叉验证，不能替代核心事实）。

## 2. 年报必查章节

- portfolio/property table：物业、面积、占用率、估值、土地期限；
- tenant/lease note：WALE、租约升级、到期墙、客户集中；
- revenue and property expense note：NPI、费用承担、电费回收；
- investment property valuation：cap rate、DCF、敏感性；
- borrowings/derivatives：债务、利率、币种、到期和套保；
- units and distributions：DI、DPU、单位数、管理费支付方式；
- acquisitions/disposals/development：对价、收益率、资本开支和交易边界；
- related parties/JV/ROFR：发起人交易、联营权益和治理风险。

## 3. 证据台账字段

每条关键数据至少记录：

| 字段 | 要求 |
|---|---|
| source_id | 与来源索引一致 |
| document | 标题、发布日期和报告期 |
| locator | 打印页/PDF 页、表格或注释 |
| original_url/local_path | 原始来源和本地副本路径 |
| as_of | 数据日期和访问日期 |
| scope | 集团、物业、JV、持股比例或分部 |
| currency/unit | SGD、USD、每平方英尺、MW、百万等 |
| status | fact / guidance / calculation / assumption |
| confidence | high / medium / low |
| contradiction | 与其他资料是否冲突及采用理由 |

## 4. 市场数据规则

价格、NAV、收益率和市值必须注明：交易所、证券类别、时间戳、币种、除权/除息状态、是否为历史收盘价。不同币种不得直接比较绝对价格；若需要组合回报，单独建立 FX 假设。

## 5. 资料缺口处理

当租户名称、单项租约、MW、到期墙或分部 NPI 未披露时：

1. 先检查年报附注、业绩会问答、监管公告和第三方交叉资料；
2. 仍不可得时标注 `未披露`，不要用行业平均值填充；
3. 说明缺口会影响哪个判断（租金、出租率、估值、DPU 或风险）；
4. 将相应结论降级为区间、情景或 `PARTIAL`。

## 6. 发布前证据检查

- 所有重大数值都能追溯到来源或可复算公式；
- 同一指标的币种、期间、合并边界和单位一致；
- 资料事实、公司指引和分析假设没有混写；
- 反面证据和未解决问题保留在报告中；
- 结论中的催化剂和风险都有对应的跟踪 KPI。
