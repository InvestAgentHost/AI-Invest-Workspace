#!/usr/bin/env python3
"""Custom Phase-4 assembly of the LMT model.json from transcribed source data.

Every numeric literal below traces to either:
  - data/curated/companies/US/LMT-lockheed-martin/financial-input-2016-2025.json (Tier 1)
  - data/curated/companies/US/LMT-lockheed-martin/segment-history-2016-2025.json (Tier 1)
  - SEC 10-K source.html tables captured in tables.json (Tier 2), FY2021-FY2025 filings,
    reconciled under a "most recently filed presentation wins" policy for any year that
    appears in more than one filing vintage with different reclassified figures.
  - data/derived/.../financial-metrics-2016-2025.md derived ratios (Tier 4), reused
    verbatim from the assemble_model.py draft's Derived Metrics sheet.
No numbers are invented; years without source coverage are left blank (via min_label/
max_label) rather than estimated.
"""
import json
from pathlib import Path

WORKDIR = Path(__file__).parent
DRAFT = json.loads((WORKDIR / "model.json").read_text())

ANNUAL = [f"FY{y}" for y in range(2016, 2026)]
PERIODS = {
    "annual": [{"label": f"FY{y}", "end": f"{y}-12-31"} for y in range(2016, 2026)],
    "scrap_cols": 0,
    "quarterly": [],
}

COMPANY = {
    "name": "Lockheed Martin Corporation",
    "ticker": "LMT",
    "currency": "USD",
    "units": "$ in millions except per-share data",
    "reporting_framework": "US GAAP",
    "fiscal_year_end": "December 31",
    "consolidation_scope": "consolidated",
    "as_of_date": "2026-08-31",
    "model_date": "2026-09-08",
}


def vals(pairs):
    """pairs: dict of {year:int -> value} using bare 4-digit years -> FY-labeled dict."""
    return {f"FY{y}": v for y, v in pairs.items()}


# --------------------------------------------------------------------------
# INCOME STATEMENT
# --------------------------------------------------------------------------

is_block1 = {
    "title": "AS-REPORTED INCOME STATEMENT",
    "rows": [
        {"id": "rev_products", "label": "Products", "type": "input", "indent": 1,
         "values": vals({2019: 50053, 2020: 54928, 2021: 56435, 2022: 55466,
                         2023: 56265, 2024: 59277, 2025: 62654}),
         "min_label": "FY2019", "note": "SEC 10-K MD&A results-of-operations detail; most recent filing per year."},
        {"id": "rev_services", "label": "Services", "type": "input", "indent": 1,
         "values": vals({2019: 9759, 2020: 10470, 2021: 10609, 2022: 10518,
                         2023: 11306, 2024: 11766, 2025: 12394}),
         "min_label": "FY2019"},
        {"id": "total_sales", "label": "Total Sales", "type": "input", "bold": True,
         "values": vals({2016: 47290, 2017: 49960, 2018: 53762, 2019: 59812,
                         2020: 65398, 2021: 67044, 2022: 65984, 2023: 67571,
                         2024: 71043, 2025: 75048}),
         "note": "financial-input-2016-2025.json: revenue (Net sales / Total sales)."},
        {"type": "spacer"},
        {"id": "cost_products", "label": "Cost of Sales — Products", "type": "input", "indent": 1,
         "values": vals({2019: -44589, 2020: -48996, 2021: -50017, 2022: -49357,
                         2023: -50206, 2024: -54852, 2025: -57020}),
         "min_label": "FY2019",
         "note": "FY2022 shown at -49,357 per FY2024/FY2025 10-K comparative (vs -49,577 in native FY2022 10-K); $220M reclassified into Other unallocated, net. Most-recent-filing convention applied throughout."},
        {"id": "cost_services", "label": "Cost of Sales — Services", "type": "input", "indent": 1,
         "values": vals({2019: -8731, 2020: -9371, 2021: -9434, 2022: -9252,
                         2023: -10027, 2024: -10217, 2025: -11339}),
         "min_label": "FY2019"},
        {"id": "impairment_other_charges", "label": "Impairment and Other Charges", "type": "input", "indent": 1,
         "values": vals({2020: -27, 2021: -36, 2022: -100, 2023: -92, 2024: -87, 2025: -66}),
         "min_label": "FY2020",
         "note": "Not separately disclosed for FY2019 (folded into Other unallocated, net)."},
        {"id": "other_unallocated_net", "label": "Other Unallocated, Net", "type": "input", "indent": 1,
         "values": vals({2019: 1875, 2020: 1650, 2021: 1504, 2022: 1012, 2023: 1233,
                         2024: 1043, 2025: 996}),
         "min_label": "FY2019"},
        {"id": "total_cost_of_sales", "label": "Total Cost of Sales", "type": "input", "bold": True,
         "border_top": True,
         "values": vals({2019: -51445, 2020: -56744, 2021: -57983, 2022: -57697,
                         2023: -59092, 2024: -64113, 2025: -67429}),
         "min_label": "FY2019"},
        {"id": "gross_profit", "label": "Gross Profit", "type": "input", "bold": True,
         "values": vals({2019: 8367, 2020: 8654, 2021: 9061, 2022: 8287, 2023: 8479,
                         2024: 6930, 2025: 7619}),
         "min_label": "FY2019"},
        {"id": "other_income_net", "label": "Other Income, Net", "type": "input", "indent": 1,
         "values": vals({2019: 178, 2020: -10, 2021: 62, 2022: 61, 2023: 28,
                         2024: 83, 2025: 112}),
         "min_label": "FY2019"},
        {"id": "operating_profit", "label": "Operating Profit", "type": "input", "bold": True,
         "border_top": True,
         "values": vals({2016: 5888, 2017: 6744, 2018: 7334, 2019: 8545, 2020: 8644,
                         2021: 9123, 2022: 8348, 2023: 8507, 2024: 7013, 2025: 7731}),
         "note": "financial-input-2016-2025.json: operating_profit."},
        {"type": "spacer"},
        {"id": "interest_expense", "label": "Interest Expense", "type": "input", "indent": 1,
         "values": vals({2019: -653, 2020: -591, 2021: -569, 2022: -623, 2023: -916,
                         2024: -1036, 2025: -1118}),
         "min_label": "FY2019"},
        {"id": "nonservice_fas_pension", "label": "Non-service FAS Pension Income (Expense)", "type": "input",
         "indent": 1,
         "values": vals({2019: -577, 2020: 219, 2021: -1292, 2022: -971, 2023: 443,
                         2024: 62, 2025: -874}),
         "min_label": "FY2019"},
        {"id": "other_nonoperating_net", "label": "Other Non-operating Income (Expense), Net", "type": "input",
         "indent": 1,
         "values": vals({2019: -74, 2020: -37, 2021: 288, 2022: -74, 2023: 64,
                         2024: 181, 2025: 183}),
         "min_label": "FY2019"},
        {"id": "ebt", "label": "Earnings Before Income Taxes", "type": "input", "bold": True, "border_top": True,
         "values": vals({2019: 7241, 2020: 8235, 2021: 7550, 2022: 6680, 2023: 8098,
                         2024: 6220, 2025: 5922}),
         "min_label": "FY2019"},
        {"id": "income_tax_expense", "label": "Income Tax Expense", "type": "input", "indent": 1,
         "values": vals({2019: -1011, 2020: -1347, 2021: -1235, 2022: -948, 2023: -1178,
                         2024: -884, 2025: -905}),
         "min_label": "FY2019"},
        {"id": "net_earnings_discontinued", "label": "Net Loss from Discontinued Operations", "type": "input",
         "indent": 1, "memo": True,
         "values": vals({2020: -55}), "min_label": "FY2020", "max_label": "FY2020"},
        {"id": "net_earnings", "label": "Net Earnings", "type": "input", "bold": True, "border_top": True,
         "values": vals({2016: 5173, 2017: 1963, 2018: 5046, 2019: 6230, 2020: 6833,
                         2021: 6315, 2022: 5732, 2023: 6920, 2024: 5336, 2025: 5017}),
         "note": "financial-input-2016-2025.json: net_income_consolidated."},
        {"id": "is_check", "label": "IS Check: Sales − COGS + Other Income − Op. Profit (should be ~0)",
         "type": "check", "memo": True,
         "expr": "{total_sales}+{total_cost_of_sales}+{other_income_net}-{operating_profit}",
         "min_label": "FY2019", "max_label": "FY2025"},
    ],
}

