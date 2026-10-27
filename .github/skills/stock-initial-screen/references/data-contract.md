# 数据、证据与汇总契约

## screen-v2 默认执行契约

新研究默认读本节及[修订规则](screen-v2.md)。后文旧版字段保留供`reverse-v1`回放，不能缺失版本标识后混用。

在Workspace用以下命令执行规范化、计算、验收、Markdown/HTML渲染：

```bash
.venv/bin/python tools/stock_screen/run_v2.py data/curated/screens/<run-id>/run.json
```

|位置|内容与所有权|
|---|---|
|`data/curated/screens/<run-id>/run.json`|时点、相对目录、财务窗口、并购边界、同行、明确来源的数值调整与口径桥接|
|同目录`assessments.json`|公司业务事实、判断分、反证、来源、置信度；与计算规则分开|
|同目录`guidance-records.json`|首次全年目标、同口径实际、发布日/申报日、原文URL/缓存、文字区间解释|
|`sources/screens/<run-id>/`|外部原始材料和原URL/哈希；不进入Git，不覆盖原件|
|`data/derived/screens/<run-id>/`|规范化财务、计算、评分输入/结果、台账、敏感性及验收；可重建|
|`research/screens/<run-id>.md`|耐久研究结论与完整公司卡|
|`outputs/screens/<run-id>/report.html`|同一结果渲染的本地可钻取报告|

v2评分输入仍含`rule_version/as_of/price_date/companies`。每家公司新增必需`metric_review`，与`B1..B5/M1..M5/I1..I5/B3a`共16个键一一对应：

- `reviewed`：有证据的数值评分。
- `provisional`：有显式假设/短历史的暂定情景，保留范围或上界，禁止自动优先。
- `evidence_limited`：规定材料检索完成但本轮不能数值评分，必须为null、附具体材料/范围和缺口。不能把未执行工作改此标签。
- `not_applicable`：经济上不适用，必须为null并解释。
- `pending_work`：必要工作尚未执行；禁止自动优先且交付验收失败。

`perimeter_years`为当前经济边界的完整年数；`provisional_history`表示数值使用前身/混合历史。少于三年时B1/B2/M3最多3且必须provisional。`price`包括正GAAP TTM、有效历史分位/年数、forward及短历史同业对照，无法构建历史分位时保留null。

每条证据含`company_id/metric_id/score/review/claim_type/claim/sources/value/limitations/confidence/as_of/locator`。`sources`逐份存`url/local_path`，路径相对Workspace，原URL与本地路径不得混同。定量分的`value`保存计算对象，不能只写结论。

唯一结果`scoring-results.json`由`tools/stock_screen/engine_v2.py`生成，增加`quality_floor`（缺项均取1的独立压力检查）、`quality_robust_to_unscored`、`stage_1_bounds`及`completion_status`。`complete_limited`只指有限覆盖的流程完成，不能称全部指标事实完整。正式质量通过但缺项压力不通过时为`quality_sensitive`，不能优先研究。

验收要求名单无重复/无漏项、每家公司三个维度及均分有值、16项逐项有记录、所有来源存在/哈希匹配、定量与输入/结果一致、无未来EPS、无pending、短历史有forward对照。Markdown与HTML直接使用相同结果；前端只筛选/排序，不重算分数。结构验收不等于全部来源事实已被独立审计。

---


## reverse-v1 旧版复现契约


## 路径和运行参数

从仓库根运行。`run-id` 建议为 `YYYY-MM-DD-<universe-slug>`；同日重跑用独立后缀，原始材料不覆盖。

| 内容 | 路径 |
|---|---|
| 外部财报/价格/行业文件 | `sources/companies/<market>/<ticker>-<slug>/` 或 `sources/screens/<run-id>/` |
| 原始来源清单与本轮元数据 | `sources/screens/<run-id>/manifest.json` |
| 提取值、证据账本、评分输入/输出 | `data/derived/screens/<run-id>/` |
| 耐久结论、方法选择、待核验问题 | `research/screens/<run-id>.md` |
| 生成HTML与图形 | `outputs/screens/<run-id>/` |

运行参数至少包括 `as_of`、`price_date`、规则版本、公司名单、财务窗口、B3a基期、经营资本定义、税率算法、分部选择、同行与剔除规则、估值来源/口径/起点/分位算法。源文件保存原始URL、内容日期、取得日期及本地相对路径；固定窗口、价格和数据版本，才能解释下次运行的变化。

## 证据账本

一条记录对应某公司某指标的一项支持或反证。以下字段可保存在 JSONL 或表格中，不强制庞大数据库：

