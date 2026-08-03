# AI 云盘 API（Open API · drive）

## 简介

脚本 **`scripts/private_cloud.py`** 对接 Gangtise 终端 **AI 云盘**（**不消耗积分**）。列表结果**不包含**对话、AI 速记、AI 翻译文件夹中的文件。

- **getList**：分页检索云盘文件，返回 `fileId` 及元信息。
- **download/file**：按 `fileId` 下载文件内容。

## 模式（`-m` / `--mode`）

| 模式 | 说明 |
|------|------|
| `search` | 列文件 → `private_cloud_list_*.csv`（默认）。 |
| `get` | 按 `--files` 下载。 |

**自动路由**：提供 `--files` 或 `--files-file` 时自动进入 `get`。参数仅含字母数字与逗号时视为 ID；含中文等则 search，**唯一完全匹配**时自动 get。

筛选参数均可选。

## 参数

| 参数 | 说明 |
|------|------|
| `-m` / `--mode` | `search` \| `get`（默认 `search`）。 |
| `-k` / `--keyword` | 文件标题关键词（`search`）。 |
| `-st` / `-et` | 文件**创建时间**（`yyyy-MM-dd` 可自动补全）。 |
| `--file-type-list` | `document` `image` `media` `article` `other`，或中文（文档、图片、音视频等）。 |
| `--space-type-list` | `1` 我的云盘、`2` 租户云盘（可传中文）。 |
| `--files` | 文件 ID 或标题，逗号分隔（提供后自动 `get`）。 |
| `--files-file` | CSV 含 `file_id` 列（提供后自动 `get`）。 |
| `-l` / `--limit` | `search` 列表条数上限（默认 100）。 |

## 调用示例

```bash
python3 scripts/private_cloud.py -m search -k "部门文档" --file-type-list document -l 30
```

```bash
python3 scripts/private_cloud.py --files 49412
```

```bash
python3 scripts/private_cloud.py -m search -k "研报" --space-type-list 2 -l 10
```

## 返回说明

- **列表 CSV**：`file_id`, `title`, `create_time`, `space_type`, `file_size`, `url`, `uploader`
- **下载**：`private_cloud_content_*.md`（`GTS_SAVE_FILE=True` 时落盘；文本类展示正文，二进制显示大小提示）
- **search 成功**：消息末尾提示可通过 `--files-file` 读取 CSV 再下载
- 路径：`workspace/gangtise/private_cloud/`
