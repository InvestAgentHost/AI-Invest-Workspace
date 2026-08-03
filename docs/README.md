# Workspace 文档中心

本目录保存整个 AI 投研 workspace 的架构、工作流、工具使用和维护文档。根目录 `README.md` 是快速入口；需要理解设计边界或执行具体操作时，从这里继续阅读。

## 文档导航

- [Workspace 架构](architecture.md)：目录职责、数据生命周期和开发边界。
- [公司资料工作流](company-materials.md)：公司 `_inbox`、自动归档、Git 边界和手动压缩同步。
- [Obsidian Vault 管理](obsidian-vault.md)：Vault 根、索引排除和 Obsidian Sync 边界。
- [Workspace 数据路径](data-paths.md)：相对路径、默认本地数据根和旧目录迁移原则。
- [跨平台初始化](cross-platform-setup.md)：macOS/Windows 目录、Python、Git 和手动资料同步。
- [Gangtise Skills 更新流程](gangtise-skill-update.md)：官方包下载、校验、完整覆盖、恢复与 Workspace 回归测试。
- [SEC 8-K 并购重组每日 Agent 工作流](sec-8k-mna-daily-agent-workflow.md)：SEC 8-K 采集、LLM 事件识别、日报和定时执行方案。
- [X Collector 指南](x-collector.md)：安装、首次使用、历史回填、增量更新、检索和故障检查。

## 文档归属规则

- Workspace 级架构、跨目录流程和工具使用指南放在 `docs/`。
- 研究结论和研究过程放在 `research/`，不放在 `docs/`。
- 外部来源说明及来源身份放在对应的 `sources/` 目录。
- 单个代码模块的简短开发说明可以保留在模块自己的 `README.md`。
- `docs/` 中的工具指南应链接到代码和数据位置，不直接承载业务数据或生成结果。

## 推荐阅读顺序

首次进入 workspace：

```text
根 README
  -> docs/architecture.md
  -> 相关工具指南
  -> 对应模块 README 或 PLAN
```
