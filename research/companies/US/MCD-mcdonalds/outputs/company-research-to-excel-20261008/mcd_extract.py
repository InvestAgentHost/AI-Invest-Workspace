#!/usr/bin/env python3
"""Programmatic extraction of MCD consolidated statements from tables.json.

Reads the collector bundle (tables.json, built from the SEC source.html of the
16 acquired filings) and returns period-keyed dictionaries per canonical row id.
No figure is typed by hand.  Precedence rule: for each period the value from the
LATEST filing that contains it is used (restatement/recast precedence); earlier
values are kept in `history` so restatements can be logged.
"""
import json
import re
from collections import defaultdict

BUNDLE = "tables.json"

# ----------------------------------------------------------------- helpers ---
def norm(s):
    s = str(s).replace("–", "-").replace("—", "-").replace("’", "'").replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def num(v):
    """Typed cell -> float/int/None.  Dash = reported nil (0)."""
    if isinstance(v, (int, float)):
        return v
    s = norm(v)
    if s in ("", "%", ")"):
        return None
    if s in ("-", "--"):
        return 0
    m = re.fullmatch(r"\(?(-?[\d,]+(?:\.\d+)?)\)?", s)
    if not m:
        return None
    x = float(m.group(1).replace(",", ""))
    if s.startswith("("):
        x = -x
    return int(x) if x == int(x) else x


def row_values(cells):
    """Compact a raw table row (after the label cell) into an ordered list of
    numeric values.  SEC HTML splits negatives into '(1,234' + ')' cells, pads
    with '' and '%' cells, and prints nil as an em dash (-> 0)."""
    out = []
    for c in cells:
        if isinstance(c, (int, float)):
            out.append(c)
            continue
        s = norm(c).replace("$", "").strip()
        if re.fullmatch(r"[%)\s]*", s):
            continue
        if s in ("-", "--"):
            out.append(0)
            continue
        m = re.fullmatch(r"\(([\d,]+(?:\.\d+)?)\)?", s)
        if m:
            x = -float(m.group(1).replace(",", ""))
            out.append(int(x) if x == int(x) and "." not in m.group(1) else x)
            continue
        m = re.fullmatch(r"\$?\s*(-?[\d,]+(?:\.\d+)?)", s)
        if m:
            x = float(m.group(1).replace(",", ""))
            out.append(int(x) if "." not in m.group(1) else x)
            continue
        out.append(("TEXT", s))
    return out


def load():
    b = json.load(open(BUNDLE))
    return b["tables"]


def filing_of(t):
    m = re.search(r"ten_k/([^/]+)/FY(\d+)/", t["source"])
    tgt, fy = m.group(1), int(m.group(2))
    q = re.search(r"10Q-Q(\d)", tgt)
    return ("10Q", fy, int(q.group(1))) if q else ("10K", fy, 4)


def txt(t):
    return norm(" ".join(" ".join(map(str, r)) for r in t["rows"]) + " " + " ".join(map(str, t["headers"]))).lower()


