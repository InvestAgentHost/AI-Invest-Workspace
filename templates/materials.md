---
type: company-material-root
company_id: <market>-<ticker>-<slug>
company: <公司名称>
as_of: YYYY-MM-DD
---

# <公司名称>原始资料

## 本地资料根目录

以下路径中的原始内容不进入 Git，需要换设备时从 Workspace 根目录手动压缩：

- `sources/companies/<market>/<ticker>-<slug>/`

该目录整体不进入 Git。财报、研报、官网快照、平台下载和用户上传资料均在其中按子目录隔离；归档工具通过哈希和来源索引确认文件身份。

研究期间的上传入口是 `research/companies/<market>/<ticker>-<slug>/data/`。交付审核时生成归档计划，用户确认后才复制或移动到 `sources/`。

## 待处理

- 需要研究时直接检查本机资料目录。
