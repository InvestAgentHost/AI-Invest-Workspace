#!/usr/bin/env python3
"""Collect prepared company-research tables into an Artifact Tool-ready JSON bundle."""

from __future__ import annotations

import argparse
import csv
import fnmatch
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


SKIP_PARTS = {
    "raw", "cache", ".cache", "browser", "indexes", "databases", ".git",
    "runs", "artifacts", "transcripts", "pdf-text", "foreign_reports_text",
    "independent_opinions_clean",
}
SKIP_FILES = {
    "research-context.md", "coverage-matrix.md", "source-index.md", "release-review.md",
    "validation-log.md", "acquisition-attempt-log.md", "evidence-ledger.md", "materials.md",
}
MISSING_MARKERS = {
    "-", "--", "---", "—", "–", "n.a.", "n.a", "na", "n/m", "n.m.", "n.m",
    "unavailable", "not disclosed", "not_disclosed", "not applicable", "not_applicable",
}
NUMBER_RE = re.compile(r"^[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?$")
PERCENT_RE = re.compile(r"^[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MD_SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")


@dataclass
class Table:
    source: str
    sha256: str
    title: str
    headers: list[str]
    rows: list[list[Any]]
    heading: str = ""
    start_line: int | None = None
    end_line: int | None = None
    kind: str = "table"
    typed_cells: list[dict[str, Any]] = field(default_factory=list)
    table_id: str = ""
    topic_hint: str = "other_notes"
    row_count: int = 0
    column_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    cell_evidence: list[dict[str, Any]] = field(default_factory=list)
    orientation: str = "metric_by_period"


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = unescape(str(value)).replace("\xa0", " ")
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^(?:\*\*|__|`)+|(?:\*\*|__|`)+$", "", text).strip()
    return text


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative_source(path: Path, workspace: Path) -> str:
    try:
        return path.resolve().relative_to(workspace.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def normalize_grid(rows: list[list[Any]]) -> list[list[Any]]:
    width = max((len(row) for row in rows), default=0)
    return [list(row) + [""] * (width - len(row)) for row in rows]


PERIOD_HEADER_RE = re.compile(
    r"^(?:period|date|fiscal(?: period| year)?|quarter|year|month|week|ltm|ttm)$"
    r"|\b(?:fy|q[1-4]|[1-4]q|h[12]|ended|year|quarter|month|week|ltm|ttm)\b"
    r"|\b20\d{2}\b",
    re.I,
)
PERIOD_VALUE_RE = re.compile(
    r"^(?:FY\d{2,4}(?:[/\-]\d{2,4})?|(?:[1-4]Q|Q[1-4])?FY\d{2,4}(?:[/\-]\d{2,4})?|"
    r"(?:[1-4]Q|Q[1-4])\s*\d{2,4}|(?:19|20)\d{2}(?:[-/]\d{1,2})?)$",
    re.I,
)


def period_like(value: Any) -> bool:
    text = clean_text(value)
    return bool(text) and (
        ISO_DATE_RE.match(text) is not None
        or PERIOD_HEADER_RE.search(text) is not None
        or PERIOD_VALUE_RE.match(text) is not None
        or re.fullmatch(r"(?:19|20)\d{2}(?:[-/]\d{1,2})?", text) is not None
    )


def normalize_orientation(table: Table) -> Table:
    """Normalize an unambiguous period-by-row table into metric-by-period form."""
    if len(table.headers) < 2 or not table.rows:
        return table
    first_header = clean_text(table.headers[0]).lower()
    period_column = first_header in {"period", "date", "fiscal", "fiscal period", "quarter", "year"}
    period_rows = sum(1 for row in table.rows if row and period_like(row[0]))
    if not period_column or period_rows < max(2, len(table.rows) // 2):
        return table

    periods = [clean_text(row[0]) for row in table.rows if row and clean_text(row[0])]
    if len(periods) != len(set(periods)):
        return table
    transposed_rows = []
    for column_index, header in enumerate(table.headers[1:], start=1):
        transposed_rows.append([
            clean_text(header),
            *[row[column_index] if column_index < len(row) else "" for row in table.rows],
        ])
    table.headers = ["metric", *periods]
    table.rows = transposed_rows
    table.orientation = "transposed_to_metric_by_period"
    table.metadata["source_orientation"] = "period_by_metric"
    table.metadata["orientation_transform"] = "transpose_period_rows_to_metric_rows"
    return table


def typed_value(value: Any, header: str = "") -> tuple[Any, str | None, str | None]:
    if value is None or isinstance(value, bool):
        return value, None, None
    if isinstance(value, (int, float)):
        return value, "number", "#,##0.0;(#,##0.0);-"
    text = clean_text(value)
    if not text or text.lower() in MISSING_MARKERS:
        return text, None, None
    if ISO_DATE_RE.match(text):
        return text, "date", "yyyy-mm-dd"
    negative = text.startswith("(") and text.endswith(")")
    core = text[1:-1].strip() if negative else text
    core = re.sub(r"^(?:US\$|S\$|HK\$|A\$|C\$|[$€£¥])\s*", "", core)
    if PERCENT_RE.match(core):
        number = float(core[:-1].replace(",", "")) / 100.0
        return (-number if negative else number), "percentage", "0.0%"
    if NUMBER_RE.match(core):
        number = float(core.replace(",", ""))
        if negative:
            number = -number
        return (int(number) if number.is_integer() else number), "number", "#,##0.0;(#,##0.0);-"
    return text, None, None


def type_table(table: Table) -> Table:
    typed_rows: list[list[Any]] = []
    typed_cells: list[dict[str, Any]] = []
    for row_index, row in enumerate(table.rows):
        typed_row = []
        for column_index, raw in enumerate(row):
            header = table.headers[column_index] if column_index < len(table.headers) else ""
            value, cell_type, number_format = typed_value(raw, header)
            typed_row.append(value)
            if cell_type:
                typed_cells.append({
                    "row": row_index,
                    "column": column_index,
                    "type": cell_type,
                    "number_format": number_format,
                })
        typed_rows.append(typed_row)
    table.rows = typed_rows
    table.typed_cells = typed_cells
    table.row_count = len(typed_rows)
    table.column_count = len(table.headers)
    return table


def classify_topic(table: Table) -> str:
    title_text = re.sub(r"[_-]+", " ", " ".join((table.title, table.heading))).lower()
    labels = " ".join(
        clean_text(item)
        for row in table.rows[:40]
        for item in row[:4]
        if isinstance(item, str)
    )
    text = re.sub(
        r"[_-]+", " ",
        " ".join((table.title, table.heading, " ".join(table.headers), labels)),
    ).lower()
    title_rules = [
        ("segments", r"\bsegment(?:s|ed)?\b|reportable segment|分部|分部门"),
        ("products_geography", r"geograph|country|region|product|service mix|end market|customer type|channel mix|地区|区域|产品|服务"),
        ("operating_kpis", r"\bkpis?\b|operational|gross booking|backlog|order|subscriber|utilization|capacity|运营|订单|用户|产能|利用率"),
        ("financials", r"financial[-_ ]?(?:time ?series|data panel)|income statement|statement of operations|balance sheet|cash flow statement|adjusted ebitda|non.?gaap|reconciliation|\brevenue\b|利润表|资产负债表|现金流量表|合并报表"),
        ("capital_returns", r"free cash flow|capital allocation|dividend|repurchase|buyback|资本配置|股息|回购"),
    ]
    for topic, pattern in title_rules:
        if re.search(pattern, title_text, re.I):
            return topic
    rules = [
        ("segments", r"\bsegment(?:s|ed)?\b|reportable segment|分部|分部门"),
        ("products_geography", r"geograph|country|region|product|service mix|end market|customer type|channel mix|地区|区域|产品|服务"),
        ("debt_liquidity", r"debt|borrow|liquidity|maturit|credit facilit|covenant|lease liabilit|债务|借款|流动性|到期"),
        ("assets_intangibles", r"goodwill|intangible|property.? plant|\bpp&e\b|\bppe\b|inventory|impairment|acquisition|商誉|无形资产|固定资产|存货|减值"),
        ("tax_shares", r"income tax|tax rate|deferred tax|stock.?based|share.?based|option|\brsu\b|equity roll|weighted average shares|所得税|股份支付|股权"),
        ("capital_returns", r"free cash flow|capex|capital expenditure|working capital|dividend|repurchase|buyback|share count|capital allocation|自由现金流|资本开支|营运资本|股息|回购"),
        ("financials", r"income statement|statement of operations|balance sheet|financial position|cash flow|profit or loss|non.?gaap|adjusted ebitda|reconciliation|利润表|资产负债表|现金流量表|合并报表"),
        ("operating_kpis", r"\bkpi\b|operational|booking|backlog|order|volume|unit|subscriber|user|member|utilization|capacity|store|headcount|运营|订单|销量|用户|产能|利用率"),
    ]
    for topic, pattern in rules:
        if re.search(pattern, text, re.I):
            return topic
    return "other_notes"


def md_cells(line: str) -> list[str]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    return [clean_text(cell.replace("\\|", "|")) for cell in re.split(r"(?<!\\)\|", text)]


def heading_context(lines: list[str]) -> dict[int, str]:
    stack: list[tuple[int, str]] = []
    result: dict[int, str] = {}
    for number, line in enumerate(lines, 1):
        match = re.match(r"^\s*(#{1,6})\s+(.+?)\s*$", line)
        if match:
            level = len(match.group(1))
            title = clean_text(match.group(2))
            stack = [item for item in stack if item[0] < level]
            stack.append((level, title))
        result[number] = " > ".join(title for _, title in stack)
    return result


def nearby_title(lines: list[str], start_line: int, fallback: str) -> str:
    for index in range(start_line - 2, max(-1, start_line - 42), -1):
        raw = lines[index]
        candidate = clean_text(re.sub(r"<[^>]+>", " ", raw))
        if not candidate or candidate.startswith("|"):
            continue
        if candidate.lower().strip("()") == "unaudited" or re.fullmatch(r"[\W_]+", candidate):
            continue
        if 3 <= len(candidate) <= 140:
            return candidate
    return fallback


def compact_row(cells: list[str]) -> list[str]:
    """Merge fragmented SEC HTML cells: '$' + '1,234' → '$1,234', etc."""
    cleaned = [clean_text(c) for c in cells]
    merged: list[str] = []
    i = 0
    while i < len(cleaned):
        cell = cleaned[i]
        if cell in ("$", "US$") and i + 1 < len(cleaned) and cleaned[i + 1]:
            merged.append(f"{cell}{cleaned[i + 1]}")
            i += 2
            continue
        if cell == "%" and merged:
            merged[-1] = f"{merged[-1]}%"
            i += 1
            continue
        if cell == "(" and i + 1 < len(cleaned):
            close_idx = i + 2
            if close_idx < len(cleaned) and cleaned[close_idx] == ")":
                merged.append(f"({cleaned[i + 1]})")
                i += 3
            else:
                merged.append(f"({cleaned[i + 1]}")
                i += 2
            continue
        if cell == ")" and merged:
            merged[-1] = f"{merged[-1]})"
            i += 1
            continue
        merged.append(cell)
        i += 1
    return [c for c in merged if c]


class ResearchHTMLTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.tables: list[dict[str, Any]] = []
        self.current: dict[str, Any] | None = None
        self.row: list[str] | None = None
        self.cell: list[str] | None = None
        self.colspan = 1

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "table":
            self.depth += 1
            if self.depth == 1:
                self.current = {"start": self.getpos()[0], "end": self.getpos()[0], "rows": []}
        elif self.depth == 1 and tag == "tr":
            self.row = []
        elif self.depth == 1 and tag in {"td", "th"} and self.row is not None:
            self.cell = []
            attrs_dict = dict(attrs)
            try:
                self.colspan = max(1, int(attrs_dict.get("colspan") or 1))
            except ValueError:
                self.colspan = 1
        elif self.cell is not None and tag == "br":
            self.cell.append(" ")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self.depth == 1 and tag in {"td", "th"} and self.cell is not None and self.row is not None:
            self.row.append(clean_text("".join(self.cell)))
            self.row.extend([""] * (self.colspan - 1))
            self.cell = None
            self.colspan = 1
        elif self.depth == 1 and tag == "tr" and self.row is not None and self.current is not None:
            if any(cell for cell in self.row):
                self.current["rows"].append(self.row)
            self.row = None
        elif tag == "table" and self.depth:
            if self.depth == 1 and self.current is not None:
                self.current["end"] = self.getpos()[0]
                self.tables.append(self.current)
                self.current = None
            self.depth -= 1

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)


def parse_markdown(path: Path, source: str, digest: str) -> list[Table]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    headings = heading_context(lines)
    tables: list[Table] = []
    pipe_ranges: list[tuple[int, int]] = []
    index = 0
    while index + 1 < len(lines):
        if "|" in lines[index] and MD_SEP_RE.match(lines[index + 1]):
            start = index + 1
            grid = [md_cells(lines[index])]
            index += 2
            while index < len(lines) and "|" in lines[index] and lines[index].strip():
                grid.append(md_cells(lines[index]))
                index += 1
            grid = normalize_grid(grid)
            title = headings.get(start, "") or nearby_title(lines, start, f"Table {len(tables) + 1}")
            tables.append(Table(source, digest, title, grid[0], grid[1:], headings.get(start, ""), start, index, "markdown"))
            pipe_ranges.append((start, index))
            continue
        index += 1

    if "<table" in text.lower():
        parser = ResearchHTMLTableParser()
        parser.feed(text)
        for item in parser.tables:
            raw_rows = [compact_row(row) for row in item["rows"]]
            rows = normalize_grid(raw_rows)
            nonempty = sum(1 for row in rows for cell in row if cell)
            if len(rows) < 2 or len(rows[0]) < 2 or nonempty < 4:
                continue
            start, end = item["start"], item["end"]
            if any(first <= start <= last for first, last in pipe_ranges):
                continue
            heading = headings.get(start, "")
            title = heading or nearby_title(lines, start, f"HTML Table {len(tables) + 1}")
            tables.append(Table(source, digest, title, rows[0], rows[1:], heading, start, end, "html"))
    return sorted(tables, key=lambda table: table.start_line or 0)


def parse_delimited(path: Path, source: str, digest: str) -> list[Table]:
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        rows = list(csv.reader(handle, delimiter=delimiter))
    if not rows:
        return []
    rows = normalize_grid(rows)
    return [Table(source, digest, path.stem, [clean_text(item) for item in rows[0]], rows[1:], kind=path.suffix.lower()[1:])]


def scalar(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value:
        return value.get("value")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def records_table(source: str, digest: str, title: str, records: list[Any]) -> Table | None:
    records = [item for item in records if isinstance(item, dict)]
    if not records:
        return None
    headers: list[str] = []
    for item in records:
        for key in item:
            if str(key) not in headers:
                headers.append(str(key))
    rows = [[scalar(item.get(key)) for key in headers] for item in records]
    return Table(source, digest, title, headers, rows, kind="json")


def parse_financial_periods(source: str, digest: str, obj: dict[str, Any]) -> list[Table]:
    periods = obj.get("periods") or {}
    if not isinstance(periods, dict):
        return []
    order = [str(item) for item in (obj.get("period_order") or list(periods))]
    metrics: list[str] = []
    for period in order:
        values = (periods.get(period) or {}).get("values") or {}
        for metric in values:
            if metric not in metrics:
                metrics.append(metric)
    panel_rows = []
    evidence_rows = []
    source_labels: dict[str, str] = {}
    statements: dict[str, str] = {}
    for metric in metrics:
        row = [metric]
        for period in order:
            item = ((periods.get(period) or {}).get("values") or {}).get(metric)
            row.append(scalar(item))
            if isinstance(item, dict):
                if item.get("source_label"):
                    source_labels[metric] = str(item["source_label"])
                if item.get("statement"):
                    statements[metric] = str(item["statement"])
                evidence_rows.append([
                    period, metric, item.get("value"), item.get("source_label", ""),
                    item.get("statement", ""), item.get("source", ""), item.get("page", ""),
                    item.get("status", ""), item.get("mapping", ""), item.get("confidence", ""),
                    item.get("note", ""),
                ])
        panel_rows.append(row)
    panel_meta = {
        key: obj[key]
        for key in ("entity", "currency", "scale", "reporting_framework",
                    "fiscal_year_end", "consolidation_scope", "as_of_date")
        if obj.get(key)
    }
    result = [Table(
        source, digest, "Financial data panel", ["metric", *order], panel_rows,
        kind="financial-json",
        metadata={"source_labels": source_labels, "statements": statements,
                  "panel_meta": panel_meta},
    )]
    if evidence_rows:
        result.append(Table(
            source, digest, "Cell evidence",
            ["period", "metric", "value", "source_label", "statement", "source", "page", "status", "mapping", "confidence", "note"],
            evidence_rows, kind="evidence-json",
        ))
    return result


def parse_research_panel(source: str, digest: str, obj: dict[str, Any]) -> list[Table]:
    periods = obj.get("periods")
    rows = obj.get("rows")
    if not isinstance(periods, list) or not periods or not all(str(item).strip() for item in periods):
        raise ValueError("research_panel.v1 requires non-empty periods")
    period_labels = [str(item).strip() for item in periods]
    if len(period_labels) != len(set(period_labels)):
        raise ValueError("research_panel.v1 periods must be unique")
    if not isinstance(rows, list) or not rows:
        raise ValueError("research_panel.v1 requires non-empty rows")

    default_unit = clean_text(obj.get("default_unit"))
    panel_rows: list[list[Any]] = []
    cell_evidence: list[dict[str, Any]] = []
    status_markers = {
        "not_disclosed": "not disclosed",
        "not_comparable": "not comparable",
        "not_applicable": "not applicable",
    }
    for row_index, item in enumerate(rows):
        if not isinstance(item, dict):
            raise ValueError(f"research_panel.v1 row {row_index + 1} must be an object")
        label = clean_text(item.get("label") or item.get("metric_id"))
        if not label:
            raise ValueError(f"research_panel.v1 row {row_index + 1} has no label")
        values = item.get("values")
        if not isinstance(values, list):
            raise ValueError(f"research_panel.v1 row {row_index + 1} has invalid values")
        values_by_period: dict[str, dict[str, Any]] = {}
        for entry in values:
            if not isinstance(entry, dict):
                raise ValueError(f"research_panel.v1 row {row_index + 1} contains an invalid value")
            period = str(entry.get("period") or "").strip()
            if not period or period not in period_labels:
                raise ValueError(f"research_panel.v1 row {row_index + 1} has an unknown period: {period}")
            if period in values_by_period:
                raise ValueError(f"research_panel.v1 row {row_index + 1} repeats period: {period}")
            values_by_period[period] = entry

        output_row: list[Any] = [
            clean_text(item.get("section")),
            label,
            clean_text(item.get("scope")),
            clean_text(item.get("unit")) or default_unit,
        ]
        for period_index, period in enumerate(period_labels):
            entry = values_by_period.get(period)
            if entry is None:
                output_row.append("")
                continue
            status = str(entry.get("status") or "").strip()
            value = entry.get("value")
            output_row.append(status_markers.get(status, scalar(value)))
            cell_evidence.append({
                "row": row_index,
                "column": 4 + period_index,
                "period": period,
                "status": status,
                "formula": entry.get("formula"),
                "note": entry.get("note"),
                "source_refs": entry.get("source_refs") or [],
            })
        panel_rows.append(output_row)

    metadata = {
        "schema_version": "research_panel.v1",
        "panel_id": obj.get("panel_id"),
        "panel_type": obj.get("panel_type"),
        "default_unit": obj.get("default_unit"),
        "comparability_notes": obj.get("comparability_notes") or [],
        "missing_periods": obj.get("missing_periods") or [],
    }
    return [Table(
        source=source,
        sha256=digest,
        title=clean_text(obj.get("title")) or clean_text(obj.get("panel_id")) or "Research panel",
        headers=["section", "metric", "scope", "unit", *period_labels],
        rows=panel_rows,
        heading=clean_text(obj.get("panel_type")),
        kind="research-panel",
        metadata=metadata,
        cell_evidence=cell_evidence,
    )]


def parse_json(path: Path, source: str, digest: str) -> list[Table]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(obj, dict) and obj.get("schema_version") == "research_panel.v1":
        return parse_research_panel(source, digest, obj)
    if isinstance(obj, dict) and all(key in obj for key in ("company", "periods", "sheets")):
        raise ValueError("Structured forecast/model specifications are outside this export skill; provide cleaned actual-data panels")
    if isinstance(obj, dict) and isinstance(obj.get("periods"), dict):
        financial = parse_financial_periods(source, digest, obj)
        if financial and financial[0].rows:
            return financial
    if isinstance(obj, list):
        table = records_table(source, digest, path.stem, obj)
        return [table] if table else []
    tables: list[Table] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, list):
                table = records_table(source, digest, str(key), value)
                if table:
                    tables.append(table)
        if not tables:
            tables.append(Table(
                source, digest, path.stem, ["field", "value"],
                [[key, scalar(value)] for key, value in obj.items()], kind="json-map",
            ))
    return tables


def parse_sec_html(dir_path: Path, workspace: Path) -> list[Table]:
    """Parse SEC filing source HTML (iXBRL) to extract financial tables."""
    source_html = dir_path / "source.html"
    if not source_html.is_file():
        source_html = dir_path / "raw" / "source.html"
    if not source_html.is_file():
        return []

    html_content = source_html.read_text(encoding="utf-8", errors="replace")
    source = relative_source(source_html, workspace)
    digest = sha256(source_html)
    lines = html_content.splitlines()

    parser = ResearchHTMLTableParser()
    parser.feed(html_content)

    tables: list[Table] = []
    for item in parser.tables:
        raw_rows = [compact_row(row) for row in item["rows"]]
        rows = normalize_grid(raw_rows)
        nonempty = sum(1 for row in rows for cell in row if cell)
        if len(rows) < 2 or len(rows[0]) < 2 or nonempty < 4:
            continue
        start, end = item["start"], item["end"]
        title = nearby_title(lines, start, f"SEC Table {len(tables) + 1}")
        tables.append(Table(
            source=source,
            sha256=digest,
            title=title,
            headers=rows[0],
            rows=rows[1:],
            heading="",
            start_line=start,
            end_line=end,
            kind="sec-html",
        ))

    return sorted(tables, key=lambda t: t.start_line or 0)


def discover_files(input_path: Path, includes: list[str], excludes: list[str]) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    root = input_path / "data" if (input_path / "data").is_dir() else input_path
    allowed = {".csv", ".tsv", ".md", ".json"}
    files = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in allowed:
            continue
        relative = path.relative_to(input_path).as_posix()
        if any(fnmatch.fnmatch(relative, pattern) or path.match(pattern) for pattern in excludes):
            continue
        if includes:
            if not any(fnmatch.fnmatch(relative, pattern) or path.match(pattern) for pattern in includes):
                continue
        else:
            if any(part.lower() in SKIP_PARTS for part in path.relative_to(root).parts):
                continue
            if path.name.lower() in SKIP_FILES:
                continue
        files.append(path)
    return sorted(files, key=lambda item: item.as_posix().lower())


def select_tables(tables: list[Table], table_patterns: list[str], period_patterns: list[str]) -> tuple[list[Table], list[str]]:
    warnings: list[str] = []
    table_re = [re.compile(pattern, re.I) for pattern in table_patterns]
    selected = [
        table for table in tables
        if not table_re or any(pattern.search(" | ".join((table.source, table.heading, table.title))) for pattern in table_re)
    ]
    if not period_patterns:
        return selected, warnings
    period_re = [re.compile(pattern, re.I) for pattern in period_patterns]
    filtered: list[Table] = []
    for table in selected:
        columns = [index for index, header in enumerate(table.headers) if any(pattern.fullmatch(str(header)) for pattern in period_re)]
        if columns:
            keep = sorted(set([0, *columns, *[
                index for index, header in enumerate(table.headers)
                if re.search(
                    r"section|metric|label|name|description|scope|unit|currency|basis|"
                    r"source|url|page|locator|note|status|formula|definition",
                    str(header), re.I,
                )
            ]]))
            column_map = {old: new for new, old in enumerate(keep)}
            table.headers = [table.headers[index] for index in keep]
            table.rows = [[row[index] if index < len(row) else "" for index in keep] for row in table.rows]
            table.cell_evidence = [
                {**item, "column": column_map[item["column"]]}
                for item in table.cell_evidence
                if item.get("column") in column_map
            ]
            filtered.append(table)
            continue
        period_columns = [
            index for index, header in enumerate(table.headers)
            if re.search(r"period|date|fiscal|quarter|year", str(header), re.I)
        ] or [0]
        matching_rows = [
            (row_index, row) for row_index, row in enumerate(table.rows)
            if any(
                pattern.fullmatch(str(row[index]))
                for index in period_columns if index < len(row)
                for pattern in period_re
            )
        ]
        if matching_rows:
            row_map = {old: new for new, (old, _) in enumerate(matching_rows)}
            table.rows = [row for _, row in matching_rows]
            table.cell_evidence = [
                {**item, "row": row_map[item["row"]]}
                for item in table.cell_evidence
                if item.get("row") in row_map
            ]
            filtered.append(table)
        else:
            warnings.append(f"No period match in {table.source}: {table.title}")
    return filtered, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input", type=Path, nargs="*",
        help="One or more prepared files, curated company directories, or company research directories",
    )
    parser.add_argument("--output", type=Path, required=True, help="Output bundle JSON")
    parser.add_argument("--include", action="append", default=[], help="Repeatable glob relative to input root")
    parser.add_argument("--exclude", action="append", default=[], help="Repeatable exclusion glob relative to input root")
    parser.add_argument("--table", action="append", default=[], help="Repeatable regex for source/title/heading")
    parser.add_argument("--period", action="append", default=[], help="Repeatable regex for period columns or rows")
    parser.add_argument(
        "--sec-source", type=Path, action="append", default=[], dest="sec_source",
        help="SEC source directory containing source.html (e.g., sources/.../sec/10-k-2025/)",
    )
    parser.add_argument("--strict", action="store_true", help="Fail on parse/selection warnings")
    args = parser.parse_args()

    if not args.input and not args.sec_source:
        parser.error("At least one input path or --sec-source directory is required")

    workspace = Path.cwd()
    input_paths = [item.resolve() for item in args.input]
    missing_inputs = [path for path in input_paths if not path.exists()]
    if missing_inputs:
        parser.error("Input does not exist: " + ", ".join(str(path) for path in missing_inputs))
    discovered = [
        path
        for input_path in input_paths
        for path in discover_files(input_path, args.include, args.exclude)
    ]
    files = sorted({path.resolve(): path for path in discovered}.values(), key=lambda item: item.as_posix().lower())
    tables: list[Table] = []
    warnings: list[str] = []

    for path in files:
        source = relative_source(path, workspace)
        digest = sha256(path)
        try:
            if path.suffix.lower() in {".csv", ".tsv"}:
                parsed = parse_delimited(path, source, digest)
            elif path.suffix.lower() == ".md":
                parsed = parse_markdown(path, source, digest)
            else:
                parsed = parse_json(path, source, digest)
            if not parsed:
                warnings.append(f"No supported table found: {source}")
            tables.extend(normalize_orientation(table) for table in parsed)
        except Exception as exc:
            message = f"Failed to parse {source}: {exc}"
            if args.strict:
                raise ValueError(message) from exc
            warnings.append(message)

    sec_source_paths = [item.resolve() for item in args.sec_source]
    for sec_dir in sec_source_paths:
        if not sec_dir.is_dir():
            message = f"SEC source directory not found: {sec_dir}"
            if args.strict:
                raise ValueError(message)
            warnings.append(message)
            continue
        try:
            sec_tables = parse_sec_html(sec_dir, workspace)
            if not sec_tables:
                warnings.append(f"No tables extracted from SEC source: {sec_dir}")
            tables.extend(normalize_orientation(table) for table in sec_tables)
        except Exception as exc:
            message = f"Failed to parse SEC source {sec_dir}: {exc}"
            if args.strict:
                raise ValueError(message) from exc
            warnings.append(message)

    tables, selection_warnings = select_tables(tables, args.table, args.period)
    warnings.extend(selection_warnings)
    if not tables:
        raise ValueError("No tables matched the requested scope")
    tables = [type_table(table) for table in tables]
    for index, table in enumerate(tables, 1):
        table.table_id = f"T{index:03d}"
        table.topic_hint = classify_topic(table)
    if args.strict and warnings:
        raise ValueError("; ".join(warnings))

    all_sources = [relative_source(p, workspace) for p in input_paths]
    all_sources.extend(relative_source(p, workspace) for p in sec_source_paths)
    sec_files = []
    for sec_dir in sec_source_paths:
        if (sec_dir / "source.html").is_file():
            sec_files.append(sec_dir / "source.html")
        elif (sec_dir / "raw" / "source.html").is_file():
            sec_files.append(sec_dir / "raw" / "source.html")
    bundle = {
        "schema": "company-research-excel-bundle.v2",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "input": all_sources[0] if len(all_sources) == 1 else all_sources,
        "filters": {"include": args.include, "exclude": args.exclude, "table": args.table, "period": args.period},
        "files": [
            {"path": relative_source(path, workspace), "sha256": sha256(path)}
            for path in [*files, *sec_files]
        ],
        "warnings": warnings,
        "tables": [asdict(table) for table in tables],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "input_files": len(files),
        "sec_sources": len(sec_source_paths),
        "tables": len(tables),
        "warnings": warnings,
        "output": str(args.output.resolve()),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
