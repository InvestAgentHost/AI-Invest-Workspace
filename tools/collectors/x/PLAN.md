# X 博主投资知识库规划

## 1. 项目定位

本项目用于持续抓取 X（Twitter）博主的公开发帖、回复、引用帖及相关上下文，将其保存为可增量更新、可检索、可引用的本地知识库。

首个样例博主：`https://x.com/ShanghaoJin`（金老师）。

项目的核心目标不是一次性生成博主分析报告，而是建立一个长期可复用的数据源。未来进行公司、行业或宏观投研时，可以检索该知识库，加入博主的历史视角、论据和观点变化。

## 2. 边界与原则

- 只采集公开内容，或用户拥有合法访问权限的内容。
- 遵守 X API、账号权限、速率限制和服务条款；不把绕过登录或反爬机制作为设计目标。
- 原始内容必须保留，模型生成的标签、摘要和论点只能作为可重建的派生数据。
- 所有投研上下文都应返回原帖链接、发布时间和必要的对话上下文。
- 区分“博主明确表达的内容”和“模型推断”，不将推断伪装成原意。
- 知识库用于研究辅助，不构成投资建议。

## 3. 整体架构

```text
X 数据源
  -> 采集器
  -> 原始归档层
  -> 规范化与关系层
  -> 全文/结构化/向量索引
  -> 投研检索 API 或 MCP
  -> 研究任务上下文
```

### 3.1 采集层

当前实施优先级：

1. 用户授权的浏览器采集：用户在本机 Chrome 中手动登录 X，采集器通过 CDP 连接该浏览器。
2. 本地导入：支持 X 数据导出包、JSON、CSV 或手工整理的数据。
3. 官方 X API v2：保留可替换的 collector 接口，未来需要更高稳定性或完整性时再接入；当前不购买 API credits。

#### 授权浏览器采集规则

- 登录必须由用户在真实浏览器中手动完成；采集器不接收、保存或填写账号密码，也不自动处理验证码。
- 采集器通过 CDP 连接用户明确启动的浏览器调试端口，不复制浏览器 profile、Cookie、token 或 storage state 到项目目录。
- 优先监听并保存页面自身请求获得的结构化 JSON/GraphQL 响应；DOM 解析只作为缺失字段的补充。
- 不绕过登录、访问控制、验证码、速率限制或反自动化机制；遇到验证或访问限制时停止相关请求并记录状态。
- 使用保守的滚动和请求间隔，限制单次滚动次数和运行时长，并支持人工停止和断点续采。
- 浏览器采集不保证完整历史覆盖。每次运行必须记录可观察到的最早和最晚帖子时间、分页或滚动终止原因及可能的数据缺口。
- 认证信息、浏览器 profile、运行日志和网络响应中的敏感头不得写入可提交文件；原始响应落盘前应过滤认证头和非目标账号的敏感数据。
- 时间线采集后检查目标博主回复和引用关系；缺失直接父帖或引用帖时，打开当前帖子详情页并监听 `TweetDetail` 响应补抓上下文。
- 父帖仍是回复时沿回复链向上追溯，默认最多 5 层；只补上文，不抓取父帖下的全部旁支回复。
- 每批详情页访问设置上限并按帖子 ID 去重；遇到登录验证、限流或访问限制时停止补抓，不绕过限制。
- 已删除、受保护、不可访问或详情页未返回的上下文必须记录帖子 ID 和失败原因。

不能只抓博主主页，还应覆盖：

- `from:ShanghaoJin` 的原创帖、回复、引用帖和转发
- 用户回复过的原帖
- 用户引用的原帖
- 对话串上下文

采集器需要具备：

- 增量游标和批次 manifest
- 内容哈希去重
- 429、网络错误和断点重试
- 原始响应保存
- 抓取时间、抓取方式和可见性记录
- 上下文详情页数量、补全关系数、缺失关系及原因

#### 图片采集规则

图片作为帖子的附件采集和保存，不作为独立知识对象或独立检索入口。

