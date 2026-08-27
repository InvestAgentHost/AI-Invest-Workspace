from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from .fetcher import SecFetcher

BLOCK_TAGS = {"p", "div", "table", "img", "h1", "h2", "h3", "h4", "h5", "h6", "li"}
SKIP_TAGS = {"script", "style", "noscript", "meta", "link"}
VOID_TAGS = {"br", "hr", "img", "meta", "link", "input"}
HIDDEN_XBRL_TAGS = {
    "ix:header",
    "ix:hidden",
    "ix:references",
    "ix:resources",
    "ix:relationship",
    "xbrli:context",
    "xbrli:unit",
    "link:schemaref",
    "link:linkbase",
    "xbrldi:explicitmember",
    "xbrldi:typedmember",
}
MOJIBAKE_MARKERS = ("â€™", "â€œ", "â€�", "â€”", "â€“", "â˜", "Â®", "Â©", "Â ", "Ã")


PROXY_MAJOR_HEADINGS = {
    "Notice of Annual Meeting of Shareholders",
    "Message from our Chief Executive Officer",
    "Proxy Statement Summary",
    "Corporate Governance",
    "Executive Compensation",
    "Shareholder Proposals",
    "Other Information",
    "Audit Committee Report",
}

PROXY_COVER_TEXT = {
    "Table of Contents",
    "UNITED STATES",
    "SECURITIES AND EXCHANGE COMMISSION",
    "Washington, DC 20549",
    "SCHEDULE 14A",
}
@dataclass
class Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list["Node"] = field(default_factory=list)
    parts: list[Any] = field(default_factory=list)
    text: str = ""
    parent: "Node | None" = None


@dataclass
class HtmlExtraction:
    markdown: str
    document: dict
    assets: list[dict]
    xbrl_metadata: list[dict] = field(default_factory=list)
    cleaning_report: dict = field(default_factory=dict)


@dataclass
class HeadingInference:
    level: int
    confidence: float
    reasons: list[str] = field(default_factory=list)
    style_signature: str | None = None


class _TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root = Node("document")
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        tag = tag.lower()
        node = Node(tag, {key.lower(): value or "" for key, value in attrs}, parent=self.stack[-1])
        if tag == "br":
            self.stack[-1].parts.append("\n")
            self.stack[-1].text += "\n"
        self.stack[-1].children.append(node)
        self.stack[-1].parts.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_endtag(self, tag: str):
        tag = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str):
        if data:
            self.stack[-1].text += data
            self.stack[-1].parts.append(data)

    def handle_entityref(self, name: str):
        text = unescape(f"&{name};")
        self.stack[-1].text += text
        self.stack[-1].parts.append(text)

    def handle_charref(self, name: str):
        text = unescape(f"&#{name};")
        self.stack[-1].text += text
        self.stack[-1].parts.append(text)


def extract_html_to_markdown(
    html: str,
    source_url: str,
    output_dir: str | Path,
    filing_metadata: dict | None = None,
    fetcher: SecFetcher | None = None,
    download_assets: bool = True,
) -> HtmlExtraction:
    html = _repair_mojibake(html)
    builder = _TreeBuilder()
    builder.feed(html)
    output = Path(output_dir)
    assets_dir = output / "assets"
    if download_assets:
        assets_dir.mkdir(parents=True, exist_ok=True)
    if fetcher is None:
        fetcher = SecFetcher() if download_assets else _NoopFetcher()
    metadata = filing_metadata or {}

    body = _first(builder.root, "body") or builder.root
    blocks: list[dict] = []
    assets: list[dict] = []
    xbrl_metadata: list[dict] = []
    state = {
        "inside_filing_body": False,
        "current_section": None,
        "style_heading_levels": {},
        "baseline_style": _style_baseline(body),
        "proxy_filing": _is_proxy_filing(metadata),
        "proxy_outline": _build_proxy_outline(body) if _is_proxy_filing(metadata) else {},
    }
    _walk(body, blocks, assets, xbrl_metadata, source_url, assets_dir, metadata, fetcher, download_assets, [], state)
    blocks = _merge_split_headings(blocks)

    markdown = _blocks_to_markdown(blocks)
    cleaning_report = _build_cleaning_report(
        html, markdown, blocks, assets, xbrl_metadata, metadata
    )
    document = {
        "source_url": source_url,
        "metadata": {**metadata, "xbrl_metadata_count": len(xbrl_metadata), "proxy_outline_count": len(state.get("proxy_outline") or {})},
        "blocks": blocks,
        "assets": assets,
    }
    return HtmlExtraction(
        markdown=markdown,
        document=document,
        assets=assets,
        xbrl_metadata=xbrl_metadata,
        cleaning_report=cleaning_report,
    )


