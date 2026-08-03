from __future__ import annotations

import json
from pathlib import Path

from x.config import load_config


def write_config(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "default_profile": "Example",
                "database_path": "knowledge/databases/x.sqlite",
                "profiles": {
                    "Example": {
                        "handle": "Example",
                        "output_dir": "sources/social/x/Example",
                    }
                },
            }
        ),
        encoding="utf-8",
    )


def test_load_config_uses_workspace_data_roots(tmp_path: Path) -> None:
    (tmp_path / "config.yaml").write_text(
        "paths:\n  sources: local-sources\n  knowledge: local-knowledge\n",
        encoding="utf-8",
    )
    config_file = tmp_path / "collector.json"
    write_config(config_file)

    config = load_config(config_file, workspace=tmp_path)

    assert config.profiles["Example"].output_dir == tmp_path / "local-sources/social/x/Example"
    assert config.database_path == tmp_path / "local-knowledge/databases/x.sqlite"


def test_load_config_keeps_explicit_absolute_paths(tmp_path: Path) -> None:
    config_file = tmp_path / "collector.json"
    write_config(config_file)
    raw = json.loads(config_file.read_text(encoding="utf-8"))
    database_path = tmp_path / "external-indexes/x.sqlite"
    output_dir = tmp_path / "external-archives/Example"
    raw["database_path"] = str(database_path)
    raw["profiles"]["Example"]["output_dir"] = str(output_dir)
    config_file.write_text(json.dumps(raw), encoding="utf-8")

    config = load_config(config_file, workspace=tmp_path)

    assert config.profiles["Example"].output_dir == output_dir
    assert config.database_path == database_path
