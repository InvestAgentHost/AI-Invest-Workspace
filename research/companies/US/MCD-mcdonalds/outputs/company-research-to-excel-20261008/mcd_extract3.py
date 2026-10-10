#!/usr/bin/env python3
"""Second-pass (gap sweep) extraction for MCD: MD&A operating tables, note schedules and
prose-disclosed series.  Same precedence rule as mcd_extract: latest filing wins.
Everything is parsed from tables.json (tables) or the prepared 10-K document.md (prose);
nothing is typed by hand."""
import glob
import re
from collections import defaultdict

import mcd_extract as m

T = m.load()
TB = {t["table_id"]: t for t in T}
SRC = "../../../../../../sources/companies/US/MCD-mcdonalds/artifacts/ten_k/MCD-mcdonalds"
SEGNAME = {"u.s.": "us", "international operated markets": "iom"}


def seg_of(lab):
    l = str(lab).lower()
    if l.startswith("u.s."):
        return "us"
    if l.startswith("international operated"):
        return "iom"
    if l.startswith("international developmental"):
        return "idl"
    return None


def nums(row, skip_label=True):
    vals = m.row_values(row[1:] if skip_label else row)
    return [v for v in vals if not isinstance(v, tuple)]


def has_text(row, tok="n/m"):
    return any(isinstance(v, tuple) and v[1] == tok for v in m.row_values(row[1:]))


def tenk(fy):
    return [t for t in T if m.filing_of(t) == ("10K", fy, 4)]


def years_row(t):
    """first row (or header) holding >=2 integer years"""
    for r in t["rows"][:4]:
        ys = [c for c in r if isinstance(c, int) and 2000 < c < 2100]
        if len(ys) >= 2:
            return ys
    hs = [int(re.search(r"(20\d\d)", m.norm(h)).group(1)) for h in t["headers"] if re.search(r"(20\d\d)", m.norm(h))]
    return hs


def n_amount_cols(ys):
    """number of leading amount columns: the year sequence restarts when the % columns begin"""
    for i in range(1, len(ys)):
        if ys[i] >= ys[0]:
            return i
    return len(ys)


class Store(dict):
    def __init__(self):
        super().__init__()
        self.src = {}

    def put(self, rid, per, val, fy, tid):
        self.setdefault(rid, {})[per] = val
        self.src[(rid, per)] = (fy, tid)


def pct_fix(v):
    """The collector turns 'x.y%' cells into fractions (0.036) but leaves split '(2.1' + '%)' cells as plain
    numbers.  Comparable-sales figures carry one decimal, so a value below 1 with more than one decimal is a
    converted fraction and is scaled back to percentage points."""
    if abs(v) < 1 and abs(round(v * 10) - v * 10) > 1e-6:
        return round(v * 100, 1)
    return v


def comps_guest():
    s = Store()
    for fy in range(2016, 2020):
        for t in tenk(fy):
            if not t["headers"][0].lower().startswith("comparable sales and guest count"):
                continue
            ys = years_row(t)
            for r in t["rows"]:
                ll = m.norm(r[0]).lower()
                sg = "total" if ll.startswith("total") else seg_of(r[0])
                if not sg or (sg in ("iom", "idl") and fy != 2019):
                    continue
                v = [pct_fix(x) for x in nums(r)]
                if len(v) != 2 * len(ys):
                    continue
                for i, y in enumerate(ys):
                    s.put(f"cg_sales_{sg}", f"FY{y}", v[2 * i], fy, t["table_id"])
                    s.put(f"cg_guest_{sg}", f"FY{y}", v[2 * i + 1], fy, t["table_id"])
    return s


def run_all():
    out = {}
    out["fs"] = franchised_sales()
    out["rm"] = restaurant_margins()
    out["sga"] = sga_mdna()
    out["oo"] = other_operating()
    out["no"] = nonoperating()
    out["rs"] = restaurants_by_segment()
    out["fx"] = currency_impact()
    out["eps"] = nongaap("eps")
    out["ni"] = nongaap("ni")
    out["oi"] = nongaap("oi")
    out["gw"] = goodwill()
    out["rent"] = rent_expense()
    out["sbc"] = sbc()
    out["capex"] = capex_purpose()
    out["debt"] = debt_by_currency()
    out["obl"] = obligations()
    out["prose"] = prose_series()
    out["cg"] = comps_guest()
    return out


