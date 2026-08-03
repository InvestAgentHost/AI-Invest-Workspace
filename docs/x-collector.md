# X Collector 使用与维护指南

X Collector 通过用户已登录的本机 Chrome 或 Edge，采集 X 博主的公开帖子、回复、引用、转发、对话上下文和图片附件，并建立可增量更新、可追溯、可检索的本地知识库。

当前首个 profile 是 `ShanghaoJin`。采集器不使用付费 X API，也不接收或保存账号密码。

## 首次使用：按顺序执行

下面命令从 Workspace 根目录运行。先激活本机 `.venv`，然后使用 `python`。

### 第一步：安装依赖

只需要在首次使用或依赖更新后执行：

```powershell
python -m pip install -r tools/collectors/x/requirements.txt
```

本机已经创建了 `tools/collectors/x/config.json`，默认采集 `ShanghaoJin`，首次使用不需要修改配置。

### 第二步：启动专用浏览器

```powershell
powershell -ExecutionPolicy Bypass -File tools/collectors/x/start_debug_browser.ps1
```

这会打开一个独立的 Chrome 或 Edge 窗口。接下来：

1. 在这个新窗口中手动登录 X。
2. 打开 `https://x.com/ShanghaoJin/with_replies`。
3. 确认页面能看到金老师的帖子和回复。
4. 保持这个浏览器窗口打开。

不要在配置文件或命令行中填写 X 账号、密码、Cookie 或 token。

### 第三步：检查连接和登录状态

```powershell
python tools/collectors/x/main.py doctor
```

输出中至少应看到：

```text
"ok": true
"x_session_present": true
```

它们位于 `cdp` 字段内，分别表示调试浏览器可以连接、浏览器中存在 X 登录会话。

如果 `ok` 是 `false`，说明专用浏览器没有启动或 9222 端口不可连接。如果 `x_session_present` 是 `false`，请回到专用浏览器重新登录 X，再运行一次 `doctor`。

如果启动脚本仍无法自动找到浏览器，可以显式指定可执行文件：

```powershell
powershell -ExecutionPolicy Bypass -File tools/collectors/x/start_debug_browser.ps1 `
  -BrowserPath "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
```

### 第四步：先试抓 10 轮

不要第一次就直接抓取几百轮。先运行：

```powershell
python tools/collectors/x/main.py collect --route both --max-scrolls 10
```

`--route both` 表示同时检查博主帖子主页和回复页面。一次 `collect` 会自动完成：

```text
采集原始数据
  -> 打开详情页补抓缺失上文和引用帖
  -> 规范化帖子和关系
  -> 下载图片
  -> 重建 SQLite 检索索引
