"""Generic URL boundaries and same-site candidate discovery."""

from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
import re


_TRACKING_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid"}
_SKIP_SCHEMES = {"mailto", "tel", "javascript", "data"}


def normalize_domain(value: str) -> str:
    raw = value.strip().lower().rstrip(".")
    if "://" in raw:
        parsed = urlsplit(raw)
        raw = parsed.hostname or ""
    elif "/" in raw:
        raise ValueError("official domain must not contain a path")
    if not raw or raw.startswith(".") or " " in raw or "." not in raw:
        raise ValueError(f"invalid official domain: {value!r}")
    try:
        return raw.encode("idna").decode("ascii")
    except UnicodeError as error:
        raise ValueError(f"invalid official domain: {value!r}") from error


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


def initial_urls(domains: list[str], seed_urls: list[str]) -> list[str]:
    values = seed_urls or [f"https://{domain}/" for domain in domains]
    return list(dict.fromkeys(normalize_url(value) for value in values))


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
