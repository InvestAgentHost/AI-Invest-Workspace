<div align="center">

# Gangtise KB

**简体中文** | [English](README.md)

在 Gangtise 内部知识库做向量检索，返回相关文本片段；需按类型/日期筛文件列表时用 gangtise-file。

</div>

---

## 这是做什么的

`gangtise-kb` 是一个本地 Agent Skill。在 Gangtise 内部知识库做向量检索，返回相关文本片段；需按类型/日期筛文件列表时用 gangtise-file。

**关键词**：`知识库检索`、`内部研报`、`会议纪要`、`观点检索`、`向量搜索`、`文本片段`、`gangtise kb`

## 安装

1. 下载：[gangtise-kb.zip](https://gts-download.obs.cn-east-3.myhuaweicloud.com/skills/gangtise-kb.zip)
2. 解压得到 `gangtise-kb/`，复制到你的 `skills/` 目录
3. 按 `SKILL.md` 说明配置运行环境（如有依赖再安装）

需配置 `GTS_ACCESS_KEY` / `GTS_SECRET_KEY`（开放平台获取），或按 skill 说明写入鉴权文件。

## 你可以这样用

- 内部研报和纪要里，关于新能源汽车销量和政策最近都怎么说的？
- 只要外资研报，帮我搜一下「新能源汽车销量与政策」相关段落，十来条就够。

## 不适合的场景

- 需要按类型/日期/证券筛选文件列表并下载核验时，改用 gangtise-file
- 需要完整结论或全文上下文时，不宜仅依赖 kb 片段

## 文档索引

| 文件 | 内容 |
|------|------|
| [SKILL.md](SKILL.md) | Agent 工作流与约定（给 AI 用） |
| [scripts/](scripts/) | 可执行脚本 / CLI |

## 版本

当前版本：`1.6.8`（以 `SKILL.md` 为准）。
