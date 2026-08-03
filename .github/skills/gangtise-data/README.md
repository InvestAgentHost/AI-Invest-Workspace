<div align="center">

# Gangtise Data

[简体中文](README.cn.md) | **English**

Fetch structured market data via Gangtise Open API: quotes, financials, valuation, industry indicators, themes, and security resolution.

</div>

---

## What this is

`gangtise-data` is a local Agent Skill. Fetch structured market data via Gangtise Open API: quotes, financials, valuation, industry indicators, themes, and security resolution.

**Keywords**: `gangtise 数据`, `日K行情`, `财务报表`, `估值分位`, `行业指标`, `题材成分股`, `证券解析`, `量化数据`

## Install

1. Download: [gangtise-data.zip](https://gts-download.obs.cn-east-3.myhuaweicloud.com/skills/gangtise-data.zip)
2. Unzip to get `gangtise-data/`, copy it into your `skills/` directory
3. Follow `SKILL.md` for runtime setup (install deps if listed)

Configure `GTS_ACCESS_KEY` / `GTS_SECRET_KEY` from the [open platform](https://open-platform.gangtise.com/), or follow the skill’s auth file instructions.

## Example prompts

- 帮我看看茅台和五粮液最近几年的估值处在什么分位，导出成表我好做对比。
- 腾讯昨天收盘价多少？把日K拉出来，前复权就行。
- 我有一份股票代码表，能不能批量把这几只的日K都导出来？
- 比亚迪收入主要靠哪块业务？按产品拆一下主营构成。
- 茅台去年四季度主营是按产品还是按地区分的，帮我拉一下。

## Docs index

| File | Contents |
|------|----------|
| [SKILL.md](SKILL.md) | Agent workflow and conventions |
| [references/](references/) | Detailed references |
| [scripts/](scripts/) | Executable scripts / CLI |

## Version

Current version: `1.6.8` (see `SKILL.md`).
