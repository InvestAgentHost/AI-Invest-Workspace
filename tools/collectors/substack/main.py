from __future__ import annotations

import argparse
import html
import hashlib
import json
import random
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from bs4 import BeautifulSoup
from markdownify import markdownify as html_to_markdown

from tools.shared.workspace_paths import load_data_paths


PAYWALL_MARKERS = (
    "This post is for paid subscribers",
    "Subscribe to continue reading",
    "Upgrade to paid",
)

ARTICLE_SELECTORS = (
    "article",
    "main article",
    "[data-testid='post-content']",
    "[class*='post-content']",
    "[class*='body-markup']",
)


@dataclass
class ProfileConfig:
    name: str
    base_url: str
    archive_url: str
    output_dir: str
    cdp_url: str
    max_scrolls: int
    min_delay: float
    max_delay: float


@dataclass
class PostResult:
    profile: str
    url: str
    slug: str
    title: str | None
    subtitle: str | None
    author: str | None
    published_at: str | None
    is_accessible: bool
    html_path: str
    markdown_path: str
    image_dir: str
    fetched_at: str
    text_length: int
    content_sha256: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Archive paid-accessible Substack posts from your own logged-in browser session."
    )
    parser.add_argument(
        "--config",
        default="tools/collectors/substack/config.json",
        help="Path to the Substack config file.",
    )
    parser.add_argument(
        "--profile",
        help="Profile name defined in the config file. Defaults to default_profile.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    archive_parser = subparsers.add_parser("archive", help="Fetch archive posts incrementally.")
    archive_parser.add_argument("--max-posts", type=int, default=0, help="0 means no limit.")
    archive_parser.add_argument("--overwrite", action="store_true", help="Refetch posts even if already recorded.")

    latest_parser = subparsers.add_parser("latest", help="Fetch only the latest published post.")
    latest_parser.add_argument("--overwrite", action="store_true", help="Refetch the latest post even if already recorded.")

    single_parser = subparsers.add_parser("single", help="Fetch one explicit post URL.")
    single_parser.add_argument("url", help="Full Substack article URL, for example https://example.substack.com/p/post-slug")
    single_parser.add_argument("--overwrite", action="store_true", help="Refetch the post even if already recorded.")

    subparsers.add_parser(
        "clean-local",
        help="Clean existing local HTML and Markdown outputs without refetching from Substack.",
    )

    return parser


def lazy_playwright() -> Any:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit(
            "Playwright is not installed. Activate the Workspace .venv and run: "
            "python -m pip install -r tools/collectors/substack/requirements.txt"
        ) from exc
    return sync_playwright


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def workspace_path(path: Path) -> str:
    """Serialize local paths portably when they live inside this Workspace."""

    resolved = path.resolve()
    try:
        return resolved.relative_to(WORKSPACE_ROOT).as_posix()
    except ValueError:
        return str(resolved)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sleep_between(min_delay: float, max_delay: float) -> None:
    low = min(min_delay, max_delay)
    high = max(min_delay, max_delay)
    time.sleep(random.uniform(low, high))


def wait_for_page_ready(page: Any) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        page.wait_for_load_state("load")


def load_json(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        example_path = path.with_name(path.stem + ".example" + path.suffix)
        if example_path.exists():
            import shutil
            shutil.copy(example_path, path)
            print(f"📋 已从 {example_path.name} 创建 {path.name}，请按需修改后重新运行。")
            raise SystemExit(0)
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_profile(
    config_path: Path, profile_name: str | None, workspace: Path | None = None
) -> ProfileConfig:
    config = load_json(config_path, fallback={})
    if not config:
        raise SystemExit(f"Config file not found or empty: {config_path}")

    selected = profile_name or config.get("default_profile")
    profiles = config.get("profiles", {})
    if selected not in profiles:
        raise SystemExit(f"Profile '{selected}' was not found in {config_path}")

    profile = profiles[selected]
    return ProfileConfig(
        name=selected,
        base_url=profile["base_url"],
        archive_url=profile["archive_url"],
        output_dir=str(
            load_data_paths(workspace).resolve(
                profile.get("output_dir")
                or f"sources/publishers/substack/{selected}"
            )
        ),
        cdp_url=profile.get("cdp_url", "http://127.0.0.1:9222"),
        max_scrolls=int(profile.get("max_scrolls", 80)),
        min_delay=float(profile.get("min_delay", 1.5)),
        max_delay=float(profile.get("max_delay", 3.0)),
    )


def validate_post_url(url: str, profile: ProfileConfig) -> str:
    parsed = urlparse(url)
    if not parsed.scheme.startswith("http"):
        raise ValueError(f"Invalid URL: {url}")
    profile_host = urlparse(profile.base_url).netloc.replace("www.", "")
    url_host = parsed.netloc.replace("www.", "")
    if url_host != profile_host:
        raise ValueError(f"URL host does not match profile '{profile.name}': {url}")
    if not parsed.path.startswith("/p/"):
        raise ValueError(f"URL is not a Substack post URL: {url}")
    clean = parsed._replace(query="", fragment="")
    return clean.geturl()


def slug_from_url(url: str) -> str:
    raw = urlparse(url).path.rsplit("/", 1)[-1] or "post"
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", raw).strip("-") or "post"


def output_paths(output_root: Path) -> dict[str, Path]:
    html_dir = output_root / "raw" / "html"
    markdown_dir = output_root / "normalized" / "markdown"
    images_dir = output_root / "assets" / "images"
    state_dir = output_root / "state"
    posts_dir = state_dir / "posts"
    for path in (html_dir, markdown_dir, images_dir, state_dir, posts_dir):
        ensure_dir(path)
    return {
        "html_dir": html_dir,
        "markdown_dir": markdown_dir,
        "images_dir": images_dir,
        "state_dir": state_dir,
        "posts_dir": posts_dir,
        "manifest_path": state_dir / "manifest.json",
    }


def load_manifest(manifest_path: Path, profile: ProfileConfig) -> dict[str, Any]:
    manifest = load_json(
        manifest_path,
        fallback={
            "profile": profile.name,
            "base_url": profile.base_url,
            "archive_url": profile.archive_url,
            "updated_at": None,
            "latest_url": None,
            "posts": {},
        },
    )
    manifest.setdefault("posts", {})
    manifest["profile"] = profile.name
    manifest["base_url"] = profile.base_url
    manifest["archive_url"] = profile.archive_url
    return manifest


def save_manifest(manifest_path: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = utc_now()
    save_json(manifest_path, manifest)


def collect_post_urls(page: Any, profile: ProfileConfig) -> list[str]:
    page.goto(profile.archive_url, wait_until="domcontentloaded")
    wait_for_page_ready(page)

    discovered: list[str] = []
    seen: set[str] = set()
    stalled_rounds = 0
    profile_host = urlparse(profile.base_url).netloc.replace("www.", "")

    for _ in range(profile.max_scrolls):
        hrefs = page.locator("a[href*='/p/']").evaluate_all("nodes => nodes.map(node => node.href)")
        for href in hrefs:
            try:
                normalized = validate_post_url(href, profile)
            except ValueError:
                continue
            if urlparse(normalized).netloc.replace("www.", "") == profile_host and normalized not in seen:
                seen.add(normalized)
                discovered.append(normalized)

        before_count = len(discovered)
        clicked_more = False
        for label in ("Show more", "Load more", "See all"):
            button = page.get_by_role("button", name=label)
            if button.count() > 0:
                button.first.click(timeout=2000)
                clicked_more = True
                break
        if not clicked_more:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

        sleep_between(profile.min_delay, profile.max_delay)

        hrefs = page.locator("a[href*='/p/']").evaluate_all("nodes => nodes.map(node => node.href)")
        for href in hrefs:
            try:
                normalized = validate_post_url(href, profile)
            except ValueError:
                continue
            if normalized not in seen:
                seen.add(normalized)
                discovered.append(normalized)

        if len(discovered) == before_count:
            stalled_rounds += 1
            if stalled_rounds >= 3:
                break
        else:
            stalled_rounds = 0

    return discovered


def locate_article_html(page: Any) -> str:
    for selector in ARTICLE_SELECTORS:
        locator = page.locator(selector)
        if locator.count() > 0:
            try:
                return locator.first.inner_html(timeout=2000)
            except Exception:
                continue
    return ""


def extract_post_payload(page: Any) -> dict[str, Any]:
    return page.evaluate(
        """
        () => {
          const meta = (selector) => document.querySelector(selector)?.content ?? null;
          const text = (selector) => document.querySelector(selector)?.textContent?.trim() ?? null;
          const article = document.querySelector('article')
            || document.querySelector("[data-testid='post-content']")
            || document.querySelector("[class*='post-content']")
            || document.querySelector("[class*='body-markup']")
            || document.querySelector('main');

          const articleText = (selector) => article?.querySelector(selector)?.textContent?.trim() ?? null;
          const postText = article?.innerText?.trim() ?? '';
          const publishedNode = article?.querySelector('time');
          const visiblePublishedDate = postText.match(
            /\\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\\s+\\d{1,2},\\s+\\d{4}\\b/i
          )?.[0] ?? null;

          return {
            title: articleText('h1') ?? meta("meta[property='og:title']"),
            subtitle: articleText('h3') ?? meta("meta[name='twitter:description']"),
            author: articleText("a[href*='@']") ?? text("a[href*='@']") ?? meta("meta[name='author']"),
            published_at: publishedNode?.getAttribute('datetime')
              ?? visiblePublishedDate
              ?? meta("meta[property='article:published_time']")
              ?? publishedNode?.textContent?.trim()
              ?? null,
            text: postText,
            outer_html: article?.outerHTML ?? '',
            paywalled: document.body.innerText.includes('This post is for paid subscribers')
              || document.body.innerText.includes('Subscribe to continue reading')
              || document.body.innerText.includes('Upgrade to paid'),
          };
        }
        """
    )


def wrap_html_document(title: str | None, body_html: str, source_url: str) -> str:
    safe_title = title or "Untitled"
    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\">\n"
        f"  <title>{safe_title}</title>\n"
        f"  <meta name=\"source\" content=\"{source_url}\">\n"
        "</head>\n"
        "<body>\n"
        f"{body_html}\n"
        "</body>\n"
        "</html>\n"
    )


def sanitize_frontmatter_value(value: str | None) -> str:
    if not value:
        return ""
    return value.replace("\r", " ").replace("\n", " ").replace('"', '\\"').strip()


def sanitize_link_url(url: str) -> str:
    url = html.unescape(url)
    parsed = urlparse(url)
    if not parsed.scheme.startswith("http"):
        return url

    filtered_params = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered in {"token", "action", "utm_source", "utm_medium", "utm_content", "change_user", "for_pub"}:
            continue
        filtered_params.append((key, value))

    cleaned = parsed._replace(query=urlencode(filtered_params, doseq=True), fragment="")
    return urlunparse(cleaned)


def sanitize_urls_in_text(text: str) -> str:
    url_pattern = re.compile(r"https?://[^\s\"'<>]+")

    def replace_url(match: re.Match[str]) -> str:
        return sanitize_link_url(match.group(0))

    return url_pattern.sub(replace_url, text)


def is_share_anchor(anchor: Any) -> bool:
    href = anchor.get("href") or ""
    text = anchor.get_text(" ", strip=True).lower()
    lowered_href = href.lower()
    return "token=" in lowered_href or "action=share" in lowered_href or text == "share"


def clean_article_html(article_html: str) -> str:
    if not article_html:
        return article_html

    soup = BeautifulSoup(article_html, "html.parser")

    for button in soup.find_all("button"):
        if button.get_text(" ", strip=True).lower() == "share":
            parent = button.parent
            button.decompose()
            if parent and getattr(parent, "name", None) in {"div", "span"}:
                remaining = parent.get_text(" ", strip=True)
                if not remaining:
                    parent.decompose()

    for anchor in soup.find_all("a"):
        if is_share_anchor(anchor):
            parent = anchor.parent
            anchor.decompose()
            if parent and getattr(parent, "name", None) in {"p", "div", "span"}:
                remaining = parent.get_text(" ", strip=True)
                if not remaining:
                    parent.decompose()
            continue

        href = anchor.get("href")
        if href:
            anchor["href"] = sanitize_link_url(href)

    for tag in soup.find_all(True):
        updated_attrs: dict[str, Any] = {}
        for attr_name, attr_value in tag.attrs.items():
            if isinstance(attr_value, str):
                updated_attrs[attr_name] = sanitize_urls_in_text(attr_value)
            elif isinstance(attr_value, list):
                updated_attrs[attr_name] = [
                    sanitize_urls_in_text(item) if isinstance(item, str) else item
                    for item in attr_value
                ]
            else:
                updated_attrs[attr_name] = attr_value
        tag.attrs = updated_attrs

    return str(soup)


def collapse_linked_local_images(markdown_text: str) -> str:
    pattern = re.compile(
        r"\[(?P<image>!\[[^\]]*\]\((?:\.\./images|\.\./\.\./assets/images)/[^)]+\))\]\([^)]*\)"
    )
    return pattern.sub(lambda match: match.group("image"), markdown_text)


def clean_markdown_document(markdown_text: str) -> str:
    cleaned_lines: list[str] = []
    share_line_pattern = re.compile(r"^\s*\[share\]\([^)]*token=[^)]+\)\s*$", re.IGNORECASE)
    share_inline_pattern = re.compile(r"\[share\]\([^)]*token=[^)]+\)", re.IGNORECASE)
    token_url_pattern = re.compile(r"\((https?://[^)\s]*token=[^)\s]*)\)")

    for line in markdown_text.splitlines():
        if share_line_pattern.match(line.strip()):
            continue
        line = share_inline_pattern.sub("", line)

        def replace_token_url(match: re.Match[str]) -> str:
            return f"({sanitize_link_url(match.group(1))})"

        line = token_url_pattern.sub(replace_token_url, line)
        cleaned_lines.append(line.rstrip())

    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip() + "\n"


def unwrap_image_anchors_for_markdown(article_html: str) -> str:
    if not article_html:
        return article_html

    soup = BeautifulSoup(article_html, "html.parser")
    for anchor in soup.find_all("a"):
        if anchor.find("img") is not None:
            anchor.unwrap()
    return str(soup)


def guess_extension(url: str, content_type: str | None) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix and len(suffix) <= 5:
        return suffix
    if not content_type:
        return ".bin"
    normalized = content_type.split(";", 1)[0].strip().lower()
    mapping = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "image/svg+xml": ".svg",
        "image/avif": ".avif",
    }
    return mapping.get(normalized, ".bin")


def download_binary(url: str) -> tuple[bytes, str | None]:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        },
    )
    with urlopen(request, timeout=30) as response:
        payload = response.read()
        content_type = response.headers.get("Content-Type")
    return payload, content_type


