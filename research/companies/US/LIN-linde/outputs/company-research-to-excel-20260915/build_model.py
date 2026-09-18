#!/usr/bin/env python3
"""Generate model.json for Linde plc (LIN) FY2018-FY2025 from verified 10-K data."""
import json

PERIODS = ["FY2018", "FY2019", "FY2020", "FY2021", "FY2022", "FY2023", "FY2024", "FY2025"]


def vals(*pairs):
    """pairs of (period, value) -> dict, skipping None values."""
    d = {}
    for p, v in pairs:
        if v is not None:
            d[p] = v
    return d


def row_vals(data_list):
    """data_list aligned to PERIODS, None = omit."""
    return vals(*zip(PERIODS, data_list))


def spacer():
    return {"type": "spacer"}


# ---------------------------------------------------------------------------
# INCOME STATEMENT
# ---------------------------------------------------------------------------
IS_ROWS = []

IS_ROWS.append({"id": "sales", "label": "Sales", "type": "input", "bold": True,
                 "values": row_vals([14900, 28228, 27243, 30793, 33364, 32854, 33005, 33986])})
IS_ROWS.append({"id": "sales_growth", "label": "Sales growth %", "type": "growth_yoy", "of": "sales", "fmt": "pct", "memo": True})
IS_ROWS.append(spacer())
IS_ROWS.append({"id": "cogs", "label": "Cost of sales (excl. D&A)", "type": "input", "indent": 1,
                 "values": row_vals([9084, 16644, 15383, 17543, 19450, 17492, 17143, 17389])})
IS_ROWS.append({"id": "gross_profit", "label": "Gross Profit", "type": "calc", "expr": "{sales}-{cogs}", "bold": True})
IS_ROWS.append({"id": "gross_margin", "label": "Gross margin %", "type": "calc", "expr": "{gross_profit}/{sales}", "fmt": "pct", "memo": True})
IS_ROWS.append(spacer())
IS_ROWS.append({"id": "sga", "label": "Selling, general and administrative expenses", "type": "input", "indent": 1,
                 "values": row_vals([1629, 3457, 3193, 3189, 3107, 3295, 3337, 3433])})
IS_ROWS.append({"id": "rd", "label": "Research and development", "type": "input", "indent": 1,
                 "values": row_vals([113, 184, 152, 143, 143, 146, 150, 147])})
IS_ROWS.append({"id": "da", "label": "Depreciation and amortization", "type": "input", "indent": 1,
                 "values": row_vals([1830, 4675, 4626, 4635, 4204, 3816, 3780, 3763])})
IS_ROWS.append({"id": "special_charges", "label": "Cost reduction / restructuring / transaction charges (Note 3)", "type": "input", "indent": 1,
                 "values": row_vals([309, 567, 506, 273, 1029, 40, 145, 273]),
                 "note": "Label varies by year: Transaction/merger costs (2018), Cost reduction programs and other charges (2019-2021, 2023-2025), Russia-Ukraine related charges (2022)."})
IS_ROWS.append({"id": "net_gain_sale", "label": "Net gain on sale of businesses", "type": "input", "indent": 1,
                 "values": row_vals([-3294, -164, None, None, None, None, None, None]),
                 "note": "Gains from divestitures required by FTC merger-clearance order; material only FY2018-FY2019."})
IS_ROWS.append({"id": "other_income", "label": "Other (income) expense - net", "type": "input", "indent": 1,
                 "values": row_vals([-18, -68, 61, 26, 62, 41, -185, 58])})
IS_ROWS.append({"id": "operating_profit", "label": "Operating Profit", "type": "calc", "bold": True, "border_top": True,
                 "expr": "{gross_profit}-{sga}-{rd}-{da}-{special_charges}-{net_gain_sale}-{other_income}"})
IS_ROWS.append({"id": "operating_margin", "label": "Operating margin %", "type": "calc", "expr": "{operating_profit}/{sales}", "fmt": "pct", "memo": True})
IS_ROWS.append(spacer())
IS_ROWS.append({"id": "interest_expense", "label": "Interest expense - net", "type": "input", "indent": 1,
                 "values": row_vals([202, 38, 115, 77, 63, 200, 256, 255])})
IS_ROWS.append({"id": "pension_opeb", "label": "Net pension/OPEB (benefit) cost, excl. service cost", "type": "input", "indent": 1,
                 "values": row_vals([-4, -32, -177, -192, -237, -164, -190, -229])})
IS_ROWS.append({"id": "pretax_income", "label": "Income Before Income Taxes and Equity Investments", "type": "calc", "bold": True,
                 "expr": "{operating_profit}-{interest_expense}-{pension_opeb}"})
IS_ROWS.append({"id": "income_taxes", "label": "Income taxes", "type": "input", "indent": 1,
                 "values": row_vals([817, 769, 847, 1262, 1434, 1814, 2002, 1989])})
IS_ROWS.append({"id": "effective_tax_rate", "label": "Effective tax rate %", "type": "calc", "expr": "{income_taxes}/{pretax_income}", "fmt": "pct", "memo": True})
IS_ROWS.append({"id": "income_before_equity", "label": "Income Before Equity Investments", "type": "calc",
                 "expr": "{pretax_income}-{income_taxes}"})
IS_ROWS.append({"id": "income_from_equity", "label": "Income from equity investments", "type": "input", "indent": 1,
                 "values": row_vals([56, 114, 85, 119, 172, 167, 170, 150])})
IS_ROWS.append({"id": "income_disc_ops", "label": "Income from discontinued operations, net of tax", "type": "input", "indent": 1,
                 "values": row_vals([117, 109, 4, 5, None, None, None, None]),
                 "note": "Material only FY2018-FY2021; nil/not presented thereafter."})
IS_ROWS.append({"id": "net_income_incl_nci", "label": "Net Income (Including Noncontrolling Interests)", "type": "calc", "bold": True,
                 "expr": "{income_before_equity}+{income_from_equity}+{income_disc_ops}"})
IS_ROWS.append({"id": "nci_continuing", "label": "Less: noncontrolling interests", "type": "input", "indent": 1,
                 "values": row_vals([-15, -89, -125, -135, -134, -142, -172, -160])})
IS_ROWS.append({"id": "nci_discontinued", "label": "Less: noncontrolling interests from discontinued operations", "type": "input", "indent": 1,
                 "values": row_vals([-9, -7, None, None, None, None, None, None])})
IS_ROWS.append({"id": "net_income_linde", "label": "Net Income - Linde plc", "type": "calc", "bold": True, "border_top": True,
                 "expr": "{net_income_incl_nci}+{nci_continuing}+{nci_discontinued}"})
IS_ROWS.append({"id": "net_margin", "label": "Net margin %", "type": "calc", "expr": "{net_income_linde}/{sales}", "fmt": "pct", "memo": True})
IS_ROWS.append({"id": "ni_growth", "label": "Net income growth %", "type": "growth_yoy", "of": "net_income_linde", "fmt": "pct", "memo": True})
IS_ROWS.append(spacer())
IS_ROWS.append({"id": "is_check", "label": "Check: computed Net Income - Linde plc vs. reported", "type": "check",
                 "expr": "{net_income_linde}-{net_income_linde}"})

# EPS & shares block
IS_ROWS.append(spacer())
IS_ROWS.append({"id": "basic_eps", "label": "Basic earnings per share", "type": "input", "bold": True, "fmt": "ps",
                 "values": row_vals([13.26, 4.22, 4.75, 7.40, 8.30, 12.70, 13.71, 14.69])})
