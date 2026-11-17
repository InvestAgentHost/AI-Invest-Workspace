# 中间产物与断点续研

长任务要能靠文件接续，不依赖压缩后的聊天记忆。范围和重要决定、来源原件、核验数据、章稿、判断依据与读者反馈各留一处；短摘要负责导航，不复制全部材料，也不保存私人逐步推理。

## 目录和更新时点

复用用户指定的项目位置及已有结构，不把任何特定仓库当作固定根目录。一个新的公司项目可以采用：

```text
<company-project>/
  <report>.docx
  sources/                         原件、FocusAlpha返回和来源快照
  data/
    research-context.md            范围、截止日、章序、用户决定
    source-index.csv               资料路径及来源定位，可沿用已有格式
    evidence-ledger.md             重要判断、支持/反证、计算和缺口
    RESUME.md                      当前状态、下一步及文件入口
    research-state.json            使用随附检查点脚本时建立
    chapters/<chapter-id>/
      memo.md                      问题、证据、局部洞见、章间连接
      draft.md                     当前正文；也可引用已有独立章文件
      reading-review.md            受审版本、读者反馈及证据回查
    derived/                       规范化数据、计算、图形程序
  outputs/figures/                  当前采用图片
```

这些是内部工作产物，不是要求额外交付的一套文件。已有来源和覆盖记录可以复用，不为符合示例改名或复制数据；纯取数与短问题无需创建空白章稿和阅读记录。原始来源保持不可变，派生数据记录输入版本。

每批有效资料保存后更新来源与当前问题的进展；完成一章、改变重要口径/范围、移交前更新恢复摘要。`RESUME.md` 保持简短：目标与产物、已完成什么、当前缺口、下一动作、关键决定和文件路径。证据细节回链到索引和 memo，不粘入整段原文或巨大 JSON。

章 memo 保留作者能交接的判断：本章回答什么、证据支持到哪里、哪项解释更可信、重要反证与条件，以及它支持、限定或挑战了其他章什么判断。在现有章 memo 中随证据更新章间发现，供主体章节完成后归纳全篇主线。研究中发现原始数据有误时，保留原版本与修正理由并重查下游，不静默改数字。

恢复时先读 context、RESUME 和状态，再读取当前章及依赖的证据。核对截止日、数据/定义、章稿和图版本；不要仅凭摘要或旧“通过”继续。前提、稿件或重要图像改变时，相关章回到待复核状态；下游所记录的旧版本只有真实复查后才能更新。

## 可选检查点脚本

[research_checkpoint.py](../scripts/research_checkpoint.py) 仅用 Python 3.10+ 标准库运行，可初始化、检查或保存状态快照，不读取其他 skill。路径从实际安装位置取得，`--company-root` 指向用户项目目录；以下假定当前目录已是本 skill 根目录：

```sh
python3 scripts/research_checkpoint.py init --company-root /path/to/company-project --as-of YYYY-MM-DD
python3 scripts/research_checkpoint.py check --company-root /path/to/company-project --require-reading-review
python3 scripts/research_checkpoint.py snapshot --company-root /path/to/company-project --require-reading-review
```

替换示例参数。`init` 不覆盖已有文件，也不自动创建空白章节。使用 `schema_version: 2`；章状态可为 `pending / in_progress / complete / partial / blocked / not_applicable`。实际工作开始才登记章节，其字段如下：

```json
{
  "id": "operations",
  "kind": "narrative",
  "status": "in_progress",
  "revision": 1,
  "as_of": "2026-11-16",
  "memo": "data/chapters/operations/memo.md",
  "draft": "data/chapters/operations/draft.md",
  "evidence_ids": ["S001"],
  "depends_on": {},
  "artifacts": [],
  "reading_review": {"status": "pending"}
}
```

日期使用项目实际截止日。`depends_on` 以章 ID 映射采用的版本号。`references` 和 `artifacts` 登记公司目录内已有文件，来源在项目外时在来源索引记录路径，不为适配检查点复制全部原件。脚本路径不能逃逸项目目录。

正文 `kind: narrative` 标为 `complete` 或证据有限的 `partial` 时，需要实际非空且独立于 memo/稿件的阅读记录；填写 `reading_review.status: pass`、当前 `chapter_revision`、当前稿件原始字节的 `draft_sha256` 及 `record_path`。记录内容按 [复核规范](review-and-delivery.md) 执行。`data_only` 仅供纯数据模块，其 memo/draft 可指向处理记录与数据产物，不要求阅读记录，不能用它绕过正文检查。

改稿后旧哈希失效，将章设为 `in_progress`、复核设为 `pending`，复核新版再记录通过。图片与插入尺寸变更由现有阅读记录追踪，脚本不会自动判断图义。

`check --require-reading-review` 只检查登记状态、依赖版本和文件一致性。空章集合或进行中的状态也可能通过；它不证明研究完整、审阅真实、证据正确或 Word 可读。正式完成仍须将约定章序与实际正文、图像和复核记录逐项核对。

`snapshot` 保存当时的状态、恢复摘要以及引用文件的 SHA-256 清单。引用正文和图像只有指纹，不是完整备份；需要回溯全文时保留项目自己的版本历史或独立归档。不要把快照目录称作可恢复全部内容的备份。
