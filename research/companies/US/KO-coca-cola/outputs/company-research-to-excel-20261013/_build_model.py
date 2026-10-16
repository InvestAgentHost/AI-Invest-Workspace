#!/usr/bin/env python3
"""Build KO model.json (bundle-only style, SKILL.md Phases 3-4) from the prepared SEC filing Markdown.

Inputs : statements_raw.json (written by _extract_statements.py) + segment/geography tables parsed here
Output : model.json  (no valuation sheets by design)
Usage  : python -I _build_model.py <workspace_root> <work_dir>
"""
import hashlib
import json
import os
import re
import sys

ROOT, WORK = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
RAW = json.load(open(os.path.join(WORK, "statements_raw.json")))

A = [f"FY{y}" for y in range(2016, 2026)]
AEND = {f"FY{y}": f"{y}-12-31" for y in range(2016, 2026)}
Q = ["3Q2024", "1Q2025", "2Q2025", "3Q2025", "1Q2026", "2Q2026"]
QEND = {"3Q2024": "2024-09-27", "1Q2025": "2025-03-28", "2Q2025": "2025-06-27",
        "3Q2025": "2025-09-26", "1Q2026": "2026-04-03", "2Q2026": "2026-07-03"}
QKEY = {"3Q2024": "10Q-Q3/FY2024", "1Q2025": "10Q-Q1/FY2025", "2Q2025": "10Q-Q2/FY2025",
        "3Q2025": "10Q-Q3/FY2025", "1Q2026": "10Q-Q1/FY2026", "2Q2026": "10Q-Q2/FY2026"}
WARN = []


# ---------------------------------------------------------------- helpers ----
def norm(label):
    t = label.lower().replace("—", "-").replace("’", "'").replace("–", "-")
    t = re.sub(r"\s+\d+$", "", t.strip())  # trailing footnote marker
    t = re.sub(r"\s+", " ", t).strip()
    return t


ALIAS = {
    "income from continuing operations before income taxes": "income before income taxes",
    "income taxes from continuing operations": "income taxes",
    "less: net income attributable to noncontrolling interests": "less: net income (loss) attributable to noncontrolling interests",
    "prepaid expenses and other assets": "prepaid expenses and other current assets",
    "other assets": "other noncurrent assets",
    "other liabilities": "other noncurrent liabilities",
    "average shares outstanding": "average shares outstanding - basic",
    "average shares outstanding assuming dilution": "average shares outstanding - diluted",
    "significant (gains) losses on sales of assets - net": "significant (gains) losses - net",
    "the coca-cola company shareowners' equity": "the coca-cola company shareowners' equity",
    "issuances of loans, notes payable and long-term debt": "issuances of debt",
    "payments of loans, notes payable and long-term debt": "payments of debt",
}


STMT = [""]


def canon(label):
    n = norm(label)
    if STMT[0] == "BS" and n == "deferred income taxes":
        return "deferred income tax liabilities"
    if n.startswith("trade accounts receivable"):
        return "trade accounts receivable, less allowances"
    if n.startswith("treasury stock, at cost"):
        return "treasury stock, at cost"
    if n.startswith("common stock"):
        return "common stock, $0.25 par value"
    if n in ("assets held for sale - discontinued operations", "liabilities held for sale - discontinued operations"):
        return n
    if n.startswith("property, plant and equipment, less accumulated"):
        return "property, plant and equipment - net"
    n = n.replace("during the period", "during the year").replace("at beginning of period", "at beginning of year").replace("at end of period", "at end of year")
    if n == "net cash provided by (used in) operating activities":
        return "net cash provided by operating activities"
    if n.startswith("income (loss) from discontinued operations") or n.startswith("income from discontinued operations"):
        return "income (loss) from discontinued operations, net of taxes"
    return ALIAS.get(n, n)


def pretty(label):
    t = re.sub(r"\s+\d+$", "", label.strip())
    t = t.replace("’", "'")
    if t.isupper():
        t = t.capitalize().replace("coca-cola", "Coca-Cola").replace("Coca-cola", "Coca-Cola")
    if t.startswith("Trade accounts receivable"):
        t = "Trade accounts receivable, less allowances"
    if t.startswith("Treasury stock, at cost"):
        t = "Treasury stock, at cost"
    if t.lower().startswith("common stock"):
        t = "Common stock, $0.25 par value"
    if t.lower().startswith("income (loss) from discontinued operations") or t.lower().startswith("income from discontinued operations"):
        t = "Income (loss) from discontinued operations, net of income taxes"
    return t


def slug(text, used):
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:44] or "row"
    base, i = s, 2
    while s in used:
        s, i = f"{base}_{i}", i + 1
    used.add(s)
    return s


def file_sha(path):
    return hashlib.sha256(open(os.path.join(ROOT, path), "rb").read()).hexdigest()


def years_of(headers, kind):
    out = []
    for h in headers[1:]:
        m = re.search(r"(20\d\d)", h)
        if m:
            out.append(int(m.group(1)))
    return out


def src_filing(year, stmt):
    return min(year + (1 if stmt == "BS" else 2), 2025)


# --------------------------------------------------- statement master lists ----
def build_statement(stmt):
    STMT[0] = stmt
    """Return ordered master [{cid,label,section}], values {cid:{period:val}}, origin {period: filing_key}."""
    keys = [f"10K-FY{y}" for y in range(2025, 2015, -1)]  # newest first
    master = []  # list of cids in order
    display = {}
    for k in keys:
        rows = RAW[k][stmt]["rows"]
        seq = []
        for lab, vals in rows:
            if not lab or lab.startswith("(In millions") or lab.startswith("(in millions"):
                continue
            seq.append(canon(lab))
            display.setdefault(canon(lab), pretty(lab))
        prev = None
        for cid in seq:
            if cid in master:
                prev = cid
                continue
            if prev is None:
                master.insert(0, cid)
            else:
                master.insert(master.index(prev) + 1, cid)
            prev = cid
    values = {c: {} for c in master}
    origin = {}
    for y in range(2016, 2026):
        fy = src_filing(y, stmt)
        k = f"10K-FY{fy}"
        t = RAW[k][stmt]
        yrs = years_of(t["headers"], stmt)
        if y not in yrs:
            WARN.append(f"{stmt} FY{y}: not in {k} headers {t['headers']}")
            continue
        col = yrs.index(y)
        origin[f"FY{y}"] = k
        for lab, vals in t["rows"]:
            if not lab or lab.lower().startswith("(in millions"):
                continue
            v = [x for x in vals]
            if len(v) < len(yrs):
                if all(x is None for x in v):
                    continue
            if col >= len(v):
                WARN.append(f"{stmt} FY{y} {k} '{lab[:40]}' has {len(v)} values for {len(yrs)} years: {v}")
                continue
            x = v[col]
            if isinstance(x, str):
                continue
            if x is not None and canon(lab) in values:
                values[canon(lab)][f"FY{y}"] = x
    # EPS sanity repair: a footnote marker printed in its own cell shifts the token
    # stream (e.g. FY2018 10-K prints "| $ 1.51 | $ 0.29 | 3 $ 1.51 |").  Validate every
    # per-share value against net income / weighted-average shares and take the next
    # token in the same row when the parsed value fails.
    if stmt == "IS":
        import math
        ni_c, wd_c, wb_c = "net income attributable to shareowners of the coca-cola company", "average shares outstanding - diluted", "average shares outstanding - basic"
        for y in range(2016, 2026):
            fy = src_filing(y, stmt)
            t_ = RAW[f"10K-FY{fy}"][stmt]
            yrs_ = years_of(t_["headers"], stmt)
            if y not in yrs_:
                continue
            col_ = yrs_.index(y)
            base = values.get(ni_c, {}).get(f"FY{y}")
            dsh = values.get(wd_c, {}).get(f"FY{y}")
            bsh = values.get(wb_c, {}).get(f"FY{y}")
            if base is None or not dsh:
                continue
            toks_by_label = {}
            for lab, vals in t_["rows"]:
                toks_by_label[canon(lab)] = vals
            for cid in ("basic net income per share", "diluted net income per share"):
                if cid not in values or f"FY{y}" not in values[cid]:
                    continue
                exp = base / (bsh if cid.startswith("basic") else dsh)
                cur = values[cid][f"FY{y}"]
                if abs(cur - exp) <= 0.06:
                    continue
                row = toks_by_label.get(cid, [])
                cand = [x for x in row if isinstance(x, (int, float)) and abs(x - exp) <= 0.06]
                if cand:
                    WARN.append(f"EPS repair FY{y} {cid}: {cur} -> {cand[0]} (expected ~{exp:.2f}) in FY{fy} 10-K")
                    values[cid][f"FY{y}"] = cand[0]
                else:
                    WARN.append(f"EPS repair FY{y} {cid}: {cur} unexplained, expected ~{exp:.2f}; left as filed")

    # quarterly
    for q in Q:
        t = RAW[QKEY[q]][stmt]
        origin[q] = QKEY[q]
        for lab, vals in t["rows"]:
            if not lab or lab.lower().startswith("(in millions"):
                continue
            c = canon(lab)
            if not vals:
                continue
            x = vals[0]
            if isinstance(x, str) or x is None:
                continue
            if c not in values:
                # new line only in a 10-Q: insert after predecessor in that 10-Q
                seq = [canon(l) for l, _ in t["rows"] if l]
                i = seq.index(c)
                pos = 0
                for p in reversed(seq[:i]):
                    if p in master:
                        pos = master.index(p) + 1
                        break
                master.insert(pos, c)
                display[c] = pretty(lab)
                values[c] = {}
                WARN.append(f"{stmt} {q}: line '{lab}' not in any 10-K; inserted after predecessor")
            values[c][q] = x
    return master, display, values, origin