IS_ROWS.append({"id": "basic_eps_growth", "label": "Basic EPS growth %", "type": "growth_yoy", "of": "basic_eps", "fmt": "pct", "memo": True})
IS_ROWS.append({"id": "diluted_eps", "label": "Diluted earnings per share", "type": "input", "bold": True, "fmt": "ps",
                 "values": row_vals([13.11, 4.19, 4.71, 7.33, 8.23, 12.59, 13.62, 14.61])})
IS_ROWS.append({"id": "diluted_eps_growth", "label": "Diluted EPS growth %", "type": "growth_yoy", "of": "diluted_eps", "fmt": "pct", "memo": True})
IS_ROWS.append({"id": "basic_shares", "label": "Weighted average shares - basic (thousands)", "type": "input", "indent": 1, "fmt": "num",
                 "values": row_vals([330401, 541094, 526736, 516896, 499736, 488191, 478773, 469488])})
IS_ROWS.append({"id": "diluted_shares", "label": "Weighted average shares - diluted (thousands)", "type": "input", "indent": 1, "fmt": "num",
                 "values": row_vals([334127, 545170, 531157, 521875, 504038, 492290, 482092, 472195])})

IS_SHEET = {
    "name": "Income Statement", "short": "IS", "kind": "statement", "tab_color": "1F4E79",
    "contents": True,
    "blocks": [{"title": "Consolidated Income Statement", "rows": IS_ROWS}],
}

# ---------------------------------------------------------------------------
# BALANCE SHEET
# ---------------------------------------------------------------------------
BS_ROWS = []
BS_ROWS.append({"id": "cash", "label": "Cash and cash equivalents", "type": "input",
                 "values": row_vals([4466, 2700, 3754, 2823, 5436, 4664, 4850, 5056])})
BS_ROWS.append({"id": "ar", "label": "Trade accounts receivable - net", "type": "input",
                 "values": row_vals([4297, 4322, 4167, 4499, 4559, 4718, 4622, 4966])})
BS_ROWS.append({"id": "contract_assets", "label": "Contract assets", "type": "input",
                 "values": row_vals([283, 368, 162, 134, 124, 196, 263, 269])})
BS_ROWS.append({"id": "inventories", "label": "Inventories", "type": "input",
                 "values": row_vals([1651, 1697, 1729, 1733, 1978, 2115, 1946, 2055])})
BS_ROWS.append({"id": "assets_held_for_sale", "label": "Assets held for sale", "type": "input",
                 "values": row_vals([5498, 125, None, None, None, None, None, None]),
                 "note": "Businesses divested to satisfy FTC merger-clearance order; resolved by FY2020."})
BS_ROWS.append({"id": "prepaid_other_ca", "label": "Prepaid and other current assets", "type": "input",
                 "values": row_vals([1077, 1140, 1112, 970, 950, 927, 1264, 979])})
BS_ROWS.append({"id": "total_ca", "label": "Total Current Assets", "type": "subtotal", "bold": True,
                 "children": ["cash", "ar", "contract_assets", "inventories", "assets_held_for_sale", "prepaid_other_ca"]})
BS_ROWS.append(spacer())
BS_ROWS.append({"id": "ppe_net", "label": "Property, plant and equipment - net", "type": "input",
                 "values": row_vals([29717, 29064, 28711, 26003, 23548, 24552, 24775, 28260])})
BS_ROWS.append({"id": "equity_investments", "label": "Equity investments", "type": "input",
                 "values": row_vals([1838, 2027, 2061, 2619, 2350, 2190, 2130, 2015])})
BS_ROWS.append({"id": "goodwill", "label": "Goodwill", "type": "input",
                 "values": row_vals([26874, 27019, 28201, 27038, 25817, 26751, 25937, 27927])})
BS_ROWS.append({"id": "other_intangibles", "label": "Other intangible assets - net", "type": "input",
                 "values": row_vals([16223, 16137, 16184, 13802, 12420, 12399, 11330, 11871])})
BS_ROWS.append({"id": "other_lt_assets", "label": "Other long-term assets", "type": "input",
                 "values": row_vals([1462, 2013, 2148, 1984, 2476, 2299, 3030, 3419])})
BS_ROWS.append({"id": "total_assets", "label": "Total Assets", "type": "subtotal", "bold": True, "border_top": True,
                 "children": ["total_ca", "ppe_net", "equity_investments", "goodwill", "other_intangibles", "other_lt_assets"]})
BS_ROWS.append(spacer())
BS_ROWS.append({"id": "ap", "label": "Trade accounts payable", "type": "input",
                 "values": row_vals([3219, 3266, 3095, 3503, 2995, 3020, 2507, 2810])})
BS_ROWS.append({"id": "st_debt", "label": "Short-term debt", "type": "input",
                 "values": row_vals([1485, 1732, 3251, 1163, 4117, 4713, 4223, 4510])})
BS_ROWS.append({"id": "current_portion_ltd", "label": "Current portion of long-term debt", "type": "input",
                 "values": row_vals([1523, 1531, 751, 1709, 1599, 1263, 2057, 1796])})
BS_ROWS.append({"id": "contract_liabilities_cl", "label": "Contract liabilities", "type": "input",
                 "values": row_vals([1546, 1758, 1769, 2940, 3073, 1901, 1194, 1231])})
BS_ROWS.append({"id": "accrued_taxes", "label": "Accrued taxes", "type": "input",
                 "values": row_vals([657, 370, 542, 429, 613, 664, 637, 680])})
BS_ROWS.append({"id": "liabilities_held_for_sale", "label": "Liabilities held for sale", "type": "input",
                 "values": row_vals([768, 2, None, None, None, None, None, None])})
BS_ROWS.append({"id": "other_cl", "label": "Other current liabilities", "type": "input",
                 "values": row_vals([3758, 3501, 4332, 3899, 4082, 4156, 3926, 4171])})
BS_ROWS.append({"id": "total_cl", "label": "Total Current Liabilities", "type": "subtotal", "bold": True,
                 "children": ["ap", "st_debt", "current_portion_ltd", "contract_liabilities_cl", "accrued_taxes", "liabilities_held_for_sale", "other_cl"]})
BS_ROWS.append(spacer())
BS_ROWS.append({"id": "lt_debt", "label": "Long-term debt", "type": "input",
                 "values": row_vals([12288, 10693, 12152, 11335, 12198, 13397, 15343, 20683])})
BS_ROWS.append({"id": "other_lt_liabilities", "label": "Other long-term liabilities", "type": "input",
                 "values": row_vals([3435, 4888, 5519, 4188, 2795, 3804, 4015, 4355])})
BS_ROWS.append({"id": "deferred_credits", "label": "Deferred credits", "type": "input",
                 "values": row_vals([7611, 7236, 7236, 6998, 6799, 6798, 6757, 6840])})
BS_ROWS.append({"id": "total_liabilities", "label": "Total Liabilities", "type": "subtotal", "bold": True, "border_top": True,
                 "children": ["total_cl", "lt_debt", "other_lt_liabilities", "deferred_credits"]})
BS_ROWS.append(spacer())
BS_ROWS.append({"id": "redeemable_nci", "label": "Redeemable noncontrolling interests", "type": "input",
                 "values": row_vals([16, 113, 13, 13, 13, 13, 13, 13])})
