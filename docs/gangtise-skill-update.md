# Gangtise Skills 更新流程

## 目标与边界

将 `.github/skills/` 下所有 `gangtise-*` 目录视为 Gangtise 上游托管目录。更新时使用官方 ZIP 完整覆盖，只允许执行 `tools/gangtise/normalize_skills.py` 定义的 frontmatter 兼容性归一化；不得保留其他 Workspace 补丁、凭据、缓存或运行数据。

Workspace 自有策略位于以下路径，不得被 Gangtise 更新覆盖：

- `tools/gangtise/run.py`：加载 `.env`、设置 `WORK_PATH`、阻止输出进入 `.github/`。
- `tools/gangtise/normalize_skills.py`：将顶层 `version`、`author` 移入 `metadata`，使官方 skill 兼容 Codex schema。
- `AGENTS.md`：规定 Gangtise 的调用和数据目录边界。
- `.env`：本机凭据，不进入 Git。
- `sources/companies/`：Gangtise 运行数据，不进入上游 skill 目录。

当前维护范围：

```text
.github/skills/gangtise-agent/
.github/skills/gangtise-data/
.github/skills/gangtise-file/
.github/skills/gangtise-kb/
.github/skills/gangtise-private/
```

## 更新原则

1. 从各 `SKILL.md` 的 `metadata.latestVersionUrl` 获取官方 ZIP。
2. 下载到新的临时目录，先验证 ZIP，再接触现有目录。
3. 覆盖前检查上游目录内没有 `.authorization`、`.env` 或其他本地私有文件。
4. 先备份，再使用带删除同步完整覆盖，避免旧版残留文件。
5. 保留未修改的 official staging，复制后执行确定性 frontmatter 归一化。
6. 更新后验证目录与 normalized staging 完全一致。
7. 通过 Workspace 启动器做端到端测试，不直接执行上游脚本。

## 1. 更新前检查

从 Workspace 根目录执行：

```bash
find .github/skills -maxdepth 3 -path '*/gangtise-*/*' \
  \( -name '.authorization' -o -name '.env' -o -name '*.local.*' \) -print

rg -n '^version:|latestVersionUrl:' .github/skills/gangtise-*/SKILL.md
git status --short -- .github/skills/gangtise-*
```

如果第一条命令发现私有文件，先停止更新并把它移出上游目录。不要把凭据复制进 ZIP staging 或 Git。

## 2. 下载官方包

创建本次专用临时目录：

```bash
gts_update_dir="$(mktemp -d /tmp/gangtise-skill-update.XXXXXX)"
mkdir "$gts_update_dir/official" "$gts_update_dir/staging" "$gts_update_dir/backup"
```

从各 skill 的 `latestVersionUrl` 下载。当前官方地址遵循以下形式：

```bash
curl -fL --retry 3 --connect-timeout 20 \
  -o "$gts_update_dir/gangtise-agent.zip" \
  'https://gts-download.obs.cn-east-3.myhuaweicloud.com/skills/gangtise-agent.zip'

curl -fL --retry 3 --connect-timeout 20 \
  -o "$gts_update_dir/gangtise-data.zip" \
  'https://gts-download.obs.cn-east-3.myhuaweicloud.com/skills/gangtise-data.zip'

curl -fL --retry 3 --connect-timeout 20 \
  -o "$gts_update_dir/gangtise-file.zip" \
  'https://gts-download.obs.cn-east-3.myhuaweicloud.com/skills/gangtise-file.zip'

curl -fL --retry 3 --connect-timeout 20 \
  -o "$gts_update_dir/gangtise-kb.zip" \
  'https://gts-download.obs.cn-east-3.myhuaweicloud.com/skills/gangtise-kb.zip'

curl -fL --retry 3 --connect-timeout 20 \
  -o "$gts_update_dir/gangtise-private.zip" \
  'https://gts-download.obs.cn-east-3.myhuaweicloud.com/skills/gangtise-private.zip'
```

若 `latestVersionUrl` 与上述地址不同，以最新 `SKILL.md` 元数据或 Gangtise 官方发布地址为准。

## 3. 验证与解压

逐个查看 ZIP 清单：

```bash
zipinfo -1 "$gts_update_dir/gangtise-agent.zip"
zipinfo -1 "$gts_update_dir/gangtise-data.zip"
zipinfo -1 "$gts_update_dir/gangtise-file.zip"
zipinfo -1 "$gts_update_dir/gangtise-kb.zip"
zipinfo -1 "$gts_update_dir/gangtise-private.zip"
```

每个 ZIP 必须满足：

- 只有一个与 ZIP 同名的根目录。
- 所有条目都位于该根目录内。
- 不包含绝对路径、`..` 路径穿越项或符号链接。
- 根目录中存在 `SKILL.md` 和 `scripts/`。

验证后解压：

```bash
unzip -q "$gts_update_dir/gangtise-agent.zip" -d "$gts_update_dir/official"
unzip -q "$gts_update_dir/gangtise-data.zip" -d "$gts_update_dir/official"
unzip -q "$gts_update_dir/gangtise-file.zip" -d "$gts_update_dir/official"
unzip -q "$gts_update_dir/gangtise-kb.zip" -d "$gts_update_dir/official"
unzip -q "$gts_update_dir/gangtise-private.zip" -d "$gts_update_dir/official"

find "$gts_update_dir/official" -type l -print
rg -n '^version:' "$gts_update_dir"/official/gangtise-*/SKILL.md
shasum -a 256 "$gts_update_dir"/*.zip
```

符号链接检查必须没有输出。记录版本和 ZIP SHA-256，便于在提交说明中追溯。

保留 `official/` 不变，将其复制为可安装 staging，再执行唯一允许的兼容性归一化：

