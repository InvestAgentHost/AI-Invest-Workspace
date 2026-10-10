#!/usr/bin/env python3
"""Assemble MCD model.json (bundle-only mode, SKILL Phase 3-4).

Every hard-coded number comes from mcd_extract / mcd_extract2, which parse the
collector bundle tables.json (SEC 10-K / 10-Q source HTML).  Nothing is typed by
hand.  Period precedence: latest filing containing a period wins (restatement
precedence); superseded values are logged to restatement_log.json.
"""
import json
import re
from collections import defaultdict

import mcd_extract as X
import mcd_extract2 as Y

T = X.load()
TB = {t["table_id"]: t for t in T}
ad, ahist, asrc, aunm = X.annual_data(T)
qd, qsrc, qunm = X.quarterly_data(T)
assert not aunm and not qunm, (aunm, qunm)
seg_new, seg_old = Y.segment_data()
revtype = Y.revenue_type_data()
comps = Y.comps_data()
sws = Y.systemwide_growth()
resttype = Y.restaurants_by_type()
item6 = Y.item6_data()
fmix = Y.franchised_mix()
sret = Y.shareholder_returns()
dstat = Y.debt_stats()
ppe = Y.ppe_data()
tax = Y.tax_data()

A = [f"FY{y}" for y in range(2016, 2026)]
Q = ["3Q2024", "4Q2024*", "1Q2025", "2Q2025", "3Q2025", "4Q2025*", "1Q2026", "2Q2026"]
QEND = {"3Q2024": "2024-09-30", "4Q2024*": "2024-12-31", "1Q2025": "2025-03-31", "2Q2025": "2025-06-30",
        "3Q2025": "2025-09-30", "4Q2025*": "2025-12-31", "1Q2026": "2026-03-31", "2Q2026": "2026-06-30"}
DER = {"4Q2024*": ("FY2024", "YTD3Q2024"), "4Q2025*": ("FY2025", "YTD3Q2025")}


def keyq(lbl):
    return lbl.rstrip("*")


def A_(rid, kind, lo=None, hi=None):
    d = {p: v for p, v in ad[kind].get(rid, {}).items() if p in A}
    return d


def avals(store, rid, periods=A):
    return {p: v for p, v in store.get(rid, {}).items() if p in periods and v is not None}


def q_flow(kind, rid, fy_fn=None):
    """Quarterly 3-month values + derived 4Q* (= FY less 9M YTD).  Returns dict."""
    out = {}
    src = qd[kind].get(rid, {})
    for lbl in Q:
        if lbl in DER:
            fy, ytd = DER[lbl]
            fyv = fy_fn(fy) if fy_fn else ad[kind].get(rid, {}).get(fy)
            y9 = src.get(ytd)
            if fyv is not None and y9 is not None:
                out[lbl] = round(fyv - y9, 6)
        else:
            v = src.get(keyq(lbl))
            if v is not None:
                out[lbl] = v
    return out


def q_stock(kind, rid):
    """Balance-sheet style: quarter-end filed value; 4Q* = 10-K year-end (filed)."""
    out = {}
    src = qd[kind].get(rid, {})
    for lbl in Q:
        if lbl in DER:
            fy = DER[lbl][0]
            v = ad[kind].get(rid, {}).get(fy)
        else:
            v = src.get(keyq(lbl))
        if v is not None:
            out[lbl] = v
    return out


def merge(a, q=None):
    d = dict(a)
    if q:
        d.update(q)
    return d


def inp(rid, label, values, **kw):
    r = {"id": rid, "label": label, "type": "input", "values": values}
    r.update(kw)
    return r


def sp():
    return {"type": "spacer"}


def calc(rid, label, expr, fmt="num", **kw):
    r = {"id": rid, "label": label, "type": "calc", "expr": expr, "fmt": fmt}
    r.update(kw)
    return r


def yoy(rid, of, label="  YoY Growth"):
    return {"id": rid, "label": label, "type": "growth_yoy", "of": of, "fmt": "pct", "memo": True}


def chk(rid, label, expr, strict=False, **kw):
    if rid.startswith(("s_", "r_tie", "ppe_tie")):
        kw.setdefault("min_label", "FY2017")
    r = {"id": rid, "label": label, "type": "check", "expr": expr, "fmt": "num", "memo": True}
    if not strict:
        r["expect_nonzero"] = True
    r.update(kw)
    return r


# =============================================================== INCOME STMT ==
def IS_(rid):
    return merge(avals(ad["IS"], rid), q_flow("IS", rid))


def IS_nq(rid):  # annual only
    return avals(ad["IS"], rid)


# SG&A: FY2016-FY2017 single line; FY2018+ split (FY2020 10-K recast).  Single-line
# values for FY2018/FY2019 (pre-recast filings) are intentionally excluded to avoid
# double counting; they are reconciled in restatement_log.json.
sga_reported = {p: v for p, v in avals(ad["IS"], "sga_reported").items() if p in ("FY2016", "FY2017")}
sga_da = merge(avals(ad["IS"], "sga_da"), q_flow("IS", "sga_da"))
sga_other = merge(avals(ad["IS"], "sga_other"), q_flow("IS", "sga_other"))

# company-operated expense components exist annually; 10-Qs give one total line
co_total_q = q_flow("IS", "co_expenses_total_q",
                    fy_fn=lambda fy: sum(ad["IS"][r].get(fy, 0) for r in ("co_food_paper", "co_payroll", "co_occupancy_other")))

is_rows = [
    inp("rev_franchised", "Revenues from franchised restaurants", IS_("rev_franchised"), indent=1),
    inp("rev_company", "Sales by Company-owned and operated restaurants", IS_("rev_company"), indent=1,
        note="Captioned 'Sales by Company-operated restaurants' in 10-Ks through FY2023"),
    inp("rev_other", "Other revenues", IS_("rev_other"), indent=1,
        note="Line first presented in FY2020 10-K with FY2018-FY2019 recast; FY2016-FY2017 pre-date the recast (no separate line)"),
    inp("total_revenues", "Total revenues", IS_("total_revenues"), bold=True, border_top=True),
    yoy("rev_yoy", "total_revenues"),
    sp(),
    inp("franchised_occupancy", "Franchised restaurants-occupancy expenses", IS_("franchised_occupancy"), indent=1),
    inp("co_food_paper", "Company-owned and operated: Food & paper", IS_nq("co_food_paper"), indent=2),
    inp("co_payroll", "Company-owned and operated: Payroll & employee benefits", IS_nq("co_payroll"), indent=2),
    inp("co_occupancy_other", "Company-owned and operated: Occupancy & other operating expenses", IS_nq("co_occupancy_other"), indent=2),
    inp("co_expenses_total_q", "Company-owned and operated restaurant expenses (10-Q single-line)", co_total_q, indent=2,
        note="10-Q presents one line; 10-K presents the three components above. 4Q* = FY components less 9M YTD"),
    calc("co_expenses", "Company-owned and operated restaurant expenses", "{co_food_paper}+{co_payroll}+{co_occupancy_other}",
         expr_q="{co_expenses_total_q}", indent=1),
    inp("other_restaurant_exp", "Other restaurant expenses", IS_("other_restaurant_exp"), indent=1,
        note="Line first presented in FY2020 10-K with FY2018-FY2019 recast"),
    inp("sga_reported", "SG&A (single-line presentation, FY2016-FY2017)", sga_reported, indent=2),
    inp("sga_da", "SG&A: Depreciation and amortization", sga_da, indent=2),
    inp("sga_other", "SG&A: Other", sga_other, indent=2),
    calc("sga_total", "Selling, general & administrative expenses", "{sga_reported}+{sga_da}+{sga_other}", indent=1,
         note="Analyst sum of as-filed components; filed as one line FY2016-FY2017"),
    inp("other_operating", "Other operating (income) expense, net", IS_("other_operating"), indent=1),
    inp("total_opex", "Total operating costs and expenses", IS_("total_opex"), bold=True, border_top=True),
    inp("operating_income", "Operating income", IS_("operating_income"), bold=True, border_top=True),
    calc("op_margin", "  Operating Margin", "{operating_income}/{total_revenues}", fmt="pct", memo=True),
    yoy("oi_yoy", "operating_income"),
    sp(),
    inp("interest_expense", "Interest expense, net of capitalized interest", IS_("interest_expense"), indent=1),
    inp("nonoperating", "Nonoperating (income) expense, net", IS_("nonoperating"), indent=1),
    inp("pretax_income", "Income before provision for income taxes", IS_("pretax_income"), bold=True, border_top=True),
    inp("tax_provision", "Provision for income taxes", IS_("tax_provision"), indent=1),
    inp("net_income", "Net income", IS_("net_income"), bold=True, border_top=True),
    calc("net_margin", "  Net Margin", "{net_income}/{total_revenues}", fmt="pct", memo=True),
    yoy("ni_yoy", "net_income"),
]

