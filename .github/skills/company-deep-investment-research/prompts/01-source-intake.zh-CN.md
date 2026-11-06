使用 `$company-deep-investment-research` 为【公司名 / ticker / 市场】执行阶段 1 资料获取与预处理。

财报采集必须直接基于 SEC EDGAR 正式公开披露：从 SEC 官方端点核实身份和披露目录，获取完整 10-K/10-Q/8-K、修订文件、相关招股书及附件。不得调用 FocusAlpha 或其他第三方服务查询身份、目录、财务数据或加工文本，不得引入第三方缓存、镜像或会议纪要。SEC 获取失败时记录缺口，不切换第三方补数。旧文件只有能证明是 SEC 直接下载的原件时才可复用。详细边界遵守 `references/source-acquisition.md`。

如范围包含官网任务，另行从已核实的公司及品牌官方域名获取页面、IR 资料和公司自发电话会文字稿，标为公司披露，不替代 SEC 财报。使用 bundled ResearchFoundry bridge 处理 SEC HTML 和官网；不要求我手动执行内部命令。若本轮仅获取资料，完成原文、检索文本、来源台账和覆盖检查后停止，不自动进入 Excel、财务重构或研究写作。

保留原始资料，生成来源索引、SHA-256、访问/内容日期、页码或 T#### 定位、采集尝试记录和覆盖矩阵。不得推断会议日期，不得伪造 speaker，不得把 provider-prepared minutes 当作原始 transcript。先展示计划，遇到歧义或权限问题暂停确认。
