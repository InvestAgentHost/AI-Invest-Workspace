from __future__ import annotations

import random
import re
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any
from urllib.parse import quote, urlparse

from ..config import ProfileConfig
from ..context import context_coverage, find_context_gaps, serialize_gaps
from ..normalize import collect_normalized_posts
from ..storage import BatchArchive, SourcePaths, update_source_manifest


CAPTURE_OPERATIONS = (
    "UserTweets",
    "UserTweetsAndReplies",
    "TweetDetail",
    "TweetResultByRestId",
    "UserByScreenName",
    "SearchTimeline",
)


DOM_EXTRACT_SCRIPT = r"""
() => Array.from(document.querySelectorAll("article[data-testid='tweet']")).map(article => {
  const time = article.querySelector("time");
  const statusAnchor = time?.closest("a[href*='/status/']")
    || article.querySelector("a[href*='/status/']");
  const href = statusAnchor?.href || '';
  const match = href.match(/x\.com\/([^/]+)\/status\/(\d+)/);
  if (!match) return null;
  const id = match[2];
  const statusLinks = Array.from(article.querySelectorAll("a[href*='/status/']"))
    .map(node => node.href.match(/\/status\/(\d+)/)?.[1])
    .filter(Boolean);
  const quoteId = statusLinks.find(value => value !== id) || null;
  const textNodes = Array.from(article.querySelectorAll("[data-testid='tweetText']"));
  const text = textNodes[0]?.innerText?.trim() || '';
  const userName = article.querySelector("[data-testid='User-Name']");
  const nameParts = (userName?.innerText || '').split('\n').filter(Boolean);
  const imageUrls = Array.from(article.querySelectorAll("img[src*='pbs.twimg.com/media']"))
    .map(node => node.currentSrc || node.src)
    .filter(Boolean)
    .map(url => url.replace(/([?&])name=[^&]+/, '$1name=orig'));
  return {
    id,
    url: href.split('?')[0],
    author_handle: match[1],
    author_name: nameParts.find(value => !value.startsWith('@')) || null,
    created_at: time?.dateTime || null,
    text,
    quoted_post_id: quoteId,
    in_reply_to_id: null,
    image_urls: [...new Set(imageUrls)],
  };
}).filter(Boolean)
"""


@dataclass(frozen=True)
class CollectResult:
    batch_id: str
    status: str
    stop_reason: str
    observed_posts: int
    responses: int
    snapshots: int
    context_pages: int
    context_resolved: int
    context_missing: int
    requested_start_at: str | None
    earliest_target_post_at: str | None
    start_date_reached: bool | None
    search_windows_processed: bool | None
    errors: list[str]


def _operation_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    return path.rsplit("/", 1)[-1] if path else "graphql"


def _is_capture_url(url: str) -> bool:
    if "/graphql/" not in url:
        return False
    return any(
        operation.casefold() in url.casefold() for operation in CAPTURE_OPERATIONS
    )


def _delay(profile: ProfileConfig) -> None:
    low, high = sorted((profile.min_delay, profile.max_delay))
    time.sleep(random.uniform(low, high))


def _progress(message: str) -> None:
    print(f"[x-collector] {message}", file=sys.stderr, flush=True)