# --------------------------------------------------------------- row makers ----
BOLD_PAT = re.compile(r"^(total|net cash|gross profit|operating income|consolidated net income|net income attributable|income before|equity attributable|net increase|cash, cash equivalents, restricted cash and restricted cash equivalents at end|cash and cash equivalents at end)")


def fmt_for(cid):
    if "per share" in cid:
        return "ps"
    return "num"


def make_rows(stmt, master, display, values, used):
    rows, idmap = [], {}
    for cid in master:
        v = values[cid]
        rid = slug(display[cid], used)
        idmap[cid] = rid
        r = {"id": rid, "label": display[cid], "type": "input", "values": v}
        if not v:
            r["bold"] = True  # section header
        elif BOLD_PAT.match(cid):
            r["bold"] = True
            r["border_top"] = True
        else:
            r["indent"] = 1
        if "per share" in cid:
            r["fmt"] = "ps"
            r.pop("indent", None)
        rows.append(r)
    return rows, idmap


def add_notes(rows, notes):
    byid = {r["id"]: r for r in rows}
    for rid, text in notes.items():
        if rid in byid:
            byid[rid]["note"] = text


def insert_after(rows, rid, new):
    for i, r in enumerate(rows):
        if r.get("id") == rid:
            rows[i + 1:i + 1] = new
            return
    rows.extend(new)


def M(idmap, *cands):
    for c in cands:
        if c in idmap:
            return idmap[c]
    raise KeyError(cands)


def T(idmap, *cands):
    return M(idmap, *cands)


# ------------------------------------------------------------------- IS -------
is_master, is_disp, is_vals, is_origin = build_statement("IS")
used_is = set()
is_rows, IS = make_rows("IS", is_master, is_disp, is_vals, used_is)
rev, cogs, gp = IS["net operating revenues"], IS["cost of goods sold"], IS["gross profit"]
sga, ooc, oi = IS["selling, general and administrative expenses"], IS["other operating charges"], IS["operating income"]
ii, ie = IS["interest income"], IS["interest expense"]
eq, oth = IS["equity income (loss) - net"], IS["other income (loss) - net"]
ebt, tax, cni = IS["income before income taxes"], IS["income taxes"], IS["consolidated net income"]
nci = IS["less: net income (loss) attributable to noncontrolling interests"]
nia = IS["net income attributable to shareowners of the coca-cola company"]
beps = IS["basic net income per share"]
deps = IS["diluted net income per share"]
wb, wd = IS["average shares outstanding - basic"], IS["average shares outstanding - diluted"]
for r in is_rows:
    if r["id"] == rev:
        r["bold"] = True
is_rows = [r for r in is_rows if not (r.get("label", "").lower().startswith("(in millions"))]
insert_after(is_rows, rev, [{"id": "rev_yoy", "label": "  YoY Growth", "type": "growth_yoy", "of": rev, "fmt": "pct", "memo": True, "max_label": "FY2025"}])
insert_after(is_rows, gp, [{"id": "gross_margin", "label": "  Gross Margin", "type": "calc", "expr": f"{{{gp}}}/{{{rev}}}", "fmt": "pct", "memo": True}])
insert_after(is_rows, oi, [
    {"id": "op_margin", "label": "  Operating Margin", "type": "calc", "expr": f"{{{oi}}}/{{{rev}}}", "fmt": "pct", "memo": True},
    {"id": "oi_yoy", "label": "  YoY Growth", "type": "growth_yoy", "of": oi, "fmt": "pct", "memo": True, "max_label": "FY2025"}])
insert_after(is_rows, tax, [{"id": "eff_tax_rate", "label": "  Effective Tax Rate", "type": "calc", "expr": f"{{{tax}}}/{{{ebt}}}", "fmt": "pct", "memo": True}])
insert_after(is_rows, nia, [
    {"id": "net_margin", "label": "  Net Margin (attributable)", "type": "calc", "expr": f"{{{nia}}}/{{{rev}}}", "fmt": "pct", "memo": True},
    {"id": "ni_yoy", "label": "  YoY Growth", "type": "growth_yoy", "of": nia, "fmt": "pct", "memo": True, "max_label": "FY2025"}])
add_notes(is_rows, {
    ebt: "FY2016 from the FY2018 10-K: income from continuing operations before income taxes.",
    IS["income (loss) from discontinued operations, net of taxes"] if "income (loss) from discontinued operations, net of taxes" in IS else "": "Shown only where the latest filing presenting the year reports it.",
})
is_chk = [
    {"id": "is_chk_gp", "label": "Check: Revenue - COGS - Gross profit (≈0)", "type": "check", "expr": f"{{{rev}}}-{{{cogs}}}-{{{gp}}}", "fmt": "num", "memo": True},
    {"id": "is_chk_oi", "label": "Check: Gross profit - SG&A - Other operating charges - Operating income (≈0)", "type": "check", "expr": f"{{{gp}}}-{{{sga}}}-{{{ooc}}}-{{{oi}}}", "fmt": "num", "memo": True},
    {"id": "is_chk_ebt", "label": "Check: Operating income + interest income - interest expense + equity income + other - EBT (≈0)", "type": "check", "expr": f"{{{oi}}}+{{{ii}}}-{{{ie}}}+{{{eq}}}+{{{oth}}}-{{{ebt}}}", "fmt": "num", "memo": True},
    {"id": "is_chk_ni", "label": "Check: EBT - income taxes - consolidated net income (≈0)", "type": "check", "expr": f"{{{ebt}}}-{{{tax}}}-{{{cni}}}", "fmt": "num", "memo": True},
    {"id": "is_chk_nia", "label": "Check: Consolidated NI - NCI - NI attributable (≈0)", "type": "check", "expr": f"{{{cni}}}-{{{nci}}}-{{{nia}}}", "fmt": "num", "memo": True},
]
# EPS and share-count are already in as-reported rows; add an implied-EPS check
is_chk.append({"id": "is_chk_eps", "label": "Check: NI attributable / diluted shares - diluted EPS (rounding, ≈0)", "type": "check", "expr": f"{{{nia}}}/{{{wd}}}-{{{deps}}}", "fmt": "ps", "memo": True, "expect_nonzero": True})
is_blocks = [
    {"title": "INCOME STATEMENT — AS REPORTED (expenses shown positive, as filed)", "rows": is_rows},
    {"title": "CHECKS", "rows": is_chk},
]

