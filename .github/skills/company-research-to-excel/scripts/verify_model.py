#!/usr/bin/env python3
"""
Verify a model.json + built workbook before delivery.

Usage:
    python3 verify_model.py model.json output.xlsx

Two layers:
 1. NUMERIC — re-evaluates every formula row (subtotal / calc / growth_yoy /
    link / check) in pure Python from the JSON input values, then reports any
    'check' row whose absolute value exceeds 0.5 (half a million at $mm units)
    in any populated period.
 2. STRUCTURAL — opens the .xlsx and confirms: every sheet exists, period
    headers match, inputs are numbers (not formulas), subtotals are formulas
    (not hardcodes), gridlines hidden, panes frozen.

Exit code 0 = all pass; exit code 2 = at least one failure.
"""
import json
import re
import sys

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

TOKEN_RE = re.compile(r"\{([A-Za-z0-9_]+:)?([A-Za-z0-9_]+)(@-\d+)?\}")
DATA_START_COL = 3
DATA_START_ROW = 6
HDR_LABEL_ROW = 3


def contents_offset(sheet):
    return (len(sheet.get("blocks", [])) + 2) if sheet.get("contents") else 0

failures = []


def report(ok, msg):
    print(("PASS: " if ok else "FAIL: ") + msg)
    if not ok:
        failures.append(msg)


class Evaluator:
    def __init__(self, model):
        self.model = model
        p = model["periods"]
        self.annual = [x["label"] for x in p.get("annual", [])]
        self.quarterly = [x["label"] for x in p.get("quarterly", [])]
        self.labels = self.annual + self.quarterly
        self.order = {lbl: i for i, lbl in enumerate(self.labels)}
        self.rows = {}
        self.cache = {}
        for sheet in model["sheets"]:
            if sheet.get("kind") != "statement":
                continue
            for block in sheet.get("blocks", []):
                for row in block.get("rows", []):
                    if row.get("id"):
                        self.rows[(sheet["short"], row["id"])] = row

    def in_span(self, row, label):
        o = self.order.get(label, -1)
        if o < 0:
            return False
        mn, mx = row.get("min_label"), row.get("max_label")
        if mn is not None and o < self.order.get(mn, 0):
            return False
        if mx is not None and o > self.order.get(mx, len(self.labels)):
            return False
        return True

    def value(self, short, rid, label, stack=()):
        key = (short, rid, label)
        if key in self.cache:
            return self.cache[key]
        if key in stack:
            raise ValueError(f"circular reference at {short}:{rid}")
        if (short, rid) not in self.rows:
            raise ValueError(f"unknown row {short}:{rid}")
        row = self.rows[(short, rid)]
        if not self.in_span(row, label):
            self.cache[key] = None
            return None
        kind = row.get("type", "input")
        stack = stack + (key,)
        v = None
        if kind == "input":
            v = row.get("values", {}).get(label)
        elif kind == "subtotal":
            vals = [self.value(short, k, label, stack)
                    for k in row.get("children", [])]
            nums = [x for x in vals if x is not None]
            v = sum(nums) if nums else None
        elif kind == "link":
            tgt = row["ref"]
            s, r = tgt.split(":") if ":" in tgt else (short, tgt)
            v = self.value(s, r, label, stack)
        elif kind == "growth_yoy":
            seq = self.annual if label in self.annual else self.quarterly
            back = 1 if label in self.annual else 4
            i = seq.index(label)
            if i >= back:
                cur = self.value(short, row["of"], label, stack)
                prev = self.value(short, row["of"], seq[i - back], stack)
                if cur is not None and prev not in (None, 0):
                    v = cur / prev - 1
        elif kind == "growth_qoq":
            if label in self.annual:
                v = None  # QoQ not meaningful on annual columns
            else:
                seq = self.quarterly
                i = seq.index(label)
                if i >= 1:
                    cur = self.value(short, row["of"], label, stack)
                    prev = self.value(short, row["of"], seq[i - 1], stack)
                    if cur is not None and prev not in (None, 0):
                        v = cur / prev - 1
        elif kind in ("calc", "check"):
            expr = row.get("expr")
            if label in self.quarterly and row.get("expr_q"):
                expr = row["expr_q"]
            v = self.eval_expr(expr, short, label, stack)
        self.cache[key] = v
        return v

    def eval_expr(self, expr, short, label, stack):
        seq = self.annual if label in self.annual else self.quarterly
        idx = seq.index(label) if label in seq else -1
        if idx < 0:
            return None
        resolved = []

        def sub(m):
            s = m.group(1).rstrip(":") if m.group(1) else short
            rid = m.group(2)
            off = int(m.group(3)[2:]) if m.group(3) else 0
            lbl = label
            if off:
                if idx - off < 0:
                    resolved.append(None)
                    return "None"
                lbl = seq[idx - off]
            val = self.value(s, rid, lbl, stack)
            resolved.append(val)
            return "0.0" if val is None else repr(float(val))

        py = TOKEN_RE.sub(sub, expr)
        if "None" in py:
            return None
        if resolved and all(v is None for v in resolved):
            return None
        try:
            return eval(py, {"__builtins__": {}}, {})
        except ZeroDivisionError:
            return None


