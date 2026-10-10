# Gap-sweep extension: executed inside build_model.py's namespace (before Derived Metrics).
# Adds MD&A operating tables, note schedules, prose-disclosed series, year-end schedules and
# the outlook / text-disclosure registers.  All values come from mcd_extract3 / mcd_extract4.
import mcd_extract as m
import mcd_extract3 as Z3
import mcd_extract4 as Z4

R3 = Z3.run_all()
A16 = A  # FY2016-FY2025


def S3(key, rid, periods=A16):
    return {p: v for p, v in R3[key].get(rid, {}).items() if p in periods and v is not None}


def sumrows(prefix, ids):
    return "+".join("{%s%s}" % (prefix, i) for i in ids)


# ------------------------------------------------------------------ SEG ------
SEG_NEW = []
rm = []
for s_, nm in (("us", "U.S."), ("iom", "International Operated Markets"), ("idl", "International Developmental Licensed Markets & Corporate")):
    rm.append(inp(f"m_rmf_{s_}", f"Franchised margins: {nm}", S3("rm", f"rm_fran_{s_}"), indent=1))
rm.append(inp("m_rmf_tot", "Franchised margins: total", S3("rm", "rm_fran_total"), bold=True, border_top=True))
for s_, nm in (("us", "U.S."), ("iom", "International Operated Markets")):
    rm.append(inp(f"m_rmc_{s_}", f"Company-owned and operated margins: {nm}", S3("rm", f"rm_co_{s_}"), indent=1,
                  note="International Developmental Licensed Markets & Corporate shown as n/m by the company"))
rm.append(inp("m_rmc_tot", "Company-owned and operated margins: total", S3("rm", "rm_co_total"), bold=True, border_top=True))
rm.append(sp())
for s_, nm in (("us", "U.S."), ("iom", "International Operated Markets")):
    rm.append(inp(f"m_rmt_{s_}", f"Total restaurant margins: {nm}", S3("rm", f"rm_tot_{s_}"), indent=1,
                  note="Reported from the FY2020 10-K (covers FY2018+)"))
rm.append(inp("m_rmt_tot", "Total restaurant margins: total", S3("rm", "rm_tot_total"), bold=True, border_top=True))
rm.append(sp())
for s_, nm in (("us", "U.S."), ("iom", "International Operated Markets"), ("idl", "International Developmental Licensed Markets & Corporate")):
    rm.append(calc(f"m_rmf_pct_{s_}", f"  Franchised margin % of franchised revenues: {nm}", f"{{m_rmf_{s_}}}/{{r_fran_{s_}}}", fmt="pct", memo=True))
rm.append(calc("m_rmf_pct_tot", "  Franchised margin % of franchised revenues: total", "{m_rmf_tot}/{r_fran_tot}", fmt="pct", memo=True))
rm.append(calc("m_rmc_pct_us", "  Company-operated margin % of company-operated sales: U.S.", "{m_rmc_us}/{r_co_us}", fmt="pct", memo=True))
rm.append(calc("m_rmc_pct_iom", "  Company-operated margin % of company-operated sales: International Operated Markets", "{m_rmc_iom}/{r_co_iom}", fmt="pct", memo=True))
rm.append(calc("m_rmc_pct_tot", "  Company-operated margin % of company-operated sales: total", "{m_rmc_tot}/{r_co_tot}", fmt="pct", memo=True))
rm.append(calc("m_rmf_share", "  Franchised margins % of total restaurant margins", "{m_rmf_tot}/({m_rmf_tot}+{m_rmc_tot})", fmt="pct", memo=True))
rm.append(chk("m_tie_rmf", "Franchised margins vs income statement (revenues less occupancy; rounding)", "{m_rmf_tot}-({IS:rev_franchised}-{IS:franchised_occupancy})"))
rm.append(chk("m_tie_rmf_seg", "Franchised margins by segment vs total (rounding)", "{m_rmf_us}+{m_rmf_iom}+{m_rmf_idl}-{m_rmf_tot}"))
rm.append(chk("m_tie_rmc", "Company-operated margins vs income statement (sales less restaurant expenses; rounding)", "{m_rmc_tot}-({IS:rev_company}-{IS:co_expenses})"))
rm.append(chk("m_tie_rmt", "Total restaurant margins vs franchised + company-operated (rounding)", "{m_rmt_tot}-{m_rmf_tot}-{m_rmc_tot}", min_label="FY2018"))
SEG_NEW.append({"title": "RESTAURANT MARGINS BY SEGMENT (MD&A, FY2017-FY2025)", "rows": rm})

