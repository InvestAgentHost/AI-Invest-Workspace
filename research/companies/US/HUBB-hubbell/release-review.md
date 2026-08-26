# Hubbell 独立 Release Review（2026-08-26）

审阅对象：`Hubbell-deep-research-2026-08-26.md`、`source-index.md`、`coverage-matrix.md`、`evidence-ledger.md`、`validation-log.md`、`data/curated/companies/US/HUBB-hubbell/`。

**Release decision: PARTIAL**（不输出目标价或买卖建议）。

## 发现与决定

1. 报告作为 Hubbell 独立研究维护，未移植其他公司的事实、估值数字或业务假设。
2. SEC 五年 10-K、最新 10-Q、Q2 8-K Exhibit 99.1、三场用户上传会议纪要（S29-S31）和 DOE/IEA/EIA 已保存并以 `[Sxx]` 引用；IR 动态页、NERC/FERC 仍受阻，不能把 A2/B2 标为 pass。
3. 五年分部收入/经营利润/backlog/资产/capex/D&A 已重建；产品级利润、利用率、渠道库存、保修和数据中心审计拆分仍是缺口，S31 的约 10% Electrical 暴露仅作为管理层主张记录。
4. 2023 FIFO 比较性处理是主要财务风险：分部 Note 20 的 2023 assets 使用 7,081.1，而 strict 合并勾稽采用 FY2023 原始 6,914.0；报告解释差异，没有静默覆盖。
5. SOTP 倍数和 IRR 仅为透明模型假设；价格与股本非同日，租赁/稀释/潜在税项尚未完全进入 EV 桥，因此发布级状态只能是 `PARTIAL`。
6. 股息+回购在 IRR 中按现金回报处理，终端股数不减少；SOTP 每股值使用最新已发行股数，不重复加入回购增厚。

## Gate 复核

| Gate | 复核状态 | 复核意见 |
|---|---|---|
| A1 | pass | 来源 ID、URL、本地路径、日期和关键哈希可追溯 |
| A2 | partial | 动态 IR/NERC/FERC 与产品级 KPI 缺口已保留 |
| B1 | pass | 两分部的产品、收入确认、资本占用和失败路径可叙述 |
| B2 | partial | DOE/IEA/EIA 三角证据；监管/竞争资料不足 |
| C1 | partial | 分部覆盖完整但产品级经营指标缺失 |
| C2 | partial | 订单到现金闭环有证据，backlog 转化和产品现金不完整 |
| D1 | pass（字段范围） | strict calculator 10 个期间检查全部 pass；2023 口径限制显式 |
| D2 | partial | 三表/衍生指标完整，租赁和营运资本细分待补 |
| E1 | partial | 方法与边界透明，第二行情源、稀释和租赁待复核 |
| E2 | partial | 情景桥、分红/回购和双算规则存在，但倍数为假设 |
| R | PARTIAL | 按最弱 mandatory sub-gate 发布，不输出目标价或推荐 |

### R1-R3 子门

| 子门 | 状态 | 复核意见 |
|---|---|---|
| R1 Coverage/depth | PARTIAL | 主要分部、三表和数据中心三层机制已写；产品级 KPI 和独立监管证据不足 |
| R2 Method calibration | PASS | 章节结构和证据组织已完成内部一致性检查；未复用其他公司的事实、假设、数字或估值 |
| R3 Independent review/publishing | PARTIAL | 已完成独立审阅、strict 财务计算、git diff 检查和最终 full-report validator；资料缺口仍要求 PARTIAL 发布 |

## 机械检查

- `.venv/bin/python .github/skills/financial-statement-analysis/scripts/calculate_metrics.py ... --strict`：通过；证据 metadata issues=0。
- `git diff --check`：通过。
- CSV/JSON 解析、报告链接和源 ID 已完成会议纪要增补后的最终 `validate_research_release.py --full-report --strict`；结果 PASS（words=12773、H2=11、H3=65、tables=37、source_ids=17）。
- Git 工作区保持未暂存、未提交；未删除或覆盖既有文件。

## 发布前补做与剩余限制

- 已完成：从 10-Q Note 9/11 完成 2026YTD 分部/营运资本/债务更新，并抽样核对 8-K 表格。
- 已尝试但受阻：独立第二行情源；租赁负债、潜在税项、完全稀释股数和债务到期仍未全部进入 SOTP。
- 用替代公开报告补 NERC/FERC 可靠性/监管数字，或继续明确 unavailable。
- 已处理并发布 2026Q1、2026Q2 电话会和 Wells Fargo 会议纪要；IR 动态归档不可访问，官方/授权逐字稿仍缺失，保持 acquisition log 的 partial，不提高发布状态。

## 终稿复核增补（2026-08-26）

- 2026H1 分部、合并现金流、营运资本和 NSI 融资已从 S06 与 S20 核对并写入报告及 `operating_current.csv`。
- 第二行情源 Stooq 访问被 JavaScript 验证页阻断（S28/A13b）；未将其作为价格证据，估值仍按 `PARTIAL` 发布。
- EV ex leases 小数错误已修正；租赁负债、潜在税项、完全稀释股数和独立同业倍数仍是估值桥缺口，因此不改为正式目标价或买卖建议。
- 最终机械校验：strict financial calculator、CSV/JSON 解析与 `git diff --check` 均通过；发布状态保持 `PARTIAL`，原因是证据/估值缺口而非格式或勾稽错误。
- 本轮逐章重写已覆盖第 1-10 章：第 1 章 7 个子节；第 2 章 7 个；Utility 6 个；Electrical 6 个；数据中心 7 个；财务 11 个；资本配置/治理 8 个；估值 7 个；监测 2 个。章节逻辑和证据组织已统一为 Hubbell 独立研究口径，未复用其他公司的事实、业务假设或估值数字。