# ------------------------------------------------------------ MD&A tables ----
def franchised_sales():
    s = Store()
    for fy in range(2019, 2026):
        for t in tenk(fy):
            if not ("conventional franchised" in m.txt(t) and "ownership type" in m.txt(t)):
                continue
            ys = years_row(t)
            n = n_amount_cols(ys)
            ys = ys[:n]
            sect = "seg"
            for r in t["rows"]:
                lab = m.norm(r[0])
                v = nums(r)
                if lab.lower().startswith("ownership type"):
                    sect = "own"
                    continue
                if len(v) < n:
                    continue
                v = v[:n]
                ll = lab.lower()
                if sect == "seg":
                    key = "fs_total" if ll == "total" else ("fs_" + seg_of(lab)) if seg_of(lab) else None
                else:
                    key = ("fs_conv" if ll.startswith("conventional") else "fs_devlic" if ll.startswith("developmental")
                           else "fs_foreign" if ll.startswith("foreign") else "fs_own_total" if ll == "total" else None)
                if key:
                    for y, x in zip(ys, v):
                        s.put(key, f"FY{y}", x, fy, t["table_id"])
    return s


def restaurant_margins():
    s = Store()
    for fy in range(2019, 2026):
        for t in tenk(fy):
            x = m.txt(t)
            first = [m.norm(r[0]).lower() for r in t["rows"][:3]]
            # FY2021+ combined table
            if "franchised:" in first or any(l.startswith("franchised:") for l in first):
                ys = years_row(t)
                n = n_amount_cols(ys)
                ys = ys[:n]
                grp = None
                for r in t["rows"]:
                    lab = m.norm(r[0])
                    ll = lab.lower()
                    if ll.endswith(":"):
                        grp = "fran" if ll.startswith("franchised") else "co" if ll.startswith("company") else "tot"
                        continue
                    sg = "total" if ll == "total" else seg_of(lab)
                    if grp is None or sg is None:
                        continue
                    v = nums(r)
                    if len(v) < n:
                        continue
                    for y, a in zip(ys, v[:n]):
                        s.put(f"rm_{grp}_{sg}", f"FY{y}", a, fy, t["table_id"])
            # FY2019/FY2020-style split tables with '% of revenue' columns
            elif t["headers"][0] == "Amount" and "% of revenue" in m.norm(" ".join(map(str, t["headers"]))).lower():
                ys = years_row(t)
                yy = ys[:3]
                labs = [m.norm(r[0]).lower() for r in t["rows"]]
                is_co = fy <= 2020 and any("n/m" in str(c) for r in t["rows"] for c in r)
                grp = "co" if is_co else "fran"
                for r in t["rows"]:
                    lab = m.norm(r[0])
                    sg = "total" if lab.lower() == "total" else seg_of(lab)
                    if sg is None:
                        continue
                    v = nums(r)
                    if len(v) < 5:
                        continue
                    for i, y in enumerate(yy):
                        s.put(f"rm_{grp}_{sg}", f"FY{y}", v[2 * i], fy, t["table_id"])
    return s


def sga_mdna():
    s = Store()
    for fy in range(2019, 2026):
        for t in tenk(fy):
            if "incentive-based compensation" not in m.txt(t):
                continue
            ys = years_row(t)
            n = n_amount_cols(ys)
            ys = ys[:n]
            for r in t["rows"]:
                lab = m.norm(r[0])
                ll = lab.lower()
                v = nums(r)
                if len(v) < n:
                    continue
                sg = seg_of(lab)
                key = (f"sga_{sg}" if sg else "sga_total" if ll.startswith("total selling") else
                       "sga_incentive" if ll.startswith("less: incentive") else
                       "sga_ex_incentive" if ll.startswith("total excluding") else None)
                if key:
                    for y, a in zip(ys, v[:n]):
                        s.put(key, f"FY{y}", a, fy, t["table_id"])
    return s


def breakdown(name, rules, fy_lo, require):
    s = Store()
    for fy in range(fy_lo, 2026):
        for t in tenk(fy):
            if not all(k in m.txt(t) for k in require) or t["row_count"] > 7:
                continue
            ys = header_years(t)
            for r in t["rows"]:
                ll = m.norm(r[0]).lower()
                v = nums(r)
                key = next((k for pat, k in rules if re.search(pat, ll)), None)
                if key is None or len(v) < len(ys):
                    continue
                for y, a in zip(ys, v[:len(ys)]):
                    s.put(key, f"FY{y}", a, fy, t["table_id"])
    return s


