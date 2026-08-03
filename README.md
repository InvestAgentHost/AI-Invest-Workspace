# AI Investment Research Workspace

这是 AI 投研主工作区，也是 Obsidian Vault 的子目录。

## 只有两条核心规则

1. `research/` 保存分析过程和研究结论，进入 Git。
2. `sources/` 保存所有外部原始资料，整体不进入 Git，换设备时直接压缩传输。

其他目录：`tools/` 和 `.github/skills/` 保存工具；`data/curated/` 保存小型分析数据；`knowledge/`、`.local/` 和 `data/derived/` 都可重建。

公司资料统一放在 `sources/companies/<market>/<ticker>-<slug>/`，其中 `<market>` 指实际研究或交易的股票市场，例如天岳先进使用 `CN`，诺基亚 ADR 使用 `US`。包括上传资料、财报、研报、官网快照和 Gangtise。X、Substack、SEC 等跨公司来源按平台放在 `sources/` 下。

所有由工具生成的路径都使用 Workspace 相对路径，或在单个来源包内部使用相对该来源根目录的短路径。原始资料内部自带的绝对路径不改写，因为它们属于原件内容。

详细规则见 [架构](docs/architecture.md)、[资料工作流](docs/company-materials.md)、[数据路径](docs/data-paths.md) 和 [跨平台设置](docs/cross-platform-setup.md)。
