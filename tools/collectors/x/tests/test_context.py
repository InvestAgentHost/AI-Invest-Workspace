from __future__ import annotations

from x.context import context_coverage, find_context_gaps


def post(
    post_id: str,
    *,
    target: bool = False,
    parent: str | None = None,
    quote: str | None = None,
) -> dict:
    return {
        "id": post_id,
        "url": f"https://x.com/i/status/{post_id}",
        "is_target_author": target,
        "in_reply_to_id": parent,
        "quoted_post_id": quote,
    }


def test_missing_direct_parent_requests_target_reply_detail() -> None:
    posts = {"100": post("100", target=True, parent="90")}
    gaps = find_context_gaps(posts, max_depth=5)
    assert len(gaps) == 1
    assert gaps[0].origin_post_id == "100"
    assert gaps[0].detail_post_id == "100"
    assert gaps[0].missing_post_id == "90"
    assert gaps[0].relation == "reply_parent"
    assert context_coverage(posts)["direct_parent_recovery_rate"] == 0.0


def test_known_parent_chain_requests_parent_detail_for_missing_ancestor() -> None:
    posts = {
        "100": post("100", target=True, parent="90"),
        "90": post("90", parent="80"),
    }
    gaps = find_context_gaps(posts, max_depth=5)
    assert len(gaps) == 1
    assert gaps[0].origin_post_id == "100"
    assert gaps[0].detail_post_id == "90"
    assert gaps[0].missing_post_id == "80"
    assert gaps[0].depth == 2
    coverage = context_coverage(posts)
    assert coverage["direct_parents_resolved"] == 1
    assert coverage["direct_parent_recovery_rate"] == 1.0


def test_quote_and_reply_are_both_reported_and_resolve_independently() -> None:
    posts = {"100": post("100", target=True, parent="90", quote="70")}
    assert {gap.relation for gap in find_context_gaps(posts, max_depth=5)} == {
        "reply_parent",
        "quote",
    }
    posts["90"] = post("90")
    coverage = context_coverage(posts)
    assert coverage["direct_parents_resolved"] == 1
    assert coverage["quoted_posts_missing"] == 1
    assert [gap.relation for gap in find_context_gaps(posts, max_depth=5)] == ["quote"]


def test_depth_limit_stops_ancestor_expansion() -> None:
    posts = {
        "100": post("100", target=True, parent="90"),
        "90": post("90", parent="80"),
        "80": post("80", parent="70"),
    }
    assert find_context_gaps(posts, max_depth=2) == []
    gaps = find_context_gaps(posts, max_depth=3)
    assert gaps[0].missing_post_id == "70"
