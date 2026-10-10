#!/usr/bin/env python3
"""Supplementary (segment / KPI / note) extraction for MCD from tables.json.
Same precedence rule as mcd_extract: the latest filing containing a period wins."""
import re
from collections import defaultdict
import mcd_extract as m

T = m.load()
TB = {t["table_id"]: t for t in T}


def tenk(fy):
    return [t for t in T if m.filing_of(t) == ("10K", fy, 4)]


def yrs_in_row(row):
    return [c for c in row if isinstance(c, int) and 2000 < c < 2100]


def header_years(t):
    """Years from the header (string) cells, then from the first int-year row."""
    ys = [int(re.search(r"(20\d\d)", m.norm(h)).group(1)) for h in t["headers"][1:] if re.search(r"(20\d\d)", m.norm(h))]
    if ys:
        return ys
    for r in t["rows"]:
        y = yrs_in_row(r)
        if len(y) >= 2:
            return y
    return []


def put(store, rid, per, val, fy, tid):
    store[rid][per] = val
    store["_src"][(rid, per)] = (fy, tid)


# --------------------------------------------------------------- segments ---
SEG_NAMES = {
    "u.s.": "us", "international operated markets": "iom",
    "international developmental licensed markets & corporate": "idl",
    "international lead markets": "ilm", "high growth markets": "hgm",
    "foundational markets & corporate": "fmc",
}
GROUPS = [("total revenues", "rev"), ("total franchised restaurants-occupancy", "fran_occ"),
          ("total company-operated restaurant expenses", "co_exp"), ("total selling, general", "sga"),
          ("total other segment items", "other_seg"), ("total operating income", "opinc"),
          ("total assets", "assets"), ("total capital expenditures", "capex"),
          ("total depreciation", "da")]


def parse_segment_table(t):
    """Return {(group, seg): [values aligned to header years]}"""
    ys = header_years(t)
    out = {}
    pending = []
    for r in t["rows"]:
        lab = m.norm(r[0]).lower().rstrip("*").strip()
        vals = m.row_values(r[1:])
        vals = [v for v in vals if not isinstance(v, tuple)]
        if not vals:
            continue
        if lab.startswith("total"):
            grp = next((g for k, g in GROUPS if lab.startswith(k)), None)
            assert grp, lab
            for seg, v in pending:
                out[(grp, seg)] = v
            out[(grp, "tot")] = vals
            pending = []
        else:
            seg = SEG_NAMES.get(lab)
            assert seg, lab
            pending.append((seg, vals))
    return ys, out


def segment_data():
    new = defaultdict(dict)
    new["_src"] = {}
    old = defaultdict(dict)
    old["_src"] = {}
    for fy in range(2016, 2026):
        for t in tenk(fy):
            x = m.txt(t)
            if not (t["headers"][0].lower().startswith("in millions") and "total capital expenditures" in x and "total assets" in x
                    and ("total depreciation" in x) and ("international" in x)):
                continue
            ys, out = parse_segment_table(t)
            is_old = "high growth markets" in x
            store = old if is_old else new
            for (g, s), vals in out.items():
                assert len(vals) == len(ys), (t["table_id"], g, s, vals, ys)
                for y, v in zip(ys, vals):
                    put(store, f"{g}_{s}", f"FY{y}", v, fy, t["table_id"])
    return new, old


# ---------------------------------------------- MD&A revenue by segment/type --
def revenue_type_data():
    out = defaultdict(dict)
    out["_src"] = {}
    for fy in range(2019, 2026):
        for t in tenk(fy):
            if not (t["headers"][0] == "Revenues" and "franchised revenues:" in m.txt(t)):
                continue
            ys = header_years(t)[:3]
            ys = [y for y in yrs_in_row([c for r in t["rows"][:3] for c in r])][:3]
            grp = None
            for r in t["rows"]:
                lab = m.norm(r[0])
                vals = m.row_values(r[1:])
                vals = [v for v in vals if not isinstance(v, tuple)]
                ll = lab.lower()
                if lab.endswith(":"):
                    grp = ("fran" if ll.startswith("franchised") else
                           "co" if ll.startswith("company") else "fc")
                    continue
                if not vals or ll in ("dollars in millions", "amount"):
                    continue
                if ll.startswith("total other revenues"):
                    key = "other_total"
                elif ll.startswith("total revenues"):
                    key = "rev_total"
                elif ll == "total":
                    key = f"{grp}_tot"
                else:
                    seg = SEG_NAMES.get(ll)
                    if not seg:
                        continue
                    key = f"{grp}_{seg}"
                for y, v in zip(ys, vals[:3]):
                    put(out, key, f"FY{y}", v, fy, t["table_id"])
    return out


