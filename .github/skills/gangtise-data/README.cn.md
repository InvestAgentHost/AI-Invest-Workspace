<div align="center">

# Gangtise Data

**简体中文** | [English](README.md)

通过 Gangtise Open API 拉取行情、财报、估值、行业指标、题材画像等结构化金融数据，支持按证券名称或代码查询并落盘。

</div>

---

## 这是做什么的

`gangtise-data` 是一个本地 Agent Skill。通过 Gangtise Open API 拉取行情、财报、估值、行业指标、题材画像等结构化金融数据，支持按证券名称或代码查询并落盘。

**关键词**：`gangtise 数据`、`日K行情`、`财务报表`、`估值分位`、`行业指标`、`题材成分股`、`证券解析`、`量化数据`

## 安装

1. 下载：[gangtise-data.zip](https://gts-download.obs.cn-east-3.myhuaweicloud.com/skills/gangtise-data.zip)
2. 解压得到 `gangtise-data/`，复制到你的 `skills/` 目录
3. 按 `SKILL.md` 说明配置运行环境（如有依赖再安装）

需配置 `GTS_ACCESS_KEY` / `GTS_SECRET_KEY`（开放平台获取），或按 skill 说明写入鉴权文件。

## 你可以这样用

- 帮我看看茅台和五粮液最近几年的估值处在什么分位，导出成表我好做对比。
- 腾讯昨天收盘价多少？把日K拉出来，前复权就行。
- 我有一份股票代码表，能不能批量把这几只的日K都导出来？
- 比亚迪收入主要靠哪块业务？按产品拆一下主营构成。
- 茅台去年四季度主营是按产品还是按地区分的，帮我拉一下。

## 文档索引

| 文件 | 内容 |
|------|------|
| [SKILL.md](SKILL.md) | Agent 工作流与约定（给 AI 用） |
| [references/](references/) | 详细参考资料 |
| [scripts/](scripts/) | 可执行脚本 / CLI |

## 版本

当前版本：`1.6.8`（以 `SKILL.md` 为准）。