```

命令结束后会输出本批次观察到的帖子数、GraphQL 响应数、DOM 快照数、上下文详情页数、补全关系数、停止原因、规范化帖子数和图片数。

### 第五步：检查试抓结果

先查看数据覆盖状态：

```powershell
python tools/collectors/x/main.py doctor
```

再做一次检索：

```powershell
python tools/collectors/x/main.py search --query "芯片" --top-k 5
```

第一次应人工抽查至少几条结果：

- 正文是否完整。
- 作者是否是 `ShanghaoJin`。
- 发布时间和原帖 URL 是否正确。
- 回复是否带有父帖 ID 或父帖上下文。
- 引用帖关系是否正确。
- 含图片的帖子是否返回 `media` 和本地图片路径。

试抓正确后，再进行历史回填。

## 历史数据回填

历史回填是从最新帖子不断向更早帖子滚动。先运行：

```powershell
python tools/collectors/x/main.py collect --route both --max-scrolls 200
```

完成后检查：

```powershell
python tools/collectors/x/main.py doctor
```

重点关注：

```text
target_posts
earliest_post_at
latest_post_at
```

每次采集都会从时间线顶部开始。因此，如果 200 轮仍未到达足够早的日期，下一次应增加滚动上限：

```powershell
python tools/collectors/x/main.py collect --route both --max-scrolls 400
python tools/collectors/x/main.py collect --route both --max-scrolls 800
```

反复使用相同的 `--max-scrolls 200` 通常只会重新覆盖相同时间范围，不会自动从上次停止的位置继续向前。原始批次会分别保存，但规范化文件和数据库会按帖子 ID 合并，不会产生重复帖子。

X 浏览器时间线不保证返回账号的严格完整历史。若继续增加滚动上限也无法取得更早帖子，只能把 `earliest_post_at` 记录为“当前浏览器路线可获得的最早边界”，不能宣称已获得全部历史帖子。

## 日常增量更新

历史回填完成后，日常更新只需要抓取时间线顶部的新帖子，不需要再次滚动几百轮。

### 每次更新的操作

如果专用浏览器尚未打开，先启动：

```powershell
powershell -ExecutionPolicy Bypass -File tools/collectors/x/start_debug_browser.ps1
```

确认 X 仍处于登录状态，然后检查：

```powershell
python tools/collectors/x/main.py doctor
```

执行浅层增量采集：

```powershell
python tools/collectors/x/main.py collect --route both --max-scrolls 20
```

通常可以按更新频率调整：

- 每天运行：`--max-scrolls 10`
- 每周运行：`--max-scrolls 20`
- 间隔较久或发帖很多：`--max-scrolls 30` 至 `50`

增量采集仍会保存新的原始批次，但规范化和索引阶段会：

- 按帖子 ID 合并已有帖子。
- 加入新帖子、回复和引用内容。
- 保留已下载成功的图片，不重复下载同一帖子附件。
- 自动重建 SQLite 检索索引。

更新后可以直接检索：

```powershell
python tools/collectors/x/main.py search --query "库存周期" --type reply
python tools/collectors/x/main.py search --query "估值" --start 2025-01-01
```

建议每次增量更新后查看一次 `doctor`，确认 `latest_post_at` 已前进、媒体没有大量失败，并检查本批次是否因登录、验证或限流提前停止。

`doctor.context` 会同时报告直接父帖和引用帖的恢复率。若 `direct_parents_missing` 或 `quoted_posts_missing` 持续增加，应先处理上下文缺失，再进行研究检索。

## 最常用命令速查

```powershell
# 启动浏览器，随后在浏览器中手动登录 X
powershell -ExecutionPolicy Bypass -File tools/collectors/x/start_debug_browser.ps1

# 检查浏览器、登录、数据覆盖和索引
python tools/collectors/x/main.py doctor

# 首次小规模试抓
python tools/collectors/x/main.py collect --route both --max-scrolls 10

# 历史回填
python tools/collectors/x/main.py collect --route both --max-scrolls 200

# 日常增量更新
python tools/collectors/x/main.py collect --route both --max-scrolls 20

# 检索
python tools/collectors/x/main.py search --query "芯片" --top-k 20
```

以下章节解释工具原理、代码结构和高级命令。只想完成首次采集或日常更新时，按照上面的步骤操作即可。

## 1. 工作流程

```text
已登录浏览器
  -> GraphQL 响应 + DOM 快照
  -> 不可变原始批次
  -> 规范化帖子、媒体和会话
  -> SQLite + 全文索引
  -> 带原帖、上下文和图片的搜索结果
