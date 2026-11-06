---
type: company-data-preparation
company_id: US-COCO-vita-coco
as_of: 2026-11-03
status: partial
---

# COCO 数据准备交付 · 2026-11-03

本轮完成SEC原始披露获取、预处理、索引和检索验证，及第一方官网资料聚合。**SEC范围PASS，官网PARTIAL，整体PARTIAL**。本轮未制作Excel、财务标准化时序或研究章节；原初筛Word与投资判断保留。

## 财报及公告范围

- 上市以来FY2021–FY2025完整10-K：5份。
- 最近四个已披露季度：FY2025Q4、FY2026Q1、FY2026Q2、FY2026Q3。保存2026年三个季度的10-Q及各季业绩8-K/EX-99.1；另保存2025Q3 10-Q供第四季度期间核对。Q4由年度10-K及全年业绩公告覆盖，不存在单独Q4 10-Q。
- IPO最终招股书424B4：1份。
- 共18份SEC文档均直接从SEC公开端点取得。未发现当前申报目录中属于该年度/季度范围的10-K/A或10-Q/A，未引入第三方补数。

来源：本次[SEC原始申报目录](../../../../sources/companies/US/COCO-vita-coco/sec/2026-11-03/metadata/sec-submissions.json)及[来源索引](data/context/2026-11-03-source-preparation/source-index.md)。原始目录访问日为2026-11-03。

## 预处理与可用性

原始HTTP字节及SHA-256单独保存；通过技能内置SEC HTML流程生成不可变Prepared包、Markdown、结构化块、XBRL元数据、清理报告和章节/表格/文本索引，并逐包验证。九份年季报的三张主表完成27项定位和回读检查。

SEC预处理文本共27,548行，索引表格条目546个；条目包含封面和说明表，不等同财务指标数量。IPO嵌套结构的机械章节索引粒度较粗，已补充535个原始table候选、299个标题标签的结构目录；完整原文保留。上述统计来自本轮生成的[验证记录](../../../../data/derived/companies/US/COCO-vita-coco/2026-11-03/data-preparation-validation.json)，仅描述资料处理结果。

季度、累计期间、原单位、比较列、空白及零均保留在来源中。本轮不计算Q4差额、不制作重述桥或标准化财务序列，也未声称已完成会计勾稽。

## 官网资料

官网26个页面已准备并索引：18个品牌站HTTP原始HTML、8个IR网页工具文本快照，全部来自公司/品牌官方URL；公司自述不升级为独立事实。目录含产品条目及少量已核对的动态来源，不代表全量历史新闻或全部合并业务。

- [业务与产品资料聚合](../../../../sources/companies/US/COCO-vita-coco/official-site/2026-11-03/artifacts/official_site/COCO-vita-coco/2026-11-03/oss_284ce8049fccbe4e9e6d/deliverables/business_and_offering_handbook.md)
- [战略与动态资料聚合](../../../../sources/companies/US/COCO-vita-coco/official-site/2026-11-03/artifacts/official_site/COCO-vita-coco/2026-11-03/oss_284ce8049fccbe4e9e6d/deliverables/strategy_and_developments.md)
- [公司信息及使用说明](../../../../sources/companies/US/COCO-vita-coco/official-site/2026-11-03/artifacts/official_site/COCO-vita-coco/2026-11-03/oss_284ce8049fccbe4e9e6d/deliverables/important_information.md)

官网限制：IR原始HTML和最近四季演示PDF仍返回403；IR文本可能来自近期工具缓存，已注明表示形式。新闻历史、动态门店目录、站外CDN的2025影响报告PDF未完整取得。保留链接和失败记录，不使用第三方替代。官网首页品牌介绍与近期新闻存在版本差异，留待后续结合SEC原文核对。

## 资料与检查入口

- [来源索引](data/context/2026-11-03-source-preparation/source-index.md)
- [逐文件指纹清单](data/context/2026-11-03-source-preparation/file-manifest.csv)
- [覆盖矩阵](data/context/2026-11-03-source-preparation/coverage-matrix.md)
- [预处理验证日志](data/context/2026-11-03-source-preparation/validation-log.md)
- [研究边界](data/context/2026-11-03-source-preparation/research-context.md)
- [来源差异与未决项](data/context/2026-11-03-source-preparation/evidence-ledger.md)
- [采集尝试与恢复](data/context/2026-11-03-source-preparation/acquisition-attempt-log.md)
- [本轮交付检查](data/context/2026-11-03-source-preparation/release-review.md)

原始资料统一保留于 `sources/companies/US/COCO-vita-coco/`；轻量入口由Git管理，原件、索引及数据准备产物仍在忽略目录中，跨设备需手工携带。