eps_rows = [
    inp("eps_basic", "Earnings per common share - basic ($)", merge(avals(ad["IS"], "eps_basic"), {l: qd["IS"]["eps_basic"].get(keyq(l)) for l in Q if l not in DER and qd["IS"]["eps_basic"].get(keyq(l)) is not None}), fmt="ps"),
    inp("eps_diluted", "Earnings per common share - diluted ($)", merge(avals(ad["IS"], "eps_diluted"), {l: qd["IS"]["eps_diluted"].get(keyq(l)) for l in Q if l not in DER and qd["IS"]["eps_diluted"].get(keyq(l)) is not None}), fmt="ps", bold=True),
    yoy("eps_yoy", "eps_diluted"),
    inp("dps_declared", "Dividends declared per common share ($)", merge(avals(ad["IS"], "dps_declared"), {l: qd["IS"]["dps_declared"].get(keyq(l)) for l in Q if l not in DER and qd["IS"]["dps_declared"].get(keyq(l)) is not None}), fmt="ps",
        note="3Q2024 includes the declaration normally made in 4Q (timing); FY basis is the 10-K figure"),
    inp("waso_basic", "Weighted-average shares outstanding - basic (mm)", merge(avals(ad["IS"], "waso_basic"), {l: qd["IS"]["waso_basic"].get(keyq(l)) for l in Q if l not in DER and qd["IS"]["waso_basic"].get(keyq(l)) is not None}), fmt="num1"),
    inp("waso_diluted", "Weighted-average shares outstanding - diluted (mm)", merge(avals(ad["IS"], "waso_diluted"), {l: qd["IS"]["waso_diluted"].get(keyq(l)) for l in Q if l not in DER and qd["IS"]["waso_diluted"].get(keyq(l)) is not None}), fmt="num1"),
]

is_checks = [
    chk("chk_rev", "Revenue components vs total (filed integers; rounding +/-2 expected)",
        "{rev_franchised}+{rev_company}+{rev_other}-{total_revenues}"),
    chk("chk_opex", "Operating cost lines vs total (rounding +/-2 expected)",
        "{franchised_occupancy}+{co_expenses}+{other_restaurant_exp}+{sga_total}+{other_operating}-{total_opex}"),
    chk("chk_opinc", "Revenue - operating costs - operating income (rounding)", "{total_revenues}-{total_opex}-{operating_income}"),
    chk("chk_pretax", "Operating income - interest - nonoperating - pre-tax (rounding)", "{operating_income}-{interest_expense}-{nonoperating}-{pretax_income}"),
    chk("chk_ni", "Pre-tax - tax - net income (rounding)", "{pretax_income}-{tax_provision}-{net_income}"),
]

IS_SHEET = {"name": "Income Statement", "short": "IS", "kind": "statement", "tab_color": "1F4E79", "contents": True,
            "blocks": [{"title": "INCOME STATEMENT - AS REPORTED", "rows": is_rows},
                       {"title": "PER-SHARE DATA AND SHARE COUNT", "rows": eps_rows},
                       {"title": "TIE-OUT CHECKS", "rows": is_checks}]}

# ================================================================ BALANCE SHEET
def BS_(rid):
    return merge(avals(ad["BS"], rid), q_stock("BS", rid))


bs_rows_assets = [
    inp("cash", "Cash and equivalents", BS_("cash"), indent=1),
    inp("receivables", "Accounts and notes receivable", BS_("receivables"), indent=1),
    inp("inventories", "Inventories, at cost, not in excess of market", BS_("inventories"), indent=1),
    inp("prepaid_other_ca", "Prepaid expenses and other current assets", BS_("prepaid_other_ca"), indent=1),
    inp("assets_held_for_sale", "Assets of businesses held for sale", BS_("assets_held_for_sale"), indent=1),
    inp("total_current_assets", "Total current assets", BS_("total_current_assets"), bold=True, border_top=True),
    sp(),
    inp("investments_affiliates", "Investments in and advances to affiliates", BS_("investments_affiliates"), indent=1),
    inp("goodwill", "Goodwill", BS_("goodwill"), indent=1),
    inp("misc_other_assets", "Miscellaneous other assets", BS_("misc_other_assets"), indent=1),
    inp("total_other_assets", "Total other assets", BS_("total_other_assets"), bold=True, border_top=True),
    inp("lease_rou", "Lease right-of-use asset, net", BS_("lease_rou"),
        note="Presented from FY2019 (ASC 842 adoption); no comparable line for FY2016-FY2018"),
    inp("ppe_gross", "Property and equipment, at cost", BS_("ppe_gross"), indent=1),
    inp("accum_depr", "Accumulated depreciation and amortization", BS_("accum_depr"), indent=1),
    inp("net_ppe", "Net property and equipment", BS_("net_ppe"), bold=True, border_top=True),
    inp("total_assets", "Total assets", BS_("total_assets"), bold=True, border_top=True),
]
bs_rows_liab = [
    inp("accounts_payable", "Accounts payable", BS_("accounts_payable"), indent=1),
    inp("lease_liab_current", "Lease liability (current)", BS_("lease_liab_current"), indent=1),
    inp("income_taxes_cl", "Income taxes", BS_("income_taxes_cl"), indent=1),
    inp("other_taxes", "Other taxes", BS_("other_taxes"), indent=1),
    inp("accrued_interest", "Accrued interest", BS_("accrued_interest"), indent=1),
    inp("accrued_payroll_other", "Accrued payroll and other liabilities", BS_("accrued_payroll_other"), indent=1),
    inp("dividend_payable", "Dividend payable", BS_("dividend_payable"), indent=1,
        note="Separate line only in the 3Q2024 10-Q"),
    inp("current_debt", "Short-term borrowings and current maturities of long-term debt", BS_("current_debt"), indent=1,
        note="Captioned 'Current maturities of long-term debt' through FY2021; line absent (nil) where blank"),
    inp("liabs_held_for_sale", "Liabilities of businesses held for sale", BS_("liabs_held_for_sale"), indent=1),
    inp("total_current_liabilities", "Total current liabilities", BS_("total_current_liabilities"), bold=True, border_top=True),
    inp("long_term_debt", "Long-term debt", BS_("long_term_debt")),
    inp("lt_lease_liab", "Long-term lease liability", BS_("lt_lease_liab")),
    inp("lt_income_taxes", "Long-term income taxes", BS_("lt_income_taxes"),
        note="Separate line from FY2017 10-K; FY2016 amount is within Other long-term liabilities (see restatement log)"),
    inp("deferred_revenues", "Deferred revenues - initial franchise fees", BS_("deferred_revenues"),
        note="Separate line from FY2018 10-K"),
    inp("other_lt_liabilities", "Other long-term liabilities", BS_("other_lt_liabilities")),
    inp("deferred_income_taxes", "Deferred income taxes", BS_("deferred_income_taxes")),
]
bs_rows_eq = [
    inp("preferred_stock", "Preferred stock (none issued)", BS_("preferred_stock"), indent=1),
    inp("common_stock", "Common stock, $0.01 par value", BS_("common_stock"), indent=1),
    inp("apic", "Additional paid-in capital", BS_("apic"), indent=1),
    inp("retained_earnings", "Retained earnings", BS_("retained_earnings"), indent=1),
    inp("aoci", "Accumulated other comprehensive income (loss)", BS_("aoci"), indent=1),
    inp("treasury_stock", "Common stock in treasury, at cost", BS_("treasury_stock"), indent=1),
    inp("total_equity", "Total shareholders' equity (deficit)", BS_("total_equity"), bold=True, border_top=True),
    inp("total_liab_equity", "Total liabilities and shareholders' equity (deficit)", BS_("total_liab_equity"), bold=True, border_top=True),
    calc("total_liabilities", "  Total liabilities (derived: total less equity)", "{total_liab_equity}-{total_equity}", memo=True, fmt="num"),
]
bs_checks = [
    chk("bs_check", "Balance Check: total assets - total liabilities and equity (should be ~0)", "{total_assets}-{total_liab_equity}", strict=True),
    chk("chk_assets", "Asset groups vs total assets (rounding +/-2 expected)", "{total_current_assets}+{total_other_assets}+{lease_rou}+{net_ppe}-{total_assets}"),
    chk("chk_ppe", "Gross PP&E - accumulated depreciation vs net PP&E (rounding)", "{ppe_gross}+{accum_depr}-{net_ppe}"),
    chk("chk_cl", "Current liability lines vs total (rounding +/-2 expected)",
        "{accounts_payable}+{lease_liab_current}+{income_taxes_cl}+{other_taxes}+{accrued_interest}+{accrued_payroll_other}+{dividend_payable}+{current_debt}+{liabs_held_for_sale}-{total_current_liabilities}"),
    chk("chk_eq", "Equity components vs total equity (rounding +/-2 expected)",
        "{preferred_stock}+{common_stock}+{apic}+{retained_earnings}+{aoci}+{treasury_stock}-{total_equity}"),
    chk("chk_cur_assets", "Current asset lines vs total (rounding +/-2 expected)",
        "{cash}+{receivables}+{inventories}+{prepaid_other_ca}+{assets_held_for_sale}-{total_current_assets}"),
]
bs_summary = [
    calc("total_debt", "Total debt (short-term + long-term)", "{current_debt}+{long_term_debt}", bold=True),
    calc("total_lease_liab", "Total lease liabilities (current + long-term)", "{lease_liab_current}+{lt_lease_liab}"),
    calc("net_debt", "Net debt (total debt less cash and equivalents)", "{total_debt}-{cash}", bold=True),
    calc("net_debt_leases", "Net debt including lease liabilities", "{net_debt}+{total_lease_liab}"),
]
BS_SHEET = {"name": "Balance Sheet", "short": "BS", "kind": "statement", "tab_color": "1F4E79", "contents": True,
            "blocks": [{"title": "ASSETS", "rows": bs_rows_assets},
                       {"title": "LIABILITIES", "rows": bs_rows_liab},
                       {"title": "SHAREHOLDERS' EQUITY (DEFICIT)", "rows": bs_rows_eq},
                       {"title": "TIE-OUT CHECKS", "rows": bs_checks},
                       {"title": "DEBT AND LEASE SUMMARY (ANALYST CALCULATION FROM FILED LINES)", "rows": bs_summary}]}

