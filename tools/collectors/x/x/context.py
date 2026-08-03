from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ContextGap:
    origin_post_id: str
    detail_post_id: str
    missing_post_id: str
    relation: str
    depth: int
    detail_url: str


def _target_posts(posts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [post for post in posts.values() if post.get("is_target_author")]


def find_context_gaps(
    posts: dict[str, dict[str, Any]],
    max_depth: int,
    include_quotes: bool = True,
) -> list[ContextGap]:
    """Return the detail pages that can reveal missing ancestors or quotes."""
    gaps: dict[tuple[str, str], ContextGap] = {}
    for origin in _target_posts(posts):
        origin_id = str(origin["id"])
        if include_quotes:
            quoted_id = origin.get("quoted_post_id")
            if quoted_id and quoted_id not in posts:
                gap = ContextGap(
                    origin_post_id=origin_id,
                    detail_post_id=origin_id,
                    missing_post_id=str(quoted_id),
                    relation="quote",
                    depth=1,
                    detail_url=str(origin["url"]),
                )
                gaps[(gap.detail_post_id, gap.missing_post_id)] = gap

        current = origin
        visited_chain: set[str] = set()
        for depth in range(1, max_depth + 1):
            current_id = str(current["id"])
            if current_id in visited_chain:
                break
            visited_chain.add(current_id)
            parent_id = current.get("in_reply_to_id")
            if not parent_id:
                break
            parent_id = str(parent_id)
            parent = posts.get(parent_id)
            if parent:
                current = parent
                continue
            gap = ContextGap(
                origin_post_id=origin_id,
                detail_post_id=current_id,
                missing_post_id=parent_id,
                relation="reply_parent",
                depth=depth,
                detail_url=str(current["url"]),
            )
            gaps[(gap.detail_post_id, gap.missing_post_id)] = gap
            break
    return sorted(
        gaps.values(),
        key=lambda gap: (gap.relation, gap.depth, gap.origin_post_id),
    )


def context_coverage(posts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    targets = _target_posts(posts)
    replies = [post for post in targets if post.get("in_reply_to_id")]
    quotes = [post for post in targets if post.get("quoted_post_id")]
    reply_resolved = sum(str(post["in_reply_to_id"]) in posts for post in replies)
    quote_resolved = sum(str(post["quoted_post_id"]) in posts for post in quotes)

    def rate(resolved: int, total: int) -> float | None:
        return round(resolved / total, 4) if total else None

    return {
        "target_replies": len(replies),
        "direct_parents_resolved": reply_resolved,
        "direct_parents_missing": len(replies) - reply_resolved,
        "direct_parent_recovery_rate": rate(reply_resolved, len(replies)),
        "target_quotes": len(quotes),
        "quoted_posts_resolved": quote_resolved,
        "quoted_posts_missing": len(quotes) - quote_resolved,
        "quoted_post_recovery_rate": rate(quote_resolved, len(quotes)),
    }


def serialize_gaps(gaps: list[ContextGap]) -> list[dict[str, Any]]:
    return [asdict(gap) for gap in gaps]