# ------------------------------------------------------- label -> row id -----
# Ordered (section, regex, id).  section=None matches anywhere; otherwise the
# parser tracks the most recent header row.
IS_RULES = [
    (r"^revenues from franchised", "rev_franchised"),
    (r"^sales by company", "rev_company"),
    (r"^other revenues", "rev_other"),
    (r"^total revenues", "total_revenues"),
    (r"^franchised restaurants-occupancy", "franchised_occupancy"),
    (r"^food & paper", "co_food_paper"),
    (r"^payroll & employee", "co_payroll"),
    (r"^occupancy & other operating", "co_occupancy_other"),
    (r"^other restaurant expenses", "other_restaurant_exp"),
    (r"^selling, general & administrative", "sga_header"),
    (r"^depreciation and amortization", "sga_da"),
    (r"^other operating \(income\) expense", "other_operating"),
    (r"^other$", "sga_other"),
    (r"^company-owned and operated restaurant expenses", "co_expenses_total_q"),
    (r"^company-operated restaurant expenses", "co_expenses_total_q"),
    (r"^total operating costs", "total_opex"),
    (r"^operating income", "operating_income"),
    (r"^interest expense", "interest_expense"),
    (r"^nonoperating", "nonoperating"),
    (r"^income before provision", "pretax_income"),
    (r"^provision for income taxes", "tax_provision"),
    (r"^net income", "net_income"),
    (r"^earnings per common share-basic", "eps_basic"),
    (r"^earnings per common share-diluted", "eps_diluted"),
    (r"^dividends declared per common share", "dps_declared"),
    (r"^weighted-average shares outstanding-basic", "waso_basic"),
    (r"^weighted-average shares outstanding-diluted", "waso_diluted"),
]
# header-only rows to ignore
IS_SKIP = (r"^revenues$", r"^operating costs and expenses$", r"^company-(owned and|operated) restaurant expenses$",
           r"^company-operated restaurant expenses$", r"^in millions", r"^quarters ended", r"^nine months", r"^six months",
           r"^september 30", r"^june 30", r"^march 31", r"^\(unaudited\)")

BS_RULES = [
    (r"^cash and equivalents", "cash"),
    (r"^accounts and notes receivable", "receivables"),
    (r"^inventories", "inventories"),
    (r"^prepaid expenses and other current", "prepaid_other_ca"),
    (r"^assets of businesses held for sale", "assets_held_for_sale"),
    (r"^total current assets", "total_current_assets"),
    (r"^investments in", "investments_affiliates"),
    (r"^goodwill", "goodwill"),
    (r"^miscellaneous", "misc_other_assets"),
    (r"^total other assets", "total_other_assets"),
    (r"^lease right-of-use asset", "lease_rou"),
    (r"^property and equipment, at cost", "ppe_gross"),
    (r"^accumulated depreciation", "accum_depr"),
    (r"^net property and equipment", "net_ppe"),
    (r"^total assets", "total_assets"),
    (r"^accounts payable", "accounts_payable"),
    (r"^lease liability", "lease_liab_current"),
    (r"^income taxes$", "income_taxes_cl"),
    (r"^other taxes", "other_taxes"),
    (r"^accrued interest", "accrued_interest"),
    (r"^accrued payroll", "accrued_payroll_other"),
    (r"^dividend payable", "dividend_payable"),
    (r"^current maturities of long-term debt", "current_debt"),
    (r"^short-term borrowings and current maturities", "current_debt"),
    (r"^liabilities of businesses held for sale", "liabs_held_for_sale"),
    (r"^total current liabilities", "total_current_liabilities"),
    (r"^long-term debt", "long_term_debt"),
    (r"^long-term lease liability", "lt_lease_liab"),
    (r"^long-term income taxes", "lt_income_taxes"),
    (r"^deferred revenues", "deferred_revenues"),
    (r"^other long-term liabilities", "other_lt_liabilities"),
    (r"^deferred income taxes", "deferred_income_taxes"),
    (r"^preferred stock", "preferred_stock"),
    (r"^common stock, ", "common_stock"),
    (r"^additional paid-in capital", "apic"),
    (r"^retained earnings", "retained_earnings"),
    (r"^accumulated other comprehensive", "aoci"),
    (r"^common stock in treasury", "treasury_stock"),
    (r"^total shareholders' equity", "total_equity"),
    (r"^total liabilities and shareholders' equity", "total_liab_equity"),
]