# ================================================================== CASH FLOW
def CF_(rid, **kw):
    return merge(avals(ad["CF"], rid), q_flow("CF", rid, **kw))


# 10-Q 'Other' within charges and credits includes the net gain/loss on sale line.
other_q = q_flow("CF", "cf_other_charges",
                 fy_fn=lambda fy: ad["CF"]["cf_other_charges"].get(fy, 0) + ad["CF"].get("cf_gain_sales", {}).get(fy, 0))
cf_other_all = merge(avals(ad["CF"], "cf_other_charges"), other_q)
wc_q = q_flow("CF", "cf_wc_total_reported",
              fy_fn=lambda fy: sum(ad["CF"][r].get(fy, 0) for r in ("cf_wc_receivables", "cf_wc_inventories", "cf_wc_payables", "cf_wc_income_taxes", "cf_wc_other_accrued")))

# merge the two labels the runtime sees for the held-for-sale cash line
held = dict(avals(ad["CF"], "cf_cash_held_sale_end"))
held.update(avals(ad["CF"], "cf_chg_cash_held_sale"))
cash_begin = merge(avals(ad["CF"], "cf_cash_begin"))
cash_end = merge(avals(ad["CF"], "cf_cash_end"))
for lbl in Q:
    if lbl in DER:
        fy, ytd = DER[lbl]
        yr = fy[2:]
        q3 = "3Q" + fy[2:]
        cash_begin[lbl] = qd["CF"]["cf_cash_end"][q3]
        cash_end[lbl] = ad["CF"]["cf_cash_end"][fy]
    else:
        cash_begin[lbl] = qd["CF"]["cf_cash_begin"][keyq(lbl)]
        cash_end[lbl] = qd["CF"]["cf_cash_end"][keyq(lbl)]

