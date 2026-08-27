"""Project-level configuration for long-lived ResearchFoundry workspaces."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import os
import tempfile
from typing import Any

import yaml


class ProjectConfigError(ValueError):
    """Raised when the user project configuration is unsafe or incomplete."""


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    """Resolved paths and defaults shared by preprocessing and research runs."""

    project_root: Path
    workspace_root: Path
    company_root: Path
    default_domain: str = "general"
    default_research_shape: str = "comprehensive"
    knowledge_policy: str = "reuse"
    include_published_runs: bool = True
    include_raw_sources: bool = True
    include_prepared_sources: bool = True
    include_research_notes: bool = True
    include_reports: bool = True

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in ("project_root", "workspace_root", "company_root"):
            payload[key] = str(payload[key])
        return payload


def load_project_config(path: str | Path) -> ProjectConfig:
    """Load and resolve a project YAML file without reading secrets."""

    config_path = Path(path).expanduser().resolve()
    if config_path.is_symlink() or not config_path.is_file():
        raise ProjectConfigError("project config must be a regular YAML file")
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        raise ProjectConfigError(f"unable to read project config: {error}") from error
    if not isinstance(payload, dict):
        raise ProjectConfigError("project config must be a YAML object")
    if payload.get("schema_version") != "researchfoundry_project.v1":
        raise ProjectConfigError("unsupported project config schema_version")
    base = config_path.parent
    project_root = _resolve_path(payload.get("project_root"), base, "project_root")
    workspace_root = _resolve_path(payload.get("workspace_root"), base, "workspace_root")
    company_root = _resolve_path(payload.get("company_root"), base, "company_root")
    if company_root != workspace_root and workspace_root not in company_root.parents:
        raise ProjectConfigError("company_root must stay below workspace_root")
    domain = str(payload.get("default_domain", "general")).strip()
    shape = str(payload.get("default_research_shape", "comprehensive")).strip()
    policy = str(payload.get("knowledge_policy", "reuse")).strip()
    if not domain or shape not in {"bounded", "comprehensive"}:
        raise ProjectConfigError(
            "default_domain must be non-empty and research shape must be bounded or comprehensive"
        )
    if policy not in {"reuse", "raw_only", "isolated"}:
        raise ProjectConfigError("knowledge_policy must be reuse, raw_only, or isolated")
    flags = payload.get("knowledge_base", {})
    if flags is None:
        flags = {}
    if not isinstance(flags, dict):
        raise ProjectConfigError("knowledge_base must be a YAML object")
    return ProjectConfig(
        project_root=project_root,
        workspace_root=workspace_root,
        company_root=company_root,
        default_domain=domain,
        default_research_shape=shape,
        knowledge_policy=policy,
        include_published_runs=_bool_flag(flags, "include_published_runs", True),
        include_raw_sources=_bool_flag(flags, "include_raw_sources", True),
        include_prepared_sources=_bool_flag(flags, "include_prepared_sources", True),
        include_research_notes=_bool_flag(flags, "include_research_notes", True),
        include_reports=_bool_flag(flags, "include_reports", True),
    )


def write_project_config(
    output: str | Path,
    *,
    project_root: str | Path,
    workspace_root: str | Path,
    company_root: str | Path,
) -> Path:
    """Create a starter config atomically; never overwrite a user config."""

    destination = Path(output).expanduser().resolve()
    if destination.exists():
        raise ProjectConfigError("project config already exists")
    values = {
        "schema_version": "researchfoundry_project.v1",
        "project_root": str(Path(project_root).expanduser().resolve()),
        "workspace_root": str(Path(workspace_root).expanduser().resolve()),
        "company_root": str(Path(company_root).expanduser().resolve()),
        "default_domain": "general",
        "default_research_shape": "comprehensive",
        "knowledge_policy": "reuse",
        "knowledge_base": {
            "include_published_runs": True,
            "include_raw_sources": True,
            "include_prepared_sources": True,
            "include_research_notes": True,
            "include_reports": True,
        },
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    rendered = yaml.safe_dump(values, allow_unicode=True, sort_keys=False)
    fd, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    except OSError:
        Path(temporary).unlink(missing_ok=True)
        raise
    return destination


def _resolve_path(value: Any, base: Path, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ProjectConfigError(f"{field} must be a non-empty path")
    path = Path(value).expanduser()
    return (path if path.is_absolute() else base / path).resolve()


def _bool_flag(flags: dict[str, Any], key: str, default: bool) -> bool:
    value = flags.get(key, default)
    if not isinstance(value, bool):
        raise ProjectConfigError(f"knowledge_base.{key} must be boolean")
    return value