# ------------------------------------------------------------- KPIs ---------
def comps_data():
    out = defaultdict(dict)
    out["_src"] = {}
    for fy in range(2020, 2026):
        for t in tenk(fy):
            if not t["headers"][0].lower().startswith("comparable sales increase"):
                continue
            ys = yrs_in_row(t["rows"][0])
            for r in t["rows"][1:]:
                lab = m.norm(r[0]).lower()
                vals = [v for v in m.row_values(r[1:]) if not isinstance(v, tuple)]
                seg = SEG_NAMES.get(lab, "total" if lab.startswith("total") else None)
                if lab.startswith("international developmental licensed markets"):
                    seg = "idl"
                if not seg:
                    continue
                for y, v in zip(ys, vals):
                    put(out, f"comp_{seg}", f"FY{y}", v / 100.0, fy, t["table_id"])
    return out


def systemwide_growth():
    out = defaultdict(dict)
    out["_src"] = {}
    for fy in range(2020, 2026):
        for t in tenk(fy):
            if not t["headers"][0].lower().startswith("systemwide sales increase"):
                continue
            ys = None
            for r in t["rows"][:3]:
                y = yrs_in_row(r)
                if len(y) == 4:
                    ys = y
            assert ys, t["table_id"]
            for r in t["rows"]:
                lab = m.norm(r[0]).lower()
                vals = [v for v in m.row_values(r[1:]) if not isinstance(v, tuple)]
                if len(vals) != 4 or lab.startswith("increase"):
                    continue
                seg = SEG_NAMES.get(lab)
                if lab.startswith("international developmental licensed"):
                    seg = "idl"
                if lab.startswith("total"):
                    seg = "total"
                if not seg:
                    continue
                for i, (y, v) in enumerate(zip(ys, vals)):
                    kind = "rep" if i < 2 else "cc"
                    put(out, f"sws_{kind}_{seg}", f"FY{y}", v / 100.0, fy, t["table_id"])
    return out


def restaurants_by_type():
    out = defaultdict(dict)
    out["_src"] = {}
    for fy in range(2019, 2026):
        for t in tenk(fy):
            if not t["headers"][0].lower().startswith("restaurants at december 31"):
                continue
            ys = header_years(t)
            for r in t["rows"]:
                lab = m.norm(r[0]).lower()
                vals = [v for v in m.row_values(r[1:]) if not isinstance(v, tuple)]
                key = ("conv" if lab.startswith("conventional") else "devlic" if lab.startswith("developmental") else
                       "foreign" if lab.startswith("foreign") else "fran_tot" if lab.startswith("total franchised") else
                       "co" if lab.startswith("company") else "sys" if lab.startswith("total systemwide") else None)
                if not key:
                    continue
                for y, v in zip(ys, vals):
                    put(out, f"rest_{key}", f"FY{y}", v, fy, t["table_id"])
    return out


def item6_data():
    """Selected financial data (Item 6 / multi-year summary): FY2016-FY2021 10-Ks."""
    out = defaultdict(dict)
    out["_src"] = {}
    rules = [("restaurants at year end", None), ("company-operated restaurants", "i6_rest_co"),
             ("franchised restaurants", "i6_rest_fran"), ("total systemwide restaurants", "i6_rest_sys"),
             ("franchised sales", "i6_fran_sales"), ("total debt", "i6_total_debt"),
             ("market price at year end", "i6_price"), ("shares outstanding", "i6_shares_out")]
    for fy in range(2016, 2022):
        for t in tenk(fy):
            x = m.txt(t)
            if not ("franchised sales" in x and "market price at year end" in x):
                continue
            ys = None
            for r in t["rows"][:3]:
                y = yrs_in_row(r)
                if len(y) >= 3:
                    ys = y
                    break
            for r in t["rows"]:
                lab = re.sub(r"\(\d\)$", "", m.norm(r[0]).lower()).strip()
                key = next((k for pat, k in rules if k and lab == pat), None)
                if not key:
                    continue
                vals = [v for v in m.row_values(r[1:]) if not isinstance(v, tuple)]
                for y, v in zip(ys, vals):
                    put(out, key, f"FY{y}", v, fy, t["table_id"])
    return out


def franchised_mix():
    out = defaultdict(dict)
    out["_src"] = {}
    for fy in range(2016, 2026):
        for t in tenk(fy):
            x = m.txt(t)
            if not (t["headers"][0].lower().startswith("in millions") and "rents" in x and "royalties" in x and "initial fees" in x):
                continue
            ys = header_years(t)
            for r in t["rows"]:
                lab = m.norm(r[0]).lower()
                key = {"rents": "fm_rents", "royalties": "fm_royalties", "initial fees": "fm_initial",
                       "revenues from franchised restaurants": "fm_total"}.get(lab)
                if not key:
                    continue
                vals = [v for v in m.row_values(r[1:]) if not isinstance(v, tuple)]
                for y, v in zip(ys, vals):
                    put(out, key, f"FY{y}", v, fy, t["table_id"])
    return out