# ------------------------------------------------------------------- BS -------
bs_master, bs_disp, bs_vals, bs_origin = build_statement("BS")
used_bs = set()
bs_rows, BS = make_rows("BS", bs_master, bs_disp, bs_vals, used_bs)
bs_rows = [r for r in bs_rows if not r["label"].lower().startswith("(in millions")]
g = lambda c: BS.get(c)
tca, ta = BS["total current assets"], BS["total assets"]
tcl = BS["total current liabilities"]
tle = BS["total liabilities and equity"]
teq = BS["total equity"]
eqa = BS["equity attributable to shareowners of the coca-cola company"]
ncieq = BS["equity attributable to noncontrolling interests"]
cash, sti = BS["cash and cash equivalents"], BS["short-term investments"]
ms = BS["marketable securities"]
ar = BS["trade accounts receivable, less allowances"]
inv = BS["inventories"]
ltd = BS["long-term debt"]
lnp, cmd = BS["loans and notes payable"], BS["current maturities of long-term debt"]
apae = BS["accounts payable and accrued expenses"]
ca_items = [BS[c] for c in ("total cash, cash equivalents and short-term investments", "marketable securities", "trade accounts receivable, less allowances", "inventories", "prepaid expenses and other current assets", "assets held for sale", "assets held for sale - discontinued operations") if c in BS]
nca_items = [BS[c] for c in ("equity method investments", "other investments", "other noncurrent assets", "deferred income tax assets", "property, plant and equipment - net", "trademarks with indefinite lives", "bottlers' franchise rights with indefinite lives", "goodwill", "other intangible assets") if c in BS]
cl_items = [BS[c] for c in ("accounts payable and accrued expenses", "loans and notes payable", "current maturities of long-term debt", "accrued income taxes", "liabilities held for sale", "liabilities held for sale - discontinued operations") if c in BS]
ncl_items = [BS[c] for c in ("long-term debt", "other noncurrent liabilities", "deferred income tax liabilities") if c in BS]
eq_items = [BS[c] for c in ("common stock, $0.25 par value", "capital surplus", "reinvested earnings", "accumulated other comprehensive income (loss)", "treasury stock, at cost") if c in BS]
S = lambda items: "+".join(f"{{{i}}}" for i in items)
bs_chk = [
    {"id": "bs_chk_cash", "label": "Check: Cash + short-term investments - subtotal (≈0)", "type": "check", "expr": f"{{{cash}}}+{{{sti}}}-{{{BS['total cash, cash equivalents and short-term investments']}}}", "fmt": "num", "memo": True},
    {"id": "bs_chk_tca", "label": "Check: Current asset lines - Total current assets (≈0)", "type": "check", "expr": f"{S(ca_items)}-{{{tca}}}", "fmt": "num", "memo": True},
    {"id": "bs_chk_ta", "label": "Check: Total current + non-current assets - Total assets (≈0)", "type": "check", "expr": f"{{{tca}}}+{S(nca_items)}-{{{ta}}}", "fmt": "num", "memo": True},
    {"id": "bs_chk_tcl", "label": "Check: Current liability lines - Total current liabilities (≈0)", "type": "check", "expr": f"{S(cl_items)}-{{{tcl}}}", "fmt": "num", "memo": True},
    {"id": "bs_chk_eq", "label": "Check: Equity components - Equity attributable to shareowners (≈0)", "type": "check", "expr": f"{S(eq_items)}-{{{eqa}}}", "fmt": "num", "memo": True},
    {"id": "bs_chk_teq", "label": "Check: Equity attributable + NCI - Total equity (≈0)", "type": "check", "expr": f"{{{eqa}}}+{{{ncieq}}}-{{{teq}}}", "fmt": "num", "memo": True},
    {"id": "bs_chk_tle", "label": "Check: Current + non-current liabilities + total equity - Total liabilities and equity (≈0)", "type": "check", "expr": f"{{{tcl}}}+{S(ncl_items)}+{{{teq}}}-{{{tle}}}", "fmt": "num", "memo": True},
    {"id": "bs_check", "label": "Balance Check: Total assets - Total liabilities and equity (≈0)", "type": "check", "expr": f"{{{ta}}}-{{{tle}}}", "fmt": "num", "memo": True},
]
wc = [
    {"id": "wc_dso", "label": "Days Sales Outstanding", "type": "calc", "expr": f"{{{ar}}}/{{IS:{rev}}}*365", "expr_q": f"{{{ar}}}/{{IS:{rev}}}*91", "fmt": "num1", "memo": True},
    {"id": "wc_dio", "label": "Days Inventory Outstanding", "type": "calc", "expr": f"{{{inv}}}/{{IS:{cogs}}}*365", "expr_q": f"{{{inv}}}/{{IS:{cogs}}}*91", "fmt": "num1", "memo": True},
    {"id": "wc_dpo", "label": "Days Payable Outstanding (accounts payable and accrued expenses)", "type": "calc", "expr": f"{{{apae}}}/{{IS:{cogs}}}*365", "expr_q": f"{{{apae}}}/{{IS:{cogs}}}*91", "fmt": "num1", "memo": True},
    {"id": "wc_ccc", "label": "Cash Conversion Cycle", "type": "calc", "expr": "{wc_dso}+{wc_dio}-{wc_dpo}", "fmt": "num1", "memo": True},
]
bs_blocks = [
    {"title": "BALANCE SHEET — AS REPORTED (year-end values from the first 10-K after the year-end; quarterly columns are 10-Q period-end)", "rows": bs_rows},
    {"title": "CHECKS", "rows": bs_chk},
    {"title": "WORKING CAPITAL ANALYTICS (quarterly uses 91 days; the 10-Q IS is a three-month column)", "rows": wc},
]

# ------------------------------------------------------------------- CF -------
cf_master, cf_disp, cf_vals, cf_origin = build_statement("CF")
used_cf = set()
cf_rows, CF = make_rows("CF", cf_master, cf_disp, cf_vals, used_cf)
cf_rows = [r for r in cf_rows if not r["label"].lower().startswith("(in millions")]
# section anchors
i_op, i_inv, i_fin = CF["operating activities"], CF["investing activities"], CF["financing activities"]
cfo = CF["net cash provided by operating activities"]
cfi = CF["net cash provided by (used in) investing activities"]
cff = CF["net cash provided by (used in) financing activities"]
fx = CF["effect of exchange rate changes on cash, cash equivalents, restricted cash and restricted cash equivalents"]
netchg = [CF[c] for c in cf_master if c.startswith("net increase (decrease) in cash")][0]
capex = CF["purchases of property, plant and equipment"]
da = CF["depreciation and amortization"]
divs, buyb = CF["dividends"], CF["purchases of stock for treasury"]
cf_ids = [CF[c] for c in cf_master]


def section(start_id, end_id, exclude=()):
    a, b = cf_ids.index(start_id), cf_ids.index(end_id)
    out = []
    for rid in cf_ids[a + 1:b]:
        r = next(x for x in cf_rows if x["id"] == rid)
        if not r["values"] or rid in exclude:
            continue
        out.append(rid)
    return out


excl_op = [CF[c] for c in ("net income from continuing operations",) if c in CF]
op_items = section(i_op, cfo, excl_op)
inv_items = section(i_inv, cfi)
fin_items = section(i_fin, cff)
disc_net = CF.get("net cash provided by (used in) discontinued operations")
for rid in [CF[c] for c in cf_master if "from discontinued operations" in c and "net cash" in c]:
    if rid in fin_items:
        fin_items.remove(rid)
for rid in list(fin_items):
    if rid == disc_net:
        fin_items.remove(rid)
# discontinued-ops sub-lines sit between financing and total; keep them out of cff sum
cf_chk = [
    {"id": "cf_chk_cfo", "label": "Check: Operating lines - Net cash provided by operating activities (≈0)", "type": "check", "expr": f"{S(op_items)}-{{{cfo}}}", "fmt": "num", "memo": True},
    {"id": "cf_chk_cfi", "label": "Check: Investing lines - Net cash from investing activities (≈0)", "type": "check", "expr": f"{S(inv_items)}-{{{cfi}}}", "fmt": "num", "memo": True},
    {"id": "cf_chk_cff", "label": "Check: Financing lines - Net cash from financing activities (≈0)", "type": "check", "expr": f"{S(fin_items)}-{{{cff}}}", "fmt": "num", "memo": True},
    {"id": "cf_check", "label": "Cash Walk Check: CFO + CFI + CFF (+ discontinued ops) + FX - Net change in cash (≈0)", "type": "check",
     "expr": f"{{{cfo}}}+{{{cfi}}}+{{{cff}}}" + (f"+{{{disc_net}}}" if disc_net else "") + f"+{{{fx}}}-{{{netchg}}}", "fmt": "num", "memo": True},
]
fcf = [
    {"id": "fcf", "label": "Free Cash Flow (CFO + purchases of PP&E; analyst calculation)", "type": "calc", "expr": f"{{{cfo}}}+{{{capex}}}", "bold": True, "fmt": "num"},
    {"id": "fcf_yoy", "label": "  YoY Growth", "type": "growth_yoy", "of": "fcf", "fmt": "pct", "memo": True, "max_label": "FY2025"},
    {"id": "capex_pct", "label": "  Capex % of Revenue", "type": "calc", "expr": f"0-{{{capex}}}/{{IS:{rev}}}", "expr_q": f"0-{{{capex}}}/{{IS:{rev}}}", "fmt": "pct", "memo": True, "max_label": "FY2025"},
    {"id": "fcf_margin", "label": "  FCF Margin", "type": "calc", "expr": f"{{fcf}}/{{IS:{rev}}}", "fmt": "pct", "memo": True, "max_label": "FY2025"},
    {"id": "fcf_conversion", "label": "  FCF / Net income attributable", "type": "calc", "expr": f"{{fcf}}/{{IS:{nia}}}", "fmt": "pct", "memo": True, "max_label": "FY2025"},
    {"id": "sh_returns", "label": "Cash returned to shareowners (dividends + treasury purchases; shown positive)", "type": "calc", "expr": f"0-{{{divs}}}-{{{buyb}}}", "fmt": "num"},
    {"id": "sh_returns_fcf", "label": "  % of Free Cash Flow", "type": "calc", "expr": "{sh_returns}/{fcf}", "fmt": "pct", "memo": True},
]
cf_note = {
    "ytd": "Quarterly CF columns are fiscal year-to-date cumulative (Q1 = 3 months, Q2 = 6 months, Q3 = 9 months), as presented in the 10-Q. They are not discrete quarters.",
}
cf_blocks = [
    {"title": "CASH FLOW STATEMENT — AS REPORTED (quarterly columns are fiscal year-to-date)", "rows": cf_rows},
    {"title": "CHECKS", "rows": cf_chk},
    {"title": "FREE CASH FLOW AND SHAREOWNER RETURN ANALYTICS (annual; quarterly shown where inputs are YTD)", "rows": fcf},
]
# YTD cash flow rows in quarterly columns: fcf_margin etc. restricted to annual via max_label; fcf and sh_returns are YTD



# ----------------------------------------------- segments / geography parse ----
def load_md(key):
    p = RAW[key]["md_path"]
    return p, open(os.path.join(ROOT, p), encoding="utf-8").read().split("\n")