CF_RULES = [
    # (section, regex, id)  section in {op, chg, wc, inv, fin, sup}
    ("op", r"^net income", "cf_net_income"),
    ("chg", r"^depreciation and amortization", "cf_da"),
    ("chg", r"^deferred income taxes", "cf_deferred_taxes"),
    ("chg", r"^share-based compensation", "cf_sbc"),
    ("chg", r"^net (\(gain\) loss|gain) on sale", "cf_gain_sales"),
    ("chg", r"^other$", "cf_other_charges"),
    ("wc", r"^accounts receivable", "cf_wc_receivables"),
    ("wc", r"^inventories, prepaid", "cf_wc_inventories"),
    ("wc", r"^accounts payable", "cf_wc_payables"),
    ("wc", r"^income taxes", "cf_wc_income_taxes"),
    ("wc", r"^other accrued liabilities", "cf_wc_other_accrued"),
    ("wc", r"^other$", "cf_wc_other_dummy"),
    ("op", r"^changes in working capital items", "cf_wc_total_reported"),
    (None, r"^cash provided by operations", "cfo"),
    ("inv", r"^capital expenditures", "cf_capex"),
    ("inv", r"^purchases of restaurant", "cf_purch_businesses"),
    ("inv", r"^purchases of equity method", "cf_purch_equity_method"),
    ("inv", r"^sales of restaurant", "cf_sales_businesses"),
    ("inv", r"^sales of property", "cf_sales_property"),
    ("inv", r"^proceeds from sale of businesses in china", "cf_proceeds_china_hk"),
    (None, r"^change in cash balances of businesses held", "cf_chg_cash_held_sale"),
    ("inv", r"^other$", "cf_other_investing"),
    ("inv", r"^cash (used for|provided by \(used for\)|\(used for\)) investing", "cfi"),
    ("fin", r"^net short-term borrowings", "cf_st_borrowings"),
    ("fin", r"^long-term financing issuances", "cf_lt_issuances"),
    ("fin", r"^long-term financing repayments", "cf_lt_repayments"),
    ("fin", r"^treasury stock purchases", "cf_treasury_purchases"),
    ("fin", r"^common stock dividends", "cf_dividends"),
    ("fin", r"^proceeds from stock option", "cf_option_proceeds"),
    ("fin", r"^excess tax benefit", "cf_excess_tax_benefit"),
    ("fin", r"^other$", "cf_other_financing"),
    ("fin", r"^cash (used for|provided by \(used for\)|\(used for\)) financing", "cff"),
    (None, r"^effect of exchange rates", "cf_fx"),
    (None, r"^cash and equivalents increase", "cf_net_change"),
    (None, r"^cash balance of businesses held for sale", "cf_cash_held_sale_end"),
    (None, r"^cash and equivalents at beginning", "cf_cash_begin"),
    (None, r"^cash and equivalents at end", "cf_cash_end"),
    ("sup", r"^interest paid", "cf_interest_paid"),
    ("sup", r"^income taxes paid", "cf_taxes_paid"),
]


def classify_cf_section(label, current):
    l = label.lower()
    if l.startswith("operating activities"):
        return "op"
    if l.startswith("charges and credits"):
        return "chg"
    if l.startswith("changes in working capital items") :
        return current  # handled as value row in 10-Q, header in 10-K
    if l.startswith("investing activities"):
        return "inv"
    if l.startswith("financing activities"):
        return "fin"
    if l.startswith("supplemental"):
        return "sup"
    return None