is_block2 = {
    "title": "EPS & SHARE COUNT",
    "rows": [
        {"id": "basic_eps", "label": "Basic EPS", "type": "input", "bold": True, "fmt": "ps",
         "values": vals({2017: 6.82, 2018: 17.74, 2019: 22.09, 2020: 24.4, 2021: 22.85,
                         2022: 21.74, 2023: 27.65, 2024: 22.39, 2025: 21.56}),
         "min_label": "FY2017"},
        {"id": "diluted_eps", "label": "Diluted EPS", "type": "input", "bold": True, "fmt": "ps",
         "values": vals({2017: 6.75, 2018: 17.59, 2019: 21.95, 2020: 24.3, 2021: 22.76,
                         2022: 21.66, 2023: 27.55, 2024: 22.31, 2025: 21.49}),
         "min_label": "FY2017"},
        {"id": "eps_yoy", "label": "  YoY Growth", "type": "growth_yoy", "of": "diluted_eps",
         "fmt": "pct", "memo": True},
        {"id": "waso_basic", "label": "Weighted Avg Shares — Basic", "type": "input", "fmt": "num1",
         "values": vals({2019: 282.0, 2020: 280.0, 2021: 276.4, 2022: 263.7, 2023: 250.3,
                         2024: 238.3, 2025: 232.7}),
         "min_label": "FY2019"},
        {"id": "waso_diluted", "label": "Weighted Avg Shares — Diluted", "type": "input", "fmt": "num1",
         "values": vals({2019: 283.8, 2020: 281.2, 2021: 277.4, 2022: 264.6, 2023: 251.2,
                         2024: 239.2, 2025: 233.5}),
         "min_label": "FY2019"},
        {"id": "dps", "label": "Dividends Declared per Common Share", "type": "input", "fmt": "ps",
         "values": vals({2017: 7.46, 2018: 8.20, 2019: 9.00, 2020: 9.80, 2021: 10.60,
                         2022: 11.40, 2023: 12.15, 2024: 12.75, 2025: 13.35}),
         "min_label": "FY2017"},
        {"id": "dps_yoy", "label": "  YoY Growth", "type": "growth_yoy", "of": "dps",
         "fmt": "pct", "memo": True},
    ],
}

is_block3 = {
    "title": "MARGINS & GROWTH",
    "rows": [
        {"id": "rev_yoy", "label": "Revenue YoY Growth", "type": "growth_yoy", "of": "total_sales",
         "fmt": "pct", "memo": True},
        {"id": "gross_margin", "label": "Gross Margin", "type": "calc",
         "expr": "{gross_profit}/{total_sales}", "fmt": "pct", "memo": True, "min_label": "FY2019"},
        {"id": "op_margin", "label": "Operating Margin", "type": "calc",
         "expr": "{operating_profit}/{total_sales}", "fmt": "pct", "memo": True},
        {"id": "op_margin_yoy", "label": "  Operating Profit YoY Growth", "type": "growth_yoy",
         "of": "operating_profit", "fmt": "pct", "memo": True},
        {"id": "net_margin", "label": "Net Margin", "type": "calc",
         "expr": "{net_earnings}/{total_sales}", "fmt": "pct", "memo": True},
        {"id": "ni_yoy", "label": "  Net Earnings YoY Growth", "type": "growth_yoy",
         "of": "net_earnings", "fmt": "pct", "memo": True},
    ],
}

IS_SHEET = {
    "name": "Income Statement", "short": "IS", "kind": "statement",
    "tab_color": "1F4E79", "contents": True,
    "blocks": [is_block1, is_block2, is_block3],
}

# --------------------------------------------------------------------------
# BALANCE SHEET
# --------------------------------------------------------------------------

