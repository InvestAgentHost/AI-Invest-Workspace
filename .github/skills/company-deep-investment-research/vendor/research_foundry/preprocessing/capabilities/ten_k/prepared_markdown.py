"""Source-neutral contract and validation for prepared 10-K Markdown."""

import hashlib
from html.parser import HTMLParser
import re

from research_foundry.preprocessing.contracts import MarkdownLineLocator


TEN_K_PREPARED_MARKDOWN_SCHEMA_V1 = (
    "urn:research_foundry:schema:ten_k_prepared_markdown:v1"
)
LEGACY_TEN_K_SEC_HTML_MARKDOWN_SCHEMA_V1 = (
    "urn:research_foundry:schema:ten_k_sec_html_markdown:v1"
)


class MarkdownValidationError(ValueError):
    """Raised when canonical Prepared Markdown is invalid."""


class _TableStructureParser(HTMLParser):
    TRACKED_TAGS = frozenset({"table", "thead", "tbody", "tfoot", "tr", "th", "td"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.error: str | None = None

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        del attrs
        if tag in self.TRACKED_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag not in self.TRACKED_TAGS or self.error is not None:
            return
        if not self.stack or self.stack[-1] != tag:
            self.error = f"unexpected closing HTML table tag </{tag}>"
            return
        self.stack.pop()


def validate_prepared_markdown(document: bytes) -> str:
    """Validate the canonical Markdown accepted from every 10-K source."""

    try:
        text = document.decode("utf-8")
    except UnicodeDecodeError as error:
        raise MarkdownValidationError("Prepared Markdown must be UTF-8") from error
    if not text.strip():
        raise MarkdownValidationError("Prepared Markdown must not be empty")
    if "\r" in text:
        raise MarkdownValidationError("Prepared Markdown must use LF newlines")
    if not text.endswith("\n") or text.endswith("\n\n"):
        raise MarkdownValidationError(
            "Prepared Markdown must end with exactly one LF"
        )

    fence_counts = {
        marker: sum(
            1 for line in text.splitlines() if re.match(rf"^\s*{marker}", line)
        )
        for marker in ("```", "~~~")
    }
    if any(count % 2 for count in fence_counts.values()):
        raise MarkdownValidationError("Prepared Markdown contains an unclosed code fence")

    parser = _TableStructureParser()
    parser.feed(text)
    parser.close()
    if parser.error is not None:
        raise MarkdownValidationError(parser.error)
    if parser.stack:
        raise MarkdownValidationError(
            f"Prepared Markdown contains unclosed HTML table tag <{parser.stack[-1]}>"
        )
    return text


def accepted_document_schemas(*legacy_schemas: str) -> frozenset[str]:
    """Return the canonical schema plus explicitly supported legacy schemas."""

    return frozenset((TEN_K_PREPARED_MARKDOWN_SCHEMA_V1, *legacy_schemas))


def build_markdown_line_locator(
    document: bytes, start_line: int, end_line: int
) -> MarkdownLineLocator:
    """Build a validated inclusive locator for one immutable Markdown artifact."""

    text = validate_prepared_markdown(document)
    line_count = len(text[:-1].split("\n"))
    if start_line < 1 or end_line < start_line or end_line > line_count:
        raise MarkdownValidationError(
            f"line range {start_line}-{end_line} is outside 1-{line_count}"
        )
    return MarkdownLineLocator(
        schema_version="markdown_line_locator.v1",
        artifact_sha256=hashlib.sha256(document).hexdigest(),
        start_line=start_line,
        end_line=end_line,
    )


def resolve_markdown_line_locator(
    document: bytes, locator: MarkdownLineLocator
) -> str:
    """Verify an artifact hash and return the exact addressed lines."""

    if hashlib.sha256(document).hexdigest() != locator.artifact_sha256:
        raise MarkdownValidationError("Prepared Markdown SHA-256 does not match locator")
    text = validate_prepared_markdown(document)
    lines = text[:-1].split("\n")
    if locator.end_line > len(lines):
        raise MarkdownValidationError("Markdown line locator is out of range")
    return "\n".join(lines[locator.start_line - 1 : locator.end_line])