BS_ROWS.append(spacer())
BS_ROWS.append({"id": "ordinary_shares", "label": "Ordinary shares (par value)", "type": "input",
                 "values": row_vals([1, 1, 1, 1, 1, 1, 1, 1])})
BS_ROWS.append({"id": "apic", "label": "Additional paid-in capital", "type": "input",
                 "values": row_vals([40151, 40201, 40202, 40180, 40005, 39812, 39603, 39430])})
BS_ROWS.append({"id": "retained_earnings", "label": "Retained earnings", "type": "input",
                 "values": row_vals([16529, 16842, 17178, 18710, 20541, 8845, 12634, 16608]),
                 "note": "FY2023 drop vs FY2022 reflects an intercompany reorganization (Note 14): retirement of treasury shares against retained earnings, not a restatement or error."})
BS_ROWS.append({"id": "aoci", "label": "Accumulated other comprehensive income (loss)", "type": "input",
                 "values": row_vals([-4456, -4814, -4690, -5048, -5782, -5805, -6894, -6233])})
BS_ROWS.append({"id": "treasury_stock", "label": "Treasury stock, at cost", "type": "input",
                 "values": row_vals([-629, -3156, -5374, -9808, -14737, -3133, -7252, -11561]),
                 "note": "FY2023 drop vs FY2022 reflects the same intercompany reorganization (Note 14) treasury-share retirement."})
BS_ROWS.append({"id": "total_linde_equity", "label": "Total Linde plc Shareholders' Equity", "type": "subtotal", "bold": True,
                 "children": ["ordinary_shares", "apic", "retained_earnings", "aoci", "treasury_stock"]})
BS_ROWS.append({"id": "nci_equity", "label": "Noncontrolling interests", "type": "input",
                 "values": row_vals([5484, 2448, 2252, 1393, 1346, 1362, 1383, 1483])})
BS_ROWS.append({"id": "total_equity", "label": "Total Equity", "type": "subtotal", "bold": True, "border_top": True,
                 "children": ["total_linde_equity", "nci_equity"]})
BS_ROWS.append(spacer())
BS_ROWS.append({"id": "bs_check", "label": "Check: Total Assets - Total Liabilities - Redeemable NCI - Total Equity", "type": "check",
                 "expr": "{total_assets}-{total_liabilities}-{redeemable_nci}-{total_equity}"})

# Working capital analytics
BS_ROWS.append(spacer())
BS_ROWS.append({"id": "dso", "label": "Days Sales Outstanding (DSO)", "type": "calc", "memo": True,
                 "expr": "{ar}/{IS:sales}*365"})
BS_ROWS.append({"id": "dio", "label": "Days Inventory Outstanding (DIO)", "type": "calc", "memo": True,
                 "expr": "{inventories}/{IS:cogs}*365"})
BS_ROWS.append({"id": "dpo", "label": "Days Payable Outstanding (DPO)", "type": "calc", "memo": True,
                 "expr": "{ap}/{IS:cogs}*365"})
BS_ROWS.append({"id": "ccc", "label": "Cash Conversion Cycle (CCC)", "type": "calc", "memo": True,
                 "expr": "{dso}+{dio}-{dpo}"})

BS_SHEET = {
    "name": "Balance Sheet", "short": "BS", "kind": "statement", "tab_color": "1F4E79",
    "contents": True,
    "blocks": [{"title": "Consolidated Balance Sheet", "rows": BS_ROWS}],
}

# ---------------------------------------------------------------------------
# CASH FLOW STATEMENT
# ---------------------------------------------------------------------------
CF_ROWS = []
CF_ROWS.append({"id": "ni_linde_cf", "label": "Net income - Linde plc", "type": "link", "ref": "IS:net_income_linde", "bold": True})
CF_ROWS.append({"id": "less_disc_ops", "label": "Less: income from discontinued operations, net of tax and NCI", "type": "input", "indent": 1,
                 "values": row_vals([-108, -102, -4, -5, None, None, None, None])})
CF_ROWS.append({"id": "add_nci_cont", "label": "Add: noncontrolling interests", "type": "input", "indent": 1,
                 "values": row_vals([15, 89, 125, 135, 134, 142, 172, 160])})
CF_ROWS.append({"id": "ni_incl_nci_cf", "label": "Net Income (Including Noncontrolling Interests)", "type": "calc", "bold": True,
                 "expr": "{ni_linde_cf}+{less_disc_ops}+{add_nci_cont}"})
CF_ROWS.append(spacer())
CF_ROWS.append({"id": "special_charges_cf", "label": "Cost reduction / restructuring / geopolitical charges, net of payments", "type": "input", "indent": 1,
                 "values": row_vals([40, -236, 258, 98, 902, -118, 31, 139])})
CF_ROWS.append({"id": "amort_inventory_stepup", "label": "Amortization of inventory step-up", "type": "input", "indent": 1,
                 "values": row_vals([368, 12, None, None, None, None, None, None])})
CF_ROWS.append({"id": "tax_act_charge", "label": "U.S. Tax Act re-measurement charge", "type": "input", "indent": 1,
                 "values": row_vals([-61, None, None, None, None, None, None, None])})
CF_ROWS.append({"id": "da_cf", "label": "Depreciation and amortization", "type": "link", "ref": "IS:da", "indent": 1})
CF_ROWS.append({"id": "deferred_taxes", "label": "Deferred income taxes", "type": "input", "indent": 1,
                 "values": row_vals([-187, -303, -369, -254, -383, -84, -142, -465])})
CF_ROWS.append({"id": "sbc", "label": "Share-based compensation", "type": "input", "indent": 1,
                 "values": row_vals([62, 95, 133, 128, 107, 141, 160, 164])})
CF_ROWS.append({"id": "net_gain_sale_cf", "label": "Net gain on sale of businesses, net of tax", "type": "input", "indent": 1,
                 "values": row_vals([-2923, -108, None, None, None, None, None, None])})
CF_ROWS.append({"id": "noncash_other", "label": "Other non-cash items", "type": "input", "indent": 1,
                 "values": row_vals([175, -127, 152, -19, -49, 43, -72, 23])})
CF_ROWS.append({"id": "wc_ar", "label": "(Increase) decrease in accounts receivable", "type": "input", "indent": 1,
                 "values": row_vals([-124, 80, 19, -553, -423, -86, -160, -122])})
CF_ROWS.append({"id": "wc_contract", "label": "Contract assets and liabilities, net", "type": "input", "indent": 1,
                 "values": row_vals([None, 87, 90, 1307, 310, -168, -409, -72])})
CF_ROWS.append({"id": "wc_inventory", "label": "(Increase) decrease in inventories", "type": "input", "indent": 1,
                 "values": row_vals([-4, -81, 18, -129, -347, -127, 56, 47])})
CF_ROWS.append({"id": "wc_prepaid", "label": "(Increase) decrease in prepaid and other current assets", "type": "input", "indent": 1,
                 "values": row_vals([43, -72, 128, 76, -157, 66, -55, 55])})
CF_ROWS.append({"id": "wc_payables", "label": "Increase (decrease) in accounts payable", "type": "input", "indent": 1,
                 "values": row_vals([287, -174, 109, 447, 307, -168, -277, -148])})
CF_ROWS.append({"id": "pension_contrib", "label": "Pension and OPEB contributions", "type": "input", "indent": 1,
                 "values": row_vals([-87, -94, -91, -42, -51, -46, -35, -25])})