def _parse_post_date(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.astimezone()


def _new_target_dates(
    items: list[dict[str, Any]], target_handle: str, seen: set[str]
) -> list[datetime]:
    dates: list[datetime] = []
    for item in items:
        post_id = str(item.get("id") or "")
        if not post_id or post_id in seen:
            continue
        seen.add(post_id)
        handle = str(item.get("author_handle") or "").lstrip("@")
        if handle.casefold() != target_handle.casefold():
            continue
        created_at = _parse_post_date(item.get("created_at"))
        if created_at is not None:
            dates.append(created_at)
    return dates


def _update_cutoff_rounds(
    target_dates: list[datetime], start_at: datetime, current_rounds: int
) -> int:
    if not target_dates:
        return current_rounds
    return current_rounds + 1 if max(target_dates) < start_at else 0


def _wait_ready(page: Any, label: str) -> bool:
    try:
        page.wait_for_load_state("domcontentloaded", timeout=15000)
    except Exception:
        pass
    try:
        page.wait_for_selector("article[data-testid='tweet']", timeout=15000)
        return True
    except Exception:
        _progress(f"no tweet articles after 15s: {label} ({page.url})")
        return False


def _advance_timeline(page: Any, stalled: int) -> None:
    # X uses a virtualized list; a direct jump to the same bottom position can
    # stop dispatching useful scroll events. Nudge upward before retrying.
    if stalled:
        _progress(f"timeline unchanged; retrying incremental scroll (stall {stalled})")
        page.evaluate("window.scrollBy(0, -Math.min(window.innerHeight, 900))")
        page.wait_for_timeout(300)
    page.mouse.wheel(0, 1800)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")


def _blocked_reason(page: Any) -> str | None:
    url = page.url.casefold()
    if "/i/flow/login" in url or "/login" in url:
        return "login_required"
    try:
        body = page.locator("body").inner_text(timeout=2000).casefold()
    except Exception:
        return None
    markers = {
        "verify you are human": "verification_required",
        "unusual activity": "verification_required",
        "rate limit exceeded": "rate_limited",
        "something went wrong. try reloading": "x_page_error",
    }
    for marker, reason in markers.items():
        if marker in body:
            return reason
    return None


def _unavailable_reason(page: Any) -> str | None:
    try:
        body = page.locator("body").inner_text(timeout=2000).casefold()
    except Exception:
        return None
    markers = {
        "this post was deleted": "deleted",
        "this tweet was deleted": "deleted",
        "此帖已被删除": "deleted",
        "this page doesn’t exist": "unavailable",
        "this page doesn't exist": "unavailable",
        "页面不存在": "unavailable",
        "these posts are protected": "protected",
        "these tweets are protected": "protected",
        "这些帖子受到保护": "protected",
        "you’re unable to view this post": "access_denied",
        "you're unable to view this post": "access_denied",
    }
    for marker, reason in markers.items():
        if marker in body:
            return reason
    return None


def _search_is_empty(page: Any) -> bool:
    try:
        body = page.locator("body").inner_text(timeout=2000).casefold()
    except Exception:
        return False
    return any(
        marker in body
        for marker in (
            "no results for",
            "no results",
            "没有结果",
            "未找到结果",
        )
    )


def _routes(
    profile: ProfileConfig, route: str, start_at: datetime | None = None
) -> list[str]:
    base = profile.profile_url.rstrip("/")
    if route == "posts":
        return [base]
    if route == "replies":
        return [base + "/with_replies"]
    if route == "active":
        cursor = start_at.date() if start_at else date(2006, 1, 1)
        today = datetime.now(start_at.tzinfo).date() if start_at else date.today()
        routes: list[str] = []
        while cursor <= today:
            window_end = min(cursor + timedelta(days=90), today + timedelta(days=1))
            query = (
                f"from:{profile.handle} since:{cursor.isoformat()} "
                f"until:{window_end.isoformat()} "
                "-filter:replies -filter:retweets"
            )
            routes.append(
                "https://x.com/search?q="
                + quote(query, safe="")
                + "&src=typed_query&f=live"
            )
            cursor = window_end
        return routes
    return [base, base + "/with_replies"] if profile.collect_replies else [base]


def _capture_dom_snapshot(
    page: Any,
    batch: BatchArchive,
    observed: dict[str, dict[str, Any]],
    route: str,
    iteration: int,
) -> list[dict[str, Any]]:
    items = page.evaluate(DOM_EXTRACT_SCRIPT)
    if items:
        batch.save_snapshot(route, iteration, items)
    for item in items:
        observed[str(item["id"])] = item
    return items


def _hydrate_context(
    page: Any,
    profile: ProfileConfig,
    paths: SourcePaths,
    batch: BatchArchive,
    observed: dict[str, dict[str, Any]],
    max_pages: int,
) -> dict[str, Any]:
    posts = collect_normalized_posts(paths, profile.handle)
    coverage_before = context_coverage(posts)
    initial_gaps = find_context_gaps(
        posts,
        max_depth=profile.max_context_depth,
        include_quotes=profile.collect_quotes,
    )
    visited_details: set[str] = set()
    detail_failures: list[dict[str, str]] = []
    detail_failure_reasons: dict[str, str] = {}
    blocked_reason: str | None = None

    while len(visited_details) < max_pages:
        gaps = find_context_gaps(
            posts,
            max_depth=profile.max_context_depth,
            include_quotes=profile.collect_quotes,
        )
        gap = next(
            (item for item in gaps if item.detail_post_id not in visited_details),
            None,
        )
        if gap is None:
            break
        visited_details.add(gap.detail_post_id)
        _progress(
            f"context page {len(visited_details)}/{max_pages}: {gap.detail_url}"
        )
        try:
            page.goto(gap.detail_url, wait_until="domcontentloaded", timeout=30000)
            _wait_ready(page, f"context {len(visited_details)}/{max_pages}")
            blocked_reason = _blocked_reason(page)
            if blocked_reason:
                break
            unavailable = _unavailable_reason(page)
            if unavailable:
                detail_failure_reasons[gap.detail_post_id] = unavailable
            _capture_dom_snapshot(
                page,
                batch,
                observed,
                route=f"context:{gap.detail_url}",
                iteration=len(visited_details),
            )
            page.wait_for_timeout(1000)
            _delay(profile)
        except Exception as exc:
            detail_failure_reasons[gap.detail_post_id] = "detail_request_failed"
            detail_failures.append(
                {
                    "post_id": gap.detail_post_id,
                    "missing_post_id": gap.missing_post_id,
                    "error": f"{type(exc).__name__}: {exc}"[:500],
                }
            )
        posts = collect_normalized_posts(paths, profile.handle)

    coverage_after = context_coverage(posts)
    remaining = find_context_gaps(
        posts,
        max_depth=profile.max_context_depth,
        include_quotes=profile.collect_quotes,
    )
    initial_missing_ids = {gap.missing_post_id for gap in initial_gaps}
    unresolved = []
    for gap in remaining:
        item = serialize_gaps([gap])[0]
        item["reason"] = (
            detail_failure_reasons.get(gap.detail_post_id)
            or "detail_requested_but_not_returned"
            if gap.detail_post_id in visited_details
            else (
                "context_page_limit_reached"
                if len(visited_details) >= max_pages
                else "no_actionable_detail_page"
            )
        )
        unresolved.append(item)
    return {
        "enabled": True,
        "max_depth": profile.max_context_depth,
        "max_pages": max_pages,
        "pages_visited": len(visited_details),
        "relationships_resolved": sum(
            post_id in posts for post_id in initial_missing_ids
        ),
        "relationships_missing": len(remaining),
        "coverage_before": coverage_before,
        "coverage_after": coverage_after,
        "unresolved": unresolved,
        "detail_failures": detail_failures,
        "stop_reason": blocked_reason
        or (
            "max_context_pages_reached"
            if len(visited_details) >= max_pages and remaining
            else "completed"
        ),
    }


def collect_browser(
    profile: ProfileConfig,
    route: str = "both",
    max_scrolls: int | None = None,
    hydrate_context: bool | None = None,
    max_context_pages: int | None = None,
    start_at: datetime | None = None,
) -> CollectResult:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is not installed; install requirements.txt"
        ) from exc

    paths = SourcePaths.from_root(profile.output_dir)
    batch = BatchArchive(paths, profile.name, "collect")
    observed: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    stop_reason = "completed_routes"
    status = "completed"
    limit = max_scrolls or profile.max_scrolls
    should_hydrate = (
        profile.hydrate_context if hydrate_context is None else hydrate_context
    )
    context_page_limit = max(1, int(max_context_pages or profile.max_context_pages))
    requested_start_at = start_at.isoformat() if start_at else None
    route_cutoffs: list[bool] = []
    active_windows_processed: list[bool] = []
    context_result: dict[str, Any] = {
        "enabled": should_hydrate,
        "pages_visited": 0,
        "relationships_resolved": 0,
        "relationships_missing": 0,
        "stop_reason": "disabled" if not should_hydrate else "not_started",
    }

    try:
        _progress(
            f"starting profile={profile.name} route={route} scrolls={limit} "
            f"hydrate_context={should_hydrate} start_at={requested_start_at or 'none'}"
        )
        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(profile.cdp_url)
            if not browser.contexts:
                raise RuntimeError("No browser context found at the CDP endpoint")
            context = browser.contexts[0]
            page = context.new_page()

            def capture(response: Any) -> None:
                if not _is_capture_url(response.url):
                    return
                try:
                    if response.status != 200:
                        return
                    payload = response.json()
                    batch.save_response(
                        _operation_from_url(response.url), response.url, payload
                    )
                except Exception as exc:
                    errors.append(
                        f"response_capture: {type(exc).__name__}: {exc}"[:500]
                    )

            page.on("response", capture)
            targets = _routes(profile, route, start_at)
            for route_number, target in enumerate(targets, 1):
                _progress(f"loading route {route_number}/{len(targets)}: {target}")
                page.goto(target, wait_until="domcontentloaded", timeout=30000)
                ready = _wait_ready(page, f"route {route_number}/{len(targets)}")
                blocked = _blocked_reason(page)
                if blocked:
                    stop_reason = blocked
                    status = "stopped"
                    break
                if not ready and route == "active":
                    _progress(
                        f"route {route_number}/{len(targets)} did not render; "
                        "refreshing the search window once"
                    )
                    page.reload(wait_until="domcontentloaded", timeout=30000)
                    ready = _wait_ready(
                        page, f"route {route_number}/{len(targets)} retry"
                    )
                    blocked = _blocked_reason(page)
                    if blocked:
                        stop_reason = blocked
                        status = "stopped"
                        break
                if not ready:
                    if route == "active":
                        _progress(
                            f"route {route_number}/{len(targets)} has no rendered "
                            "search results after retry; continuing to the next window"
                        )
                        if start_at:
                            active_windows_processed.append(True)
                        continue
                    stop_reason = _unavailable_reason(page) or "timeline_not_ready"
                    status = "stopped"
                    break
                stalled = 0
                before_cutoff_rounds = 0
                route_seen: set[str] = set()
                route_cutoff_reached = False
                previous_height = -1
                previous_count = len(observed)
                for iteration in range(limit):
                    items = _capture_dom_snapshot(
                        page, batch, observed, target, iteration
                    )
                    target_dates = _new_target_dates(
                        items, profile.handle, route_seen
                    )
                    _progress(
                        f"route {route_number}/{len(targets)} scroll "
                        f"{iteration + 1}/{limit}: {len(observed)} posts observed"
                    )
                    if start_at and target_dates:
                        before_cutoff_rounds = _update_cutoff_rounds(
                            target_dates, start_at, before_cutoff_rounds
                        )
                        oldest = min(target_dates).isoformat()
                        _progress(
                            f"route {route_number}/{len(targets)} oldest new target "
                            f"post={oldest}; cutoff rounds={before_cutoff_rounds}/2"
                        )
                        if before_cutoff_rounds >= 2:
                            route_cutoff_reached = True
                            stop_reason = "start_date_reached"
                            break
                    height = int(page.evaluate("document.body.scrollHeight"))
                    if height == previous_height and len(observed) == previous_count:
                        stalled += 1
                    else:
                        stalled = 0
                    if stalled >= profile.stalled_rounds:
                        stop_reason = "timeline_stalled"
                        break
                    previous_height = height
                    previous_count = len(observed)
                    _advance_timeline(page, stalled)
                    _delay(profile)
                    blocked = _blocked_reason(page)
                    if blocked:
                        stop_reason = blocked
                        status = "stopped"
                        break
                else:
                    stop_reason = "max_scrolls_reached"
                if route == "active" and status != "stopped":
                    active_windows_processed.append(True)
                elif start_at:
                    route_cutoffs.append(route_cutoff_reached)
                if status == "stopped":
                    break
            if status == "completed" and should_hydrate:
                _progress(f"hydrating context (up to {context_page_limit} pages)")
                context_result = _hydrate_context(
                    page,
                    profile,
                    paths,
                    batch,
                    observed,
                    max_pages=context_page_limit,
                )
                if context_result.get("stop_reason") in {
                    "login_required",
                    "verification_required",
                    "rate_limited",
                    "x_page_error",
                }:
                    status = "stopped"
                    stop_reason = str(context_result["stop_reason"])
            try:
                page.wait_for_timeout(1000)
            except Exception:
                pass
            page.close()
    except KeyboardInterrupt:
        status = "stopped"
        stop_reason = "interrupted"
        errors.append("KeyboardInterrupt: collection interrupted by user")
        _progress("interrupted; finalizing batch manifest")
    except Exception as exc:
        status = "failed"
        stop_reason = "collector_error"
        errors.append(f"{type(exc).__name__}: {exc}"[:500])

    dates = sorted(
        item["created_at"] for item in observed.values() if item.get("created_at")
    )
    target_dates = sorted(
        item["created_at"]
        for item in observed.values()
        if item.get("created_at")
        and str(item.get("author_handle") or "").lstrip("@").casefold()
        == profile.handle.casefold()
    )
    search_windows_processed = (
        len(active_windows_processed) == len(_routes(profile, route, start_at))
        and all(active_windows_processed)
        if route == "active"
        else None
    )
    start_date_reached = (
        len(route_cutoffs) == len(_routes(profile, route, start_at))
        and all(route_cutoffs)
        if start_at and route != "active"
        else None
    )
    if start_date_reached and status == "completed":
        stop_reason = "start_date_reached"
    batch.manifest["observed_post_ids"] = sorted(observed)
    batch.manifest["earliest_post_at"] = dates[0] if dates else None
    batch.manifest["latest_post_at"] = dates[-1] if dates else None
    batch.manifest["requested_start_at"] = requested_start_at
    batch.manifest["earliest_target_post_at"] = target_dates[0] if target_dates else None
    batch.manifest["start_date_reached"] = start_date_reached
    batch.manifest["search_windows_processed"] = search_windows_processed
    batch.manifest["context"] = context_result
    batch.finish(status, stop_reason, errors)
    update_source_manifest(paths, batch.manifest)
    _progress(
        f"finished status={status} reason={stop_reason} posts={len(observed)}"
    )
    return CollectResult(
        batch_id=batch.batch_id,
        status=status,
        stop_reason=stop_reason,
        observed_posts=len(observed),
        responses=len(batch.manifest["response_files"]),
        snapshots=len(batch.manifest["snapshot_files"]),
        context_pages=int(context_result.get("pages_visited", 0)),
        context_resolved=int(context_result.get("relationships_resolved", 0)),
        context_missing=int(context_result.get("relationships_missing", 0)),
        requested_start_at=requested_start_at,
        earliest_target_post_at=target_dates[0] if target_dates else None,
        start_date_reached=start_date_reached,
        search_windows_processed=search_windows_processed,
        errors=errors,
    )
