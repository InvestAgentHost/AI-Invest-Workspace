from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from tools.shared.workspace_paths import DataPaths, load_data_paths


@dataclass(frozen=True)
class ProfileConfig:
    name: str
    handle: str
    profile_url: str
    output_dir: Path
    cdp_url: str
    collect_replies: bool
    collect_quotes: bool
    download_images: bool
    max_scrolls: int
    stalled_rounds: int
    min_delay: float
    max_delay: float
    hydrate_context: bool = True
    max_context_depth: int = 5
    max_context_pages: int = 100


@dataclass(frozen=True)
class AppConfig:
    default_profile: str
    database_path: Path
    profiles: dict[str, ProfileConfig]


def _resolve(path: str, data_paths: DataPaths) -> Path:
    return data_paths.resolve(path)


def load_config(path: Path, workspace: Path | None = None) -> AppConfig:
    if not path.exists():
        raise FileNotFoundError(
            f"Config not found: {path}. Copy config.example.json to config.json and edit it."
        )
    data_paths = load_data_paths(workspace)
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    profiles: dict[str, ProfileConfig] = {}
    for name, item in raw.get("profiles", {}).items():
        handle = str(item.get("handle") or name).lstrip("@")
        profiles[name] = ProfileConfig(
            name=name,
            handle=handle,
            profile_url=str(item.get("profile_url") or f"https://x.com/{handle}"),
            output_dir=_resolve(
                str(item.get("output_dir") or f"sources/social/x/{handle}"),
                data_paths,
            ),
            cdp_url=str(item.get("cdp_url", "http://127.0.0.1:9222")),
            collect_replies=bool(item.get("collect_replies", True)),
            collect_quotes=bool(item.get("collect_quotes", True)),
            download_images=bool(item.get("download_images", True)),
            max_scrolls=max(1, int(item.get("max_scrolls", 80))),
            stalled_rounds=max(1, int(item.get("stalled_rounds", 5))),
            min_delay=max(0.1, float(item.get("min_delay", 1.5))),
            max_delay=max(0.1, float(item.get("max_delay", 3.0))),
            hydrate_context=bool(item.get("hydrate_context", True)),
            max_context_depth=max(1, int(item.get("max_context_depth", 5))),
            max_context_pages=max(1, int(item.get("max_context_pages", 100))),
        )
    if not profiles:
        raise ValueError(f"No profiles are configured in {path}")
    default_profile = str(raw.get("default_profile") or next(iter(profiles)))
    if default_profile not in profiles:
        raise ValueError(f"Default profile '{default_profile}' is not configured")
    return AppConfig(
        default_profile=default_profile,
        database_path=_resolve(
            str(raw.get("database_path", "knowledge/databases/x.sqlite")), data_paths
        ),
        profiles=profiles,
    )


def select_profile(config: AppConfig, name: str | None) -> ProfileConfig:
    selected = name or config.default_profile
    try:
        return config.profiles[selected]
    except KeyError as exc:
        raise KeyError(f"Unknown profile '{selected}'") from exc