def local_image_relative_path(slug: str, file_name: str) -> str:
    return f"../../assets/images/{slug}/{file_name}"


def localize_images(article_html: str, page_url: str, slug: str, images_root: Path) -> tuple[str, list[str]]:
    if not article_html:
        return article_html, []

    soup = BeautifulSoup(article_html, "html.parser")
    post_image_dir = images_root / slug
    ensure_dir(post_image_dir)

    downloaded_paths: list[str] = []
    seen_urls: dict[str, str] = {}
    image_index = 1

    for source in soup.find_all("source"):
        source.decompose()

    for image in soup.find_all("img"):
        original_url = image.get("src") or image.get("data-src")
        if not original_url:
            continue

        absolute_url = urljoin(page_url, original_url)
        if absolute_url in seen_urls:
            local_path = seen_urls[absolute_url]
        else:
            try:
                payload, content_type = download_binary(absolute_url)
            except Exception:
                continue
            extension = guess_extension(absolute_url, content_type)
            file_name = f"image-{image_index:03d}{extension}"
            image_index += 1
            output_path = post_image_dir / file_name
            output_path.write_bytes(payload)
            local_path = local_image_relative_path(slug, file_name)
            seen_urls[absolute_url] = local_path
            downloaded_paths.append(workspace_path(output_path))

        image["src"] = local_path
        for attr in ("srcset", "data-src", "data-srcset", "loading", "decoding"):
            if attr in image.attrs:
                del image.attrs[attr]

    return str(soup), downloaded_paths


