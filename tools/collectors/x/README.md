# X Collector

通过用户已登录的本机 Chrome/Edge 采集 X 博主的公开帖子、回复、引用、对话上下文和图片附件，并建立本地 SQLite 全文检索。时间线采集后会自动打开详情页，补抓缺失父帖、引用帖和最多 5 层向上回复链。

## 数据边界

- 原始 GraphQL 响应和 DOM 快照：`sources/social/x/<handle>/raw/batches/`
- 规范化帖子、媒体和会话：`sources/social/x/<handle>/normalized/`
- 图片附件：`sources/social/x/<handle>/assets/images/<post_id>/`
- 增量状态：`sources/social/x/<handle>/state/`
- SQLite/FTS 索引：`knowledge/databases/x.sqlite`

采集器不接收或保存账号密码，不复制 Cookie、token、storage state 或浏览器 profile。用户必须在独立浏览器窗口中手动登录 X。

## 安装

```powershell
python -m pip install -r tools/collectors/x/requirements.txt
Copy-Item tools/collectors/x/config.example.json tools/collectors/x/config.json
```

`config.json` 是本地配置，已被 `.gitignore` 排除。示例 profile 已指向 `ShanghaoJin`。

## 启动授权浏览器

```powershell
powershell -ExecutionPolicy Bypass -File tools/collectors/x/start_debug_browser.ps1
```

在新窗口中手动登录 X。该脚本使用 `%TEMP%\x-research-browser` 作为隔离的本地浏览器 profile，不会将认证信息写入 workspace。

检查连接：

```powershell
python tools/collectors/x/main.py doctor
```

## 采集和检索

首次历史回填：

```powershell
python tools/collectors/x/main.py collect --route both --max-scrolls 200
```

`collect` 默认在采集后补抓缺失上下文，再自动运行规范化、图片下载和索引。其他命令：

```powershell
python tools/collectors/x/main.py normalize
python tools/collectors/x/main.py index
python tools/collectors/x/main.py search --query "AI 芯片" --top-k 20
python tools/collectors/x/main.py search --query "库存周期" --type reply --start 2023-01-01
```

搜索结果以博主帖子为命中主体，并随帖子返回：

- 原帖 ID、URL、发布时间和来源路径
- 父帖、引用帖和转发对象（补抓成功或已归档时）
- 按原帖顺序排列的图片附件、本地路径和下载状态

## 完整性限制

浏览器时间线不保证提供全部历史帖子。每个不可变批次的 `manifest.json` 会记录实际观察到的时间范围、帖子 ID、上下文补抓结果、停止原因和错误。`doctor` 汇总当前覆盖范围及直接父帖/引用帖恢复率。遇到登录验证、异常活动提示或限流时，采集器停止，不自动规避。

上下文补抓默认最多打开 100 个详情页并向上追溯 5 层。可使用 `--max-context-pages` 调低页面上限，或使用 `--no-hydrate-context` 临时关闭。

详细设计和后续阶段见 `PLAN.md`。
