#!/usr/bin/env python3
"""Extract consolidated IS / BS / CF tables from KO prepared filing Markdown (10-K and 10-Q).
Writes statements_raw.json: {filing_key: {statement: {"headers": [...], "rows": [[label, [vals...]], ...],
 "md_path": ..., "line": n}}}. Values are numbers (parentheses negative) or None for blank.
Usage: python -I _extract_statements.py <workspace_root> <out_json>
"""
import glob
import json
import os
import re
import sys

root, out = sys.argv[1], sys.argv[2]
A = os.path.join(root, "sources/companies/US/KO-coca-cola/artifacts/ten_k")

TITLES = {
    "IS": r"CONSOLIDATED STATEMENTS? OF INCOME",
    "BS": r"CONSOLIDATED BALANCE SHEETS?",
    "CF": r"CONSOLIDATED STATEMENTS? OF CASH FLOWS?",
}
NUM = re.compile(r"^\(?-?\$?\s*[\d,]+(?:\.\d+)?\)?$")


def parse_num(s):
    s = s.strip().replace("$", "").replace(" ", "")
    if s in ("", "—", "-", "–"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()").replace(",", "")
    try:
        v = float(s)
    except ValueError:
        return "TEXT:" + s
    v = -v if neg else v
    return int(v) if v == int(v) else v


def split_row(line):
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return cells


def extract(md_lines, kind, is_q):
    pat = re.compile(r"^#+\s*(?:CONDENSED\s+)?" + TITLES[kind] + r"\s*(?:\(UNAUDITED\))?\s*$", re.I)
    cands = [i for i, l in enumerate(md_lines) if pat.match(l.strip())]
    for i in cands:
        # first table within next 15 lines
        j = i + 1
        while j < min(i + 16, len(md_lines)) and not md_lines[j].startswith("|"):
            j += 1
        if j >= len(md_lines) or not md_lines[j].startswith("|"):
            continue
        k = j
        rows = []
        while k < len(md_lines) and md_lines[k].startswith("|"):
            rows.append(md_lines[k])
            k += 1
        if len(rows) < 8:
            continue
        hdr = split_row(rows[0])
        body = []
        for r in rows[2:]:
            c = split_row(re.sub(r"\s*\|\s*\)", ")", r))
            label = c[0]
            vals = []
            for x in c[1:]:
                toks = x.replace("$", " ").split()
                if not toks:
                    vals.append(None)
                for tk in toks:
                    vals.append(parse_num(tk))
                # NOTE: a bare integer token (a footnote marker) can sit alone in a cell
                # ahead of its value, e.g. "| 3 $ 1.51 |", which shifts every later column.
                # The parser keeps both tokens; _build_model.py validates per-share values
                # against net income / shares and repairs the shift.
            # merge "$ | 1,234" artifacts are already collapsed; drop all-empty duplicates columns later
            body.append([label, vals])
        unit = next((md_lines[x].strip() for x in range(i, j) if md_lines[x].strip().startswith("(")), "")
        return {"headers": hdr, "rows": body, "line": i + 1, "table_line": j + 1, "unit": unit}
    return None


res = {}
for d in sorted(glob.glob(os.path.join(A, "KO-coca-cola*/FY*"))):
    om = json.load(open(os.path.join(d, "output_manifest.json")))
    tgt = d.split("ten_k/")[1]
    if "8K" in tgt:
        continue
    md_path = os.path.join(d, om["package_path"], "prepared/document.md")
    lines = open(md_path, encoding="utf-8").read().split("\n")
    is_q = "10Q" in tgt
    key = tgt.replace("KO-coca-cola-10Q-", "10Q-").replace("KO-coca-cola/", "10K-")
    entry = {"accession": om["source"]["accession"], "md_path": os.path.relpath(md_path, root)}
    for kind in ("IS", "BS", "CF"):
        entry[kind] = extract(lines, kind, is_q)
    res[key] = entry
    print(key, {k: (len(v["rows"]) if v else None) for k, v in entry.items() if k in ("IS", "BS", "CF")})
json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
