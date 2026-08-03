# Obsidian Vault 管理

Vault 根目录是 Workspace 的父目录：

```text
AI Invest/
├── .obsidian/
└── Workspace/
```

GitHub 管理 Workspace 的 tracked 文件；Obsidian Sync 只管理 `.obsidian/`。建议在 Obsidian Sync 中排除整个 `Workspace/`，避免 GitHub 与 Obsidian Sync 同时修改同一批 Markdown。

在 Obsidian 的排除文件设置中加入：

```text
^Workspace/\.git/
^Workspace/\.venv/
^Workspace/sources/
^Workspace/\.local/
^Workspace/knowledge/
^Workspace/data/derived/
^Workspace/outputs/
^Workspace/inbox/
```

这些是 Vault 相对路径，不包含 macOS 或 Windows 的本机绝对路径。工作区正式命名为 `Workspace` 后只保留这一组；不要长期保留 `Workspace-next` 的过渡规则。

建议只索引 `research/`、`docs/`、`templates/` 和 `data/curated/`。原始资料需要查阅时，从 `sources/` 直接打开，不把它当作知识库正文。
