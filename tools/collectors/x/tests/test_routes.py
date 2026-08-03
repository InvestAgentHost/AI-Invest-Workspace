from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from x.collectors.browser import _routes
from x.config import ProfileConfig


def test_active_route_uses_search_filters_for_proactive_posts(tmp_path) -> None:
    profile = ProfileConfig(
        name="Example",
        handle="Example",
        profile_url="https://x.com/Example",
        output_dir=tmp_path,
        cdp_url="http://127.0.0.1:9222",
        collect_replies=True,
        collect_quotes=True,
        download_images=False,
        max_scrolls=1,
        stalled_rounds=1,
        min_delay=0.1,
        max_delay=0.1,
    )
    urls = _routes(
        profile,
        "active",
        datetime(2024, 1, 1, tzinfo=ZoneInfo("Asia/Hong_Kong")),
    )
    url = urls[0]
    assert "from%3AExample" in url
    assert "since%3A2024-01-01" in url
    assert "until%3A2024-03-31" in url
    assert "-filter%3Areplies" in url
    assert "-filter%3Aretweets" in url
    assert len(urls) > 1