bs_block1 = {
    "title": "AS-REPORTED BALANCE SHEET",
    "rows": [
        {"id": "cash_and_equivalents", "label": "Cash and Cash Equivalents", "type": "input", "indent": 1,
         "values": vals({2016: 1837, 2017: 2861, 2018: 772, 2019: 1514, 2020: 3160,
                         2021: 3604, 2022: 2547, 2023: 1442, 2024: 2483, 2025: 4121}),
         "note": "FY2016-2018 labeled 'Cash, cash equivalents and short-term investments' in financial-input; values reconcile to the same balance shown as 'Cash and cash equivalents' from FY2019 forward."},
        {"id": "receivables_net", "label": "Receivables, Net", "type": "input", "indent": 1,
         "values": vals({2020: 1978, 2021: 1963, 2022: 2505, 2023: 2132, 2024: 2351, 2025: 3901}),
         "min_label": "FY2020"},
        {"id": "contract_assets", "label": "Contract Assets", "type": "input", "indent": 1,
         "values": vals({2020: 9545, 2021: 10579, 2022: 12318, 2023: 13183, 2024: 12957, 2025: 13001}),
         "min_label": "FY2020"},
        {"id": "inventories", "label": "Inventories", "type": "input", "indent": 1,
         "values": vals({2020: 3545, 2021: 2981, 2022: 3088, 2023: 3132, 2024: 3474, 2025: 3524}),
         "min_label": "FY2020"},
        {"id": "other_current_assets", "label": "Other Current Assets", "type": "input", "indent": 1,
         "values": vals({2020: 1150, 2021: 688, 2022: 533, 2023: 632, 2024: 584, 2025: 815}),
         "min_label": "FY2020"},
        {"id": "total_current_assets", "label": "Total Current Assets", "type": "input", "bold": True,
         "border_top": True,
         "values": vals({2016: 14780, 2017: 17505, 2018: 16103, 2019: 17095, 2020: 19378,
                         2021: 19815, 2022: 20991, 2023: 20521, 2024: 21849, 2025: 25362}),
         "note": "financial-input-2016-2025.json: current_assets."},
        {"id": "ppe_net", "label": "Property, Plant and Equipment, Net", "type": "input", "indent": 1,
         "values": vals({2020: 7213, 2021: 7597, 2022: 7975, 2023: 8370, 2024: 8726, 2025: 8875}),
         "min_label": "FY2020"},
        {"id": "goodwill", "label": "Goodwill", "type": "input", "indent": 1,
         "values": vals({2020: 10806, 2021: 10813, 2022: 10780, 2023: 10799, 2024: 11067, 2025: 11314}),
         "min_label": "FY2020"},
        {"id": "intangible_assets_net", "label": "Intangible Assets, Net", "type": "input", "indent": 1,
         "values": vals({2020: 3012, 2021: 2706, 2022: 2459, 2023: 2212, 2024: 2015, 2025: 1887}),
         "min_label": "FY2020"},
        {"id": "deferred_income_taxes_bs", "label": "Deferred Income Taxes", "type": "input", "indent": 1,
         "values": vals({2020: 3475, 2021: 2290, 2022: 3744, 2023: 2953, 2024: 3557, 2025: 2975}),
         "min_label": "FY2020"},
        {"id": "capitalized_software", "label": "Capitalized Software", "type": "input", "indent": 1,
         "values": vals({2024: 1866, 2025: 2417}), "min_label": "FY2024",
         "note": "Broken out as a separate face-BS line beginning with the FY2025 10-K; previously included within Other noncurrent assets."},
        {"id": "other_noncurrent_assets", "label": "Other Noncurrent Assets", "type": "input", "indent": 1,
         "values": vals({2020: 6826, 2021: 7652, 2022: 6931, 2023: 7601, 2024: 6537, 2025: 7010}),
         "min_label": "FY2020"},
        {"id": "total_assets", "label": "Total Assets", "type": "input", "bold": True, "border_top": True,
         "values": vals({2016: 47560, 2017: 46620, 2018: 44876, 2019: 47528, 2020: 50710,
                         2021: 50873, 2022: 52880, 2023: 52456, 2024: 55617, 2025: 59840}),
         "note": "financial-input-2016-2025.json: total_assets."},
        {"type": "spacer"},
        {"id": "accounts_payable", "label": "Accounts Payable", "type": "input", "indent": 1,
         "values": vals({2020: 880, 2021: 780, 2022: 2117, 2023: 2312, 2024: 2222, 2025: 3630}),
         "min_label": "FY2020"},
        {"id": "salaries_benefits_payroll", "label": "Salaries, Benefits and Payroll Taxes", "type": "input",
         "indent": 1,
         "values": vals({2020: 3163, 2021: 3108, 2022: 3075, 2023: 3133, 2024: 3125, 2025: 3184}),
         "min_label": "FY2020"},
        {"id": "contract_liabilities", "label": "Contract Liabilities", "type": "input", "indent": 1,
         "values": vals({2020: 7545, 2021: 8107, 2022: 8488, 2023: 9190, 2024: 9795, 2025: 11440}),
         "min_label": "FY2020"},
        {"id": "current_maturities_ltd", "label": "Current Maturities of Long-Term Debt", "type": "input",
         "indent": 1,
         "values": vals({2020: 500, 2022: 118, 2023: 168, 2024: 643, 2025: 1168}),
         "min_label": "FY2020",
         "note": "FY2021 not separately disclosed under the FY2022 10-K's presentation (folded into Other current liabilities, ~$6M)."},
        {"id": "other_current_liabilities", "label": "Other Current Liabilities", "type": "input", "indent": 1,
         "values": vals({2020: 1845, 2021: 2002, 2022: 2089, 2023: 2134, 2024: 3635, 2025: 3913}),
         "min_label": "FY2020"},
        {"id": "total_current_liabilities", "label": "Total Current Liabilities", "type": "input", "bold": True,
         "border_top": True,
         "values": vals({2016: 12456, 2017: 12913, 2018: 14398, 2019: 13972, 2020: 13933,
                         2021: 13997, 2022: 15887, 2023: 16937, 2024: 19420, 2025: 23335}),
         "note": "financial-input-2016-2025.json: current_liabilities."},
        {"id": "long_term_debt_net", "label": "Long-Term Debt, Net", "type": "input", "indent": 1,
         "values": vals({2020: 11669, 2021: 11670, 2022: 15429, 2023: 17291, 2024: 19627, 2025: 20532}),
         "min_label": "FY2020"},
        {"id": "total_debt_memo_pre2020", "label": "Total Debt, Net (Selected Financial Data basis, memo)",
         "type": "input", "indent": 1, "memo": True,
         "values": vals({2016: 14282, 2017: 14263, 2018: 14104, 2019: 12654}),
         "min_label": "FY2016", "max_label": "FY2019",
         "note": "Pre-2020 Selected Financial Data 'Total debt, net' concept (includes current maturities); face-BS split into current/long-term portions is only available from FY2020 onward in collected filings."},
        {"id": "accrued_pension_liabilities", "label": "Accrued Pension Liabilities", "type": "input", "indent": 1,
         "values": vals({2020: 12874, 2021: 8319, 2022: 5472, 2023: 6162, 2024: 4791, 2025: 3915}),
         "min_label": "FY2020"},
        {"id": "other_noncurrent_liabilities", "label": "Other Noncurrent Liabilities", "type": "input", "indent": 1,
         "values": vals({2020: 6196, 2021: 5928, 2022: 6826, 2023: 5231, 2024: 5446, 2025: 5337}),
         "min_label": "FY2020"},
        {"id": "total_liabilities", "label": "Total Liabilities", "type": "input", "bold": True, "border_top": True,
         "values": vals({2016: 46083, 2017: 47396, 2018: 43427, 2019: 44357, 2020: 44672,
                         2021: 39914, 2022: 43614, 2023: 45621, 2024: 49284, 2025: 53119}),
         "note": "financial-input-2016-2025.json: total_liabilities."},
        {"type": "spacer"},
        {"id": "common_stock", "label": "Common Stock, $1 Par Value", "type": "input", "indent": 1,
         "values": vals({2020: 279, 2021: 271, 2022: 254, 2023: 240, 2024: 234, 2025: 229}),
         "min_label": "FY2020"},
        {"id": "additional_paid_in_capital", "label": "Additional Paid-In Capital", "type": "input", "indent": 1,
         "values": vals({2020: 221, 2021: 94, 2022: 92, 2023: 0, 2024: 0, 2025: 0}),
         "min_label": "FY2020"},
        {"id": "retained_earnings", "label": "Retained Earnings", "type": "input", "indent": 1,
         "values": vals({2020: 21636, 2021: 21600, 2022: 16943, 2023: 15398, 2024: 14551, 2025: 14034}),
         "min_label": "FY2020"},
        {"id": "aoci", "label": "Accumulated Other Comprehensive Loss", "type": "input", "indent": 1,
         "values": vals({2020: -16121, 2021: -11006, 2022: -8023, 2023: -8803, 2024: -8452, 2025: -7542}),
         "min_label": "FY2020"},
        {"id": "noncontrolling_interest", "label": "Noncontrolling Interests in Subsidiary", "type": "input",
         "indent": 1, "memo": True,
         "values": vals({2020: 23}), "min_label": "FY2020", "max_label": "FY2020"},
        {"id": "total_equity", "label": "Total Equity", "type": "input", "bold": True, "border_top": True,
         "values": vals({2016: 1477, 2017: -776, 2018: 1449, 2019: 3171, 2020: 6038,
                         2021: 10959, 2022: 9266, 2023: 6835, 2024: 6333, 2025: 6721}),
         "note": "financial-input-2016-2025.json: total_equity."},
        {"id": "bs_check", "label": "Balance Check: Assets − Liabilities − Equity (should be ~0)",
         "type": "check", "memo": True,
         "expr": "{total_assets}-{total_liabilities}-{total_equity}"},
    ],
}