def parse_statement(t, kind, col_years):
    """Return {row_id: {col_key: value}} for one statement table.

    col_years: list of column keys aligned with the numeric columns
    (after the label column).  Unmapped, value-bearing rows are returned
    in the second element so the caller can review them.
    """
    out = {}
    unmapped = []
    section = None
    sga_seen = False
    rules = {"IS": IS_RULES, "BS": BS_RULES}.get(kind)
    for row in t["rows"]:
        label = norm(row[0])
        ll = label.lower()
        vals = row_values(row[1:])
        if any(isinstance(v, tuple) for v in vals):
            vals = [None]  # text-bearing row (header / note); no data
        has_val = any(v is not None for v in vals)
        if has_val and len(vals) != len(col_years):
            unmapped.append("LENGTH:%s:%d!=%d" % (label, len(vals), len(col_years)))
            continue
        if kind == "CF":
            if ll.startswith("changes in working capital items") and not has_val:
                section = "wc"
                continue
            new = classify_cf_section(label, section)
            if new is not None and not has_val:
                section = new
                continue
            if ll.startswith("in millions"):
                continue
            if ll.startswith("adjustments to reconcile") or ll.startswith("charges and credits"):
                continue
            if not has_val:
                continue
            rid = None
            for sec, rx, cid in CF_RULES:
                if (sec is None or sec == section) and re.search(rx, ll):
                    rid = cid
                    break
            # label "Changes in working capital items" carrying values (10-Q)
            if ll.startswith("changes in working capital items"):
                rid = "cf_wc_total_reported"
            # 'Net income' appears once; cash begin/end are sectionless
            if rid is None:
                unmapped.append(label)
                continue
        else:
            if ll.startswith("in millions"):
                continue
            if not has_val:
                if ll.startswith("selling, general & administrative"):
                    sga_seen = True
                continue
            rid = None
            for rx, cid in rules:
                if re.search(rx, ll):
                    rid = cid
                    break
            if kind == "IS":
                # 'Depreciation and amortization' / 'Other' only valid inside SG&A block
                if rid in ("sga_da", "sga_other") and not sga_seen:
                    rid = None
                if rid == "sga_header":  # single-line SG&A (FY2016-17 presentation)
                    rid = "sga_reported"
            if rid is None:
                unmapped.append(label)
                continue
        if rid in out:
            unmapped.append("DUPLICATE:" + label)
            continue
        out[rid] = dict(zip(col_years, vals))
    return out, unmapped


def years_from_headers(t):
    ys = []
    for h in t["headers"][1:]:
        m = re.search(r"(20\d\d)", norm(h))
        if m:
            ys.append(int(m.group(1)))
    return ys


def find_annual_statement(tables, fy, kind):
    pat = {"IS": ("total revenues", "operating income", "diluted"),
           "BS": ("total assets", "total liabilities and shareholders"),
           "CF": ("cash provided by operations", "financing")}[kind]
    c = []
    for t in tables:
        f = filing_of(t)
        if f[0] != "10K" or f[1] != fy:
            continue
        x = txt(t)
        if not all(p in x for p in pat):
            continue
        if kind == "IS" and not t["headers"][0].lower().startswith("in millions, except per share"):
            continue
        if kind == "BS" and not t["headers"][0].lower().startswith("in millions, except per share"):
            continue
        if kind == "CF" and not t["headers"][0].lower().startswith("in millions"):
            continue
        if kind == "CF" and "sales of property" not in x:
            continue
        c.append(t)
    assert len(c) == 1, (fy, kind, [t["table_id"] for t in c])
    return c[0]


def annual_data(tables):
    """Return data[kind][row_id][FYxxxx] (latest filing wins) and history."""
    data = {k: defaultdict(dict) for k in ("IS", "BS", "CF")}
    hist = {k: defaultdict(lambda: defaultdict(list)) for k in ("IS", "BS", "CF")}
    unm = defaultdict(set)
    src = {k: defaultdict(dict) for k in ("IS", "BS", "CF")}   # (rid,period) -> table id used
    for fy in range(2016, 2026):
        for kind in ("IS", "BS", "CF"):
            t = find_annual_statement(tables, fy, kind)
            ys = years_from_headers(t)
            rows, un = parse_statement(t, kind, ys)
            for u in un:
                unm[(kind, fy)].add(u)
            for rid, byy in rows.items():
                for y, v in byy.items():
                    if v is None:
                        continue
                    key = f"FY{y}"
                    hist[kind][rid][key].append((fy, v, t["table_id"]))
                    # later filing overwrites (fy loop ascending)
                    data[kind][rid][key] = v
                    src[kind][rid][key] = (fy, t["table_id"])
    return data, hist, src, unm


