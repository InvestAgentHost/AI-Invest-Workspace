# Graco 深度研究归档

归档日为 2026-11-17，时区 Asia/Hong_Kong。财务实际覆盖至 2026-09-25，订单积压观测至 2026-10-16，估值日为 2026-11-12，模型参考 2026-11-11 纽约收盘。报告保存日期与各项数据截止时间分别记录。

## 研究与证据

| 资料 | 归档入口与核对 |
|---|---|
| 深度报告 | [GGG.docx](outputs/reports/20261113/GGG.docx)。本次上传件、此处现有版本与已保存的报告样本字节一致，沿用现有归档。内容含公司结论、商业模式、竞争、分部经营与订单、基本面、管理层和估值截图。Word 包内最后修改时间为 2026-11-13 10:50（香港时间）。 |
| 盈利预测与估值 | [2026-11-12 工作簿](outputs/valuation-2026-11-12/GGG-盈利预测与估值-2026-11-12.xlsx)。报告估值截图和现存工作簿一致。工作簿位于 Git 历史提交 `108babba4dcd12022066fdfd95f5a2769d6b1c12` 的同一路径，已核对文件指纹。 |
| 财务原件 | [2025 10-K](../../../../sources/companies/US/GGG-graco/sec-2026-11-06/10-K-2025-12-26.html)、[2026Q3 10-Q](../../../../sources/companies/US/GGG-graco/sec-2026-11-06/10-Q-2026-09-25.html)及[历史 SEC 文件索引](../../../../sources/companies/US/GGG-graco/sec-2026-11-06/manifest.json)。 |
| 投资者材料 | [2026Q3 业绩会材料](https://investors.graco.com/static-files/b72c4a70-1b74-4c27-898d-504792c36e3a#page=10)、[Valco 交割](https://investors.graco.com/news-releases/news-release-details/graco-inc-closes-acquisition-valco-melton/)、[ABB 授权](https://investors.graco.com/news-releases/news-release-details/graco-announces-technology-partnership-abb-bring-high-torque-etm)、[加速回购 8-K](https://www.sec.gov/Archives/edgar/data/42888/000119312526455736/d125383d8k.htm)。本轮按原文点查上述事件和关键口径。 |
| 治理、订单与图表 | [2026 DEF 14A](../../../../sources/companies/US/GGG-graco/sec-governance-2026-11-12/d93954ddef14a.htm)、[订单连续披露数据](../../../../data/derived/companies/US/GGG-graco/orders-2026-11-12/orders.json)、[图表目录](outputs/figures/)。旧的 [数据及来源记录](data/)按各自研究时点阅读。 |

## 版本与复核

| 文件 | 字节数 | SHA-256 |
|---|---:|---|
| 归档 Word | 9,229,293 | `a012f03d9103575f05483b3d48c94af0e774a5a5d211eacd6fbc99983d4e89c7` |
| 估值 Excel | 70,496 | `5d0d0a910dc731e3e010dfc6b74681b0957e57a321b3972ca2169694ff2707a6` |

两份文件通过包完整性检查。读取了 Word 正文和末节估值图，并从实际存档 Excel 读取关键公式、输入和结果，独立复算基准买入价、退出价和参考价 XIRR。归档保留 Word 和 Excel 原文件。旧聊天及较早生成版本的 12% 回报、21 倍基准倍数与此版不同，比较时按文件指纹和输入区识别版本。此版矩阵网格未包含 26 倍，表内 `Valuation Model!D81` 提示「参数不在矩阵」。核心原公式及数据在[保留基线](tracking/baselines/2026-11-17.md)。

## 后续使用

从[跟踪规则](tracking/rules.md)进入。首次运行重点核对后续披露及未决事项。原始证据位于 `sources/companies/US/GGG-graco/`。跨设备续接时，手工携带仍未纳入 Git 的原始资料和必要图表或重建数据。
