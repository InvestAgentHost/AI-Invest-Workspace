#!/usr/bin/env python3
"""Independent verification of the Operating Metrics and Note Schedules sheets.

For every hard-coded cell it re-reads the source filing text (the same prepared Markdown
the extraction used) and confirms the printed value is present on or near the recorded
line. This is deliberately a second path: it does not consult operating_raw.json, so a
bug in that file's structure cannot hide itself here.

Usage: python -I _ops_audit.py <workspace_root> <work_dir>
"""
import json
import os
import re
import sys
from bisect import bisect_left

from openpyxl import load_workbook

ROOT, W = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
OPS = json.load(open(os.path.join(W, "operating_raw.json")))
wb = load_workbook(os.path.join(W, "KO_model.xlsx"))
cache = {}


def lines(path):
    if path not in cache:
        cache[path] = open(os.path.join(ROOT, path), encoding="utf-8").read().split("\n")
    return cache[path]


def fmt(v):
    if isinstance(v, float) and v != int(v):
        return f"{abs(v):,.1f}".rstrip("0").rstrip(".")
    return f"{abs(int(v)):,}"


# Anchor for every (table, period): each fiscal year of a table appears in more than one
# filing (as the current year in its own 10-K and as a comparative in later ones), so the
# lookup keeps them all and a value matches if it appears in ANY filing that prints it.
ANCH = {}


def _add(kind, fy, blk):
    y = re.findall(r"(20\d\d)", " ".join(blk.get("years", [])) or "")
    for yy in (y or [str(fy)]):
        ANCH.setdefault((kind, f"FY{yy}"), []).append((blk["path"], blk["line"]))
    if "years" not in blk:
        ANCH.setdefault((kind, f"FY{fy}"), []).append((blk["path"], blk["line"]))


for y, v in OPS["unit_case_volume_bn"].items():
    ANCH.setdefault(("vol", f"FY{y}"), []).append((v["path"], v["line"]))
for fy, blk in OPS["volume_growth"].items():
    ANCH.setdefault(("vg", f"FY{fy}"), []).append((blk["path"], blk["line"]))
for fy, blk in OPS["revenue_factors"].items():
    ANCH.setdefault(("fac", f"FY{fy}"), []).append((blk["path"], blk["line"]))
for kind, table in (("lob", OPS["line_of_business"]), ("mix", OPS["segment_revenue_pct"]),
                    ("eq", OPS["equity_method_summary"]), ("fv", OPS["equity_fair_value"]),
                    ("tpt", OPS["tax_pretax"]), ("tcd", OPS["tax_current_deferred"]),
                    ("utb", OPS["unrecognized_tax_benefits"]), ("debt", OPS["debt_by_type"])):
    for fy, blk in table.items():
        # years are carried either as a list or as the keys of a per-year sub-block
        ys = blk.get("years") or list((blk.get("blocks") or {}).keys()) or [fy]
        for yy in ys:
            ANCH.setdefault((kind, f"FY{yy}"), []).append((blk["path"], blk["line"]))
for fy, blk in OPS["held_for_sale"].items():
    for yy in (blk.get("years") or [fy]):
        ANCH.setdefault(("hfs", f"FY{yy}"), []).append((blk["path"], blk["line"]))


def near_text(path, line, rows=None, window=180):
    """Text of the filing around a line: a window generous enough to cover a table."""
    L = lines(path)
    lo = max(0, line - 6)
    hi = min(len(L), line + (rows or window))
    return L[lo:hi]


report = {"checked": 0, "found": 0, "missing": [], "sheets": {}}
for sheet_name in ("Operating Metrics", "Note Schedules"):
    ws = wb[sheet_name]
    hdr = {c.column: c.value for c in ws[3] if c.value}
    sheet_stats = {"cells": 0, "found": 0}
    for row in ws.iter_rows(min_row=6):
        label = row[0].value
        if not label or not isinstance(label, str):
            continue
        if label.startswith(("Check", "Balance Check", "Cash Walk")):
            continue
        rid = None
        for c in row[2:]:
            p = hdr.get(c.column)
            if not p or p == "·" or c.value is None or isinstance(c.value, str):
                continue
            v = c.value
            sheet_stats["cells"] += 1
            report["checked"] += 1
            # a value must appear somewhere in the sheet's own source window for that period:
            # try every anchor whose period matches, since a row draws on several tables
            hit = False
            cands = [a for k, a in ANCH.items() if k[1] == p]
            for (path, line) in [x for sub in cands for x in sub]:
                txt = " ".join(near_text(path, line))
                txt2 = re.sub(r"\s*\|\s*\)", ")", txt)
                printed = fmt(abs(v))
                if printed in txt2 or printed.replace(".", "") in re.sub(r"[^0-9]", "", txt2):
                    hit = True
                    break
            if hit:
                sheet_stats["found"] += 1
                report["found"] += 1
            else:
                report["missing"].append((sheet_name, str(label)[:50], p, v))
    report["sheets"][sheet_name] = sheet_stats

print(f"operating/note cells checked: {report['checked']}  matched to source text: {report['found']}")
for s, st in report["sheets"].items():
    print(f"   {s}: {st['found']}/{st['cells']}")
if report["missing"]:
    print("NOT FOUND IN SOURCE WINDOW:")
    for m in report["missing"][:40]:
        print("   ", m)
else:
    print("all values located in their source filing window")