def header_years(t):
    ys = [int(re.search(r"(20\d\d)", m.norm(h)).group(1)) for h in t["headers"] if re.search(r"(20\d\d)", m.norm(h))]
    if ys:
        return ys
    return years_row(t)


def other_operating():
    return breakdown("oo", [(r"^gains on sales", "oo_gains"), (r"^equity in", "oo_equity"), (r"^asset dispositions", "oo_dispositions"),
                            (r"^impairment and other", "oo_impairment"), (r"^total$", "oo_total")], 2016,
                     ["gains on sales of restaurant businesses", "impairment and other charges"])


def nonoperating():
    return breakdown("no", [(r"^interest income", "no_interest_income"), (r"^foreign currency and hedging", "no_fx_hedging"),
                            (r"^other (\(income\) )?expense", "no_other"), (r"^total$", "no_total")], 2016,
                     ["interest income", "foreign currency and hedging activity"])


def restaurants_by_segment():
    s = Store()
    for fy in range(2019, 2026):
        for t in tenk(fy):
            if t["row_count"] != 4 or not all(re.fullmatch(r"20\d\d", m.norm(h)) for h in t["headers"][:3] if m.norm(h)):
                continue
            labs = [m.norm(r[0]).lower() for r in t["rows"]]
            if not (labs[0].startswith("u.s.") and labs[-1] == "total"):
                continue
            ys = header_years(t)
            for r in t["rows"]:
                v = nums(r)
                sg = "total" if m.norm(r[0]).lower() == "total" else seg_of(r[0])
                if min(v[:3] or [0]) < 1000:
                    break
                for y, a in zip(ys, v[:len(ys)]):
                    s.put(f"rseg_{sg}", f"FY{y}", a, fy, t["table_id"])
    return s


def currency_impact():
    s = Store()
    keys = [("revenues", "fx_revenues"), ("company-operated margins", "fx_co_margin"), ("company-owned and operated margins", "fx_co_margin"),
            ("franchised margins", "fx_fran_margin"), ("selling, general", "fx_sga"), ("operating income", "fx_op_income"),
            ("net income", "fx_net_income"), ("earnings per common share", "fx_eps")]
    for fy in range(2017, 2026):
        for t in tenk(fy):
            if t["headers"][0] != "Reported amount":
                continue
            ys = years_row(t)
            n = len(ys) // 2
            for r in t["rows"]:
                ll = m.norm(r[0]).lower()
                key = next((k for pat, k in keys if ll.startswith(pat)), None)
                if not key:
                    continue
                v = nums(r)
                if len(v) != 2 * n:
                    continue
                for y, a in zip(ys[:n], v[n:]):
                    s.put(key, f"FY{y}", a, fy, t["table_id"])
    return s


def nongaap(kind):
    """kind: eps | ni | oi.  Returns rows keyed by adjustment label slug plus gaap / nongaap totals"""
    title = {"eps": "diluted earnings per common share reconciliation", "ni": "net income reconciliation", "oi": None}[kind]
    s = Store()
    labels = {}
    for fy in range(2017, 2026):
        for t in tenk(fy):
            h0 = m.norm(t["headers"][0]).lower()
            if kind != "oi":
                if h0 != title:
                    continue
            else:
                if not any(m.norm(r[0]).lower().startswith("gaap operating income") for r in t["rows"]):
                    continue
            ys = years_row(t)
            n = n_amount_cols(ys)
            ys = ys[:n]
            inside = False
            for r in t["rows"]:
                lab = m.norm(r[0])
                ll = lab.lower()
                v = nums(r)
                if ll.startswith("gaap"):
                    key, inside = f"{kind}_gaap", True
                elif ll.startswith("non-gaap") and "margin" in ll:
                    key = f"{kind}_ng_margin"
                elif ll.startswith("non-gaap"):
                    key, inside = f"{kind}_nongaap", False
                elif inside and v:
                    slug = re.sub(r"[^a-z0-9]+", "_", re.sub(r"\(\d\)", "", ll)).strip("_")
                    key = f"{kind}_adj_{slug}"
                    labels[key] = lab
                else:
                    continue
                if key.endswith("_ng_margin"):
                    vv = [x / 100 if x > 1 else x for x in v][:n]
                else:
                    vv = v[:n]
                if len(vv) < n:
                    continue
                for y, a in zip(ys, vv):
                    s.put(key, f"FY{y}", a, fy, t["table_id"])
    s.labels = labels
    return s