cf_op = [
    inp("cf_net_income", "Net income", CF_("cf_net_income"), bold=True),
    inp("cf_da", "Depreciation and amortization", CF_("cf_da"), indent=1, group=True),
    inp("cf_deferred_taxes", "Deferred income taxes", CF_("cf_deferred_taxes"), indent=1, group=True),
    inp("cf_sbc", "Share-based compensation", CF_("cf_sbc"), indent=1, group=True),
    inp("cf_gain_sales", "Net (gain) loss on sale of restaurant and other businesses", avals(ad["CF"], "cf_gain_sales"), indent=1, group=True,
        note="Separate line FY2017+ (recast); in 10-Qs it is included in 'Other' below"),
    inp("cf_other_charges", "Other", cf_other_all, indent=1, group=True,
        note="10-Q 'Other' and 4Q* include the net gain/loss on sale line"),
    inp("cf_wc_receivables", "Working capital: Accounts receivable", avals(ad["CF"], "cf_wc_receivables"), indent=2, group=True),
    inp("cf_wc_inventories", "Working capital: Inventories, prepaid expenses and other current assets", avals(ad["CF"], "cf_wc_inventories"), indent=2, group=True),
    inp("cf_wc_payables", "Working capital: Accounts payable", avals(ad["CF"], "cf_wc_payables"), indent=2, group=True),
    inp("cf_wc_income_taxes", "Working capital: Income taxes", avals(ad["CF"], "cf_wc_income_taxes"), indent=2, group=True),
    inp("cf_wc_other_accrued", "Working capital: Other accrued liabilities", avals(ad["CF"], "cf_wc_other_accrued"), indent=2, group=True),
    inp("cf_wc_total_q", "Changes in working capital items (10-Q single-line)", wc_q, indent=2, group=True,
        note="10-Q presents one line; 4Q* = FY sum of the five lines less 9M YTD"),
    calc("cf_wc_total", "Changes in working capital items", "{cf_wc_receivables}+{cf_wc_inventories}+{cf_wc_payables}+{cf_wc_income_taxes}+{cf_wc_other_accrued}",
         expr_q="{cf_wc_total_q}", indent=1),
    inp("cfo", "Cash provided by operations", CF_("cfo"), bold=True, border_top=True),
]
cf_inv = [
    inp("cf_capex", "Capital expenditures", CF_("cf_capex"), indent=1),
    inp("cf_purch_businesses", "Purchases of restaurant (and other) businesses", CF_("cf_purch_businesses"), indent=1),
    inp("cf_purch_equity_method", "Purchases of equity method investments", CF_("cf_purch_equity_method"), indent=1),
    inp("cf_sales_businesses", "Sales of restaurant (and other) businesses", CF_("cf_sales_businesses"), indent=1),
    inp("cf_proceeds_china_hk", "Proceeds from sale of businesses in China and Hong Kong", avals(ad["CF"], "cf_proceeds_china_hk"), indent=1),
    inp("cf_sales_property", "Sales of property", CF_("cf_sales_property"), indent=1),
    inp("cf_other_investing", "Other investing", CF_("cf_other_investing"), indent=1),
    inp("cfi", "Cash provided by (used for) investing activities", CF_("cfi"), bold=True, border_top=True),
]
cf_fin = [
    inp("cf_st_borrowings", "Net short-term borrowings (repayments)", CF_("cf_st_borrowings"), indent=1),
    inp("cf_lt_issuances", "Long-term financing issuances", CF_("cf_lt_issuances"), indent=1),
    inp("cf_lt_repayments", "Long-term financing repayments", CF_("cf_lt_repayments"), indent=1),
    inp("cf_treasury_purchases", "Treasury stock purchases", CF_("cf_treasury_purchases"), indent=1),
    inp("cf_dividends", "Common stock dividends", CF_("cf_dividends"), indent=1),
    inp("cf_option_proceeds", "Proceeds from stock option exercises", CF_("cf_option_proceeds"), indent=1),
    inp("cf_excess_tax_benefit", "Excess tax benefit on share-based compensation", avals(ad["CF"], "cf_excess_tax_benefit"), indent=1),
    inp("cf_other_financing", "Other financing", CF_("cf_other_financing"), indent=1),
    inp("cff", "Cash provided by (used for) financing activities", CF_("cff"), bold=True, border_top=True),
]
cf_walk = [
    inp("cf_fx", "Effect of exchange rates on cash and equivalents", CF_("cf_fx")),
    inp("cf_net_change", "Cash and equivalents increase (decrease)", CF_("cf_net_change"), bold=True),
    inp("cf_chg_held_sale", "Change in cash balances of businesses held for sale", held,
        note="Captioned 'Cash balance of businesses held for sale at end of year' in the FY2016 10-K"),
    inp("cf_cash_begin", "Cash and equivalents at beginning of period", cash_begin),
    inp("cf_cash_end", "Cash and equivalents at end of period", cash_end, bold=True, border_top=True),
    sp(),
    inp("cf_interest_paid", "Interest paid (supplemental)", avals(ad["CF"], "cf_interest_paid"), indent=1,
        note="Supplemental disclosure in 10-K only"),
    inp("cf_taxes_paid", "Income taxes paid, net (supplemental)",
        merge(avals(ad["CF"], "cf_taxes_paid"), {"FY2025": [r for r in TB["T840"]["rows"] if r[0].startswith("Total income taxes paid")][0][1]}), indent=1,
        note="Supplemental disclosure in 10-K only; FY2025 moved to the Income Tax note under ASU 2023-09 (table T840 of the FY2025 10-K)"),
]
cf_checks = [
    chk("cf_check", "Cash Walk Check (annual): begin + net change + held-for-sale change - end (filed integers; rounding +/-1 in FY2022-FY2023)",
        "{cf_cash_begin}+{cf_net_change}+{cf_chg_held_sale}-{cf_cash_end}", max_label="FY2025"),
    chk("cf_check_q", "Cash Walk Check (quarterly)", "{cf_cash_begin}+{cf_net_change}-{cf_cash_end}", strict=True, min_label="3Q2024"),
    chk("chk_cfo", "Operating lines vs CFO (rounding +/-2 expected)",
        "{cf_net_income}+{cf_da}+{cf_deferred_taxes}+{cf_sbc}+{cf_gain_sales}+{cf_other_charges}+{cf_wc_total}-{cfo}"),
    chk("chk_cfi", "Investing lines vs CFI (rounding +/-2 expected)",
        "{cf_capex}+{cf_purch_businesses}+{cf_purch_equity_method}+{cf_sales_businesses}+{cf_proceeds_china_hk}+{cf_sales_property}+{cf_other_investing}-{cfi}"),
    chk("chk_cff", "Financing lines vs CFF (rounding +/-2 expected)",
        "{cf_st_borrowings}+{cf_lt_issuances}+{cf_lt_repayments}+{cf_treasury_purchases}+{cf_dividends}+{cf_option_proceeds}+{cf_excess_tax_benefit}+{cf_other_financing}-{cff}"),
    chk("chk_netchg", "CFO + CFI + CFF + FX vs net change (rounding +/-2 expected)", "{cfo}+{cfi}+{cff}+{cf_fx}-{cf_net_change}"),
    chk("chk_cash_bs", "Ending cash vs balance sheet cash (rounding)", "{cf_cash_end}-{BS:cash}"),
]
cf_fcf = [
    calc("fcf", "Free cash flow (CFO + capital expenditures)", "{cfo}+{cf_capex}", bold=True),
    yoy("fcf_yoy", "fcf"),
    calc("capex_pct", "  Capital expenditures % of revenue", "0-{cf_capex}/{IS:total_revenues}", fmt="pct", memo=True),
    calc("fcf_margin", "  FCF margin", "{fcf}/{IS:total_revenues}", fmt="pct", memo=True),
    calc("fcf_conv", "  FCF conversion (FCF / net income)", "{fcf}/{IS:net_income}", fmt="pct", memo=True),
    calc("shareholder_returns_cf", "Dividends + treasury stock purchases (cash basis)", "0-{cf_dividends}-{cf_treasury_purchases}"),
    calc("returns_to_fcf", "  Shareholder returns % of FCF", "{shareholder_returns_cf}/{fcf}", fmt="pct", memo=True),
]
CF_SHEET = {"name": "Cash Flow", "short": "CF", "kind": "statement", "tab_color": "1F4E79", "contents": True,
            "blocks": [{"title": "OPERATING ACTIVITIES", "rows": cf_op},
                       {"title": "INVESTING ACTIVITIES", "rows": cf_inv},
                       {"title": "FINANCING ACTIVITIES", "rows": cf_fin},
                       {"title": "CASH RECONCILIATION AND SUPPLEMENTAL", "rows": cf_walk},
                       {"title": "TIE-OUT CHECKS", "rows": cf_checks},
                       {"title": "FREE CASH FLOW ANALYTICS (ANALYST CALCULATION)", "rows": cf_fcf}]}

# ================================================================== SEGMENTS
def S(store, rid, periods):
    return {p: v for p, v in store.get(rid, {}).items() if p in periods and v is not None}


SEGP = [f"FY{y}" for y in range(2017, 2026)]
SEGP_OLD = ["FY2016", "FY2017", "FY2018"]
sn = {"us": "U.S.", "iom": "International Operated Markets", "idl": "International Developmental Licensed Markets & Corporate"}


def seg_block(title, grp, bold_total=True, tie=None, margin_of=None, mix=False, store=seg_new, periods=SEGP, prefix="s", total_label=None):
    rows = []
    for s in ("us", "iom", "idl"):
        rows.append(inp(f"{prefix}_{grp}_{s}", sn[s], S(store, f"{grp}_{s}", periods), indent=1))
    rows.append({"id": f"{prefix}_{grp}_tot", "label": total_label or f"Total", "type": "subtotal",
                 "children": [f"{prefix}_{grp}_{s}" for s in ("us", "iom", "idl")], "bold": True})
    if margin_of:
        for s in ("us", "iom", "idl"):
            rows.append(calc(f"{prefix}_{grp}_m_{s}", f"  {sn[s]} margin", f"{{{prefix}_{grp}_{s}}}/{{{prefix}_{margin_of}_{s}}}", fmt="pct", memo=True))
        rows.append(calc(f"{prefix}_{grp}_m_tot", "  Total margin", f"{{{prefix}_{grp}_tot}}/{{{prefix}_{margin_of}_tot}}", fmt="pct", memo=True))
    if mix:
        for s in ("us", "iom", "idl"):
            rows.append(calc(f"{prefix}_{grp}_mix_{s}", f"  {sn[s]} % of total", f"{{{prefix}_{grp}_{s}}}/{{{prefix}_{grp}_tot}}", fmt="pct", memo=True))
    if tie:
        rows.append(chk(f"{prefix}_{grp}_tie", tie[0], tie[1]))
    return rows


# first segment-revenue period is FY2017 (FY2019 10-K recast); SEG rows therefore start at FY2017.
seg_blocks = [
    {"title": "SEGMENT REVENUES (CURRENT REPORTABLE-SEGMENT STRUCTURE, FY2017-FY2025)",
     "rows": seg_block("", "rev", mix=True, tie=("Segment revenue vs IS total revenues (rounding / recast timing)", "{s_rev_tot}-{IS:total_revenues}"),
                       total_label="Total revenues") + [yoy("s_rev_yoy", "s_rev_tot")]},
    {"title": "SEGMENT OPERATING INCOME", "rows": seg_block("", "opinc", margin_of="rev",
                                                           tie=("Segment operating income vs IS operating income", "{s_opinc_tot}-{IS:operating_income}"),
                                                           total_label="Total operating income")},
    {"title": "SEGMENT TOTAL ASSETS", "rows": seg_block("", "assets", tie=("Segment assets vs BS total assets", "{s_assets_tot}-{BS:total_assets}"), total_label="Total assets")},
    {"title": "SEGMENT CAPITAL EXPENDITURES", "rows": seg_block("", "capex", tie=("Segment capex vs CF capital expenditures (sign flipped)", "{s_capex_tot}+{CF:cf_capex}"), total_label="Total capital expenditures")},
    {"title": "SEGMENT DEPRECIATION AND AMORTIZATION", "rows": seg_block("", "da", tie=("Segment D&A vs CF depreciation and amortization", "{s_da_tot}-{CF:cf_da}"), total_label="Total depreciation and amortization")},
    {"title": "SEGMENT EXPENSE DETAIL (DISCLOSED FROM FY2022 10-K, ASU 2023-07 PRESENTATION)",
     "rows": (seg_block("", "fran_occ", periods=SEGP, total_label="Total franchised restaurants-occupancy expenses") + [sp()] +
              seg_block("", "co_exp", periods=SEGP, total_label="Total Company-operated restaurant expenses") + [sp()] +
              seg_block("", "sga", periods=SEGP, total_label="Total selling, general & administrative expenses") + [sp()] +
              seg_block("", "other_seg", periods=SEGP, total_label="Total other segment items"))},
]

