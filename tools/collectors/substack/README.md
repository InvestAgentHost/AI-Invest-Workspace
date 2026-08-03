# Substack Collector

抓取用户有权限访问的 Substack 文章，并将完整内容归档到 `sources/publishers/substack/<profile>`。

## 数据边界

- `raw/html/`：原始 HTML
- `normalized/markdown/`：清洗后的 Markdown
- `assets/images/`：文章图片
- `state/`：增量 manifest 和帖子元数据，本地运行状态，不入 Git

工具目录只保存代码和配置，内容数据不写入 `tools/`。

## 配置

本地配置为 `tools/collectors/substack/config.json`，不入 Git。首次运行会从 `config.example.json` 创建配置副本。

```powershell
python tools/collectors/substack/main.py archive
```

`archive` 是常规增量同步入口：它扫描整个归档列表，逐个按 slug 检查本地 Markdown，
因此一次可以抓取多篇新增文章。`latest` 只检查第一篇，不适合日常增量同步。

每个 profile 包含：

- `base_url`：博主主页
- `archive_url`：归档页
- `output_dir`：来源归档根目录
- `cdp_url`：浏览器调试端口
- `max_scrolls`：最大滚动次数
- `min_delay` / `max_delay`：请求间隔

## 安装与运行

```powershell
python -m pip install -r tools/collectors/substack/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
powershell -ExecutionPolicy Bypass -File tools/collectors/substack/start_debug_browser.ps1
python tools/collectors/substack/main.py archive
```

其他命令：

```powershell
python tools/collectors/substack/main.py latest
python tools/collectors/substack/main.py single "https://example.substack.com/p/example"
python tools/collectors/substack/main.py clean-local
```

`archive` 和 `latest` 使用 `state/manifest.json` 与本地 Markdown 共同判断是否跳过；
使用 `--overwrite` 可强制重新抓取。抓取结果属于原始资料，全部留在 `sources/`，不再复制到 Git 阅读层。需要形成可同步的研究结论时，在 `research/` 中新建分析笔记并引用原始 URL 或 Workspace 相对路径。
