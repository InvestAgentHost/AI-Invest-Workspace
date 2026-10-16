#!/usr/bin/env python3
"""Build the "Operating Metrics" and "Note Schedules" sheet blocks for the KO workbook
from operating_raw.json (written by _extract_operating.py).

Annual columns only: every row is bounded to FY2016-FY2025 with min_label / max_label,
so the quarterly columns stay blank. Values are the percentages and dollar amounts as
filed; percent rows are stored as ratios (0.01 = 1%) to match the workbook's pct format.
Each row carries its source filing and line in the note column.

Usage: imported by _build_model.py, or run directly to print a summary.
"""
import json
import os
import re

ANNUAL = [f"FY{y}" for y in range(2016, 2026)]
LATEST = "FY2025"


def norm_seg(c):
    return {"Europe, Middle East & Africa": "EMEA"}.get(c, c)


def load(work):
    return json.load(open(os.path.join(work, "operating_raw.json")))


def annual_series(pairs, lo="FY2016", hi=LATEST):
    """pairs: iterable of (label, value). Keeps the window and drops blanks."""
    out = {}
    for lab, v in pairs:
        if lab in ANNUAL and lo <= lab <= hi and v is not None:
            out[lab] = v
    return out


def growth_series(vg, metric_idx):
    """v1: number of the volume table's 'first' period; growth of FY y is read from the
    filing that reports y as its most recent period, on either the two-period layout
    (two pairs per row) or the single-period layout (unit cases / concentrate sales)."""
    out = {}
    for fy, blk in sorted(vg.items()):
        periods = blk["periods"]
        rows = {norm_seg(r[0]): r for r in blk["rows"]}
        for pi, (y, _prev) in enumerate(periods):
            lab = f"FY{y}"
            if lab not in ANNUAL:
                continue
            vals = {}
            for seg, r in rows.items():
                v = r[1 + 2 * pi + metric_idx]
                if v is None and seg == "Bottling Investments" and metric_idx == 1:
                    vals[seg] = "N/A"
                elif v is not None:
                    vals[seg] = v / 100.0
            out.setdefault(lab, {}).update(vals)
    return out