sg = []
for s_, nm in (("us", "U.S."), ("iom", "International Operated Markets"), ("idl", "International Developmental Licensed Markets & Corporate")):
    sg.append(inp(f"m_sga_{s_}", nm, S3("sga", f"sga_{s_}"), indent=1))
sg.append(inp("m_sga_tot", "Total selling, general & administrative expenses", S3("sga", "sga_total"), bold=True, border_top=True))
sg.append(inp("m_sga_inc", "Less: incentive-based compensation (cash incentives and share-based compensation)", S3("sga", "sga_incentive"), indent=1))
sg.append(inp("m_sga_ex", "Total excluding incentive-based compensation", S3("sga", "sga_ex_incentive"), bold=True, border_top=True))
sg.append(calc("m_sga_inc_pct", "  Incentive-based compensation % of SG&A", "{m_sga_inc}/{m_sga_tot}", fmt="pct", memo=True))
sg.append(yoy("m_sga_yoy", "m_sga_tot"))
sg.append(yoy("m_sga_ex_yoy", "m_sga_ex", "  Excluding incentive compensation: YoY Growth"))
sg.append(chk("m_tie_sga", "MD&A SG&A vs income statement (rounding)", "{m_sga_tot}-{IS:sga_total}"))
sg.append(chk("m_tie_sga_seg", "SG&A by segment vs total (rounding)", "{m_sga_us}+{m_sga_iom}+{m_sga_idl}-{m_sga_tot}"))
sg.append(chk("m_tie_sga_inc", "Total less incentive vs excluding incentive (rounding)", "{m_sga_tot}-{m_sga_inc}-{m_sga_ex}"))
SEG_NEW.append({"title": "SELLING, GENERAL & ADMINISTRATIVE EXPENSES BY SEGMENT AND INCENTIVE COMPENSATION (MD&A, FY2017-FY2025)", "rows": sg})
SEG_SHEET["blocks"][-1:-1] = SEG_NEW  # keep the superseded-structure block last

# ------------------------------------------------------------------ OM -------
fs = []
fs_total = merge(S3("fs", "fs_total"), {"FY2016": item6["i6_fran_sales"]["FY2016"]})
for s_, nm in (("us", "U.S."), ("iom", "International Operated Markets"), ("idl", "International Developmental Licensed Markets")):
    fs.append(inp(f"x_fs_{s_}", nm, S3("fs", f"fs_{s_}"), indent=1))
fs.append(inp("x_fs_tot", "Franchised sales: total", fs_total, bold=True, border_top=True,
              note="FY2016 from Item 6 selected financial data (segment split not comparable); FY2017+ from the MD&A franchised-sales table"))
fs.append(yoy("x_fs_yoy", "x_fs_tot"))
fs.append(inp("x_fs_conv", "Conventional franchised", S3("fs", "fs_conv"), indent=1))
fs.append(inp("x_fs_dev", "Developmental licensed", S3("fs", "fs_devlic"), indent=1))
fs.append(inp("x_fs_aff", "Foreign affiliated", S3("fs", "fs_foreign"), indent=1))
fs.append(sp())
fs.append(calc("x_sws", "Systemwide sales (analyst: franchised sales + Company-owned and operated sales)", "{x_fs_tot}+{IS:rev_company}", bold=True,
               note="Company defines Systemwide sales as sales at all restaurants; this sum is an analyst reconstruction from two disclosed components"))
fs.append(yoy("x_sws_yoy", "x_sws"))
fs.append(calc("x_take", "  Franchised revenues % of franchised sales", "{IS:rev_franchised}/{x_fs_tot}", fmt="pct", memo=True))
fs.append(calc("x_sga_sws", "  SG&A % of Systemwide sales", "{IS:sga_total}/{x_sws}", fmt="pct", memo=True))
fs.append(calc("x_fs_per_rest", "  Franchised sales per average franchised restaurant ($mm)", "{x_fs_tot}/(({rest_fran_tot}+{rest_fran_tot@-1})/2)", fmt="ps", memo=True, min_label="FY2017"))
fs.append(chk("x_tie_fs_seg", "Franchised sales by segment vs total (rounding)", "{x_fs_us}+{x_fs_iom}+{x_fs_idl}-{x_fs_tot}", min_label="FY2017"))
fs.append(chk("x_tie_fs_own", "Franchised sales by ownership type vs total (rounding)", "{x_fs_conv}+{x_fs_dev}+{x_fs_aff}-{x_fs_tot}", min_label="FY2017"))