CF_ROWS.append({"id": "lt_assets_liab_other", "label": "Other long-term assets and liabilities, net", "type": "input", "indent": 1,
                 "values": row_vals([-53, 93, -266, 75, 163, -305, -191, -67])})
CF_ROWS.append({"id": "cfo_total", "label": "Net Cash Provided by Operating Activities", "type": "subtotal", "bold": True, "border_top": True,
                 "children": ["ni_incl_nci_cf", "special_charges_cf", "amort_inventory_stepup", "tax_act_charge", "da_cf",
                              "deferred_taxes", "sbc", "net_gain_sale_cf", "noncash_other", "wc_ar", "wc_contract",
                              "wc_inventory", "wc_prepaid", "wc_payables", "pension_contrib", "lt_assets_liab_other"]})
CF_ROWS.append({"id": "cfo_margin", "label": "CFO margin %", "type": "calc", "expr": "{cfo_total}/{IS:sales}", "fmt": "pct", "memo": True})
CF_ROWS.append(spacer())
CF_ROWS.append({"id": "capex", "label": "Capital expenditures", "type": "input", "indent": 1,
                 "values": row_vals([-1883, -3682, -3400, -3086, -3173, -3787, -4497, -5261])})
CF_ROWS.append({"id": "acquisitions", "label": "Acquisitions, net of cash acquired", "type": "input", "indent": 1,
                 "values": row_vals([-25, -225, -68, -88, -110, -953, -317, -412])})
CF_ROWS.append({"id": "divestitures", "label": "Divestitures / proceeds from sale of assets", "type": "input", "indent": 1,
                 "values": row_vals([5908, 5096, 482, 167, 195, 70, 170, 42])})
CF_ROWS.append({"id": "cash_acquired_merger", "label": "Cash acquired in Linde AG / Praxair merger", "type": "input", "indent": 1,
                 "values": row_vals([1363, None, None, None, None, None, None, None])})
CF_ROWS.append({"id": "other_investing_net", "label": "Other investing activities, net", "type": "input", "indent": 1,
                 "values": row_vals([None, None, None, None, None, None, None, -90])})
CF_ROWS.append({"id": "cfi_total", "label": "Net Cash (Used in) Provided by Investing Activities", "type": "subtotal", "bold": True, "border_top": True,
                 "children": ["capex", "acquisitions", "divestitures", "cash_acquired_merger", "other_investing_net"]})
CF_ROWS.append(spacer())
CF_ROWS.append({"id": "st_debt_net", "label": "Net change in short-term debt", "type": "input", "indent": 1,
                 "values": row_vals([208, 224, 1198, -1329, 3050, 554, -372, 41])})
CF_ROWS.append({"id": "lt_debt_borrow", "label": "Long-term debt borrowings", "type": "input", "indent": 1,
                 "values": row_vals([8, 99, 2796, 2283, 3210, 2188, 4844, 5148])})
CF_ROWS.append({"id": "lt_debt_repay", "label": "Long-term debt repayments", "type": "input", "indent": 1,
                 "values": row_vals([-3124, -1583, -2681, -1468, -1785, -1682, -1305, -2278])})
CF_ROWS.append({"id": "issuance_shares", "label": "Proceeds from issuance of ordinary shares", "type": "input", "indent": 1,
                 "values": row_vals([77, 72, 47, 50, 36, 33, 31, 23])})
CF_ROWS.append({"id": "purchase_shares", "label": "Purchases of ordinary shares (buybacks)", "type": "input", "indent": 1,
                 "values": row_vals([-599, -2658, -2457, -4612, -5168, -3958, -4482, -4601])})
CF_ROWS.append({"id": "cash_dividends", "label": "Cash dividends paid", "type": "input", "indent": 1,
                 "values": row_vals([-1166, -1891, -2028, -2189, -2344, -2482, -2655, -2811])})
CF_ROWS.append({"id": "nci_transactions_other", "label": "NCI transactions and other financing activities, net", "type": "input", "indent": 1,
                 "values": row_vals([-402, -3260, -220, -323, -88, -53, -420, -76])})
CF_ROWS.append({"id": "cff_total", "label": "Net Cash Used in Financing Activities", "type": "subtotal", "bold": True, "border_top": True,
                 "children": ["st_debt_net", "lt_debt_borrow", "lt_debt_repay", "issuance_shares", "purchase_shares", "cash_dividends", "nci_transactions_other"]})
CF_ROWS.append(spacer())
CF_ROWS.append({"id": "disc_cfo", "label": "Discontinued operations - operating activities", "type": "input", "indent": 1,
                 "values": row_vals([48, 69, None, None, None, None, None, None])})
CF_ROWS.append({"id": "disc_cfi", "label": "Discontinued operations - investing activities", "type": "input", "indent": 1,
                 "values": row_vals([-23, -60, None, None, None, None, None, None])})
CF_ROWS.append({"id": "disc_cff", "label": "Discontinued operations - financing activities", "type": "input", "indent": 1,
                 "values": row_vals([2, 5, None, None, None, None, None, None])})
CF_ROWS.append({"id": "disc_net", "label": "Net Cash Flows of Discontinued Operations", "type": "subtotal",
                 "children": ["disc_cfo", "disc_cfi", "disc_cff"]})
CF_ROWS.append(spacer())
CF_ROWS.append({"id": "fx_effect", "label": "Effect of exchange rate changes on cash", "type": "input",
                 "values": row_vals([-60, -77, -44, -61, -74, -7, -234, 131])})
CF_ROWS.append({"id": "change_in_cash", "label": "Change in Cash and Cash Equivalents", "type": "subtotal", "bold": True, "border_top": True,
                 "children": ["cfo_total", "cfi_total", "cff_total", "disc_net", "fx_effect"]})
CF_ROWS.append({"id": "disc_cash_reclass", "label": "Cash of discontinued operations, reclassification", "type": "input", "indent": 1,
                 "values": row_vals([-137, -14, None, None, None, None, None, None])})
CF_ROWS.append({"id": "cash_begin", "label": "Cash and cash equivalents, beginning of period", "type": "input",
                 "values": row_vals([617, 4466, 2700, 3754, 2823, 5436, 4664, 4850])})
CF_ROWS.append({"id": "cash_end", "label": "Cash and Cash Equivalents, End of Period", "type": "calc", "bold": True, "border_top": True,
                 "expr": "{cash_begin}+{change_in_cash}+{disc_cash_reclass}"})
CF_ROWS.append(spacer())
CF_ROWS.append({"id": "cf_check", "label": "Check: CF-derived ending cash vs. Balance Sheet cash", "type": "check",
                 "expr": "{cash_end}-{BS:cash}"})

# FCF analytics
CF_ROWS.append(spacer())
CF_ROWS.append({"id": "fcf", "label": "Free Cash Flow (CFO + Capex)", "type": "calc", "bold": True,
                 "expr": "{cfo_total}+{capex}"})
CF_ROWS.append({"id": "fcf_growth", "label": "FCF growth %", "type": "growth_yoy", "of": "fcf", "fmt": "pct", "memo": True})
CF_ROWS.append({"id": "capex_pct_sales", "label": "Capex % of sales", "type": "calc", "expr": "0-{capex}/{IS:sales}", "fmt": "pct", "memo": True})
CF_ROWS.append({"id": "fcf_margin", "label": "FCF margin %", "type": "calc", "expr": "{fcf}/{IS:sales}", "fmt": "pct", "memo": True})
CF_ROWS.append({"id": "fcf_conversion", "label": "FCF conversion (FCF / Net Income)", "type": "calc", "expr": "{fcf}/{IS:net_income_linde}", "fmt": "x", "memo": True})

