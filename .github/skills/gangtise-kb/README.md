<div align="center">

# Gangtise KB

[简体中文](README.cn.md) | **English**

Vector search over Gangtise internal knowledge bases; returns text snippets. Use gangtise-file for typed file lists and downloads.

</div>

---

## What this is

`gangtise-kb` is a local Agent Skill. Vector search over Gangtise internal knowledge bases; returns text snippets. Use gangtise-file for typed file lists and downloads.

**Keywords**: `知识库检索`, `内部研报`, `会议纪要`, `观点检索`, `向量搜索`, `文本片段`, `gangtise kb`

## Install

1. Download: [gangtise-kb.zip](https://gts-download.obs.cn-east-3.myhuaweicloud.com/skills/gangtise-kb.zip)
2. Unzip to get `gangtise-kb/`, copy it into your `skills/` directory
3. Follow `SKILL.md` for runtime setup (install deps if listed)

Configure `GTS_ACCESS_KEY` / `GTS_SECRET_KEY` from the [open platform](https://open-platform.gangtise.com/), or follow the skill’s auth file instructions.

## Example prompts

- 内部研报和纪要里，关于新能源汽车销量和政策最近都怎么说的？
- 只要外资研报，帮我搜一下「新能源汽车销量与政策」相关段落，十来条就够。

## When not to use

- 需要按类型/日期/证券筛选文件列表并下载核验时，改用 gangtise-file
- 需要完整结论或全文上下文时，不宜仅依赖 kb 片段

## Docs index

| File | Contents |
|------|----------|
| [SKILL.md](SKILL.md) | Agent workflow and conventions |
| [scripts/](scripts/) | Executable scripts / CLI |

## Version

Current version: `1.6.8` (see `SKILL.md`).
