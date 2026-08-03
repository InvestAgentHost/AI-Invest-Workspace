#!/usr/bin/env python
"""Retrieve compact, cited evidence from the local X investor archive."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[3]
COLLECTOR_ROOT = WORKSPACE / "tools" / "collectors" / "x"
if str(COLLECTOR_ROOT) not in sys.path:
    sys.path.insert(0, str(COLLECTOR_ROOT))

from x.config import load_config, select_profile  # noqa: E402
from x.search import search_posts  # noqa: E402


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Retrieve cited target-author posts from the local X archive."
    )
    result.add_argument("--query", default="", help="Keywords or exact phrase.")
    result.add_argument("--profile", help="Configured profile name.")
    result.add_argument("--types", default="original,quote", help="Comma-separated post types.")
    result.add_argument("--start", help="Inclusive ISO date/time lower bound.")
    result.add_argument("--end", help="Inclusive ISO date/time upper bound.")
    result.add_argument("--top-k", type=int, default=10, help="Maximum final evidence rows.")
    result.add_argument(
        "--snippet-chars", type=int, default=700, help="Maximum characters per post text."
    )
    result.add_argument(
        "--include-context", action="store_true", help="Include parent, quote, and repost context."
    )
    return result


def _snippet(value: Any, limit: int) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: max(0, limit - 3)] + "..."


def _compact_media(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "media_type": row.get("media_type"),
            "source_url": row.get("source_url"),
            "expanded_url": row.get("expanded_url"),
            "local_path": row.get("local_path"),
        }
        for row in rows
    ]


def _compact_post(post: dict[str, Any], snippet_chars: int) -> dict[str, Any]:
    source_paths = list(post.get("source_paths") or [])
    return {
        key: post.get(key)
        for key in (
            "id",
            "url",
            "created_at",
            "post_type",
            "author_handle",
            "quoted_post_id",
            "in_reply_to_id",
            "reposted_post_id",
        )
    } | {
        "text": _snippet(post.get("text"), snippet_chars),
        "media": _compact_media(post.get("media") or []),
        "source_paths": source_paths[-3:],
        "source_path_count": len(source_paths),
    }


def _queries(query: str) -> list[str]:
    strict = query.strip()
    terms = list(dict.fromkeys(term for term in strict.replace('"', " ").split() if term))
    return [strict, *terms] if len(terms) > 1 else [strict]


def main() -> int:
    args = parser().parse_args()
    config_path = WORKSPACE / "tools" / "collectors" / "x" / "config.json"
    config = load_config(config_path, workspace=WORKSPACE)
    profile = select_profile(config, args.profile)
    requested_types = [item.strip() for item in args.types.split(",") if item.strip()]
    allowed_types = {"original", "quote", "reply", "repost"}
    invalid = sorted(set(requested_types) - allowed_types)
    if invalid:
        parser().error(f"Unknown post types: {', '.join(invalid)}")
    if not requested_types:
        parser().error("Specify at least one post type")

    candidates: dict[str, dict[str, Any]] = {}
    per_type_limit = max(1, args.top_k)
    queries = _queries(args.query)
    query_mode = "strict"
    for query in queries:
        for post_type in requested_types:
            for post in search_posts(
                config.database_path,
                profile.name,
                query=query,
                top_k=per_type_limit,
                post_type=post_type,
                start=args.start,
                end=args.end,
                include_context=args.include_context,
            ):
                candidates.setdefault(str(post["id"]), post)
        if candidates or query == queries[-1]:
            break
        query_mode = "term_fallback"

    posts = sorted(
        candidates.values(),
        key=lambda item: (item.get("created_at") or "", item.get("id") or ""),
        reverse=True,
    )[: max(1, args.top_k)]
    evidence = [_compact_post(post, max(1, args.snippet_chars)) for post in posts]
    if args.include_context:
        for item, post in zip(evidence, posts, strict=True):
            context = post.get("context") or {}
            item["context"] = {
                label: _compact_post(value, max(1, args.snippet_chars))
                for label, value in context.items()
            }

    print(
        json.dumps(
            {
                "profile": profile.name,
                "handle": profile.handle,
                "query": args.query,
                "query_mode": query_mode,
                "types": requested_types,
                "start": args.start,
                "end": args.end,
                "count": len(evidence),
                "evidence": evidence,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