bs_block2 = {
    "title": "WORKING CAPITAL ANALYTICS",
    "rows": [
        {"id": "wc_dso", "label": "Days Sales Outstanding", "type": "calc",
         "expr": "{receivables_net}/{IS:total_sales}*365", "fmt": "num1", "memo": True,
         "min_label": "FY2020"},
        {"id": "wc_dio", "label": "Days Inventory Outstanding", "type": "calc",
         "expr": "{inventories}/(0-{IS:total_cost_of_sales})*365", "fmt": "num1", "memo": True,
         "min_label": "FY2020"},
        {"id": "wc_dpo", "label": "Days Payable Outstanding", "type": "calc",
         "expr": "{accounts_payable}/(0-{IS:total_cost_of_sales})*365", "fmt": "num1", "memo": True,
         "min_label": "FY2020"},
        {"id": "wc_ccc", "label": "Cash Conversion Cycle", "type": "calc",
         "expr": "{wc_dso}+{wc_dio}-{wc_dpo}", "fmt": "num1", "memo": True,
         "min_label": "FY2020"},
    ],
}

BS_SHEET = {
    "name": "Balance Sheet", "short": "BS", "kind": "statement",
    "tab_color": "1F4E79", "contents": True,
    "blocks": [bs_block1, bs_block2],
}

# --------------------------------------------------------------------------
# CASH FLOW
# --------------------------------------------------------------------------

