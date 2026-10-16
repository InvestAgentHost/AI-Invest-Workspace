#!/usr/bin/env python3
"""Extract KO operating KPIs (MD&A volume, revenue factors, line of business) and
operating-related Notes (equity method investees, income taxes, debt) from the prepared
filing Markdown. Values are copied, not re-keyed; each block records the filing and line.

Robustness notes:
- Values carry footnote markers and, in the debt note, weighted-average rates in the same
  cell as the amount ("$ 26,945 3.6 %"). `row_values` reads at most `ncols` values per row
  and drops numbers followed by "%" when `drop_pct` is set, so a marker or a rate cell
  cannot shift a column.
- Tables whose rows must add up (equity investee summary, revenue by line of business,
  unrecognized tax benefits roll-forward) carry a `checks` list with the tie-out result,
  so a mis-parse is visible rather than silent.
Writes operating_raw.json.
Usage: python -I _extract_operating.py <workspace_root> <out_json>
"""
import glob
import json
import os
import re
import sys
from bs4 import BeautifulSoup

root, out = sys.argv[1], sys.argv[2]
A = os.path.join(root, "sources/companies/US/KO-coca-cola/artifacts/ten_k")
VALUE = re.compile(r"\(?\s*\d[\d,]*(?:\.\d+)?\s*\)?")


def parse_num(s):
    s = s.strip()
    if s in ("", "—", "-", "–", "N/A", "nan"):
        return None
    neg = s.strip().startswith("(")
    s = s.strip().strip("()").replace(",", "").replace("$", "").replace("%", "").strip()
    try:
        v = float(s)
    except ValueError:
        return None
    v = -v if neg else v
    return int(v) if v == int(v) else v


