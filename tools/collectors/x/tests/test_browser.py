from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from x.collectors.browser import _new_target_dates, _update_cutoff_rounds


def test_new_target_dates_ignores_other_authors_and_seen_posts() -> None:
    seen = {"1"}
    dates = _new_target_dates(
        [
            {
                "id": "1",
                "author_handle": "Example",
                "created_at": "2025-01-01T00:00:00Z",
            },
            {
                "id": "2",
                "author_handle": "Other",
                "created_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "3",
                "author_handle": "@example",
                "created_at": "2024-06-01T00:00:00Z",
            },
        ],
        "Example",
        seen,
    )
    assert [value.isoformat() for value in dates] == ["2024-06-01T00:00:00+00:00"]
    assert seen == {"1", "2", "3"}


def test_cutoff_requires_two_rounds_wholly_before_boundary() -> None:
    cutoff = datetime(2024, 1, 1, tzinfo=ZoneInfo("Asia/Hong_Kong"))
    before = datetime(2023, 12, 1, tzinfo=ZoneInfo("Asia/Hong_Kong"))
    after = datetime(2025, 1, 1, tzinfo=ZoneInfo("Asia/Hong_Kong"))

    rounds = _update_cutoff_rounds([before, after], cutoff, 0)
    assert rounds == 0
    rounds = _update_cutoff_rounds([before], cutoff, rounds)
    assert rounds == 1
    rounds = _update_cutoff_rounds([before], cutoff, rounds)
    assert rounds == 2
