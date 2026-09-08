#!/usr/bin/env python3
"""
Render a polished investment-research workbook from a model.json spec.

Usage:
    python3 build_workbook.py model.json output.xlsx

The spec is produced by assemble_model.py and documented in the skill's
data-schema reference. In short:
  company  — identity, currency, units, fiscal calendar, model date
  periods  — annual labels (left block), scrap_cols (blank scratch), quarterly labels (right block)
  sheets   — kind "statement" (blocks of typed rows sharing the period column layout)
             or kind "table" (Cover, Sources — free-form grids)

Row types on statement sheets:
  input       hardcoded value per period (blue font = "as filed")
  subtotal    =SUM of child rows (black formula, top border)
  calc        arbitrary expression over row ids, e.g. "{gp}/{total_rev}"
              optional "expr_q" overrides the expression in quarterly columns
  growth_yoy  y/y growth of another row (prior annual col / 4 quarters back)
  link        green cross-sheet reference to another sheet's row
  check       expression that should be ~0; formatted red when |value| > 0.5
              set "expect_nonzero": true for reconciliation rows — amber, not enforced
  spacer      blank row

House style: blue inputs, black formulas, green links, dark-navy section bars,
light-blue period headers, grey scrap columns, parenthesized negatives, dash
zeros, hidden gridlines, frozen panes. Arial throughout.
"""
import json
import re
import sys

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, NamedStyle, PatternFill, Side
from openpyxl.utils import get_column_letter

# ------------------------------------------------------------------ style ----
NAVY = "1F4E79"
LIGHT_BLUE = "D6E4F0"
SCRAP_GREY = "F2F2F2"
WHITE = "FFFFFF"
CHARCOAL = "333333"

FILL_TITLE = PatternFill("solid", fgColor=NAVY)
FILL_HDR = PatternFill("solid", fgColor=LIGHT_BLUE)
FILL_SCRAP = PatternFill("solid", fgColor=SCRAP_GREY)
FILL_COL_HDR = PatternFill("solid", fgColor=NAVY)

F_TITLE = Font(name="Arial", bold=True, color=WHITE, size=14)
F_SECTION = Font(name="Arial", bold=True, color=WHITE, size=10)
F_SCOPE = Font(name="Arial", color="808080", italic=True, size=9)
F_INPUT = Font(name="Arial", color="0000CC", size=10)
F_INPUT_BOLD = Font(name="Arial", color="0000CC", bold=True, size=10)
F_FORMULA = Font(name="Arial", color=CHARCOAL, size=10)
F_FORMULA_BOLD = Font(name="Arial", color=CHARCOAL, bold=True, size=10)
F_LINK = Font(name="Arial", color="008000", size=10)
F_LINK_BOLD = Font(name="Arial", color="008000", bold=True, size=10)
F_MEMO = Font(name="Arial", color="999999", italic=True, size=9)
F_HDR = Font(name="Arial", bold=True, color=WHITE, size=10)
F_PERIOD_LABEL = Font(name="Arial", bold=True, color=CHARCOAL, size=10)
F_DATE = Font(name="Arial", color="808080", italic=True, size=8)
F_CHECK_RED = Font(name="Arial", color="FF0000", bold=True, size=10)
F_CHECK_AMBER = Font(name="Arial", color="BF8F00", italic=True, size=10)
F_CONTENTS = Font(name="Arial", color="0563C1", size=9, underline="single")
F_LABEL = Font(name="Arial", color=CHARCOAL, size=10)
F_LABEL_BOLD = Font(name="Arial", color=CHARCOAL, bold=True, size=10)
F_TABLE_HEADER = Font(name="Arial", bold=True, color=CHARCOAL, size=10)

THIN_TOP = Border(top=Side(style="thin", color="999999"))
THIN_BOTTOM = Border(bottom=Side(style="thin", color="999999"))

FMT = {
    "num": '#,##0;(#,##0);"-"',
    "num1": '#,##0.0;(#,##0.0);"-"',
    "ps": '#,##0.00;(#,##0.00);"-"',
    "pct": '0.0%;(0.0%);"-"',
    "x": '0.0"x";(0.0"x");"-"',
    "txt": "@",
}

LABEL_COL = 1
NOTE_COL = 2         # collapsed source/basis column
DATA_START_COL = 3   # annual block starts here
HDR_LABEL_ROW = 3    # period labels
HDR_DATE_ROW = 4     # period end dates
DATA_START_ROW = 6

TOKEN_RE = re.compile(r"\{([A-Za-z0-9_]+:)?([A-Za-z0-9_]+)(@-\d+)?\}")


