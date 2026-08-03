from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


LOCAL_CONFIG_NAME = "config.yaml"


@dataclass(frozen=True)
class DataPaths:
    """Resolved roots for data that may live outside the Git workspace."""

    workspace_root: Path
    sources_root: Path
    knowledge_root: Path

    def resolve(self, value: str | Path) -> Path:
        candidate = Path(value)
        if candidate.is_absolute():
            return candidate

        parts = candidate.parts
        if parts and parts[0].lower() == "sources":
            return self.sources_root.joinpath(*parts[1:])
        if parts and parts[0].lower() == "knowledge":
            return self.knowledge_root.joinpath(*parts[1:])
        return self.workspace_root / candidate


def find_workspace_root(start: Path | None = None) -> Path:
    """Find the workspace from a child path, falling back to the current directory."""

    candidate = (start or Path.cwd()).resolve()
    for directory in (candidate, *candidate.parents):
        if (directory / "AGENTS.md").is_file():
            return directory
    return candidate


def _configured_path(raw: object, default: Path, workspace: Path) -> Path:
    if not raw:
        return default
    candidate = Path(str(raw))
    return candidate if candidate.is_absolute() else (workspace / candidate).resolve()


def load_data_paths(workspace_root: Path | None = None) -> DataPaths:
    """Load optional local roots, retaining workspace directories as the default."""

    workspace = find_workspace_root(workspace_root)
    config_path = workspace / LOCAL_CONFIG_NAME
    raw: dict[str, object] = {}
    if config_path.exists():
        try:
            loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML in {config_path}: {exc}") from exc
        if not isinstance(loaded, dict):
            raise ValueError(f"{config_path} must contain a YAML mapping")
        paths = loaded.get("paths", {})
        if not isinstance(paths, dict):
            raise ValueError(f"{config_path} field 'paths' must be a mapping")
        raw = paths

    return DataPaths(
        workspace_root=workspace,
        sources_root=_configured_path(raw.get("sources"), workspace / "sources", workspace),
        knowledge_root=_configured_path(raw.get("knowledge"), workspace / "knowledge", workspace),
    )