def write_html_extraction(extraction: HtmlExtraction, output_dir: str | Path) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "document.md").write_text(extraction.markdown, encoding="utf-8")
    (output / "document.json").write_text(json.dumps(extraction.document, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "xbrl_metadata.json").write_text(json.dumps(extraction.xbrl_metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "cleaning_report.json").write_text(json.dumps(extraction.cleaning_report, ensure_ascii=False, indent=2), encoding="utf-8")


class _NoopFetcher:
    """Prevent accidental network access when asset downloads are disabled."""

    def download(self, url: str, path: str | Path) -> Path:
        raise RuntimeError(f"asset download disabled: {url}")


def _walk(
    node: Node,
    blocks: list[dict],
    assets: list[dict],
    xbrl_metadata: list[dict],
    source_url: str,
    assets_dir: Path,
    filing_metadata: dict,
    fetcher: SecFetcher,
    download_assets: bool,
    path_parts: list[str],
    state: dict[str, bool],
) -> None:
    if node.tag in SKIP_TAGS:
        return
    dom_path = _dom_path(node, path_parts)
    hidden_reason = _hidden_or_metadata_reason(node)
    if hidden_reason:
        _collect_metadata(node, xbrl_metadata, dom_path, hidden_reason)
        return
    if node.tag == "table":
        is_toc_table = bool(state.get("proxy_filing") and _is_proxy_toc_table(node))
        proxy_table_heading = None if is_toc_table else _proxy_heading_from_table(node, state)
        if proxy_table_heading:
            inference = HeadingInference(int(proxy_table_heading["level"]), 0.99, ["proxy_toc_table_anchor"], _style_signature(node))
            _append_heading(blocks, inference.level, str(proxy_table_heading["title"]), source_url, dom_path, filing_metadata, inferred=True, state=state, inference=inference)
        rows = _table_rows(node, assets, source_url, assets_dir, fetcher, download_assets)
        if rows:
            blocks.append(_block("table", _table_to_markdown(rows), source_url, dom_path, filing_metadata, rows=rows, is_toc=is_toc_table))
        return
    if node.tag == "img":
        asset = _asset_for_img(node, source_url, assets_dir, fetcher, download_assets)
        assets.append(asset)
        blocks.append(_block("image", f"![{asset['filename']}](assets/{asset['filename']})", source_url, dom_path, filing_metadata, asset=asset))
        return
    if node.tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        text = _node_text(node)
        if text:
            level = int(node.tag[1])
            _append_heading(blocks, level, text, source_url, dom_path, filing_metadata, inferred=False, state=state)
        return
    if node.tag in {"p", "li"} or (node.tag == "div" and not _has_block_child(node)):
        plain_text = _node_text(node)
        if state.get("proxy_filing") and _is_proxy_running_toc_link(node, plain_text):
            return
        markdown_text, embedded_assets = _node_markdown(node, assets, source_url, assets_dir, fetcher, download_assets)
        if markdown_text:
            if node.tag == "li":
                blocks.append(_block("list_item", markdown_text, source_url, dom_path, filing_metadata, embedded_assets=embedded_assets))
            else:
                allow_visual = bool(state["inside_filing_body"] or state.get("proxy_filing"))
                inference = None if embedded_assets else _infer_heading_level(plain_text, node, allow_visual=allow_visual, state=state)
                if inference:
                    _append_heading(blocks, inference.level, plain_text, source_url, dom_path, filing_metadata, inferred=True, state=state, inference=inference)
                else:
                    blocks.append(_block("paragraph", markdown_text, source_url, dom_path, filing_metadata, embedded_assets=embedded_assets))
        return

    child_counts: dict[str, int] = {}
    for child in node.children:
        count = child_counts.get(child.tag, 0) + 1
        child_counts[child.tag] = count
        _walk(child, blocks, assets, xbrl_metadata, source_url, assets_dir, filing_metadata, fetcher, download_assets, [*path_parts, f"{node.tag}[{count}]"], state)


def _append_heading(
    blocks: list[dict],
    level: int,
    text: str,
    source_url: str,
    dom_path: str,
    filing_metadata: dict,
    inferred: bool,
    state: dict[str, Any],
    inference: HeadingInference | None = None,
) -> None:
    normalized = _clean_heading_text(text)
    if re.fullmatch(r"PART\s+[IVXLC]+", normalized, re.IGNORECASE):
        state["inside_filing_body"] = True
        state["current_section"] = normalized
    if re.match(r"^ITEM\s+\d+[A-Z]?\.?\s+\S", normalized, re.IGNORECASE):
        state["inside_filing_body"] = True
        state["current_section"] = normalized
    metadata: dict[str, Any] = {"level": level, "inferred": inferred}
    if inference:
        metadata.update(
            {
                "heading_confidence": inference.confidence,
                "heading_reason": inference.reasons,
                "style_signature": inference.style_signature,
            }
        )
        if inference.style_signature and level >= 3:
            style_levels = state.setdefault("style_heading_levels", {})
            style_levels[(state.get("current_section") or "", inference.style_signature)] = level
    blocks.append(_block("heading", _format_heading(level, normalized), source_url, dom_path, filing_metadata, **metadata))


def _block(block_type: str, text: str, source_url: str, dom_path: str, filing_metadata: dict, **extra) -> dict:
    metadata = {
        "source_url": source_url,
        "dom_path": dom_path,
        "filename": filing_metadata.get("filename"),
        "filing_type": filing_metadata.get("filing_type"),
        "accession": filing_metadata.get("accession"),
    }
    metadata.update(extra)
    return {"type": block_type, "text": text, "metadata": metadata}


def _asset_for_img(node: Node, source_url: str, assets_dir: Path, fetcher: SecFetcher, download_assets: bool) -> dict:
    src = node.attrs.get("src", "")
    asset_url = urljoin(source_url, src)
    filename = Path(urlparse(asset_url).path).name or Path(src).name or "image"
    asset = {"filename": filename, "src": src, "url": asset_url, "alt": node.attrs.get("alt", ""), "style": node.attrs.get("style", "")}
    if download_assets and filename:
        destination = assets_dir / filename
        try:
            if not destination.exists():
                parsed = urlparse(asset_url)
                if parsed.scheme in {"http", "https"}:
                    fetcher.download(asset_url, destination)
                else:
                    source_path = Path(asset_url)
                    if source_path.exists():
                        shutil.copyfile(source_path, destination)
            asset["path"] = str(destination)
        except Exception as exc:  # noqa: BLE001
            asset["download_error"] = str(exc)
    return asset


def _format_heading(level: int, text: str) -> str:
    heading_text = re.sub(r"\s+", " ", text).strip()
    return f"{'#' * min(level, 6)} {heading_text}"


def _merge_split_headings(blocks: list[dict]) -> list[dict]:
    merged: list[dict] = []
    index = 0
    while index < len(blocks):
        block = blocks[index]
        metadata = block.get("metadata", {}) if isinstance(block.get("metadata"), dict) else {}
        filing_type = str(metadata.get("filing_type") or "").upper()
        if block.get("type") != "heading" or "14A" not in filing_type:
            merged.append(block)
            index += 1
            continue
        level = metadata.get("level")
        pieces = [_heading_plain_text(block.get("text", ""))]
        next_index = index + 1
        while next_index < len(blocks):
            candidate = blocks[next_index]
            if candidate.get("type") != "heading" or candidate.get("metadata", {}).get("level") != level:
                break
            candidate_text = _heading_plain_text(candidate.get("text", ""))
            combined = " ".join([*pieces, candidate_text]).strip()
            proposal_prefix = len(pieces) == 1 and re.match(r"^Proposal No\.\s*\d+", pieces[0], re.IGNORECASE)
            if not proposal_prefix and (len(combined) > 80 or sum(len(piece.split()) for piece in pieces) > 4 or len(candidate_text.split()) > 3):
                break
            pieces.append(candidate_text)
            next_index += 1
        if len(pieces) > 1:
            new_block = json.loads(json.dumps(block))
            new_block["text"] = _format_heading(int(level or 3), " ".join(pieces))
            reason = new_block.setdefault("metadata", {}).setdefault("heading_reason", [])
            if isinstance(reason, list) and "split_heading_merge" not in reason:
                reason.append("split_heading_merge")
            merged.append(new_block)
            index = next_index
        else:
            merged.append(block)
            index += 1
    return merged


def _heading_plain_text(text: str) -> str:
    return re.sub(r"^#{1,6}\s*", "", str(text)).strip()

def _blocks_to_markdown(blocks: list[dict]) -> str:
    parts: list[str] = []
    for block in blocks:
        text = block.get("text", "").strip()
        if not text:
            continue
        if block["type"] == "list_item":
            parts.append(f"- {text}")
        else:
            parts.append(text)
    return "\n\n".join(parts).strip() + "\n"


def _table_rows(
    node: Node,
    assets: list[dict],
    source_url: str,
    assets_dir: Path,
    fetcher: SecFetcher,
    download_assets: bool,
) -> list[list[str]]:
    raw_rows: list[list[dict[str, object]]] = []
    for tr in _descendants(node, {"tr"}):
        if _hidden_or_metadata_reason(tr):
            continue
        position = 0
        raw_row: list[dict[str, object]] = []
        for cell in tr.children:
            if cell.tag not in {"td", "th"} or _hidden_or_metadata_reason(cell):
                continue
            colspan = _cell_colspan(cell)
            text, _embedded_assets = _node_markdown(cell, assets, source_url, assets_dir, fetcher, download_assets)
            raw_row.append({"text": text, "start": position, "end": position + colspan, "colspan": colspan})
            position += colspan
        if raw_row and any(str(cell["text"]).strip() for cell in raw_row):
            raw_rows.append(raw_row)
    return _logical_table_rows(raw_rows)


def _cell_colspan(cell: Node) -> int:
    try:
        return max(1, int(cell.attrs.get("colspan", "1") or "1"))
    except ValueError:
        return 1


def _logical_table_rows(raw_rows: list[list[dict[str, object]]]) -> list[list[str]]:
    if not raw_rows:
        return []
    header_index = _header_row_index(raw_rows)
    if header_index is None:
        return [_compact_table_row([str(cell["text"]) for cell in row]) for row in raw_rows]

    ranges = _column_ranges_from_header(raw_rows, header_index)
    if not ranges:
        return [_compact_table_row([str(cell["text"]) for cell in row]) for row in raw_rows]

    rows: list[list[str]] = []
    for row in raw_rows[header_index:]:
        logical = [_text_for_range(row, start, end) for start, end in ranges]
        if any(logical):
            rows.append(logical)
    return rows


def _header_row_index(raw_rows: list[list[dict[str, object]]]) -> int | None:
    for index, row in enumerate(raw_rows):
        non_empty = [cell for cell in row if str(cell["text"]).strip()]
        if len(non_empty) >= 2:
            return index
    return None


def _column_ranges_from_header(raw_rows: list[list[dict[str, object]]], header_index: int) -> list[tuple[int, int]]:
    header_cells = [cell for cell in raw_rows[header_index] if str(cell["text"]).strip()]
    if not header_cells:
        return []

    starts = [int(cell["start"]) for cell in header_cells]
    ends = [int(cell["end"]) for cell in header_cells]
    max_end = max(int(cell["end"]) for row in raw_rows for cell in row)
    ranges: list[tuple[int, int]] = []

    first_start = starts[0]
    if first_start > 0 and _any_text_in_range(raw_rows[header_index + 1 :], 0, first_start):
        ranges.append((0, first_start))

    boundaries: list[int] = []
    for left_end, right_start in zip(ends, starts[1:]):
        gap = right_start - left_end
        if gap <= 1:
            boundaries.append(left_end)
        else:
            boundaries.append((left_end + right_start) // 2)

    for index, start in enumerate(starts):
        if index == 0:
            left = start
        else:
            left = boundaries[index - 1]
        right = boundaries[index] if index < len(boundaries) else max_end
        if right > left:
            ranges.append((left, right))
    return ranges


def _any_text_in_range(rows: list[list[dict[str, object]]], start: int, end: int) -> bool:
    for row in rows:
        if _text_for_range(row, start, end):
            return True
    return False


def _text_for_range(row: list[dict[str, object]], start: int, end: int) -> str:
    pieces: list[str] = []
    for cell in row:
        cell_start = int(cell["start"])
        cell_end = int(cell["end"])
        if cell_end <= start or cell_start >= end:
            continue
        text = str(cell["text"]).strip()
        if text:
            pieces.append(text)
    return _compact_table_tokens(pieces)


def _compact_table_tokens(tokens: list[str]) -> list[str] | str:
    cleaned = [_clean_text(token) for token in tokens if _clean_text(token)]
    merged: list[str] = []
    index = 0
    while index < len(cleaned):
        cell = cleaned[index]
        if cell in {"$", "US$"} and index + 1 < len(cleaned):
            merged.append(f"{cell} {cleaned[index + 1]}")
            index += 2
            continue
        if cell == "%" and merged:
            merged[-1] = f"{merged[-1]} %"
            index += 1
            continue
        if cell in {"(", "["} and index + 1 < len(cleaned):
            close = ")" if cell == "(" else "]"
            merged.append(f"{cell}{cleaned[index + 1]}{close if index + 2 < len(cleaned) and cleaned[index + 2] == close else ''}")
            index += 3 if index + 2 < len(cleaned) and cleaned[index + 2] == close else 2
            continue
        if cell in {")",
            "]",
        } and merged:
            merged[-1] = f"{merged[-1]}{cell}"
            index += 1
            continue
        merged.append(cell)
        index += 1
    if len(tokens) == 1:
        return merged[0] if merged else ""
    return " ".join(merged)


def _compact_table_row(row: list[str]) -> list[str]:
    compacted = _compact_table_tokens(row)
    if isinstance(compacted, str):
        return [compacted] if compacted else []
    return compacted


def _table_to_markdown(rows: list[list[str]]) -> str:
    width = max(len(row) for row in rows)
    normalized = [row + [""] * (width - len(row)) for row in rows]
    header = normalized[0]
    separator = ["---"] * width
    body = normalized[1:]
    return "\n".join([_md_row(header), _md_row(separator), *[_md_row(row) for row in body]])


def _md_row(row: list[str]) -> str:
    return "| " + " | ".join(cell.replace("|", "\\|").strip() for cell in row) + " |"


def _node_markdown(
    node: Node,
    assets: list[dict],
    source_url: str,
    assets_dir: Path,
    fetcher: SecFetcher,
    download_assets: bool,
) -> tuple[str, list[dict]]:
    if node.tag in SKIP_TAGS or _hidden_or_metadata_reason(node):
        return "", []
    pieces: list[str] = []
    embedded_assets: list[dict] = []
    for part in node.parts:
        if isinstance(part, str):
            pieces.append(part)
        elif isinstance(part, Node):
            if part.tag == "table":
                continue
            if part.tag == "img":
                asset = _asset_for_img(part, source_url, assets_dir, fetcher, download_assets)
                assets.append(asset)
                embedded_assets.append(asset)
                pieces.append(_image_markdown(asset))
                continue
            child_text, child_assets = _node_markdown(part, assets, source_url, assets_dir, fetcher, download_assets)
            if child_text:
                pieces.append(child_text)
            embedded_assets.extend(child_assets)
    return _clean_text(_join_text_parts(pieces)), embedded_assets


def _image_markdown(asset: dict) -> str:
    filename = asset.get("filename", "image")
    alt = str(asset.get("alt") or filename).replace("[", "(").replace("]", ")")
    return f"![{alt}](assets/{filename})"


def _node_text(node: Node) -> str:
    if node.tag in SKIP_TAGS or _hidden_or_metadata_reason(node):
        return ""
    pieces: list[str] = []
    for part in node.parts:
        if isinstance(part, str):
            pieces.append(part)
        elif isinstance(part, Node):
            if part.tag in {"table", "img"}:
                continue
            pieces.append(_node_text(part))
    return _clean_text(_join_text_parts(pieces))


def _join_text_parts(pieces: list[str]) -> str:
    text = ""
    for piece in pieces:
        if not piece:
            continue
        if not text:
            text = piece
            continue
        if piece.startswith((",", ".", ";", ":", ")", "]", "%")):
            text = text.rstrip() + piece
        elif text.endswith(("(", "[", "$", "\n")):
            text += piece.lstrip()
        else:
            text += " " + piece.lstrip()
    return text


def _clean_text(text: str) -> str:
    text = _repair_mojibake(unescape(text)).replace("\xa0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\s+([,.;:%\)\]])", r"\1", text)
    text = re.sub(r"([\(\[\$])\s+", r"\1", text)
    text = re.sub("\\s+([\\u2019'])\\s+", r"\1", text)
    text = re.sub("([A-Za-z0-9])\\s+([\\u2019'])([A-Za-z])", r"\1\2\3", text)
    text = re.sub("([\\u201c\\u2018])\\s+", r"\1", text)
    text = re.sub("\\s+([\\u201d\\u2019])", r"\1", text)
    text = re.sub(r"\$([^\s])", r"$ \1", text)
    return text.strip()


def _repair_mojibake(text: str) -> str:
    if sum(text.count(marker) for marker in MOJIBAKE_MARKERS) < 2:
        return text
    before = sum(text.count(marker) for marker in MOJIBAKE_MARKERS)
    for encoding in ("cp1252", "latin-1"):
        try:
            repaired = text.encode(encoding, errors="strict").decode("utf-8", errors="strict")
        except UnicodeError:
            continue
        after = sum(repaired.count(marker) for marker in MOJIBAKE_MARKERS)
        if after < before:
            return repaired
    return text


def _has_block_child(node: Node) -> bool:
    return any(child.tag in BLOCK_TAGS and not _hidden_or_metadata_reason(child) for child in node.children)


def _descendants(node: Node, tags: set[str]) -> list[Node]:
    found: list[Node] = []
    for child in node.children:
        if child.tag in tags:
            found.append(child)
        found.extend(_descendants(child, tags))
    return found


def _first(node: Node, tag: str) -> Node | None:
    if node.tag == tag:
        return node
    for child in node.children:
        found = _first(child, tag)
        if found:
            return found
    return None


def _dom_path(node: Node, parts: list[str]) -> str:
    if not parts:
        return node.tag
    return "/".join([*parts, node.tag])


def _hidden_or_metadata_reason(node: Node) -> str | None:
    tag = node.tag.lower()
    if tag in HIDDEN_XBRL_TAGS:
        return "xbrl_metadata_tag"
    attrs = node.attrs
    if "hidden" in attrs:
        return "hidden_attribute"
    if attrs.get("aria-hidden", "").lower() == "true":
        return "aria_hidden"
    style = attrs.get("style", "").lower().replace(" ", "")
    if "display:none" in style or "visibility:hidden" in style:
        return "hidden_style"
    class_name = attrs.get("class", "").lower()
    if re.search(r"\b(hidden|hide|d-none)\b", class_name):
        return "hidden_class"
    return None


def _collect_metadata(node: Node, xbrl_metadata: list[dict], dom_path: str, reason: str) -> None:
    text = _metadata_text(node)
    attrs = {key: value for key, value in node.attrs.items() if key in {"id", "name", "contextref", "unitref", "decimals", "format", "scheme", "style", "class"}}
    metadata = {
        "tag": node.tag,
        "reason": reason,
        "dom_path": dom_path,
        "attrs": attrs,
        "text_preview": text[:500],
        "text_length": len(text),
    }
    tag_names = sorted(_xbrl_tag_names(node))
    if tag_names:
        metadata["tag_names"] = tag_names[:100]
        metadata["tag_name_count"] = len(tag_names)
    xbrl_metadata.append(metadata)


def _metadata_text(node: Node) -> str:
    pieces: list[str] = []
    for part in node.parts:
        if isinstance(part, str):
            pieces.append(part)
        elif isinstance(part, Node):
            pieces.append(_metadata_text(part))
    return _clean_text(_join_text_parts(pieces))


def _xbrl_tag_names(node: Node) -> set[str]:
    names: set[str] = set()
    tag = node.tag.lower()
    if _is_namespaced_name(tag):
        names.add(node.tag)
    name_attr = node.attrs.get("name", "").lower()
    if _is_namespaced_name(name_attr):
        names.add(node.attrs.get("name", ""))
    for child in node.children:
        names.update(_xbrl_tag_names(child))
    return names


def _is_namespaced_name(value: str) -> bool:
    return bool(
        re.match(
            r"^[A-Za-z_][A-Za-z0-9_.-]*:[A-Za-z_][A-Za-z0-9_.-]*$",
            value,
        )
    )


def _build_cleaning_report(
    html: str,
    markdown: str,
    blocks: list[dict],
    assets: list[dict],
    xbrl_metadata: list[dict],
    filing_metadata: dict,
) -> dict:
    """Emit bounded diagnostics so the Terminal Agent can debug anomalies."""

    block_counts: dict[str, int] = {}
    heading_reason_counts: dict[str, int] = {}
    inferred_headings = 0
    explicit_headings = 0
    for block in blocks:
        block_type = str(block.get("type") or "unknown")
        block_counts[block_type] = block_counts.get(block_type, 0) + 1
        if block_type != "heading":
            continue
        block_metadata = block.get("metadata") or {}
        if block_metadata.get("inferred"):
            inferred_headings += 1
        else:
            explicit_headings += 1
        for reason in block_metadata.get("heading_reason") or ():
            reason_text = str(reason)
            heading_reason_counts[reason_text] = heading_reason_counts.get(reason_text, 0) + 1

    heading_text = "\n".join(
        str(block.get("text") or "")
        for block in blocks
        if block.get("type") == "heading"
    )
    semantic_heading_tag_count = len(
        re.findall(r"<h[1-6](?:\s|>)", html, flags=re.IGNORECASE)
    )
    warnings: list[str] = []
    filing_type = str(filing_metadata.get("filing_type") or "").upper()
    if "10-K" in filing_type and not re.search(r"(?im)^\s*(?:#\s*)?(?:PART|ITEM)\b", heading_text):
        warnings.append("sec_part_or_item_heading_not_found")
    if inferred_headings > max(12, explicit_headings * 3 + 6):
        if explicit_headings == 0 and semantic_heading_tag_count == 0:
            warnings.append("heading_inference_used_without_semantic_heading_tags")
        else:
            warnings.append("heading_inference_dominates_structure")
    if not blocks:
        warnings.append("no_visible_blocks")
    if not any(block.get("type") == "paragraph" for block in blocks):
        warnings.append("no_visible_paragraphs")

    namespaces = sorted(
        {
            str(tag_name).split(":", 1)[0]
            for entry in xbrl_metadata
            for tag_name in entry.get("tag_names") or ()
            if ":" in str(tag_name)
        }
    )
    visible_text = _metric_text("\n".join(str(block.get("text") or "") for block in blocks))
    markdown_text = _metric_text(markdown)
    return {
        "schema_version": "ten_k_html_cleaning_report.v1",
        "source_format": "sec_native_html",
        "filing_type": filing_type or None,
        "generic_rules_only": True,
        "input": {"html_char_count": len(html)},
        "output": {
            "markdown_char_count": len(markdown),
            "visible_text_char_count": len(visible_text),
            "block_count": len(blocks),
            "block_counts": dict(sorted(block_counts.items())),
            "heading_count": inferred_headings + explicit_headings,
            "semantic_heading_tag_count": semantic_heading_tag_count,
            "explicit_heading_count": explicit_headings,
            "inferred_heading_count": inferred_headings,
            "heading_reason_counts": dict(sorted(heading_reason_counts.items())),
            "table_count": block_counts.get("table", 0),
            "asset_count": len(assets),
            "hidden_metadata_count": len(xbrl_metadata),
            "custom_xbrl_namespaces": namespaces,
        },
        "quality": {
            "visible_text_to_markdown_ratio": round(
                len(markdown_text) / max(len(visible_text), 1), 3
            ),
            "warnings": warnings,
        },
        "debug_boundary": {
            "source_authority": "raw/source.html",
            "prepared_authority": "prepared/document.md",
            "index_authority": "semantic_index_is_retrieval_aid_only",
            "company_specific_rules": [],
        },
    }


def _metric_text(value: str) -> str:
    value = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", value)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _infer_heading_level(text: str, node: Node, allow_visual: bool, state: dict[str, Any]) -> HeadingInference | None:
    normalized = _clean_heading_text(text)
    if not normalized or len(normalized) > 180:
        return None
    if _looks_like_toc_entry(normalized):
        return None
    upper = normalized.upper()
    if re.fullmatch(r"PART\s+[IVXLC]+", upper):
        return HeadingInference(1, 1.0, ["part_heading"])
    if upper in {"SIGNATURES", "EXHIBIT INDEX", "INDEX TO CONSOLIDATED FINANCIAL STATEMENTS"}:
        return HeadingInference(1, 1.0, ["major_heading"])
    if re.match(r"^ITEM\s+\d+[A-Z]?\.?\s+\S", upper):
        return HeadingInference(2, 1.0, ["item_heading"])
    if re.match(r"^ITEM\s+\d+[A-Z]?\.?$", upper):
        return HeadingInference(2, 1.0, ["item_heading"])
    if re.match(r"^CONSOLIDATED\s+(STATEMENTS?|BALANCE SHEETS?)\b", upper):
        return HeadingInference(2, 0.98, ["financial_statement_heading"])
    if upper.startswith("NOTES TO CONSOLIDATED FINANCIAL STATEMENTS"):
        return HeadingInference(2, 0.98, ["notes_heading"])
    if not allow_visual:
        return None
    if state.get("proxy_filing") and normalized == "Table of Contents":
        if "toc" in _node_anchor_ids(node) and (_node_font_size(node) or 0.0) >= 18:
            return HeadingInference(1, 0.99, ["proxy_toc_title"], _style_signature(node))
        return None
    if state.get("proxy_filing") and normalized in PROXY_COVER_TEXT:
        return None
    proxy_entry = _proxy_toc_entry_for_node(node, state)
    if proxy_entry:
        return HeadingInference(int(proxy_entry["level"]), 0.99, ["proxy_toc_anchor"], _style_signature(node))

    visual = _visual_heading_features(node, normalized, state)
    reasons = list(visual["reasons"])
    style_signature = visual["style_signature"]
    proxy_level = _proxy_heading_level(node, normalized, state, visual)
    if proxy_level:
        return HeadingInference(proxy_level, 0.94, ["proxy_visual_heading", *reasons], style_signature)

    style_levels = state.get("style_heading_levels", {})
    propagated_level = style_levels.get((state.get("current_section") or "", style_signature))
    if propagated_level and visual["score"] >= 3.0:
        return HeadingInference(propagated_level, 0.9, ["same_style_as_prior_heading", *reasons], style_signature)
    if visual["score"] >= 4.5:
        return HeadingInference(3, min(0.92, 0.72 + visual["score"] / 20), reasons, style_signature)
    if not state.get("proxy_filing") and _is_visual_heading(node, normalized):
        return HeadingInference(3, 0.86, ["legacy_visual_heading", *reasons], style_signature)
    return None



def _is_proxy_filing(filing_metadata: dict) -> bool:
    filing_type = str(filing_metadata.get("filing_type") or "").upper()
    filename = str(filing_metadata.get("filename") or "").lower()
    return "14A" in filing_type or "def14" in filename or "pre14" in filename



def _build_proxy_outline(body: Node) -> dict[str, dict[str, Any]]:
    outline: dict[str, dict[str, Any]] = {}
    order = 0
    for table in _descendants(body, {"table"}):
        links = _proxy_links_in_node(table)
        if len(links) < 3:
            continue
        if not _is_proxy_toc_table(table):
            continue
        for link in links:
            href = _clean_anchor_id(link.attrs.get("href", ""))
            if not href:
                continue
            title = _clean_heading_text(_node_text(link))
            if not _valid_proxy_toc_title(title):
                continue
            level = _proxy_toc_link_level(link)
            existing = outline.get(href)
            if not existing or level < int(existing.get("level", 9)):
                outline[href] = {"anchor": href, "title": title, "level": level, "order": order}
            order += 1
    return outline


def _is_proxy_toc_table(node: Node) -> bool:
    links = _proxy_links_in_node(node)
    if len(links) < 3:
        return False
    valid_titles = [_clean_heading_text(_node_text(link)) for link in links if _valid_proxy_toc_title(_clean_heading_text(_node_text(link)))]
    if len(valid_titles) < 3:
        return False
    text = _node_text(node)
    has_page_numbers = bool(re.search(r"\b\d{1,3}\b", text))
    has_toc_words = any(word in text for word in ("Proxy Statement", "Corporate Governance", "Executive Compensation", "Shareholder"))
    return has_page_numbers or has_toc_words


def _proxy_links_in_node(node: Node) -> list[Node]:
    links: list[Node] = []
    if node.tag == "a" and _clean_anchor_id(node.attrs.get("href", "")):
        links.append(node)
    for child in node.children:
        links.extend(_proxy_links_in_node(child))
    return links


def _valid_proxy_toc_title(title: str) -> bool:
    if not title or title.isdigit() or len(title) < 3:
        return False
    if title in PROXY_COVER_TEXT:
        return False
    if title in {"Summary", "Governance", "Directors", "Compensation", "Proposals", "Other Information"}:
        return False
    if re.fullmatch(r"\d{1,3}", title):
        return False
    return True


def _is_proxy_running_toc_link(node: Node, text: str) -> bool:
    if _clean_heading_text(text) != "Table of Contents":
        return False
    if "toc" in _node_anchor_ids(node):
        return False
    links = _proxy_links_in_node(node)
    if not any(_clean_anchor_id(link.attrs.get("href", "")) == "toc" for link in links):
        return False
    return (_node_font_size(node) or 0.0) <= 10


def _proxy_toc_link_level(link: Node) -> int:
    if _has_bold_descendant(link):
        return 1
    if _ancestor_style_contains(link, "padding-left"):
        return 2
    font_size = _node_font_size(link) or 0.0
    if font_size >= 9.5:
        return 1
    return 2


def _ancestor_style_contains(node: Node, token: str) -> bool:
    current: Node | None = node
    while current:
        if token.lower() in current.attrs.get("style", "").lower():
            return True
        current = current.parent
    return False


def _proxy_toc_entry_for_node(node: Node, state: dict[str, Any]) -> dict[str, Any] | None:
    outline = state.get("proxy_outline") or {}
    if not outline:
        return None
    for anchor_id in _node_anchor_ids(node):
        entry = outline.get(anchor_id)
        if entry:
            return entry
    return None


def _proxy_heading_from_table(node: Node, state: dict[str, Any]) -> dict[str, Any] | None:
    outline = state.get("proxy_outline") or {}
    if not outline:
        return None
    table_text = _clean_heading_text(_node_text(node))
    for anchor_id in _node_anchor_ids(node):
        entry = outline.get(anchor_id)
        if not entry:
            continue
        title = str(entry.get("title") or "")
        if title and title in table_text:
            return entry
    return None


def _node_anchor_ids(node: Node) -> list[str]:
    ids: list[str] = []
    for attr in ("id", "name"):
        anchor_id = _clean_anchor_id(node.attrs.get(attr, ""))
        if anchor_id:
            ids.append(anchor_id)
    for child in node.children:
        ids.extend(_node_anchor_ids(child))
    return ids


def _clean_anchor_id(value: str) -> str:
    value = (value or "").strip()
    if not value.startswith("#") and "#" not in value and value and re.match(r"^[A-Za-z0-9_\-:.]+$", value):
        return value.lower()
    if "#" in value:
        value = value.rsplit("#", 1)[-1]
    else:
        value = value.lstrip("#")
    return value.strip().lower()


def _proxy_heading_level(node: Node, text: str, state: dict[str, Any], visual: dict[str, Any]) -> int | None:
    if not state.get("proxy_filing"):
        return None
    if text in PROXY_COVER_TEXT:
        return None
    font_size = _node_font_size(node) or 0.0
    bold = _has_bold_descendant(node)
    anchored = _has_anchor_id(node)
    known = text in PROXY_MAJOR_HEADINGS
    if text in PROXY_COVER_TEXT and not anchored:
        return None
    if not (anchored or known or (bold and font_size >= 14)):
        return None
    if visual.get("score", 0.0) < 2.0 and not known:
        return None
    if font_size >= 24:
        return 1
    if font_size >= 15 or known:
        return 2
    if font_size >= 11.5:
        return 3
    return None


def _has_anchor_id(node: Node) -> bool:
    if node.attrs.get("id"):
        return True
    if node.tag == "a" and node.attrs.get("name"):
        return True
    return any(_has_anchor_id(child) for child in node.children)

def _clean_heading_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" .")


def _looks_like_toc_entry(text: str) -> bool:
    if re.match(r"^Item\s+\d+[A-Z]?\.?\s+.+\s+\d+$", text, re.IGNORECASE):
        return True
    return False


def _style_baseline(root: Node) -> dict[str, float | None]:
    font_sizes: list[float] = []
    for node in _iter_nodes(root):
        if node.tag not in {"p", "div"} or _has_block_child(node):
            continue
        text = _node_text(node)
        if len(text) < 80:
            continue
        size = _node_font_size(node)
        if size is not None:
            font_sizes.append(size)
    return {"font_size": _mode_number(font_sizes)}


def _iter_nodes(node: Node):
    yield node
    for child in node.children:
        yield from _iter_nodes(child)


def _mode_number(values: list[float]) -> float | None:
    if not values:
        return None
    buckets: dict[float, int] = {}
    for value in values:
        bucket = round(value, 1)
        buckets[bucket] = buckets.get(bucket, 0) + 1
    return max(buckets.items(), key=lambda item: item[1])[0]


def _visual_heading_features(node: Node, text: str, state: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    score = 0.0
    words = text.split()
    if not 1 <= len(words) <= 10 or len(text) > 110:
        return {"score": 0.0, "reasons": [], "style_signature": _style_signature(node)}
    if text.endswith((".", ";", ":")) and not re.search(r"[()/]", text):
        return {"score": 0.0, "reasons": [], "style_signature": _style_signature(node)}
    if _is_inside_table(node):
        return {"score": 0.0, "reasons": [], "style_signature": _style_signature(node)}

    score += 1.0
    reasons.append("short_standalone_text")
    margin_top = _node_margin_top(node)
    if margin_top >= 12:
        score += 1.5
        reasons.append("margin_top_large")
    elif margin_top >= 6:
        score += 0.5
        reasons.append("margin_top_medium")
    if _has_bold_descendant(node):
        score += 1.0
        reasons.append("bold")
    if _has_italic_descendant(node):
        score += 1.0
        reasons.append("italic")
    font_size = _node_font_size(node)
    baseline_size = (state.get("baseline_style") or {}).get("font_size")
    if font_size is not None and baseline_size is not None and font_size > baseline_size + 0.2:
        score += 1.0
        reasons.append("font_size_above_body")
    if _followed_by_paragraph(node):
        score += 1.0
        reasons.append("followed_by_paragraph")
    class_name = node.attrs.get("class", "").lower()
    if any(token in class_name for token in ("heading", "title", "subtitle")):
        score += 1.0
        reasons.append("heading_class")
    return {"score": score, "reasons": reasons, "style_signature": _style_signature(node)}


def _style_signature(node: Node) -> str:
    font_size = _node_font_size(node)
    font_size_part = f"{font_size:.1f}" if font_size is not None else "none"
    weight = "bold" if _has_bold_descendant(node) else (_first_style_value(node, "font-weight") or "normal")
    font_style = "italic" if _has_italic_descendant(node) else "normal"
    margin = _node_margin_top(node)
    margin_bucket = "large" if margin >= 12 else "medium" if margin >= 6 else "small" if margin > 0 else "none"
    align = _style_value(node.attrs.get("style", ""), "text-align") or "none"
    return f"fs={font_size_part}|weight={weight}|style={font_style}|mt={margin_bucket}|align={align}"


def _node_margin_top(node: Node) -> float:
    return _parse_css_size(_style_value(node.attrs.get("style", ""), "margin-top")) or 0.0


def _node_font_size(node: Node) -> float | None:
    value = _first_style_value(node, "font-size")
    if value:
        return _parse_css_size(value)
    value = _first_font_shorthand_size(node)
    return _parse_css_size(value)



def _first_font_shorthand_size(node: Node) -> str | None:
    value = _font_shorthand_size(node.attrs.get("style", ""))
    if value:
        return value
    for child in node.children:
        value = _first_font_shorthand_size(child)
        if value:
            return value
    return None


def _font_shorthand_size(style: str) -> str | None:
    match = re.search(r"(?:^|;)\s*font\s*:\s*[^;]*?(\d+(?:\.\d+)?\s*(?:pt|px|em|rem|%))", style, re.IGNORECASE)
    return match.group(1) if match else None

def _first_style_value(node: Node, prop: str) -> str | None:
    value = _style_value(node.attrs.get("style", ""), prop)
    if value:
        return value
    for child in node.children:
        value = _first_style_value(child, prop)
        if value:
            return value
    return None


def _style_value(style: str, prop: str) -> str | None:
    match = re.search(rf"(?:^|;)\s*{re.escape(prop)}\s*:\s*([^;]+)", style, re.IGNORECASE)
    return match.group(1).strip().lower() if match else None


def _parse_css_size(value: str | None) -> float | None:
    if not value:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", value)
    return float(match.group(0)) if match else None


def _has_italic_descendant(node: Node) -> bool:
    if node.tag in {"i", "em"}:
        return True
    style = node.attrs.get("style", "").lower().replace(" ", "")
    if "font-style:italic" in style:
        return True
    return any(_has_italic_descendant(child) for child in node.children)


def _followed_by_paragraph(node: Node) -> bool:
    if not node.parent:
        return False
    siblings = node.parent.children
    start = None
    for index, sibling in enumerate(siblings):
        if sibling is node:
            start = index + 1
            break
    if start is None:
        return False
    for sibling in siblings[start:]:
        if sibling.tag in {"hr", "br"}:
            continue
        if _hidden_or_metadata_reason(sibling):
            continue
        if sibling.tag == "table":
            return False
        if sibling.tag in {"p", "div"} and not _has_block_child(sibling):
            text = _node_text(sibling)
            if not text:
                continue
            return len(text) > 45 or text.endswith(".")
        if _node_text(sibling):
            return False
    return False


def _is_inside_table(node: Node) -> bool:
    current = node.parent
    while current:
        if current.tag in {"table", "thead", "tbody", "tfoot", "tr", "td", "th"}:
            return True
        current = current.parent
    return False


def _is_visual_heading(node: Node, text: str) -> bool:
    if len(text) > 95 or text.count(".") > 1:
        return False
    words = text.split()
    if not 1 <= len(words) <= 8:
        return False
    if re.search(r"\d", text) and not re.search(r"[A-Za-z]{3,}", text):
        return False
    class_name = node.attrs.get("class", "").lower()
    class_heading = any(token in class_name for token in ("heading", "title", "subtitle"))
    return class_heading or _has_bold_descendant(node)


def _has_bold_descendant(node: Node) -> bool:
    if node.tag in {"b", "strong"}:
        return True
    style = node.attrs.get("style", "").lower().replace(" ", "")
    if any(token in style for token in ("font-weight:bold", "font-weight:700", "font-weight:600")):
        return True
    return any(_has_bold_descendant(child) for child in node.children)




