| 字段 | 内容 |
|---|---|
| `company_id`, `metric_id`, `evidence_id` | 稳定发行人标识、B1等、来源记录ID |
| `claim_type` | source_fact / company_claim / calculation / judgment / inference / unresolved |
| `claim`, `direction` | 主张；support / contradict / context |
| `source_id`, `url`, `local_path`, `locator` | 原始来源、相对路径、页码/章节/段落 |
| `published_on`, `retrieved_on`, `period` | 发布时间、取得日、财务/业务期间 |
| `value`, `unit`, `currency`, `basis` | 数值、单位、币种及GAAP/调整/合并等 |
| `reasoning`, `confidence`, `limitations` | 对档位的解释、high/medium/low、局限 |

每个评分汇总另存：原始输入、公式、规则条款、支持/反对证据ID、分数、缺失原因、评分判断。对子项保留 B3a/B3b、M3三列、M4a/b、I4a/b及分部权重。报告输出引用具体证据，而不是只写供应商名称。

未披露为 `not_disclosed`，未取得为 `not_retrieved`，经济上无意义为 `not_meaningful`，历史不足为 `short_history`，规则缺失为 `rule_undefined`。这些状态在计算输入中均为 `null`，说明写在 `missing_reasons`。不能用0、-1或字符串“-”冒充缺失数值。

## 汇总脚本输入

`scoring-input.json` 是从证据账本导出的计算接口，**不是证据账本的替代品**。仅接受 `rule_version = reverse-v1`。

下面是纯虚构的接口例子，不得作为真实公司证据：

```json
{
  "rule_version": "reverse-v1",
  "as_of": "2026-10-20",
  "price_date": "2026-10-19",
  "companies": [
    {
      "company_id": "US/EXAMPLE",
      "name": "Synthetic example",
      "perimeter_years": 10,
      "scores": {
        "B1": 4, "B2": 4, "B3": 4, "B4": 4, "B5": 4, "B3a": 3,
        "M1": 4, "M2": 3, "M3": 3, "M4": null, "M5": 4,
        "I1": 4, "I2": 4, "I3": 4, "I4": 3, "I5": 4
      },
      "missing_reasons": {"M4": "not_disclosed: no comparable first guidance"},
      "blocking_issues": [],
      "review_flags": ["M4 unavailable; management factor uses four measures"],
      "price": {
        "trailing_pe": 18.5,
        "percentile": 25.2,
        "history_years": 10
      }
    }
  ]
}
```

要求：

- 16个评分键全部存在，B3a不计入商业维度五项平均。B、M及B3a为1–5整数；I可用1–5小数以容纳分部加权。
- `null` 必须给非空缺失原因；B1/B2/M3在 `perimeter_years < 3` 时必须为空。`perimeter_years` 是当前边界下可用完整财年数，不是上市周年数。
- `blocking_issues` 用于足以改变门槛且未解决的问题，如B1负资本例外、P/E减值失真或关键资料冲突；非阻塞提示放 `review_flags`。
- 分位为0–100的百分数，历史长度为年。只有当正TTM P/E、有效分位、正的历史长度都具备时才存在有效档位。无意义的P/E配 `percentile: null`，不传负数分位。
- 输入分数必须已经依据证据复核；未经核实的淘汰理由不能先填成1分。
- 引擎使用 Decimal 做half-up；维度按一位小数后判断质量。排序平均使用三维已显示分数的算术平均、展示两位小数。

## 分类顺序与输出

| 顺序 | 条件 | 机器状态 |
|---|---|---|
| 1 | 有证据的B1=1或M5=1 | `removed` |
| 2 | 有blocking issues、必需硬门槛缺失或当前边界不足3年 | `manual_review` |
| 3 | 已有数据可证实Stage 1失败 | `fails_stage_1` |
| 4 | Stage 1仍未知，或任一维度缺两项以上 | `manual_review` |
| 5 | 质量通过且有效分位≤100/3 | `research_now` |
| 5 | 质量通过且100/3至200/3 | `watch_closely` |
| 5 | 质量通过且分位>200/3 | `watchlist` |
| 5 | 质量通过但无有效估值 | `quality_pass_valuation_unavailable` |
| 5 | 质量未通过且处底部三分之一 | `cheap_fails_quality` |
| 5 | 质量未通过且非底部/无有效估值 | `ignore` |

若B1已知不足3，即使B2或B3a缺失也已能证实Stage 1失败；如果B1满足但其余门槛缺失，则不能推定通过。

排序：可行动的质量通过组、失败组、人工/估值待评组、硬淘汰组；每组按三维平均降序，平均缺失置末，同分按稳定公司ID。`removed`并不删除记录。每家公司输出各维度未舍入/显示均值、缺项、Stage 1状态、质量状态、估值档位、结论、原因及提示；总计覆盖整份名单。

## 引擎不承担的验证

脚本不能证明资料真实、同行合理、单项阈值正确或评分证据充分，也不会补齐参考文件中未披露的中间档位。数据获取、十五项打分、每日P/E序列构建、分位计算、引用和HTML呈现由执行 skill 的 agent 完成。

原样本完整重放可能与 `reverse-v1` 的人工复核结果不同，应同时保留 `source_verdict` 和新输出并解释差异；不能把样本基准答案硬编码进引擎。