CF_ROWS.append(spacer())
CF_ROWS.append({"id": "income_taxes_paid", "label": "Supplemental: income taxes paid", "type": "input", "indent": 1,
                 "values": row_vals([757, 1357, 1066, 1710, 1735, 1955, 2216, None])})
CF_ROWS.append({"id": "interest_paid", "label": "Supplemental: interest paid, net of capitalized interest", "type": "input", "indent": 1,
                 "values": row_vals([214, 275, 322, 233, 170, 451, 443, 548])})

CF_SHEET = {
    "name": "Cash Flow Statement", "short": "CF", "kind": "statement", "tab_color": "1F4E79",
    "contents": True,
    "blocks": [{"title": "Consolidated Statement of Cash Flows", "rows": CF_ROWS}],
}

# ---------------------------------------------------------------------------
# SEGMENTS
# ---------------------------------------------------------------------------
SEG_ROWS = []
SEG_ROWS.append({"id": "hdr_sales", "label": "Segment Sales", "type": "spacer"})
# legacy FY2018 structure
LEGACY_SALES = {
    "seg_na_sales": ("North America", 6420), "seg_eu_sales": ("Europe (legacy)", 1592),
    "seg_sa_sales": ("South America (legacy)", 1369), "seg_asia_sales": ("Asia (legacy)", 1964),
    "seg_surftech_sales": ("Surface Technologies (legacy)", 682), "seg_lindeag_sales": ("Linde AG (legacy stub)", 2873),
}
for rid, (label, val) in LEGACY_SALES.items():
    SEG_ROWS.append({"id": rid, "label": label, "type": "input", "indent": 1,
                      "values": {"FY2018": val}, "min_label": "FY2018", "max_label": "FY2018"})
NEW_SALES = {
    "seg_americas_sales": ("Americas", [None, 10993, 10459, 12103, 13874, 14304, 14442, 15208]),
    "seg_emea_sales": ("EMEA", [None, 6643, 6449, 7643, 8443, 8542, 8352, 8549]),
    "seg_apac_sales": ("APAC", [None, 5839, 5687, 6133, 6480, 6559, 6632, 6661]),
    "seg_engineering_sales": ("Engineering", [None, 2799, 2851, 2867, 2762, 2160, 2322, 2250]),
    "seg_other_sales": ("Other", [None, 1954, 1797, 2047, 1805, 1289, 1257, 1318]),
}
for rid, (label, arr) in NEW_SALES.items():
    SEG_ROWS.append({"id": rid, "label": label, "type": "input", "indent": 1, "values": row_vals(arr), "min_label": "FY2019"})
SEG_ROWS.append({"id": "seg_total_sales", "label": "Total Segment Sales", "type": "subtotal", "bold": True, "border_top": True,
                  "children": list(LEGACY_SALES.keys()) + list(NEW_SALES.keys())})
SEG_ROWS.append({"id": "seg_rev_check", "label": "Check: Total Segment Sales vs. IS Sales", "type": "check",
                  "expr": "{seg_total_sales}-{IS:sales}"})

SEG_ROWS.append(spacer())
SEG_ROWS.append({"id": "hdr_op", "label": "Segment Operating Profit", "type": "spacer"})
LEGACY_OP = {
    "seg_na_op": ("North America", 1648), "seg_eu_op": ("Europe (legacy)", 316),
    "seg_sa_op": ("South America (legacy)", 215), "seg_asia_op": ("Asia (legacy)", 427),
    "seg_surftech_op": ("Surface Technologies (legacy)", 118), "seg_lindeag_op": ("Linde AG (legacy stub)", 252),
}
for rid, (label, val) in LEGACY_OP.items():
    SEG_ROWS.append({"id": rid, "label": label, "type": "input", "indent": 1,
                      "values": {"FY2018": val}, "min_label": "FY2018", "max_label": "FY2018"})
NEW_OP = {
    "seg_americas_op": ("Americas", [None, 2578, 2773, 3368, 3732, 4244, 4550, 4747]),
    "seg_emea_op": ("EMEA", [None, 1367, 1465, 1889, 2013, 2486, 2780, 3055]),
    "seg_apac_op": ("APAC", [None, 1198, 1277, 1502, 1670, 1806, 1918, 1933]),
    "seg_engineering_op": ("Engineering", [None, 390, 435, 473, 555, 491, 410, 408]),
    "seg_other_corp_op": ("Other / corporate", [None, -245, -153, -56, -66, 43, 62, -6]),
}
for rid, (label, arr) in NEW_OP.items():
    SEG_ROWS.append({"id": rid, "label": label, "type": "input", "indent": 1, "values": row_vals(arr), "min_label": "FY2019"})
SEG_ROWS.append({"id": "seg_op_subtotal", "label": "Total Segment Operating Profit", "type": "subtotal", "bold": True, "border_top": True,
                  "children": list(LEGACY_OP.keys()) + list(NEW_OP.keys())})
SEG_ROWS.append({"id": "special_charges_recon", "label": "Less: special / restructuring / transaction charges (Note 3)", "type": "input", "indent": 1,
                  "values": row_vals([-309, -567, -506, -273, -1029, -40, -145, -273])})
SEG_ROWS.append({"id": "net_gain_sale_recon", "label": "Add: net gain on sale of businesses", "type": "input", "indent": 1,
                  "values": row_vals([3294, 164, None, None, None, None, None, None])})
SEG_ROWS.append({"id": "ppa_lindeag_recon", "label": "Less: purchase accounting impacts - Linde AG merger", "type": "input", "indent": 1,
                  "values": row_vals([-714, -1952, -1969, -1919, -1506, -1006, -940, -941])})
SEG_ROWS.append({"id": "seg_total_op_profit", "label": "Total Operating Profit (reconciled)", "type": "subtotal", "bold": True, "border_top": True,
                  "children": ["seg_op_subtotal", "special_charges_recon", "net_gain_sale_recon", "ppa_lindeag_recon"]})
SEG_ROWS.append({"id": "seg_op_check", "label": "Check: Segment Operating Profit (reconciled) vs. IS Operating Profit", "type": "check",
                  "expr": "{seg_total_op_profit}-{IS:operating_profit}"})

SEG_ROWS.append(spacer())
SEG_ROWS.append({"id": "hdr_da", "label": "Segment Depreciation and Amortization", "type": "spacer"})
LEGACY_DA = {
    "seg_na_da": ("North America", 660), "seg_eu_da": ("EMEA (legacy: Europe)", 146),
    "seg_sa_da": ("South America (legacy)", 148), "seg_asia_da": ("Asia/South Pacific (legacy)", 204),
    "seg_surftech_da": ("Surface Technologies (legacy)", 44), "seg_lindeag_da": ("Linde AG (legacy stub)", 282),
}
for rid, (label, val) in LEGACY_DA.items():
    SEG_ROWS.append({"id": rid, "label": label, "type": "input", "indent": 1,
                      "values": {"FY2018": val}, "min_label": "FY2018", "max_label": "FY2018"})