def build_markdown_document(payload: dict[str, Any], result: PostResult) -> str:
    body_html = payload.get("outer_html") or ""
    markdown_source = unwrap_image_anchors_for_markdown(body_html)
    markdown_body = html_to_markdown(markdown_source, heading_style="ATX") if markdown_source else payload.get("text") or ""
    markdown_body = collapse_linked_local_images(markdown_body)
    markdown_body = clean_markdown_document(markdown_body)
    markdown_body = markdown_body.strip()
    frontmatter = [
        "---",
        f'title: "{sanitize_frontmatter_value(result.title)}"',
        f'subtitle: "{sanitize_frontmatter_value(result.subtitle)}"',
        f'author: "{sanitize_frontmatter_value(result.author)}"',
        f'published_at: "{sanitize_frontmatter_value(result.published_at)}"',
        f'url: "{result.url}"',
        f'slug: "{result.slug}"',
        f'profile: "{result.profile}"',
        f'fetched_at: "{result.fetched_at}"',
        f"is_accessible: {str(result.is_accessible).lower()}",
        "---",
        "",
    ]
    return "\n".join(frontmatter) + markdown_body + "\n"


def build_post_record(result: PostResult) -> dict[str, Any]:
    record = asdict(result)
    record["updated_at"] = utc_now()
    return record


