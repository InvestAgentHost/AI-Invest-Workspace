---
name: deepseek-source-tagging
description: "使用 DeepSeek 为 AI Invest Workspace 中的 Damnang Substack 原始 Markdown 文章生成本地标签。用户要求给 Damnang 文章打标签、批量给来源 Markdown 加 LLM 标签或重新生成文章标签时使用。"
metadata:
  category: knowledge-management
  provider: DeepSeek
---

# DeepSeek 来源文章打标签

## 适用场景

当用户用自然语言要求给 Damnang 的 Substack 文章、投研来源 Markdown 或
本地来源文章打标签时，使用本 Skill。默认处理当前归档中的全部文章，
除非用户指定单篇或数量范围。

## 执行方式

调用工作区现有工具：

```bash
python -B tools/knowledge/llm_tag_articles.py
```

工具默认读取：

`sources/publishers/substack/damnnang/normalized/markdown/`

它会把每篇完整 Markdown 原文发送给 DeepSeek API，要求模型返回 JSON
格式的 `tags` 数组，然后写回该文章的 YAML frontmatter。API 配置从：

`.env`

读取。不得打印、暴露或复制 `DEEPSEEK_API_KEY` 的值。若工具提示缺少密钥，
只告知用户在上述 `.env` 中设置 `DEEPSEEK_API_KEY`，不要自行猜测或输出密钥。

把自然语言范围转换为以下参数：

- “全部文章”：不加范围参数。
- “处理某一篇”：加 `--slug <不含 .md 的文件名>`。
- “前 N 篇”：加 `--limit N`。
- “预览”：加 `--dry-run`，只检查选择范围，不调用 API，也不修改文件。
- “重新生成/强制更新”：加 `--force`，忽略已有缓存重新调用 API。

示例：

```bash
# 单篇
python -B tools/knowledge/llm_tag_articles.py \
  --slug nokia-nok-the-market-is-still-putting

# 前 10 篇
python -B tools/knowledge/llm_tag_articles.py \
  --limit 10

# 预览前 10 篇
python -B tools/knowledge/llm_tag_articles.py \
  --dry-run --limit 10
```

除非用户明确要求预览，否则直接执行用户指定的范围。用户已经指定人工确认
默认通过，因此不要暂停等待逐篇确认。

## 标签边界

模型可以根据完整文章自由判断核心主题，不使用固定主题枚举。提示词要求返回
3-8 个简洁标签，关注正文真正讨论的公司、技术、产业和价值链环节，避免泛化词
和仅顺带提到的概念。工具会统一格式并加上 `llm/` 前缀，例如
`llm/optical-interconnect`。

工具只维护 `sources/` 原始资料 Markdown 中的 `llm/` 标签。这些修改不会进入 Git，也不用于 Obsidian 图谱：

- 保留已有的人工标签和来源标签。
- 新结果会替换旧的 `llm/` 标签。
- 不创建主题页、实体注册表、投资结论或 `[[内部链接]]`。
- 不修改 normalized Markdown 归档之外的原始来源文件。

结果缓存位于：

`knowledge/indexes/llm-tags/`

缓存按文章内容、模型和提示词版本区分，重复执行时通常不会再次调用 API。

## 完成后

简要报告处理范围、文章数量、API/缓存结果和失败项。不得报告 API 密钥。
生成的标签只是知识发现元数据，不是最终投资判断；除非用户另有要求，不要在
本 Skill 中自动沉淀投资结论或建立人工判断关系。