cf_block1 = {
    "title": "AS-REPORTED CASH FLOW STATEMENT",
    "rows": [
        {"id": "net_earnings_cf", "label": "Net Earnings (from Income Statement)", "type": "link",
         "ref": "IS:net_earnings", "bold": True},
        {"id": "da", "label": "Depreciation and Amortization", "type": "input", "indent": 1,
         "values": vals({2016: 1215, 2017: 1195, 2018: 1161, 2019: 1189, 2020: 1290,
                         2021: 1364, 2022: 1404, 2023: 1430, 2024: 1559, 2025: 1687}),
         "note": "financial-input-2016-2025.json: depreciation_amortization; cross-validated against SEC CF tables for FY2019-2025."},
        {"id": "sbc", "label": "Stock-Based Compensation", "type": "input", "indent": 1,
         "values": vals({2019: 189, 2020: 221, 2021: 227, 2022: 238, 2023: 265, 2024: 277, 2025: 304}),
         "min_label": "FY2019"},
        {"id": "equity_method_impairment", "label": "Equity Method Investment Impairment", "type": "input",
         "indent": 1, "memo": True,
         "values": vals({2020: 128}), "min_label": "FY2020", "max_label": "FY2020"},
        {"id": "tax_resolution_isgs", "label": "Tax Resolution Related to Former IS&GS Business", "type": "input",
         "indent": 1, "memo": True,
         "values": vals({2020: 55}), "min_label": "FY2020", "max_label": "FY2020"},
        {"id": "deferred_income_taxes_cf", "label": "Deferred Income Taxes", "type": "input", "indent": 1,
         "values": vals({2019: 222, 2020: 5, 2021: -183, 2022: -757, 2023: -498, 2024: -588, 2025: 372}),
         "min_label": "FY2019"},
        {"id": "pension_settlement_charge", "label": "Pension Settlement Charge", "type": "input", "indent": 1,
         "values": vals({2021: 1665, 2022: 1470, 2025: 479}), "min_label": "FY2019"},
        {"id": "impairment_other_charges_cf", "label": "Impairment and Other Charges", "type": "input", "indent": 1,
         "values": vals({2020: 27, 2021: 36, 2022: 100, 2023: 92, 2024: 87, 2025: 66}),
         "min_label": "FY2019"},
        {"id": "reach_forward_losses", "label": "Reach-Forward Losses on Select Programs", "type": "input",
         "indent": 1,
         "values": vals({2023: 45, 2024: 1965, 2025: 1615}), "min_label": "FY2019",
         "note": "Separately disclosed beginning with the FY2023 comparative in the FY2025 10-K; earlier years folded into Other, net."},
        {"id": "gain_property_sale", "label": "Gain on Property Sale", "type": "input", "indent": 1, "memo": True,
         "values": vals({2019: -51}), "min_label": "FY2019", "max_label": "FY2019"},
        {"id": "chg_receivables", "label": "Change in Receivables, Net", "type": "input", "indent": 1,
         "values": vals({2019: 107, 2020: 359, 2021: 15, 2022: -542, 2023: 373, 2024: -219, 2025: -1550}),
         "min_label": "FY2019"},
        {"id": "chg_contract_assets", "label": "Change in Contract Assets", "type": "input", "indent": 1,
         "values": vals({2019: 378, 2020: -451, 2021: -1034, 2022: -1739, 2023: -865, 2024: -109, 2025: -283}),
         "min_label": "FY2019"},
        {"id": "chg_inventories", "label": "Change in Inventories", "type": "input", "indent": 1,
         "values": vals({2019: -622, 2020: 74, 2021: 564, 2022: -107, 2023: -44, 2024: -478, 2025: -286}),
         "min_label": "FY2019"},
        {"id": "chg_accounts_payable", "label": "Change in Accounts Payable", "type": "input", "indent": 1,
         "values": vals({2019: -1098, 2020: -372, 2021: -98, 2022: 1274, 2023: 151, 2024: -93, 2025: 1341}),
         "min_label": "FY2019"},
        {"id": "chg_contract_liabilities", "label": "Change in Contract Liabilities", "type": "input", "indent": 1,
         "values": vals({2019: 563, 2020: 491, 2021: 562, 2022: 381, 2023: 702, 2024: 605, 2025: 1219}),
         "min_label": "FY2019"},
        {"id": "chg_income_taxes", "label": "Change in Income Taxes", "type": "input", "indent": 1,
         "values": vals({2019: -151, 2020: -19, 2021: 45, 2022: 148, 2023: -133, 2024: 131, 2025: -255}),
         "min_label": "FY2019"},
        {"id": "chg_pension_funding", "label": "Pension Funding (Qualified DB / Postretirement Plans)",
         "type": "input", "indent": 1,
         "values": vals({2019: 81, 2020: -1197, 2021: -267, 2022: -412, 2023: -378, 2024: -992, 2025: -415}),
         "min_label": "FY2019"},
        {"id": "other_operating_net", "label": "Other, Net", "type": "input", "indent": 1,
         "values": vals({2019: 274, 2020: 739, 2021: 10, 2022: 612, 2023: -140, 2024: -509, 2025: -754}),
         "min_label": "FY2019"},
        {"id": "cfo_total", "label": "Net Cash Provided by Operating Activities", "type": "input", "bold": True,
         "border_top": True,
         "values": vals({2016: 5189, 2017: 6476, 2018: 3138, 2019: 7311, 2020: 8183,
                         2021: 9221, 2022: 7802, 2023: 7920, 2024: 6972, 2025: 8557}),
         "note": "financial-input-2016-2025.json: cfo."},
        {"type": "spacer"},
        {"id": "capex_ppe", "label": "Capital Expenditures", "type": "input", "indent": 1,
         "values": vals({2016: -1063, 2017: -1177, 2018: -1278, 2019: -1484, 2020: -1766,
                         2021: -1522, 2022: -1670, 2023: -1691, 2024: -1685, 2025: -1649}),
         "note": "financial-input-2016-2025.json: capex_total, sign flipped to match as-reported outflow convention used elsewhere on this sheet."},
        {"id": "acquisitions_businesses", "label": "Acquisitions of Businesses", "type": "input", "indent": 1,
         "memo": True,
         "values": vals({2020: -282}), "min_label": "FY2020", "max_label": "FY2020"},
        {"id": "other_investing_net", "label": "Other, Net", "type": "input", "indent": 1,
         "values": vals({2019: 243, 2020: -244, 2021: 361, 2022: -119, 2023: -3, 2024: -107, 2025: -328}),
         "min_label": "FY2019"},
        {"id": "cfi_total", "label": "Net Cash Used for Investing Activities", "type": "input", "bold": True,
         "border_top": True,
         "values": vals({2019: -1241, 2020: -2010, 2021: -1161, 2022: -1789, 2023: -1694,
                         2024: -1792, 2025: -1977}),
         "min_label": "FY2019"},
        {"type": "spacer"},
        {"id": "repayment_commercial_paper", "label": "Repayment of Commercial Paper, Net", "type": "input",
         "indent": 1, "memo": True,
         "values": vals({2019: -600}), "min_label": "FY2019", "max_label": "FY2019"},
        {"id": "issuance_lt_debt", "label": "Issuance of Long-Term Debt, Net of Related Costs", "type": "input",
         "indent": 1,
         "values": vals({2020: 1131, 2022: 6211, 2023: 1975, 2024: 2970, 2025: 1985}),
         "min_label": "FY2019"},
        {"id": "repayments_lt_debt", "label": "Repayments of Long-Term Debt", "type": "input", "indent": 1,
         "values": vals({2019: -900, 2020: -1650, 2021: -500, 2022: -2250, 2023: -115,
                         2024: -168, 2025: -642}),
         "min_label": "FY2019"},
        {"id": "repurchases_common_stock", "label": "Repurchases of Common Stock", "type": "input", "indent": 1,
         "values": vals({2016: -2096, 2017: -2001, 2018: -1492, 2019: -1200, 2020: -1100,
                         2021: -4087, 2022: -7900, 2023: -6000, 2024: -3700, 2025: -3000}),
         "note": "financial-input-2016-2025.json: buybacks, sign flipped to outflow convention."},
        {"id": "dividends_paid", "label": "Dividends Paid", "type": "input", "indent": 1,
         "values": vals({2016: -2048, 2017: -2163, 2018: -2347, 2019: -2556, 2020: -2764,
                         2021: -2940, 2022: -3016, 2023: -3056, 2024: -3059, 2025: -3131}),
         "note": "financial-input-2016-2025.json: dividends_paid, sign flipped to outflow convention."},
        {"id": "other_financing_net", "label": "Other, Net", "type": "input", "indent": 1,
         "values": vals({2019: -72, 2020: -144, 2021: -89, 2022: -115, 2023: -135,
                         2024: -182, 2025: -154}),
         "min_label": "FY2019"},
        {"id": "cff_total", "label": "Net Cash Used for Financing Activities", "type": "input", "bold": True,
         "border_top": True,
         "values": vals({2019: -5328, 2020: -4527, 2021: -7616, 2022: -7070, 2023: -7331,
                         2024: -4139, 2025: -4942}),
         "min_label": "FY2019"},
        {"type": "spacer"},
        {"id": "net_change_cash", "label": "Net Change in Cash and Cash Equivalents", "type": "input", "bold": True,
         "border_top": True,
         "values": vals({2019: 742, 2020: 1646, 2021: 444, 2022: -1057, 2023: -1105,
                         2024: 1041, 2025: 1638}),
         "min_label": "FY2019"},
        {"id": "cash_beginning", "label": "Cash and Cash Equivalents at Beginning of Year", "type": "input",
         "indent": 1,
         "values": vals({2019: 772, 2020: 1514, 2021: 3160, 2022: 3604, 2023: 2547,
                         2024: 1442, 2025: 2483}),
         "min_label": "FY2019"},
        {"id": "cash_ending", "label": "Cash and Cash Equivalents at End of Year", "type": "input", "bold": True,
         "values": vals({2019: 1514, 2020: 3160, 2021: 3604, 2022: 2547, 2023: 1442,
                         2024: 2483, 2025: 4121}),
         "min_label": "FY2019"},
        {"id": "cf_check", "label": "Cash Walk Check: CFO+CFI+CFF − Net Change (should be ~0)",
         "type": "check", "memo": True,
         "expr": "{cfo_total}+{cfi_total}+{cff_total}-{net_change_cash}",
         "min_label": "FY2019", "max_label": "FY2025"},
        {"id": "cf_bs_tie_check", "label": "Ending Cash vs Balance Sheet Cash (should be ~0)", "type": "check",
         "memo": True,
         "expr": "{cash_ending}-{BS:cash_and_equivalents}",
         "min_label": "FY2019", "max_label": "FY2025"},
    ],
}

