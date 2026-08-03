from __future__ import annotations

import hashlib
import json
import mimetypes
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .config import ProfileConfig
from .storage import SourcePaths, read_jsonl, utc_now, write_jsonl


def _walk(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _unwrap_result(value: Any) -> dict[str, Any] | None:
    seen: set[int] = set()
    current = value
    while isinstance(current, dict) and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current.get("legacy"), dict) and (
            current["legacy"].get("full_text") is not None
            or current["legacy"].get("id_str") is not None
        ):
            return current
        for key in ("tweet", "result"):
            if isinstance(current.get(key), dict):
                current = current[key]
                break
        else:
            results = current.get("tweet_results")
            if isinstance(results, dict) and isinstance(results.get("result"), dict):
                current = results["result"]
            else:
                return None
    return None


def _tweet_candidates(payload: Any) -> Iterator[dict[str, Any]]:
    yielded: set[str] = set()
    for node in _walk(payload):
        result = _unwrap_result(node)
        if not result:
            continue
        legacy = result.get("legacy", {})
        post_id = str(result.get("rest_id") or legacy.get("id_str") or "")
        if post_id and post_id not in yielded and legacy.get("full_text") is not None:
            yielded.add(post_id)
            yield result


def _nested_result_id(value: Any) -> str | None:
    result = _unwrap_result(value)
    if not result:
        return None
    return (
        str(result.get("rest_id") or result.get("legacy", {}).get("id_str") or "")
        or None
    )


def _iso_date(value: Any) -> str | None:
    if not value:
        return None
    raw = str(value)
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return raw
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _user_from_result(
    result: dict[str, Any]
) -> tuple[str | None, str | None, str | None]:
    user_result = (
        result.get("core", {}).get("user_results", {}).get("result", {})
        if isinstance(result.get("core"), dict)
        else {}
    )
    user_legacy = user_result.get("legacy", {}) if isinstance(user_result, dict) else {}
    user_core = user_result.get("core", {}) if isinstance(user_result, dict) else {}
    return (
        str(user_result.get("rest_id") or "") or None,
        user_core.get("screen_name")
        or user_legacy.get("screen_name")
        or result.get("author_handle"),
        user_core.get("name") or user_legacy.get("name") or result.get("author_name"),
    )


def _media_from_legacy(legacy: dict[str, Any], post_id: str) -> list[dict[str, Any]]:
    media_items = (
        legacy.get("extended_entities", {}).get("media")
        or legacy.get("entities", {}).get("media")
        or []
    )
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for position, item in enumerate(media_items):
        if not isinstance(item, dict):
            continue
        source_url = item.get("media_url_https") or item.get("media_url")
        if source_url and item.get("type") == "photo" and "name=" not in source_url:
            separator = "&" if "?" in source_url else "?"
            source_url = f"{source_url}{separator}name=orig"
        media_id = str(item.get("media_key") or item.get("id_str") or source_url or "")
        if not media_id or media_id in seen:
            continue
        seen.add(media_id)
        size = item.get("original_info") or item.get("sizes", {}).get("large", {})
        rows.append(
            {
                "media_id": media_id,
                "post_id": post_id,
                "media_type": {"photo": "image", "animated_gif": "gif"}.get(
                    item.get("type"), item.get("type") or "image"
                ),
                "position": position,
                "source_url": source_url,
                "expanded_url": item.get("expanded_url"),
                "local_path": None,
                "mime_type": None,
                "width": size.get("width") or size.get("w"),
                "height": size.get("height") or size.get("h"),
                "content_hash": None,
                "downloaded_at": None,
                "download_status": "pending" if source_url else "missing_url",
                "error": None,
            }
        )
    return rows


def post_from_graphql(
    result: dict[str, Any], target_handle: str
) -> dict[str, Any] | None:
    legacy = result.get("legacy", {})
    post_id = str(result.get("rest_id") or legacy.get("id_str") or "")
    if not post_id:
        return None
    author_id, author_handle, author_name = _user_from_result(result)
    note_text = (
        result.get("note_tweet", {})
        .get("note_tweet_results", {})
        .get("result", {})
        .get("text")
    )
    reply_id = legacy.get("in_reply_to_status_id_str")
    quoted_id = _nested_result_id(result.get("quoted_status_result")) or (
        str(legacy["quoted_status_id_str"])
        if legacy.get("quoted_status_id_str")
        else None
    )
    reposted_id = _nested_result_id(legacy.get("retweeted_status_result"))
    if reposted_id:
        post_type = "repost"
    elif reply_id:
        post_type = "reply"
    elif quoted_id or legacy.get("is_quote_status"):
        post_type = "quote"
    else:
        post_type = "original"
    handle = str(author_handle or "")
    return {
        "id": post_id,
        "author_id": author_id or legacy.get("user_id_str"),
        "author_handle": handle or None,
        "author_name": author_name,
        "created_at": _iso_date(legacy.get("created_at")),
        "text": note_text or legacy.get("full_text") or "",
        "post_type": post_type,
        "conversation_id": str(legacy.get("conversation_id_str") or post_id),
        "in_reply_to_id": str(reply_id) if reply_id else None,
        "quoted_post_id": quoted_id,
        "reposted_post_id": reposted_id,
        "lang": legacy.get("lang"),
        "like_count": legacy.get("favorite_count"),
        "reply_count": legacy.get("reply_count"),
        "repost_count": legacy.get("retweet_count"),
        "quote_count": legacy.get("quote_count"),
        "view_count": result.get("views", {}).get("count"),
        "url": f"https://x.com/{handle or 'i'}/status/{post_id}",
        "is_target_author": handle.casefold() == target_handle.casefold(),
        "source_kind": "graphql",
        "source_paths": [],
        "content_hash": hashlib.sha256(
            (note_text or legacy.get("full_text") or "").encode("utf-8")
        ).hexdigest(),
        "media": _media_from_legacy(legacy, post_id),
    }