rs = []
for s_, nm in (("us", "U.S."), ("iom", "International Operated Markets"), ("idl", "International Developmental Licensed Markets & Corporate")):
    rs.append(inp(f"x_rs_{s_}", nm, S3("rs", f"rseg_{s_}"), indent=1))
rs.append(inp("x_rs_tot", "Total systemwide restaurants", S3("rs", "rseg_total"), bold=True, border_top=True))
rs.append(calc("x_net_add", "Net restaurant additions (year-over-year change)", "{x_rs_tot}-{x_rs_tot@-1}", min_label="FY2018"))
rs.append(calc("x_unit_growth", "  Net unit growth %", "{x_net_add}/{x_rs_tot@-1}", fmt="pct", memo=True, min_label="FY2018"))
for s_, nm in (("us", "U.S."), ("iom", "International Operated Markets"), ("idl", "International Developmental Licensed Markets & Corporate")):
    rs.append(calc(f"x_rs_add_{s_}", f"  Net additions: {nm}", f"{{x_rs_{s_}}}-{{x_rs_{s_}@-1}}", memo=True, min_label="FY2018"))
rs.append(chk("x_tie_rs", "Segment restaurants vs total (rounding)", "{x_rs_us}+{x_rs_iom}+{x_rs_idl}-{x_rs_tot}", min_label="FY2017", strict=True))
rs.append(chk("x_tie_rs2", "Segment restaurant total vs restaurant-count block", "{x_rs_tot}-{rest_sys}", min_label="FY2017", strict=True))

fxr = []
for k, lab in (("fx_revenues", "Revenues"), ("fx_fran_margin", "Franchised margins"), ("fx_co_margin", "Company-owned and operated margins"),
               ("fx_sga", "Selling, general & administrative expenses (negative = higher expense)"), ("fx_op_income", "Operating income"),
               ("fx_net_income", "Net income")):
    fxr.append(inp("x_" + k, lab, S3("fx", k), indent=1))
fxr.append(inp("x_fx_eps", "Earnings per common share - diluted ($)", S3("fx", "fx_eps"), indent=1, fmt="ps"))
fxr.append(calc("x_fx_oi_pct", "  Currency impact as % of reported operating income", "{x_fx_op_income}/{IS:operating_income}", fmt="pct", memo=True))
fxr.append(calc("x_fx_rev_pct", "  Currency impact as % of reported revenues", "{x_fx_revenues}/{IS:total_revenues}", fmt="pct", memo=True))

# ---- non-GAAP reconciliations: keep only the adjustment lines of the filing that supplies the non-GAAP total
GROUPS = {
    "eps": {"gains_charges": ["strategic_charges", "strategic_gains_charges", "gains_charges", "gains_charges_net_of_tax"],
            "tax": ["income_tax_benefit_cost_net"], "settle": ["france_tax_settlement", "tax_settlement"]},
    "ni": {"gains_charges": ["gains_charges", "gains_charges_net_of_tax"], "tax": ["income_tax_benefit_cost_net"],
           "settle": ["france_tax_settlement", "tax_settlement"]},
    "oi": {"gains_charges": ["gains_charges"], "russia": ["russia_sale_charge"], "dy": ["dynamic_yield_sale_gain"],
           "japan": ["japan_stock_sale_gains"], "labs": ["mcd_tech_labs_sale_charge"]},
}


