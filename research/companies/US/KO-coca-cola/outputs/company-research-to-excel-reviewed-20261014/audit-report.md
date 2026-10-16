# KO Excel 底稿修订与数据复核

复核日期：2026-10-14。覆盖 FY2016–FY2025，以及 3Q2024、1Q/2Q/3Q2025、1Q/2Q2026；最新已覆盖报表期间为 2026-07-03。本次复核既有期间，未扩展到后续披露。

## 交付与原文件

- 最终底稿：[KO_model_formatted.xlsx](KO_model_formatted.xlsx)。新增 `Audit 2026-10-14` sheet，逐项记录来源、单元格、原值、修订值与原因。
- 原底稿历史路径（该 Excel 已移至系统废纸篓）：`research/companies/US/KO-coca-cola/outputs/company-research-to-excel-20261013/KO_model.xlsx`。
- 当前仅保留 `KO_model_formatted.xlsx`，已完成数据修复和全工作簿格式优化。原始版及三个中间副本已移至系统废纸篓；下文校验记录中的旧文件名和校验和属于当时的修复版本。
- 原文件 SHA-256：`103d385ad9385d1ff25c8050235a1a44c9c1351fe6681f2e43c26ba740c7c151`。最终文件 SHA-256：`a4d839c7c15dc63af40f7f25cc5ddd3a1ebad17139bceb52c2eb1e88250e5914`。

## 已修复的问题

以下属于来源事实与机械提取问题，不涉及预测或投资判断。

1. **浓缩液销量增长整段缺失**：2020 年以后，提取器把浓缩液值放在第三个字段，组装器却读取第二个字段。已恢复 FY2020–FY2025。Worldwide 依次为 **−7%、+9%、+5%、+2%、+1%、+1%**。来源：`sources/companies/US/KO-coca-cola/artifacts/ten_k/KO-coca-cola/FY2020/psp_b79ab798eb324e1d912ca3860d0fc698/raw/source.html` 至 `sources/companies/US/KO-coca-cola/artifacts/ten_k/KO-coca-cola/FY2025/psp_49eb40deba72424d91379bb74482f553/raw/source.html` 的 MD&A Beverage Volume 表。
2. **脚注当作数值或列错位**：原始 HTML 中的上标在 Markdown 里被转成普通数字。已用 HTML 单元格、期间和行名读取数据，去除上标及抬高位置的脚注。例：Asia Pacific 单位箱增速 FY2018 **10% → 4%**、FY2019 **10% → 5%**；Latin America FY2017 **−3% → −2%**、FY2019 **0% → +1%**；Latin America 浓缩液增速 FY2018 **−2% → +1%**。来源：`sources/companies/US/KO-coca-cola/artifacts/ten_k/KO-coca-cola/FY2019/psp_405c783f553d43c9b2011bba81319d93/raw/source.html` 与其中的比较期间。
3. **Bottling Investments 浓缩液销量不适用**：原文明确披露 `N/A`。已清除年度误读值和六个季度栏里脚注造成的连续 **5%**，统一显示 `N/A`。来源：各 10-K/10-Q 的同一销量表；公司这一分部指标不能当作已披露的浓缩液增长率。
4. **缺少分部行**：补齐 Asia Pacific 浓缩液增长；在经营指标表末尾补齐 Global Ventures 浓缩液增长，避免移动原有公式引用。恢复有来源的 FY2016 分部销量数据。Global Ventures FY2018 是 FY2019 年报所展示的比较口径；保留并注明其收购业务／Costa 口径差异。
5. **收入驱动因素表错误**：FY2019 Bottling Investments 收购／剥离影响 **10% → 5%**；补齐 FY2019 Asia Pacific **3%**、Bottling Investments **10%** 的收入总影响。来源：`sources/companies/US/KO-coca-cola/artifacts/ten_k/KO-coca-cola/FY2019/psp_405c783f553d43c9b2011bba81319d93/raw/source.html` 的 net operating revenue factors 表。
6. **来源明确为零的单元格留空**：三张财务报表及待售资产／负债附注中，原文印刷破折号所表示的零已补齐。未把未披露或不适用项目改为零。
7. **附注对比表不完整**：原“公允价值与账面价值对比”只有公允价值。保留原值，补充七家权益法投资对象的账面价值、差额与总计，差额采用公式。FY2025 合计公允价值 **34,286**、账面价值 **13,999**、差额 **20,287**，单位为百万美元。来源：`sources/companies/US/KO-coca-cola/artifacts/ten_k/KO-coca-cola/FY2025/psp_49eb40deba72424d91379bb74482f553/raw/source.html` Note 6，Fair Value / Carrying Value / Difference 原表。
8. **说明过期／格式不一致**：更新 Cover/Sources 中“未建经营指标与附注表”和“衍生指标仅有年度”等过期描述；Global Ventures 季度销量改为百分比显示；补充季度净债务／EBITDA 分母口径说明。

