<div align="center">

# Gangtise File

[简体中文](README.cn.md) | **English**

Search and download documents from Gangtise File Center: reports, announcements, transcripts, and related file IDs/metadata.

</div>

---

## What this is

`gangtise-file` is a local Agent Skill. Search and download documents from Gangtise File Center: reports, announcements, transcripts, and related file IDs/metadata.

**Keywords**: `文件中心`, `公告检索`, `研报下载`, `会议纪要`, `gangtise file`, `找报告`, `文档 ID`

## Install

1. Download: [gangtise-file.zip](https://gts-download.obs.cn-east-3.myhuaweicloud.com/skills/gangtise-file.zip)
2. Unzip to get `gangtise-file/`, copy it into your `skills/` directory
3. Follow `SKILL.md` for runtime setup (install deps if listed)

Configure `GTS_ACCESS_KEY` / `GTS_SECRET_KEY` from the [open platform](https://open-platform.gangtise.com/), or follow the skill’s auth file instructions.

## Example prompts

- 比亚迪今年有哪些研究报告？先列个清单，大概二十篇。
- 外资研报里和自动驾驶相关的，今年上半年有哪些？
- 海外独立分析师关于肿瘤的观点有没有？原文和中文版都帮我下下来。
- 五粮液今年公告里提到业绩的有哪些？
- 电话会纪要里和锂电相关的，业绩发布会那种，帮我找二十条。

## Docs index

| File | Contents |
|------|----------|
| [SKILL.md](SKILL.md) | Agent workflow and conventions |
| [references/](references/) | Detailed references |
| [scripts/](scripts/) | Executable scripts / CLI |

## Version

Current version: `1.6.8` (see `SKILL.md`).