- 采集帖子时同步读取图片媒体字段，并将可访问的原图保存到该博主来源目录。
- 每张图片必须通过 `post_id` 关联到具体帖子；同一图片被多个帖子引用时可按媒体 ID 或内容哈希去重，但必须保留全部帖子关联。
- 保存媒体 ID、原始 URL、本地相对路径、格式、尺寸、内容哈希、抓取时间和下载状态。
- 保留帖子内图片的原始顺序，保证检索结果可以按原帖顺序展示。
- 图片下载失败、链接失效或权限受限时，不影响帖子入库；应保留原始 URL、失败状态和错误原因，供后续重试。
- 默认不对图片建立独立向量索引或图片搜索；未来如增加 OCR 或视觉理解，其结果只能作为可重建的派生数据，并继续引用原帖和原图。
- 视频、GIF 等其他媒体至少保存媒体元数据、封面和原始链接；是否下载原文件由配置决定。

### 3.2 原始归档层

原始数据不可覆盖，后续解析逻辑变化时应能从原文重新构建索引。

建议保存：

- 帖子 ID、作者、文本、发布时间、URL
- 帖子类型：`original`、`reply`、`quote`、`repost`
- 回复对象、引用对象和会话 ID
- 语言、媒体、外链和互动数据
- 图片原文件及其与帖子的关联、顺序和下载状态
- 抓取时间、数据来源、原始响应路径、内容哈希

### 3.3 规范化与关系层

将数据统一为帖子、用户、实体、对话和关系等结构，建立：

- 回复链
- 引用链
- 对话串
- 提及关系
- 帖子与公司、股票、行业、宏观变量的关系

回复内容不能被视为附属数据。博主经常在回复中补充条件、反驳观点和例外情况。

外部作者的父帖和引用帖作为 context 保存，用于解释目标博主观点，但不作为目标博主帖子参与默认检索命中。规范化时计算直接父帖恢复率和引用帖恢复率。

### 3.4 检索层

同时提供三种索引：

- SQLite 或 DuckDB：按作者、时间、类型、实体等结构化过滤
- 全文索引：关键词、短语和精确匹配
- 向量索引：自然语言语义搜索

典型查询：

```text
主题 = 半导体
公司 = NVDA
时间 = 2023-01-01 至 2024-12-31
类型 = 回复
关键词 = 估值、周期、库存
语义问题 = “他如何判断 AI 芯片周期见顶？”
```

检索结果必须带原帖 ID、URL、发布时间和上下文，不能只返回脱离原文的向量片段。

当命中的帖子包含图片时，检索结果应同时返回按原帖顺序排列的图片附件，包括本地相对路径、原始 URL、媒体类型和下载状态。图片跟随帖子结果返回，不单独参与默认检索和排序。

## 4. 数据模型

### 4.1 posts

```text
id
author_id
created_at
text
post_type
conversation_id
in_reply_to_id
quoted_post_id
lang
like_count/reply_count/repost_count/view_count
url
raw_path
content_hash
```

### 4.2 entities

```text
post_id
entity_type: company/stock/industry/country/person/indicator
name
canonical_name
ticker
confidence
```

### 4.3 claims（派生数据）

```text
claim_id
post_id
topic
claim_text
stance
time_horizon
conditions
confidence
analysis_version
```

`claims` 只用于检索和聚合，不能替代原始帖子。

### 4.4 conversations

```text
conversation_id
root_post_id
post_ids
participants
created_at
updated_at
```

### 4.5 media

```text
media_id
post_id
media_type: image/video/gif
position
source_url
local_path
mime_type
width
height
content_hash
downloaded_at
download_status
error
```

`media` 是帖子附件关系。默认查询入口仍是帖子；命中帖子后按 `position` 返回其媒体。若使用媒体 ID 或内容哈希对文件去重，不得丢失媒体与多个帖子的关联。

## 5. 目录设计

```text
tools/collectors/x/
  PLAN.md
  README.md
  requirements.txt
  config.example.json
  config.json                 # 本地配置，不入库
  main.py

  x/
    collectors/
      api.py
      browser.py
      importer.py
    normalize.py
    conversations.py
    entities.py
    chunking.py
    embeddings.py
    search.py
    storage.py
  tests/

sources/social/x/ShanghaoJin/
  profile.json                # 受 Git 管理的来源身份
  README.md

sources/social/x/ShanghaoJin/
  raw/
  normalized/
  assets/
    images/                   # 按帖子关联保存的图片附件
  state/

knowledge/
  indexes/x/ShanghaoJin/
  databases/x.sqlite
```

`sources/social/x/ShanghaoJin/profile.json` 保存来源身份和采集范围；实际帖子、图片和状态位于 Workspace 内的 ignored payload，检索数据库位于 ignored `knowledge/`：

```json
{
  "handle": "ShanghaoJin",
  "display_name": "金老师",
  "language": ["zh", "en"],
  "enabled": true,
  "collect_replies": true,
  "collect_quotes": true
}
```