```

运行一次 `collect` 默认会依次完成：

```text
collect -> 补抓上下文 -> normalize -> 下载图片 -> index
```

## 2. 代码位置与角色

| 位置 | 角色 | 作用 |
| --- | --- | --- |
| `tools/collectors/x/main.py` | CLI 总入口 | 提供 `collect`、`normalize`、`index`、`search` 和 `doctor` |
| `tools/collectors/x/config.example.json` | 示例配置 | 定义 profile、CDP 地址、数据库和采集参数 |
| `tools/collectors/x/config.json` | 本地配置 | 实际运行配置，不进入 Git |
| `tools/collectors/x/start_debug_browser.ps1` | 浏览器启动器 | 启动隔离的 Chrome/Edge 调试窗口 |
| `tools/collectors/x/x/config.py` | 配置层 | 读取并校验应用与 profile 配置 |
| `tools/collectors/x/x/collectors/browser.py` | 采集层 | 连接 CDP、滚动时间线、监听 GraphQL、保存 DOM 快照 |
| `tools/collectors/x/x/context.py` | 上下文规划层 | 查找缺失父帖与引用帖、限制追溯深度、计算恢复率 |
| `tools/collectors/x/x/storage.py` | 归档层 | 管理目录、不可变批次、manifest、JSON 和 JSONL |
| `tools/collectors/x/x/normalize.py` | 规范化层 | 解析帖子与关系、合并数据、下载图片、构建会话 |
| `tools/collectors/x/x/search.py` | 索引检索层 | 建立 SQLite/FTS，执行关键词和结构化检索 |
| `tools/collectors/x/x/doctor.py` | 诊断层 | 检查浏览器、登录会话、覆盖范围、媒体和索引状态 |
| `tools/collectors/x/tests/` | 测试 | 验证解析、合并、中文检索、图片和父帖上下文 |
| `tools/collectors/x/PLAN.md` | 设计文档 | 记录长期架构、数据模型、实施阶段和质量原则 |

## 3. 数据位置与边界

工具代码与业务数据分离。采集内容不会写入 `tools/`。

```text
sources/social/x/ShanghaoJin/
  profile.json
  raw/
    batches/<batch_id>/
      manifest.json
      responses/             # 页面返回的 GraphQL JSON
      snapshots/             # 当前页面可见帖子的 DOM 提取结果
  normalized/
    posts.jsonl
    media.jsonl
    conversations.jsonl
  assets/
    images/<post_id>/        # 与帖子关联的图片附件
  state/
    manifest.json            # 本地增量状态，不进入 Git

knowledge/databases/
  x.sqlite                   # 可从来源数据重建，不进入 Git