def nums_from_row(line):
    line = re.sub(r"\s*\|\s*\)", ")", line)
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    label = cells[0]
    vals = []
    for c in cells[1:]:
        for t in c.replace("$", " ").split():
            if t in ("—", "-", "–"):
                vals.append(0)
                continue
            neg = t.startswith("(") and t.endswith(")")
            s = t.strip("()").replace(",", "")
            try:
                x = float(s)
            except ValueError:
                continue
            vals.append(-int(x) if neg else int(x))
    return label, vals


YEAR_ROW = re.compile(r"^(?:As of and for the )?(?:Year Ended December 31,\s*)?(20\d\d)$|^(?:As of and for the )?Year Ended December 31,\s*(20\d\d)$")


def fit(vals, n):
    if len(vals) == n:
        return vals
    if len(vals) == 2 * n and vals[0::2] == vals[1::2]:
        return vals[0::2]
    if len(vals) > n:
        return vals[:n]
    return vals


def parse_segments(key):
    p, L = load_md(key)
    out = {}
    cols = None
    year = None
    for i, l in enumerate(L):
        if not l.startswith("|"):
            if l.strip() and not l.startswith("|") and cols is not None and year is not None and re.match(r"^\d+$|^During |^[A-Z]", l.strip()) and "Latin America" not in l:
                pass
            continue
        if "Latin America" in l and "Consolidated" in l:
            cols = [c.strip() for c in l.strip().strip("|").split("|")][1:]
            cols = [c for c in cols if c]
            year = None
            continue
        if cols is None:
            continue
        lab, vals = nums_from_row(l)
        m = YEAR_ROW.match(lab.strip())
        if m:
            year = int(m.group(1) or m.group(2))
            out.setdefault(year, {"cols": cols, "line": i + 1})
            continue
        if year is None:
            continue
        if lab.startswith("Third party") and "third_party" in out[year]:
            # a block without its own year row (descending order): the previous year
            year -= 1
            out.setdefault(year, {"cols": cols, "line": i + 1, "inferred_year": True})
        blk = out[year]
        n = len(cols)
        keymap = [("Third party", "third_party"), ("Intersegment", "interseg"), ("Total net operating revenues", "total_rev"),
                  ("Operating income", "op_income"), ("Capital expenditures", "capex"), ("Depreciation and amortization", "da")]
        for pref, k in keymap:
            if lab.startswith(pref) and k not in blk:
                blk[k] = fit(vals, n)
    return p, out


SEG_FILING = {2017: 2019, 2018: 2020, 2019: 2021, 2020: 2022, 2021: 2023, 2022: 2024, 2023: 2024, 2024: 2024}
SEGS = {}
for fy in (2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025):
    p, d = parse_segments(f"10K-FY{fy}")
    SEGS[fy] = (p, d)


def nice(c):
    return {"Europe, Middle East & Africa": "EMEA", "EMEA": "EMEA"}.get(c, c)


def seg_block_rows(prefix, label_prefix, years_src, drop_cols=("Consolidated", "Eliminations", "Operating Segments Total")):
    """years_src: {fiscal_year: filing_fy}. Returns rows for third-party revenue, intersegment,
    total revenue, operating income, D&A and capex. Intersegment and total revenue are carried
    as their own rows because a segment note's third-party column is not the consolidated
    income-statement line: the consolidated total includes intersegment revenue, so a basis
    whose note predates a restatement ties out on the total row and not on the third-party row.
    """
    cols_by_year = {y: SEGS[f][1][y]["cols"] for y, f in years_src.items()}
    base = next(iter(cols_by_year.values()))
    for y, c in cols_by_year.items():
        if c != base:
            WARN.append(f"{prefix}: segment columns differ in {y}: {c} vs {base}")
    segcols = [c for c in base if c not in drop_cols]
    rows = []
    ids = {}
    for metric, mk, title in (("third_party", "third_party", "Third-party net operating revenues"),
                              ("interseg", "interseg", "Intersegment net operating revenues"),
                              ("total_rev", "total_rev", "Total net operating revenues (third-party + intersegment)"),
                              ("op_income", "op_income", "Operating income (loss)"),
                              ("da", "da", "Depreciation and amortization"),
                              ("capex", "capex", "Capital expenditures")):
        rows.append({"id": f"{prefix}_{mk}_hdr", "label": title, "type": "input", "values": {}, "bold": True})
        kids = []
        this_cols = list(segcols)
        # intersegment and total revenue only reconcile to the Consolidated column once the
        # Eliminations column is present (intersegment revenue is eliminated on consolidation)
        if metric in ("interseg", "total_rev") and "Eliminations" in base:
            this_cols = this_cols + ["Eliminations"]
        for ci, c in enumerate(this_cols):
            vals = {}
            for y, f in years_src.items():
                blk = SEGS[f][1][y]
                arr = blk.get(mk)
                if arr is None or base.index(c) >= len(arr):
                    continue
                if blk["cols"] != base:
                    continue
                vals[f"FY{y}"] = arr[base.index(c)]
            rid = f"{prefix}_{mk}_{re.sub(r'[^a-z0-9]+', '_', c.lower()).strip('_')}"
            rows.append({"id": rid, "label": nice(c), "type": "input", "values": vals, "indent": 1})
            kids.append(rid)
        # consolidated reported
        vals = {}
        for y, f in years_src.items():
            blk = SEGS[f][1][y]
            arr = blk.get(mk)
            if arr is not None and "Consolidated" in blk["cols"]:
                vals[f"FY{y}"] = arr[blk["cols"].index("Consolidated")]
        rid = f"{prefix}_{mk}_total"
        rows.append({"id": rid, "label": "Consolidated (as reported)", "type": "input", "values": vals, "bold": True, "border_top": True})
        rows.append({"id": f"{prefix}_{mk}_chk", "label": "Check: segments + Corporate - Consolidated (≈0)", "type": "check",
                     "expr": "+".join(f"{{{k}}}" for k in kids) + f"-{{{rid}}}", "fmt": "num", "memo": True})
        rows.append({"type": "spacer"})
        ids[mk] = (kids, rid)
    # the third-party segment total excludes intersegment revenue; the IS line includes it
    tp_total = ids["third_party"][1]
    tot_total = ids["total_rev"][1]
    rows.append({"id": f"{prefix}_tp_vs_is", "label": "Info: third-party total - IS net operating revenues (differences = intersegment revenue and later restatements)", "type": "check",
                 "expr": f"{{{tp_total}}}-{{IS:{rev}}}", "fmt": "num", "memo": True, "expect_nonzero": True,
                 "min_label": min(f"FY{y}" for y in years_src), "max_label": max(f"FY{y}" for y in years_src)})
    rows.append({"id": f"{prefix}_tot_vs_is", "label": "Info: total net operating revenues - IS net operating revenues (differences = later restatements only)", "type": "check",
                 "expr": f"{{{tot_total}}}-{{IS:{rev}}}", "fmt": "num", "memo": True, "expect_nonzero": True,
                 "min_label": min(f"FY{y}" for y in years_src), "max_label": max(f"FY{y}" for y in years_src)})
    return rows, ids


for r in (is_rows, bs_rows, cf_rows):
    pass

yrsA = {2016: 2018, 2017: 2018, 2018: 2018}
yrsB = {y: SEG_FILING[y] for y in range(2017, 2025)}
yrsC = {2023: 2025, 2024: 2025, 2025: 2025}
rowsA, idsA = seg_block_rows("a", "A", yrsA)
rowsB, idsB = seg_block_rows("b", "B", yrsB)
rowsC, idsC = seg_block_rows("c", "C", yrsC)


def span(rows, lo, hi):
    for r in rows:
        if r.get("type") != "spacer":
            r["min_label"], r["max_label"] = lo, hi
    return rows


span(rowsA, "FY2016", "FY2018")
span(rowsB, "FY2017", "FY2024")
span(rowsC, "FY2023", "FY2025")


def tie_rows(prefix, ids, lo, hi):
    out = []
    kids, rid = ids["third_party"]
    out.append({"id": f"{prefix}_tie_rev", "label": "Check: segment third-party revenue vs IS net operating revenues (≈0)", "type": "check", "expr": f"{{{rid}}}-{{IS:{rev}}}", "fmt": "num", "memo": True, "min_label": lo, "max_label": hi})
    kids, rid = ids["op_income"]
    out.append({"id": f"{prefix}_tie_oi", "label": "Check: segment operating income vs IS operating income (≈0)", "type": "check", "expr": f"{{{rid}}}-{{IS:{oi}}}", "fmt": "num", "memo": True, "min_label": lo, "max_label": hi})
    kids, rid = ids["da"]
    out.append({"id": f"{prefix}_tie_da", "label": "Check: segment D&A vs CF depreciation and amortization (≈0)", "type": "check", "expr": f"{{{rid}}}-{{CF:{da}}}", "fmt": "num", "memo": True, "min_label": lo, "max_label": hi})
    kids, rid = ids["capex"]
    out.append({"id": f"{prefix}_tie_capex", "label": "Info: segment capex + CF purchases of PP&E (differences = non-cash/other definition)", "type": "check", "expr": f"{{{rid}}}+{{CF:{capex}}}", "fmt": "num", "memo": True, "min_label": lo, "max_label": hi, "expect_nonzero": True})
    return out