def ng_rows(kind, label_gaap, label_ng, fmt, is_ref):
    st = R3[kind]
    out = {g: {} for g in GROUPS[kind]}
    for per in st[f"{kind}_nongaap"]:
        if per not in A16:
            continue
        ref_fy = st.src[(f"{kind}_nongaap", per)][0]
        for g, members in GROUPS[kind].items():
            for mem in members:
                rid = f"{kind}_adj_{mem}"
                if per in st.get(rid, {}) and st.src[(rid, per)][0] == ref_fy:
                    out[g][per] = out[g].get(per, 0) + st[rid][per]
    rows = [inp(f"x_{kind}_gaap", label_gaap, S3(kind, f"{kind}_gaap"), bold=True, fmt=fmt)]
    names = {"gains_charges": "(Gains) / charges (strategic charges, restructuring, impairments, disposals)", "tax": "Income tax (benefit) cost, net",
             "settle": "Tax settlement", "russia": "Russia sale charge", "dy": "Dynamic Yield sale gain", "japan": "Japan stock sale gains",
             "labs": "McDonald's Tech Labs sale charge"}
    for g, vals in out.items():
        vals = {p: round(v, 4) for p, v in vals.items()}
        if any(v != 0 for v in vals.values()):
            rows.append(inp(f"x_{kind}_adj_{g}", names[g], vals, indent=1, fmt=fmt))
    rows.append(inp(f"x_{kind}_ng", label_ng, S3(kind, f"{kind}_nongaap"), bold=True, border_top=True, fmt=fmt))
    adj_ids = [r["id"] for r in rows if r["id"].startswith(f"x_{kind}_adj_")]
    lo = "FY2017" if kind == "eps" else "FY2021"
    rows.append(chk(f"x_{kind}_tie", "GAAP + adjustments vs non-GAAP (disclosed rounding)", "{x_%s_gaap}%s-{x_%s_ng}" % (kind, "".join("+{%s}" % i for i in adj_ids), kind), min_label=lo))
    rows.append(chk(f"x_{kind}_tie_is", "GAAP figure vs income statement (rounding)", "{x_%s_gaap}-{%s}" % (kind, is_ref), min_label=lo))
    return rows


ng_eps = ng_rows("eps", "GAAP earnings per share - diluted ($)", "Non-GAAP earnings per share - diluted ($)", "ps", "IS:eps_diluted")
ng_ni = ng_rows("ni", "GAAP net income", "Non-GAAP net income", "num", "IS:net_income")
ng_oi = ng_rows("oi", "GAAP operating income", "Non-GAAP operating income", "num", "IS:operating_income")
ng_oi.insert(-2, inp("x_oi_ngm", "Non-GAAP operating margin (as reported)", S3("oi", "oi_ng_margin"), fmt="pct", memo=True))
ng_oi.insert(-2, calc("x_oi_ngm_calc", "  Non-GAAP operating margin (recomputed on total revenues)", "{x_oi_ng}/{IS:total_revenues}", fmt="pct", memo=True))

cxp = [inp("x_cx_new", "New restaurants", S3("capex", "cx_new"), indent=1), inp("x_cx_exist", "Existing restaurants", S3("capex", "cx_existing"), indent=1),
       inp("x_cx_other", "Other", S3("capex", "cx_other"), indent=1),
       {"id": "x_cx_tot", "label": "Total capital expenditures", "type": "subtotal", "bold": True, "children": ["x_cx_new", "x_cx_exist", "x_cx_other"]},
       chk("x_cx_tie", "Capex by purpose vs cash-flow capital expenditures (sign flipped; rounding)", "{x_cx_tot}+{CF:cf_capex}", max_label="FY2019")]

# update Item 6 block: franchised sales now covered by the MD&A block above
for _b in OM_SHEET["blocks"]:
    if _b["title"].startswith("FRANCHISED SALES AND MARKET DATA"):
        _b["title"] = "MARKET DATA (ITEM 6 SELECTED FINANCIAL DATA, FY2016-FY2021 ONLY)"
        _b["rows"] = [r for r in _b["rows"] if r["id"] != "i6_fran_sales"]
OM_SHEET["blocks"][1:1] = [
    {"title": "FRANCHISED SALES AND SYSTEMWIDE SALES (MD&A; FY2016 TOTAL FROM ITEM 6)", "rows": fs},
    {"title": "RESTAURANTS BY SEGMENT AND NET ADDITIONS", "rows": rs},
]
OM_SHEET["blocks"] += [
    {"title": "CURRENCY TRANSLATION IMPACT ON REPORTED RESULTS (COMPANY-DISCLOSED BENEFIT / (COST) VS PRIOR-YEAR RATES)", "rows": fxr},
    {"title": "NON-GAAP RECONCILIATION: EARNINGS PER SHARE (ADJUSTMENT LINES AS PRESENTED IN THE FILING SUPPLYING EACH NON-GAAP FIGURE)", "rows": ng_eps},
    {"title": "NON-GAAP RECONCILIATION: NET INCOME (FY2021+)", "rows": ng_ni},
    {"title": "NON-GAAP RECONCILIATION: OPERATING INCOME (FY2021+)", "rows": ng_oi},
    {"title": "CAPITAL EXPENDITURES BY PURPOSE (DISCLOSED FY2016-FY2019 ONLY)", "rows": cxp},
]

