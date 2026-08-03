# Workspace 架构

截至：2026-08-03

## 目录职责

```text
Workspace/
├── research/       分析过程、公司研究、行业研究和投资结论，Git
├── sources/        所有外部原始资料，整体 ignored，手动压缩
│   ├── companies/  公司资料和该公司的 Gangtise
│   ├── social/     X 等社交来源
│   ├── publishers/ Substack、微信等出版来源
│   └── providers/  SEC 等跨公司的供应商资料
├── data/curated/   小型、稳定、用于分析的数据，Git
├── data/derived/   可重建数据，ignored
├── knowledge/      数据库和索引，ignored
├── tools/          工具代码，Git
└── .local/         浏览器、日志、缓存和状态，ignored
```

## 同步方式

- GitHub：`research/`、工具、skills、模板和小型精选数据。
- 手动压缩：整个 `sources/` 或其中一个公司/平台目录。
- Obsidian：只索引 Git 层，不索引 `sources/`、`knowledge/` 和 `.local/`。
- 每台机器重建：`.venv/`、`.local/`、`knowledge/` 和 `data/derived/`。

不维护逐文件索引、哈希清单或 library/catalog 副本。原始文件的可用性以本机目录是否存在为准。

公司研究、公司原始资料和公司精选数据共用 `<market>/<ticker>-<slug>` 标识。`<market>` 指实际投资或交易市场，而不是公司注册地，例如 Nokia ADR 使用 `US/NOK-nokia`。

## 路径规则

工具生成的本地路径、配置示例、研究引用使用相对 Workspace 根的 POSIX 路径，例如 `sources/companies/CN/688234-sicc/`。本机 `config.yaml`、`.env` 和运行日志可以包含绝对路径，但它们不进入 Git。

第三方原始文件中的绝对路径、网页正文、PDF 文本和用户提供文档不做内容改写，以保持来源原貌。