rowsA += tie_rows("a", idsA, "FY2016", "FY2016")
kidsR_, ridR_ = idsA["third_party"]
kidsO_, ridO_ = idsA["op_income"]
rowsA += [
    {"id": "a_info_rev", "label": "Info: basis A revenue - IS revenue (FY2017-FY2018 differ because IS uses the later recast)", "type": "check", "expr": f"{{{ridR_}}}-{{IS:{rev}}}", "fmt": "num", "memo": True, "expect_nonzero": True, "min_label": "FY2017", "max_label": "FY2018"},
    {"id": "a_info_oi", "label": "Info: basis A operating income - IS operating income (FY2017-FY2018 differ because IS uses the later recast)", "type": "check", "expr": f"{{{ridO_}}}-{{IS:{oi}}}", "fmt": "num", "memo": True, "expect_nonzero": True, "min_label": "FY2017", "max_label": "FY2018"},
]
rowsB += tie_rows("b", idsB, "FY2017", "FY2024")
rowsC += tie_rows("c", idsC, "FY2023", "FY2025")
# margins for latest basis
def seg_margins(prefix, ids, lo, hi, names):
    out = []
    kidsR, _ = ids["third_party"]
    kidsO, _ = ids["op_income"]
    for kr, ko_ in zip(kidsR, kidsO):
        lab = next(r["label"] for r in (rowsA + rowsB + rowsC) if r.get("id") == kr)
        if lab in ("Corporate", "Eliminations"):
            continue
        out.append({"id": f"{ko_}_mgn", "label": f"{lab} operating margin (op. income / third-party revenue)", "type": "calc", "expr": f"{{{ko_}}}/{{{kr}}}", "fmt": "pct", "memo": True, "min_label": lo, "max_label": hi})
    return out


rowsA += seg_margins("a", idsA, "FY2016", "FY2018", None)
rowsB += seg_margins("b", idsB, "FY2017", "FY2024", None)
rowsC += seg_margins("c", idsC, "FY2023", "FY2025", None)

seg_blocks = [
    {"title": "SEGMENTS — BASIS C (FY2025 10-K recast: Global Ventures dissolved into the geographic segments; FY2023-FY2025 only)", "rows": rowsC},
    {"title": "SEGMENTS — BASIS B (FY2019-FY2024 10-K presentation incl. Global Ventures; FY2017-FY2024, each year from the latest 10-K presenting it on this basis)", "rows": rowsB},
    {"title": "SEGMENTS — BASIS A (FY2018 10-K presentation: no Global Ventures; FY2016-FY2018)", "rows": rowsA},
]


# geography ----------------------------------------------------------------
def parse_geo(key):
    p, L = load_md(key)
    rev_, ppe_ = None, None
    for i in range(len(L) - 3):
        if L[i].startswith("| United States") and L[i + 1].startswith("| International"):
            third = L[i + 2]
            hdr = next((L[j] for j in range(i - 1, i - 4, -1) if L[j].startswith("| ") and ("Year Ended" in L[j] or "December 31" in L[j])), "")
            yrs = [int(x) for x in re.findall(r"20\d\d", hdr)]
            if third.startswith("| Net operating revenues") and rev_ is None:
                rev_ = (i + 1, yrs, nums_from_row(L[i])[1], nums_from_row(L[i + 1])[1], nums_from_row(L[i + 2])[1])
            elif third.startswith("| Property, plant and equipment") and ppe_ is None:
                ppe_ = (i + 1, yrs, nums_from_row(L[i])[1], nums_from_row(L[i + 1])[1], nums_from_row(L[i + 2])[1])
    return p, rev_, ppe_


geo_us, geo_int, geo_tot, ppe_us, ppe_int, ppe_tot = {}, {}, {}, {}, {}, {}
geo_src = {}
for y in range(2016, 2026):
    fy = min(y + 2, 2025)
    p, rv, _unused = parse_geo(f"10K-FY{fy}")
    fy2 = min(y + 1, 2025)
    p2, _unused2, pp = parse_geo(f"10K-FY{fy2}")
    geo_src[y] = (fy, p, rv[0] if rv else None, pp[0] if pp else None, fy2)
    if rv and y in rv[1]:
        ix = rv[1].index(y)
        geo_us[f"FY{y}"], geo_int[f"FY{y}"], geo_tot[f"FY{y}"] = rv[2][ix], rv[3][ix], rv[4][ix]
    else:
        WARN.append(f"geo revenue FY{y} not found in FY{fy}")
    if pp and y in pp[1]:
        ix = pp[1].index(y)
        ppe_us[f"FY{y}"], ppe_int[f"FY{y}"], ppe_tot[f"FY{y}"] = pp[2][ix], pp[3][ix], pp[4][ix]
geo_blocks = [
    {"title": "NET OPERATING REVENUES BY GEOGRAPHY (Note: Operating Segments — Geographic and Customer Data)", "rows": [
        {"id": "geo_us", "label": "United States", "type": "input", "values": geo_us, "indent": 1},
        {"id": "geo_int", "label": "International", "type": "input", "values": geo_int, "indent": 1},
        {"id": "geo_total", "label": "Net operating revenues (as reported)", "type": "input", "values": geo_tot, "bold": True, "border_top": True},
        {"id": "geo_us_mix", "label": "  United States % of revenue", "type": "calc", "expr": "{geo_us}/{geo_total}", "fmt": "pct", "memo": True, "max_label": "FY2025"},
        {"id": "geo_int_yoy", "label": "  International YoY Growth", "type": "growth_yoy", "of": "geo_int", "fmt": "pct", "memo": True, "max_label": "FY2025"},
        {"id": "geo_us_yoy", "label": "  United States YoY Growth", "type": "growth_yoy", "of": "geo_us", "fmt": "pct", "memo": True, "max_label": "FY2025"},
        {"id": "geo_chk", "label": "Check: US + International - reported total (≈0)", "type": "check", "expr": "{geo_us}+{geo_int}-{geo_total}", "fmt": "num", "memo": True},
        {"id": "geo_chk_is", "label": "Check: geography total vs IS net operating revenues (≈0)", "type": "check", "expr": f"{{geo_total}}-{{IS:{rev}}}", "fmt": "num", "memo": True},
    ]},
    {"title": "PROPERTY, PLANT AND EQUIPMENT — NET BY GEOGRAPHY", "rows": [
        {"id": "ppe_us", "label": "United States", "type": "input", "values": ppe_us, "indent": 1},
        {"id": "ppe_int", "label": "International", "type": "input", "values": ppe_int, "indent": 1},
        {"id": "ppe_total", "label": "Property, plant and equipment — net (as reported)", "type": "input", "values": ppe_tot, "bold": True, "border_top": True},
        {"id": "ppe_chk", "label": "Check: US + International - reported total (≈0)", "type": "check", "expr": "{ppe_us}+{ppe_int}-{ppe_total}", "fmt": "num", "memo": True},
        {"id": "ppe_chk_bs", "label": "Check: geography total vs BS property, plant and equipment - net (≈0)", "type": "check", "expr": f"{{ppe_total}}-{{BS:{BS['property, plant and equipment - net']}}}", "fmt": "num", "memo": True},
    ]},
]

for b in geo_blocks:
    for r in b["rows"]:
        r["max_label"] = "FY2025"

# ------------------------------------------------------------------- DM -------
ISr = lambda k: f"{{IS:{k}}}"
BSr = lambda k: f"{{BS:{k}}}"
CFr = lambda k: f"{{CF:{k}}}"
debt_now = f"({BSr(lnp)}+{BSr(cmd)}+{BSr(ltd)})"
debt_prev = f"({BSr(lnp + '@-1')}+{BSr(cmd + '@-1')}+{BSr(ltd + '@-1')})"
def bsr(k, off=""):
    return "{BS:" + k + off + "}"
