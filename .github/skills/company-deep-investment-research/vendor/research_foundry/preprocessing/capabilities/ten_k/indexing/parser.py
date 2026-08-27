"""Deterministic section, narrative-chunk, and native-table extraction.

This deliberately stops at source organization. It does not infer financial
concepts, summarize disclosures, or ask a model to classify a table.
"""

from bisect import bisect_right
from html import unescape
from html.parser import HTMLParser
import re
from typing import Any

from .citation import make_locator
from .models import SemanticIndexError

_HEADING = re.compile(r"^(?P<marks>#{1,6})[ \t]+(?P<title>.+?)[ \t]*$")
_PLAIN_ITEM = re.compile(
    r"^(?:(?P<part>PART\s+[IVX]+)\.?[ \t]+)?ITEM[ \t]*(?P<number>\d+[A-Za-z]?)(?:[ \t]*[.|][ \t]*|[ \t]+)(?P<title>.+?)[ \t]*$",
    re.IGNORECASE,
)
_TABLE = re.compile(r"<table\b[^>]*>.*?</table\s*>", re.IGNORECASE | re.DOTALL)
_MD_TABLE_SEPARATOR = re.compile(
    r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$"
)
_ITEM_TITLE = re.compile(r"\bITEM\s*(?P<number>\d+[A-Za-z]?)\b", re.IGNORECASE)


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[dict[str, Any]]] = []
        self._row: list[dict[str, Any]] | None = None
        self._cell: dict[str, Any] | None = None
        self.depth = 0
        self.error: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if self.error:
            return
        if tag == "table":
            self.depth += 1
        elif tag == "tr":
            if self._row is not None:
                self.error = "nested or unclosed table row"
            self._row = []
        elif tag in {"td", "th"}:
            if self._row is None or self._cell is not None:
                self.error = "table cell outside row"
                return
            values = dict(attrs)
            self._cell = {
                "text_parts": [],
                "colspan": _positive_span(values.get("colspan")),
                "rowspan": _positive_span(values.get("rowspan")),
            }

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell["text_parts"].append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self.error:
            return
        if tag in {"td", "th"}:
            if self._cell is None or self._row is None:
                self.error = "table cell closes without an open cell"
                return
            cell = self._cell
            self._row.append(
                {
                    "text": " ".join("".join(cell["text_parts"]).split()),
                    "colspan": cell["colspan"],
                    "rowspan": cell["rowspan"],
                }
            )
            self._cell = None
        elif tag == "tr":
            if self._row is None or self._cell is not None or not self._row:
                self.error = "table row is incomplete"
                return
            self.rows.append(self._row)
            self._row = None
        elif tag == "table":
            if self.depth != 1 or self._row is not None or self._cell is not None:
                self.error = "table closes before rows are complete"
                return
            self.depth = 0