cf_block2 = {
    "title": "FREE CASH FLOW ANALYTICS",
    "rows": [
        {"id": "fcf", "label": "Free Cash Flow", "type": "calc", "bold": True,
         "expr": "{cfo_total}+{capex_ppe}", "fmt": "num"},
        {"id": "fcf_yoy", "label": "  YoY Growth", "type": "growth_yoy", "of": "fcf",
         "fmt": "pct", "memo": True},
        {"id": "capex_pct_revenue", "label": "  Capex % of Revenue", "type": "calc",
         "expr": "0-{capex_ppe}/{IS:total_sales}", "fmt": "pct", "memo": True},
        {"id": "fcf_margin", "label": "  FCF Margin", "type": "calc",
         "expr": "{fcf}/{IS:total_sales}", "fmt": "pct", "memo": True},
        {"id": "fcf_conversion", "label": "  FCF Conversion (% of Net Earnings)", "type": "calc",
         "expr": "{fcf}/{IS:net_earnings}", "fmt": "pct", "memo": True},
        {"id": "total_shareholder_returns", "label": "Total Cash Returned to Shareholders", "type": "calc",
         "expr": "0-{dividends_paid}-{repurchases_common_stock}", "fmt": "num", "memo": True},
    ],
}

CF_SHEET = {
    "name": "Cash Flow", "short": "CF", "kind": "statement",
    "tab_color": "1F4E79", "contents": True,
    "blocks": [cf_block1, cf_block2],
}

# --------------------------------------------------------------------------
# SEGMENTS  (incl. geography / customer / contract-type company totals)
# --------------------------------------------------------------------------

SEG_YEARS = list(range(2016, 2026))


def seg_series(lst):
    return {f"FY{y}": v for y, v in zip(SEG_YEARS, lst)}


seg_rev = {
    "Aeronautics": [17769, 19410, 21242, 23693, 26266, 26748, 26987, 27474, 28618, 30257],
    "Missiles and Fire Control": [6608, 7282, 8462, 10131, 11257, 11693, 11317, 11253, 12682, 14450],
    "Rotary and Mission Systems": [13462, 13663, 14250, 15128, 15995, 16789, 16148, 16239, 17264, 17312],
    "Space": [9409, 9605, 9808, 10860, 11880, 11814, 11532, 12605, 12479, 13029],
}
seg_op = {
    "Aeronautics": [1887, 2176, 2272, 2521, 2843, 2799, 2866, 2825, 2523, 2086],
    "Missiles and Fire Control": [1018, 1034, 1248, 1441, 1545, 1648, 1635, 1541, 413, 1989],
    "Rotary and Mission Systems": [906, 902, 1302, 1421, 1615, 1798, 1673, 1865, 1921, 1323],
    "Space": [1289, 980, 1055, 1191, 1149, 1134, 1045, 1158, 1226, 1345],
}
seg_backlog = {
    "Aeronautics": [34182, 35692, 55601, 55636, 56551, 56551, 56630, 60156, 62763, 59435],
    "Missiles and Fire Control": [14704, 17729, 21363, 25796, 29183, 29183, 28735, 32229, 38783, 46650],
    "Rotary and Mission Systems": [28430, 30030, 31320, 34296, 36249, 36249, 34949, 37726, 38117, 47715],
    "Space": [18842, 22042, 22184, 28253, 25148, 25148, 29684, 30456, 36377, 39822],
}
seg_ids = {
    "Aeronautics": "aero", "Missiles and Fire Control": "mfc",
    "Rotary and Mission Systems": "rms", "Space": "space",
}

seg_rev_rows = []
for name, sid in seg_ids.items():
    seg_rev_rows.append({"id": f"seg_{sid}_rev", "label": f"{name} — Sales", "type": "input",
                          "values": seg_series(seg_rev[name])})
seg_rev_rows.append({
    "id": "seg_total_rev", "label": "Total Segment Sales", "type": "subtotal", "bold": True, "border_top": True,
    "children": [f"seg_{sid}_rev" for sid in seg_ids.values()],
})
seg_rev_rows.append({
    "id": "seg_rev_check", "label": "vs IS Total Sales (should be ~0)", "type": "check", "memo": True,
    "expr": "{seg_total_rev}-{IS:total_sales}", "min_label": "FY2017",
    "note": "FY2016 excluded: segment note presented total sales of $47,248M for FY2016 (FY2017 10-K's segment table) vs $47,290M in the consolidated Selected Financial Data basis used for IS:total_sales — a $42M presentation difference documented in segment-history-2016-2025.json.",
})
for name, sid in seg_ids.items():
    seg_rev_rows.append({"id": f"seg_{sid}_mix", "label": f"  {name} % of Total Sales", "type": "calc",
                          "expr": f"{{seg_{sid}_rev}}/{{seg_total_rev}}", "fmt": "pct", "memo": True})
for name, sid in seg_ids.items():
    seg_rev_rows.append({"id": f"seg_{sid}_yoy", "label": f"  {name} YoY Growth", "type": "growth_yoy",
                          "of": f"seg_{sid}_rev", "fmt": "pct", "memo": True})

seg_block1 = {"title": "SEGMENT REVENUE", "rows": seg_rev_rows}