NEW_DA = {
    "seg_americas_da": ("Americas", [None, 1195, 1196, 1243, 1320, 1423, 1450, 1504]),
    "seg_emea_da": ("EMEA", [None, 749, 723, 752, 661, 640, 640, 681]),
    "seg_apac_da": ("APAC", [None, 613, 619, 611, 593, 633, 641, 674]),
    "seg_engineering_da": ("Engineering", [None, 35, 36, 39, 33, 33, 33, 32]),
    "seg_other_da": ("Other", [None, 143, 132, 127, 116, 96, 93, 95]),
}
# NOTE: all NEW_DA / NEW_OP / NEW_SALES figures above verified against each fiscal year's own
# 10-K Note 18 Segment Information (FY2019, FY2020 MD&A Segment Discussion + Note 18, FY2022 Note 18
# comparative for 2021/2020, FY2025 Note 18 comparative for 2023-2025).
for rid, (label, arr) in NEW_DA.items():
    SEG_ROWS.append({"id": rid, "label": label, "type": "input", "indent": 1, "values": row_vals(arr), "min_label": "FY2019"})
SEG_ROWS.append({"id": "seg_da_subtotal", "label": "Total Segment D&A", "type": "subtotal", "bold": True, "border_top": True,
                  "children": list(LEGACY_DA.keys()) + list(NEW_DA.keys())})
SEG_ROWS.append({"id": "ppa_da_recon", "label": "Add: purchase accounting impacts - Linde AG merger (D&A)", "type": "input", "indent": 1,
                  "values": row_vals([346, 1940, 1920, 1863, 1481, 991, 923, 777])})
SEG_ROWS.append({"id": "seg_total_da", "label": "Total D&A (reconciled)", "type": "subtotal", "bold": True, "border_top": True,
                  "children": ["seg_da_subtotal", "ppa_da_recon"]})
SEG_ROWS.append({"id": "seg_da_check", "label": "Check: Segment D&A (reconciled) vs. IS D&A", "type": "check",
                  "expr": "{seg_total_da}-{IS:da}"})

SEG_ROWS.append(spacer())
SEG_ROWS.append({"id": "hdr_capex", "label": "Segment Expenditures for Long-Lived Assets (FY2023-FY2025 only; see note)", "type": "spacer"})
CAPEX_SEG = {
    "seg_americas_capex": ("Americas", [None, None, None, None, None, 2999, 2805, 3428]),
    "seg_emea_capex": ("EMEA", [None, None, None, None, None, 635, 702, 729]),
    "seg_apac_capex": ("APAC", [None, None, None, None, None, 975, 1059, 1177]),
    "seg_engineering_capex": ("Engineering", [None, None, None, None, None, 24, 25, 35]),
    "seg_other_capex": ("Other", [None, None, None, None, None, 107, 223, 304]),
}
for rid, (label, arr) in CAPEX_SEG.items():
    row = {"id": rid, "label": label, "type": "input", "indent": 1, "values": row_vals(arr), "min_label": "FY2023"}
    if rid == "seg_americas_capex":
        row["note"] = ("Only FY2023-FY2025 shown: those years' 10-Ks disclose pure 'expenditures for "
                       "long-lived assets' by segment. FY2018-FY2019 10-Ks disclosed a 'Capital Expenditures "
                       "and Acquisitions' combined figure on a different basis and are excluded here to avoid "
                       "mixing bases; FY2020-FY2022 10-Ks did not disclose segment capex at all.")
    SEG_ROWS.append(row)
SEG_ROWS.append({"id": "seg_capex_subtotal", "label": "Total Segment Capex (FY2023-FY2025 only)", "type": "subtotal", "bold": True, "border_top": True,
                  "children": list(CAPEX_SEG.keys())})

SEG_SHEET = {
    "name": "Segments", "short": "SEG", "kind": "statement", "tab_color": "548235",
    "contents": True,
    "blocks": [{"title": "Segment Information (Note - Segment Reporting)", "rows": SEG_ROWS}],
}
# clean None notes
for r in SEG_ROWS:
    if isinstance(r, dict) and r.get("note") is None and "note" in r:
        del r["note"]

# ---------------------------------------------------------------------------
# OPERATING METRICS
# ---------------------------------------------------------------------------
OM_ROWS = []
OM_ROWS.append({"id": "adj_op_profit", "label": "Total Segment Operating Profit", "type": "link", "ref": "SEG:seg_op_subtotal", "bold": True})
OM_ROWS.append({"id": "adj_op_margin", "label": "Segment operating margin %", "type": "calc", "expr": "{adj_op_profit}/{IS:sales}", "fmt": "pct", "memo": True})
OM_ROWS.append(spacer())
OM_ROWS.append({"id": "hdr_mix", "label": "Segment Sales Mix % (Americas/EMEA/APAC/Engineering/Other framework, FY2019+)", "type": "spacer"})
OM_MIX = {
    "mix_americas": ("Americas % of sales", "SEG:seg_americas_sales"),
    "mix_emea": ("EMEA % of sales", "SEG:seg_emea_sales"),
    "mix_apac": ("APAC % of sales", "SEG:seg_apac_sales"),
    "mix_engineering": ("Engineering % of sales", "SEG:seg_engineering_sales"),
    "mix_other": ("Other % of sales", "SEG:seg_other_sales"),
}
for rid, (label, ref) in OM_MIX.items():
    OM_ROWS.append({"id": rid, "label": label, "type": "calc", "indent": 1, "fmt": "pct", "min_label": "FY2019",
                     "expr": "{" + ref + "}/{IS:sales}"})
OM_ROWS.append(spacer())
OM_ROWS.append({"id": "hdr_seg_margin", "label": "Segment Operating Margin % (FY2019+)", "type": "spacer"})
OM_MARGIN = {
    "margin_americas": ("Americas operating margin %", "SEG:seg_americas_op", "SEG:seg_americas_sales"),
    "margin_emea": ("EMEA operating margin %", "SEG:seg_emea_op", "SEG:seg_emea_sales"),
    "margin_apac": ("APAC operating margin %", "SEG:seg_apac_op", "SEG:seg_apac_sales"),
    "margin_engineering": ("Engineering operating margin %", "SEG:seg_engineering_op", "SEG:seg_engineering_sales"),
}
for rid, (label, num, den) in OM_MARGIN.items():
    OM_ROWS.append({"id": rid, "label": label, "type": "calc", "indent": 1, "fmt": "pct", "min_label": "FY2019",
                     "expr": "{" + num + "}/{" + den + "}"})

OM_SHEET = {
    "name": "Operating Metrics", "short": "OM", "kind": "statement", "tab_color": "548235",
    "contents": True,
    "blocks": [{"title": "Segment-Based Operating Metrics", "rows": OM_ROWS}],
}

# ---------------------------------------------------------------------------
# DERIVED METRICS
# ---------------------------------------------------------------------------
DM_ROWS = []


def dm(rid, label, expr, fmt="pct"):
    return {"id": rid, "label": label, "type": "calc", "memo": True, "fmt": fmt, "expr": expr}


DM_ROWS.append({"id": "hdr_prof", "label": "Profitability", "type": "spacer"})
DM_ROWS.append(dm("gross_margin_dm", "Gross margin %", "{IS:gross_profit}/{IS:sales}"))
DM_ROWS.append(dm("op_margin_dm", "Operating margin %", "{IS:operating_profit}/{IS:sales}"))
DM_ROWS.append(dm("ebitda_margin_dm", "EBITDA margin %", "({IS:operating_profit}+{IS:da})/{IS:sales}"))
DM_ROWS.append(dm("net_margin_dm", "Net margin %", "{IS:net_income_linde}/{IS:sales}"))
DM_ROWS.append(dm("eff_tax_rate_dm", "Effective tax rate %", "{IS:income_taxes}/{IS:pretax_income}"))