# MD&A: franchised revenues / company-operated sales by segment
rt_rows = []
for grp, nm in (("fran", "Franchised revenues"), ("co", "Company-owned and operated sales")):
    for s in ("us", "iom", "idl"):
        rt_rows.append(inp(f"r_{grp}_{s}", f"{nm}: {sn[s]}", S(revtype, f"{grp}_{s}", SEGP), indent=1))
    rt_rows.append({"id": f"r_{grp}_tot", "label": f"Total {nm.lower()}", "type": "subtotal", "bold": True,
                    "children": [f"r_{grp}_{s}" for s in ("us", "iom", "idl")]})
rt_rows.append(inp("r_other_total", "Other revenues (total)", S(revtype, "other_total", SEGP)))
rt_rows.append({"id": "r_total", "label": "Total revenues", "type": "subtotal", "bold": True,
                "children": ["r_fran_tot", "r_co_tot", "r_other_total"]})
rt_rows.append(chk("r_tie_fran", "Franchised revenues by segment vs IS (rounding)", "{r_fran_tot}-{IS:rev_franchised}"))
rt_rows.append(chk("r_tie_co", "Company-operated sales by segment vs IS (rounding)", "{r_co_tot}-{IS:rev_company}"))
rt_rows.append(chk("r_tie_tot", "Total revenues vs IS (rounding / FY2017 pre-recast)", "{r_total}-{IS:total_revenues}"))
seg_blocks.append({"title": "REVENUE BY TYPE AND SEGMENT (MD&A REVENUE TABLE)", "rows": rt_rows})

# superseded structure FY2016-FY2018 (FY2018 10-K)
old_names = {"us": "U.S.", "ilm": "International Lead Markets", "hgm": "High Growth Markets", "fmc": "Foundational Markets & Corporate"}
old_rows = []
for grp, nm in (("rev", "Revenues"), ("opinc", "Operating income"), ("assets", "Total assets"), ("capex", "Capital expenditures"), ("da", "Depreciation and amortization")):
    for s in ("us", "ilm", "hgm", "fmc"):
        old_rows.append(inp(f"o_{grp}_{s}", f"{nm}: {old_names[s]}", S(seg_old, f"{grp}_{s}", SEGP_OLD), indent=1, max_label="FY2018"))
    old_rows.append(inp(f"o_{grp}_tot", f"Total {nm.lower()} (as reported)", S(seg_old, f"{grp}_tot", SEGP_OLD), bold=True, border_top=True, max_label="FY2018"))
    old_rows.append(sp())
old_rows.append(chk("o_tie_rev", "Old-structure revenue by segment vs reported total", "{o_rev_us}+{o_rev_ilm}+{o_rev_hgm}+{o_rev_fmc}-{o_rev_tot}", max_label="FY2018"))
old_rows.append(chk("o_tie_opinc", "Old-structure operating income by segment vs reported total", "{o_opinc_us}+{o_opinc_ilm}+{o_opinc_hgm}+{o_opinc_fmc}-{o_opinc_tot}", max_label="FY2018"))
seg_blocks.append({"title": "SUPERSEDED SEGMENT STRUCTURE (U.S. / INT'L LEAD / HIGH GROWTH / FOUNDATIONAL), FY2016-FY2018 - NOT COMPARABLE WITH BLOCKS ABOVE", "rows": old_rows})
SEG_SHEET = {"name": "Segments", "short": "SEG", "kind": "statement", "tab_color": "548235", "contents": True, "blocks": seg_blocks}

# ============================================================= OPERATING KPIs
rest_rows = [
    inp("rest_conv", "Conventional franchised", S(resttype, "rest_conv", A), indent=1),
    inp("rest_devlic", "Developmental licensed", S(resttype, "rest_devlic", A), indent=1),
    inp("rest_foreign", "Foreign affiliated", S(resttype, "rest_foreign", A), indent=1),
    inp("rest_fran_tot", "Total franchised restaurants",
        merge(S(resttype, "rest_fran_tot", A), {p: v for p, v in item6["i6_rest_fran"].items() if p in ("FY2016",)}), bold=True, border_top=True,
        note="FY2016 from Item 6 selected data (no type split)"),
    inp("rest_co", "Company-owned and operated restaurants",
        merge(S(resttype, "rest_co", A), {p: v for p, v in item6["i6_rest_co"].items() if p in ("FY2016",)}), indent=1),
    inp("rest_sys", "Total systemwide restaurants",
        merge(S(resttype, "rest_sys", A), {p: v for p, v in item6["i6_rest_sys"].items() if p in ("FY2016",)}), bold=True, border_top=True),
    yoy("rest_sys_yoy", "rest_sys"),
    calc("rest_fran_share", "  Franchised % of systemwide restaurants", "{rest_fran_tot}/{rest_sys}", fmt="pct", memo=True),
    chk("rest_tie", "Franchised + company-operated vs systemwide", "{rest_fran_tot}+{rest_co}-{rest_sys}", strict=True),
]
comp_rows = []
for s, nm in (("us", "U.S."), ("iom", "International Operated Markets"), ("idl", "International Developmental Licensed Markets"), ("total", "Total Company")):
    comp_rows.append(inp(f"comp_{s}", f"Comparable sales growth: {nm}", S(comps, f"comp_{s}", A), fmt="pct", bold=(s == "total")))
sws_rows = []
for kind, nm in (("rep", "as reported"), ("cc", "excluding currency translation")):
    for s, nn in (("us", "U.S."), ("iom", "International Operated Markets"), ("idl", "International Developmental Licensed Markets"), ("total", "Total Company")):
        sws_rows.append(inp(f"sws_{kind}_{s}", f"Systemwide sales growth, {nm}: {nn}", S(sws, f"sws_{kind}_{s}", A), fmt="pct", bold=(s == "total")))