# ------------------------------------------------------------- quarterly -----
def find_q_statement(tables, fy, q, kind):
    pat = {"IS": "condensed consolidated statement of income",
           "BS": "condensed consolidated balance sheet",
           "CF": "condensed consolidated statement of cash flows"}[kind]
    c = [t for t in tables if filing_of(t) == ("10Q", fy, q) and pat in norm(t["headers"][0]).lower()]
    assert len(c) == 1, (fy, q, kind, [t["table_id"] for t in c])
    return c[0]


def q_statement_columns(t, q):
    """For 10-Q IS/CF: return list of (key, kind) for the numeric columns,
    where kind is 'Q' (three months) or 'YTD'.  The year row is the first
    row whose cells are ints."""
    for row in t["rows"]:
        nums = [c for c in row[1:] if isinstance(c, int) and 2000 < c < 2100]
        if len(nums) >= 2 and not any(isinstance(c, str) and c.strip() for c in row[1:] if not isinstance(c, int)):
            years = nums
            break
    else:
        raise ValueError("no year row")
    if len(years) == 2:                     # Q1: only the quarter
        return [(years[0], "Q"), (years[1], "Q")]
    assert len(years) == 4
    return [(years[0], "Q"), (years[1], "Q"), (years[2], "YTD"), (years[3], "YTD")]


def quarterly_data(tables):
    """IS and CF quarterly (three-month and YTD) values plus BS period-end.
    Returns dict[kind][rid][key] with key like '3Q2025' (quarter), 'YTD3Q2025' (cumulative)."""
    out = {k: defaultdict(dict) for k in ("IS", "BS", "CF")}
    srcq = {k: defaultdict(dict) for k in ("IS", "BS", "CF")}
    order = [(2024, 3), (2025, 1), (2025, 2), (2025, 3), (2026, 1), (2026, 2)]
    unm = defaultdict(set)
    for fy, q in order:
        for kind in ("IS", "CF"):
            t = find_q_statement(tables, fy, q, kind)
            cols = q_statement_columns(t, q)
            keys = [f"{q}Q{y}" if kk == "Q" else f"YTD{q}Q{y}" for y, kk in cols]
            rows, un = parse_statement(t, kind, keys)
            for u in un:
                unm[(kind, f"{fy}Q{q}")].add(u)
            for rid, byk in rows.items():
                for k, v in byk.items():
                    if v is None:
                        continue
                    out[kind][rid][k] = v          # later filing wins (loop ascending)
                    srcq[kind][rid][k] = (f"{fy}Q{q}", t["table_id"])
        # balance sheet: current column = period end
        t = find_q_statement(tables, fy, q, "BS")
        hdr = [norm(h) for h in t["rows"][1]] if False else None
        # header row containing 'In millions'
        for row in t["rows"]:
            if norm(row[0]).lower().startswith("in millions"):
                hrow = row
                break
        ymatch = re.search(r"(20\d\d)", norm(hrow[1]))
        key = f"{q}Q{ymatch.group(1)}"
        rows, un = parse_statement(t, "BS", [key, "prior_ye"])
        for u in un:
            unm[("BS", f"{fy}Q{q}")].add(u)
        for rid, byk in rows.items():
            v = byk.get(key)
            if v is not None:
                out["BS"][rid][key] = v
                srcq["BS"][rid][key] = (f"{fy}Q{q}", t["table_id"])
    return out, srcq, unm


if __name__ == "__main__":
    import sys
    T = load()
    data, hist, src, unm = annual_data(T)
    for k, v in sorted(unm.items()):
        print("UNMAPPED annual", k, sorted(v))
    qd, qsrc, qunm = quarterly_data(T)
    for k, v in sorted(qunm.items()):
        print("UNMAPPED quarterly", k, sorted(v))
    for kind in ("IS", "BS", "CF"):
        print(kind, "annual rows", len(data[kind]), "quarterly rows", len(qd[kind]))
