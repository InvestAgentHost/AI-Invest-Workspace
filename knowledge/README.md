# Knowledge

默认根路径是 Workspace 的 `knowledge/`。`config.yaml` 只用于特殊本机覆盖。

保存面向机器检索的目录、索引和数据库。

- `catalogs/`：文档、实体和来源目录
- `indexes/`：全文与向量索引
- `databases/`：SQLite、DuckDB 等本地数据库
- `profiles/`：博主或知识源配置

索引与数据库原则上必须能从 `sources/`、`data/` 和 `research/` 重建。

`knowledge/` 不通过 Git、微信压缩包或 Obsidian Sync 在设备间同步；每台机器从来源和研究资产重建。
