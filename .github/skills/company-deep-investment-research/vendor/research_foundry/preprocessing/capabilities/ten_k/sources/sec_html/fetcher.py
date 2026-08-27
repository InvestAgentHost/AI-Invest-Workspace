from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen


DEFAULT_USER_AGENT = ""


def validate_sec_user_agent(value: str) -> str:
    """Require the identifying contact SEC asks clients to send."""

    user_agent = str(value).strip()
    if not user_agent:
        raise ValueError("a SEC-compliant User-Agent with a real contact email is required")
    if "@" not in user_agent or "example.com" in user_agent.casefold():
        raise ValueError("SEC User-Agent must include a real contact email, not a placeholder")
    return user_agent


@dataclass
class FetchResponse:
    url: str
    status_code: int
    text: str | None = None
    content: bytes | None = None
    content_type: str = ""


class SecFetcher:
    def __init__(self, user_agent: str = DEFAULT_USER_AGENT, timeout: int = 30, retries: int = 2, pause_seconds: float = 0.12):
        self.user_agent = validate_sec_user_agent(user_agent)
        self.timeout = timeout
        self.retries = retries
        self.pause_seconds = pause_seconds

    def get_text(self, url: str) -> str:
        response = self._request(url, binary=False)
        if response.text is None:
            return _decode_response_text(response.content or b"", response.content_type)
        return response.text

    def get_json_text(self, url: str) -> str:
        return self.get_text(url)

    def get_binary(self, url: str) -> bytes:
        response = self._request(url, binary=True)
        return response.content or b""

    def download(self, url: str, path: str | Path) -> Path:
        data = self.get_binary(url)
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return destination

    def _request(self, url: str, binary: bool) -> FetchResponse:
        last_exc: Exception | None = None
        for attempt in range(self.retries + 1):
            if attempt:
                time.sleep(self.pause_seconds * attempt)
            try:
                try:
                    import requests  # type: ignore

                    response = requests.get(url, headers={"User-Agent": self.user_agent}, timeout=self.timeout)
                    response.raise_for_status()
                    content_type = response.headers.get("content-type", "")
                    return FetchResponse(
                        url=url,
                        status_code=response.status_code,
                        text=None if binary else _decode_response_text(response.content, content_type),
                        content=response.content,
                        content_type=content_type,
                    )
                except ImportError:
                    request = Request(url, headers={"User-Agent": self.user_agent})
                    with urlopen(request, timeout=self.timeout) as handle:
                        content = handle.read()
                        content_type = handle.headers.get("content-type", "")
                        return FetchResponse(
                            url=url,
                            status_code=getattr(handle, "status", 200),
                            text=None if binary else _decode_response_text(content, content_type),
                            content=content,
                            content_type=content_type,
                        )
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
        raise RuntimeError(f"Failed to fetch {url}: {last_exc}")


def _decode_response_text(content: bytes, content_type: str = "") -> str:
    charset = _charset_from_content_type(content_type) or _charset_from_meta(content) or "utf-8"
    try:
        text = content.decode(charset, errors="replace")
    except LookupError:
        text = content.decode("utf-8", errors="replace")
    return _repair_mojibake(text)


def _charset_from_content_type(content_type: str) -> str | None:
    match = re.search(r"charset=([^;\s]+)", content_type, re.IGNORECASE)
    if match:
        return match.group(1).strip('"\'')
    return None


def _charset_from_meta(content: bytes) -> str | None:
    head = content[:4096].decode("ascii", errors="ignore")
    match = re.search(r"<meta[^>]+charset=[\"']?([^\"'>\s;]+)", head, re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(r"<meta[^>]+content=[\"'][^\"']*charset=([^\"'\s;]+)", head, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def _repair_mojibake(text: str) -> str:
    markers = ("â€™", "â€œ", "â€�", "â€”", "â€“", "â˜", "Â®", "Â©", "Â ", "Ã")
    if sum(text.count(marker) for marker in markers) < 3:
        return text
    try:
        repaired = text.encode("latin-1", errors="strict").decode("utf-8", errors="strict")
    except UnicodeError:
        return text
    before = sum(text.count(marker) for marker in markers)
    after = sum(repaired.count(marker) for marker in markers)
    return repaired if after < before else text