i6_rows = [
    inp("i6_fran_sales", "Franchised sales ($mm, Item 6 selected data)", S(item6, "i6_fran_sales", A), bold=True,
        note="Item 6 table discontinued after the FY2021 10-K; no tabular source for FY2022-FY2025"),
    inp("i6_price", "Market price at year end ($, Item 6)", S(item6, "i6_price", A), fmt="ps",
        note="Item 6 table discontinued after the FY2021 10-K"),
    inp("i6_total_debt", "Total debt ($mm, Item 6)", S(item6, "i6_total_debt", A)),
]
fm_rows = [
    inp("fm_rents", "Rents", S(fmix, "fm_rents", A), indent=1),
    inp("fm_royalties", "Royalties", S(fmix, "fm_royalties", A), indent=1),
    inp("fm_initial", "Initial fees", S(fmix, "fm_initial", A), indent=1),
    {"id": "fm_total", "label": "Revenues from franchised restaurants", "type": "subtotal", "bold": True, "children": ["fm_rents", "fm_royalties", "fm_initial"]},
    calc("fm_rent_pct", "  Rents % of franchised revenues", "{fm_rents}/{fm_total}", fmt="pct", memo=True),
    calc("fm_roy_pct", "  Royalties % of franchised revenues", "{fm_royalties}/{fm_total}", fmt="pct", memo=True),
    chk("fm_tie", "Franchised revenue composition vs IS (rounding)", "{fm_total}-{IS:rev_franchised}"),
]
sr_rows = [
    inp("sr_shares_rep", "Number of shares repurchased (mm)", S(sret, "sr_shares_rep", A), fmt="num1"),
    inp("sr_shares_out", "Shares outstanding at year end (mm)", S(sret, "sr_shares_out", A)),
    inp("sr_dps", "Dividends declared per share ($)", S(sret, "sr_dps", A), fmt="ps"),
    inp("sr_buyback", "Treasury stock purchases (in shareholders' equity)", S(sret, "sr_buyback", A), indent=1),
    inp("sr_div_paid", "Dividends paid", S(sret, "sr_div_paid", A), indent=1),
    inp("sr_total", "Total returned to shareholders (as reported)", S(sret, "sr_total", A), bold=True, border_top=True),
    chk("sr_tie", "Buybacks + dividends vs total returned (rounding)", "{sr_buyback}+{sr_div_paid}-{sr_total}"),
    chk("sr_tie_cf", "Dividends paid vs cash-flow dividends (rounding)", "{sr_div_paid}+{CF:cf_dividends}"),
]
ds_rows = [
    inp("ds_fixed", "Fixed-rate debt as % of total debt", S(dstat, "ds_fixed", A), fmt="pct"),
    inp("ds_wavg_rate", "Weighted-average annual interest rate of total debt", S(dstat, "ds_wavg_rate", A), fmt="pct"),
    inp("ds_fx_debt", "Foreign currency-denominated debt as % of total debt", S(dstat, "ds_fx_debt", A), fmt="pct"),
    inp("ds_debt_cap", "Total debt as % of total capitalization", S(dstat, "ds_debt_cap", A), fmt="pct"),
    inp("ds_cfo_debt", "Cash provided by operations as % of total debt", S(dstat, "ds_cfo_debt", A), fmt="pct"),
]
OM_SHEET = {"name": "Operating Metrics", "short": "OM", "kind": "statement", "tab_color": "548235", "contents": True,
            "blocks": [{"title": "RESTAURANT COUNT (YEAR END)", "rows": rest_rows},
                       {"title": "COMPARABLE SALES GROWTH (FY2018-FY2025; SEGMENT DEFINITIONS PER FY2020+ 10-KS)", "rows": comp_rows},
                       {"title": "SYSTEMWIDE SALES GROWTH (FY2019-FY2025)", "rows": sws_rows},
                       {"title": "FRANCHISED SALES AND MARKET DATA (ITEM 6, FY2016-FY2021 ONLY)", "rows": i6_rows},
                       {"title": "FRANCHISED REVENUE COMPOSITION", "rows": fm_rows},
                       {"title": "SHAREHOLDER RETURNS (MD&A TABLE)", "rows": sr_rows},
                       {"title": "DEBT STRUCTURE STATISTICS (MD&A TABLE)", "rows": ds_rows}]}

# =============================================================== NOTE SCHEDULES
ppe_rows = [
    inp("ppe_land", "Land", S(ppe, "ppe_land", A), indent=1),
    inp("ppe_bld_owned", "Buildings and improvements on owned land", S(ppe, "ppe_bld_owned", A), indent=1),
    inp("ppe_bld_leased", "Buildings and improvements on leased land", S(ppe, "ppe_bld_leased", A), indent=1),
    inp("ppe_equip", "Equipment, signs and seating", S(ppe, "ppe_equip", A), indent=1),
    inp("ppe_other", "Other", S(ppe, "ppe_other", A), indent=1),
    inp("ppe_cost", "Property and equipment, at cost", S(ppe, "ppe_cost", A), bold=True, border_top=True),
    inp("ppe_accum", "Accumulated depreciation and amortization", S(ppe, "ppe_accum", A), indent=1),
    inp("ppe_net", "Net property and equipment", S(ppe, "ppe_net", A), bold=True, border_top=True),
    chk("ppe_tie_comp", "Components vs cost (rounding)", "{ppe_land}+{ppe_bld_owned}+{ppe_bld_leased}+{ppe_equip}+{ppe_other}-{ppe_cost}"),
    chk("ppe_tie_bs", "Note net PP&E vs balance sheet (rounding)", "{ppe_net}-{BS:net_ppe}"),
]
tax_rows = [
    inp("pti_us", "Income before taxes: U.S.", S(tax, "pti_us", A), indent=1),
    inp("pti_non_us", "Income before taxes: outside the U.S.", S(tax, "pti_non_us", A), indent=1),
    inp("pti_total", "Income before provision for income taxes", S(tax, "pti_total", A), bold=True, border_top=True),
    inp("cur_fed", "Current: U.S. federal", S(tax, "cur_fed", A), indent=1),
    inp("cur_state", "Current: U.S. state", S(tax, "cur_state", A), indent=1),
    inp("cur_foreign", "Current: outside the U.S.", S(tax, "cur_foreign", A), indent=1),
    inp("cur_total", "Current tax provision", S(tax, "cur_total", A), bold=True, border_top=True),
    inp("def_fed", "Deferred: U.S. federal", S(tax, "def_fed", A), indent=1),
    inp("def_state", "Deferred: U.S. state", S(tax, "def_state", A), indent=1),
    inp("def_foreign", "Deferred: outside the U.S.", S(tax, "def_foreign", A), indent=1),
    inp("def_total", "Deferred tax (benefit) provision", S(tax, "def_total", A), bold=True, border_top=True),
    inp("tax_total", "Provision for income taxes", S(tax, "tax_total", A), bold=True, border_top=True),
    calc("tax_rate_us_share", "  U.S. share of pre-tax income", "{pti_us}/{pti_total}", fmt="pct", memo=True),
    chk("tax_tie_pti", "Pre-tax split vs IS (rounding)", "{pti_total}-{IS:pretax_income}"),
    chk("tax_tie_prov", "Tax provision vs IS (rounding)", "{tax_total}-{IS:tax_provision}"),
    chk("tax_tie_comp", "Current + deferred vs total (rounding)", "{cur_total}+{def_total}-{tax_total}"),
]
NS_SHEET = {"name": "Note Schedules", "short": "NS", "kind": "statement", "tab_color": "548235", "contents": True,
            "blocks": [{"title": "PROPERTY AND EQUIPMENT (NOTE)", "rows": ppe_rows},
                       {"title": "INCOME TAXES (NOTE)", "rows": tax_rows}]}

exec(open("build_ext.py", encoding="utf-8").read())

# ================================================================= DERIVED METRICS
def dm(rid, label, expr, fmt="pct", **kw):
    return calc(rid, label, expr, fmt=fmt, memo=True, **kw)


