<div align="center">

# Gangtise File

**简体中文** | [English](README.md)

在 Gangtise 文件中心按报告、公告、纪要等类型检索文档，返回文件 ID 与元数据，并可按类型与 ID 下载完整文件。

</div>

---

## 这是做什么的

`gangtise-file` 是一个本地 Agent Skill。在 Gangtise 文件中心按报告、公告、纪要等类型检索文档，返回文件 ID 与元数据，并可按类型与 ID 下载完整文件。

**关键词**：`文件中心`、`公告检索`、`研报下载`、`会议纪要`、`gangtise file`、`找报告`、`文档 ID`

## 安装

1. 下载：[gangtise-file.zip](https://gts-download.obs.cn-east-3.myhuaweicloud.com/skills/gangtise-file.zip)
2. 解压得到 `gangtise-file/`，复制到你的 `skills/` 目录
3. 按 `SKILL.md` 说明配置运行环境（如有依赖再安装）

需配置 `GTS_ACCESS_KEY` / `GTS_SECRET_KEY`（开放平台获取），或按 skill 说明写入鉴权文件。

## 你可以这样用

- 比亚迪今年有哪些研究报告？先列个清单，大概二十篇。
- 外资研报里和自动驾驶相关的，今年上半年有哪些？
- 海外独立分析师关于肿瘤的观点有没有？原文和中文版都帮我下下来。
- 五粮液今年公告里提到业绩的有哪些？
- 电话会纪要里和锂电相关的，业绩发布会那种，帮我找二十条。

## 文档索引

| 文件 | 内容 |
|------|------|
| [SKILL.md](SKILL.md) | Agent 工作流与约定（给 AI 用） |
| [references/](references/) | 详细参考资料 |
| [scripts/](scripts/) | 可执行脚本 / CLI |

## 版本

当前版本：`1.6.8`（以 `SKILL.md` 为准）。