debt_prev = f"({bsr(lnp,'@-1')}+{bsr(cmd,'@-1')}+{bsr(ltd,'@-1')})"
ebitda = f"({ISr(oi)}+{CFr(da)})"
cashlike = f"({BSr(cash)}+{BSr(sti)}+{BSr(ms)})"
D = lambda i, l, e, f="pct", **kw: dict({"id": i, "label": l, "type": "calc", "expr": e, "fmt": f, "memo": True, "max_label": "FY2025"}, **kw)
D1 = lambda i, l, e, f="pct": D(i, l, e, f, min_label="FY2017")
dm_blocks = [
    {"title": "1. PROFITABILITY", "rows": [
        D("dm_gross_margin", "Gross Margin", f"{ISr(gp)}/{ISr(rev)}"),
        D("dm_sga_pct", "SG&A % of Revenue", f"{ISr(sga)}/{ISr(rev)}"),
        D("dm_op_margin", "Operating Margin", f"{ISr(oi)}/{ISr(rev)}"),
        D("dm_ebitda", "EBITDA (operating income + D&A; analyst calculation)", f"{ebitda}", "num"),
        D("dm_ebitda_margin", "EBITDA Margin", f"{ebitda}/{ISr(rev)}"),
        D("dm_net_margin", "Net Margin (attributable)", f"{ISr(nia)}/{ISr(rev)}"),
        D("dm_eff_tax", "Effective Tax Rate", f"{ISr(tax)}/{ISr(ebt)}"),
        D("dm_equity_inc_share", "Equity income % of pre-tax income", f"{ISr(eq)}/{ISr(ebt)}"),
    ]},
    {"title": "2. RETURNS (average of opening and closing balances)", "rows": [
        D1("dm_roa", "ROA (NI attributable / average total assets)", f"{ISr(nia)}/({bsr(ta)}+{bsr(ta,'@-1')})*2"),
        D1("dm_roe", "ROE (NI attributable / average equity attributable)", f"{ISr(nia)}/({bsr(eqa)}+{bsr(eqa,'@-1')})*2"),
        D1("dm_roic", "ROIC (operating income x (1 - tax rate) / average equity + debt)", f"{ISr(oi)}*(1-{{dm_eff_tax}})/(({bsr(teq)}+{bsr(teq,'@-1')}+{debt_now}+{debt_prev})/2)"),
        D1("dm_asset_turn", "Asset Turnover", f"{ISr(rev)}/({bsr(ta)}+{bsr(ta,'@-1')})*2", "x"),
    ]},
    {"title": "3. LEVERAGE", "rows": [
        D("dm_debt", "Total debt (loans and notes payable + current maturities + long-term debt)", f"{debt_now}", "num"),
        D("dm_cashlike", "Cash, short-term investments and marketable securities", f"{cashlike}", "num"),
        D("dm_net_debt", "Net debt", "{dm_debt}-{dm_cashlike}", "num"),
        D("dm_nd_ebitda", "Net Debt / EBITDA", "{dm_net_debt}/{dm_ebitda}", "x"),
        D("dm_debt_equity", "Debt / Total Equity", f"{{dm_debt}}/{BSr(teq)}", "x"),
    ]},
    {"title": "4. SOLVENCY", "rows": [
        D("dm_equity_ratio", "Equity Ratio (total equity / total assets)", f"{BSr(teq)}/{BSr(ta)}"),
        D("dm_debt_assets", "Debt / Total Assets", f"{{dm_debt}}/{BSr(ta)}"),
    ]},
    {"title": "5. LIQUIDITY", "rows": [
        D("dm_current_ratio", "Current Ratio", f"{BSr(tca)}/{BSr(tcl)}", "x"),
        D("dm_quick_ratio", "Quick Ratio ((current assets - inventories) / current liabilities)", f"({BSr(tca)}-{BSr(inv)})/{BSr(tcl)}", "x"),
        D("dm_cash_ratio", "Cash Ratio ((cash + short-term investments + marketable securities) / current liabilities)", f"{{dm_cashlike}}/{BSr(tcl)}", "x"),
    ]},
    {"title": "6. COVERAGE", "rows": [
        D("dm_int_cov", "Interest Coverage (operating income / interest expense)", f"{ISr(oi)}/{ISr(ie)}", "x"),
        D("dm_cfo_int", "CFO / Interest Expense", f"{CFr(cfo)}/{ISr(ie)}", "x"),
    ]},
    {"title": "7. CASH CONVERSION", "rows": [
        D("dm_cfo_margin", "CFO Margin", f"{CFr(cfo)}/{ISr(rev)}"),
        D("dm_cfo_ebitda", "CFO / EBITDA", f"{CFr(cfo)}/{ebitda}", "x"),
        D("dm_capex_int", "Capex Intensity (purchases of PP&E / revenue)", f"0-{CFr(capex)}/{ISr(rev)}"),
        D("dm_fcf", "Free Cash Flow (CFO + purchases of PP&E)", f"{CFr('fcf')}", "num"),
        D("dm_fcf_margin", "FCF Margin", f"{CFr('fcf')}/{ISr(rev)}"),
        D("dm_fcf_conv", "FCF / Net income attributable", f"{CFr('fcf')}/{ISr(nia)}", "x"),
        D("dm_da_capex", "D&A / Capex", f"0-{CFr(da)}/{CFr(capex)}", "x"),
    ]},
    {"title": "8. EARNINGS QUALITY", "rows": [
        D("dm_cfo_ni", "CFO / Net income attributable", f"{CFr(cfo)}/{ISr(nia)}", "x"),
        D1("dm_accrual", "Accrual Ratio ((NI attributable - CFO) / average total assets)", f"({ISr(nia)}-{CFr(cfo)})/({bsr(ta)}+{bsr(ta,'@-1')})*2"),
    ]},
    {"title": "9. GROWTH", "rows": [
        D1("dm_rev_g", "Revenue Growth", f"{ISr(rev)}/{{IS:{rev}@-1}}-1"),
        D1("dm_oi_g", "Operating Income Growth", f"{ISr(oi)}/{{IS:{oi}@-1}}-1"),
        D1("dm_ni_g", "Net Income (attributable) Growth", f"{ISr(nia)}/{{IS:{nia}@-1}}-1"),
        D1("dm_eps_g", "Diluted EPS Growth", f"{ISr(deps)}/{{IS:{deps}@-1}}-1"),
        D1("dm_cfo_g", "CFO Growth", f"{CFr(cfo)}/{{CF:{cfo}@-1}}-1"),
        D1("dm_shares_g", "Diluted weighted-average shares change", f"{ISr(wd)}/{{IS:{wd}@-1}}-1"),
    ]},
    {"title": "10. SHAREOWNER RETURNS", "rows": [
        D("dm_div", "Cash dividends paid (shown positive)", f"0-{CFr(divs)}", "num"),
        D("dm_buyback", "Purchases of stock for treasury (shown positive)", f"0-{CFr(buyb)}", "num"),
        D("dm_issue", "Issuances of stock", f"{CFr(CF['issuances of stock'])}", "num"),
        D("dm_div_payout", "Dividend payout (dividends / NI attributable)", "{dm_div}" + f"/{ISr(nia)}"),
        D("dm_total_payout", "Total payout ((dividends + treasury purchases) / NI attributable)", "({dm_div}+{dm_buyback})" + f"/{ISr(nia)}"),
        D("dm_div_fcf", "Dividends % of FCF", "{dm_div}/{dm_fcf}"),
    ]},
    {"title": "11. WORKING CAPITAL", "rows": [
        D("dm_dso", "Days Sales Outstanding", f"{BSr(ar)}/{ISr(rev)}*365", "num1"),
        D("dm_dio", "Days Inventory Outstanding", f"{BSr(inv)}/{ISr(cogs)}*365", "num1"),
        D("dm_dpo", "Days Payable Outstanding (accounts payable and accrued expenses)", f"{BSr(apae)}/{ISr(cogs)}*365", "num1"),
        D("dm_ccc", "Cash Conversion Cycle", "{dm_dso}+{dm_dio}-{dm_dpo}", "num1"),
    ]},
]


# ---------------------------------------------------- label length control ----
MAXW = 70
SHORT_CAPTIONS = {
    "proceeds from disposals of businesses, equity method investments and nonmarketable securities": "Proceeds from disposals of businesses, equity method inv. & nonmkt. securities",
    "acquisitions of businesses, equity method investments and nonmarketable securities": "Acquisitions of businesses, equity method inv. & nonmkt. securities",
    "effect of exchange rate changes on cash, cash equivalents, restricted cash and restricted cash equivalents": "Effect of exchange rate changes on cash and restricted cash",
    "net increase (decrease) in cash, cash equivalents, restricted cash and restricted cash equivalents during the year": "Net increase (decrease) in cash and restricted cash",
    "cash, cash equivalents, restricted cash and restricted cash equivalents at beginning of year": "Cash and restricted cash at beginning of year",
    "cash, cash equivalents, restricted cash and restricted cash equivalents at end of year": "Cash and restricted cash at end of year",
    "cash, cash equivalents, restricted cash and restricted cash equivalents": "Cash and restricted cash",
    "adjustments to reconcile consolidated net income to net cash provided by operating activities:": "Adjustments to reconcile net income to operating cash flow:",
    "net cash provided by (used in) operating activities from discontinued operations": "Net cash from operating activities - discontinued operations",
    "net cash provided by (used in) investing activities from discontinued operations": "Net cash from investing activities - discontinued operations",
    "net cash provided by (used in) financing activities from discontinued operations": "Net cash from financing activities - discontinued operations",
}
CHECK_SHORT = {
    "Check: Operating income + interest income - interest expense + equity income + other - EBT (≈0)": "Check: Operating income to pre-tax income bridge (≈0)",
    "Check: Gross profit - SG&A - Other operating charges - Operating income (≈0)": "Check: Gross profit - SG&A - other charges - Op. income (≈0)",
    "Check: Current + non-current liabilities + total equity - Total liabilities and equity (≈0)": "Check: Liabilities + equity components - Total L&E (≈0)",
    "Check: Total current + non-current assets - Total assets (≈0)": "Check: Current + non-current assets - Total assets (≈0)",
    "Cash Walk Check: CFO + CFI + CFF (+ discontinued ops) + FX - Net change in cash (≈0)": "Cash walk check: CFO+CFI+CFF(+disc.)+FX - net change (≈0)",
    "Check: Operating lines - Net cash provided by operating activities (≈0)": "Check: Operating lines - Net cash from operations (≈0)",
    "Info: segment capex + CF purchases of PP&E (differences = non-cash/other definition)": "Info: segment capex + CF purchases of PP&E (definitions differ)",
    "Info: basis A revenue - IS revenue (FY2017-FY2018 differ because IS uses the later recast)": "Info: basis A revenue - IS revenue (IS uses later recast)",
    "Info: basis A operating income - IS operating income (FY2017-FY2018 differ because IS uses the later recast)": "Info: basis A op. income - IS op. income (IS uses later recast)",
    "Cash returned to shareowners (dividends + treasury purchases; shown positive)": "Cash returned to shareowners (dividends + buybacks, positive)",
    "Free Cash Flow (CFO + purchases of PP&E; analyst calculation)": "Free cash flow (CFO + PP&E purchases; analyst calc.)",
    "Days Payable Outstanding (accounts payable and accrued expenses)": "Days Payable Outstanding (AP and accrued expenses)",
}
def fix_labels(blocks):
    for b in blocks:
        for r in b["rows"]:
            l = r.get("label")
            if not l:
                continue
            key = norm(l)
            if key in SHORT_CAPTIONS:
                r["note"] = (r.get("note", "") + " Filed caption: " + l).strip()
                r["label"] = SHORT_CAPTIONS[key]
            elif l in CHECK_SHORT:
                r["label"] = CHECK_SHORT[l]
            if len(r["label"]) + 3 * r.get("indent", 0) > MAXW:
                r["note"] = (r.get("note", "") + " Full label: " + r["label"]).strip()
                r["label"] = r["label"][: MAXW - 3 * r.get("indent", 0) - 1].rstrip() + "…"