# ------------------------------------------------------------------ NS -------
oo = [inp("n_oo_gain", "Gains on sales of restaurant businesses", S3("oo", "oo_gains"), indent=1),
      inp("n_oo_eq", "Equity in earnings of unconsolidated affiliates", S3("oo", "oo_equity"), indent=1),
      inp("n_oo_disp", "Asset dispositions and other (income) expense, net", S3("oo", "oo_dispositions"), indent=1),
      inp("n_oo_imp", "Impairment and other charges (gains), net", S3("oo", "oo_impairment"), indent=1),
      inp("n_oo_tot", "Other operating (income) expense, net", S3("oo", "oo_total"), bold=True, border_top=True),
      chk("n_oo_tie1", "Components vs total (rounding)", "{n_oo_gain}+{n_oo_eq}+{n_oo_disp}+{n_oo_imp}-{n_oo_tot}"),
      chk("n_oo_tie2", "Total vs income statement (rounding)", "{n_oo_tot}-{IS:other_operating}")]
no = [inp("n_no_int", "Interest income", S3("no", "no_interest_income"), indent=1),
      inp("n_no_fx", "Foreign currency and hedging activity", S3("no", "no_fx_hedging"), indent=1),
      inp("n_no_oth", "Other (income) expense", S3("no", "no_other"), indent=1),
      inp("n_no_tot", "Nonoperating (income) expense, net", S3("no", "no_total"), bold=True, border_top=True),
      chk("n_no_tie1", "Components vs total (rounding)", "{n_no_int}+{n_no_fx}+{n_no_oth}-{n_no_tot}"),
      chk("n_no_tie2", "Total vs income statement (rounding)", "{n_no_tot}-{IS:nonoperating}")]
gw = [inp("n_gw_us", "U.S.", S3("gw", "gw_us"), indent=1), inp("n_gw_iom", "International Operated Markets", S3("gw", "gw_iom"), indent=1),
      inp("n_gw_idl", "International Developmental Licensed Markets & Corporate", S3("gw", "gw_idl"), indent=1),
      {"id": "n_gw_tot", "label": "Goodwill: consolidated", "type": "subtotal", "bold": True, "children": ["n_gw_us", "n_gw_iom", "n_gw_idl"]},
      chk("n_gw_tie", "Goodwill by segment vs balance sheet (rounding)", "{n_gw_tot}-{BS:goodwill}", min_label="FY2019")]
CUR = [("usd", "U.S. dollar"), ("eur", "Euro"), ("gbp", "British pound sterling"), ("cad", "Canadian dollar"), ("aud", "Australian dollar"),
       ("jpy", "Japanese yen"), ("cny", "Chinese renminbi"), ("other", "Other currencies")]
debt = [inp(f"n_d_{k}", f"Debt obligations: {nm}", S3("debt", f"debt_{k}"), indent=1) for k, nm in CUR]
debt += [{"id": "n_d_before", "label": "Debt obligations before fair value adjustments and deferred debt costs", "type": "subtotal", "bold": True,
          "children": [f"n_d_{k}" for k, _ in CUR]},
         inp("n_d_fv", "Fair value adjustments", S3("debt", "debt_fv_adj"), indent=1),
         inp("n_d_dc", "Deferred debt costs", S3("debt", "debt_deferred_costs"), indent=1),
         {"id": "n_d_total", "label": "Total debt obligations (carrying amount)", "type": "subtotal", "bold": True, "children": ["n_d_before", "n_d_fv", "n_d_dc"]},
         calc("n_d_fx_share", "  Non-U.S.-dollar share of debt before adjustments", "1-{n_d_usd}/{n_d_before}", fmt="pct", memo=True),
         inp("n_d_fair", "Fair value of debt obligations (debt note text; $mm, rounded to $0.1bn)", S3("prose", "debt_fair_value"), indent=1),
         calc("n_d_fair_pct", "  Fair value % of carrying amount", "{n_d_fair}/{n_d_total}", fmt="pct", memo=True),
         inp("n_d_mat12", "Aggregate debt maturities falling due in the next year", S3("obl", "ob_debt_next12")),
         chk("n_d_tie1", "Total debt obligations vs balance sheet total debt (rounding)", "{n_d_total}-{BS:total_debt}"),
         chk("n_d_tie2", "Maturity schedule total vs debt before adjustments (rounding)", "{n_d_before}-%s" % "{n_d_mat_total}"),
         ]