def parse_markdown(document: bytes, *, max_chunk_chars: int = 8_000) -> dict[str, list[dict[str, Any]]]:
    """Build all index records from one validated Prepared Markdown document."""

    if max_chunk_chars < 1:
        raise SemanticIndexError("max_chunk_chars must be positive")
    try:
        text = document.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SemanticIndexError("Prepared Markdown must be UTF-8") from error
    if not text.endswith("\n"):
        raise SemanticIndexError("Prepared Markdown must end with LF")
    lines = text[:-1].split("\n")
    digest = __import__("hashlib").sha256(document).hexdigest()
    starts: list[int] = []
    cursor = 0
    for line in lines:
        starts.append(cursor)
        cursor += len(line) + 1

    table_ranges: list[tuple[int, int, str, list[list[dict[str, Any]]]]] = []
    for match in _TABLE.finditer(text):
        start = bisect_right(starts, match.start())
        end = bisect_right(starts, match.end() - 1)
        parser = _TableParser()
        parser.feed(match.group(0))
        parser.close()
        if parser.error or parser.depth or parser._row is not None or parser._cell is not None:
            raise SemanticIndexError(parser.error or "HTML table is incomplete")
        if not parser.rows:
            raise SemanticIndexError("HTML table contains no rows")
        table_ranges.append((start, end, match.group(0), parser.rows))

    occupied_html_lines = {line for start, end, _, _ in table_ranges for line in range(start, end + 1)}
    line_number = 1
    while line_number < len(lines):
        if (
            line_number in occupied_html_lines
            or not _looks_like_md_table_row(lines[line_number - 1])
            or not _MD_TABLE_SEPARATOR.match(lines[line_number])
        ):
            line_number += 1
            continue
        start = line_number
        end = line_number + 1
        while end < len(lines) and _looks_like_md_table_row(lines[end]):
            end += 1
        if any(line in occupied_html_lines for line in range(start, end)):
            line_number = end
            continue
        rows = [_md_table_cells(lines[row - 1]) for row in range(start, end + 1) if row != start + 1]
        if rows and any(any(cell["text"] for cell in row) for row in rows):
            source = "\n".join(lines[start - 1 : end])
            table_ranges.append((start, end, source, rows))
        line_number = end
    table_ranges.sort(key=lambda value: (value[0], value[1]))

    headings: list[dict[str, Any]] = []
    current_item: str | None = None
    for number, line in enumerate(lines, start=1):
        if any(start <= number <= end for start, end, _, _ in table_ranges):
            continue
        match = _HEADING.match(line)
        if match:
            title = _clean_title(match.group("title"))
            item_match = _ITEM_TITLE.search(title)
            if item_match and title.upper().startswith("ITEM"):
                current_item = item_match.group("number").upper()
            headings.append({"line": number, "level": len(match.group("marks")), "title": title, "item": current_item})
            continue
        plain = _PLAIN_ITEM.match(line)
        if plain and plain.group("title").strip():
            current_item = plain.group("number").upper()
            headings.append({"line": number, "level": 2, "title": _clean_title(line), "item": current_item})

    sections: list[dict[str, Any]] = []
    for index, heading in enumerate(headings):
        end = len(lines)
        for following in headings[index + 1 :]:
            if following["level"] <= heading["level"]:
                end = following["line"] - 1
                break
        stack: list[dict[str, Any]] = []
        for candidate in headings[: index + 1]:
            while stack and candidate["level"] <= stack[-1]["level"]:
                stack.pop()
            stack.append(candidate)
        path = [candidate["title"] for candidate in stack]
        section_id = _stable_id("sec", digest, str(heading["line"]), "/".join(path))
        sections.append({
            "section_id": section_id,
            "title": heading["title"],
            "level": heading["level"],
            "item": heading["item"],
            "section_path": path,
            "start_line": heading["line"],
            "end_line": end,
            "locator": make_locator(document, heading["line"], end),
        })

    section_for_line = _section_lookup(sections)
    chunks: list[dict[str, Any]] = []
    occupied = {line for start, end, _, _ in table_ranges for line in range(start, end + 1)}
    paragraph_blocks: list[tuple[int, int, str, dict[str, Any] | None]] = []
    current: list[int] = []

    def flush() -> None:
        nonlocal current
        if not current:
            return
        first, last = current[0], current[-1]
        source = "\n".join(lines[first - 1 : last]).strip()
        if source:
            section = section_for_line(first)
            section_id = section.get("section_id") if section else None
            paragraph_blocks.append((first, last, source, section))
        current = []

    for number, line in enumerate(lines, start=1):
        if number in occupied or not line.strip() or _HEADING.match(line) or _PLAIN_ITEM.match(line):
            flush()
            continue
        if current and len("\n".join(lines[current[0] - 1 : number])) > max_chunk_chars:
            flush()
        current.append(number)
    flush()

    # Keep paragraphs together inside one section until the configured bound.
    # A table range is a hard boundary so a narrative locator never silently
    # absorbs a native table between two paragraphs.
    grouped: list[list[tuple[int, int, str, dict[str, Any] | None]]] = []
    for block in paragraph_blocks:
        if not grouped:
            grouped.append([block])
            continue
        previous = grouped[-1][-1]
        previous_section = previous[3].get("section_id") if previous[3] else None
        block_section = block[3].get("section_id") if block[3] else None
        between = range(previous[1] + 1, block[0])
        current_chars = sum(len(value[2]) + (2 if index else 0) for index, value in enumerate(grouped[-1]))
        if (
            previous_section != block_section
            or any(line in occupied for line in between)
            or (current_chars + len(block[2]) + 2 > max_chunk_chars and grouped[-1])
        ):
            grouped.append([block])
        else:
            grouped[-1].append(block)
    for group in grouped:
        first, last = group[0][0], group[-1][1]
        source = "\n\n".join(value[2] for value in group)
        section = group[0][3]
        chunks.append({
            "chunk_id": _stable_id("chn", digest, str(first), str(last), source),
            "section_id": section.get("section_id") if section else None,
            "item": section.get("item") if section else None,
            "section_path": section.get("section_path", []) if section else [],
            "start_line": first,
            "end_line": last,
            "char_count": len(source),
            "text": source,
            "locator": make_locator(document, first, last),
        })

    tables: list[dict[str, Any]] = []
    for ordinal, (start, end, html, rows) in enumerate(table_ranges, start=1):
        section = section_for_line(start)
        tables.append({
            "table_id": _stable_id("tbl", digest, str(start), str(end), html),
            "ordinal": ordinal,
            "item": section.get("item") if section else None,
            "section_id": section.get("section_id") if section else None,
            "section_path": section.get("section_path", []) if section else [],
            "start_line": start,
            "end_line": end,
            "row_count": len(rows),
            "column_count": max(len(row) for row in rows),
            "rows": rows,
            "source_html": html,
            "format": "html" if html.lstrip().lower().startswith("<table") else "markdown",
            "locator": make_locator(document, start, end),
        })
    return {"sections": sections, "chunks": chunks, "tables": tables}


def _section_lookup(sections: list[dict[str, Any]]) -> Any:
    def lookup(line: int) -> dict[str, Any] | None:
        candidates = [section for section in sections if section["start_line"] <= line <= section["end_line"]]
        return max(candidates, key=lambda section: section["start_line"], default=None)
    return lookup


def _clean_title(value: str) -> str:
    return unescape(re.sub(r"\s+", " ", value.strip(" .|")))


def _positive_span(value: str | None) -> int:
    try:
        parsed = int(value or "1")
    except ValueError:
        return 1
    return parsed if parsed > 0 else 1


def _looks_like_md_table_row(line: str) -> bool:
    stripped = line.strip()
    return "|" in stripped and not stripped.startswith("```")


def _md_table_cells(line: str) -> list[dict[str, Any]]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|") and not stripped.endswith("\\|"):
        stripped = stripped[:-1]
    values = re.split(r"(?<!\\)\|", stripped)
    return [
        {"text": value.replace("\\|", "|").strip(), "colspan": 1, "rowspan": 1}
        for value in values
    ]


def _stable_id(prefix: str, *parts: str) -> str:
    import hashlib
    return f"{prefix}_{hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:20]}"