ANN = {"max_label": "FY2025"}
dm_blocks = [
    {"title": "PROFITABILITY", "rows": [
        dm("dm_fran_margin_usd", "Franchised margin ($mm)", "{IS:rev_franchised}-{IS:franchised_occupancy}", fmt="num"),
        dm("dm_fran_margin", "Franchised margin % of franchised revenues", "({IS:rev_franchised}-{IS:franchised_occupancy})/{IS:rev_franchised}"),
        dm("dm_co_margin_usd", "Company-operated margin ($mm)", "{IS:rev_company}-{IS:co_expenses}", fmt="num"),
        dm("dm_co_margin", "Company-operated margin % of company-operated sales", "({IS:rev_company}-{IS:co_expenses})/{IS:rev_company}"),
        dm("dm_sga_pct", "SG&A % of revenues", "{IS:sga_total}/{IS:total_revenues}"),
        dm("dm_op_margin", "Operating margin", "{IS:operating_income}/{IS:total_revenues}"),
        dm("dm_ebitda", "EBITDA ($mm; operating income + cash-flow D&A)", "{IS:operating_income}+{CF:cf_da}", fmt="num"),
        dm("dm_ebitda_margin", "EBITDA margin", "{dm_ebitda}/{IS:total_revenues}"),
        dm("dm_net_margin", "Net margin", "{IS:net_income}/{IS:total_revenues}"),
        dm("dm_eff_tax", "Effective tax rate", "{IS:tax_provision}/{IS:pretax_income}"),
        dm("dm_da_pct", "D&A % of revenues", "{CF:cf_da}/{IS:total_revenues}"),
    ]},
    {"title": "RETURNS AND EFFICIENCY (ANNUAL; AVERAGE BALANCES)", "rows": [
        dm("dm_avg_assets", "Average total assets ($mm)", "({BS:total_assets}+{BS:total_assets@-1})/2", fmt="num", min_label="FY2017", **ANN),
        dm("dm_roa", "Return on average assets", "{IS:net_income}/{dm_avg_assets}", min_label="FY2017", **ANN),
        dm("dm_asset_turn", "Asset turnover", "{IS:total_revenues}/{dm_avg_assets}", fmt="x", min_label="FY2017", **ANN),
        dm("dm_ic", "Invested capital ($mm; total debt + lease liabilities + equity)", "{BS:total_debt}+{BS:total_lease_liab}+{BS:total_equity}", fmt="num",
           note="Lease liabilities are on the balance sheet from FY2019 (ASC 842); FY2016-FY2018 exclude them - not comparable across the FY2018/FY2019 boundary", **ANN),
        dm("dm_nopat", "NOPAT ($mm; operating income x (1 - effective tax rate))", "{IS:operating_income}*(1-{dm_eff_tax})", fmt="num", **ANN),
        dm("dm_roic", "ROIC (NOPAT / average invested capital)", "{dm_nopat}/(({dm_ic}+{dm_ic@-1})/2)", min_label="FY2017", **ANN),
    ]},
    {"title": "LEVERAGE AND COVERAGE (ANNUAL)", "rows": [
        dm("dm_net_debt_ebitda", "Net debt / EBITDA", "{BS:net_debt}/{dm_ebitda}", fmt="x", **ANN),
        dm("dm_nd_lease_ebitda", "Net debt incl. lease liabilities / EBITDA (EBITDA not rent-adjusted)", "{BS:net_debt_leases}/{dm_ebitda}", fmt="x",
           note="Lease liabilities on balance sheet from FY2019 only (ASC 842)", **ANN),
        dm("dm_debt_assets", "Total debt / total assets", "{BS:total_debt}/{BS:total_assets}", **ANN),
        dm("dm_int_cov", "Interest coverage (operating income / interest expense)", "{IS:operating_income}/{IS:interest_expense}", fmt="x", **ANN),
        dm("dm_ebitda_int", "EBITDA / interest expense", "{dm_ebitda}/{IS:interest_expense}", fmt="x", **ANN),
        dm("dm_cfo_debt", "Cash provided by operations / total debt", "{CF:cfo}/{BS:total_debt}", **ANN),
    ]},
    {"title": "LIQUIDITY (PERIOD-END)", "rows": [
        dm("dm_current_ratio", "Current ratio", "{BS:total_current_assets}/{BS:total_current_liabilities}", fmt="x"),
        dm("dm_quick_ratio", "Quick ratio ((cash + receivables) / current liabilities)", "({BS:cash}+{BS:receivables})/{BS:total_current_liabilities}", fmt="x"),
        dm("dm_cash_ratio", "Cash ratio", "{BS:cash}/{BS:total_current_liabilities}", fmt="x"),
    ]},
    {"title": "CASH CONVERSION AND CAPITAL ALLOCATION", "rows": [
        dm("dm_cfo_margin", "CFO margin", "{CF:cfo}/{IS:total_revenues}"),
        dm("dm_cfo_ebitda", "CFO / EBITDA", "{CF:cfo}/{dm_ebitda}", fmt="x"),
        dm("dm_capex_pct", "Capital expenditures % of revenues", "0-{CF:cf_capex}/{IS:total_revenues}"),
        dm("dm_capex_da", "Capital expenditures / D&A", "0-{CF:cf_capex}/{CF:cf_da}", fmt="x"),
        dm("dm_fcf_margin", "FCF margin", "{CF:fcf}/{IS:total_revenues}"),
        dm("dm_fcf_conv", "FCF / net income", "{CF:fcf}/{IS:net_income}", fmt="x"),
        dm("dm_div_payout", "Dividends paid % of net income", "(0-{CF:cf_dividends})/{IS:net_income}"),
        dm("dm_div_fcf", "Dividends paid % of FCF", "(0-{CF:cf_dividends})/{CF:fcf}"),
        dm("dm_bb_fcf", "Treasury stock purchases % of FCF", "(0-{CF:cf_treasury_purchases})/{CF:fcf}"),
        dm("dm_total_ret_fcf", "Dividends + buybacks % of FCF", "{CF:shareholder_returns_cf}/{CF:fcf}"),
    ]},
    {"title": "SYSTEMWIDE AND FRANCHISE ECONOMICS", "rows": [
        dm("dm_sws", "Systemwide sales ($mm; franchised sales + Company-operated sales)", "{OM:x_sws}", fmt="num", **ANN),
        dm("dm_sws_g", "Systemwide sales growth (reported currency)", "{OM:x_sws}/{OM:x_sws@-1}-1", min_label="FY2017", **ANN),
        dm("dm_take", "Franchised revenues % of franchised sales", "{IS:rev_franchised}/{OM:x_fs_tot}", **ANN),
        dm("dm_fran_margin_fs", "Franchised margins % of franchised sales", "({IS:rev_franchised}-{IS:franchised_occupancy})/{OM:x_fs_tot}", **ANN),
        dm("dm_sga_sws", "SG&A % of Systemwide sales", "{IS:sga_total}/{OM:x_sws}", **ANN),
        dm("dm_oi_sws", "Operating income % of Systemwide sales", "{IS:operating_income}/{OM:x_sws}", **ANN),
        dm("dm_rev_per_rest", "Total revenues per average systemwide restaurant ($mm)", "{IS:total_revenues}/(({OM:rest_sys}+{OM:rest_sys@-1})/2)", fmt="ps", min_label="FY2017", **ANN),
        dm("dm_int_rate", "Interest expense / average total debt", "{IS:interest_expense}/(({BS:total_debt}+{BS:total_debt@-1})/2)", min_label="FY2017", **ANN),
        dm("dm_capex_per_unit", "Capital expenditures per net restaurant addition ($mm; net additions can be small or negative)", "(0-{CF:cf_capex})/{OM:x_net_add}", fmt="ps", min_label="FY2018", **ANN),
    ]},
    {"title": "EARNINGS QUALITY", "rows": [
        dm("dm_cfo_ni", "CFO / net income", "{CF:cfo}/{IS:net_income}", fmt="x"),
        dm("dm_accrual", "Accrual ratio ((net income - CFO) / average assets)", "({IS:net_income}-{CF:cfo})/{dm_avg_assets}", min_label="FY2017", **ANN),
    ]},
    {"title": "GROWTH", "rows": [
        {"id": "dm_l_rev", "label": "Total revenues", "type": "link", "ref": "IS:total_revenues"},
        yoy("dm_g_rev", "dm_l_rev"),
        {"id": "dm_l_oi", "label": "Operating income", "type": "link", "ref": "IS:operating_income"},
        yoy("dm_g_oi", "dm_l_oi"),
        {"id": "dm_l_ni", "label": "Net income", "type": "link", "ref": "IS:net_income"},
        yoy("dm_g_ni", "dm_l_ni"),
        {"id": "dm_l_eps", "label": "Diluted EPS ($)", "type": "link", "ref": "IS:eps_diluted", "fmt": "ps"},
        yoy("dm_g_eps", "dm_l_eps"),
        {"id": "dm_l_cfo", "label": "Cash provided by operations", "type": "link", "ref": "CF:cfo"},
        yoy("dm_g_cfo", "dm_l_cfo"),
        {"id": "dm_l_fcf", "label": "Free cash flow", "type": "link", "ref": "CF:fcf"},
        yoy("dm_g_fcf", "dm_l_fcf"),
    ]},
]
DM_SHEET = {"name": "Derived Metrics", "short": "DM", "kind": "statement", "tab_color": "7030A0", "contents": True, "blocks": dm_blocks}
# note: ROE and debt/equity are omitted by design - shareholders' equity is negative in every period (deficit), so the ratios are not meaningful.

# current segment structure starts FY2017 (blocks 1-7); block 8 keeps FY2016-FY2018
for _b in SEG_SHEET["blocks"][:-1]:
    for _r in _b["rows"]:
        if _r.get("type") != "spacer":
            _r.setdefault("min_label", "FY2017")

# annual-only sheets: keep quarterly columns out of their row spans
for _sh in (SEG_SHEET, OM_SHEET, NS_SHEET):
    for _b in _sh["blocks"]:
        for _r in _b["rows"]:
            if _r.get("type") != "spacer" and "max_label" not in _r:
                _r["max_label"] = "FY2025"

# ============================================================== COVER / SOURCES
src_rows = []
for line in open("../../data/source-index.md", encoding="utf-8"):
    if re.match(r"\| S\d{3} \|", line):
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        src_rows.append(c)

