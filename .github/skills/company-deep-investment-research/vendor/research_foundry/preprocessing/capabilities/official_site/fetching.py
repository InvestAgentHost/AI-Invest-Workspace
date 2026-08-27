"""HTTP acquisition with explicit size, retry, and official-domain boundaries."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Protocol

import httpx

from .discovery import is_approved_url


class OfficialSiteFetchError(RuntimeError):
    """Raised when a URL cannot be acquired within the deterministic boundary."""


DEFAULT_USER_AGENT = "ResearchFoundry/0.1 (+https://openai.com/)"


@dataclass(frozen=True, slots=True)
class FetchedResponse:
    requested_url: str
    final_url: str
    status_code: int
    headers: dict[str, str]
    content: bytes


class Fetcher(Protocol):
    def fetch(self, url: str, *, max_bytes: int, approved_domains: list[str]) -> FetchedResponse: ...


class HttpOfficialSiteFetcher:
    def __init__(
        self,
        *,
        timeout_seconds: float = 30,
        retries: int = 2,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.user_agent = user_agent

    def fetch(self, url: str, *, max_bytes: int, approved_domains: list[str]) -> FetchedResponse:
        error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                with _new_http_client(
                    timeout=self.timeout_seconds,
                    user_agent=self.user_agent,
                ) as client:
                    with client.stream("GET", url) as response:
                        if not is_approved_url(str(response.url), approved_domains):
                            raise OfficialSiteFetchError("redirect left approved official domains")
                        response.raise_for_status()
                        announced = response.headers.get("content-length")
                        if announced and int(announced) > max_bytes:
                            raise OfficialSiteFetchError("response exceeds max_response_bytes")
                        body = bytearray()
                        for chunk in response.iter_bytes():
                            body.extend(chunk)
                            if len(body) > max_bytes:
                                raise OfficialSiteFetchError("response exceeds max_response_bytes")
                        return FetchedResponse(
                            requested_url=url,
                            final_url=str(response.url),
                            status_code=response.status_code,
                            headers={key.lower(): value for key, value in response.headers.items()},
                            content=bytes(body),
                        )
            except (httpx.HTTPError, httpx.InvalidURL, OSError, ValueError) as caught:
                error = caught
                if attempt < self.retries:
                    time.sleep(0.25 * (2**attempt))
        raise OfficialSiteFetchError(str(error or "unknown fetch failure"))


def _new_http_client(*, timeout: float, user_agent: str) -> httpx.Client:
    """Honor valid proxy settings, but tolerate malformed inherited proxy rules."""

    try:
        return httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": user_agent},
        )
    except httpx.InvalidURL:
        return httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": user_agent},
            trust_env=False,
        )