def cells_of(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


MARKER = re.compile(r"[1-9](?:,[1-9])*")


def row_values(line, ncols, drop_pct=False, skip_label=True, first_only=False):
    """Read up to ncols values from a table row.

    The prepared Markdown splits values across cells and fuses footnote markers onto
    them, so the numbers are read from a repaired copy of the row:
    - a negative separated from its sign   ("| (4 | )% 7 |"  -> "(4) % 7")
    - a percent sign in its own cell       ("| 1 | % 5 |"    -> "1 % 5")
    - an em-dash standing for zero         ("| — |"          -> "| 0 |")

    Footnote markers are the hard part: the converters print them in the same cell as the
    value they annotate, on either side ("| 1 15.8 |", "| 528 1 |", "| 2,3 14 |"). A
    single-digit token (or comma-list of them) is therefore read as a marker, not a value,
    when nothing but whitespace separates it from a neighbouring number; a token alone in
    its cell is a value even when it is one digit (the tax roll-forward rows carry real
    6's and 9's). Percentage-bearing numbers are never markers, which keeps the factor
    tables — whose values are percents one cell apart — intact; with `drop_pct` those
    numbers are instead skipped, separating the debt note's amounts from its rates.

    `first_only` reads the leading value of a cell and ignores any trailing marker, which
    is what the single-period volume table needs (its cells read "| 3 4 |" = value 3,
    marker 4).
    """
    raw = " | ".join(cells_of(line)[1:] if skip_label else cells_of(line))
    raw = re.sub(r"\|\s*\)", ")", raw)                    # close a paren opened in the previous cell
    raw = re.sub(r"\|\s*%", " %", raw)                    # a "%"-only cell qualifies the number before it
    raw = re.sub(r"(?<![\d).])[—–](?![\d])", "0", raw)    # a standalone dash is zero

    toks = []
    for m in VALUE.finditer(raw):
        pct = bool(re.match(r"\s*%", raw[m.end():m.end() + 4]))
        toks.append({"t": m.group(0), "pct": pct, "a": m.start(), "b": m.end()})
    for i, tk in enumerate(toks):
        if tk["pct"] or not MARKER.fullmatch(tk["t"].strip()):
            continue
        near = False
        for j in (i - 1, i + 1):
            if 0 <= j < len(toks):
                gap = raw[min(tk["b"], toks[j]["b"]):max(tk["a"], toks[j]["a"])] if j > i else raw[toks[j]["b"]:tk["a"]]
                if "|" not in gap:
                    near = True
        tk["marker"] = near

    out = []
    for tk in toks:
        if drop_pct and tk["pct"]:
            continue
        if tk.get("marker") and not first_only:
            continue
        v = parse_num(tk["t"])
        if v is None:
            continue
        out.append(v)
        if len(out) == ncols:
            break
    while len(out) < ncols:
        out.append(None)
    return out


def find_table(L, start, n=40):
    j = start
    while j < len(L) and not L[j].startswith("|"):
        if j - start > 8:
            return [], start
        j += 1
    rows = []
    while j < len(L) and L[j].startswith("|"):
        rows.append(L[j])
        j += 1
    return rows[:n], j


def md_of(d):
    md = os.path.join(d, "prepared/document.md")
    if os.path.exists(md):
        return md
    om = json.load(open(os.path.join(d, "output_manifest.json")))
    return os.path.join(d, om["package_path"], "prepared/document.md")


def years_from(rowline, fallback):
    y = [int(x) for x in re.findall(r"(20\d\d)", rowline)]
    return y if y else fallback


F = {}
for d in sorted(glob.glob(os.path.join(A, "KO-coca-cola/FY*"))):
    fy = int(re.search(r"FY(\d{4})", d).group(1))
    p = md_of(d)
    F[fy] = (os.path.relpath(p, root), open(p, encoding="utf-8").read().split("\n"))

res = {}
CHECKS = []


def asum(*xs):
    """Sum that propagates a missing value instead of raising, so one unparsed cell
    leaves a visible failed check rather than killing the run."""
    return None if any(x is None for x in xs) else sum(xs)


def check(table, year, label, lhs, rhs, tol=1.5):
    if lhs is None or rhs is None:
        return
    ok = abs(lhs - rhs) <= tol
    CHECKS.append({"table": table, "year": year, "label": label,
                   "lhs": lhs, "rhs": rhs, "ok": bool(ok)})


# ---------------------------------------------------------------- unit case volume bn
ucv = {}
for fy, (p, L) in F.items():
    for i, l in enumerate(L):
        m = re.search(r"The Coca-Cola system sold "
                      r"([0-9.]+)\s*billion"
                      r"(?:[,]?\s*(?:and\s+)?([0-9.]+)\s*billion)?"
                      r"(?:[,]?\s*(?:and\s+)?([0-9.]+)\s*billion)?"
                      r" unit cases", l)
        if not m:
            continue
        for k, v in enumerate([x for x in m.groups() if x]):
            y = fy - k
            ucv.setdefault(y, {"value": float(v), "filing": f"FY{fy} 10-K", "line": i + 1, "path": p})
        break
res["unit_case_volume_bn"] = ucv

# ------------------------------------------------------ volume growth table
VOL = {}
for fy, (p, L) in F.items():
    for i, l in enumerate(L):
        if re.search(r"Information about our volume growth worldwide", l, re.I):
            rows, j = find_table(L, i + 1, 12)
            hdr = cells_of(rows[0]) if rows else []
            periods = re.findall(r"(20\d\d)\s+versus\s+(20\d\d)", " ".join(hdr))
            body = []
            for r in rows[2:]:
                lab = cells_of(r)[0]
                if not lab or lab.startswith("Year Ended"):
                    continue
                if periods:
                    v = row_values(r, 4)
                    body.append([lab, v[0], v[1], v[2], v[3]])
                else:
                    c = cells_of(r)
                    uc = row_values(c[1], 1, first_only=True, skip_label=False) if len(c) > 1 else [None]
                    cs = row_values(c[3], 1, first_only=True, skip_label=False) if len(c) > 3 else [None]
                    # Match the same [unit cases, concentrate sales] pair layout
                    # used by the earlier two-period tables.
                    body.append([lab, uc[0], cs[0]])
            if body:
                VOL[fy] = {"rows": body, "line": j - len(rows) + 1, "path": p,
                           "periods": [[int(a), int(b)] for a, b in periods] or [[fy, fy - 1]]}
            break
res["volume_growth"] = VOL

# Prepared Markdown flattens superscript footnotes into ordinary numeric tokens.
# Re-read the original HTML presentation cells for this table instead of guessing
# which single-digit numbers are values. Keep N/A in its own metric position.
sys.path.insert(0, root)
from tools.research.audit_ko_workbook import html_rows, values as html_values
for fy, (p, L) in F.items():
    html_path = os.path.join(root, os.path.dirname(os.path.dirname(p)), "raw/source.html")
    soup = BeautifulSoup(open(html_path, encoding="utf-8").read(), "lxml")
    for tag in list(soup.find_all("sup")) + list(soup.find_all(style=re.compile(r"vertical-align\s*:\s*super|top\s*:\s*-", re.I))):
        tag.decompose()
    table = next(t for t in soup.find_all("table") if "worldwide" in t.get_text(" ", strip=True).lower()
                 and "unit cases" in t.get_text(" ", strip=True).lower()
                 and "concentrate sales" in t.get_text(" ", strip=True).lower())
    rows = html_rows(table)
    periods = re.findall(r"(20\d\d)\s+(?:versus|vs\.)\s+(20\d\d)", table.get_text(" ", strip=True))
    body = [[c[0]] + html_values(c[1:]) for c in rows if c and c[0] in
            ("Worldwide", "EMEA", "Europe, Middle East & Africa", "Latin America", "North America",
             "Asia Pacific", "Global Ventures", "Bottling Investments")]
    VOL[fy] = {"rows": body, "path": p, "html_path": os.path.relpath(html_path, root),
               "line": VOL.get(fy, {}).get("line", 0),
               "periods": [[int(a), int(b)] for a, b in periods] or [[fy, fy - 1]]}
res["volume_growth"] = VOL

# --------------------------------------------- net operating revenue factor table
FAC = {}
for fy, (p, L) in F.items():
    for i, l in enumerate(L):
        if re.search(r"estimated impact of the factors resulting in the increase", l, re.I):
            rows, j = find_table(L, i + 1, 12)
            hdr = cells_of(rows[0])[1:]
            body = []
            for r in rows[2:]:
                lab = cells_of(r)[0]
                if not lab:
                    continue
                v = row_values(r, 5)
                body.append([lab] + v)
                check("revenue_factors", fy, f"{lab}: components - Total",
                      asum(*v[:4]), v[4], tol=1.5)
            FAC[fy] = {"headers": hdr, "rows": body, "line": j - len(rows) + 1, "path": p}
            break
res["revenue_factors"] = FAC

# --------------------------------------------- revenue by line of business (US / Intl / Total)
LOB = {}
for fy, (p, L) in F.items():
    for i, l in enumerate(L):
        if re.search(r"net operating revenues disaggregated between the United States and International", l, re.I):
            rows, j = find_table(L, i + 1, 30)
            blocks = {}
            year = None
            for r in rows:
                lab = cells_of(r)[0]
                m = re.match(r"Year Ended December 31, (\d{4})", lab)
                if m:
                    year = int(m.group(1))
                    blocks[year] = {}
                    continue
                if year is None or not lab:
                    continue
                v = row_values(r, 3)
                blocks[year][lab] = v
                if lab.startswith("Total"):
                    parts = [blocks[year].get(k) for k in ("Concentrate operations", "Finished product operations")]
                    if all(parts):
                        check("line_of_business", year, "concentrate + finished - Total",
                              asum(*[x[2] for x in parts]), v[2])
                        check("line_of_business", year, "US + International - Total",
                              asum(v[0], v[1]), v[2])
            if blocks:
                LOB[fy] = {"blocks": blocks, "line": j - len(rows) + 1, "path": p}
            break
res["line_of_business"] = LOB

# --------------------------------------------- revenue % by operating segment
SEGPCT = {}
for fy, (p, L) in F.items():
    for i, l in enumerate(L):
        if re.search(r"by operating segment and Corporate as a percentage of Company net operating revenues", l, re.I):
            rows, j = find_table(L, i + 1, 14)
            years = years_from(rows[0], [fy, fy - 1])
            body = {}
            for r in rows[2:]:
                lab = cells_of(r)[0]
                if not lab:
                    continue
                body[lab] = row_values(r, len(years))
            for yi, y in enumerate(years):
                tot = body.get("Total", [None] * len(years))[yi]
                if tot is None:
                    continue
                s = sum(v[yi] for k, v in body.items() if k not in ("Total",) and v[yi] is not None)
                check("segment_revenue_pct", y, "segments + Corporate - Total", round(s, 1), tot, tol=0.15)
            SEGPCT[fy] = {"years": years, "rows": body, "line": j - len(rows) + 1, "path": p}
            break
res["segment_revenue_pct"] = SEGPCT

# --------------------------------------------- equity method investee aggregate summary
EQ = {}
for fy, (p, L) in F.items():
    for i, l in enumerate(L):
        if re.search(r"summary of financial information for our equity method investees", l, re.I):
            rows, j = find_table(L, i + 1, 30)
            yrs = years_from(rows[0], [fy - k for k in range(3)])
            body = {}
            for r in rows[2:]:
                lab = cells_of(r)[0]
                if not lab:
                    continue
                body[lab] = row_values(r, len(yrs))
                if lab in ("Gross profit", "Total assets"):
                    continue
            for yi, y in enumerate(yrs):
                gp = body.get("Gross profit")
                if gp and body.get("Net operating revenues") and body.get("Cost of goods sold"):
                    check("equity_method_summary", y, "revenue - COGS - gross profit",
                          asum(body["Net operating revenues"][yi], -body["Cost of goods sold"][yi]), gp[yi])
                ni = body.get("Net income attributable to common shareowners")
                cin = body.get("Consolidated net income")
                nci = body.get("Less: Net income attributable to noncontrolling interests")
                if ni and cin and nci:
                    check("equity_method_summary", y, "consolidated NI - NCI - NI to common",
                          asum(cin[yi], -nci[yi]) if nci[yi] is not None else None, ni[yi])
            EQ[fy] = {"years": yrs, "rows": body, "line": j - len(rows) + 1, "path": p}
            break
res["equity_method_summary"] = EQ

# --------------------------------------------- equity method fair value vs carrying
EQFV = {}
for fy, (p, L) in F.items():
    for i, l in enumerate(L):
        if re.search(r"difference between calculated fair value", l, re.I):
            rows, j = find_table(L, i + 1, 16)
            body = []
            for r in rows[2:]:
                lab = cells_of(r)[0]
                if not lab:
                    continue
                v = row_values(r, 3)
                body.append([lab] + v)
                if lab.startswith("Total"):
                    continue
                if None not in (v[0], v[1], v[2]):
                    check("equity_fair_value", fy, f"{lab}: fair - carrying - difference",
                          asum(v[0], -v[1]), v[2])
            if body:
                EQFV[fy] = {"rows": body, "line": j - len(rows) + 1, "path": p}
            break
res["equity_fair_value"] = EQFV

# --------------------------------------------- income taxes: pre-tax by jurisdiction
TAXPT = {}
for fy, (p, L) in F.items():
    for i, l in enumerate(L):
        if re.search(r"Income before income taxes consisted of the following", l, re.I):
            rows, j = find_table(L, i + 1, 14)
            ranges = [(m.start(), m.end()) for m in re.finditer(r"20\d\d", rows[0])]
            yrs = [int(rows[0][a:b]) for a, b in ranges]
            body = {}
            for r in rows[2:]:
                lab = cells_of(r)[0]
                if not lab:
                    continue
                body[lab] = row_values(r, len(yrs))
            for yi, y in enumerate(yrs):
                if body.get("United States") and body.get("International") and body.get("Total"):
                    check("tax_pretax", y, "US + International - Total",
                          asum(body["United States"][yi], body["International"][yi]), body["Total"][yi])
            TAXPT[fy] = {"years": yrs, "rows": body, "line": j - len(rows) + 1, "path": p}
            break
res["tax_pretax"] = TAXPT

# --------------------------------------------- income taxes: current / deferred
TAXCD = {}
for fy, (p, L) in F.items():
    for i, l in enumerate(L):
        if re.search(r"^Income taxes consisted of the following", l.strip(), re.I):
            rows, j = find_table(L, i + 1, 24)
            blocks = {}
            year = None
            for r in rows:
                lab = cells_of(r)[0]
                if re.match(r"^(19|20)\d\d$", lab):
                    year = int(lab)
                    blocks[year] = {}
                    continue
                if year is None or not lab or lab in ("Current", "Deferred"):
                    if year is not None and lab in ("Current", "Deferred"):
                        blocks[year][lab] = row_values(r, 4)
                    continue
            for y, b in blocks.items():
                if "Current" in b and "Deferred" in b:
                    check("tax_current_deferred", y, "US + state + international - Total (current)",
                          asum(*b["Current"][:3]), b["Current"][3])
                    check("tax_current_deferred", y, "US + state + international - Total (deferred)",
                          asum(*b["Deferred"][:3]), b["Deferred"][3])
            if blocks:
                TAXCD[fy] = {"blocks": blocks, "line": j - len(rows) + 1, "path": p}
            break
res["tax_current_deferred"] = TAXCD

# --------------------------------------------- unrecognized tax benefits rollforward
UTB = {}
for fy, (p, L) in F.items():
    for i, l in enumerate(L):
        if re.search(r"reconciliation of the changes in the gross amount of unrecognized tax benefits", l, re.I):
            rows, j = find_table(L, i + 1, 16)
            yrs = years_from(rows[0], [fy - k for k in range(3)])
            body = {}
            for r in rows[2:]:
                lab = cells_of(r)[0]
                if not lab:
                    continue
                body[lab] = row_values(r, len(yrs))
            beg = body.get("Balance of unrecognized tax benefits at beginning of year")
            end = body.get("Balance of unrecognized tax benefits at end of year")
            if beg and end:
                for yi, y in enumerate(yrs):
                    moves = sum(v[yi] for k, v in body.items()
                                if k not in ("Balance of unrecognized tax benefits at beginning of year",
                                             "Balance of unrecognized tax benefits at end of year")
                                and v[yi] is not None)
                    check("unrecognized_tax_benefits", y, "begin + movements - end", asum(beg[yi], moves), end[yi], tol=2.5)
            UTB[fy] = {"years": yrs, "rows": body, "line": j - len(rows) + 1, "path": p}
            break
res["unrecognized_tax_benefits"] = UTB

# --------------------------------------------- long-term debt by type
DEBT = {}
for fy, (p, L) in F.items():
    for i, l in enumerate(L):
        if re.search(r"The Company.s long-term debt consisted of the following", l, re.I):
            rows, j = find_table(L, i + 1, 24)
            yrs = years_from(rows[1] if len(rows) > 1 else rows[0], [fy, fy - 1])
            # Each year cell holds "Amount Average Rate", so the amount is the cell's FIRST
            # value. Reading per cell avoids the rate (whose "%" is sometimes omitted, e.g.
            # "767 4.8") being mistaken for the following year's amount.
            body = []
            for r in rows[2:]:
                c = cells_of(r)
                lab = c[0]
                if not lab or lab.startswith("Fixed interest"):
                    continue
                v = []
                for ci in range(1, min(len(c), len(yrs) + 1)):
                    got = row_values(c[ci], 1, first_only=True, skip_label=False)
                    v.append(got[0] if got else None)
                while len(v) < len(yrs):
                    v.append(None)
                body.append([lab] + v)
            tot = next((x for x in body if x[0].startswith("Total")), None)
            cur = next((x for x in body if x[0].startswith("Less") and "current" in x[0].lower()), None)
            ltd = next((x for x in body if x[0] == "Long-term debt"), None)
            if tot and cur and ltd:
                for yi, y in enumerate(yrs):
                    a, b2, c2 = tot[1 + yi], cur[1 + yi], ltd[1 + yi]
                    if None in (a, b2, c2):
                        continue
                    check("debt_by_type", y, "total - current portion - long-term debt", a - b2, c2)
            DEBT[fy] = {"years": yrs, "rows": body, "line": j - len(rows) + 1, "path": p}
            break
res["debt_by_type"] = DEBT

# --------------------------------------------- goodwill by operating segment
GW = {}
for fy, (p, L) in F.items():
    for i, l in enumerate(L):
        if re.search(r"carrying value of our goodwill by operating segment", l, re.I):
            rows, j = find_table(L, i + 1, 40)
            body = []
            year = None
            for r in rows:
                lab = cells_of(r)[0]
                if re.match(r"^(19|20)\d\d$", lab):
                    year = int(lab)
                    continue
                v = row_values(r, 6)
                if lab:
                    body.append([f"{year}: {lab}" if year else lab] + v)
            if body:
                GW[fy] = {"rows": body, "line": j - len(rows) + 1, "path": p}
            break
res["goodwill_by_segment"] = GW


# --------------------------------------------- assets and liabilities held for sale
HFS = {}
for fy, (p, L) in F.items():
    for i, l in enumerate(L):
        if re.search(r"major classes of assets and liabilities that were classified as held for sale", l, re.I):
            rows, j = find_table(L, i + 1, 32)
            yrs = years_from(rows[0], [fy, fy - 1])
            body = []
            for r in rows[2:]:
                lab = cells_of(r)[0]
                if not lab:
                    continue
                v = row_values(r, len(yrs))
                body.append([lab] + v)
            if body:
                HFS[fy] = {"years": yrs, "rows": body, "line": j - len(rows) + 1, "path": p}
            break
res["held_for_sale"] = HFS

# --------------------------------------------- bottler / customer concentration
CONC = {}
for fy, (p, L) in F.items():
    for i, l in enumerate(L):
        m = re.search(r"one bottler accounted for (\d+)% of our net operating revenues", l)
        if m:
            CONC.setdefault(fy, []).append({"kind": "bottler", "pct": int(m.group(1)), "line": i + 1, "path": p})
        if re.search(r"No bottlers or customers represented 10% or more", l):
            CONC.setdefault(fy, []).append({"kind": "none", "pct": None, "line": i + 1, "path": p})
res["customer_concentration"] = CONC

res["checks"] = CHECKS
json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
bad = [c for c in CHECKS if not c["ok"]]
print(f"operating tables: {len(res)-1} kinds; tie-out checks: {len(CHECKS)} ({len(bad)} failing)")
for c in bad[:20]:
    print("   FAIL", c["table"], c["year"], c["label"], c["lhs"], c["rhs"])
print("unit case volume years:", sorted(res["unit_case_volume_bn"]))
print("factor table years:", sorted(res["revenue_factors"]))
print("line of business years:", sorted(res["line_of_business"]))
print("debt years:", sorted(res["debt_by_type"]))