for _b in (is_blocks, bs_blocks, cf_blocks, seg_blocks, geo_blocks, dm_blocks):
    fix_labels(_b)

# ------------------------------------------------- restatement comparison ----
def stmt_val(key, stmt, cid, year):
    t = RAW[key][stmt]
    yrs = years_of(t["headers"], stmt)
    if year not in yrs:
        return None
    for lab, vals in t["rows"]:
        if lab and canon(lab) == cid:
            x = vals[yrs.index(year)] if yrs.index(year) < len(vals) else None
            return None if isinstance(x, str) else x
    return None


restate = []
STMT[0] = "IS"
for y in range(2016, 2025):
    used = f"10K-FY{src_filing(y, 'IS')}"
    orig = f"10K-FY{y}"
    for nm, cid in (("Net operating revenues", "net operating revenues"), ("Operating income", "operating income"),
                    ("Consolidated net income", "consolidated net income"),
                    ("Net income attributable to shareowners", "net income attributable to shareowners of the coca-cola company")):
        a, b = stmt_val(orig, "IS", cid, y), stmt_val(used, "IS", cid, y)
        if a is not None and b is not None and a != b:
            restate.append((f"FY{y}", nm, a, b, orig, used))
STMT[0] = "CF"
for y in range(2016, 2025):
    used = f"10K-FY{src_filing(y, 'CF')}"
    orig = f"10K-FY{y}"
    a = stmt_val(orig, "CF", "net cash provided by operating activities", y)
    b = stmt_val(used, "CF", "net cash provided by operating activities", y)
    if a is not None and b is not None and a != b:
        restate.append((f"FY{y}", "Net cash provided by operating activities", a, b, orig, used))
print("restatements:", len(restate))
for r in restate:
    print("  ", r)

# ------------------------------------------------------------- cover/sources ----
def hdr(t):
    return [{"text": t, "bold": True}]


cover = [
    hdr("The Coca-Cola Company (NYSE: KO)"),
    [],
    ["Ticker / exchange", "KO / NYSE"],
    ["CIK", "0000021344"],
    ["Reporting framework", "US GAAP, consolidated"],
    ["Currency / units", "USD; $ in millions except per-share data"],
    ["Fiscal year end", "December 31 (10-Q quarters end on the Friday nearest the calendar quarter end)"],
    ["Annual window", "FY2016-FY2025 (ten 10-Ks)"],
    ["Quarterly window", "3Q2024, 1Q2025, 2Q2025, 3Q2025, 1Q2026, 2Q2026 (six 10-Qs; no 4Q columns because a 10-K is not a quarterly filing)"],
    ["Latest covered period", "2Q2026 (quarter ended July 3, 2026; 10-Q filed 2026-07-29)"],
    ["Workbook date", "2026-10-13"],
    [],
    hdr("Sheet directory"),
    ["Income Statement (IS)", "As-reported income statement, growth/margin rows, six tie-out checks"],
    ["Balance Sheet (BS)", "As-reported balance sheet, eight tie-out checks, working-capital days"],
    ["Cash Flow (CF)", "As-reported cash flow statement (quarterly columns are fiscal year-to-date), four checks, FCF and shareowner-return analytics"],
    ["Segments (SEG)", "Three segment bases kept separate (A: FY2016-FY2018, B: FY2017-FY2024, C: FY2023-FY2025), each tied to consolidated totals"],
    ["Geography (GEO)", "US / International net operating revenues and PP&E"],
    ["Derived Metrics (DM)", "Ratios computed as live formulas from IS/BS/CF; annual only"],
    ["Operating Metrics (OPS)", "System unit case volume, unit case and concentrate sales volume growth by segment, the net operating revenue factor table (volume / price-mix / FX / acquisitions & divestitures), revenue by line of business (concentrate vs finished product), segment revenue mix and customer concentration. All from the 10-K MD&A and Note 3; annual only."],
    ["Note Schedules (NOTE)", "Equity method investees (aggregate financials and the Company's share), fair value vs carrying value of publicly traded investees, income taxes (pre-tax by jurisdiction, current/deferred, unrecognized tax benefits roll-forward), long-term debt by type and assets and liabilities held for sale. All from Notes 2, 6, 11 and 15; annual only."],
    ["Sources", "Filing accessions, file paths, SHA-256, annual-column provenance, restatement log"],
    [],
    hdr("Colour legend"),
    ["Blue font", "Hard-coded value copied from a filing"],
    ["Black font", "Formula"],
    ["Green font", "Cross-sheet link"],
    ["Grey italic", "Memo / analytic row"],
    [],
    hdr("How annual columns were sourced"),
    ["Income statement and cash flow", "Each fiscal year is taken from the 10-K filed two years later (or the FY2025 10-K for FY2024 and FY2025), so later reclassifications are reflected. The first-filed value is compared with the value used in the Sources sheet."],
    ["Balance sheet", "Each year-end is taken from the 10-K for the following year (the FY2025 10-K for FY2025), i.e. the later comparative column."],
    ["Quarterly", "IS: three-month column of each 10-Q. BS: period-end balance of each 10-Q. CF: fiscal year-to-date column of each 10-Q (Q1 = 3 months, Q2 = 6 months, Q3 = 9 months)."],
    [],
    hdr("Comparability notes"),
    ["Sign convention", "Income-statement expenses are shown positive as filed (cost of goods sold, SG&A, interest expense, income taxes). Cash-flow outflows are negative as filed."],
    ["Discontinued operations", "FY2016-FY2018 filings present a discontinued-operations line (FY2017-FY2018). The latest filing presenting each year is used, so FY2017 and FY2018 follow the FY2019 and FY2020 10-K presentation."],
    ["Recast years", "Later 10-Ks recast earlier years: FY2016 operating income (FY2018 10-K), FY2017 and FY2018 net operating revenues and operating income (FY2019 and FY2020 10-Ks), and operating cash flow for FY2016-FY2018. FY2016 is on the older pre-recast basis because no later 10-K presents it; FY2016-to-FY2017 growth rates therefore mix bases. The differences are listed in the Sources sheet; the cause is not analysed here."],
    ["Caption changes", "FY2021 onward: 'prepaid expenses and other current assets', 'other noncurrent assets/liabilities' replace earlier captions; debt issuance/payment captions were renamed in the FY2023 10-K with identical values. Equivalent lines share one row."],
    ["Segments", "KO re-segmented in the FY2019 10-K (Global Ventures added) and again in the FY2025 10-K (Global Ventures dissolved). Segment series are not stitched across bases. The FY2025 10-K recast covers FY2023-FY2025 only."],
    ["Fiscal 2025 events", "Large FY2024 'Other operating charges' and FY2024-FY2025 cash-flow movements relate to the IRS tax litigation deposit and the settlement of the fairlife contingent consideration (see 10-K notes). The workbook does not adjust them."],
    [],
    hdr("Not built in this pass"),
    ["Valuation / forecast sheets", "Excluded by instruction."],
    ["Non-operating note detail", "Not built: segment-level goodwill roll-forward, pension and postretirement detail, stock-based compensation, fair value measurement hierarchy, lease detail and the debt maturity schedule. These are in the 10-K notes but are outside the operating and capital-allocation scope of this pass."],
    ["Segment-level KPI time series", "Unit case volume is disclosed in billion unit cases only as a system total; the filings do not give a per-segment unit case base, so growth rates are recorded as reported rather than derived. Global Ventures exists FY2019-FY2024 only."],
    ["Non-GAAP bridge", "Not built: KO's comparable (non-GAAP) measures are in the 8-K earnings releases and IR schedules acquired in the research package; they are not included here."],
    ["Quarterly gaps", "4Q2024 and 4Q2025 are not filed as separate statements and are not derived here; quarterly year-over-year rows are therefore omitted."],
    [],
    hdr("Scope"),
    ["", "Data-preparation workbook only. No investment thesis, valuation, target price or recommendation."],
]