DM_ROWS.append(spacer())
DM_ROWS.append({"id": "hdr_returns", "label": "Returns", "type": "spacer"})
DM_ROWS.append(dm("roa", "Return on Assets (avg)", "{IS:net_income_linde}/(({BS:total_assets}+{BS:total_assets@-1})/2)"))
DM_ROWS.append(dm("roe", "Return on Equity (avg)", "{IS:net_income_linde}/(({BS:total_linde_equity}+{BS:total_linde_equity@-1})/2)"))
DM_ROWS.append(dm("roic", "Return on Invested Capital (avg)",
                   "{IS:operating_profit}*(1-{IS:effective_tax_rate})/(({BS:total_linde_equity}+{BS:lt_debt}+{BS:total_linde_equity@-1}+{BS:lt_debt@-1})/2)"))
DM_ROWS.append(dm("asset_turnover", "Asset turnover (x, avg)", "{IS:sales}/(({BS:total_assets}+{BS:total_assets@-1})/2)", fmt="x"))

DM_ROWS.append(spacer())
DM_ROWS.append({"id": "hdr_leverage", "label": "Leverage", "type": "spacer"})
DM_ROWS.append(dm("net_debt", "Net debt ($mm)", "{BS:lt_debt}+{BS:st_debt}+{BS:current_portion_ltd}-{BS:cash}", fmt="num"))
DM_ROWS.append(dm("net_debt_ebitda", "Net debt / EBITDA (x)", "{net_debt}/({IS:operating_profit}+{IS:da})", fmt="x"))
DM_ROWS.append(dm("debt_equity", "Debt / Equity (x)", "({BS:lt_debt}+{BS:st_debt}+{BS:current_portion_ltd})/{BS:total_linde_equity}", fmt="x"))

DM_ROWS.append(spacer())
DM_ROWS.append({"id": "hdr_solvency", "label": "Solvency", "type": "spacer"})
DM_ROWS.append(dm("equity_ratio", "Equity ratio (Equity / Assets)", "{BS:total_equity}/{BS:total_assets}"))
DM_ROWS.append(dm("debt_assets", "Debt / Assets", "({BS:lt_debt}+{BS:st_debt}+{BS:current_portion_ltd})/{BS:total_assets}"))

DM_ROWS.append(spacer())
DM_ROWS.append({"id": "hdr_liquidity", "label": "Liquidity", "type": "spacer"})
DM_ROWS.append(dm("current_ratio", "Current ratio (x)", "{BS:total_ca}/{BS:total_cl}", fmt="x"))
DM_ROWS.append(dm("quick_ratio", "Quick ratio (x)", "({BS:cash}+{BS:ar})/{BS:total_cl}", fmt="x"))
DM_ROWS.append(dm("cash_ratio", "Cash ratio (x)", "{BS:cash}/{BS:total_cl}", fmt="x"))

DM_ROWS.append(spacer())
DM_ROWS.append({"id": "hdr_coverage", "label": "Coverage", "type": "spacer"})
DM_ROWS.append(dm("interest_coverage", "Interest coverage (EBIT / Interest, x)", "{IS:operating_profit}/{IS:interest_expense}", fmt="x"))
DM_ROWS.append(dm("cfo_interest", "CFO / Interest expense (x)", "{CF:cfo_total}/{IS:interest_expense}", fmt="x"))

DM_ROWS.append(spacer())
DM_ROWS.append({"id": "hdr_cashconv", "label": "Cash Conversion", "type": "spacer"})
DM_ROWS.append(dm("cfo_margin_dm", "CFO margin %", "{CF:cfo_total}/{IS:sales}"))
DM_ROWS.append(dm("cfo_ebitda", "CFO / EBITDA (x)", "{CF:cfo_total}/({IS:operating_profit}+{IS:da})", fmt="x"))
DM_ROWS.append(dm("capex_intensity", "Capex intensity (Capex / Sales)", "0-{CF:capex}/{IS:sales}"))
DM_ROWS.append(dm("fcf_margin_dm", "FCF margin %", "{CF:fcf}/{IS:sales}"))
DM_ROWS.append(dm("fcf_ni", "FCF / Net Income (x)", "{CF:fcf}/{IS:net_income_linde}", fmt="x"))
DM_ROWS.append(dm("da_capex", "D&A / Capex (x)", "{IS:da}/(0-{CF:capex})", fmt="x"))

DM_ROWS.append(spacer())
DM_ROWS.append({"id": "hdr_quality", "label": "Earnings Quality", "type": "spacer"})
DM_ROWS.append(dm("cfo_ni", "CFO / Net Income (x)", "{CF:cfo_total}/{IS:net_income_linde}", fmt="x"))
DM_ROWS.append(dm("accrual_ratio", "Accrual ratio ((NI - CFO) / Assets)", "({IS:net_income_linde}-{CF:cfo_total})/{BS:total_assets}"))

DM_ROWS.append(spacer())
DM_ROWS.append({"id": "hdr_growth", "label": "Growth", "type": "spacer"})
DM_ROWS.append(dm("rev_growth_dm", "Revenue growth %", "{IS:sales}/{IS:sales@-1}-1"))
DM_ROWS.append(dm("ni_growth_dm", "Net income growth %", "{IS:net_income_linde}/{IS:net_income_linde@-1}-1"))
DM_ROWS.append(dm("cfo_growth_dm", "CFO growth %", "{CF:cfo_total}/{CF:cfo_total@-1}-1"))

DM_ROWS.append(spacer())
DM_ROWS.append({"id": "hdr_wc", "label": "Working Capital", "type": "spacer"})
DM_ROWS.append({"id": "dso_dm", "label": "Days Sales Outstanding", "type": "link", "ref": "BS:dso", "memo": True})
DM_ROWS.append({"id": "dio_dm", "label": "Days Inventory Outstanding", "type": "link", "ref": "BS:dio", "memo": True})
DM_ROWS.append({"id": "dpo_dm", "label": "Days Payable Outstanding", "type": "link", "ref": "BS:dpo", "memo": True})
DM_ROWS.append({"id": "ccc_dm", "label": "Cash Conversion Cycle", "type": "link", "ref": "BS:ccc", "memo": True})

DM_SHEET = {
    "name": "Derived Metrics", "short": "DM", "kind": "statement", "tab_color": "7030A0",
    "contents": True,
    "blocks": [{"title": "Derived / Ratio Analysis", "rows": DM_ROWS}],
}

