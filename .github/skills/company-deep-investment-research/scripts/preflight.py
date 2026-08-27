#!/usr/bin/env python3
"""Run a concise prerequisite check for the bundled research runtime."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path)
    args = parser.parse_args()
    bridge = Path(__file__).with_name("research_foundry_local.py")
    command = [sys.executable, str(bridge), "doctor"]
    if args.workspace:
        command.extend(("--workspace", str(args.workspace)))
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
