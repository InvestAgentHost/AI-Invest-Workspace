#!/usr/bin/env python3
"""Run a vendored Gangtise script with Workspace-owned defaults."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = WORKSPACE_ROOT / ".github" / "skills"
DEFAULT_OUTPUT_ROOT = WORKSPACE_ROOT / "sources"


def _available_skills() -> list[str]:
    return sorted(
        path.name.removeprefix("gangtise-")
        for path in SKILLS_ROOT.glob("gangtise-*")
        if (path / "scripts").is_dir()
    )


def _load_workspace_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError as exc:
        raise SystemExit(
            "python-dotenv is required; install it with "
            "`python -m pip install python-dotenv`."
        ) from exc

    load_dotenv(WORKSPACE_ROOT / ".env", override=False)


def _resolve_script(skill: str, script_name: str) -> Path:
    if Path(script_name).name != script_name or not script_name.endswith(".py"):
        raise SystemExit("script must be a Python filename from the selected skill's scripts directory")

    script = SKILLS_ROOT / f"gangtise-{skill}" / "scripts" / script_name
    if not script.is_file():
        raise SystemExit(f"Gangtise script not found: {script.relative_to(WORKSPACE_ROOT)}")
    return script


def _resolve_output_root(output_subdir: str | None = None) -> Path:
    configured = os.getenv("WORK_PATH")
    output_root = Path(configured).expanduser() if configured else DEFAULT_OUTPUT_ROOT
    if not output_root.is_absolute():
        output_root = WORKSPACE_ROOT / output_root
    if output_subdir:
        relative = Path(output_subdir)
        if relative.is_absolute() or ".." in relative.parts:
            raise SystemExit("--output-subdir must be a safe relative path such as CN/688234-sicc")
        output_root = output_root / relative
    output_root = output_root.resolve()

    github_root = (WORKSPACE_ROOT / ".github").resolve()
    if output_root == github_root or github_root in output_root.parents:
        raise SystemExit("WORK_PATH must not point inside .github/; use sources or another data directory")
    return output_root


def main() -> None:
    skills = _available_skills()
    parser = argparse.ArgumentParser(
        description="Run a Gangtise skill script without writing runtime data under .github/."
    )
    proxy_group = parser.add_mutually_exclusive_group()
    proxy_group.add_argument(
        "--inherit-proxy",
        dest="use_proxy",
        action="store_true",
        help="Preserve HTTP(S)/ALL_PROXY variables (default).",
    )
    proxy_group.add_argument(
        "--direct",
        dest="use_proxy",
        action="store_false",
        help="Remove HTTP(S)/ALL_PROXY variables and force a direct connection.",
    )
    parser.set_defaults(use_proxy=True)
    parser.add_argument(
        "--output-subdir",
        help="Isolate output under sources, such as companies/CN/688234-sicc/gangtise.",
    )
    parser.add_argument("skill", choices=skills, help="Gangtise skill suffix, such as data or file.")
    parser.add_argument("script", help="Python filename under the selected skill's scripts directory.")
    parser.add_argument("script_args", nargs=argparse.REMAINDER, help="Arguments passed to the script.")
    args = parser.parse_args()

    _load_workspace_env()
    script = _resolve_script(args.skill, args.script)
    output_root = _resolve_output_root(args.output_subdir)

    env = os.environ.copy()
    env["WORK_PATH"] = str(output_root)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if not args.use_proxy:
        for name in ("ALL_PROXY", "HTTPS_PROXY", "HTTP_PROXY", "all_proxy", "https_proxy", "http_proxy"):
            env.pop(name, None)

    command = [sys.executable, "-B", str(script), *args.script_args]
    os.execve(sys.executable, command, env)


if __name__ == "__main__":
    main()