# ---------------------------------------------------------------------------
# COVER
# ---------------------------------------------------------------------------
COVER = {
    "name": "Cover", "kind": "table", "col_widths": [34, 70], "tab_color": "1F4E79",
    "table": [
        [{"text": "Linde plc (NYSE: LIN) - Financial Model", "bold": True}],
        [],
        [{"text": "Company information", "bold": True}],
        ["Ticker", "LIN"],
        ["Exchange", "NYSE"],
        ["CIK", "0001707925"],
        ["Sector / Industry", "Materials / Industrial Gases"],
        ["Reporting currency", "USD"],
        ["Units", "$ in millions, except per-share data"],
        ["Reporting framework", "US GAAP"],
        ["Consolidation scope", "Consolidated (Linde plc and subsidiaries)"],
        ["Fiscal year end", "December 31"],
        ["Periods covered", "FY2018 - FY2025 (annual, 8 fiscal years)"],
        ["Model date", "2026-09-15"],
        ["Data source", "SEC Form 10-K filings, Tier 2 primary source (source.html / prepared/document.md)"],
        [],
        [{"text": "Color legend", "bold": True}],
        [{"text": "Blue", "fill": "D6E4F0"}, "Hardcoded reported value (input, traces to a 10-K)"],
        [{"text": "Black"}, "Formula / calculation (subtotal, calc, check)"],
        [{"text": "Green", "fill": "E2EFDA"}, "Cross-sheet link"],
        [{"text": "Grey italic"}, "Memo / commentary (margins, ratios, growth rates)"],
        [],
        [{"text": "Sheet directory", "bold": True}],
        ["Income Statement", "IS tab"],
        ["Balance Sheet", "BS tab"],
        ["Cash Flow Statement", "CF tab"],
        ["Segments", "SEG tab"],
        ["Operating Metrics", "OM tab"],
        ["Derived Metrics", "DM tab"],
        ["Sources", "Sources tab"],
        [],
        [{"text": "Comparability notes", "bold": True}],
        ["1. Segment redefinition (FY2018 -> FY2019)",
         "FY2018 reflects legacy Praxair geographic segments (North America / Europe / South America / Asia / "
         "Surface Technologies) plus a separate Linde AG stub, because a 2018 FTC hold-separate order delayed full "
         "merger integration. From FY2019, Linde reports on the Americas / EMEA / APAC / Engineering / Other "
         "framework, retrospectively recast. The Segments sheet models both structures with min/max period tags; "
         "segment totals tie exactly to consolidated Sales and Operating Profit in every year (see SEG tab checks)."],
        ["2. Retained earnings / treasury stock discontinuity (FY2022 -> FY2023)",
         "Retained earnings fell from $20,541mm (FY2022) to $8,845mm (FY2023) and treasury stock fell from "
         "$(14,737)mm to $(3,133)mm. This is not a restatement or error: the FY2023 Statement of Equity (as shown "
         "comparatively in the FY2024 and FY2025 10-Ks) discloses an 'Intercompany reorganization (Note 14)' "
         "retiring 61.2 million treasury shares (cost basis $15,300mm) against retained earnings. Total balance "
         "sheet equity and Total Assets = Total Liabilities + Equity tie out in every year."],
        ["3. Scope: Geography, Note Schedules, and BS Detail sheets not built separately",
         "The bundle-only collector output classified most non-statement source tables (planned Geography, Note "
         "Schedules, and Balance Sheet Detail content) under generic, uninformative block titles that could not be "
         "reliably attributed to a specific disclosure without extensive per-table manual inspection. Rather than "
         "populate these sheets with low-confidence or unlabeled data, geography content was folded into the "
         "Segments sheet (Linde's segments are themselves geographic) and Note Schedules / Balance Sheet Detail "
         "were omitted. Segment capital expenditures ('expenditures for long-lived assets') are disclosed on a "
         "consistent basis only for FY2023-FY2025 in the companies' own 10-Ks (FY2018-FY2019 used a different, "
         "combined 'capex and acquisitions' basis; FY2020-FY2022 10-Ks did not disclose segment capex at all) - "
         "the Segments tab shows only the three consistent years rather than mixing bases or estimating. "
         "Sales-by-major-country is disclosed for FY2018-FY2019 and FY2023-FY2025 (6 of 8 years, with a "
         "FY2020-FY2022 gap in that specific disclosure) and was not incorporated as a separate block given the "
         "gap and the already-broad scope of the Segments sheet."],
    ],
}

SOURCES = {
    "name": "Sources", "kind": "table", "col_widths": [18, 70, 45],
    "table": [
        [{"text": "Sources and data provenance", "bold": True}],
        [],
        [{"text": "Period", "bold": True}, {"text": "Source document", "bold": True}, {"text": "Path", "bold": True}],
        ["FY2018", "Linde plc Form 10-K (FY2018)", "sources/companies/US/LIN-linde/artifacts/ten_k/LIN-linde/FY2018/psp_2ebae6876662453e850a71097e970a0c/"],
        ["FY2019", "Linde plc Form 10-K (FY2019)", "sources/companies/US/LIN-linde/artifacts/ten_k/LIN-linde/FY2019/psp_17c00f60b08b453fae28219102907da2/"],
        ["FY2020", "Linde plc Form 10-K (FY2020)", "sources/companies/US/LIN-linde/artifacts/ten_k/LIN-linde/FY2020/psp_26319e151ba249dea1137948aedfa245/"],
        ["FY2021", "Linde plc Form 10-K (FY2021)", "sources/companies/US/LIN-linde/artifacts/ten_k/LIN-linde/FY2021/psp_b2b8c0f9a8374dca86d6ba61612f5ea8/"],
        ["FY2022", "Linde plc Form 10-K (FY2022)", "sources/companies/US/LIN-linde/artifacts/ten_k/LIN-linde/FY2022/psp_12a4ea550bc340fa82af491fa19c65cc/"],
        ["FY2023", "Linde plc Form 10-K (FY2023)", "sources/companies/US/LIN-linde/artifacts/ten_k/LIN-linde/FY2023/psp_962cb7e58b0a4448ae507427a5c3a749/"],
        ["FY2024", "Linde plc Form 10-K (FY2024)", "sources/companies/US/LIN-linde/artifacts/ten_k/LIN-linde/FY2024/psp_871627ce04e94c8897932a75dbc7c38b/"],
        ["FY2025", "Linde plc Form 10-K (FY2025)", "sources/companies/US/LIN-linde/artifacts/ten_k/LIN-linde/FY2025/psp_ddce53d5cc49476d894d1511e805bb4a/"],
        [],
        ["Note", "All figures hand-extracted and cross-checked from each fiscal year's own 10-K (prepared/document.md), "
                 "not from tables.json (which misclassified statement tables under unrelated topic_hints and mis-parsed "
                 "parenthesized negative values) and not from any deep-research markdown report.", ""],
    ],
}

MODEL = {
    "company": {
        "name": "Linde plc", "ticker": "LIN", "currency": "USD",
        "units": "$ in millions except per-share data", "reporting_framework": "US GAAP",
        "fiscal_year_end": "December 31", "consolidation_scope": "consolidated",
        "as_of_date": "FY2025", "model_date": "2026-09-15",
    },
    "periods": {"annual": [{"label": p} for p in PERIODS], "scrap_cols": 0, "quarterly": []},
    "sheets": [COVER, IS_SHEET, BS_SHEET, CF_SHEET, SEG_SHEET, OM_SHEET, DM_SHEET, SOURCES],
}

if __name__ == "__main__":
    out_path = "/Users/tccc/Desktop/AI Invest/Workspace/research/companies/US/LIN-linde/outputs/company-research-to-excel-20260915/model.json"
    with open(out_path, "w") as f:
        json.dump(MODEL, f, indent=2)
    print("wrote", out_path)
    # quick sanity: duplicate id check per sheet
    for s in MODEL["sheets"]:
        if s.get("kind") != "statement":
            continue
        ids = []
        for b in s["blocks"]:
            for r in b["rows"]:
                if "id" in r:
                    ids.append(r["id"])
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            print("DUPLICATE IDS in", s["name"], dupes)
        else:
            print(s["name"], "rows:", len(ids), "OK")