def numeric_checks(model):
    ev = Evaluator(model)
    n_checks = 0
    for sheet in model["sheets"]:
        if sheet.get("kind") != "statement":
            continue
        for block in sheet.get("blocks", []):
            for row in block.get("rows", []):
                if row.get("type") != "check" or not row.get("id"):
                    continue
                if row.get("expect_nonzero"):
                    print(f'INFO: expected-non-zero check "{row.get("label")}" '
                          f'on {sheet["name"]} — styled amber, not enforced')
                    continue
                n_checks += 1
                bad = []
                for label in ev.labels:
                    v = ev.value(sheet["short"], row["id"], label)
                    if v is not None and abs(v) > 0.5:
                        bad.append(f"{label}={v:,.1f}")
                report(not bad,
                       f'check "{row["label"]}" on {sheet["name"]}: '
                       + ("all periods tie" if not bad else "OFF in " + ", ".join(bad)))
    report(n_checks > 0, f"model defines {n_checks} tie-out check row(s)")
    return ev


def window_coverage(model, ev):
    """Check for hollow or empty period columns on statement sheets."""
    p = model["periods"]
    labels = ([x["label"] for x in p.get("annual", [])]
              + [x["label"] for x in p.get("quarterly", [])])
    for sheet in model["sheets"]:
        if sheet.get("kind") != "statement":
            continue
        short = sheet["short"]
        input_rows = [
            row for block in sheet.get("blocks", [])
            for row in block.get("rows", [])
            if row.get("type", "input") == "input" and row.get("id")
        ]
        if not input_rows:
            continue
        for label in labels:
            in_span = [r for r in input_rows if ev.in_span(r, label)]
            if not in_span:
                continue
            populated = sum(1 for r in in_span
                           if r.get("values", {}).get(label) is not None)
            pct = populated / len(in_span) if in_span else 0
            if populated == 0:
                report(False, f'{sheet["name"]}: period {label} has 0/{len(in_span)} inputs populated (empty column)')
            elif pct < 0.5:
                print(f'WARN: {sheet["name"]}: period {label} has {populated}/{len(in_span)} inputs populated ({pct:.0%} — hollow column)')


def structural_checks(model, xlsx_path):
    wb = load_workbook(xlsx_path)
    p = model["periods"]
    scrap_n = int(p.get("scrap_cols", 5))
    expected_hdr = ([x["label"] for x in p.get("annual", [])]
                    + ["·"] * scrap_n
                    + [x["label"] for x in p.get("quarterly", [])])
    for sheet in model["sheets"]:
        name = re.sub(r"[\[\]:*?/\\]", "-", sheet["name"])[:31]
        report(name in wb.sheetnames, f'sheet "{name}" exists')
        if name not in wb.sheetnames:
            continue
        ws = wb[name]
        if sheet.get("kind") != "statement":
            continue
        got = [ws.cell(row=HDR_LABEL_ROW, column=DATA_START_COL + i).value
               for i in range(len(expected_hdr))]
        report(got == expected_hdr,
               f'{name}: period header layout matches spec'
               + ("" if got == expected_hdr else f" (got {got})"))
        report(not ws.sheet_view.showGridLines, f"{name}: gridlines hidden")
        report(bool(ws.freeze_panes), f"{name}: panes frozen")

    # Input vs formula cell checks
    col_of = {}
    c = DATA_START_COL
    for x in p.get("annual", []):
        col_of[x["label"]] = c
        c += 1
    c += scrap_n
    for x in p.get("quarterly", []):
        col_of[x["label"]] = c
        c += 1
    all_labels = list(col_of.keys())

    for sheet in model["sheets"]:
        if sheet.get("kind") != "statement":
            continue
        name = re.sub(r"[\[\]:*?/\\]", "-", sheet["name"])[:31]
        if name not in wb.sheetnames:
            continue
        ws = wb[name]
        short = sheet["short"]
        from openpyxl.utils import get_column_letter as gcl

        # Build row number map (mirrors build_registry logic)
        co = contents_offset(sheet)
        r = DATA_START_ROW + co
        row_map = {}
        for block in sheet.get("blocks", []):
            r += 1  # block title row
            for row in block.get("rows", []):
                rid = row.get("id")
                if rid:
                    row_map[rid] = (r, row)
                r += 1
            r += 1  # gap after block

        bad_inputs = 0
        bad_formulas = 0
        for rid, (excel_row, row) in row_map.items():
            kind = row.get("type", "input")
            if kind == "spacer":
                continue
            sample_col = col_of.get(all_labels[0]) if all_labels else None
            if sample_col is None:
                continue
            cell = ws.cell(row=excel_row, column=sample_col)
            if kind == "input":
                if cell.value is not None and isinstance(cell.value, str) and cell.value.startswith("="):
                    bad_inputs += 1
            elif kind in ("subtotal", "calc", "check", "link", "growth_yoy", "growth_qoq"):
                if cell.value is not None and not (isinstance(cell.value, str) and cell.value.startswith("=")):
                    bad_formulas += 1

        if bad_inputs:
            report(False, f'{name}: {bad_inputs} input row(s) contain formulas instead of hardcoded values')
        if bad_formulas:
            report(False, f'{name}: {bad_formulas} formula row(s) contain hardcoded values instead of formulas')


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    with open(sys.argv[1]) as f:
        model = json.load(f)
    ev = numeric_checks(model)
    window_coverage(model, ev)
    structural_checks(model, sys.argv[2])
    print()
    if failures:
        print(f"{len(failures)} FAILURE(S) — fix model.json and rebuild.")
        sys.exit(2)
    print("All verification checks passed.")


if __name__ == "__main__":
    main()