def sheet_ops(OPS):
    """Returns (blocks, ids) for the Operating Metrics sheet."""
    WARN = []
    ids = {}
    ucv = OPS["unit_case_volume_bn"]
    vol_rows = [
        {"id": "ops_ucv", "label": "Unit case volume (billion unit cases)", "type": "input", "fmt": "num1",
         "values": {f"FY{y}": v["value"] for y, v in sorted(ucv.items()) if f"FY{y}" in ANNUAL},
         "bold": True, "min_label": "FY2016", "max_label": LATEST},
        {"id": "ops_ucv_yoy", "label": "  YoY Growth", "type": "growth_yoy", "of": "ops_ucv", "fmt": "pct", "memo": True, "min_label": "FY2017", "max_label": LATEST},
    ]
    src = next((v for v in ucv.values() if v["filing"].startswith("FY")), None)
    vol_rows[0]["note"] = ("Company-reported Coca-Cola system unit case volume; the sentence in each 10-K lists that "
                           "year and the two prior years. Values are in billion unit cases as printed.")

    blk_vol = {"title": "BEVERAGE VOLUME — SYSTEM UNIT CASE VOLUME (Company disclosure, not from the financial statements)", "rows": vol_rows}

    # volume growth by segment, unit cases and concentrate sales, one table per metric
    def growth_rows(prefix, title, metric_idx):
        rows = [{"id": f"{prefix}_hdr", "label": title, "type": "input", "values": {}, "bold": True}]
        data = growth_series(OPS["volume_growth"], metric_idx)
        segs = []
        for y in sorted(data):
            for s in data[y]:
                if s not in segs:
                    segs.append(s)
        for s in segs:
            rows.append({"id": f"{prefix}_{re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')}", "label": s,
                         "type": "input", "indent": 1, "fmt": "pct",
                         "values": {y: data[y][s] for y in sorted(data) if s in data[y]}})
        for r in rows:
            if r["type"] != "spacer":
                r["min_label"], r["max_label"] = "FY2016", LATEST
        return rows

    blk_vol["rows"] += [{"type": "spacer"}] + growth_rows("ops_ucg", "Unit case volume growth by operating segment (as reported)", 0)
    blk_vol["rows"] += [{"type": "spacer"}] + growth_rows("ops_csg", "Concentrate sales volume growth by operating segment (as reported)", 1)

    # revenue factors
    fac = OPS["revenue_factors"]
    ids_fac = {}
    fac_rows = []
    names = ["Volume", "Price/Mix", "FX", "Acquisitions & Divestitures", "Total"]
    for ni, nm in enumerate(names):
        rid = f"ops_fac_{re.sub(r'[^a-z0-9]+', '_', nm.lower()).strip('_')}"
        val = {}
        for fy, blk in fac.items():
            for r in blk["rows"]:
                y = f"FY{fy}"
                if y in ANNUAL and r[1 + ni] is not None:
                    val.setdefault(norm_seg(r[0]), {})[y] = r[1 + ni] / 100.0
        rows = [{"id": f"{rid}_hdr", "label": f"Net operating revenue impact — {nm}", "type": "input", "values": {}, "bold": True}]
        segs = ["Consolidated"] + sorted(s for s in val if s != "Consolidated")
        for s in segs:
            rows.append({"id": f"{rid}_{re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')}", "label": s,
                         "type": "input", "indent": 1, "fmt": "pct", "values": val.get(s, {})})
        for r in rows:
            r["min_label"], r["max_label"] = "FY2019", LATEST
        fac_rows += rows + [{"type": "spacer"}]
        ids_fac[ni] = rows
    # component sum check per segment
    chk_rows = []
    seg_ids = {s: f"ops_fac_price_mix_{re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')}" for s in
               ["Consolidated"] + sorted({norm_seg(r[0]) for fy, b in fac.items() for r in b["rows"] if norm_seg(r[0]) != "Consolidated"})}
    for s, rid0 in seg_ids.items():
        key = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
        parts = [f"{{ops_fac_volume_{key}}}", f"{{ops_fac_price_mix_{key}}}", f"{{ops_fac_fx_{key}}}",
                 f"{{ops_fac_acquisitions_divestitures_{key}}}"]
        chk_rows.append({"id": f"ops_fac_chk_{key}", "label": f"Check: {s} revenue factors sum to Total (≈0)", "type": "check",
                         "expr": "+".join(parts) + f"-{{ops_fac_total_{key}}}", "fmt": "pct", "memo": True,
                         "min_label": "FY2019", "max_label": LATEST})
    blk_fac = {"title": "NET OPERATING REVENUE FACTORS — VOLUME / PRICE-MIX / FX / ACQUISITIONS & DIVESTITURES (% impact, as reported)",
               "rows": fac_rows + chk_rows}

    # line of business
    lob = OPS["line_of_business"]
    lob_rows = []
    for metric in ("Concentrate operations", "Finished product operations", "Total"):
        vals = {"United States": {}, "International": {}, "Total": {}}
        for fy, blk in lob.items():
            for y, rowsd in blk["blocks"].items():
                lab = f"FY{y}"
                if lab not in ANNUAL or metric not in rowsd:
                    continue
                v = rowsd[metric]
                if v[0] is not None:
                    vals["United States"][lab] = v[0]
                if v[1] is not None:
                    vals["International"][lab] = v[1]
                if v[2] is not None:
                    vals["Total"][lab] = v[2]
        hdr_i = f"ops_lob_{re.sub(r'[^a-z0-9]+', '_', metric.lower()).strip('_')}"
        lob_rows.append({"id": f"{hdr_i}_hdr", "label": metric, "type": "input", "values": {}, "bold": True})
        for k in ("United States", "International", "Total"):
            kid = f"{hdr_i}_{re.sub(r'[^a-z0-9]+', '_', k.lower()).strip('_')}"
            lob_rows.append({"id": kid, "label": k, "type": "input", "indent": 1, "values": vals[k],
                             "bold": k == "Total", "border_top": k == "Total"})
        lob_rows.append({"id": f"{hdr_i}_chk", "label": f"Check: {metric} US + International - Total (≈0)", "type": "check",
                         "expr": f"{{{hdr_i}_united_states}}+{{{hdr_i}_international}}-{{{hdr_i}_total}}", "fmt": "num", "memo": True})
        lob_rows.append({"type": "spacer"})
    lob_rows.append({"id": "ops_lob_chk_is", "label": "Check: line of business total vs IS net operating revenues (≈0)", "type": "check",
                     "expr": "{ops_lob_total_total}-{IS:net_operating_revenues}", "fmt": "num", "memo": True})
    for r in lob_rows:
        if r.get("type") != "spacer":
            r["min_label"], r["max_label"] = "FY2018", LATEST
            r.setdefault("note", "Note 3: Business and Revenue Disclosures — net operating revenues disaggregated by line of business.")
    blk_lob = {"title": "NET OPERATING REVENUES BY LINE OF BUSINESS — CONCENTRATE VS FINISHED PRODUCT OPERATIONS (Note 3)", "rows": lob_rows}

    # segment revenue mix
    segpct = OPS["segment_revenue_pct"]
    mix = {}
    for fy, blk in segpct.items():
        for yi, y in enumerate(blk["years"]):
            lab = f"FY{y}"
            if lab not in ANNUAL:
                continue
            for seg, vals in blk["rows"].items():
                if yi < len(vals) and vals[yi] is not None:
                    mix.setdefault(norm_seg(seg), {})[lab] = vals[yi] / 100.0
    mix_rows = []
    for s in ["EMEA", "Latin America", "North America", "Asia Pacific", "Global Ventures", "Bottling Investments", "Corporate", "Total"]:
        if s not in mix:
            continue
        mix_rows.append({"id": f"ops_mix_{re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')}", "label": s, "type": "input",
                         "values": mix[s], "indent": s != "Total", "bold": s == "Total", "border_top": s == "Total",
                         "fmt": "pct", "min_label": "FY2018", "max_label": LATEST})
    blk_mix = {"title": "REVENUE MIX — OPERATING SEGMENT % OF COMPANY NET OPERATING REVENUES (as reported; Global Ventures exists FY2019-FY2024 only)",
               "rows": mix_rows}

    # customer concentration
    conc = OPS["customer_concentration"]
    conc_rows = []
    for fy in sorted(conc):
        lab = f"FY{fy}"
        if lab not in ANNUAL:
            continue
        item = next((c for c in conc[fy] if c["kind"] == "bottler"), None)
        if item:
            conc_rows.append({"id": f"ops_conc_{fy}", "label": f"Largest bottler % of net operating revenues ({lab})", "type": "calc",
                              "expr": str(item["pct"] / 100.0), "fmt": "pct", "memo": True,
                              "min_label": lab, "max_label": lab,
                              "note": f"As disclosed in the FY{fy} 10-K: one bottler accounted for {item['pct']}% of net operating revenues (EMEA and Asia Pacific segments). This is a fixed value, not a workbook formula."})
    if conc_rows:
        blk_conc = {"title": "CUSTOMER CONCENTRATION", "rows": conc_rows}
    else:
        blk_conc = None

    blocks = [blk_vol, blk_fac, blk_lob, blk_mix]
    if blk_conc:
        blocks.append(blk_conc)
    return blocks