# ------------------------------------------------------------- notes ---------
def goodwill():
    s = Store()
    for fy in range(2019, 2026):
        for t in tenk(fy):
            hs = [m.norm(h).lower() for h in t["headers"]]
            if not (hs and any("international operated" in h for h in hs) and any(m.norm(r[0]).lower().startswith("balance at december 31") for r in t["rows"])):
                continue
            segs = [("us" if h.startswith("u.s.") else "iom" if h.startswith("international operated") else
                     "idl" if h.startswith("international developmental") else "total" if h.startswith("consolidated") else None)
                    for h in hs[1:]]
            for r in t["rows"]:
                mm = re.match(r"balance at december 31, (20\d\d)", m.norm(r[0]).lower())
                if not mm:
                    continue
                v = nums(r)
                for sg, a in zip(segs, v):
                    if sg:
                        s.put(f"gw_{sg}", f"FY{mm.group(1)}", a, fy, t["table_id"])
    return s


def rent_expense():
    s = Store()
    for fy in range(2016, 2026):
        for t in tenk(fy):
            labs = [m.norm(r[0]).lower() for r in t["rows"]]
            if t["row_count"] == 10 and labs[-1] == "total rent expense":
                ys = header_years(t)
                for y, a in zip(ys, nums(t["rows"][-1])):
                    s.put("rent_total", f"FY{y}", a, fy, t["table_id"])
            if t["row_count"] == 3 and labs[-1] == "total rent expense":
                ys = header_years(t)
                for r, key in zip(t["rows"], ["rent_restaurants", "rent_other", "rent_total"]):
                    for y, a in zip(ys, nums(r)):
                        s.put(key, f"FY{y}", a, fy, t["table_id"])
    return s


def sbc():
    s = Store()
    for fy in range(2016, 2026):
        for t in tenk(fy):
            if t["row_count"] == 3 and m.norm(t["rows"][0][0]).lower().startswith("share-based compensation expense"):
                ys = header_years(t)
                for r, key in zip(t["rows"], ["sbc_expense", "sbc_after_tax", "sbc_eps"]):
                    for y, a in zip(ys, nums(r)):
                        s.put(key, f"FY{y}", a, fy, t["table_id"])
    return s


def capex_purpose():
    s = Store()
    for fy in range(2016, 2020):
        for t in tenk(fy):
            labs = [m.norm(r[0]).lower() for r in t["rows"]]
            if labs[:2] == ["new restaurants", "existing restaurants"]:
                ys = header_years(t)
                for r in t["rows"]:
                    key = {"new restaurants": "cx_new", "existing restaurants": "cx_existing", "total capital expenditures": "cx_total"}.get(m.norm(r[0]).lower())
                    if not key and m.norm(r[0]).lower().startswith("other"):
                        key = "cx_other"
                    if key:
                        for y, a in zip(ys, nums(r)):
                            s.put(key, f"FY{y}", a, fy, t["table_id"])
    return s


def debt_by_currency():
    s = Store()
    s.labels = {}
    for fy in range(2016, 2026):
        for t in tenk(fy):
            if not (t["headers"][0].lower().startswith("interest rates") and "total debt obligations" in m.txt(t)):
                continue
            for r in t["rows"]:
                lab = m.norm(r[0])
                ll = lab.lower()
                v = nums(r)
                if len(v) < 2:
                    continue
                if ll.startswith("total ") and not ll.startswith("total debt"):
                    key = "debt_" + next((k for pat, k in (("u.s", "usd"), ("euro", "eur"), ("australian", "aud"), ("british", "gbp"),
                                                           ("canadian", "cad"), ("japanese", "jpy"), ("chinese", "cny"), ("other", "other")) if pat in ll), "x_" + re.sub(r"[^a-z0-9]+", "_", ll))
                elif ll.startswith("debt obligations before"):
                    key = "debt_before_adj"
                elif ll.startswith("fair value adjustments"):
                    key = "debt_fv_adj"
                elif ll.startswith("deferred debt costs"):
                    key = "debt_deferred_costs"
                elif ll.startswith("total debt obligations"):
                    key = "debt_total"
                else:
                    continue
                s.labels[key] = re.sub(r"\(\d\)", "", lab)
                s.put(key, f"FY{fy}", v[-2], fy, t["table_id"])
                s.put(key, f"FY{fy-1}", v[-1], fy, t["table_id"])
    return s