def sanitize_sheet_name(name):
    name = re.sub(r"[\[\]:*?/\\]", "-", name)
    return name[:31]


class Layout:
    """Shared column layout for every statement sheet."""

    def __init__(self, periods):
        self.annual = periods.get("annual", [])
        self.quarterly = periods.get("quarterly", [])
        self.scrap_n = int(periods.get("scrap_cols", 5))
        self.col_of = {}
        c = DATA_START_COL
        for p in self.annual:
            self.col_of[p["label"]] = c
            c += 1
        self.scrap_cols = list(range(c, c + self.scrap_n))
        c += self.scrap_n
        for p in self.quarterly:
            self.col_of[p["label"]] = c
            c += 1
        self.last_col = max(c - 1, DATA_START_COL)
        self.annual_labels = [p["label"] for p in self.annual]
        self.quarterly_labels = [p["label"] for p in self.quarterly]
        self.all_labels = self.annual_labels + self.quarterly_labels
        self.order = {lbl: i for i, lbl in enumerate(self.all_labels)}

    def in_span(self, row, label):
        o = self.order.get(label, -1)
        if o < 0:
            return False
        mn, mx = row.get("min_label"), row.get("max_label")
        if mn is not None and o < self.order.get(mn, 0):
            return False
        if mx is not None and o > self.order.get(mx, len(self.all_labels)):
            return False
        return True

    def end_of(self, label):
        for p in self.annual + self.quarterly:
            if p["label"] == label:
                return p.get("end", "")
        return ""


def contents_offset(sheet):
    return (len(sheet.get("blocks", [])) + 2) if sheet.get("contents") else 0


def build_registry(model):
    registry = {}
    sheet_names = {}
    block_rows = {}
    for sheet in model["sheets"]:
        if sheet.get("kind") != "statement":
            continue
        short = sheet["short"]
        registry[short] = {}
        block_rows[short] = []
        sheet_names[short] = sanitize_sheet_name(sheet["name"])
        r = DATA_START_ROW + contents_offset(sheet)
        for block in sheet.get("blocks", []):
            block_rows[short].append(r)
            r += 1
            for row in block.get("rows", []):
                rid = row.get("id")
                if rid:
                    if rid in registry[short]:
                        raise ValueError(f"duplicate row id '{short}:{rid}'")
                    registry[short][rid] = r
                r += 1
            r += 1
    return registry, sheet_names, block_rows