def shareholder_returns():
    out = defaultdict(dict)
    out["_src"] = {}
    names = {"number of shares repurchased": "sr_shares_rep", "shares outstanding at year end": "sr_shares_out",
             "dividends declared per share": "sr_dps", "treasury stock purchases (in shareholders' equity)": "sr_buyback",
             "dividends paid": "sr_div_paid", "total returned to shareholders": "sr_total"}
    for fy in range(2016, 2026):
        for t in tenk(fy):
            if "total returned to shareholders" not in m.txt(t):
                continue
            ys = header_years(t)
            for r in t["rows"]:
                key = names.get(m.norm(r[0]).lower())
                if not key:
                    continue
                vals = [v for v in m.row_values(r[1:]) if not isinstance(v, tuple)]
                for y, v in zip(ys, vals):
                    put(out, key, f"FY{y}", v, fy, t["table_id"])
    return out


def debt_stats():
    out = defaultdict(dict)
    out["_src"] = {}
    for fy in range(2016, 2026):
        for t in tenk(fy):
            if "fixed-rate debt as a percent" not in m.txt(t):
                continue
            ys = [int(re.search(r"(20\d\d)", m.norm(h)).group(1)) for h in t["headers"] if re.search(r"(20\d\d)", m.norm(h))]
            for r in t["rows"]:
                lab = m.norm(r[0]).lower()
                key = ("ds_fixed" if lab.startswith("fixed-rate") else "ds_wavg_rate" if lab.startswith("weighted-average annual") else
                       "ds_fx_debt" if lab.startswith("foreign currency-denominated") else
                       "ds_debt_cap" if lab.startswith("total debt as a percent") else
                       "ds_cfo_debt" if lab.startswith("cash provided by operations as a percent") else None)
                if not key:
                    continue
                vals = [v for v in m.row_values(r[1:]) if not isinstance(v, tuple)]
                for y, v in zip(ys, vals):
                    put(out, key, f"FY{y}", v / 100.0, fy, t["table_id"])
    return out


def ppe_data():
    out = defaultdict(dict)
    out["_src"] = {}
    names = {"land": "ppe_land", "buildings and improvements on owned land": "ppe_bld_owned",
             "buildings and improvements on leased land": "ppe_bld_leased", "equipment, signs and seating": "ppe_equip",
             "other": "ppe_other", "property and equipment, at cost": "ppe_cost",
             "accumulated depreciation and amortization": "ppe_accum", "net property and equipment": "ppe_net"}
    for fy in range(2018, 2026):
        for t in tenk(fy):
            x = m.txt(t)
            if not ("buildings and improvements on owned land" in x and "equipment, signs and seating" in x):
                continue
            ys = header_years(t)
            for r in t["rows"]:
                key = names.get(m.norm(r[0]).lower())
                if not key:
                    continue
                vals = [v for v in m.row_values(r[1:]) if not isinstance(v, tuple)]
                for y, v in zip(ys, vals):
                    put(out, key, f"FY{y}", v, fy, t["table_id"])
    return out


def tax_data():
    out = defaultdict(dict)
    out["_src"] = {}
    for fy in range(2016, 2026):
        for t in tenk(fy):
            x = m.txt(t)
            if t["headers"][0].lower().startswith("in millions") and "outside the u.s." in x and "income before provision for income tax" in x and t["row_count"] == 3:
                ys = header_years(t)
                for r, key in zip(t["rows"], ["pti_us", "pti_non_us", "pti_total"]):
                    vals = [v for v in m.row_values(r[1:]) if not isinstance(v, tuple)]
                    for y, v in zip(ys, vals):
                        put(out, key, f"FY{y}", v, fy, t["table_id"])
            if "current tax provision" in x and "deferred tax" in x and t["row_count"] == 9:
                ys = header_years(t)
                keys = ["cur_fed", "cur_state", "cur_foreign", "cur_total", "def_fed", "def_state", "def_foreign", "def_total", "tax_total"]
                for r, key in zip(t["rows"], keys):
                    vals = [v for v in m.row_values(r[1:]) if not isinstance(v, tuple)]
                    for y, v in zip(ys, vals):
                        put(out, key, f"FY{y}", v, fy, t["table_id"])
    return out


if __name__ == "__main__":
    new, old = segment_data()
    print("SEG new:", sorted(k for k in new if k != "_src"))
    print(" periods", sorted(new["rev_tot"]), "old", sorted(old["rev_tot"]))
    for nm, f in [("revtype", revenue_type_data), ("comps", comps_data), ("sws", systemwide_growth),
                  ("rest", restaurants_by_type), ("item6", item6_data), ("fm", franchised_mix),
                  ("sr", shareholder_returns), ("debt", debt_stats), ("ppe", ppe_data), ("tax", tax_data)]:
        d = f()
        print(nm, {k: sorted(v) [:1] + sorted(v)[-1:] for k, v in d.items() if k != "_src"})