def val_series(rows_src, years, label_candidates):
    """Pick a row by label (first match) and return {FY: value}."""
    out = {}
    for cand in label_candidates:
        for lab, vals in rows_src:
            if lab == cand or lab.startswith(cand):
                for yi, y in enumerate(years):
                    if yi < len(vals) and vals[yi] is not None and f"FY{y}" in ANNUAL:
                        out[f"FY{y}"] = vals[yi]
                if out:
                    return out
    return out


def sheet_notes(OPS):
    blocks = []
    # equity method investee aggregate
    eq = OPS["equity_method_summary"]
    merged = {}
    yrs_seen = set()
    for fy, blk in eq.items():
        for lab, vals in blk["rows"].items():
            key = lab.replace("Company equity income (loss) — net", "Equity income (loss) — net")
            for yi, y in enumerate(blk["years"]):
                if yi < len(vals) and vals[yi] is not None and f"FY{y}" in ANNUAL:
                    merged.setdefault(key, {})[f"FY{y}"] = vals[yi]
                    yrs_seen.add(y)
    order = ["Net operating revenues", "Cost of goods sold", "Gross profit", "Operating income",
             "Consolidated net income", "Less: Net income attributable to noncontrolling interests",
             "Net income attributable to common shareowners", "Equity income (loss) — net"]
    rows = []
    for nm in order:
        if nm not in merged:
            continue
        rid = "note_eq_" + re.sub(r"[^a-z0-9]+", "_", nm.lower()).strip("_")
        rows.append({"id": rid, "label": nm, "type": "input", "values": merged[nm],
                     "bold": nm in ("Gross profit", "Operating income", "Equity income (loss) — net"),
                     "indent": nm not in ("Gross profit", "Operating income", "Equity income (loss) — net"),
                     "min_label": f"FY{min(yrs_seen)}", "max_label": f"FY{max(yrs_seen)}",
                     "note": "Note 6 Equity Method Investments — aggregate financial information of the investees, and the Company's share of their net income."})
    if rows:
        rows.append({"id": "note_eq_chk_is", "label": "Check: investees' equity income - IS equity income (loss) — net (≈0)", "type": "check",
                     "expr": "{note_eq_equity_income_loss_net}-{IS:equity_income_loss_net}", "fmt": "num", "memo": True,
                     "min_label": f"FY{min(yrs_seen)}", "max_label": f"FY{max(yrs_seen)}"})
    blocks.append({"title": "EQUITY METHOD INVESTEES — AGGREGATE FINANCIAL INFORMATION AND THE COMPANY'S SHARE OF NET INCOME (Note 6)",
                   "rows": rows})

    # fair value vs carrying value (latest filing)
    fv = OPS["equity_fair_value"]
    latest = max(fv)
    fv_rows = []
    for row in fv[latest]["rows"]:
        lab, v = row[0], row[1:]
        if lab.startswith("Total"):
            continue
        fv_rows.append({"id": "note_fv_" + re.sub(r"[^a-z0-9]+", "_", lab.lower()).strip("_"), "label": lab, "type": "input",
                        "values": {LATEST: v[0]}, "indent": 1, "min_label": LATEST, "max_label": LATEST})
    blocks.append({"title": f"EQUITY METHOD INVESTMENTS — FAIR VALUE VS CARRYING VALUE, PUBLICLY TRADED INVESTEES ({LATEST}, Note 6)",
                   "rows": fv_rows})

    # income taxes
    tp = OPS["tax_pretax"]
    tp_rows = []
    for nm in ("United States", "International", "Total"):
        vals = {}
        for fy, blk in tp.items():
            for yi, y in enumerate(blk["years"]):
                if nm in blk["rows"] and yi < len(blk["rows"][nm]) and blk["rows"][nm][yi] is not None and f"FY{y}" in ANNUAL:
                    vals[f"FY{y}"] = blk["rows"][nm][yi]
        tp_rows.append({"id": "note_tax_pt_" + nm.lower().replace(" ", "_"), "label": nm, "type": "input", "values": vals,
                        "bold": nm == "Total", "border_top": nm == "Total", "indent": nm != "Total",
                        "min_label": "FY2016", "max_label": LATEST,
                        "note": "Note 15 Income Taxes — income before income taxes by jurisdiction. FY2024-FY2023 Puerto Rico amounts were reclassified from United States to International on adoption of ASU 2023-09."})
    blocks.append({"title": "INCOME BEFORE INCOME TAXES BY JURISDICTION (Note 15)", "rows": tp_rows})

    # current / deferred
    cd = OPS["tax_current_deferred"]
    cd_rows = []
    for nm in ("Current", "Deferred"):
        vals_tot, vals_us, vals_sl, vals_int = {}, {}, {}, {}
        for fy, blk in cd.items():
            for y, b in blk["blocks"].items():
                if nm not in b or f"FY{y}" not in ANNUAL:
                    continue
                for k, tgt in zip(range(4), (vals_us, vals_sl, vals_int, vals_tot)):
                    if k < len(b[nm]) and b[nm][k] is not None:
                        tgt[f"FY{y}"] = b[nm][k]
        cd_rows.append({"id": f"note_tax_{nm.lower()}_hdr", "label": nm, "type": "input", "values": {}, "bold": True})
        for k, tgt in (("United States", vals_us), ("State and Local", vals_sl), ("International", vals_int), ("Total", vals_tot)):
            cd_rows.append({"id": f"note_tax_{nm.lower()}_{re.sub(r'[^a-z0-9]+', '_', k.lower()).strip('_')}", "label": k,
                            "type": "input", "values": tgt, "indent": k != "Total", "bold": k == "Total",
                            "min_label": "FY2019", "max_label": LATEST,
                            "note": "Note 15 Income Taxes — current and deferred tax expense by jurisdiction."})
        cd_rows.append({"type": "spacer"})
    for r in cd_rows:
        if r.get("type") != "spacer":
            r.setdefault("min_label", "FY2019")
            r["max_label"] = LATEST
    blocks.append({"title": "INCOME TAXES — CURRENT AND DEFERRED BY JURISDICTION (Note 15)", "rows": cd_rows})

    # unrecognized tax benefits
    utb = OPS["unrecognized_tax_benefits"]
    utb_rows = []
    labs = []
    for fy, blk in utb.items():
        for lab in blk["rows"]:
            if lab not in labs:
                labs.append(lab)
    used_utb = set()
    for lab in labs:
        vals = {}
        for fy, blk in utb.items():
            if lab not in blk["rows"]:
                continue
            for yi, y in enumerate(blk["years"]):
                if yi < len(blk["rows"][lab]) and blk["rows"][lab][yi] is not None and f"FY{y}" in ANNUAL:
                    vals[f"FY{y}"] = blk["rows"][lab][yi]
        base = re.sub(r"[^a-z0-9]+", "_", lab.lower()).strip("_")[:40]
        rid, n = "note_utb_" + base, 2
        while rid in used_utb:
            rid, n = f"note_utb_{base}_{n}", n + 1
        used_utb.add(rid)
        utb_rows.append({"id": rid, "label": lab,
                         "type": "input", "values": vals, "indent": not lab.startswith("Balance"),
                         "bold": lab.startswith("Balance"), "min_label": "FY2016", "max_label": LATEST,
                         "note": "Note 15 Income Taxes — reconciliation of the gross unrecognized tax benefits."})
    blocks.append({"title": "UNRECOGNIZED TAX BENEFITS — ROLL-FORWARD (Note 15)", "rows": utb_rows})

    # debt by type (latest filing)
    db = OPS["debt_by_type"]
    latest_d = max(db)
    dblk = db[latest_d]
    years_d = dblk["years"]
    d_rows = []
    for row in dblk["rows"]:
        lab = row[0]
        vals = {f"FY{years_d[i]}": row[1 + i] for i in range(len(years_d)) if row[1 + i] is not None}
        d_rows.append({"id": "note_debt_" + re.sub(r"[^a-z0-9]+", "_", lab.lower()).strip("_")[:40], "label": lab,
                       "type": "input", "values": vals, "indent": not lab.startswith(("Total", "Long-term")),
                       "bold": lab.startswith(("Total", "Long-term")), "border_top": lab.startswith(("Total", "Long-term")),
                       "min_label": f"FY{min(years_d)}", "max_label": f"FY{max(years_d)}",
                       "note": "Note 11 Debt and Borrowing Arrangements — long-term debt by type, as filed (amounts only; weighted-average rates are in the filing)."})
    blocks.append({"title": f"LONG-TERM DEBT BY TYPE ({latest_d} 10-K, Note 11)", "rows": d_rows})

    # held for sale
    hfs = OPS["held_for_sale"]
    latest_h = max(hfs)
    hblk = hfs[latest_h]
    h_rows = []
    for row in hblk["rows"]:
        lab = row[0]
        vals = {f"FY{hblk['years'][i]}": row[1 + i] for i in range(len(hblk["years"])) if row[1 + i] is not None}
        h_rows.append({"id": "note_hfs_" + re.sub(r"[^a-z0-9]+", "_", lab.lower()).strip("_")[:40], "label": lab,
                       "type": "input", "values": vals, "indent": True,
                       "bold": lab in ("Assets held for sale", "Liabilities held for sale"),
                       "border_top": lab in ("Assets held for sale", "Liabilities held for sale"),
                       "min_label": f"FY{min(hblk['years'])}", "max_label": f"FY{max(hblk['years'])}",
                       "note": "Note 2 Acquisitions and Divestitures — major classes of assets and liabilities classified as held for sale."})
    blocks.append({"title": f"ASSETS AND LIABILITIES HELD FOR SALE ({latest_h} 10-K, Note 2)", "rows": h_rows})

    return blocks


if __name__ == "__main__":
    import sys
    OPS = load(sys.argv[1])
    b1 = sheet_ops(OPS)
    b2 = sheet_notes(OPS)
    print("Ops sheet blocks:", len(b1), "rows:", sum(len(b["rows"]) for b in b1))
    for b in b1:
        print("   ", b["title"][:90], len(b["rows"]))
    print("Notes sheet blocks:", len(b2), "rows:", sum(len(b["rows"]) for b in b2))
    for b in b2:
        print("   ", b["title"][:90], len(b["rows"]))
