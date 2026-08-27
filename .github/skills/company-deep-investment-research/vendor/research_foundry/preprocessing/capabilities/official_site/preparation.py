"""Generic HTML and text-layer PDF preparation without company-specific rules."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
import re

import fitz


_SKIP_TAGS = {"script", "style", "noscript", "svg", "canvas", "nav", "footer", "form", "dialog"}
_BLOCK_TAGS = {"p", "div", "section", "article", "main", "header", "blockquote", "pre", "li", "dt", "dd"}
_MIN_SUBSTANTIVE_CHARS = 120
_MIN_SUBSTANTIVE_BLOCKS = 2


@dataclass(frozen=True, slots=True)
class PreparedHealth:
    status: str
    substantive_char_count: int
    content_block_count: int
    heading_count: int


class _MarkdownParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self.title: str | None = None
        self._text: list[str] = []
        self._prefix = ""
        self._skip_tag: str | None = None
        self._skip_tag_depth = 0
        self._title_depth = 0
        self._link: str | None = None
        self._link_text: list[str] | None = None
        self._table_rows: list[list[str]] = []
        self._table_row: list[str] | None = None
        self._table_cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        values = {key.lower(): value for key, value in attrs}
        if self._skip_tag:
            if tag == self._skip_tag:
                self._skip_tag_depth += 1
            return
        role = (values.get("role") or "").casefold()
        if tag in _SKIP_TAGS or role in {"navigation", "contentinfo"}:
            self._flush()
            self._skip_tag = tag
            self._skip_tag_depth = 1
            return
        if tag == "title":
            self._title_depth = 1
            self._text = []
        elif re.fullmatch(r"h[1-6]", tag):
            self._flush()
            self._prefix = "#" * int(tag[1]) + " "
        elif tag in _BLOCK_TAGS:
            self._flush()
            if tag == "li":
                self._prefix = "- "
            elif tag == "blockquote":
                self._prefix = "> "
        elif tag == "br":
            self._flush()
        elif tag == "a":
            self._flush()
            self._link = values.get("href")
            self._link_text = []
        elif tag == "tr":
            self._flush()
            self._table_row = []
        elif tag in {"td", "th"}:
            self._table_cell = []

    def handle_data(self, data: str) -> None:
        if self._skip_tag:
            return
        if self._table_cell is not None:
            self._table_cell.append(data)
        elif self._link_text is not None:
            self._link_text.append(data)
        else:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._skip_tag:
            if tag == self._skip_tag:
                self._skip_tag_depth -= 1
                if not self._skip_tag_depth:
                    self._skip_tag = None
            return
        if tag == "title" and self._title_depth:
            self.title = _clean_text("".join(self._text)) or self.title
            self._title_depth = 0
            self._text = []
        elif tag in {"td", "th"} and self._table_cell is not None:
            if self._table_row is not None:
                self._table_row.append(_clean_text("".join(self._table_cell)))
            self._table_cell = None
        elif tag == "tr" and self._table_row is not None:
            if any(self._table_row):
                self._table_rows.append(self._table_row)
            self._table_row = None
        elif tag == "table":
            self._flush_table()
        elif tag == "a":
            if self._link and self._link_text:
                text = _clean_text("".join(self._link_text))
                if text:
                    self.blocks.append(f"[{text}]({self._link})")
            self._link = None
            self._link_text = None
        elif re.fullmatch(r"h[1-6]", tag) or tag in _BLOCK_TAGS:
            self._flush()

    def close(self) -> None:
        super().close()
        self._flush()
        self._flush_table()

    def _flush(self) -> None:
        text = _clean_text("".join(self._text))
        if text:
            value = f"{self._prefix}{text}".strip()
            if not self.blocks or self.blocks[-1] != value:
                self.blocks.append(value)
        self._text = []
        self._prefix = ""

    def _flush_table(self) -> None:
        if not self._table_rows:
            return
        width = max(len(row) for row in self._table_rows)
        rows = [row + [""] * (width - len(row)) for row in self._table_rows]
        table_lines = ["| " + " | ".join(_escape_cell(value) for value in rows[0]) + " |"]
        table_lines.append("| " + " | ".join("---" for _ in range(width)) + " |")
        for row in rows[1:]:
            table_lines.append("| " + " | ".join(_escape_cell(value) for value in row) + " |")
        self.blocks.append("\n".join(table_lines))
        self._table_rows = []


def html_to_markdown(content: bytes, *, source_alias: str, url: str, content_type: str) -> tuple[bytes, str | None, list[str]]:
    charset_match = re.search(r"charset\s*=\s*['\"]?([\w.-]+)", content_type, flags=re.IGNORECASE)
    charset = charset_match.group(1) if charset_match else "utf-8"
    warnings: list[str] = []
    try:
        html = content.decode(charset)
    except (LookupError, UnicodeDecodeError):
        html = content.decode("utf-8", errors="replace")
        warnings.append("html_decoded_with_utf8_replacement")
    parser = _MarkdownParser()
    parser.feed(html)
    parser.close()
    body = "\n\n".join(parser.blocks).strip()
    if not body:
        raise ValueError("HTML contains no preparable visible text")
    heading = parser.title or "Official website source"
    document = f"# {heading}\n\nSource: [{source_alias}]({url})\n\n{body}\n"
    return document.encode("utf-8"), parser.title, warnings


def analyze_prepared_markdown(content: bytes) -> PreparedHealth:
    """Classify whether Prepared Markdown contains research-usable body text."""

    text = content.decode("utf-8", errors="replace")
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    body_blocks: list[str] = []
    heading_count = 0
    for index, block in enumerate(blocks):
        if index == 0 and block.startswith("# "):
            continue
        if re.fullmatch(r"Source:\s*\[[^]]+\]\([^)]+\)", block):
            continue
        if re.fullmatch(r"\[[^]]+\]\([^)]+\)", block):
            continue
        if block.startswith("#"):
            heading_count += 1
        body_blocks.append(block)
    body = "\n".join(body_blocks)
    plain = re.sub(r"https?://\S+", " ", body)
    plain = re.sub(r"[\[\]()`*_#>|~-]", " ", plain)
    substantive_chars = len(re.sub(r"\s+", "", plain))
    status = (
        "healthy"
        if substantive_chars >= _MIN_SUBSTANTIVE_CHARS
        and len(body_blocks) >= _MIN_SUBSTANTIVE_BLOCKS
        else "low_content"
    )
    return PreparedHealth(
        status=status,
        substantive_char_count=substantive_chars,
        content_block_count=len(body_blocks),
        heading_count=heading_count,
    )


def pdf_to_markdown(content: bytes, *, source_alias: str, url: str) -> tuple[bytes | None, str | None, list[str]]:
    warnings: list[str] = []
    try:
        document = fitz.open(stream=content, filetype="pdf")
    except Exception as error:
        return None, None, [f"pdf_open_failed:{type(error).__name__}"]
    try:
        metadata_title = _clean_text(str(document.metadata.get("title") or "")) or None
        pages: list[str] = []
        visible_chars = 0
        for number, page in enumerate(document, start=1):
            text = page.get_text("text").replace("\r\n", "\n").replace("\r", "\n").strip()
            visible_chars += len(re.sub(r"\s+", "", text))
            pages.append(f"## Page {number}\n\n{text}" if text else f"## Page {number}\n\n[No extractable text]")
        if visible_chars < max(40, len(document) * 10):
            return None, metadata_title, ["pdf_has_no_reliable_text_layer"]
        title = metadata_title or "Official PDF document"
        markdown = f"# {title}\n\nSource: [{source_alias}]({url})\n\n" + "\n\n".join(pages) + "\n"
        return markdown.encode("utf-8"), metadata_title, warnings
    finally:
        document.close()


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()