def clean_local_outputs(paths: dict[str, Path]) -> dict[str, int]:
    cleaned_html = 0
    cleaned_markdown = 0

    for html_file in sorted(paths["html_dir"].glob("*.html")):
        original = html_file.read_text(encoding="utf-8")
        cleaned = clean_article_html(original)
        if cleaned != original:
            html_file.write_text(cleaned, encoding="utf-8")
        cleaned_html += 1

    for markdown_file in sorted(paths["markdown_dir"].glob("*.md")):
        original = markdown_file.read_text(encoding="utf-8")
        cleaned = collapse_linked_local_images(original)
        cleaned = clean_markdown_document(cleaned)
        if cleaned != original:
            markdown_file.write_text(cleaned, encoding="utf-8")
        cleaned_markdown += 1

    return {
        "html": cleaned_html,
        "markdown": cleaned_markdown,
    }


def fetch_single_post(page: Any, profile: ProfileConfig, url: str, paths: dict[str, Path]) -> PostResult:
    page.goto(url, wait_until="domcontentloaded")
    wait_for_page_ready(page)
    sleep_between(profile.min_delay, profile.max_delay)

    payload = extract_post_payload(page)
    article_html = payload.get("outer_html") or locate_article_html(page)
    if not payload.get("outer_html") and article_html:
        payload["outer_html"] = article_html

    payload["outer_html"] = clean_article_html(payload.get("outer_html") or "")

    localized_html, downloaded_images = localize_images(
        article_html=payload.get("outer_html") or "",
        page_url=url,
        slug=slug_from_url(url),
        images_root=paths["images_dir"],
    )
    payload["outer_html"] = localized_html

    text = payload.get("text") or ""
    paywalled = bool(payload.get("paywalled"))
    accessible = bool(text) and not any(marker in text for marker in PAYWALL_MARKERS)
    if paywalled and len(text) < 1200:
        accessible = False

    slug = slug_from_url(url)
    html_path = paths["html_dir"] / f"{slug}.html"
    markdown_path = paths["markdown_dir"] / f"{slug}.md"

    result = PostResult(
        profile=profile.name,
        url=url,
        slug=slug,
        title=payload.get("title"),
        subtitle=payload.get("subtitle"),
        author=payload.get("author"),
        published_at=payload.get("published_at"),
        is_accessible=accessible,
        html_path=workspace_path(html_path),
        markdown_path=workspace_path(markdown_path),
        image_dir=workspace_path(paths["images_dir"] / slug),
        fetched_at=utc_now(),
        text_length=len(text),
        content_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )

    html_doc = wrap_html_document(result.title, payload.get("outer_html") or "", result.url)
    markdown_doc = build_markdown_document(payload, result)
    html_path.write_text(html_doc, encoding="utf-8")
    markdown_path.write_text(markdown_doc, encoding="utf-8")

    record = build_post_record(result)
    record["raw_text_path"] = workspace_path(paths["posts_dir"] / f"{slug}.txt")
    record["raw_text_length"] = len(text)
    record["paywall_marker_detected"] = paywalled
    record["downloaded_images"] = downloaded_images
    save_json(paths["posts_dir"] / f"{slug}.json", record)
    (paths["posts_dir"] / f"{slug}.txt").write_text(text, encoding="utf-8")
    return result


