---
schema_version: research_foundry_official_site_deliverable.v1
document_type: important_information
target_name: OTLY-oatly
as_of: '2026-10-20'
snapshot_id: oss_c753e0a1cd4fab82f112
run_id: run_218d0e7dbefa4eaf87f5a5971ca97570
quality_status: partial
---

# 官网重要信息与采集限制

截至 2026-10-20；本文件是官网采集材料的清洗导航，仅转述与定位公司披露，不包含投研判断。官网表述均为 `COMPANY_CLAIM`，未作独立核验。

## 已准备的说明材料

| 内容 | 来源 |
|---|---|
| Sustainability / Oatly | [O0012:L1-L271] |
| 17 facts about Oatly and nutrition / Oatly | [O0017:L1-L259] |
| Random Answers & FAQ / Oatly | [O0016:L1-L171] |
| Oatly Sustainability Update 2024 / Oatly | [O0094:L1-L867] |
| Oatly Sustainability Update 2023 / Oatly | [O0095:L1-L1065] |
| Sustainability report 2022 / Oatly | [O0096:L1-L1287] |

## 质量状态：PARTIAL

- IR homepage, corporate-governance page and press-release archive could not be preserved as full raw pages because the server returned HTTP 403. Browser fallback timed out. SEC annual/interim filings remain fully acquired in the separate SEC route.
- The IR listing identifies a 2025 sustainability report; that full report could not be downloaded from the blocked IR domain. Available main-site HTML sustainability reports are 2024, 2023 and 2022; do not label the 2024 report as the latest report.

## 使用方法与边界

所有 source alias 对应 sources.jsonl，原始字节、SHA-256、清洗路径及行数可回查。日期不明的页面保留 unavailable，不使用采集日代替内容日。英语主站快照不等于全球各语言站点的完整镜像；网页中的营养、环保和品牌主张仍属公司口径。首页、新闻入口、F.A.R.M. 空页面和 schoolmilk 引导页内容较少，已注明不可作为实质证据。