def obligations():
    """Next-12-month and total contractual flows: debt, leases, minimum rent receivable."""
    s = Store()
    for fy in range(2016, 2026):
        docs = glob.glob(f"{SRC}/FY{fy}/psp_*/prepared/document.md")
        for t in tenk(fy):
            hs = [m.norm(h).lower() for h in t["headers"]]
            x = m.txt(t)
            # FY2016-FY2020: 'Contractual cash outflows' table (leases, debt, minimum rent receivable)
            if "contractual cash outflows" in " ".join(hs) or (t["rows"] and "contractual cash outflows" in m.norm(" ".join(map(str, t["rows"][0]))).lower()):
                data = [r for r in t["rows"] if (isinstance(r[0], int) or str(r[0]).lower() in ("thereafter", "total"))]
                if data:
                    first, total = data[0], [r for r in data if str(r[0]).lower() == "total"][0]
                    for key, i in (("ob_leases", 0), ("ob_min_rent", 2)):
                        s.put(key + "_next12", f"FY{fy}", nums(first)[i], fy, t["table_id"])
                        s.put(key + "_total", f"FY{fy}", nums(total)[i], fy, t["table_id"])
            # FY2021+: minimum rent table (Owned / Leased / Total) and lease maturity table
            if hs[:4] == ["in millions", "owned sites", "leased sites", "total"]:
                rows = [r for r in t["rows"] if isinstance(r[0], int) or str(r[0]).lower().startswith(("thereafter", "total"))]
                s.put("ob_min_rent_next12", f"FY{fy}", nums(rows[0])[2], fy, t["table_id"])
                tot = [r for r in rows if str(r[0]).lower().startswith("total")][0]
                s.put("ob_min_rent_total", f"FY{fy}", nums(tot)[2], fy, t["table_id"])
            if hs[:1] == ["in millions"] and "present value of lease liability" in x and "total lease payments" in x:
                r0 = [r for r in t["rows"] if isinstance(r[0], int)][0]
                tot = [r for r in t["rows"] if m.norm(r[0]).lower() == "total lease payments"][0]
                col = -1 if "total" in "".join(hs) else -1
                s.put("ob_leases_next12", f"FY{fy}", nums(r0)[-1], fy, t["table_id"])
                s.put("ob_leases_total", f"FY{fy}", nums(tot)[-1], fy, t["table_id"])
        if docs:
            txt = open(docs[0], encoding="utf-8").read()
            mm = re.search(r"Aggregate maturities for \d{4} debt balances.*?are as follows \(in millions\):(.*?)\. These amounts", txt, re.S)
            if mm:
                items = re.findall(r"(?:(\d{4})|Thereafter)\s*[–-]?\s*\$?\s*([\d,]+(?:\.\d+)?)", mm.group(1).replace("$ ", "$"))
                vals = [float(b.replace(",", "")) for a, b in items]
                if len(vals) >= 6:
                    s.put("ob_debt_next12", f"FY{fy}", vals[0], fy, "prose")
                    s.put("ob_debt_total", f"FY{fy}", sum(vals), fy, "prose")
    return s


# ------------------------------------------------------------- prose ---------
def debt_ladder(fy):
    """Aggregate debt maturities (before fair value adjustments and deferred costs) from the debt note."""
    d1 = re.sub(r"\s+", " ", doc_text(fy))
    mm = re.search(r"Aggregate maturities for \d{4} debt balances.*?are as follows \(in millions\):(.*?)\. These amounts", d1)
    items = re.findall(r"((?:20\d\d)|Thereafter)\s*[–-]?\s*\$?\s*([\d,]+(?:\.\d+)?)", mm.group(1).replace("$ ", "$"))
    return [(a, float(b.replace(",", ""))) for a, b in items]


def doc_text(fy):
    p = glob.glob(f"{SRC}/FY{fy}/psp_*/prepared/document.md")[0]
    return open(p, encoding="utf-8").read()


