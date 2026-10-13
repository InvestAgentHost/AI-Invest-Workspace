# 公司资料工作流

## 用户投递

新公司资料不需要预分类。研究期间可以按使用习惯直接放进：

```text
research/companies/<market>/<ticker>-<slug>/data/
```

研究完成后，Codex 先生成归档清单并询问是否归档。用户确认后，原始资料归入：

```text
sources/companies/<market>/<ticker>-<slug>/
├── inbox/              新收到、尚未整理的资料
├── sec/                财报和公告
├── ir/                 公司 IR 和官网材料
├── transcripts/        业绩会和会议纪要
├── sellside/           券商研报
└── user-provided/      用户上传的原始资料
```

归档使用哈希和来源索引，不覆盖同名文件。未确认归档前，资料继续留在研究目录的 `data/` 收件区。

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
