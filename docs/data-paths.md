# Workspace 数据路径

## 标准路径

```text
sources/companies/CN/688234-sicc/
sources/companies/CN/688630-xinqiweizhuang/
sources/companies/US/NOK-nokia/
sources/social/x/ShanghaoJin/
sources/publishers/substack/damnnang/
sources/providers/sec/
knowledge/databases/x.sqlite
```

公司原始资料和 Gangtise 数据放在同一个公司目录，因此换设备时通常只压缩一个目录：

```text
sources/companies/CN/688234-sicc/
```

## 相对路径规则

tracked 文档中只允许出现 Workspace 相对路径，例如：

```text
sources/companies/CN/688234-sicc/filings/2026-03-28/report.PDF
```

禁止写入 `/Users/...`、`C:\Users\...`、`G:\...` 或其他机器专属路径。工具内部可将相对路径解析为绝对路径，但不得把解析结果写回 tracked 文件。

`sources/` 内部的 manifest 可以使用相对该来源根目录的短路径，例如 X 归档中的 `assets/images/<post-id>/image.jpg`。这同样是可移植的相对路径；不要为了统一外观把它扩展为本机绝对路径。

原始资料内容本身不做清洗。若 PDF、网页快照或供应商 JSON 内部包含绝对路径，将其视为原始内容，不修改。
