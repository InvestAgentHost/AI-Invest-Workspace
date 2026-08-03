# 公司资料工作流

## 用户投递

新公司资料不需要预分类，直接放进：

```text
sources/companies/<market>/<ticker>-<slug>/inbox/
```

随后让 Codex 整理该公司资料。整理结果仍然留在同一个公司目录：

```text
sources/companies/<market>/<ticker>-<slug>/
├── inbox/              新收到、尚未整理的资料
├── filings/            财报和公告
├── broker-research/    券商研报
├── official-website/   官网抓取
├── gangtise/           Gangtise 下载
├── user-materials/     用户上传但暂时不确定类型的资料
└── models/             自制模型和工作簿
```

不要求为每个文件维护 manifest、哈希或 Git 索引。需要知道资料是否存在时，直接查看公司目录。

## 研究结论

分析、判断和整理后的研究结论进入：

```text
research/companies/<market>/<ticker>-<slug>/
```

这些 Markdown、YAML 和文本进入 Git，并使用相对路径引用 `sources/` 原始资料。

## 手动同步

换设备时按课题压缩：

```text
sources/companies/CN/688234-sicc/
sources/social/x/ShanghaoJin/
sources/publishers/substack/damnnang/
```

不要传输 `.git/`、`.venv/`、`.local/`、`knowledge/`、`data/derived/`、Cookie 或凭据。
