# Hubbell 验证日志（阶段 0）

## 环境与能力检查（2026-08-26）

- 工作区：`/Users/tccc/Desktop/AI Invest/Workspace`；Git 分支 `main`，与其他公司研究的已有用户变更隔离，未触碰。
- Python：`.venv/bin/python` 3.12.13；`pandas`、`requests`、`bs4` 可用。
- 结构化数据：计划使用 pandas + 标准化 CSV/JSON；后续优先 SEC HTML/XBRL parser。
- 网络/官网：沙箱直连代理失败；经用户批准的联网权限使用 `curl` + SEC User-Agent 成功访问 SEC submissions（HTTP 200）和 Hubbell IR（HTTP 200）。
- PDF：`pdfinfo` 可用；未发现 `pdftotext`、`pdfplumber`、`pypdf`；年度报告 PDF 页面和表格若必须使用，将采用 SEC HTML/XBRL、浏览器/可用替代提取，并记录页码验证限制。
- 浏览器连接器：当前工具清单未提供可调用的浏览器 MCP；不把该能力当作已验证。
- Gangtise：技能目录和 `tools/gangtise/run.py` 存在；授权状态尚未检查，正式调用前验证环境变量和输出路径。
- 计算：计划检查并使用 `.github/skills/financial-statement-analysis` 的 strict 计算器；若缺失，使用透明的 `.venv` 计算脚本并将计算 gate 降为 `PARTIAL`。

## 研究方法与证据组织

- 报告采用：身份/边界 -> 行业需求链 -> 分业务经营闭环 -> 特定主题机会 -> 五年三表与衍生指标 -> 资本配置/治理/风险 -> SOTP/IRR -> 监测清单 -> 发布状态。
- 证据组织使用 `research-context.md`、`source-index.md`、`evidence-ledger.md`、`acquisition-attempt-log.md`、`coverage-matrix.md`、`segment-operating-units.md`、`validation-log.md`、`release-review.md`；先台账后叙事，区分事实/公司主张/分析计算/判断/假设/未解决。
- Hubbell 的路由和章节以 Utility Solutions、Electrical Solutions、Corporate/Other 的制造/硬件经济为准，所有事实、假设和估值数字均来自 Hubbell 研究范围内的来源或明确标注的独立资料。

## 阶段 0 gate 状态

| Gate | 状态 | 说明 |
|---|---|---|
| A1 Provenance integrity | partial | SEC/IR 入口和元数据已保存；五年原始文件尚未抓取 |
| A2 Evidence sufficiency | partial | SEC/官方/DOE/IEA/EIA 已取得；IR 动态、NERC/FERC、产品级 KPI 缺口保留 |
| B1 Economic intelligibility | pass | 两分部制造/分销、收入确认、资本占用和失败路径已验证 |
| B2 Triangulation | partial | DOE/IEA/EIA 可用；监管与独立竞争资料不足 |
| C1 Segment coverage | partial | US/ES 五年主表覆盖；产品级利润、利用率和渠道库存 unavailable |
| C2 Economic closure | partial | 订单/生产/交付/现金路径已建；backlog 转化和产品现金不完整 |
| D1 Reconciliation | pass | strict calculator 勾稽通过；2023 FIFO 限制显式记录 |
| D2 Analytical coverage | partial | 三表和衍生指标已生成；租赁/营运资本细分和部分 APM bridge 待补 |
| E1 Method/boundary validity | partial | 初步 SOTP + EV/EBITDA/FCF 交叉方向；dated market boundary 未取得 |
| E2 Model completeness | partial | SOTP/IRR 情景、净债务、股本、分红回购已建立；租赁、稀释和独立倍数缺口保留 |
| R1-R3 Release | partial | 完整报告和独立 release review 已完成；按最弱 mandatory sub-gate 以 `PARTIAL` 发布 |

## 当前校验

