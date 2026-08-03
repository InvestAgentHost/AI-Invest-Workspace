from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from .config import AppConfig, ProfileConfig
from .context import context_coverage
from .storage import SourcePaths, read_json, read_jsonl


def _cdp_status(url: str) -> dict[str, Any]:
    endpoint = url.rstrip("/") + "/json/version"
    try:
        with urlopen(endpoint, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
        result = {"ok": True, "endpoint": endpoint, "browser": payload.get("Browser")}
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as playwright:
                browser = playwright.chromium.connect_over_cdp(url)
                contexts = browser.contexts
                cookies = contexts[0].cookies("https://x.com") if contexts else []
                cookie_names = {item.get("name") for item in cookies}
                result["browser_contexts"] = len(contexts)
                result["x_session_present"] = "auth_token" in cookie_names
        except Exception as exc:
            result["session_check_error"] = f"{type(exc).__name__}: {exc}"
        return result
    except Exception as exc:
        return {
            "ok": False,
            "endpoint": endpoint,
            "error": f"{type(exc).__name__}: {exc}",
        }


def inspect_profile(config: AppConfig, profile: ProfileConfig) -> dict[str, Any]:
    paths = SourcePaths.from_root(profile.output_dir)
    source_profile = read_json(paths.root / "profile.json", {})
    posts = read_jsonl(paths.posts_jsonl)
    media = read_jsonl(paths.media_jsonl)
    batch_manifests = sorted(paths.raw_batches.glob("*/manifest.json"))
    last_batch = read_json(batch_manifests[-1], {}) if batch_manifests else {}
    index = None
    if config.database_path.exists():
        try:
            with sqlite3.connect(config.database_path) as db:
                row = db.execute(
                    "SELECT indexed_at, post_count, media_count FROM index_metadata WHERE profile = ?",
                    (profile.name,),
                ).fetchone()
                if row:
                    index = {
                        "indexed_at": row[0],
                        "post_count": row[1],
                        "media_count": row[2],
                    }
        except sqlite3.Error as exc:
            index = {"error": str(exc)}
    dates = sorted(post["created_at"] for post in posts if post.get("created_at"))
    coverage = context_coverage({str(post["id"]): post for post in posts})
    last_context = last_batch.get("context") or {}
    coverage["last_batch"] = (
        {
            "enabled": last_context.get("enabled"),
            "pages_visited": last_context.get("pages_visited"),
            "relationships_resolved": last_context.get("relationships_resolved"),
            "relationships_missing": last_context.get("relationships_missing"),
            "stop_reason": last_context.get("stop_reason"),
            "unresolved_count": len(last_context.get("unresolved", [])),
        }
        if last_context
        else None
    )
    return {
        "profile": profile.name,
        "handle": profile.handle,
        "source_profile_status": source_profile.get("status"),
        "output_dir": str(paths.root),
        "cdp": _cdp_status(profile.cdp_url),
        "raw_batches": len(batch_manifests),
        "normalized_posts": len(posts),
        "target_posts": sum(bool(post.get("is_target_author")) for post in posts),
        "media": len(media),
        "media_downloaded": sum(
            item.get("download_status") == "downloaded" for item in media
        ),
        "media_failed": sum(item.get("download_status") == "failed" for item in media),
        "earliest_post_at": dates[0] if dates else None,
        "latest_post_at": dates[-1] if dates else None,
        "context": coverage,
        "index": index,
    }