## 6. 建议 CLI

```powershell
python tools/collectors/x/main.py collect --handle ShanghaoJin
python tools/collectors/x/main.py normalize
python tools/collectors/x/main.py index --profile ShanghaoJin
python tools/collectors/x/main.py search --profile ShanghaoJin --query "AI 芯片估值和库存周期" --top-k 20
python tools/collectors/x/main.py doctor
```

其中 `doctor` 用于检查配置、认证、数据缺口、重复率、索引状态和最近一次同步结果。

## 7. 分阶段实施

### 阶段一：采集与归档

- 完成配置文件和博主 profile
- 实现通过 CDP 连接用户已登录 Chrome 的授权浏览器采集
- 优先解析页面的结构化 JSON/GraphQL 响应，并以 DOM 解析补充必要字段
- 对缺失父帖和引用帖执行有深度与页面数上限的详情页补抓
- 保存原始 JSON
- 保存图片附件及其帖子关联、原始顺序和下载状态
- 实现分页、游标、去重、重试和 manifest

验收：无需保存账号密码、Cookie 或 token 即可连接用户已登录的浏览器；同一批数据重复运行不会产生重复记录或重复图片文件；中断后可以继续；图片下载失败不阻塞帖子归档，并可在后续运行中重试；运行结果明确报告实际时间覆盖、上下文补抓结果和终止原因。

### 阶段二：规范化与关系

- 建立统一帖子模型
- 区分原创、回复、引用和转发
- 恢复回复链、引用链和对话上下文
- 保存结构化数据库

验收：给定一个回复，可以找到其父帖、向上回复链、会话和相关引用内容；直接父帖或引用帖无法恢复时有明确原因。

### 阶段三：检索索引

- 加入全文检索
- 加入主题和实体索引
- 加入向量检索
- 设计统一 Python API

验收：可以按关键词、实体、时间和自然语言问题组合查询，并返回原帖引用；命中含图帖子时，同时返回按原帖顺序排列的图片附件。

### 阶段四：投研调用

- 提供投研任务使用的检索上下文格式
- 加入原帖引用、时间范围和数据覆盖说明
- 通过 MCP 或其他统一接口供分析 Agent 调用

验收：针对真实投研问题，结果既有相关帖子，也保留上下文和时间信息。

### 阶段五：高级派生数据

- 主题分类
- 实体标准化
- 论点和条件抽取
- 观点变化与潜在冲突检测
- 预测台账

这些内容均应作为可删除、可重建的派生索引，不能污染原始归档。

## 8. 质量与可观测性

每次采集和分析保存：

- 数据批次和游标
- 时间覆盖范围
- 失败、重试和限流记录
- 去重数量
- 缺失字段统计
- 模型名称、prompt 版本和分析版本

主要质量指标：

- 时间区间覆盖率
- 分页完整性
- 重复率
- 回复和引用链恢复率
- 上下文详情页成功率及缺失原因分布
- 搜索结果相关性
- 原帖链接可复核率

## 9. 是否需要炼化为 Skill

知识库本身不应炼化成 Skill。

适合放入知识库的内容：

- 博主帖子、回复和引用记录
- 原始文本和元数据
- 向量索引和全文索引
- 观点、实体和主题等派生数据

适合放入 Skill 的内容：

- 如何调用知识库
- 如何按主题和时间检索
- 如何引用原帖
- 如何区分原文与模型推断
- 如何处理观点冲突和时间变化
- 如何说明数据覆盖范围和不确定性

推荐后续制作一个通用的 `x-investor-research` Skill，调用不同博主 profile 的知识库。不要为金老师单独制作一个包含大量历史事实的 Skill，因为帖子会持续更新，而且不适合通过 Skill 文件进行高效检索。

## 10. 当前优先级

当前优先级应是：

1. 通过用户授权的真实浏览器合法、保守、可增量地获得 X 数据
2. 完整保存原始内容
3. 正确恢复回复和引用关系
4. 建立全文、结构化和向量检索
5. 用真实投研问题验证检索质量
6. 在检索接口稳定后，再编写通用 Skill

当前不购买 X API credits。官方 API collector 仅保留接口边界，不作为首版实现或运行依赖。

暂不优先做自动交易信号、博主能力排名或一次性画像报告。这些功能依赖更严格的时间对齐和人工复核，且容易将文本检索误包装成投资建议。
