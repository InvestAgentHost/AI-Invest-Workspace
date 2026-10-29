# PepsiCo（PEP）研究入口

更新日期：2026-10-29。已开展经营历史、三张财务报表、资本回报、薪酬计划与管理团队分析。底稿`Profit Forecast`覆盖2026全年补齐、2027—2031逐年预测与稳定期；`Valuation Model`按用户模板增加悲观、基准、乐观三情景，折现现金分红与退出P/FCF股权价值，并提供手动更新利润路径的步骤。原经营预测仍保留，现对应北美温和修复情景；估值基准采用较慢北美增长。情景与估值输入均为研究建议，完整再投资、融资和现金用途仍待闭环。各专题的覆盖限制以其说明为准，尤其是经营ROIC的历史与最新季度缺口。

## 当前阅读入口

- [图表与专题索引](outputs/README.md)：从这里选择当前采用版，区分历史补充、兼容副本与已停用版本。
- [历史Excel底稿](outputs/company-research-to-excel/PEP_model.xlsx)及[覆盖说明](outputs/company-research-to-excel/README.md)。
- [现金流与股东回报](outputs/cash-flow-20261028/README.md)：含十年累计现金流向、分红、回购及实际缩股；缩股图已补充年化缩股率。
- [利润表与资本回报](outputs/income-returns-20261028/README.md)。
- [管理层、薪酬及治理证据](outputs/management-20261029/README.md)。
- [Ramon Laguarta职业生涯与重要选择](management/ramon-laguarta-career-and-decisions-2026-10-29.md)。
- [官网业务资料](outputs/official-site-snapshot-20261020/business_and_offering_handbook.md)、[重要信息](outputs/official-site-snapshot-20261020/important_information.md)、[战略与进展](outputs/official-site-snapshot-20261020/strategy_and_developments.md)。

个人Word报告由用户维护；本次目录整理未改写Word或Excel内容。图表文件的移动不会改变Word中已嵌入的图片。

## 文件保存与版本规则

- 研究结论、专题说明、目录索引及已有的小型来源定位表保留在Git。现有`PEP_model.xlsx`沿用仓库既有的底稿例外；本次不新增二进制文件入库。
- PNG、SVG和ZIP是可重建的本地交付文件，由本目录的`.gitignore`排除。现有图片退出Git跟踪，当前使用的本地文件继续保留。
- 原始财报、官网资料等外部材料位于`sources/companies/US/PEP-pepsico/`，保持Git忽略。财报阅读层为`sources/companies/US/PEP-pepsico/sec/prepared-v3/`；2026年DEF 14A在`sources/companies/US/PEP-pepsico/sec/DEF-14A/FY2026/`。
- 图表计算、生成程序、检查记录及可重建CSV位于`data/derived/companies/US/PEP-pepsico/`。不要把数据或原件复制进Git以方便找图。
- 用户于2026-10-29明确要求只保留实际有用的文件。已被替代、重复及字体/薪酬计划混用有问题的旧图、旧包和临时预览已永久删除，不再保留图表归档；当前采用版与范围独立的历史补充图继续保留。
- 删除路径、替代文件、原因及SHA-256记录在`data/derived/companies/US/PEP-pepsico/file-cleanup-20261029/deletion-manifest.json`。此前的移动清单只记录整理过程，不表示旧图仍可恢复。
- 跨设备继续采用手工归档转移被忽略的公司材料；仅同步Git不足以带走图表、原件及运行记录。

## 资料与底稿沿革

- 初始资料准备截至2026-10-20：FY2016—FY2025十份10-K、FY2024—FY2026 Q1—Q3九份10-Q及92份官网来源。初始PASS仅指抓取、清洗、编目与校验；不是整份投资研究的最终发布结论。
- 2026-10-21核查经营工作表，补充官方业绩公告、分部重述、Q4数据、适用时间轴与英文空白说明。审计及独立复核位于`research/companies/US/PEP-pepsico/data/company-research-to-excel/`；补充原件位于`sources/companies/US/PEP-pepsico/earnings/`。
- 2026-10-22重整底稿阅读顺序：`Segments`为三张经营表；`Operating Metrics`保存长期与近期季度趋势、历史拆分及关键影响。详细使用说明见底稿目录。
- 初始完成记录：`research/companies/US/PEP-pepsico/data/data-preparation-report-2026-10-20.md`；来源台账：`research/companies/US/PEP-pepsico/data/source-index.md`。
- 资料并非全站、全历史穷举；原有失败台账和未决问题继续保留。