seg_op_rows = []
for name, sid in seg_ids.items():
    seg_op_rows.append({"id": f"seg_{sid}_op", "label": f"{name} — Operating Profit", "type": "input",
                         "values": seg_series(seg_op[name])})
seg_op_rows.append({
    "id": "seg_total_op", "label": "Total Segment Operating Profit", "type": "subtotal", "bold": True,
    "border_top": True,
    "children": [f"seg_{sid}_op" for sid in seg_ids.values()],
})
seg_op_rows.append({"id": "fas_cas_pension_adj", "label": "FAS/CAS Pension Operating Adjustment", "type": "input",
                     "values": seg_series([902, 1613, 1803, 2049, 1876, 1960, 1709, 1660, 1624, 1518])})
seg_op_rows.append({"id": "seg_other_unallocated_net", "label": "Other Unallocated, Net (Corporate)",
                     "type": "input",
                     "values": seg_series([-114, 39, -346, -78, -384, -216, -580, -542, -694, -530]),
                     "note": "Residual bridging segment operating profit + FAS/CAS adjustment to consolidated operating profit; includes stock compensation, severance/restructuring and other corporate items."})
seg_op_rows.append({
    "id": "op_bridge_check", "label": "Bridge to Consolidated Operating Profit (should be ~0)", "type": "check",
    "memo": True,
    "expr": "{seg_total_op}+{fas_cas_pension_adj}+{seg_other_unallocated_net}-{IS:operating_profit}",
})
for name, sid in seg_ids.items():
    seg_op_rows.append({"id": f"seg_{sid}_margin", "label": f"  {name} Operating Margin", "type": "calc",
                         "expr": f"{{seg_{sid}_op}}/{{seg_{sid}_rev}}", "fmt": "pct", "memo": True})

seg_block2 = {"title": "SEGMENT OPERATING PROFIT", "rows": seg_op_rows}

seg_backlog_rows = []
for name, sid in seg_ids.items():
    seg_backlog_rows.append({"id": f"seg_{sid}_backlog", "label": f"{name} — Backlog", "type": "input",
                              "values": seg_series(seg_backlog[name])})
seg_backlog_rows.append({
    "id": "seg_total_backlog", "label": "Total Backlog", "type": "subtotal", "bold": True, "border_top": True,
    "children": [f"seg_{sid}_backlog" for sid in seg_ids.values()],
})
seg_block3 = {"title": "SEGMENT BACKLOG", "rows": seg_backlog_rows}

geo_years = list(range(2019, 2026))


def geo_series(lst):
    return {f"FY{y}": v for y, v in zip(geo_years, lst)}


seg_block4 = {
    "title": "REVENUE BY CONTRACT TYPE / CUSTOMER / GEOGRAPHY (COMPANY TOTAL)",
    "rows": [
        {"id": "fixed_price_sales", "label": "Fixed-Price Contracts", "type": "input",
         "values": geo_series([36205, 39106, 41609, 40969, 40004, 42728, 45200]), "min_label": "FY2019"},
        {"id": "cost_reimbursable_sales", "label": "Cost-Reimbursable Contracts", "type": "input",
         "values": geo_series([23607, 26292, 25435, 25015, 27567, 28315, 29848]), "min_label": "FY2019"},
        {"id": "contract_type_check", "label": "vs IS Total Sales (should be ~0)", "type": "check", "memo": True,
         "expr": "{fixed_price_sales}+{cost_reimbursable_sales}-{IS:total_sales}",
         "min_label": "FY2019", "max_label": "FY2025"},
        {"type": "spacer"},
        {"id": "customer_us_gov", "label": "U.S. Government", "type": "input",
         "values": geo_series([42425, 48468, 48150, 48515, 49423, 52044, 53412]), "min_label": "FY2019"},
        {"id": "customer_international", "label": "International", "type": "input",
         "values": geo_series([16531, 16386, 18439, 16931, 17644, 18515, 21343]), "min_label": "FY2019"},
        {"id": "customer_us_commercial", "label": "U.S. Commercial and Other", "type": "input",
         "values": geo_series([856, 544, 455, 538, 504, 484, 293]), "min_label": "FY2019"},
        {"id": "customer_check", "label": "vs IS Total Sales (should be ~0)", "type": "check", "memo": True,
         "expr": "{customer_us_gov}+{customer_international}+{customer_us_commercial}-{IS:total_sales}",
         "min_label": "FY2019", "max_label": "FY2025"},
        {"type": "spacer"},
        {"id": "geo_united_states", "label": "United States", "type": "input",
         "values": geo_series([43281, 49012, 48605, 49053, 49927, 52528, 53705]), "min_label": "FY2019"},
        {"id": "geo_europe", "label": "Europe", "type": "input",
         "values": geo_series([5928, 6334, 6760, 6267, 7011, 7716, 8805]), "min_label": "FY2019"},
        {"id": "geo_asia_pacific", "label": "Asia Pacific", "type": "input",
         "values": geo_series([5826, 5176, 6108, 5479, 5851, 6241, 7815]), "min_label": "FY2019"},
        {"id": "geo_middle_east", "label": "Middle East", "type": "input",
         "values": geo_series([3944, 3940, 4253, 3796, 3554, 3075, 2864]), "min_label": "FY2019"},
        {"id": "geo_other", "label": "Other", "type": "input",
         "values": geo_series([833, 936, 1318, 1389, 1228, 1483, 1859]), "min_label": "FY2019"},
        {"id": "geo_check", "label": "vs IS Total Sales (should be ~0)", "type": "check", "memo": True,
         "expr": "{geo_united_states}+{geo_europe}+{geo_asia_pacific}+{geo_middle_east}+{geo_other}-{IS:total_sales}",
         "min_label": "FY2019", "max_label": "FY2025"},
    ],
}

SEG_SHEET = {
    "name": "Segments", "short": "SEG", "kind": "statement",
    "tab_color": "548235", "contents": True,
    "blocks": [seg_block1, seg_block2, seg_block3, seg_block4],
}

# --------------------------------------------------------------------------
# DERIVED METRICS  (reused verbatim from the assemble_model.py draft)
# --------------------------------------------------------------------------

DM_SHEET = None
for s in DRAFT["sheets"]:
    if s.get("short") == "DM":
        DM_SHEET = s
        break
if DM_SHEET is None:
    raise SystemExit("Derived Metrics sheet not found in draft model.json")
DM_SHEET["tab_color"] = "7030A0"

# --------------------------------------------------------------------------
# COVER & SOURCES
# --------------------------------------------------------------------------

