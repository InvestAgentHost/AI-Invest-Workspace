# macOS 与 Windows 初始化

## Git 层

在新机器克隆仓库后，从仓库根创建 `.venv`，安装 `requirements-workspace.txt`，再从 `config.example.yaml` 创建本机 `config.yaml`。tracked 配置只使用相对路径。

macOS/Linux：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-workspace.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

Windows PowerShell：

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-workspace.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 本地资料层

从另一台机器压缩 `sources/` 下所需的公司、平台或供应商子目录，通过微信传输后按原相对路径解压。无需传输整个 Workspace，也不要传输运行时目录。

首次恢复后检查：文件数与压缩前大致一致；抽查重要文件可以打开；`git status` 不显示 `sources/` 文件。

## Obsidian

Vault 根放在 Workspace 父目录，按 `docs/obsidian-vault.md` 配置排除。Workspace 内容由 GitHub 和手动原始资料包管理，不由 Obsidian Sync 管理。