class Builder:
    def __init__(self, model):
        self.model = model
        self.layout = Layout(model["periods"])
        self.registry, self.sheet_names, self.block_rows = build_registry(model)
        self.wb = Workbook()
        self.wb.remove(self.wb.active)

    def ref(self, cur_short, token_sheet, row_id, col, offset=0):
        short = (token_sheet or cur_short).rstrip(":") if token_sheet else cur_short
        if short not in self.registry or row_id not in self.registry[short]:
            raise ValueError(f"unknown row reference '{short}:{row_id}'")
        r = self.registry[short][row_id]
        cell = f"{get_column_letter(col - offset)}{r}"
        if short != cur_short:
            return f"'{self.sheet_names[short]}'!{cell}"
        return cell

    def translate(self, expr, cur_short, col):
        def sub(m):
            sheet_tok, rid, off = m.group(1), m.group(2), m.group(3)
            offset = int(off[2:]) if off else 0
            return self.ref(cur_short, sheet_tok, rid, col, offset)
        return "=" + TOKEN_RE.sub(sub, expr)

    def font_for(self, row, kind):
        if row.get("memo"):
            return F_MEMO
        bold = row.get("bold", False)
        if kind == "input":
            return F_INPUT_BOLD if bold else F_INPUT
        if kind == "link":
            return F_LINK_BOLD if bold else F_LINK
        return F_FORMULA_BOLD if bold else F_FORMULA

    def sheet_header(self, ws, title, is_statement=True):
        last = self.layout.last_col if is_statement else 8
        ws.cell(row=1, column=1, value=title)
        for c in range(1, last + 1):
            ws.cell(row=1, column=c).fill = FILL_TITLE
        ws.cell(row=1, column=1).font = F_TITLE
        ws.cell(row=1, column=1).alignment = Alignment(vertical="center")
        ws.row_dimensions[1].height = 28
        co = self.model["company"]
        scope_parts = []
        if co.get("units"):
            scope_parts.append(co["units"])
        if co.get("currency"):
            scope_parts.append(co["currency"])
        if co.get("model_date"):
            scope_parts.append(f'as of {co["model_date"]}')
        note = "  |  ".join(scope_parts)
        c2 = ws.cell(row=2, column=1, value=note)
        c2.font = F_SCOPE
        ws.row_dimensions[2].height = 16

    def period_headers(self, ws):
        L = self.layout
        for p in L.annual + L.quarterly:
            c = L.col_of[p["label"]]
            h = ws.cell(row=HDR_LABEL_ROW, column=c, value=p["label"])
            h.fill, h.font = FILL_HDR, F_PERIOD_LABEL
            h.alignment = Alignment(horizontal="center")
            h.border = THIN_BOTTOM
            d = ws.cell(row=HDR_DATE_ROW, column=c, value=p.get("end", ""))
            d.font = F_DATE
            d.alignment = Alignment(horizontal="center")
        for c in L.scrap_cols:
            h = ws.cell(row=HDR_LABEL_ROW, column=c, value="·")
            h.fill = FILL_SCRAP
            h.alignment = Alignment(horizontal="center")
            h.font = F_MEMO

    def write_statement(self, sheet):
        L = self.layout
        short = sheet["short"]
        ws = self.wb.create_sheet(self.sheet_names[short])
        co = self.model["company"]
        self.sheet_header(ws, f'{co.get("name", "")} — {sheet["name"]}')
        self.period_headers(ws)
        ws.sheet_format.defaultRowHeight = 16.5

        ws.column_dimensions["A"].width = 46
        for c in range(DATA_START_COL, L.last_col + 1):
            ws.column_dimensions[get_column_letter(c)].width = (
                9 if c in L.scrap_cols else 12
            )

        blocks = sheet.get("blocks", [])
        titles = [self.block_title(i, b) for i, b in enumerate(blocks, 1)]

        r = DATA_START_ROW
        if sheet.get("contents"):
            ws.cell(row=r, column=1, value="CONTENTS").font = F_TABLE_HEADER
            for i, title in enumerate(titles):
                tgt = f"#'{self.sheet_names[short]}'!A{self.block_rows[short][i]}"
                safe = title.replace('"', '""')
                cell = ws.cell(row=r + 1 + i, column=1,
                               value=f'=HYPERLINK("{tgt}","{safe}")')
                cell.font = F_CONTENTS
                cell.alignment = Alignment(indent=1)
            r += contents_offset(sheet)

        self.has_notes = False
        for bi, block in enumerate(blocks):
            ws.row_dimensions[r - 1].height = 8
            t = ws.cell(row=r, column=1, value=titles[bi])
            t.font = F_SECTION
            ws.row_dimensions[r].height = 20
            for c in range(1, L.last_col + 1):
                ws.cell(row=r, column=c).fill = FILL_TITLE
            r += 1
            for row in block.get("rows", []):
                self.write_row(ws, short, r, row)
                r += 1
            r += 1
        for c in L.scrap_cols:
            for rr in range(HDR_LABEL_ROW, r):
                ws.cell(row=rr, column=c).fill = FILL_SCRAP
        if self.has_notes:
            ws.column_dimensions["B"].width = 34
            ws.column_dimensions.group("B", "B", outline_level=1, hidden=True)
        else:
            ws.column_dimensions["B"].width = 2
        self.finish_sheet(ws, sheet)

    @staticmethod
    def block_title(n, block):
        title = block.get("title", "")
        return title if re.match(r"^\d+\.", title) else f"{n}. {title}"

    def write_row(self, ws, short, r, row):
        L = self.layout
        kind = row.get("type", "input")
        if kind == "spacer":
            return
        lab = ws.cell(row=r, column=1, value=row.get("label", ""))
        if row.get("memo"):
            lab.font = F_MEMO
        elif row.get("bold"):
            lab.font = F_LABEL_BOLD
        else:
            lab.font = F_LABEL
        if row.get("indent"):
            lab.alignment = Alignment(indent=int(row["indent"]))
        if row.get("note"):
            nb = ws.cell(row=r, column=NOTE_COL, value=str(row["note"]))
            nb.font = F_DATE
            nb.alignment = Alignment(wrap_text=True, vertical="top")
            self.has_notes = True
        if row.get("group"):
            ws.row_dimensions[r].outlineLevel = 1
        fmt = FMT.get(row.get("fmt", "num"), FMT["num"])
        font = self.font_for(row, kind)
        if kind == "check" and row.get("expect_nonzero"):
            font = F_CHECK_AMBER

        for label in L.all_labels:
            if not L.in_span(row, label):
                continue
            c = L.col_of[label]
            cell = ws.cell(row=r, column=c)
            val = self.cell_content(short, row, kind, label, c)
            if val is None:
                continue
            cell.value = val
            cell.number_format = fmt
            cell.font = font
            cell.alignment = Alignment(horizontal="right")
            if kind == "subtotal" or row.get("border_top"):
                cell.border = THIN_TOP

        if kind == "check" and not row.get("expect_nonzero"):
            rng = (f"{get_column_letter(DATA_START_COL)}{r}:"
                   f"{get_column_letter(L.last_col)}{r}")
            ws.conditional_formatting.add(
                rng,
                CellIsRule(operator="notBetween", formula=["-0.5", "0.5"],
                           font=F_CHECK_RED),
            )
        if kind == "subtotal" or row.get("border_top"):
            for c in L.scrap_cols:
                ws.cell(row=r, column=c).border = THIN_TOP

    def cell_content(self, short, row, kind, label, col):
        L = self.layout
        if kind == "input":
            return row.get("values", {}).get(label)
        if kind == "subtotal":
            kids = row.get("children", [])
            if not kids:
                raise ValueError(f"subtotal '{row.get('id')}' has no children")
            refs = [self.ref(short, None, k, col) for k in kids]
            return "=" + "+".join(refs)
        if kind == "link":
            tgt = row["ref"]
            sheet_tok, rid = tgt.split(":") if ":" in tgt else (None, tgt)
            return "=" + self.ref(short, (sheet_tok + ":") if sheet_tok else None,
                                  rid, col)
        if kind == "growth_yoy":
            of = row["of"]
            if label in L.annual_labels:
                i = L.annual_labels.index(label)
                if i == 0:
                    return None
                prev_col = L.col_of[L.annual_labels[i - 1]]
            else:
                j = L.quarterly_labels.index(label)
                if j < 4:
                    return None
                prev_col = L.col_of[L.quarterly_labels[j - 4]]
            cur = self.ref(short, None, of, col)
            prev = self.ref(short, None, of, prev_col)
            return f'=IF(N({prev})=0,"",{cur}/{prev}-1)'
        if kind == "growth_qoq":
            of = row["of"]
            if label in L.annual_labels:
                return None  # QoQ not meaningful on annual columns
            j = L.quarterly_labels.index(label)
            if j < 1:
                return None
            prev_col = L.col_of[L.quarterly_labels[j - 1]]
            cur = self.ref(short, None, of, col)
            prev = self.ref(short, None, of, prev_col)
            return f'=IF(N({prev})=0,"",{cur}/{prev}-1)'
        if kind in ("calc", "check"):
            expr = row.get("expr")
            if label in L.quarterly_labels and row.get("expr_q"):
                expr = row["expr_q"]
            if not expr:
                raise ValueError(f"row '{row.get('id')}' missing expr")
            return self.translate(expr, short, col)
        raise ValueError(f"unknown row type '{kind}'")

    def write_table(self, sheet):
        ws = self.wb.create_sheet(sanitize_sheet_name(sheet["name"]))
        co = self.model["company"]
        self.sheet_header(ws, f'{co.get("name", "")} — {sheet["name"]}',
                          is_statement=False)
        widths = sheet.get("col_widths", [28, 60, 60, 40])
        for i, w in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = w
        r = 4
        for trow in sheet.get("table", []):
            for ci, cell in enumerate(trow, start=1):
                target = ws.cell(row=r, column=ci)
                if isinstance(cell, dict):
                    target.value = cell.get("text", "")
                    if cell.get("url"):
                        target.hyperlink = cell["url"]
                        target.font = Font(name="Arial", color="0563C1",
                                           underline="single", size=10)
                    elif cell.get("bold"):
                        target.font = Font(name="Arial", bold=True, size=10)
                    elif cell.get("header"):
                        target.font = F_HDR
                        target.fill = FILL_COL_HDR
                    if cell.get("fill"):
                        target.fill = PatternFill("solid", fgColor=cell["fill"])
                else:
                    target.value = cell
                    target.font = F_LABEL
            r += 1
        self.finish_sheet(ws, sheet, freeze="A4")

    def finish_sheet(self, ws, sheet, freeze=None):
        ws.sheet_view.showGridLines = False
        ws.sheet_view.zoomScale = 85
        ws.freeze_panes = freeze or f"{get_column_letter(DATA_START_COL)}{DATA_START_ROW}"
        if sheet.get("tab_color"):
            ws.sheet_properties.tabColor = sheet["tab_color"]

    def run(self, out_path):
        for sheet in self.model["sheets"]:
            if sheet.get("kind") == "statement":
                self.write_statement(sheet)
            else:
                self.write_table(sheet)
        self.wb.save(out_path)
        print(f"wrote {out_path}")


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    with open(sys.argv[1]) as f:
        model = json.load(f)
    Builder(model).run(sys.argv[2])


if __name__ == "__main__":
    main()