debt.insert(-1, inp("n_d_mat_total", "Aggregate debt maturities: total (sum of the maturity schedule)", S3("obl", "ob_debt_total")))
lease = [inp("n_l_rest", "Rent expense: restaurants", S3("rent", "rent_restaurants"), indent=1, note="FY2016-FY2018 filed on a different (company-operated / franchised) basis; only the total is comparable"),
         inp("n_l_oth", "Rent expense: other", S3("rent", "rent_other"), indent=1),
         inp("n_l_tot", "Total rent expense", S3("rent", "rent_total"), bold=True, border_top=True),
         inp("n_l_var_co", "Variable lease payments in excess of minimum rents: Company-owned and operated restaurants", S3("prose", "var_rent_co"), indent=1,
             note="Disclosed in the lease note text"),
         inp("n_l_var_fr", "Variable lease payments in excess of minimum rents: franchised restaurants", S3("prose", "var_rent_fran"), indent=1),
         sp(),
         inp("n_l_pay12", "Lease payments due in the next 12 months", S3("obl", "ob_leases_next12"), indent=1,
             note="FY2016-FY2020: operating lease commitments per the contractual-obligations table; FY2021+: total (operating + finance) lease payments from the lease note"),
         inp("n_l_payt", "Total remaining lease payments (undiscounted)", S3("obl", "ob_leases_total"), indent=1),
         inp("n_l_rent12", "Minimum rent receivable under franchise arrangements in the next 12 months", S3("obl", "ob_min_rent_next12"), indent=1),
         inp("n_l_rentt", "Total minimum rent receivable under franchise arrangements (undiscounted)", S3("obl", "ob_min_rent_total"), indent=1),
         calc("n_l_cover12", "  Minimum rent receivable / lease payments, next 12 months", "{n_l_rent12}/{n_l_pay12}", fmt="x", memo=True),
         calc("n_l_covert", "  Minimum rent receivable / lease payments, total", "{n_l_rentt}/{n_l_payt}", fmt="x", memo=True)]
fa = [inp("n_fa_net", "Net property and equipment under franchise arrangements", S3("prose", "fa_net_ppe"), indent=1, note="Disclosed in $bn to one decimal; converted to $mm"),
      inp("n_fa_land", "  of which land", S3("prose", "fa_land"), indent=1),
      inp("n_fa_acc", "Accumulated depreciation and amortization on franchise-arrangement property", S3("prose", "fa_accum"), indent=1),
      calc("n_fa_pct", "  Franchise-arrangement property % of balance sheet net PP&E", "{n_fa_net}/{BS:net_ppe}", fmt="pct", memo=True),
      sp(),
      inp("n_ad_co", "Advertising costs in Company-owned and operated restaurant expenses", S3("prose", "adv_company_op"), indent=1),
      inp("n_ad_prod", "Advertising production and other marketing-related costs (in SG&A)", S3("prose", "adv_production"), indent=1),
      calc("n_ad_co_pct", "  Restaurant advertising % of Company-owned and operated sales", "{n_ad_co}/{IS:rev_company}", fmt="pct", memo=True),
      sp(),
      inp("n_sbc", "Share-based compensation expense", S3("sbc", "sbc_expense"), indent=1),
      inp("n_sbc_at", "Share-based compensation expense, after tax", S3("sbc", "sbc_after_tax"), indent=1),
      inp("n_sbc_eps", "Share-based compensation per diluted share ($)", S3("sbc", "sbc_eps"), indent=1, fmt="ps"),
      chk("n_sbc_tie", "Share-based compensation vs cash-flow add-back (rounding)", "{n_sbc}-{CF:cf_sbc}")]
facts = [inp("n_f_tot", "Franchised restaurants % of systemwide restaurants (text)", S3("prose", "franchised_pct_total"), fmt="pct",
             note="Stated in MD&A text for FY2018 and FY2023-FY2025 only"),
         inp("n_f_us", "Segment franchised %: U.S. (segment note text)", S3("prose", "franchised_pct_us"), fmt="pct", indent=1),
         inp("n_f_iom", "Segment franchised %: International Operated Markets", S3("prose", "franchised_pct_iom"), fmt="pct", indent=1),
         inp("n_f_idl", "Segment franchised %: International Developmental Licensed Markets & Corporate", S3("prose", "franchised_pct_idl"), fmt="pct", indent=1),
         inp("n_f_oi_ex", "Share of operating income earned outside the U.S. (liquidity section text, approximate)", S3("prose", "oi_outside_us"), fmt="pct"),
         inp("n_f_emp", "Company employees worldwide (text, approximate; 'over' / 'approximately')", S3("prose", "employees")),
         inp("n_f_del", "Restaurants offering delivery (text, approximate)", S3("prose", "delivery_restaurants")),
         inp("n_f_dt", "Drive thru locations (text, approximate)", S3("prose", "drive_thru"))]