- 已保存并计算 SHA-256：SEC submissions JSON `978e2f497f6e6407210ea7a13a1ca72b01ed7fc789603cc6c846999ee52e9642`；IR home HTML `99de9b95e8108c0bf716d0804205185e1dc437c52cddcffcbe04cbcdea181570`。
- 正式 SEC intake 已完成第一批：S01-S05 10-K 与 S06 2026Q2 10-Q HTML、index.json 和 prepared `document.txt` 均已保存；原始文件哈希记录在 `source-index.md`（Company Facts JSON SHA-256 `cbad7cc261333e5397faf635864ab61db830df38d6e5540afb19bc8e2b60cfc2`）。
- 已保存 S20 Q2 2026 业绩发布 8-K Exhibit 99.1 并提取文本；该文件披露 Q2 净销售额同比增长 15%、调整后 EPS、FY2026 指引和 Utility/Electrical 分部经营讨论，均按公司主张/前瞻性处理。
- 已保存 S12 2025 年报/代理 PDF（186 页），使用 bundled Poppler `pdftotext -layout` 提取 925,851 字符；PDF 与 SEC HTML 的财务数字将抽样核对，不以官网再版覆盖 SEC。
- Hubbell GCS-Web 动态归档页多次空响应，已在 acquisition log 记录为 partial；SEC 8-K 展品和 10-K/10-Q 作为替代官方披露。
- 已生成 `financial_analysis/financial_timeseries.csv`（FY2021-FY2025，135 行）及 `financial_metrics.csv`（75 行）；Company Facts 选择规则为精确年度起止日 + 最新提交的 10-K fact，2021-22 CFO 使用 continuing-operations concept 以匹配公司 FCF 定义。`statement_mapping_ledger.csv` 记录概念映射、单位和口径限制。
- Company Facts 与 S01/S02 文本已完成勾稽：2025 revenue 5,844.6、consolidated net income 891.9、parent net income 887.1、CFO 1,029.8、capex 155.1、cash 482.5；完整三表、分部和 APM strict 复核通过，2023 FIFO 限制保留。
- 已按 `financial-statement-analysis` 的 statement-mapping、metric-catalog、input-schema 和 sector-overrides 建立 `financial_metrics_input_strict.json`，并运行 strict calculator；10 个资产/权益及母公司/NCI 勾稽检查全部 `pass`，evidence metadata issues=0。输出保存为 `financial_metrics_output.json` 与 `.md`。2023 资产负债表采用 FY2023 原始列并标记 FIFO 可比性限制，避免把 Company Facts 可能已重分类的单项事实直接混入。
- 已取得独立 Yahoo chart 行情（S27）：2026-08-25 NYSE 收盘价 $464.19；结合 S06 2026-07-23 流通股 52.832571m，生成 `data/curated/companies/US/HUBB-hubbell/market_snapshot.csv`。这是估值边界输入，不是目标价；价格与股本非同日且尚无第二行情源，估值 gate 保持 `PARTIAL`。
- 已运行完整发布校验：`.venv/bin/python .github/skills/company-investment-research/scripts/validate_research_release.py --full-report --strict`；结果 `PASS: no mechanical release findings`，指标 words=4035、h2=11、h3=29、tables=14、source_ids=14。机械通过不改变 A2/B2/C1/C2/D2/E1/E2 的定性 `PARTIAL` 状态。
- FY2025 10-K 初读已确认：两报告分部（Utility Solutions、Electrical Solutions）；2025 合并净销售额 5,844.6 百万美元；分部净销售额约 3,672.3/2,172.3 百万美元；2025 firm backlog 2,159 百万美元；前十大客户约占 42% 销售；主要产品收入在发货时点确认，少量 Utility 合同按履约进度确认。上述均为 S01 披露，后续在 evidence ledger 增加逐项定位。
- 阶段 0 文件尚未运行完整 release validator；正式报告和必需结构化产物形成后运行 `validate_research_release.py --full-report --strict` 及 `git diff --check`。
- Git 保持未暂存、未提交；未修改或删除其他公司的研究文件。

