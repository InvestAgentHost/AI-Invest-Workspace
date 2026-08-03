from __future__ import annotations

import json
from pathlib import Path

from x.config import ProfileConfig
from x.normalize import normalize_profile, post_from_graphql
from x.storage import SourcePaths, read_jsonl


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
        max_scrolls=2,
        stalled_rounds=1,
        min_delay=0.1,
        max_delay=0.1,
    )


def tweet_result(post_id: str = "100", handle: str = "Example") -> dict:
    return {
        "__typename": "Tweet",
        "rest_id": post_id,
        "core": {
            "user_results": {
                "result": {
                    "rest_id": "u1",
                    "core": {"screen_name": handle, "name": "示例博主"},
                    "legacy": {"screen_name": handle, "name": "示例博主"},
                }
            }
        },
        "legacy": {
            "id_str": post_id,
            "full_text": "AI 芯片库存周期正在改善",
            "created_at": "Mon Jan 01 10:00:00 +0000 2024",
            "conversation_id_str": "90",
            "in_reply_to_status_id_str": "90",
            "lang": "zh",
            "favorite_count": 3,
            "reply_count": 1,
            "retweet_count": 2,
            "extended_entities": {
                "media": [
                    {
                        "id_str": "m1",
                        "type": "photo",
                        "media_url_https": "https://pbs.twimg.com/media/example.jpg",
                        "original_info": {"width": 1200, "height": 800},
                    }
                ]
            },
        },
    }


def test_graphql_post_keeps_relationships_and_media() -> None:
    post = post_from_graphql(tweet_result(), "Example")
    assert post is not None
    assert post["post_type"] == "reply"
    assert post["in_reply_to_id"] == "90"
    assert post["is_target_author"] is True
    assert post["created_at"] == "2024-01-01T10:00:00+00:00"
    assert post["media"][0]["position"] == 0
    assert post["media"][0]["source_url"].endswith("example.jpg?name=orig")


def test_graphql_quote_id_survives_without_embedded_quote() -> None:
    result = tweet_result()
    result["legacy"]["in_reply_to_status_id_str"] = None
    result["legacy"]["is_quote_status"] = True
    result["legacy"]["quoted_status_id_str"] = "70"
    post = post_from_graphql(result, "Example")
    assert post is not None
    assert post["post_type"] == "quote"
    assert post["quoted_post_id"] == "70"


def test_normalize_merges_graphql_and_dom(tmp_path: Path) -> None:
    paths = SourcePaths.from_root(tmp_path)
    response_dir = paths.raw_batches / "batch" / "responses"
    snapshot_dir = paths.raw_batches / "batch" / "snapshots"
    response_dir.mkdir(parents=True)
    snapshot_dir.mkdir(parents=True)
    (response_dir / "response.json").write_text(
        json.dumps({"data": {"entry": {"tweet_results": {"result": tweet_result()}}}}),
        encoding="utf-8",
    )
    (snapshot_dir / "snapshot.json").write_text(
        json.dumps(
            {
                "posts": [
                    {
                        "id": "100",
                        "url": "https://x.com/Example/status/100",
                        "author_handle": "Example",
                        "created_at": "2024-01-01T10:00:00Z",
                        "text": "页面短文本",
                        "image_urls": [],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    result = normalize_profile(profile(tmp_path), download_images=False)
    posts = read_jsonl(paths.posts_jsonl)
    media = read_jsonl(paths.media_jsonl)
    assert result["posts"] == 1
    assert posts[0]["text"] == "AI 芯片库存周期正在改善"
    assert posts[0]["source_kind"] == "graphql"
    assert posts[0]["is_target_author"] is True
    assert len(posts[0]["source_paths"]) == 2
    assert media[0]["post_id"] == "100"
    assert media[0]["download_status"] == "pending"


def test_new_user_core_schema_identifies_target_author() -> None:
    result = tweet_result()
    result["core"]["user_results"]["result"].pop("legacy")
    post = post_from_graphql(result, "Example")
    assert post is not None
    assert post["author_handle"] == "Example"
    assert post["author_name"] == "示例博主"
    assert post["is_target_author"] is True