cover_table = [
    [{"text": "McDonald's Corporation - Financial Model Workbook", "bold": True}],
    [],
    ["Ticker / exchange", "MCD / NYSE"],
    ["SEC registrant / CIK", "MCDONALDS CORP / 0000063908"],
    ["Reporting framework", "US GAAP (per SEC Form 10-K / 10-Q); consolidated"],
    ["Fiscal year end", "December 31"],
    ["Currency and units", "USD millions except per-share data and restaurant counts"],
    ["Annual window", "FY2016-FY2025 (10 Form 10-K filings; latest-filing-wins precedence for restated periods)"],
    ["Quarterly window", "3Q2024-2Q2026 (6 Form 10-Q filings: 3Q24, 1Q25, 2Q25, 3Q25, 1Q26, 2Q26)"],
    ["Latest filing covered", "Form 10-Q for the quarter ended 2026-06-30 (filed 2026-08-07); 3Q2026 10-Q not yet filed at 2026-10-08"],
    ["Research as-of date", "2026-10-08"],
    [],
    [{"text": "Colour legend", "bold": True}],
    ["Blue", "Hard-coded value copied from a filed statement table"],
    ["Black", "Formula / analyst calculation"],
    ["Green", "Cross-sheet link"],
    ["Grey italic", "Memo / ratio rows"],
    ["Amber check rows", "Rounding tie-outs of as-filed integers (+/-2 expected); red = strict tie-out failure"],
    [],
    [{"text": "Sheet directory", "bold": True}],
    ["Income Statement (IS)", "As-reported income statement, per-share data, tie-outs"],
    ["Balance Sheet (BS)", "As-reported balance sheet, tie-outs, debt and lease summary"],
    ["Cash Flow (CF)", "As-reported cash flow, cash walk, free cash flow analytics"],
    ["Segments (SEG)", "Reportable-segment revenue, operating income, assets, capex, D&A; revenue by type; restaurant margins by segment; SG&A by segment and incentive compensation; superseded FY2016-FY2018 structure"],
    ["Operating Metrics (OM)", "Restaurant counts (type and segment), net additions, comparable sales and guest counts, systemwide sales growth, franchised sales, franchised revenue mix, currency translation impact, non-GAAP reconciliations, capex by purpose, shareholder returns, debt statistics"],
    ["Note Schedules (NS)", "Property and equipment, income taxes, other operating and nonoperating components, goodwill by segment, debt by currency and maturity, rent and lease commitments, franchise-arrangement assets, advertising, share-based compensation, text-only operating facts"],
    ["Year-End Schedules", "Debt, lease and minimum-rent maturity ladders (Dec 2025 and Dec 2024), restructuring reserve roll-forward, equity-method investees"],
    ["Outlook & Text KPIs", "Verbatim management outlook statements FY2016-FY2025 10-Ks (FORWARD-LOOKING, not realised) and operating-KPI sentences FY2021-FY2025 with line locators"],
    ["Derived Metrics (DM)", "Margins, returns, leverage, liquidity, cash conversion, growth (formulas on the statements)"],
    ["Sources", "Filing register, extraction method, comparability and restatement notes"],
    [],
    [{"text": "Comparability and method notes", "bold": True}],
    ["4Q columns marked *", "Income statement and cash flow 4Q = FY (10-K) less nine-month YTD (10-Q): analyst derivation, not a filed quarterly statement. Balance-sheet 4Q columns are the filed 10-K year-end balances. EPS / share counts are not derived."],
    ["Revenue recast", "FY2018-FY2019 were recast in the FY2020 10-K (new 'Other revenues' and 'Other restaurant expenses' lines; revenue and cost both higher, operating income unchanged). FY2016-FY2017 are as originally reported and are not comparable at line level."],
    ["Segment structure", "Current segments (U.S. / International Operated Markets / International Developmental Licensed Markets & Corporate) available from FY2017 (FY2019 10-K recast). FY2016 exists only under the superseded structure."],
    ["Negative equity", "Shareholders' equity is a deficit in every period; ROE and debt/equity are not meaningful and are omitted."],
    ["Precision", "FY2016-FY2019 10-K tables show one decimal; FY2018 onward as later recast are whole millions. Tie-outs therefore show +/-1-2 rounding in recent years."],
    ["Systemwide sales", "The company does not tabulate Systemwide sales in dollars; the OM row reconstructs it as franchised sales + Company-owned and operated sales (analyst calculation). Cross-check: 2025 SG&A / reconstructed Systemwide sales = 2.2%, equal to the company's own 'about 2.2% of Systemwide sales' statement."],
    ["Text-only facts", "Rows built from MD&A / note prose (advertising, variable rent, franchise-arrangement property, debt fair value, segment franchised %, employees, delivery / drive thru) are company statements rounded as printed; they are not audited tables."],
    ["Guidance", "The Outlook & Text KPIs sheet quotes management guidance and targets verbatim. They are forward-looking company statements (SEC filing text), not realised data."],
    ["Not loaded", "Official-site material and earnings-call transcripts (out of scope); 1Q/2Q 2024 quarterly flows (prior-year comparatives in the 2025 10-Qs); deferred-tax components, effective-tax-rate reconciliation, unrecognised tax benefits, derivative / fair-value tables, option and RSU activity, monthly repurchase table and the 5-year shareholder-return index (financial-reporting detail outside the operating scope of this pass); FY2016-FY2018 old-structure MD&A tables other than those shown in the superseded-structure block; 10-Q MD&A KPI tables."],
]

sources_table = [
    [{"text": "Source ID", "header": True}, {"text": "Form / period", "header": True}, {"text": "Period end", "header": True},
     {"text": "SEC URL (accession folder)", "header": True}, {"text": "Local path", "header": True}, {"text": "Raw source.html SHA-256", "header": True},
     {"text": "Notes", "header": True}],
]
for c in src_rows:
    sources_table.append([c[0], f"{c[1]} - {c[2]}", c[3], c[5], c[6], c[7], c[10][:140] if len(c) > 10 else ""])
sources_table += [
    [],
    [{"text": "Extraction method", "bold": True}],
    ["Collector", "collect_tables.py over the 16 raw source.html files -> tables.json (858 tables)"],
    ["Parser", "mcd_extract.py / mcd_extract2.py (statements, segments, KPIs) and mcd_extract3.py / mcd_extract4.py (MD&A operating tables, note schedules, prose series, outlook text) map rows by caption and compact SEC split-cell negatives; no value is typed by hand"],
    ["Precedence", "For a period reported in several filings the latest filing is used; superseded differences > 1.0 are listed in restatement_log.json"],
    ["Tier discipline", "Tier 2 per company-research-to-excel: SEC filing HTML only; no press releases, third-party data or research reports"],
    [],
    [{"text": "Restatement / reclassification log (differences > 1.0 between filings)", "bold": True}],
]
rlog = []
for k in ("IS", "BS", "CF"):
    for rid, per in ahist[k].items():
        for p, lst in per.items():
            if p not in A:
                continue
            vals = [v for _, v, _ in lst]
            if max(vals) - min(vals) > 1.0:
                rlog.append({"statement": k, "row": rid, "period": p, "by_filing_fy": [(fy, v, t) for fy, v, t in lst]})
json.dump(rlog, open("restatement_log.json", "w"), indent=1)
for e in rlog:
    sources_table.append([f"{e['statement']}:{e['row']} {e['period']}",
                          "; ".join(f"10-K FY{fy}: {v:,.1f}" for fy, v, _ in e["by_filing_fy"]),
                          "latest filing used"])

model = {
    "company": {"name": "McDonald's Corporation", "ticker": "MCD", "currency": "USD", "units": "$ in millions except per-share data",
                "reporting_framework": "US GAAP", "fiscal_year_end": "December 31", "consolidation_scope": "Consolidated",
                "as_of_date": "2026-06-30", "model_date": "2026-10-08"},
    "periods": {"annual": [{"label": a, "end": f"{a[2:]}-12-31"} for a in A], "scrap_cols": 1,
                "quarterly": [{"label": q, "end": QEND[q]} for q in Q]},
    "sheets": [
        {"name": "Cover", "kind": "table", "col_widths": [30, 120], "tab_color": "1F4E79", "table": cover_table},
        IS_SHEET, BS_SHEET, CF_SHEET, SEG_SHEET, OM_SHEET, NS_SHEET, SCHED_SHEET, OUTLOOK_SHEET, DM_SHEET,
        {"name": "Sources", "kind": "table", "col_widths": [26, 40, 12, 70, 60, 66, 60], "tab_color": "1F4E79", "table": sources_table},
    ],
}
json.dump(model, open("model.json", "w"), indent=1, ensure_ascii=False)
print("model.json written; restatement entries:", len(rlog))
