from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from x.collectors.browser import collect_browser
from x.config import AppConfig, load_config, select_profile
from x.doctor import inspect_profile
from x.normalize import normalize_profile
from x.search import index_profile, search_posts


DEFAULT_CONFIG = "tools/collectors/x/config.json"


def emit(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def progress(message: str) -> None:
    print(f"[x-collector] {message}", file=sys.stderr, flush=True)


def parse_start_date(value: str | None, timezone_name: str) -> datetime | None:
    if not value:
        return None
    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown timezone: {timezone_name}") from exc
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid --start-date value: {value}") from exc
    return parsed.replace(tzinfo=timezone) if parsed.tzinfo is None else parsed


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description="Archive and search public X posts from an authorized browser session."
    )
    root.add_argument(
        "--config", default=DEFAULT_CONFIG, help="Local JSON configuration path."
    )
    root.add_argument(
        "--profile", help="Configured profile name; defaults to default_profile."
    )
    commands = root.add_subparsers(dest="command", required=True)

    collect = commands.add_parser(
        "collect", help="Collect posts through a logged-in Chrome/Edge CDP session."
    )
    collect.add_argument(
        "--route", choices=("posts", "replies", "active", "both"), default="both"
    )
    collect.add_argument(
        "--max-scrolls", type=int, help="Override the profile scroll limit per route."
    )
    collect.add_argument(
        "--start-date",
        help="Stop after the target timeline reliably passes this local ISO date/time.",
    )
    collect.add_argument(
        "--timezone",
        default="Asia/Hong_Kong",
        help="Timezone for a --start-date without an explicit offset.",
    )
    collect.add_argument(
        "--no-normalize",
        action="store_true",
        help="Only archive raw responses and snapshots.",
    )
    collect.add_argument(
        "--no-index",
        action="store_true",
        help="Do not rebuild the SQLite search index.",
    )
    collect.add_argument(
        "--no-hydrate-context",
        action="store_true",
        help="Do not open detail pages to recover missing parents and quotes.",
    )
    collect.add_argument(
        "--max-context-pages",
        type=int,
        help="Override the maximum detail pages opened for context recovery.",
    )

    normalize = commands.add_parser(
        "normalize", help="Rebuild normalized JSONL from immutable raw batches."
    )
    normalize.add_argument(
        "--skip-images",
        action="store_true",
        help="Do not download pending image attachments.",
    )

    commands.add_parser("index", help="Rebuild the profile's SQLite and FTS index.")

    search = commands.add_parser(
        "search", help="Search normalized target-author posts."
    )
    search.add_argument(
        "--query", default="", help="Keyword or exact phrase; blank lists recent posts."
    )
    search.add_argument("--top-k", type=int, default=20)
    search.add_argument("--type", choices=("original", "reply", "quote", "repost"))
    search.add_argument("--start", help="Inclusive ISO date/time lower bound.")
    search.add_argument("--end", help="Inclusive ISO date/time upper bound.")
    search.add_argument("--no-context", action="store_true")

    commands.add_parser(
        "doctor", help="Check browser, archive, media, coverage, and index status."
    )
    return root


def _load(args: argparse.Namespace) -> tuple[AppConfig, Any]:
    config = load_config(Path(args.config))
    return config, select_profile(config, args.profile)


def run(args: argparse.Namespace) -> int:
    config, profile = _load(args)
    if args.command == "collect":
        start_at = parse_start_date(args.start_date, args.timezone)
        collected = collect_browser(
            profile,
            route=args.route,
            max_scrolls=args.max_scrolls,
            hydrate_context=False if args.no_hydrate_context else None,
            max_context_pages=args.max_context_pages,
            start_at=start_at,
        )
        result: dict[str, Any] = {"collect": asdict(collected)}
        should_process = (
            collected.status != "failed"
            and collected.stop_reason != "interrupted"
            and not args.no_normalize
        )
        if should_process:
            progress("normalizing raw batches and downloading pending media")
            result["normalize"] = normalize_profile(profile)
            if not args.no_index:
                progress("rebuilding SQLite search index")
                result["index"] = index_profile(config.database_path, profile)
        emit(result)
        return 0 if collected.status == "completed" else 1
    if args.command == "normalize":
        progress("normalizing raw batches and downloading pending media")
        emit(normalize_profile(profile, download_images=not args.skip_images))
        return 0
    if args.command == "index":
        progress("rebuilding SQLite search index")
        emit(index_profile(config.database_path, profile))
        return 0
    if args.command == "search":
        emit(
            {
                "profile": profile.name,
                "query": args.query,
                "results": search_posts(
                    config.database_path,
                    profile.name,
                    query=args.query,
                    top_k=args.top_k,
                    post_type=args.type,
                    start=args.start,
                    end=args.end,
                    include_context=not args.no_context,
                ),
            }
        )
        return 0
    if args.command == "doctor":
        report = inspect_profile(config, profile)
        emit(report)
        return 0 if report["cdp"]["ok"] else 2
    raise ValueError(f"Unsupported command: {args.command}")


def main() -> int:
    args = parser().parse_args()
    try:
        return run(args)
    except (FileNotFoundError, KeyError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