def prose_series():
    s = Store()
    for fy in range(2016, 2026):
        d = doc_text(fy)
        d1 = re.sub(r"\s+", " ", d)

        def trio(pat, key):
            mm = re.search(pat + r".{0,1500}?\(in millions\):?\s*(.*?)\.", d1)
            if not mm:
                return
            for yy, val in re.findall(r"(20\d\d)\s*[–-]\s*\$?\s*([\d,]+(?:\.\d+)?)", mm.group(1)):
                s.put(key, f"FY{yy}", float(val.replace(",", "")), fy, "prose")
        trio(r"Advertising costs included in operating expenses", "adv_company_op")
        trio(r"Production costs for radio and television advertising", "adv_production")
        mm = re.search(r"Rent expense included (?:variable lease payments|percent rents) in excess of minimum rents \(in millions\) as follows – Company-(?:owned and )?operated restaurants: (.*?)\. Franchised restaurants: (.*?)\.(?: These| Total|$| [A-Z])", d1)
        if mm:
            for key, g in (("var_rent_co", mm.group(1)), ("var_rent_fran", mm.group(2))):
                for yy, val in re.findall(r"(20\d\d)\s*[–-]\s*\$?\s*([\d,]+(?:\.\d+)?)", g):
                    s.put(key, f"FY{yy}", float(val.replace(",", "")), fy, "prose")
        mm = re.search(r"net property and equipment under franchise arrangements totaled \$ ?([\d.]+) billion \(including land of \$ ?([\d.]+) billion\) after deducting accumulated depreciation and amortization of \$ ?([\d.]+) billion", d1)
        if mm:
            for key, g in (("fa_net_ppe", mm.group(1)), ("fa_land", mm.group(2)), ("fa_accum", mm.group(3))):
                s.put(key, f"FY{fy}", float(g) * 1000, fy, "prose")
        mm = re.search(r"fair value of the Company.s debt obligations was estimated at \$ ?([\d.]+) billion, compared to a carrying amount of \$ ?([\d.]+) billion", d1)
        if mm:
            s.put("debt_fair_value", f"FY{fy}", float(mm.group(1)) * 1000, fy, "prose")
            s.put("debt_carrying_text", f"FY{fy}", float(mm.group(2)) * 1000, fy, "prose")
        mm = re.search(r"where it earns approximately (\d+)% of its operating income", d1)
        if mm:
            s.put("oi_outside_us", f"FY{fy}", float(mm.group(1)) / 100, fy, "prose")
        for sg, pat in (("us", r"U\.S\.[^•]{0,90}?The segment is (\d+)% franchised"), ("iom", r"International Operated Markets(?: segment)? - comprised.{0,400}?The segment is (\d+)% franchised"),
                        ("idl", r"International Developmental Licensed Markets[^•]{0,500}?(?:segment is|Markets are) (\d+)% franchised")):
            mm = re.search(pat, d1)
            if mm:
                s.put(f"franchised_pct_{sg}", f"FY{fy}", float(mm.group(1)) / 100, fy, "prose")
        mm = re.search(r"Franchised restaurants represent(?:ed|s)? approximately (\d+)% of McDonald.s restaurants worldwide", d1)
        if mm:
            s.put("franchised_pct_total", f"FY{fy}", float(mm.group(1)) / 100, fy, "prose")
        mm = re.search(r"Company employees.{0,160}?totaled (?:over |approximately )?([\d,]+) worldwide", d1)
        if mm:
            s.put("employees", f"FY{fy}", float(mm.group(1).replace(",", "")), fy, "prose")
        mm = re.search(r"delivery from (?:over |nearly |approximately )?([\d,]+) restaurants", d1)
        if mm:
            s.put("delivery_restaurants", f"FY{fy}", float(mm.group(1).replace(",", "")), fy, "prose")
        mm = re.search(r"nearly ([\d,]+) drive thru locations", d1)
        if mm:
            s.put("drive_thru", f"FY{fy}", float(mm.group(1).replace(",", "")), fy, "prose")
    return s


if __name__ == "__main__":
    R = run_all()
    for nm, st in R.items():
        print("=====", nm)
        for rid, per in st.items():
            ps = sorted(per)
            print(f"  {rid:28} {ps[0]}-{ps[-1]} n={len(ps):2d}  " + " ".join(f"{p[2:]}:{per[p]:g}" if isinstance(per[p], (int, float)) else f"{p[2:]}:{per[p]}" for p in ps[-4:]))