```

原始批次不会被规范化过程覆盖。解析逻辑改变后，可以从 `raw/batches/` 重建规范化文件和数据库。

`sources/social/x/ShanghaoJin/profile.json` 和 `README.md` 由 Git 管理；批次 manifest、帖子、图片和数据库留在 Workspace 内但由 Git 忽略。

## 4. 采集方式

### 4.1 GraphQL 主通道

采集器监听 X 页面自身发出的 GraphQL 请求，保存与用户帖子、回复和帖子详情有关的结构化 JSON。它通常提供：

- 完整帖子正文和发布时间
- 作者身份
- 回复、引用和转发关系
- 会话 ID
- 互动指标
- 图片和其他媒体字段

原始响应不包含采集器自行添加的认证头。采集器不会保存账号密码、Cookie、token 或浏览器 profile。

### 4.2 DOM 补充通道

采集器同时提取页面当前可见的帖子元素，用于补充 GraphQL 解析遗漏的数据。规范化时按帖子 ID 合并，GraphQL 数据优先，DOM 数据只补充空缺字段。

### 4.3 回复与引用上下文补抓

时间线采集结束后，工具会检查目标博主帖子中的关系：

- 回复的 `in_reply_to_id` 在本地是否有对应父帖。
- 引用的 `quoted_post_id` 在本地是否有对应帖子。
- 已有父帖本身是否仍然回复了更早帖子。

若上文缺失，工具会打开当前回复或父帖的详情页，监听 `TweetDetail` GraphQL 响应，并把父帖作为同一批次的上下文保存。默认最多向上追溯 5 层、每批最多打开 100 个详情页。它只补抓向上的回复链，不抓父帖下面的所有旁支回复。

外部作者帖子会保存为 context，但 `is_target_author` 为 false，不参与目标博主的默认搜索命中。

补抓失败会在批次 `manifest.json` 中记录原因，包括：

- `deleted`
- `unavailable`
- `protected`
- `access_denied`
- `detail_request_failed`
- `detail_requested_but_not_returned`
- `context_page_limit_reached`

### 4.4 停止条件

以下情况会停止或结束当前采集：

- 达到 `max_scrolls`
- 时间线连续多轮没有新增内容
- 需要重新登录
- 出现人工验证或异常活动提示
- X 返回限流或页面错误
- 用户手动终止程序

停止原因、观察到的帖子 ID 和时间覆盖范围保存在批次 `manifest.json` 中。

## 5. 高级命令参考

### 5.1 只采集原始数据

```powershell
python tools/collectors/x/main.py collect --route both --no-normalize
```

### 5.2 重建规范化数据

```powershell
python tools/collectors/x/main.py normalize
```

跳过图片下载：

```powershell
python tools/collectors/x/main.py normalize --skip-images
```

### 5.3 重建数据库索引

```powershell
python tools/collectors/x/main.py index
```

### 5.4 检索

```powershell
python tools/collectors/x/main.py search --query "AI 芯片" --top-k 20
python tools/collectors/x/main.py search --query "库存周期" --type reply
python tools/collectors/x/main.py search --query "估值" --start 2023-01-01 --end 2024-12-31
```

`--type` 支持：

- `original`
- `reply`
- `quote`
- `repost`

搜索结果默认只把目标博主的帖子作为命中项。若相关内容已经归档，结果会附带：

- 父帖
- 引用帖
- 转发对象
- 按原帖顺序排列的图片附件
- 原始 URL、发布时间和原始响应路径

中文三字符以上的词组使用 SQLite FTS trigram；较短关键词使用子串回退，以支持“芯片”等常见两字符词。

### 5.5 上下文补抓控制

默认启用上下文补抓。临时关闭：

```powershell
python tools/collectors/x/main.py collect --route both --max-scrolls 20 --no-hydrate-context
```

临时限制本批最多打开的详情页数量：

```powershell
python tools/collectors/x/main.py collect --route both --max-scrolls 20 --max-context-pages 30
```

本地 `config.json` 中的默认值：

```json
{
  "hydrate_context": true,
  "max_context_depth": 5,
  "max_context_pages": 100
}
```

## 6. 图片处理

图片是帖子附件，不是独立检索对象。

- 图片通过 `post_id` 与帖子关联。
- 保存原帖中的图片顺序。
- 优先请求 X CDN 的原图尺寸。
- 保存原始 URL、本地相对路径、格式、尺寸、内容哈希和下载状态。
- 图片下载失败不会阻止帖子归档，后续运行会再次尝试。
- 查询命中帖子时，图片随帖子结果一起返回。

视频和 GIF 当前主要保存媒体信息及来源关系，是否下载完整文件不属于首版范围。

## 7. Doctor 输出

```powershell
python tools/collectors/x/main.py doctor
```

主要字段：

- `cdp.ok`：浏览器调试端口是否可连接。
- `cdp.x_session_present`：是否检测到 X 登录会话。
- `raw_batches`：原始采集批次数量。
- `normalized_posts`：规范化帖子总数，包括上下文帖子。
- `target_posts`：目标博主帖子数量。
- `media_downloaded`、`media_failed`：图片下载状态。
- `earliest_post_at`、`latest_post_at`：当前数据时间覆盖范围。
- `context.direct_parent_recovery_rate`：目标博主回复的直接父帖恢复率。
- `context.quoted_post_recovery_rate`：目标博主引用帖恢复率。
- `context.last_batch`：最近批次打开的详情页数、补全数、缺失数和停止原因。
- `index`：最近一次数据库索引状态和数量。

`doctor` 返回非零退出码通常表示浏览器尚未启动或 CDP 不可连接。

## 8. 测试

```powershell
python -m pytest tools/collectors/x/tests -q
python -m compileall -q tools/collectors/x
python -m black --check tools/collectors/x/main.py tools/collectors/x/x tools/collectors/x/tests
```

测试覆盖 GraphQL 解析、GraphQL/DOM 合并、媒体关联、中文短词检索、目标作者过滤、直接父帖补抓规划、向上回复链追溯、引用帖补全和深度限制。

## 9. 安全与完整性边界

- 只采集用户有权访问的公开内容。
- 登录由用户手动完成，工具不填写密码或处理验证码。
- 不提交 `config.json`、浏览器 profile、Cookie、token、运行状态、原始语料或数据库。
- 不绕过登录、访问控制、反自动化验证或速率限制。
- 浏览器页面可见范围不等于 X 的完整历史档案。
- 所有研究引用应保留原帖 URL、发布时间和必要上下文。
- 模型推断不能冒充博主原意。

## 10. 当前未实现能力

以下能力属于后续阶段，不影响当前采集、归档和全文检索：

- 向量语义检索
- OCR 和图片内容理解
- 实体与论点模型抽取
- 观点变化和冲突检测
- MCP 服务
- 自动交易信号