NS_SHEET["blocks"] += [
    {"title": "OTHER OPERATING (INCOME) EXPENSE, NET - COMPONENTS (MD&A / NOTE)", "rows": oo},
    {"title": "NONOPERATING (INCOME) EXPENSE, NET - COMPONENTS (MD&A)", "rows": no},
    {"title": "GOODWILL BY SEGMENT (YEAR END; NOTE)", "rows": gw},
    {"title": "DEBT BY CURRENCY, FAIR VALUE AND MATURITY (FINANCING NOTE)", "rows": debt},
    {"title": "RENT, LEASE COMMITMENTS AND MINIMUM RENT RECEIVABLE", "rows": lease},
    {"title": "FRANCHISE-ARRANGEMENT ASSETS, ADVERTISING AND SHARE-BASED COMPENSATION", "rows": fa},
    {"title": "OTHER OPERATING FACTS DISCLOSED IN TEXT ONLY (APPROXIMATE; NOT TABULATED BY THE COMPANY)", "rows": facts},
]

# ------------------------------------------------------- table-kind sheets ---
H = lambda t: {"text": t, "header": True}
B = lambda t: {"text": t, "bold": True}


def tb(fy, pred):
    c = [t for t in Z3.tenk(fy) if pred(t)]
    assert len(c) == 1, (fy, [t["table_id"] for t in c])
    return c[0]


def ladder_tbl(fy, hdr0, firstcell):
    return tb(fy, lambda t: [m.norm(h).lower() for h in t["headers"]][:2] == hdr0)


sched = [[B("Year-end schedules disclosed in the notes (USD millions). Source: Form 10-K notes; table IDs refer to tables.json in this output folder.")], []]
for fy in (2025, 2024):
    sched.append([B(f"Aggregate debt maturities at December 31, {fy} (before fair value adjustments and deferred debt costs)")])
    sched.append([H("Year"), H("Amount")])
    for a, v in Z3.debt_ladder(fy):
        sched.append([a, v])
    sched.append([])
for fy in (2025, 2024):
    t = tb(fy, lambda t: [m.norm(h).lower() for h in t["headers"]][:4] == ["in millions", "owned sites", "leased sites", "total"])
    sched.append([B(f"Minimum rent payments due to the Company under franchise arrangements at December 31, {fy} (table {t['table_id']})")])
    sched.append([H("Year"), H("Owned sites"), H("Leased sites"), H("Total")])
    for r in t["rows"]:
        sched.append([r[0]] + Z3.nums(r))
    sched.append([])
for fy in (2025, 2024):
    t = tb(fy, lambda t: [m.norm(h).lower() for h in t["headers"]][0] == "in millions" and "present value of lease liability" in m.txt(t))
    sched.append([B(f"Lease payment maturities at December 31, {fy} (table {t['table_id']})")])
    sched.append([H("Year"), H("Operating"), H("Finance"), H("Total (as filed)")])
    for r in t["rows"]:
        v = Z3.nums(r)
        sched.append([r[0]] + v)
    sched.append([])
t = tb(2025, lambda t: m.norm(t["headers"][0]).lower() == "employee termination benefits" or [m.norm(h).lower() for h in t["headers"]][:2] == ["employee termination benefits", "costs to terminate contracts"])
sched.append([B(f"Restructuring reserve roll-forward - Accelerating the Organization (table {t['table_id']})")])
sched.append([H("Line"), H("Employee termination benefits"), H("Costs to terminate contracts"), H("Professional services and other"), H("Total")])
for r in t["rows"]:
    v = Z3.nums(r)
    sched.append([m.norm(r[0])] + (v if v else []))
sched.append([])
t = tb(2025, lambda t: [m.norm(h).lower() for h in t["headers"]][:2] == ["december 31, 2025", "december 31, 2024"] and "grand foods holding" in m.txt(t))
sched.append([B(f"Equity-method investees (table {t['table_id']}); company-reported, Level 1 fair value where listed")])
sched.append([H("Investee"), H("Ownership 2025"), H("Fair value 2025"), H("Carrying 2025"), H("Ownership 2024"), H("Fair value 2024"), H("Carrying 2024")])
for r in t["rows"][1:]:
    v = [x for x in m.row_values(r[1:])]
    sched.append([m.norm(r[0])] + [x[1] if isinstance(x, tuple) else x for x in v])