COVER = {
    "name": "Cover", "kind": "table", "tab_color": "1F4E79", "col_widths": [40, 70],
    "table": [
        [{"text": "Lockheed Martin Corporation (NYSE: LMT)", "bold": True}],
        [],
        [{"text": "Company information", "bold": True}],
        ["Ticker", "LMT"],
        ["Reporting currency", "USD"],
        ["Units", "$ in millions except per-share data"],
        ["Reporting framework", "US GAAP"],
        ["Fiscal year end", "December 31"],
        ["Consolidation scope", "Consolidated"],
        ["Periods covered", "FY2016–FY2025 (annual only; no quarterly data requested)"],
        ["Model date", "2026-09-08"],
        [],
        [{"text": "Color legend", "bold": True}],
        [{"text": "Blue", "fill": "D6E4F0"}, "Hardcoded reported value (as filed / curated input)"],
        [{"text": "Black"}, "Formula or calculation"],
        [{"text": "Green", "fill": "E2EFDA"}, "Cross-sheet link"],
        [{"text": "Grey italic"}, "Memo / commentary / ratio annotation"],
        [{"text": "Red bold (checks)"}, "Check row failing tolerance (|value| > 0.5)"],
        [],
        [{"text": "Data completeness notes", "bold": True}],
        ["FY2016–FY2018", "Headline coverage only (revenue, operating profit, net earnings, D&A, "
                             "aggregate BS totals, CFO, capex, dividends, buybacks) from the curated "
                             "financial-input panel; SEC filings for these years were not among the "
                             "collected source set, so detailed line items are not available."],
        ["FY2019", "Full income statement and cash flow detail available (FY2021 10-K); balance sheet "
                   "detail begins FY2020 (earliest face-BS table collected)."],
        ["FY2020–FY2025", "Full as-reported IS/BS/CF detail, reconciled across overlapping filing "
                              "vintages using a most-recent-filing-wins convention for any reclassified "
                              "figures (see Sources tab)."],
        ["Segments", "Full FY2016–FY2025 coverage for the four reportable segments (Aeronautics, "
                     "Missiles and Fire Control, Rotary and Mission Systems, Space); geography/customer/"
                     "contract-type detail covers FY2019–FY2025."],
        [],
        [{"text": "Sheet directory", "bold": True}],
        ["Income Statement", "IS tab"],
        ["Balance Sheet", "BS tab"],
        ["Cash Flow", "CF tab"],
        ["Segments", "SEG tab"],
        ["Derived Metrics", "DM tab"],
        ["Sources", ""],
    ],
}

SOURCES = {
    "name": "Sources", "kind": "table", "col_widths": [26, 70, 22],
    "table": [
        [{"text": "Sources and data provenance", "bold": True}],
        [],
        [{"text": "Source", "bold": True}, {"text": "Description", "bold": True},
         {"text": "Coverage", "bold": True}],
        ["financial-input-2016-2025.json",
         "Curated Tier-1 panel: revenue, operating profit, net earnings, D&A, cash & BS aggregates, "
         "CFO, capex, dividends, buybacks.", "FY2016–FY2025"],
        ["segment-history-2016-2025.json",
         "Curated Tier-1 segment panel: sales, operating profit, backlog by segment; FAS/CAS pension "
         "operating bridge.", "FY2016–FY2025"],
        ["financial-metrics-2016-2025.md",
         "Derived Tier-4 ratio panel (cash conversion, returns, liquidity, growth, etc.) — reused "
         "verbatim on the Derived Metrics tab.", "FY2016–FY2025 (sparse pre-2019)"],
        ["sources/.../ten_k/LMT/FY2025/.../raw/source.html", "FY2025 10-K (filed 2026): as-reported IS, "
         "BS, CF, EPS/WASO detail, segment note, geography/customer/contract-type tables.",
         "FY2025 native; FY2024/FY2023 comparatives"],
        ["sources/.../ten_k/LMT/FY2024/.../raw/source.html", "FY2024 10-K: as-reported IS, BS, CF detail; "
         "segment note.", "FY2024 native; FY2023/FY2022 comparatives"],
        ["sources/.../ten_k/LMT/FY2023/.../raw/source.html", "FY2023 10-K: as-reported IS, BS, CF detail; "
         "segment note.", "FY2023 native; FY2022/FY2021 comparatives"],
        ["sources/.../ten_k/LMT/FY2022/.../raw/source.html", "FY2022 10-K: as-reported IS, BS, CF detail; "
         "segment note; 5-year Selected Financial Data table.", "FY2022 native; FY2021/FY2020 comparatives; "
         "5-yr data FY2018–FY2022"],
        ["sources/.../ten_k/LMT/FY2021/.../raw/source.html", "FY2021 10-K: as-reported IS, BS, CF detail; "
         "segment note; 5-year Selected Financial Data table.", "FY2021 native; FY2020/FY2019 comparatives; "
         "5-yr data FY2017–FY2021"],
        [],
        [{"text": "Reconciliation policy", "bold": True}],
        ["Most-recent-filing-wins", "When the same fiscal year's figures differ across filing vintages due "
         "to reclassification (e.g., FY2022 Products cost of sales: $(49,577)M in the native FY2022 10-K "
         "vs $(49,357)M in the FY2023/FY2024 10-K comparative columns, a ~$220M shift into 'Other "
         "unallocated, net'), this model uses the value from the most recently filed presentation of that "
         "year, for consistency with the company's current disclosure basis. Column totals tie under either "
         "convention.", ""],
        [],
        [{"text": "Excluded inputs", "bold": True}],
        ["research/companies/US/LMT-lockheed-martin/data/*.md", "Deep-research narrative notes — used "
         "only as background context, never as a numeric source, per skill policy.", ""],
        ["financial-input-2021-2025.json / segment-history-2021-2025.json",
         "Byte-identical to the 2016-2025 versions (verified via diff); not used separately.", ""],
        ["sec-cleaned directory", "Not present for LMT; skipped.", ""],
    ],
}

# --------------------------------------------------------------------------
# ASSEMBLE
# --------------------------------------------------------------------------

model = {
    "company": COMPANY,
    "periods": PERIODS,
    "sheets": [COVER, IS_SHEET, BS_SHEET, CF_SHEET, SEG_SHEET, DM_SHEET, SOURCES],
}

out_path = WORKDIR / "model.json"
out_path.write_text(json.dumps(model, indent=2, ensure_ascii=False), encoding="utf-8")

# quick internal sanity report
for s in model["sheets"]:
    if s.get("kind") == "statement":
        nrows = sum(len(b.get("rows", [])) for b in s["blocks"])
        print(f"{s['short']:5s} {s['name']:20s} blocks={len(s['blocks'])} rows={nrows}")
print("wrote", out_path)
