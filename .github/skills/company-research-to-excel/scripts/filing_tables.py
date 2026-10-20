"""Native filing table extraction. Never compact individual rows or infer periods.

Indices refer to physical HTML table/tr/td elements, all zero based. The export
auditor reopens the original with a different parser; this module is not its oracle.
"""
from __future__ import annotations

import hashlib
import json
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

from model_contract import ALLOWED_FORMS


def visible_text(value):
    return re.sub(r"\s+", " ", unescape(value).replace("\xa0", " ")).strip()


def document_type(html):
    match = re.search(
        r'<(?:ix:)?nonNumeric\b[^>]*\bname\s*=\s*[\'"]dei:DocumentType[\'"][^>]*>(.*?)</(?:ix:)?nonNumeric>',
        html, re.I | re.S,
    )
    if match:
        return visible_text(re.sub(r"<[^>]*>", "", match[1])).upper()
    match = re.search(r"<TYPE>\s*(10-[KQ](?:/A)?)\s*(?:\r?\n|<)", html, re.I)
    return match[1].upper() if match else None


def source_record(path, workspace, metadata=None):
    path, workspace = path.resolve(), workspace.resolve()
    relative = path.relative_to(workspace).as_posix()
    raw = path.read_bytes()
    html = raw.decode("utf-8", errors="replace")
    meta = dict(metadata or {})
    detected = document_type(html)
    declared = meta.get("filing_type") or meta.get("form")
    if detected and declared and detected != declared:
        raise ValueError(f"Original form {detected} conflicts with manifest {declared}: {relative}")
    form = detected or declared
    if form not in ALLOWED_FORMS:
        raise ValueError(f"Cannot positively identify a 10-K/10-Q original: {relative} ({form})")
    digest = hashlib.sha256(raw).hexdigest()
    record = {**meta, "source_id": meta.get("source_id") or f"F_{digest[:16]}",
              "path": relative, "sha256": digest, "filing_type": form,
              "form_detection": "native_document" if detected else "manifest_pending_audit"}
    return record, html


class NativeTables(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.tables, self.count = [], [], 0
        self.hidden = []

    def handle_starttag(self, tag, attrs):
        tag, attrs = tag.lower(), dict(attrs)
        if tag in {"sup", "script", "style", "ix:hidden"}:
            self.hidden.append(tag)
        if tag == "table":
            if self.stack:
                self.stack[-1]["nested"] = True
            self.stack.append({"index": self.count, "rows": [], "row": None,
                               "cell": None, "nested": False, "line": self.getpos()[0]})
            self.count += 1
        if not self.stack:
            return
        table = self.stack[-1]
        if tag == "tr":
            table["row"] = []
            table["rows"].append(table["row"])
        elif tag in {"td", "th"} and table["row"] is not None:
            rowspan, colspan = int(attrs.get("rowspan", 1)), int(attrs.get("colspan", 1))
            if not 1 <= rowspan <= 1000 or not 1 <= colspan <= 1000:
                raise ValueError("Unsupported native span; review original row-group geometry explicitly")
            cell = {"parts": [], "rowspan": rowspan, "colspan": colspan, "facts": []}
            table["row"].append(cell)
            table["cell"] = cell
        elif tag.startswith("ix:") and table["cell"] is not None:
            if tag in {"ix:nonfraction", "ix:nonnumeric"}:
                table["cell"]["facts"].append(attrs)
        elif tag == "br" and table["cell"] is not None:
            table["cell"]["parts"].append(" ")

    def handle_data(self, data):
        if self.stack and not self.hidden and self.stack[-1]["cell"] is not None:
            self.stack[-1]["cell"]["parts"].append(data)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self.hidden:
            self.hidden.remove(tag)
        if not self.stack:
            return
        table = self.stack[-1]
        if tag in {"td", "th"}:
            table["cell"] = None
        elif tag == "tr":
            table["row"] = None
        elif tag == "table":
            table = self.stack.pop()
            if not table["nested"]:
                table["end_line"] = self.getpos()[0]
                self.tables.append(table)


def extract_tables(html):
    parser = NativeTables()
    parser.feed(html)
    result = []
    for table in sorted(parser.tables, key=lambda t: t["index"]):
        occupied, evidence = {}, []
        for ri, row in enumerate(table["rows"]):
            ci = 0
            for physical_ci, cell in enumerate(row):
                while (ri, ci) in occupied:
                    ci += 1
                text = visible_text("".join(cell["parts"]))
                for dr in range(cell["rowspan"]):
                    for dc in range(cell["colspan"]):
                        occupied[ri + dr, ci + dc] = text
                evidence.append({"row": ri, "column": ci, "raw_text": text,
                                 "html_table_index": table["index"], "html_row_index": ri,
                                 "html_cell_index": physical_ci, "facts": cell["facts"],
                                 "rowspan": cell["rowspan"], "colspan": cell["colspan"]})
                ci += cell["colspan"]
        if not occupied:
            continue
        height = max(r for r, _ in occupied) + 1
        width = max(c for _, c in occupied) + 1
        grid = [[occupied.get((r, c), "") for c in range(width)] for r in range(height)]
        if not any(any(cell for cell in row) for row in grid):
            continue
        result.append({"index": table["index"], "grid": grid, "evidence": evidence,
                       "start_line": table["line"], "end_line": table["end_line"]})
    return result


def read_manifest(path):
    """Explicit manifest: {sources: [{path, filing_type, filing_date, url, ...}]}.

    Paths are Workspace-relative. A folder name never establishes the SEC form.
    """
    if not path:
        return {}
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    return {item["path"]: item for item in obj.get("sources", [])}
