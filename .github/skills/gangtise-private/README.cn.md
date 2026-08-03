<div align="center">

# Gangtise Private

**简体中文** | [English](README.md)

读取 Gangtise 终端个人私有数据：自选股池、微信群消息、我的会议、录音速记、AI 云盘等，结果可落盘 CSV/Markdown。

</div>

---

## 这是做什么的

`gangtise-private` 是一个本地 Agent Skill。读取 Gangtise 终端个人私有数据：自选股池、微信群消息、我的会议、录音速记、AI 云盘等，结果可落盘 CSV/Markdown。

**关键词**：`自选股池`、`微信群消息`、`我的会议`、`录音速记`、`AI 云盘`、`私有数据`、`gangtise private`

## 安装

1. 下载：[gangtise-private.zip](https://gts-download.obs.cn-east-3.myhuaweicloud.com/skills/gangtise-private.zip)
2. 解压得到 `gangtise-private/`，复制到你的 `skills/` 目录
3. 按 `SKILL.md` 说明配置运行环境（如有依赖再安装）

需配置 `GTS_ACCESS_KEY` / `GTS_SECRET_KEY`（开放平台获取），或按 skill 说明写入鉴权文件。

## 你可以这样用

- 我终端里「自选股1」这个池子有哪些票？
- 我名下所有自选股池列一下，我想核对有没有漏加。
- 指定几个股票池里的成分股名单导出来。
- AI学习群里上个月聊半导体的消息帮我翻一下。
- 我常用的几个微信群分别是哪几个，群名对一下。

## 文档索引

| 文件 | 内容 |
|------|------|
| [SKILL.md](SKILL.md) | Agent 工作流与约定（给 AI 用） |
| [references/](references/) | 详细参考资料 |
| [scripts/](scripts/) | 可执行脚本 / CLI |

## 版本

当前版本：`1.6.8`（以 `SKILL.md` 为准）。