t = tb(2025, lambda t: [m.norm(h).lower() for h in t["headers"]][:2] == ["year ended december 31,", ""] and "dividends received" in m.txt(t))
sched.append([])
sched.append([B(f"Summarised financial data of the equity-method investees (table {t['table_id']})")])
sched.append([H("Line"), H("2025"), H("2024")])
for r in t["rows"][1:]:
    sched.append([m.norm(r[0])] + Z3.nums(r))
SCHED_SHEET = {"name": "Year-End Schedules", "kind": "table", "col_widths": [64, 18, 18, 18, 18, 18, 18], "tab_color": "548235", "table": sched}

# outlook + text register
gd = Z4.guidance()
reg = [[B("Management outlook and operating-KPI statements quoted verbatim from Form 10-K MD&A text. Source tier: SEC filing (company statement). Nature: FORWARD-LOOKING guidance / targets or company-stated facts - not realised results, not audited, not verified independently.")],
       [B("Locator = line number in the prepared document.md of the cited 10-K (sources/companies/US/MCD-mcdonalds/artifacts/ten_k/MCD-mcdonalds/FY<year>/psp_*/prepared/document.md). Management-stated conditions are preserved in the quoted text.")],
       [],
       [H("10-K fiscal year"), H("Guided year"), H("Item"), H("Verbatim statement"), H("Line")]]
for g in gd:
    reg.append([f"FY{g['fy']}", g["guided_year"], g["item"], g["text"], g["line"]])
reg += [[], [B("Operating KPI and strategy statements (FY2021-FY2025 10-Ks)")], [H("10-K fiscal year"), H("Topic"), H(""), H("Verbatim statement"), H("Line")]]
for k in Z4.kpi_sentences():
    reg.append([f"FY{k['fy']}", k["topic"], "", k["text"], k["line"]])
OUTLOOK_SHEET = {"name": "Outlook & Text KPIs", "kind": "table", "col_widths": [16, 16, 52, 150, 8], "tab_color": "548235", "table": reg}

# ---- comparable sales back-fill (U.S. and Total Company are continuous across the segment change) and guest counts
CG = lambda k: {p: round(v / 100, 4) for p, v in R3["cg"].get(k, {}).items() if p in A16}
for _b in OM_SHEET["blocks"]:
    if _b["title"].startswith("COMPARABLE SALES GROWTH"):
        for _r in _b["rows"]:
            if _r["id"] in ("comp_us", "comp_total"):
                _k = "cg_sales_us" if _r["id"] == "comp_us" else "cg_sales_total"
                _r["values"] = merge({p: v for p, v in CG(_k).items() if p in ("FY2016", "FY2017")}, _r["values"])
                _r["note"] = "FY2016-FY2017 from the FY2018/FY2019 10-K comparable-sales and guest-count tables (U.S. and Total Company definitions unchanged)"
        _b["title"] = "COMPARABLE SALES GROWTH (U.S. / TOTAL FROM FY2016; SEGMENTS FROM FY2018; SEGMENT DEFINITIONS PER FY2019+ 10-KS)"
        _gc = []
        for s_, nm in (("us", "U.S."), ("iom", "International Operated Markets"), ("idl", "International Developmental Licensed Markets & Corporate"), ("total", "Total Company")):
            _gc.append(inp(f"x_gc_{s_}", f"Comparable guest counts growth: {nm}", CG(f"cg_guest_{s_}"), fmt="pct", bold=(s_ == "total"),
                           note="Guest-count tables were discontinued after the FY2019 10-K"))
        _b["rows"] += [sp()] + _gc
for _b in OM_SHEET["blocks"]:
    if _b["title"].startswith("CURRENCY TRANSLATION"):
        for _r in _b["rows"]:
            if _r["id"].startswith("x_fx_") and _r["id"] not in ("x_fx_oi_pct", "x_fx_rev_pct") or _r["id"] in ("x_fx_op_income", "x_fx_net_income", "x_fx_revenues", "x_fx_sga", "x_fx_fran_margin", "x_fx_co_margin"):
                if not _r["label"].startswith("Currency impact"):
                    _r["label"] = "Currency impact - " + _r["label"]