## 会议纪要清洗与发布（2026-08-26）

- ResearchFoundry `transcripts` 子技能已按用户确认的事件身份运行三次：2026Q1（2026-04-30）、2026Q2（2026-07-14）和 Wells Fargo Conference（2026-06-09）。
- 三次 run 均完成 `plan -> run -> prepare -> publish -> inspect`；artifact 已验证，分别为 44、62、41 个 `T####` 标记，source representation 均为 `raw_transcript`，coverage 标记为 `partial`。
- 原始用户文件未修改；清洗稿保留双语文本、数字、限定条件和 `[indiscernible]/[听不清]` 等不确定内容。Wells Fargo 文档的出席人员、Presentation 和 QA 标题被保留为 metadata，不被误当作发言人。
- 会议纪要证据已登记为 S29-S31，并用于更新主报告的 Utility book-to-bill、765 kV、NSI 协同/去杠杆和数据中心约 10% Electrical 暴露等观点；所有这些均标记为管理层主张或前瞻性信息，不替代 SEC 审计数据。

## 最终 intake / release 前复核（2026-08-26）

- 2026Q2 10-Q 与 8-K Exhibit 99.1 已逐项核对：六个月合并销售 3,228.5、经营利润 612.4；Utility 销售/经营利润 1,974.7/409.0；Electrical 1,253.8/203.4。未经审计且含 NSI 并表影响，另存于 `data/curated/companies/US/HUBB-hubbell/operating_current.csv`。
- 2026-06-30 债务、现金、应收和存货余额已补入报告；NSI 收购现金 3,005.7 与长期债务 4,803.9 已作为中期风险单独披露，不混入 FY2021-FY2025 年度趋势。
- 已尝试第二行情源 Stooq；返回 JavaScript verification page，无可用价格。响应保存并登记为 S28/A13b，Yahoo 仍是唯一可用行情源，估值 gate 保持 `PARTIAL`。
- 修正 `market_snapshot.csv` 与报告中的 EV ex leases：`26,351.851261` 百万美元，公式为 24,524.351261 + 2,325.4 - 497.9。
- strict 财务计算器、CSV/JSON 解析、`git diff --check` 和 full-report strict validator 已在修正前通过；修正后将全部重跑并记录最终结果。
- 章节重写后复跑结果：strict calculator（JSON/Markdown）通过；全部 CSV/JSON 可解析；`git diff --check` 通过；`validate_research_release.py --full-report --strict` 通过（words=11528、H2=11、H3=64、tables=36、source_ids=14）。

## 独立性清理复核（2026-08-26）

- 已从主报告及 Hubbell 研究记录中移除其他公司名称、对标范式和相关方法说明；保留的是 Hubbell 自身的事实、来源、计算、判断和未解决问题。
- 对 Hubbell 报告、原始资料和结构化数据执行不区分大小写的相关公司/证券代码扫描，无匹配。
- 清理后重新运行 `git diff --check` 与完整 `validate_research_release.py --full-report --strict`，结果均通过。

## 会议纪要增补后的报告复核（2026-08-26）

- 主报告已接入 S29-S31 的逐轮证据，更新 Utility book-to-bill/2027 订单可见度、765 kV 商业化、ES 数据中心约 10% 管理层估计、NSI 协同与去杠杆、FY2026 指引和现金回报风险。
- 重新运行完整发布校验：`validate_research_release.py --full-report --strict`，结果 `PASS: no mechanical release findings`；报告指标 words=12773、H2=11、H3=65、tables=37、source_ids=17。
- `meeting_minutes_digest.csv` 共 9 条结构化记录，CSV/JSON 解析、`git diff --check` 和三场 transcript artifact inspect 均通过；发布状态仍为 `PARTIAL`，原因是审计拆分、监管独立证据、租赁/稀释和同业倍数等缺口。