def post_from_dom(item: dict[str, Any], target_handle: str) -> dict[str, Any] | None:
    post_id = str(item.get("id") or "")
    if not post_id:
        return None
    handle = str(item.get("author_handle") or "").lstrip("@")
    text = str(item.get("text") or "")
    quoted_id = str(item.get("quoted_post_id") or "") or None
    reply_id = str(item.get("in_reply_to_id") or "") or None
    media = []
    for position, url in enumerate(dict.fromkeys(item.get("image_urls") or [])):
        media.append(
            {
                "media_id": hashlib.sha256(url.encode("utf-8")).hexdigest()[:24],
                "post_id": post_id,
                "media_type": "image",
                "position": position,
                "source_url": url,
                "expanded_url": None,
                "local_path": None,
                "mime_type": None,
                "width": None,
                "height": None,
                "content_hash": None,
                "downloaded_at": None,
                "download_status": "pending",
                "error": None,
            }
        )
    return {
        "id": post_id,
        "author_id": None,
        "author_handle": handle or None,
        "author_name": item.get("author_name"),
        "created_at": _iso_date(item.get("created_at")),
        "text": text,
        "post_type": "reply" if reply_id else "quote" if quoted_id else "original",
        "conversation_id": post_id,
        "in_reply_to_id": reply_id,
        "quoted_post_id": quoted_id,
        "reposted_post_id": None,
        "lang": None,
        "like_count": None,
        "reply_count": None,
        "repost_count": None,
        "quote_count": None,
        "view_count": None,
        "url": item.get("url") or f"https://x.com/{handle or 'i'}/status/{post_id}",
        "is_target_author": handle.casefold() == target_handle.casefold(),
        "source_kind": "dom",
        "source_paths": [],
        "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "media": media,
    }


def _merge_media(
    existing: list[dict[str, Any]], incoming: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for item in existing + incoming:
        key = (
            str(item.get("post_id")),
            str(item.get("media_id") or item.get("source_url")),
        )
        if key in rows:
            rows[key] = {
                **item,
                **{k: v for k, v in rows[key].items() if v not in (None, "")},
            }
        else:
            rows[key] = item
    return sorted(rows.values(), key=lambda row: int(row.get("position") or 0))


def merge_post(
    existing: dict[str, Any] | None, incoming: dict[str, Any], source_path: str
) -> dict[str, Any]:
    incoming = dict(incoming)
    incoming["source_paths"] = [source_path]
    if not existing:
        return incoming
    prefer_incoming = (
        incoming.get("source_kind") == "graphql"
        and existing.get("source_kind") != "graphql"
    )
    primary, secondary = (
        (incoming, existing) if prefer_incoming else (existing, incoming)
    )
    merged = dict(primary)
    for key, value in secondary.items():
        if key not in {"media", "source_paths"} and merged.get(key) in (None, "", []):
            merged[key] = value
    merged["source_paths"] = sorted(
        set(existing.get("source_paths", []) + [source_path])
    )
    merged["is_target_author"] = bool(
        existing.get("is_target_author") or incoming.get("is_target_author")
    )
    if merged.get("author_handle") and "/i/status/" in str(merged.get("url")):
        merged["url"] = f"https://x.com/{merged['author_handle']}/status/{merged['id']}"
    merged["media"] = _merge_media(existing.get("media", []), incoming.get("media", []))
    return merged


def collect_normalized_posts(
    paths: SourcePaths, target_handle: str
) -> dict[str, dict[str, Any]]:
    posts: dict[str, dict[str, Any]] = {}
    for path in sorted(paths.raw_batches.glob("*/responses/*.json")):
        wrapper = json.loads(path.read_text(encoding="utf-8"))
        for result in _tweet_candidates(wrapper.get("data")):
            post = post_from_graphql(result, target_handle)
            if post:
                posts[post["id"]] = merge_post(
                    posts.get(post["id"]), post, path.relative_to(paths.root).as_posix()
                )
    for path in sorted(paths.raw_batches.glob("*/snapshots/*.json")):
        wrapper = json.loads(path.read_text(encoding="utf-8"))
        for item in wrapper.get("posts", []):
            post = post_from_dom(item, target_handle)
            if post:
                posts[post["id"]] = merge_post(
                    posts.get(post["id"]), post, path.relative_to(paths.root).as_posix()
                )
    return posts


def _extension(url: str, content_type: str | None) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}:
        return suffix
    guessed = mimetypes.guess_extension((content_type or "").split(";", 1)[0].strip())
    return guessed or ".bin"