```bash
cp -a "$gts_update_dir/official/." "$gts_update_dir/staging/"
python -B tools/gangtise/normalize_skills.py \
  --skills-root "$gts_update_dir/staging"
python -B tools/gangtise/normalize_skills.py \
  --skills-root "$gts_update_dir/staging" --check
```

第二条归一化命令应退出成功且没有 `needs normalization` 输出。该脚本只移动 `version`、`author`，若上游已修复或出现字段冲突，不会猜测性改写。

## 4. 备份与完整覆盖

先备份当前目录：

```bash
cp -a .github/skills/gangtise-agent "$gts_update_dir/backup/gangtise-agent"
cp -a .github/skills/gangtise-data "$gts_update_dir/backup/gangtise-data"
cp -a .github/skills/gangtise-file "$gts_update_dir/backup/gangtise-file"
cp -a .github/skills/gangtise-kb "$gts_update_dir/backup/gangtise-kb"
cp -a .github/skills/gangtise-private "$gts_update_dir/backup/gangtise-private"
```

再完整覆盖。`--delete` 会删除官方新版中已经不存在的旧文件，因此只能对以下五个精确目录使用：

```bash
rsync -a --delete "$gts_update_dir/staging/gangtise-agent/" .github/skills/gangtise-agent/
rsync -a --delete "$gts_update_dir/staging/gangtise-data/" .github/skills/gangtise-data/
rsync -a --delete "$gts_update_dir/staging/gangtise-file/" .github/skills/gangtise-file/
rsync -a --delete "$gts_update_dir/staging/gangtise-kb/" .github/skills/gangtise-kb/
rsync -a --delete "$gts_update_dir/staging/gangtise-private/" .github/skills/gangtise-private/
```

## 5. 更新后验证

确认五个目录与 normalized staging 完全一致：

```bash
diff -qr .github/skills/gangtise-agent "$gts_update_dir/staging/gangtise-agent"
diff -qr .github/skills/gangtise-data "$gts_update_dir/staging/gangtise-data"
diff -qr .github/skills/gangtise-file "$gts_update_dir/staging/gangtise-file"
diff -qr .github/skills/gangtise-kb "$gts_update_dir/staging/gangtise-kb"
diff -qr .github/skills/gangtise-private "$gts_update_dir/staging/gangtise-private"
```

五条命令都应没有输出。随后检查 Python 语法，不生成字节码缓存：

```bash
python -B tools/gangtise/normalize_skills.py --check

python -B -c 'import ast, pathlib; files=sorted(pathlib.Path(".github/skills").glob("gangtise-*/scripts/*.py")); [ast.parse(p.read_text(encoding="utf-8")) for p in files]; print("Python sources parsed:", len(files))'

find .github/skills/gangtise-* -type d -name '__pycache__' -print
git diff --check
```

`__pycache__` 检查必须没有输出。

## 6. Workspace 回归测试

始终通过 Workspace 启动器调用：

```bash
python tools/gangtise/run.py --output-subdir companies/CN/688234-sicc/gangtise data security.py -k 天岳先进
```

验收条件：

```bash
test ! -e .github/workspace
find sources/companies/CN/688234-sicc/gangtise/security -type f -name 'security_*.csv' -print
find .github/skills/gangtise-* -type d -name '__pycache__' -print
```

- 查询成功。
- 输出位于 `sources/companies/CN/688234-sicc/gangtise/`。
- `.github/workspace` 不存在。
- 上游目录中没有 `__pycache__`。

## 7. 失败恢复

如果覆盖后验证或回归测试失败，在临时目录仍存在时用备份恢复对应目录：

```bash
rsync -a --delete "$gts_update_dir/backup/gangtise-agent/" .github/skills/gangtise-agent/
rsync -a --delete "$gts_update_dir/backup/gangtise-data/" .github/skills/gangtise-data/
rsync -a --delete "$gts_update_dir/backup/gangtise-file/" .github/skills/gangtise-file/
rsync -a --delete "$gts_update_dir/backup/gangtise-kb/" .github/skills/gangtise-kb/
rsync -a --delete "$gts_update_dir/backup/gangtise-private/" .github/skills/gangtise-private/
```

恢复后重新执行目录对比和 Workspace 回归测试。确认更新成功前不要删除临时备份。

## 8. 成功后清理

所有验证通过后，仅清理本次专用临时目录：

```bash
case "$gts_update_dir" in
  /tmp/gangtise-skill-update.*) rm -rf -- "$gts_update_dir"; unset gts_update_dir ;;
  *) echo "Refusing to remove unexpected path: $gts_update_dir" ;;
esac
```

不要对未核验的变量、Workspace 根目录或 `.github/skills/` 使用递归删除。

## Frontmatter 兼容性归一化

Gangtise 官方包当前在 `SKILL.md` frontmatter 顶层使用 `version` 和 `author`，Codex 严格 skill schema 不允许这两个顶层字段。Workspace 通过 `tools/gangtise/normalize_skills.py` 自动将它们移入 `metadata`。

归一化规则严格限定为：

- 解析并验证原始 YAML。
- 仅移动顶层 `version`、`author` 原始行。
- 不修改 skill 正文或其他 frontmatter 字段。
- 重新解析并确认移动前后语义一致。
- 若上游已修复，则不产生修改。
- 若字段冲突或 YAML 布局不受支持，则停止更新。

官方原始内容始终保留在本次临时目录的 `official/`，安装目录与 normalized staging 保持一致。

## 快速复用指令

以后可直接要求 Codex：

> 按 `docs/gangtise-skill-update.md` 更新全部 Gangtise skills，保留官方原包基线，执行规定的 frontmatter 归一化，并验证数据只写入 `sources/companies/`。
