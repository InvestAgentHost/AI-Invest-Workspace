使用 `$company-deep-investment-research` 对【公司名 / ticker】执行独立 release review。

检查来源 ID、URL/本地路径、页码/T#### 定位、事实与判断分层、覆盖矩阵、三表勾稽、CSV/JSON 解析、strict 财务计算、Markdown 表格和代码围栏、git diff --check、完整报告校验，以及参考公司名称/代码/事实泄漏。

逐项记录 A1-E2 和 R1-R3，通过、失败、缺口、修复和最终 PASS/PARTIAL/BLOCKED。不要为了机械通过删除未解决问题或放松证据边界。

同时扫描 `research/companies/<market>/<company-id>/data/` 中新增的上传资料，生成只读归档计划，列出建议目标目录、哈希和已知引用。将归档计划交给用户确认；未确认前不移动或删除文件。