def select_urls(args: argparse.Namespace, page: Any, profile: ProfileConfig) -> list[str]:
    if args.command == "archive":
        urls = collect_post_urls(page, profile)
        return urls[: args.max_posts] if args.max_posts > 0 else urls
    if args.command == "latest":
        urls = collect_post_urls(page, profile)
        return urls[:1]
    if args.command == "single":
        return [validate_post_url(args.url, profile)]
    raise ValueError(f"Unsupported command: {args.command}")


def should_skip(slug: str, manifest: dict[str, Any], paths: dict[str, Path], overwrite: bool) -> bool:
    """Skip only when the manifest and local normalized Markdown agree."""

    if overwrite or slug not in manifest.get("posts", {}):
        return False
    return (paths["markdown_dir"] / f"{slug}.md").is_file()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    config_path = Path(args.config)
    profile = load_profile(config_path, args.profile)
    output_root = Path(profile.output_dir)
    paths = output_paths(output_root)
    manifest = load_manifest(paths["manifest_path"], profile)

    if args.command == "clean-local":
        cleaned_counts = clean_local_outputs(paths)
        print(
            json.dumps(
                {
                    "event": "done",
                    "profile": profile.name,
                    "command": args.command,
                    "output_dir": workspace_path(output_root),
                    "cleaned_html": cleaned_counts["html"],
                    "cleaned_markdown": cleaned_counts["markdown"],
                },
                ensure_ascii=False,
            )
        )
        return 0

    sync_playwright = lazy_playwright()
    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(profile.cdp_url)
        if not browser.contexts:
            raise SystemExit(
                "No browser contexts were found. Start Edge or Chrome with remote debugging and sign in first."
            )

        context = browser.contexts[0]
        page = context.new_page()
        urls = select_urls(args, page, profile)

        fetched = 0
        skipped = 0
        overwrite = bool(getattr(args, "overwrite", False))
        for url in urls:
            slug = slug_from_url(url)
            if should_skip(slug, manifest, paths, overwrite):
                skipped += 1
                continue

            result = fetch_single_post(page, profile, url, paths)
            manifest["posts"][slug] = asdict(result)
            manifest["latest_url"] = url if args.command in {"latest", "archive"} and not manifest.get("latest_url") else manifest.get("latest_url")
            if args.command == "archive" and fetched == 0:
                manifest["latest_url"] = url
            if args.command == "latest":
                manifest["latest_url"] = url
            save_manifest(paths["manifest_path"], manifest)
            fetched += 1
            print(
                json.dumps(
                    {
                        "event": "post_saved",
                        "profile": profile.name,
                        "slug": slug,
                        "html_path": workspace_path(paths["html_dir"] / f"{slug}.html"),
                        "markdown_path": workspace_path(paths["markdown_dir"] / f"{slug}.md"),
                        "accessible": result.is_accessible,
                        "text_length": result.text_length,
                    },
                    ensure_ascii=False,
                )
            )

        page.close()

    print(
        json.dumps(
            {
                "event": "done",
                "profile": profile.name,
                "command": args.command,
                "output_dir": workspace_path(output_root),
                "fetched": fetched,
                "skipped": skipped,
                "manifest": workspace_path(paths["manifest_path"]),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
