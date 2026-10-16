# KO Excel 格式审查

日期：2026-10-14。

最终阅读版：[KO_model_formatted.xlsx](KO_model_formatted.xlsx)。以已核实的 `KO_model_fixed.xlsx` 为数据基础，本目录仅保留格式完成版；其余四份原始／中间 Excel 已移至系统废纸篓。

- 全部 11 个 sheet 的有效内容统一为 Arial，正文／数字 10.5 pt；标题 16 pt、章节 11 pt、来源与日期 8.5–9.5 pt。衍生指标数字取消浅灰斜体，增强对比度。
- 深蓝章节、青绿季度表头、浅底汇总与校验行；蓝色披露输入、深色公式、绿色跨表引用。加粗集中在标题与关键汇总，N/A 单独辨识。
- 正文约 21 pt 行高；长项目与说明按内容增高。封面、来源和审计概要重新调整列宽、换行与留白；审计详细来源列可用列分组展开查看。
- 经营指标、报表和附注统一数字格式、年度／季度列宽，缩小三列空白间隔；冻结表头与项目列，合并空白标题区域，保留原有导航和所有原有单元格内容。
- 配置表头重复打印与横向页面；经营指标和附注新增区域完整纳入打印范围。默认仅选中 Operating Metrics，避免工作表被同时分组选中。

已在 Excel 中预览经营指标与衍生指标页。最终版与数据修复版的全部单元格值、公式、数值缓存、批注、超链接完全一致；原有条件格式保留。1,791 个数值公式独立校验通过，无错误、勾稽差异或来源公式不一致。

格式审查记录：`data/derived/companies/US/KO-coca-cola/workbook-audit-20261014/format-audit-final.json`。公式复核记录：`data/derived/companies/US/KO-coca-cola/workbook-audit-20261014/formula-audit-formatted.json`。可复用格式工具：`tools/research/style_research_workbook.py`。
