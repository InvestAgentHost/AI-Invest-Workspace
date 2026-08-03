from __future__ import annotations

import json
from pathlib import Path

from x.config import ProfileConfig
from x.search import index_profile, search_posts
from x.storage import SourcePaths, write_jsonl


def profile(root: Path) -> ProfileConfig:
    return ProfileConfig(
        name="Example",
        handle="Example",
        profile_url="https://x.com/Example",
        output_dir=root,
        cdp_url="http://127.0.0.1:9222",
        collect_replies=True,
        collect_quotes=True,
        download_images=False,
        max_scrolls=1,
        stalled_rounds=1,
        min_delay=0.1,
        max_delay=0.1,
    )


def post(post_id: str, text: str, target: bool, parent: str | None = None) -> dict:
    return {
        "id": post_id,
        "author_id": "u1",
        "author_handle": "Example" if target else "Other",
        "author_name": "示例",
        "created_at": "2024-01-01T00:00:00+00:00",
        "text": text,
        "post_type": "reply" if parent else "original",
        "conversation_id": parent or post_id,
        "in_reply_to_id": parent,
        "quoted_post_id": None,
        "reposted_post_id": None,
        "lang": "zh",
        "like_count": 1,
        "reply_count": 0,
        "repost_count": 0,
        "quote_count": 0,
        "view_count": 10,
        "url": f"https://x.com/i/status/{post_id}",
        "is_target_author": target,
        "source_kind": "graphql",
        "content_hash": post_id,
        "source_paths": ["raw/test.json"],
        "media_ids": ["m1"] if post_id == "100" else [],
    }


def test_search_returns_short_chinese_term_media_and_parent(tmp_path: Path) -> None:
    paths = SourcePaths.from_root(tmp_path / "source")
    paths.ensure()
    write_jsonl(
        paths.posts_jsonl,
        [
            post("90", "行业库存仍然很高", False),
            post("100", "AI 芯片库存周期正在改善", True, "90"),
        ],
    )
    write_jsonl(
        paths.media_jsonl,
        [
            {
                "media_id": "m1",
                "post_id": "100",
                "media_type": "image",
                "position": 0,
                "source_url": "https://example.test/image.jpg",
                "expanded_url": None,
                "local_path": "assets/images/100/image.jpg",
                "mime_type": "image/jpeg",
                "width": 100,
                "height": 80,
                "content_hash": "hash",
                "downloaded_at": "2024-01-01T00:01:00+00:00",
                "download_status": "downloaded",
                "error": None,
            }
        ],
    )
    database = tmp_path / "x.sqlite"
    index_profile(database, profile(paths.root))
    results = search_posts(database, "Example", query="芯片", top_k=5)
    assert [item["id"] for item in results] == ["100"]
    assert results[0]["media"][0]["local_path"].endswith("image.jpg")
    assert results[0]["context"]["parent"]["id"] == "90"


def test_search_does_not_return_context_author_as_hit(tmp_path: Path) -> None:
    paths = SourcePaths.from_root(tmp_path / "source")
    paths.ensure()
    write_jsonl(
        paths.posts_jsonl,
        [post("90", "半导体观点", False), post("100", "目标帖子", True)],
    )
    write_jsonl(paths.media_jsonl, [])
    database = tmp_path / "x.sqlite"
    index_profile(database, profile(paths.root))
    assert search_posts(database, "Example", query="半导体") == []