src_rows = [
    [{"text": "Filing", "header": True}, {"text": "Accession", "header": True}, {"text": "Prepared Markdown (repository-relative)", "header": True},
     {"text": "SHA-256 of prepared Markdown", "header": True}, {"text": "IS / BS / CF statement start lines", "header": True}],
]
for k in [f"10K-FY{y}" for y in range(2016, 2026)] + [QKEY[q] for q in Q]:
    e = RAW[k]
    src_rows.append([k, e["accession"], e["md_path"], file_sha(e["md_path"]),
                     f'IS L{e["IS"]["line"]} / BS L{e["BS"]["line"]} / CF L{e["CF"]["line"]}'])
src_rows += [[], hdr("Annual column provenance (which 10-K supplies each fiscal-year column)")]
src_rows.append([{"text": "Column", "header": True}, {"text": "IS and CF source", "header": True}, {"text": "BS source", "header": True}, {"text": "Segments source", "header": True}, {"text": "Geography source", "header": True}])
for y in range(2016, 2026):
    seg = []
    if y <= 2018: seg.append("A: FY2018 10-K")
    if 2017 <= y <= 2024: seg.append(f"B: FY{SEG_FILING[y]} 10-K")
    if y >= 2023: seg.append("C: FY2025 10-K")
    src_rows.append([f"FY{y}", f"FY{src_filing(y, 'IS')} 10-K", f"FY{src_filing(y, 'BS')} 10-K", "; ".join(seg), f"FY{min(y + 2, 2025)} 10-K"])
src_rows += [[], hdr("Quarterly column provenance")]
for q in Q:
    src_rows.append([q, QKEY[q], f"period end {QEND[q]}"])
src_rows += [[], hdr("Restatement log: first-filed value vs value used in the workbook (differences only)")]
src_rows.append([{"text": "Column", "header": True}, {"text": "Line", "header": True}, {"text": "As first filed", "header": True}, {"text": "Used in workbook", "header": True}, {"text": "First-filed / used filing", "header": True}])
for c, nm, a, b, o, u in restate:
    src_rows.append([c, nm, a, b, f"{o} -> {u}"])
if not restate:
    src_rows.append(["none", "", "", "", ""])
src_rows += [[], hdr("Operating data and note schedules — table provenance (filing, and the line each table starts on)")]
src_rows.append([{"text": "Table", "header": True}, {"text": "Source", "header": True}, {"text": "Years covered", "header": True}, {"text": "Note", "header": True}])
_op = OPS
_vol_years = sorted(int(y) for y in _op["unit_case_volume_bn"])
src_rows.append(["System unit case volume (bn)", "10-K MD&A, heading 'Beverage Volume'", f"{min(_vol_years)}-{max(_vol_years)}",
                 "Each 10-K prints its year and the two prior years; the earliest year therefore comes from the earliest filing that shows it."])
src_rows.append(["Volume growth by segment", "10-K MD&A, table 'Information about our volume growth'", "FY2017-FY2025",
                 "Two layouts: FY2017-FY2020 print two prior periods side by side; FY2021 onward print one period with Unit Cases and Concentrate Sales columns."])
src_rows.append(["Net operating revenue factors", "10-K MD&A, table 'estimated impact of the factors'", "FY2019-FY2025",
                 "Caption changed: 'Price, Product & Geographic Mix' (FY2019-FY2024) became 'Price/Mix' (FY2025). Values are percentage impacts as filed."])
src_rows.append(["Revenue by line of business", "10-K Note 3 Net Operating Revenues", "FY2018-FY2025",
                 "Concentrate vs finished product operations, split United States / International."])
src_rows.append(["Segment revenue mix", "10-K MD&A, 'as a percentage of Company net operating revenues'", "FY2018-FY2025",
                 "Global Ventures appears FY2019-FY2024 only."])
src_rows.append(["Equity method investees (aggregate)", "10-K Note 6 Equity Method Investments", "FY2016-FY2025",
                 "Aggregate investee financials and the Company's proportionate share of net income."])
src_rows.append(["Equity investee fair value vs carrying", "10-K Note 6, publicly traded investees", "latest filing (FY2025)",
                 "Quoted closing prices against carrying value."])
src_rows.append(["Income taxes", "10-K Note 15 Income Taxes and MD&A", "FY2016-FY2025",
                 "Pre-tax income by jurisdiction, current/deferred by jurisdiction, unrecognized tax benefit roll-forward. FY2024-FY2023 Puerto Rico amounts reclassified from United States to International on ASU 2023-09 adoption."])
src_rows.append(["Long-term debt by type", "10-K Note 11 Debt and Borrowing Arrangements", "latest filing (FY2025 vs FY2024)",
                 "Amounts only; weighted-average rates are in the filing. Captions change between years, so a stitched series would be misleading and the latest filing's two columns are shown instead."])
src_rows.append(["Assets and liabilities held for sale", "10-K Note 2 Acquisitions and Divestitures", "latest filing (FY2025 vs FY2024)",
                 "Major classes of assets and liabilities classified as held for sale."])
src_rows.append(["Customer concentration", "10-K Item 1 Business / Note 20", "FY2025",
                 "One bottler accounted for 10% of net operating revenues in FY2025 (EMEA and Asia Pacific); none in FY2024 or FY2023."])
src_rows += [[], hdr("Parsing notes"),
             ["", "Statements were parsed from the prepared Markdown produced by the bundled ResearchFoundry SEC-HTML flow (research package S001-S016). Numbers are copied, not re-keyed. Totals are stored as reported and verified by the check rows."],
             ["", "Operating tables and note schedules are parsed from the same prepared Markdown by _extract_operating.py. Every table whose rows must add up carries a tie-out check at extraction time (354 checks, all passing), and every hard-coded value was re-located in its source filing text by an independent audit script (_ops_audit.py, 753/753 cells)."]]

# ------------------------------------------------- operating metrics / notes ----
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("_ops_sheets", os.path.join(WORK, "_ops_sheets.py"))
_ops = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_ops)
OPS = _ops.load(WORK)
ops_blocks = _ops.sheet_ops(OPS)
note_blocks = _ops.sheet_notes(OPS)
ops_src = {}
for blk in ops_blocks + note_blocks:
    for r in blk["rows"]:
        if r.get("note") and any(k in r["note"] for k in ("Note 6", "Note 15", "Note 11", "Note 2", "Note 3")):
            ops_src[r["id"]] = r["note"]
print("ops blocks", len(ops_blocks), "note blocks", len(note_blocks))

model = {
    "company": {"name": "The Coca-Cola Company", "ticker": "KO", "currency": "USD",
                "units": "$ in millions except per-share data", "reporting_framework": "US GAAP",
                "fiscal_year_end": "December 31", "consolidation_scope": "Consolidated",
                "as_of_date": "2026-07-03", "model_date": "2026-10-13"},
    "periods": {"annual": [{"label": a, "end": AEND[a]} for a in A], "scrap_cols": 3,
                "quarterly": [{"label": q, "end": QEND[q]} for q in Q]},
    "sheets": [
        {"name": "Cover", "kind": "table", "col_widths": [38, 120], "tab_color": "1F4E79", "table": cover},
        {"name": "Income Statement", "short": "IS", "kind": "statement", "tab_color": "1F4E79", "contents": True, "blocks": is_blocks},
        {"name": "Balance Sheet", "short": "BS", "kind": "statement", "tab_color": "1F4E79", "contents": True, "blocks": bs_blocks},
        {"name": "Cash Flow", "short": "CF", "kind": "statement", "tab_color": "1F4E79", "contents": True, "blocks": cf_blocks},
        {"name": "Segments", "short": "SEG", "kind": "statement", "tab_color": "548235", "contents": True, "blocks": seg_blocks},
        {"name": "Geography", "short": "GEO", "kind": "statement", "tab_color": "548235", "contents": True, "blocks": geo_blocks},
        {"name": "Derived Metrics", "short": "DM", "kind": "statement", "tab_color": "7030A0", "contents": True, "blocks": dm_blocks},
        {"name": "Operating Metrics", "short": "OPS", "kind": "statement", "tab_color": "BF8F00", "contents": True, "blocks": ops_blocks},
        {"name": "Note Schedules", "short": "NOTE", "kind": "statement", "tab_color": "BF8F00", "contents": True, "blocks": note_blocks},
        {"name": "Sources", "kind": "table", "col_widths": [26, 52, 90, 70, 40], "tab_color": "1F4E79", "table": src_rows},
    ],
}
out = os.path.join(WORK, "model.json")
json.dump(model, open(out, "w"), indent=1, ensure_ascii=False)
print("WARN", len(WARN))
for w in WARN:
    print("  ", w[:200])
for s in model["sheets"]:
    if s.get("kind") == "statement":
        print(s["short"], len(s["blocks"]), sum(len(b["rows"]) for b in s["blocks"]))