def download_media(media: dict[str, Any], paths: SourcePaths) -> dict[str, Any]:
    row = dict(media)
    url = row.get("source_url")
    if not url or row.get("media_type") != "image":
        return row
    try:
        request = Request(
            url, headers={"User-Agent": "Mozilla/5.0", "Accept": "image/*"}
        )
        with urlopen(request, timeout=30) as response:
            payload = response.read()
            content_type = response.headers.get("Content-Type")
        digest = hashlib.sha256(payload).hexdigest()
        file_name = f"{int(row.get('position') or 0):02d}-{digest[:16]}{_extension(url, content_type)}"
        output = paths.images / str(row["post_id"]) / file_name
        output.parent.mkdir(parents=True, exist_ok=True)
        if not output.exists():
            output.write_bytes(payload)
        row.update(
            {
                "local_path": output.relative_to(paths.root).as_posix(),
                "mime_type": (content_type or "").split(";", 1)[0] or None,
                "content_hash": digest,
                "downloaded_at": utc_now(),
                "download_status": "downloaded",
                "error": None,
            }
        )
    except Exception as exc:
        row["download_status"] = "failed"
        row["error"] = f"{type(exc).__name__}: {exc}"[:500]
    return row


def build_conversations(posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for post in posts:
        grouped.setdefault(str(post.get("conversation_id") or post["id"]), []).append(
            post
        )
    rows = []
    for conversation_id, members in grouped.items():
        dates = sorted(
            value for value in (item.get("created_at") for item in members) if value
        )
        participants = sorted(
            {item.get("author_handle") for item in members if item.get("author_handle")}
        )
        ids = [
            item["id"]
            for item in sorted(members, key=lambda item: item.get("created_at") or "")
        ]
        rows.append(
            {
                "conversation_id": conversation_id,
                "root_post_id": conversation_id,
                "post_ids": ids,
                "participants": participants,
                "created_at": dates[0] if dates else None,
                "updated_at": dates[-1] if dates else None,
            }
        )
    return sorted(rows, key=lambda row: row["conversation_id"])


def normalize_profile(
    profile: ProfileConfig, download_images: bool | None = None
) -> dict[str, Any]:
    paths = SourcePaths.from_root(profile.output_dir)
    paths.ensure()
    posts_by_id = collect_normalized_posts(paths, profile.handle)
    previous_media = {
        (str(row.get("post_id")), str(row.get("media_id"))): row
        for row in read_jsonl(paths.media_jsonl)
    }
    should_download = (
        profile.download_images if download_images is None else download_images
    )
    media_rows: list[dict[str, Any]] = []
    posts = sorted(
        posts_by_id.values(),
        key=lambda item: (item.get("created_at") or "", item["id"]),
    )
    for post in posts:
        resolved = []
        for media in post.pop("media", []):
            old = previous_media.get(
                (str(media.get("post_id")), str(media.get("media_id")))
            )
            if (
                old
                and old.get("download_status") == "downloaded"
                and old.get("local_path")
            ):
                row = {**media, **old}
            elif should_download:
                row = download_media(media, paths)
            else:
                row = media
            resolved.append(row)
            media_rows.append(row)
        post["media_ids"] = [row["media_id"] for row in resolved]
    conversations = build_conversations(posts)
    write_jsonl(paths.posts_jsonl, posts)
    write_jsonl(paths.media_jsonl, media_rows)
    write_jsonl(paths.conversations_jsonl, conversations)
    target_posts = [post for post in posts if post.get("is_target_author")]
    target_posts_by_type = {
        post_type: sum(post.get("post_type") == post_type for post in target_posts)
        for post_type in ("original", "quote", "reply", "repost")
    }
    active_posts = [
        post
        for post in target_posts
        if post.get("post_type") in {"original", "quote"}
    ]
    active_dates = sorted(
        str(post["created_at"])
        for post in active_posts
        if post.get("created_at")
    )
    return {
        "profile": profile.name,
        "posts": len(posts),
        "target_posts": len(target_posts),
        "target_posts_by_type": target_posts_by_type,
        "target_active_posts": len(active_posts),
        "earliest_target_active_post_at": active_dates[0] if active_dates else None,
        "latest_target_active_post_at": active_dates[-1] if active_dates else None,
        "media": len(media_rows),
        "media_downloaded": sum(
            row.get("download_status") == "downloaded" for row in media_rows
        ),
        "media_failed": sum(
            row.get("download_status") == "failed" for row in media_rows
        ),
        "conversations": len(conversations),
        "output": str(paths.normalized),
    }
