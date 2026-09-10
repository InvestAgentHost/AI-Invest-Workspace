"""Dependency-light URL/HTTP helpers: normalization, domain whitelist,
sitemap/link extraction, and a single polite GET with a redirect-domain guard.

Rewritten against the standard library only (`urllib.request`, no `httpx`):
the only third-party dependencies this skill has are PyMuPDF (PDF text
extraction) and PyYAML (topic-draft frontmatter parsing) — see
references/fetch-contract.md.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from html.parser import HTMLParser
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

DEFAULT_USER_AGENT = "CompanyWebsiteIntelligence/1.0"
_TRACKING_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid"}
_SKIP_SCHEMES = {"mailto", "tel", "javascript", "data"}


class FetchError(RuntimeError):
    """Raised when a URL (or a redirect target) leaves the domain whitelist,
    or the response exceeds the byte cap."""


@dataclass(frozen=True)
class FetchedPage:
    requested_url: str
    final_url: str
    status_code: int
    content_type: str
    content: bytes


def normalize_domain(value: str) -> str:
    return value.strip().rstrip(".").lower().encode("idna").decode("ascii")


def normalize_url(value: str, *, base_url: str | None = None) -> str:
    raw = value.strip()
    if base_url:
        raw = urljoin(base_url, raw)
    parsed = urlsplit(raw)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"URL must be absolute HTTP(S): {value!r}")
    host = parsed.hostname.encode("idna").decode("ascii").lower()
    port = parsed.port
    netloc = host
    if port and not ((parsed.scheme.lower() == "http" and port == 80) or (parsed.scheme.lower() == "https" and port == 443)):
        netloc = f"{host}:{port}"
    query = [
        (key, item)
        for key, item in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.casefold().startswith("utm_") and key.casefold() not in _TRACKING_KEYS
    ]
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    return urlunsplit((parsed.scheme.lower(), netloc, path, urlencode(query, doseq=True), ""))


def is_approved_url(url: str, domains: list[str]) -> bool:
    try:
        host = (urlsplit(url).hostname or "").lower().encode("idna").decode("ascii")
    except (UnicodeError, ValueError):
        return False
    return any(host == domain or host.endswith(f".{domain}") for domain in domains)


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag.lower() == "a" and values.get("href"):
            self.links.append(values["href"] or "")


def extract_approved_links(html: str, base_url: str, domains: list[str]) -> list[str]:
    parser = _LinkParser()
    parser.feed(html)
    links: list[str] = []
    for value in parser.links:
        if value.split(":", 1)[0].casefold() in _SKIP_SCHEMES:
            continue
        try:
            normalized = normalize_url(value, base_url=base_url)
        except ValueError:
            continue
        if is_approved_url(normalized, domains) and normalized not in links:
            links.append(normalized)
    return links


def sitemap_urls(xml: str, base_url: str, domains: list[str]) -> list[str]:
    values = re.findall(r"<loc\b[^>]*>\s*(.*?)\s*</loc>", xml, flags=re.IGNORECASE | re.DOTALL)
    links: list[str] = []
    for value in values:
        try:
            normalized = normalize_url(value, base_url=base_url)
        except ValueError:
            continue
        if is_approved_url(normalized, domains) and normalized not in links:
            links.append(normalized)
    return links


def is_sitemap_index(xml: str) -> bool:
    return bool(re.search(r"<sitemapindex\b", xml, re.IGNORECASE))


def extract_title(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _domain_guarded_opener(domains: list[str]):
    class _Guard(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001, D102
            if not is_approved_url(newurl, domains):
                raise FetchError(f"redirect left approved domains: {newurl}")
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    return build_opener(_Guard)


def fetch(
    url: str,
    *,
    approved_domains: list[str],
    max_bytes: int = 5_000_000,
    timeout_seconds: float = 30,
    retries: int = 2,
    user_agent: str = DEFAULT_USER_AGENT,
) -> FetchedPage:
    """One polite GET. Raises FetchError if the URL or any redirect hop
    leaves the domain whitelist, or the response exceeds max_bytes."""

    if not is_approved_url(url, approved_domains):
        raise FetchError(f"URL not in approved domains: {url}")

    opener = _domain_guarded_opener(approved_domains)
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            request = Request(url, headers={"User-Agent": user_agent})
            with opener.open(request, timeout=timeout_seconds) as response:
                final_url = response.geturl()
                if not is_approved_url(final_url, approved_domains):
                    raise FetchError(f"redirect left approved domains: {final_url}")
                announced = response.headers.get("content-length")
                if announced and int(announced) > max_bytes:
                    raise FetchError(f"response exceeds max_bytes ({announced} > {max_bytes})")
                body = response.read(max_bytes + 1)
                if len(body) > max_bytes:
                    raise FetchError(f"response exceeds max_bytes ({max_bytes})")
                return FetchedPage(
                    requested_url=url,
                    final_url=final_url,
                    status_code=response.status,
                    content_type=response.headers.get("content-type", ""),
                    content=bytes(body),
                )
        except FetchError:
            raise
        except (HTTPError, URLError, OSError, ValueError) as error:
            last_error = error
            if attempt < retries:
                time.sleep(0.25 * (2**attempt))
    raise FetchError(str(last_error or "unknown fetch failure"))


def polite_sleep(min_interval_seconds: float = 1.0) -> None:
    """Sleep before a request so sequential CLI invocations stay near 1 req/s."""

    time.sleep(min_interval_seconds)