## 全工作簿检查结果

对原有十个 sheet 全部检查：七个 sheet 的输入与来源比较；Derived Metrics 独立重算；Cover/Sources 核对期间、范围、来源路径、比较口径和目录。

| Sheet | 来源单元格检查 | 修订／补充单元格 |
| --- | ---: | ---: |
| Income Statement | 326 | 3 |
| Balance Sheet | 546 | 2 |
| Cash Flow | 534 | 14 |
| Operating Metrics | 833 | 81 |
| Note Schedules | 330 | 31 |
| Segments | 918 | 0 |
| Geography | 78 | 0 |

- **3,565** 个不同来源单元格核对，未匹配项目 **0**；检查数包含少量已用公式链接的已披露输入。
- **131** 个单元格修订或补齐，涵盖原错误、空缺、已披露零值以及新增附注数据；这个数不等于 131 个错误。
- 原有数值公式 **1,780** 个，全部保留。新增附注桥接与勾稽公式 **11** 个；最终 **1,791** 个全部独立求值，无错误、无超容差的勾稽差异、无公式链接与原文数值不一致。
- Excel 原生 `calculate full rebuild` 重算的 **1,791** 个结果与独立求值全部一致，无 Excel 错误单元格。最终版只进一步调整显示与导航，保留这些已核实的数值公式缓存。
- Income Statement、Balance Sheet、Cash Flow、Segments、Geography 中的**既有非零披露金额没有发现错误**。附注既有非零金额也与原表一致；问题在零值和对比列缺漏。

## 保留的口径差异与空白

- 单位箱绝对量为按十亿箱四舍五入的披露值，其计算同比与公司直接披露的可比增长率是两种指标；不能要求两行相等。本次均保留原口径。
- IS 季度栏为单季；BS 为期末；CF 为年初至今累计。没有把累计现金流与单季收入混算，现有年度现金流比率覆盖不随意延展。
- 季度净债务／EBITDA 的 EBITDA 为单季，未年化；其数值不能直接与年度分母的倍数比较。已在对应行注明。
- 分部三套历史口径分别保留；Global Ventures 重分部前后未跨口径拼接。
- 未单独披露或原范围未覆盖的项目继续留空；`N/A` 表示公司明确认定不适用。4Q 和未建的非 GAAP 桥仍不补造。

## 复核证据与后续维护

详细逐格来源和数值：`data/derived/companies/US/KO-coca-cola/workbook-audit-20261014/source-cell-audit.json`。独立公式结果：`data/derived/companies/US/KO-coca-cola/workbook-audit-20261014/formula-audit-final.json`。文件及原生重算核对：`data/derived/companies/US/KO-coca-cola/workbook-audit-20261014/final-verification.json`。

已修正原 `_extract_operating.py` 的销量 HTML 解析与字段排列，以及 `_ops_sheets.py` 的 N/A、FY2016 覆盖和零值过滤。完整复核工具为 `tools/research/audit_ko_workbook.py`，公式验证工具为 `tools/research/workbook_formula_audit.py`，均使用 Workspace `.venv`。

现有工作簿有后续补充的季度数据，旧 `model.json` 未完整包含它们；因此本次在工作簿副本上实施经来源核对的范围修订，不从旧模型重建。`data/derived/companies/US/KO-coca-cola/workbook-audit-20261014/model_verified.json` 仅是输入更新快照，不能视为完整工作簿重建入口。原始 SEC HTML 与 prepared Markdown 没有改动。
