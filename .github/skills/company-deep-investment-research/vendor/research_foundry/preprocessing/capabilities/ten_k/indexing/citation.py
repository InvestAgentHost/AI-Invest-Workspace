"""Exact line/hash citations shared by index writers and Agent tools."""

import hashlib
from collections.abc import Mapping

from research_foundry.preprocessing.capabilities.ten_k.prepared_markdown import (
    build_markdown_line_locator,
    resolve_markdown_line_locator,
)


def make_locator(document: bytes, start_line: int, end_line: int) -> dict[str, object]:
    """Return a JSON-ready, 1-based inclusive locator for exact source lines."""

    return build_markdown_line_locator(document, start_line, end_line).model_dump(mode="json")


def resolve_locator(document: bytes, locator: Mapping[str, object]) -> str:
    """Verify the hash and return the exact source text addressed by a locator."""

    from research_foundry.preprocessing.contracts import MarkdownLineLocator

    return resolve_markdown_line_locator(document, MarkdownLineLocator.model_validate(dict(locator)))


def sha256(document: bytes) -> str:
    return hashlib.sha256(document).hexdigest()
