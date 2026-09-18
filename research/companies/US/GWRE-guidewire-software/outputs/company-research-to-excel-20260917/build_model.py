#!/usr/bin/env python3
"""
build_model.py — Build model.json for Guidewire Software, Inc. (GWRE)
from SEC filing tables in tables.json.

Revenue label history:
  FY2015–FY2018 (original): License and other, Maintenance, Services
  FY2019 (original):        License and subscription, Maintenance, Services
  FY2020+ (restated):       Subscription and support, License, Services

The FY2020 10-K restated FY2019/FY2018 into the new 3-segment categories.
For FY2017 and earlier, we map old categories as:
  "License and other" → license_rev / license_cost / license_gp
  "Maintenance"       → subscription_and_support_rev / cost / gp
  "Services"          → services_rev / cost / gp

This is the best mapping because "Maintenance" became "Subscription and support"
when Guidewire shifted to cloud, and "License and other" maps to "License".
"""

import json, re, os, sys
from pathlib import Path
from collections import OrderedDict

# ---------- paths ----------
BASE = Path(__file__).resolve().parent
TABLES_PATH = BASE / "tables.json"
OUTPUT_PATH = BASE / "model.json"

# ---------- table indices ----------
ANNUAL_IS = {
    "FY2017": 33, "FY2018": 109, "FY2019": 179, "FY2020": 251,
    "FY2021": 323, "FY2022": 392, "FY2023": 466, "FY2024": 539,
    "FY2025": 763, "FY2026": 1002,
}
ANNUAL_BS = {
    "FY2017": 32, "FY2018": 108, "FY2019": 178, "FY2020": 250,
    "FY2021": 322, "FY2022": 391, "FY2023": 465, "FY2024": 538,
    "FY2025": 762, "FY2026": 1001,
}
ANNUAL_CF = {
    "FY2017": 36, "FY2018": 112, "FY2019": 182, "FY2020": 254,
    "FY2021": 326, "FY2022": 395, "FY2023": 469, "FY2024": 542,
    "FY2025": 766, "FY2026": 1005,
}

QUARTERLY_IS = {
    "1Q2024": 602, "2Q2024": 642, "3Q2024": 694,
    "1Q2025": 825, "2Q2025": 872, "3Q2025": 928,
    "1Q2026": 1065, "2Q2026": 1113, "3Q2026": 1172,
}
QUARTERLY_BS = {
    "1Q2024": 601, "2Q2024": 641, "3Q2024": 693,
    "1Q2025": 824, "2Q2025": 871, "3Q2025": 927,
    "1Q2026": 1064, "2Q2026": 1112, "3Q2026": 1171,
}
QUARTERLY_CF = {
    "1Q2024": 606, "2Q2024": 646, "3Q2024": 698,
    "1Q2025": 829, "2Q2025": 876, "3Q2025": 932,
    "1Q2026": 1069, "2Q2026": 1117, "3Q2026": 1176,
}

# Geographic revenue tables in FY2026 10-K (tables 1009, 1010, 1011)
GEO_REV_TABLES = {
    "FY2026": 1009, "FY2025": 1010, "FY2024": 1011,
}

# ---------- FY period mapping for annual tables ----------
# Each annual 10-K IS/CF has 3 years; BS has 2 years.
# The first data row contains the year numbers.
# FY year N means fiscal year ended July 31 of year N.

FY_LABELS = [f"FY{y}" for y in range(2015, 2027)]
Q_LABELS = [
    "1Q2024", "2Q2024", "3Q2024",
    "1Q2025", "2Q2025", "3Q2025",
    "1Q2026", "2Q2026", "3Q2026",
]

# Quarter end dates
Q_END_DATES = {
    "1Q2024": "October 31, 2023", "2Q2024": "January 31, 2024", "3Q2024": "April 30, 2024",
    "1Q2025": "October 31, 2024", "2Q2025": "January 31, 2025", "3Q2025": "April 30, 2025",
    "1Q2026": "October 31, 2025", "2Q2026": "January 31, 2026", "3Q2026": "April 30, 2026",
}

# ---------- value parsing ----------
def parse_value(v):
    """Parse a cell value from tables.json into a numeric value or None."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, str):
        v = v.strip()
        if v in ("", "—", "—", "$—", "—"):
            return None
        # Handle "$(...)" negative format
        m = re.match(r'^\$?\(([0-9,\.]+)\)$', v)
        if m:
            return -float(m.group(1).replace(",", ""))
        # Handle "(...)" negative format
        m = re.match(r'^\(([0-9,\.]+)\)$', v)
        if m:
            return -float(m.group(1).replace(",", ""))
        # Handle regular dollar amounts
        v2 = v.replace("$", "").replace(",", "").strip()
        if v2 == "":
            return None
        try:
            return int(v2) if "." not in v2 else float(v2)
        except ValueError:
            return None
    return None


def normalize_label(label):
    """Normalize a row label for matching."""
    if not isinstance(label, str):
        return str(label).strip().lower()
    s = label.strip().lower()
    # Remove trailing notes like "(1)", "(2)" etc.
    s = re.sub(r'\s*\(\d+\)\s*$', '', s)
    # Remove leading/trailing punctuation and extra spaces
    s = s.rstrip(':').strip()
    return s


def reassemble_row_values(row, num_periods):
    """
    Parse a table row into (label, [value_per_period]).

    Handles the common tables.json issue where negative values in parentheses
    are split across multiple cells, e.g.:
        ['Income (loss)', 1471, '(15,624', ')', 21861, '', '']
    should yield values [1471, -15624, 21861].

    Returns (label_string, list_of_values) where list_of_values has length num_periods.
    Each value is numeric or None.
    """
    if not row:
        return ("", [None] * num_periods)

    label = row[0]
    cells = row[1:]  # Everything after the label

    values = []
    i = 0
    while i < len(cells):
        cell = cells[i]

        # Skip trailing empty strings
        if isinstance(cell, str) and cell.strip() == '':
            i += 1
            continue

        # If it's a bare closing paren, skip (was already consumed)
        if isinstance(cell, str) and cell.strip() == ')':
            i += 1
            continue

        # If it's a number, take it directly
        if isinstance(cell, (int, float)):
            values.append(cell)
            i += 1
            continue

        if isinstance(cell, str):
            s = cell.strip()

            # Check for split negative: starts with "(" or "$(" but doesn't end with ")"
            if (s.startswith('(') or s.startswith('$(')) and not s.endswith(')'):
                # Look ahead for the closing paren
                combined = s
                j = i + 1
                while j < len(cells):
                    next_cell = str(cells[j]).strip()
                    combined += next_cell
                    j += 1
                    if ')' in next_cell:
                        break
                val = parse_value(combined)
                values.append(val)
                i = j
                continue

            # Regular string value
            val = parse_value(s)
            if val is not None:
                values.append(val)
            else:
                # Could be a dash or other null
                values.append(None)
            i += 1
            continue

        i += 1

    # Pad or trim to num_periods
    while len(values) < num_periods:
        values.append(None)

    return (label, values[:num_periods])


# ---------- extraction helpers ----------
def extract_annual_is(table, filing_fy):
    """Extract IS data from an annual 10-K IS table.
    Returns dict: {period_label: {field_id: value}}
    Uses reassemble_row_values to handle split-cell negative values.
    """
    rows = table["rows"]
    # First row should contain year numbers
    year_row = rows[0]
    years = []
    for c in year_row:
        if isinstance(c, int) and 2000 <= c <= 2030:
            years.append(c)

    if not years:
        return {}

    num_periods = len(years)
    periods = [f"FY{y}" for y in years]
    result = {p: {} for p in periods}

    section = None

    for row in rows[1:]:
        if not row or not isinstance(row[0], str):
            continue
        raw_label = row[0].strip()
        label = normalize_label(raw_label)

        # Section headers
        if label in ("revenue", "revenues"):
            section = "revenue"
            continue
        if label in ("cost of revenue", "cost of revenues"):
            section = "cost"
            continue
        if label in ("gross profit",):
            section = "gross_profit"
            continue
        if label in ("operating expenses",):
            section = "opex"
            continue
        if label.startswith("net income") and "per share" in label:
            section = "eps"
            continue
        if label.startswith("shares used") or label.startswith("weighted"):
            section = "shares"
            continue
        if label.startswith("earnings per share"):
            section = "eps"
            continue

        # Map label to field_id
        field_id = None

        if section == "revenue":
            if "subscription and support" in label:
                field_id = "subscription_and_support_rev"
            elif "license and subscription" in label:
                field_id = "subscription_and_support_rev"
            elif "license and other" in label:
                field_id = "license_rev"
            elif label == "license":
                field_id = "license_rev"
            elif "maintenance" in label:
                field_id = "subscription_and_support_rev"
            elif "services" in label:
                field_id = "services_rev"
            elif "total revenue" in label or "total revenues" in label:
                field_id = "total_revenue"

        elif section == "cost":
            if "subscription and support" in label:
                field_id = "subscription_and_support_cost"
            elif "license and subscription" in label:
                field_id = "subscription_and_support_cost"
            elif "license and other" in label:
                field_id = "license_cost"
            elif label == "license":
                field_id = "license_cost"
            elif "maintenance" in label:
                field_id = "subscription_and_support_cost"
            elif "services" in label:
                field_id = "services_cost"
            elif "total cost" in label:
                field_id = "total_cost_of_revenue"

        elif section == "gross_profit":
            if "subscription and support" in label:
                field_id = "subscription_and_support_gp"
            elif "license and subscription" in label:
                field_id = "subscription_and_support_gp"
            elif "license and other" in label:
                field_id = "license_gp"
            elif label == "license":
                field_id = "license_gp"
            elif "maintenance" in label:
                field_id = "subscription_and_support_gp"
            elif "services" in label:
                field_id = "services_gp"
            elif "total gross profit" in label:
                field_id = "total_gross_profit"

        elif section == "opex":
            if "research and development" in label:
                field_id = "research_and_development"
            elif "sales and marketing" in label:
                field_id = "sales_and_marketing"
            elif "general and administrative" in label:
                field_id = "general_and_administrative"
            elif "total operating" in label:
                field_id = "total_operating_expenses"

        elif section == "eps":
            if label in ("basic",):
                field_id = "basic_eps"
            elif label in ("diluted",):
                field_id = "diluted_eps"
            elif "basic and diluted" in label:
                field_id = "basic_and_diluted_eps"

        elif section == "shares":
            if label in ("basic",):
                field_id = "waso_basic"
            elif label in ("diluted",):
                field_id = "waso_diluted"
            elif "basic and diluted" in label:
                field_id = "waso_basic_and_diluted"

        if field_id is None:
            if "income" in label and "from operations" in label:
                field_id = "operating_income"
            elif label == "income from operations":
                field_id = "operating_income"
            elif "interest income" in label:
                field_id = "interest_income"
            elif "interest expense" in label:
                field_id = "interest_expense"
            elif "other income" in label or "other expense" in label:
                field_id = "other_income_expense"
            elif ("income" in label or "loss" in label) and "before" in label and ("provision" in label or "tax" in label):
                field_id = "income_before_taxes"
            elif "provision for" in label or "benefit from" in label:
                if "income tax" in label or "tax" in label:
                    field_id = "income_tax_expense"
            elif label.startswith("net income") or label.startswith("net loss"):
                if "per share" not in label:
                    field_id = "net_income"

        if field_id is None:
            continue

        # Use reassemble_row_values to handle split negative values
        _, vals = reassemble_row_values(row, num_periods)

        # Handle "basic and diluted" combo fields
        if field_id == "basic_and_diluted_eps":
            for i, period in enumerate(periods):
                if vals[i] is not None:
                    result[period]["basic_eps"] = vals[i]
                    result[period]["diluted_eps"] = vals[i]
        elif field_id == "waso_basic_and_diluted":
            for i, period in enumerate(periods):
                if vals[i] is not None:
                    result[period]["waso_basic"] = vals[i]
                    result[period]["waso_diluted"] = vals[i]
        else:
            for i, period in enumerate(periods):
                if vals[i] is not None:
                    result[period][field_id] = vals[i]

    return result


def extract_annual_bs(table, filing_fy):
    """Extract BS data from an annual 10-K BS table.
    Returns dict: {period_label: {field_id: value}}
    """
    rows = table["rows"]
    headers = table["headers"]

    # Determine period labels from headers
    # BS headers like "July 31, 2026", "July 31, 2025"
    periods = []
    for h in headers:
        if isinstance(h, str):
            m = re.search(r'(\d{4})', h)
            if m:
                periods.append(f"FY{m.group(1)}")

    if not periods:
        # Try from first row
        for c in rows[0]:
            if isinstance(c, str):
                m = re.search(r'(\d{4})', c)
                if m:
                    yr = int(m.group(1))
                    if 2000 <= yr <= 2030:
                        periods.append(f"FY{yr}")

    if not periods:
        return {}

    result = {p: {} for p in periods}

    # Map labels
    section = None  # "current_assets", "noncurrent_assets", "current_liabilities", etc.

    for row in rows:
        if not row or not isinstance(row[0], str):
            continue
        raw_label = row[0].strip()
        label = normalize_label(raw_label)

        # Skip pure section headers
        if label in ("assets", "liabilities and stockholders' equity",
                      "liabilities and stockholders equity",
                      "commitments and contingencies",
                      "stockholders' equity", "stockholders equity"):
            continue
        if label.startswith("commitments and contingenc"):
            continue

        # Section detection
        if "current assets" in label:
            section = "current_assets"
            continue
        if "current liabilities" in label:
            section = "current_liabilities"
            continue
        if "stockholders" in label and "equity" in label and "total" not in label:
            section = "equity"
            continue

        field_id = None

        # Current Assets
        if "cash and cash equiv" in label:
            field_id = "cash_and_equivalents"
        elif "short-term investment" in label or "short term investment" in label:
            field_id = "short_term_investments"
        elif "accounts receivable" in label and "unbilled" not in label:
            field_id = "accounts_receivable"
        elif "unbilled accounts receivable" in label:
            if section == "current_assets":
                field_id = "unbilled_ar_current"
            else:
                field_id = "unbilled_ar_noncurrent"
        elif "prepaid" in label and "current" in label:
            field_id = "prepaid_and_other_current"
        elif "prepaid" in label and section == "current_assets":
            field_id = "prepaid_and_other_current"
        elif "total current assets" in label:
            field_id = "total_current_assets"
        elif "long-term investment" in label or "long term investment" in label:
            field_id = "long_term_investments"
        elif "property and equipment" in label:
            field_id = "property_and_equipment"
        elif "operating lease" in label and "asset" in label:
            field_id = "operating_lease_assets"
        elif "intangible" in label:
            field_id = "intangible_assets"
        elif "goodwill" in label:
            field_id = "goodwill"
        elif "deferred tax" in label and "asset" in label:
            field_id = "deferred_tax_assets"
        elif "deferred tax" in label and section not in ("current_liabilities",):
            field_id = "deferred_tax_assets"
        elif "other assets" in label and "total" not in label:
            field_id = "other_assets"
        elif label == "total assets":
            field_id = "total_assets"

        # Current Liabilities
        elif "accounts payable" in label:
            field_id = "accounts_payable"
        elif "accrued employee" in label or "accrued compensation" in label:
            field_id = "accrued_employee_compensation"
        elif "deferred revenue" in label or "deferred revenues" in label:
            if section == "current_liabilities":
                field_id = "deferred_revenue_current"
            else:
                field_id = "deferred_revenue_noncurrent"
        elif "other current liabilities" in label:
            field_id = "other_current_liabilities"
        elif "total current liabilities" in label:
            field_id = "total_current_liabilities"
        elif "lease liabilit" in label:
            field_id = "lease_liabilities"
        elif "convertible" in label and "note" in label:
            field_id = "convertible_notes"
        elif "other liabilities" in label and "total" not in label:
            field_id = "other_liabilities"
        elif "total liabilities" in label and "equity" not in label:
            field_id = "total_liabilities"

        # Equity
        elif "common stock" in label:
            field_id = "common_stock"
        elif "additional paid" in label:
            field_id = "additional_paid_in_capital"
        elif "accumulated other comprehensive" in label:
            field_id = "aoci"
        elif "retained earnings" in label or "accumulated deficit" in label:
            field_id = "retained_earnings"
        elif "total stockholders" in label:
            field_id = "total_stockholders_equity"
        elif "total liabilities and" in label:
            field_id = "total_liabilities_and_equity"

        if field_id is None:
            continue

        _, vals = reassemble_row_values(row, len(periods))
        for i, period in enumerate(periods):
            if vals[i] is not None:
                result[period][field_id] = vals[i]

    return result


def extract_annual_cf(table, filing_fy):
    """Extract CF data from an annual 10-K CF table.
    Returns dict: {period_label: {field_id: value}}
    """
    rows = table["rows"]

    # First row has year numbers
    year_row = rows[0]
    years = []
    for c in year_row:
        if isinstance(c, int) and 2000 <= c <= 2030:
            years.append(c)

    if not years:
        return {}

    num_periods = len(years)
    periods = [f"FY{y}" for y in years]
    result = {p: {} for p in periods}

    section = None  # "cfo", "cfi", "cff"

    for row in rows[1:]:
        if not row or not isinstance(row[0], str):
            continue
        raw_label = row[0].strip()
        label = normalize_label(raw_label)

        # Section headers (must be "CASH FLOWS FROM..." not "Net cash...")
        if "operating activities" in label and "net cash" not in label:
            section = "cfo"
            continue
        if "investing activities" in label and "net cash" not in label:
            section = "cfi"
            continue
        if "financing activities" in label and "net cash" not in label:
            section = "cff"
            continue
        if "adjustments to reconcile" in label:
            continue
        if "changes in operating" in label:
            continue
        if "supplemental" in label:
            break  # Stop at supplemental disclosures

        field_id = None

        # CFO items
        if section == "cfo":
            if label.startswith("net income") or label.startswith("net loss"):
                field_id = "cf_net_income"
            elif "depreciation and amortization" in label:
                field_id = "depreciation_and_amortization"
            elif "amortization of debt" in label:
                field_id = "amortization_of_debt_costs"
            elif "amortization of contract" in label:
                field_id = "amortization_of_contract_costs"
            elif "stock-based compensation" in label or "stock based compensation" in label:
                field_id = "stock_based_compensation"
            elif "allowance" in label or "credit loss" in label or "bad debt" in label or "revenue reserve" in label:
                field_id = "changes_allowances"
            elif "deferred" in label and ("tax" in label or "income tax" in label):
                field_id = "deferred_income_tax"
            elif "amortization of premium" in label or "accretion of discount" in label:
                field_id = "amortization_of_premium_on_securities"
            elif "gain" in label and "strategic" in label and "sale" in label:
                field_id = "gains_losses_strategic_investments"
            elif ("loss" in label or "gain" in label) and "strategic" in label and "sale" in label:
                field_id = "gains_losses_strategic_investments"
            elif "fair value" in label and "strategic" in label:
                field_id = "changes_fair_value_strategic"
            elif "loss on retirement" in label:
                field_id = "loss_on_retirement_of_debt"
            elif "accelerated depreciation" in label and "lease" in label:
                field_id = "accelerated_depreciation_lease"
            elif "gain from lease" in label:
                field_id = "gain_from_lease_assignment"
            elif "excess tax benefit" in label:
                field_id = "excess_tax_benefit"
            elif "other non-cash" in label or "other non cash" in label:
                field_id = "other_noncash_items"
            elif "accounts receivable" in label and "unbilled" not in label:
                field_id = "change_accounts_receivable"
            elif "unbilled" in label:
                field_id = "change_unbilled_ar"
            elif "prepaid" in label or ("other assets" in label and "operating" not in label):
                field_id = "change_prepaid_and_other"
            elif "operating lease" in label and "asset" in label:
                field_id = "change_operating_lease_assets"
            elif "accounts payable" in label:
                field_id = "change_accounts_payable"
            elif "accrued" in label and ("employee" in label or "compensation" in label):
                field_id = "change_accrued_compensation"
            elif "deferred revenue" in label:
                field_id = "change_deferred_revenue"
            elif "lease liabilit" in label:
                field_id = "change_lease_liabilities"
            elif "other liabilit" in label:
                field_id = "change_other_liabilities"
            elif "net cash" in label:
                field_id = "cfo_total"

        # CFI items
        elif section == "cfi":
            if "purchases of available" in label or "purchase of available" in label:
                field_id = "purchases_of_afs_securities"
            elif ("maturities" in label or "sales" in label) and "available" in label:
                field_id = "maturities_sales_afs_securities"
            elif "sales of available" in label:
                field_id = "maturities_sales_afs_securities"
            elif "purchase" in label and "property" in label:
                field_id = "purchases_of_ppe"
            elif "capitalized software" in label:
                field_id = "capitalized_software"
            elif "acquisition" in label and "strategic" in label:
                field_id = "acquisition_strategic_investments"
            elif "purchase" in label and "strategic" in label:
                field_id = "acquisition_strategic_investments"
            elif "strategic investment" in label and "purchase" not in label and "acquisition" not in label:
                if "sale" not in label:
                    field_id = "acquisition_strategic_investments"
            elif "sale of strategic" in label or "sale of strategic" in label:
                field_id = "sale_strategic_investments"
            elif "acquisition" in label and ("business" in label or "net of" in label):
                field_id = "acquisitions_net_of_cash"
            elif "net cash" in label:
                field_id = "cfi_total"

        # CFF items
        elif section == "cff":
            if "proceeds" in label and "convertible" in label:
                field_id = "proceeds_convertible_notes"
            elif "payment" in label and "retirement" in label and "convertible" in label:
                field_id = "payment_retirement_notes"
            elif "payment" in label and "maturity" in label and "convertible" in label:
                field_id = "payment_maturity_notes"
            elif "purchase of capped call" in label or "capped calls" in label:
                field_id = "purchase_capped_calls"
            elif "revolving credit" in label:
                field_id = "payment_revolving_credit"
            elif "proceeds" in label and "common stock" in label and "net of" in label:
                field_id = "proceeds_common_stock_net"
            elif "proceeds" in label and "employee stock" in label:
                field_id = "proceeds_espp"
            elif "proceeds" in label and ("exercise" in label or "stock option" in label):
                field_id = "proceeds_stock_options"
            elif "proceeds" in label and "common stock" in label:
                field_id = "proceeds_stock_options"
            elif "repurchase" in label and ("common stock" in label or "retirement" in label):
                field_id = "repurchase_stock"
            elif "taxes remitted" in label:
                field_id = "taxes_remitted_rsu"
            elif "excess tax benefit" in label:
                field_id = "excess_tax_benefit_financing"
            elif "net cash" in label:
                field_id = "cff_total"

        # Items outside sections
        if field_id is None:
            if "effect of foreign exchange" in label or "effect of exchange" in label:
                field_id = "fx_effect"
            elif "net increase" in label or "net decrease" in label:
                field_id = "net_change_in_cash"
            elif "beginning of" in label or "beginning of year" in label:
                field_id = "cash_beginning"
            elif "end of" in label or "end of year" in label:
                field_id = "cash_ending"

        if field_id is None:
            continue

        _, vals = reassemble_row_values(row, num_periods)
        for i, period in enumerate(periods):
            if vals[i] is not None:
                result[period][field_id] = vals[i]

    return result


def extract_quarterly_is(table, filing_q):
    """Extract quarterly IS data. Use only the quarter-only columns (Three Months Ended)."""
    rows = table["rows"]
    headers = table["headers"]

    # Determine how many periods there are
    # 1Q tables: 2 columns (current quarter, prior year same quarter)
    # 2Q tables: 4 columns (3mo curr, 3mo prev, 6mo curr, 6mo prev)
    # 3Q tables: 4 columns (3mo curr, 3mo prev, 9mo curr, 9mo prev)

    # Parse headers to find "Three Months Ended" vs "Six/Nine Months Ended"
    header_text = " ".join(str(h) for h in headers).lower()
    has_ytd = "six months" in header_text or "nine months" in header_text

    # Find the year row
    year_row = None
    for r in rows[:5]:
        years_in_row = [c for c in r if isinstance(c, int) and 2000 <= c <= 2030]
        if len(years_in_row) >= 2:
            year_row = r
            break

    if year_row is None:
        return {}

    # For quarterly IS, we want the first 2 columns (3-month only)
    years_found = [c for c in year_row if isinstance(c, int) and 2000 <= c <= 2030]

    # Determine quarter number from filing_q
    q_num = int(filing_q[0])  # 1, 2, or 3
    fy_year = int(filing_q[2:6])

    # The current quarter's FY
    current_q = filing_q  # e.g. "1Q2026"
    # Prior year same quarter
    prior_q = f"{q_num}Q{fy_year - 1}"  # e.g. "1Q2025"

    periods = [current_q, prior_q]
    # Only use first 2 data columns (quarter-only)
    col_indices = [0, 1]  # columns after label

    result = {p: {} for p in periods}

    section = None

    for row in rows:
        if not row or not isinstance(row[0], str):
            continue
        raw_label = row[0].strip()
        label = normalize_label(raw_label)

        if label in ("revenue", "revenues"):
            section = "revenue"
            continue
        if label in ("cost of revenue", "cost of revenues"):
            section = "cost"
            continue
        if label in ("gross profit",):
            section = "gross_profit"
            continue
        if label in ("operating expenses",):
            section = "opex"
            continue
        if label.startswith("net income") and "per share" in label:
            section = "eps"
            continue
        if label.startswith("shares used") or label.startswith("weighted"):
            section = "shares"
            continue

        field_id = None

        if section == "revenue":
            if "subscription and support" in label:
                field_id = "subscription_and_support_rev"
            elif label == "license":
                field_id = "license_rev"
            elif "services" in label:
                field_id = "services_rev"
            elif "total revenue" in label:
                field_id = "total_revenue"
        elif section == "cost":
            if "subscription and support" in label:
                field_id = "subscription_and_support_cost"
            elif label == "license":
                field_id = "license_cost"
            elif "services" in label:
                field_id = "services_cost"
            elif "total cost" in label:
                field_id = "total_cost_of_revenue"
        elif section == "gross_profit":
            if "subscription and support" in label:
                field_id = "subscription_and_support_gp"
            elif label == "license":
                field_id = "license_gp"
            elif "services" in label:
                field_id = "services_gp"
            elif "total gross profit" in label:
                field_id = "total_gross_profit"
        elif section == "opex":
            if "research and development" in label:
                field_id = "research_and_development"
            elif "sales and marketing" in label:
                field_id = "sales_and_marketing"
            elif "general and administrative" in label:
                field_id = "general_and_administrative"
            elif "total operating" in label:
                field_id = "total_operating_expenses"
        elif section == "eps":
            if label == "basic":
                field_id = "basic_eps"
            elif label == "diluted":
                field_id = "diluted_eps"
        elif section == "shares":
            if label == "basic":
                field_id = "waso_basic"
            elif label == "diluted":
                field_id = "waso_diluted"

        if field_id is None:
            if "income" in label and "from operations" in label:
                field_id = "operating_income"
            elif "interest income" in label:
                field_id = "interest_income"
            elif "interest expense" in label:
                field_id = "interest_expense"
            elif "other income" in label or "other expense" in label:
                field_id = "other_income_expense"
            elif ("income" in label or "loss" in label) and "before" in label and ("provision" in label or "tax" in label):
                field_id = "income_before_taxes"
            elif "provision for" in label or "benefit from" in label:
                if "income tax" in label or "tax" in label:
                    field_id = "income_tax_expense"
            elif label.startswith("net income") or label.startswith("net loss"):
                if "per share" not in label:
                    field_id = "net_income"

        if field_id is None:
            continue

        for idx, period in enumerate(periods):
            col = col_indices[idx]
            if col + 1 < len(row):
                val = parse_value(row[col + 1])
                if val is not None:
                    result[period][field_id] = val

    return result


def extract_quarterly_bs(table, filing_q):
    """Extract quarterly BS data. Use only the first column (quarter-end)."""
    rows = table["rows"]
    headers = table["headers"]

    # Parse headers for dates
    periods = []
    for h in headers:
        if isinstance(h, str):
            # Match patterns like "October 31, 2025" or "July 31, 2025"
            m = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+,?\s+(\d{4})', h)
            if m:
                month = m.group(1)
                year = int(m.group(2))
                # Map to quarter label
                month_to_q = {
                    "October": ("1Q", 1), "January": ("2Q", 0),
                    "April": ("3Q", 0), "July": ("FY", 0),
                }
                if month in month_to_q:
                    prefix, year_offset = month_to_q[month]
                    if prefix == "FY":
                        periods.append(f"FY{year}")
                    else:
                        periods.append(f"{prefix}{year + year_offset}")
                else:
                    periods.append(f"UNK{year}")

    if not periods:
        return {}

    result = {p: {} for p in periods}

    section = None

    for row in rows:
        if not row or not isinstance(row[0], str):
            continue
        raw_label = row[0].strip()
        label = normalize_label(raw_label)

        if label in ("assets",):
            continue
        if "liabilities and stockholders" in label:
            continue
        if label.startswith("commitments and contingenc"):
            continue
        if "current assets" in label:
            section = "current_assets"
            continue
        if "current liabilities" in label:
            section = "current_liabilities"
            continue
        if "stockholders" in label and "equity" in label and "total" not in label:
            section = "equity"
            continue

        field_id = None

        if "cash and cash equiv" in label:
            field_id = "cash_and_equivalents"
        elif "short-term investment" in label:
            field_id = "short_term_investments"
        elif "accounts receivable" in label and "unbilled" not in label:
            field_id = "accounts_receivable"
        elif "unbilled accounts receivable" in label:
            if section == "current_assets":
                field_id = "unbilled_ar_current"
            else:
                field_id = "unbilled_ar_noncurrent"
        elif "prepaid" in label:
            field_id = "prepaid_and_other_current"
        elif "total current assets" in label:
            field_id = "total_current_assets"
        elif "long-term investment" in label:
            field_id = "long_term_investments"
        elif "property and equipment" in label:
            field_id = "property_and_equipment"
        elif "operating lease" in label and "asset" in label:
            field_id = "operating_lease_assets"
        elif "intangible" in label:
            field_id = "intangible_assets"
        elif "goodwill" in label:
            field_id = "goodwill"
        elif "deferred tax" in label:
            field_id = "deferred_tax_assets"
        elif "other assets" in label:
            field_id = "other_assets"
        elif label == "total assets":
            field_id = "total_assets"
        elif "accounts payable" in label:
            field_id = "accounts_payable"
        elif "accrued employee" in label or "accrued compensation" in label:
            field_id = "accrued_employee_compensation"
        elif "deferred revenue" in label:
            if section == "current_liabilities":
                field_id = "deferred_revenue_current"
            else:
                field_id = "deferred_revenue_noncurrent"
        elif "other current liabilities" in label:
            field_id = "other_current_liabilities"
        elif "total current liabilities" in label:
            field_id = "total_current_liabilities"
        elif "lease liabilit" in label:
            field_id = "lease_liabilities"
        elif "convertible" in label and "note" in label:
            field_id = "convertible_notes"
        elif "other liabilities" in label and "total" not in label:
            field_id = "other_liabilities"
        elif "total liabilities" in label and "equity" not in label:
            field_id = "total_liabilities"
        elif "common stock" in label:
            field_id = "common_stock"
        elif "additional paid" in label:
            field_id = "additional_paid_in_capital"
        elif "accumulated other comprehensive" in label:
            field_id = "aoci"
        elif "retained earnings" in label or "accumulated deficit" in label:
            field_id = "retained_earnings"
        elif "total stockholders" in label:
            field_id = "total_stockholders_equity"
        elif "total liabilities and" in label:
            field_id = "total_liabilities_and_equity"

        if field_id is None:
            continue

        for i, period in enumerate(periods):
            if i + 1 < len(row):
                val = parse_value(row[i + 1])
                if val is not None:
                    result[period][field_id] = val

    return result


def extract_quarterly_cf(table, filing_q):
    """Extract quarterly CF data (cumulative YTD)."""
    rows = table["rows"]

    # Find the year row (may be several header rows deep)
    year_row = None
    year_row_idx = None
    for idx, r in enumerate(rows[:8]):
        years_in_row = [c for c in r if isinstance(c, int) and 2000 <= c <= 2030]
        if len(years_in_row) >= 2:
            year_row = r
            year_row_idx = idx
            break

    if year_row is None:
        return {}

    years_found = [c for c in year_row if isinstance(c, int) and 2000 <= c <= 2030]

    q_num = int(filing_q[0])
    fy_year = int(filing_q[2:6])
    current_q = filing_q
    prior_q = f"{q_num}Q{fy_year - 1}"

    periods = [current_q, prior_q]
    result = {p: {} for p in periods}
    section = None

    for row in rows[year_row_idx + 1:]:
        if not row or not isinstance(row[0], str):
            continue
        raw_label = row[0].strip()
        label = normalize_label(raw_label)

        if "operating activities" in label and "net cash" not in label:
            section = "cfo"
            continue
        if "investing activities" in label and "net cash" not in label:
            section = "cfi"
            continue
        if "financing activities" in label and "net cash" not in label:
            section = "cff"
            continue
        if "adjustments to reconcile" in label:
            continue
        if "changes in operating" in label:
            continue
        if "supplemental" in label:
            break

        field_id = None

        if section == "cfo":
            if label.startswith("net income") or label.startswith("net loss"):
                field_id = "cf_net_income"
            elif "depreciation and amortization" in label:
                field_id = "depreciation_and_amortization"
            elif "amortization of debt" in label:
                field_id = "amortization_of_debt_costs"
            elif "amortization of contract" in label:
                field_id = "amortization_of_contract_costs"
            elif "stock-based compensation" in label:
                field_id = "stock_based_compensation"
            elif "allowance" in label or "credit loss" in label or "revenue reserve" in label:
                field_id = "changes_allowances"
            elif "deferred" in label and "tax" in label:
                field_id = "deferred_income_tax"
            elif "amortization of premium" in label or "accretion" in label:
                field_id = "amortization_of_premium_on_securities"
            elif ("gain" in label or "loss" in label) and "strategic" in label and "sale" in label:
                field_id = "gains_losses_strategic_investments"
            elif "fair value" in label and "strategic" in label:
                field_id = "changes_fair_value_strategic"
            elif "loss on retirement" in label:
                field_id = "loss_on_retirement_of_debt"
            elif "other non-cash" in label or "other non cash" in label:
                field_id = "other_noncash_items"
            elif "accounts receivable" in label and "unbilled" not in label:
                field_id = "change_accounts_receivable"
            elif "unbilled" in label:
                field_id = "change_unbilled_ar"
            elif "prepaid" in label:
                field_id = "change_prepaid_and_other"
            elif "operating lease" in label and "asset" in label:
                field_id = "change_operating_lease_assets"
            elif "accounts payable" in label:
                field_id = "change_accounts_payable"
            elif "accrued" in label and ("employee" in label or "compensation" in label):
                field_id = "change_accrued_compensation"
            elif "deferred revenue" in label:
                field_id = "change_deferred_revenue"
            elif "lease liabilit" in label:
                field_id = "change_lease_liabilities"
            elif "other liabilit" in label:
                field_id = "change_other_liabilities"
            elif "net cash" in label:
                field_id = "cfo_total"
        elif section == "cfi":
            if "purchases of available" in label:
                field_id = "purchases_of_afs_securities"
            elif ("maturities" in label or "sales" in label) and "available" in label:
                field_id = "maturities_sales_afs_securities"
            elif "purchase" in label and "property" in label:
                field_id = "purchases_of_ppe"
            elif "capitalized software" in label:
                field_id = "capitalized_software"
            elif "acquisition" in label and "strategic" in label:
                field_id = "acquisition_strategic_investments"
            elif "sale of strategic" in label:
                field_id = "sale_strategic_investments"
            elif "acquisition" in label and ("business" in label or "net of" in label):
                field_id = "acquisitions_net_of_cash"
            elif "net cash" in label:
                field_id = "cfi_total"
        elif section == "cff":
            if "proceeds" in label and "convertible" in label:
                field_id = "proceeds_convertible_notes"
            elif "payment" in label and "retirement" in label:
                field_id = "payment_retirement_notes"
            elif "payment" in label and "maturity" in label:
                field_id = "payment_maturity_notes"
            elif "capped call" in label:
                field_id = "purchase_capped_calls"
            elif "revolving credit" in label:
                field_id = "payment_revolving_credit"
            elif "employee stock purchase" in label:
                field_id = "proceeds_espp"
            elif "proceeds" in label and ("exercise" in label or "stock option" in label):
                field_id = "proceeds_stock_options"
            elif "proceeds" in label and "common stock" in label:
                field_id = "proceeds_stock_options"
            elif "repurchase" in label:
                field_id = "repurchase_stock"
            elif "net cash" in label:
                field_id = "cff_total"

        if field_id is None:
            if "effect of foreign exchange" in label or "effect of exchange" in label:
                field_id = "fx_effect"
            elif "net increase" in label or "net decrease" in label:
                field_id = "net_change_in_cash"
            elif "beginning of" in label:
                field_id = "cash_beginning"
            elif "end of" in label:
                field_id = "cash_ending"

        if field_id is None:
            continue

        for idx, period in enumerate(periods):
            if idx + 1 < len(row):
                val = parse_value(row[idx + 1])
                if val is not None:
                    result[period][field_id] = val

    return result


# ---------- geographic revenue extraction ----------
def extract_geo_revenue(table, filing_fy):
    """Extract geographic revenue breakdown from FY2026 10-K note tables."""
    rows = table["rows"]
    result = {}

    for row in rows:
        if not row or not isinstance(row[0], str):
            continue
        label = normalize_label(row[0])

        field_id = None
        if label == "u.s." or label == "united states":
            field_id = "us_revenue"
        elif label == "canada":
            field_id = "canada_revenue"
        elif label == "other americas":
            field_id = "other_americas_revenue"
        elif label == "total americas":
            field_id = "americas_revenue"
        elif label == "total emea":
            field_id = "emea_revenue"
        elif label == "total apac":
            field_id = "apac_revenue"
        elif label == "total revenue":
            field_id = "geo_total_revenue"

        if field_id is None:
            continue

        # The last column is total across segments
        # Row format: [label, sub_sup, license, services, total]
        total_col = len(row) - 1
        # Find the last non-empty numeric column
        for ci in range(len(row) - 1, 0, -1):
            val = parse_value(row[ci])
            if val is not None:
                result[field_id] = val
                break

    return result


# ============================================================
# MAIN EXTRACTION
# ============================================================

def main():
    print("Loading tables.json...")
    with open(TABLES_PATH) as f:
        data = json.load(f)
    tables = data["tables"]
    print(f"Loaded {len(tables)} tables.")

    # ---- Collect all data ----
    # Data stores: {period: {field_id: value}}
    is_data = {}
    bs_data = {}
    cf_data = {}

    # ---- Annual IS ----
    print("\nExtracting Annual Income Statements...")
    for filing_fy, tidx in sorted(ANNUAL_IS.items()):
        extracted = extract_annual_is(tables[tidx], filing_fy)
        for period, fields in extracted.items():
            if period not in is_data:
                is_data[period] = {}
            # Later filings override earlier ones
            is_data[period].update(fields)
        print(f"  {filing_fy} (Table {tidx}): {len(extracted)} periods, fields per period: {[len(v) for v in extracted.values()]}")

    # ---- Annual BS ----
    print("\nExtracting Annual Balance Sheets...")
    for filing_fy, tidx in sorted(ANNUAL_BS.items()):
        extracted = extract_annual_bs(tables[tidx], filing_fy)
        for period, fields in extracted.items():
            if period not in bs_data:
                bs_data[period] = {}
            bs_data[period].update(fields)
        print(f"  {filing_fy} (Table {tidx}): {len(extracted)} periods, fields per period: {[len(v) for v in extracted.values()]}")

    # ---- Annual CF ----
    print("\nExtracting Annual Cash Flows...")
    for filing_fy, tidx in sorted(ANNUAL_CF.items()):
        extracted = extract_annual_cf(tables[tidx], filing_fy)
        for period, fields in extracted.items():
            if period not in cf_data:
                cf_data[period] = {}
            cf_data[period].update(fields)
        print(f"  {filing_fy} (Table {tidx}): {len(extracted)} periods, fields per period: {[len(v) for v in extracted.values()]}")

    # ---- Quarterly IS ----
    print("\nExtracting Quarterly Income Statements...")
    for filing_q, tidx in sorted(QUARTERLY_IS.items()):
        extracted = extract_quarterly_is(tables[tidx], filing_q)
        for period, fields in extracted.items():
            if period not in is_data:
                is_data[period] = {}
            is_data[period].update(fields)
        print(f"  {filing_q} (Table {tidx}): periods={list(extracted.keys())}, fields: {[len(v) for v in extracted.values()]}")

    # ---- Quarterly BS ----
    print("\nExtracting Quarterly Balance Sheets...")
    for filing_q, tidx in sorted(QUARTERLY_BS.items()):
        extracted = extract_quarterly_bs(tables[tidx], filing_q)
        for period, fields in extracted.items():
            if period not in bs_data:
                bs_data[period] = {}
            bs_data[period].update(fields)
        print(f"  {filing_q} (Table {tidx}): periods={list(extracted.keys())}, fields: {[len(v) for v in extracted.values()]}")

    # ---- Quarterly CF ----
    print("\nExtracting Quarterly Cash Flows (YTD cumulative)...")
    for filing_q, tidx in sorted(QUARTERLY_CF.items()):
        extracted = extract_quarterly_cf(tables[tidx], filing_q)
        for period, fields in extracted.items():
            if period not in cf_data:
                cf_data[period] = {}
            cf_data[period].update(fields)
        print(f"  {filing_q} (Table {tidx}): periods={list(extracted.keys())}, fields: {[len(v) for v in extracted.values()]}")

    # ---- Geographic Revenue ----
    print("\nExtracting Geographic Revenue...")
    geo_data = {}
    for fy, tidx in GEO_REV_TABLES.items():
        geo = extract_geo_revenue(tables[tidx], fy)
        geo_data[fy] = geo
        print(f"  {fy} (Table {tidx}): {len(geo)} fields")

    # ============================================================
    # BUILD model.json
    # ============================================================

    annual_periods = [f"FY{y}" for y in range(2017, 2027)]  # FY2017-FY2026
    quarterly_periods = Q_LABELS

    all_periods = annual_periods + quarterly_periods

    def make_values(data_store, field_id, periods_list=None):
        """Build the values dict for a row from a data store."""
        if periods_list is None:
            periods_list = all_periods
        vals = {}
        for p in periods_list:
            if p in data_store and field_id in data_store[p]:
                v = data_store[p][field_id]
                if isinstance(v, float) and v == int(v) and abs(v) > 10:
                    v = int(v)
                vals[p] = v
        return vals if vals else {}

    def make_row(id_, label, row_type="input", values=None, **kwargs):
        """Build a row dict."""
        row = {"id": id_, "label": label, "type": row_type}
        if values:
            row["values"] = values
        for k, v in kwargs.items():
            if v is not None:
                row[k] = v
        return row

    # ============================================================
    # INCOME STATEMENT SHEET
    # ============================================================
    is_rows = []

    # Block 1: INCOME STATEMENT
    is_block1 = []

    # Revenue
    is_block1.append(make_row("subscription_and_support_rev", "Subscription and Support Revenue",
                              values=make_values(is_data, "subscription_and_support_rev"), indent=1))
    is_block1.append(make_row("license_rev", "License Revenue",
                              values=make_values(is_data, "license_rev"), indent=1))
    is_block1.append(make_row("services_rev", "Services Revenue",
                              values=make_values(is_data, "services_rev"), indent=1))
    is_block1.append(make_row("total_revenue", "Total Revenue",
                              values=make_values(is_data, "total_revenue"), bold=True))
    is_block1.append(make_row("rev_yoy", "Revenue Growth YoY", row_type="growth_yoy",
                              source="total_revenue", fmt="pct"))

    # Separator
    is_block1.append(make_row("spacer_cost", "", row_type="spacer"))

    # Cost of Revenue
    is_block1.append(make_row("subscription_and_support_cost", "Cost of Revenue - Subscription and Support",
                              values=make_values(is_data, "subscription_and_support_cost"), indent=1))
    is_block1.append(make_row("license_cost", "Cost of Revenue - License",
                              values=make_values(is_data, "license_cost"), indent=1))
    is_block1.append(make_row("services_cost", "Cost of Revenue - Services",
                              values=make_values(is_data, "services_cost"), indent=1))
    is_block1.append(make_row("total_cost_of_revenue", "Total Cost of Revenue",
                              values=make_values(is_data, "total_cost_of_revenue"), bold=True))

    # Gross Profit
    is_block1.append(make_row("spacer_gp", "", row_type="spacer"))
    is_block1.append(make_row("subscription_and_support_gp", "Gross Profit - Subscription and Support",
                              values=make_values(is_data, "subscription_and_support_gp"), indent=1))
    is_block1.append(make_row("license_gp", "Gross Profit - License",
                              values=make_values(is_data, "license_gp"), indent=1))
    is_block1.append(make_row("services_gp", "Gross Profit - Services",
                              values=make_values(is_data, "services_gp"), indent=1))
    is_block1.append(make_row("total_gross_profit", "Total Gross Profit",
                              values=make_values(is_data, "total_gross_profit"), bold=True))
    is_block1.append(make_row("gross_margin", "Gross Margin", row_type="calc",
                              expr="{total_gross_profit}/{total_revenue}", fmt="pct", memo=True))

    # Operating Expenses
    is_block1.append(make_row("spacer_opex", "", row_type="spacer"))
    is_block1.append(make_row("research_and_development", "Research and Development",
                              values=make_values(is_data, "research_and_development"), indent=1))
    is_block1.append(make_row("sales_and_marketing", "Sales and Marketing",
                              values=make_values(is_data, "sales_and_marketing"), indent=1))
    is_block1.append(make_row("general_and_administrative", "General and Administrative",
                              values=make_values(is_data, "general_and_administrative"), indent=1))
    is_block1.append(make_row("total_operating_expenses", "Total Operating Expenses",
                              values=make_values(is_data, "total_operating_expenses"), bold=True))

    # Operating Income
    is_block1.append(make_row("spacer_opinc", "", row_type="spacer"))
    is_block1.append(make_row("operating_income", "Income (Loss) from Operations",
                              values=make_values(is_data, "operating_income"), bold=True))
    is_block1.append(make_row("op_margin", "Operating Margin", row_type="calc",
                              expr="{operating_income}/{total_revenue}", fmt="pct", memo=True))

    # Below-the-line
    is_block1.append(make_row("spacer_btl", "", row_type="spacer"))
    is_block1.append(make_row("interest_income", "Interest Income",
                              values=make_values(is_data, "interest_income"), indent=1))
    is_block1.append(make_row("interest_expense", "Interest Expense",
                              values=make_values(is_data, "interest_expense"), indent=1))
    is_block1.append(make_row("other_income_expense", "Other Income (Expense), Net",
                              values=make_values(is_data, "other_income_expense"), indent=1))
    is_block1.append(make_row("income_before_taxes", "Income (Loss) Before Income Taxes",
                              values=make_values(is_data, "income_before_taxes")))
    is_block1.append(make_row("income_tax_expense", "Provision for (Benefit from) Income Taxes",
                              values=make_values(is_data, "income_tax_expense"), indent=1))
    is_block1.append(make_row("net_income", "Net Income (Loss)",
                              values=make_values(is_data, "net_income"), bold=True))
    is_block1.append(make_row("net_margin", "Net Margin", row_type="calc",
                              expr="{net_income}/{total_revenue}", fmt="pct", memo=True))
    is_block1.append(make_row("ni_yoy", "Net Income Growth YoY", row_type="growth_yoy",
                              source="net_income", fmt="pct"))

    # Block 2: EPS & SHARE COUNT
    eps_block = []
    eps_block.append(make_row("basic_eps", "Basic EPS",
                              values=make_values(is_data, "basic_eps"), bold=True, fmt="ps"))
    eps_block.append(make_row("diluted_eps", "Diluted EPS",
                              values=make_values(is_data, "diluted_eps"), bold=True, fmt="ps"))
    eps_block.append(make_row("waso_basic", "Weighted Avg Shares - Basic",
                              values=make_values(is_data, "waso_basic"), fmt="num"))
    eps_block.append(make_row("waso_diluted", "Weighted Avg Shares - Diluted",
                              values=make_values(is_data, "waso_diluted"), fmt="num"))

    # Block 3: MARGINS & GROWTH
    margin_block = []
    margin_block.append(make_row("sub_support_rev_pct", "Subscription & Support % of Revenue", row_type="calc",
                                 expr="{subscription_and_support_rev}/{total_revenue}", fmt="pct"))
    margin_block.append(make_row("license_rev_pct", "License % of Revenue", row_type="calc",
                                 expr="{license_rev}/{total_revenue}", fmt="pct"))
    margin_block.append(make_row("services_rev_pct", "Services % of Revenue", row_type="calc",
                                 expr="{services_rev}/{total_revenue}", fmt="pct"))
    margin_block.append(make_row("sub_support_gm", "Subscription & Support Gross Margin", row_type="calc",
                                 expr="{subscription_and_support_gp}/{subscription_and_support_rev}", fmt="pct"))
    margin_block.append(make_row("license_gm", "License Gross Margin", row_type="calc",
                                 expr="{license_gp}/{license_rev}", fmt="pct"))
    margin_block.append(make_row("services_gm", "Services Gross Margin", row_type="calc",
                                 expr="{services_gp}/{services_rev}", fmt="pct"))
    margin_block.append(make_row("rnd_pct_rev", "R&D % of Revenue", row_type="calc",
                                 expr="{research_and_development}/{total_revenue}", fmt="pct"))
    margin_block.append(make_row("snm_pct_rev", "S&M % of Revenue", row_type="calc",
                                 expr="{sales_and_marketing}/{total_revenue}", fmt="pct"))
    margin_block.append(make_row("gna_pct_rev", "G&A % of Revenue", row_type="calc",
                                 expr="{general_and_administrative}/{total_revenue}", fmt="pct"))
    margin_block.append(make_row("opex_pct_rev", "Total Opex % of Revenue", row_type="calc",
                                 expr="{total_operating_expenses}/{total_revenue}", fmt="pct"))
    margin_block.append(make_row("sub_support_rev_yoy", "Sub & Support Revenue Growth YoY", row_type="growth_yoy",
                                 source="subscription_and_support_rev", fmt="pct"))
    margin_block.append(make_row("license_rev_yoy", "License Revenue Growth YoY", row_type="growth_yoy",
                                 source="license_rev", fmt="pct"))
    margin_block.append(make_row("services_rev_yoy", "Services Revenue Growth YoY", row_type="growth_yoy",
                                 source="services_rev", fmt="pct"))
    margin_block.append(make_row("effective_tax_rate", "Effective Tax Rate", row_type="calc",
                                 expr="{income_tax_expense}/{income_before_taxes}", fmt="pct"))

    # Block 4: IS CHECK
    check_block = []
    check_block.append(make_row("is_check", "IS Check (should be 0)", row_type="check",
                                expr="{total_revenue}-{total_cost_of_revenue}-{total_operating_expenses}-{operating_income}"))

    is_sheet = {
        "id": "IS",
        "label": "Income Statement",
        "blocks": [
            {"label": "INCOME STATEMENT", "rows": is_block1},
            {"label": "EPS & SHARE COUNT", "rows": eps_block},
            {"label": "MARGINS & GROWTH", "rows": margin_block},
            {"label": "IS CHECK", "rows": check_block},
        ]
    }

    # ============================================================
    # BALANCE SHEET
    # ============================================================
    bs_block = []

    # Current Assets
    bs_block.append(make_row("cash_and_equivalents", "Cash and Cash Equivalents",
                             values=make_values(bs_data, "cash_and_equivalents"), indent=1))
    bs_block.append(make_row("short_term_investments", "Short-term Investments",
                             values=make_values(bs_data, "short_term_investments"), indent=1))
    bs_block.append(make_row("accounts_receivable", "Accounts Receivable, Net",
                             values=make_values(bs_data, "accounts_receivable"), indent=1))
    bs_block.append(make_row("unbilled_ar_current", "Unbilled Accounts Receivable, Net (Current)",
                             values=make_values(bs_data, "unbilled_ar_current"), indent=1))
    bs_block.append(make_row("prepaid_and_other_current", "Prepaid Expenses and Other Current Assets",
                             values=make_values(bs_data, "prepaid_and_other_current"), indent=1))
    bs_block.append(make_row("total_current_assets", "Total Current Assets",
                             values=make_values(bs_data, "total_current_assets"), bold=True))

    # Non-current Assets
    bs_block.append(make_row("spacer_nca", "", row_type="spacer"))
    bs_block.append(make_row("long_term_investments", "Long-term Investments",
                             values=make_values(bs_data, "long_term_investments"), indent=1))
    bs_block.append(make_row("unbilled_ar_noncurrent", "Unbilled Accounts Receivable (Non-current)",
                             values=make_values(bs_data, "unbilled_ar_noncurrent"), indent=1))
    bs_block.append(make_row("property_and_equipment", "Property and Equipment, Net",
                             values=make_values(bs_data, "property_and_equipment"), indent=1))
    bs_block.append(make_row("operating_lease_assets", "Operating Lease Assets",
                             values=make_values(bs_data, "operating_lease_assets"), indent=1))
    bs_block.append(make_row("intangible_assets", "Intangible Assets, Net",
                             values=make_values(bs_data, "intangible_assets"), indent=1))
    bs_block.append(make_row("goodwill", "Goodwill",
                             values=make_values(bs_data, "goodwill"), indent=1))
    bs_block.append(make_row("deferred_tax_assets", "Deferred Tax Assets, Net",
                             values=make_values(bs_data, "deferred_tax_assets"), indent=1))
    bs_block.append(make_row("other_assets", "Other Assets",
                             values=make_values(bs_data, "other_assets"), indent=1))
    bs_block.append(make_row("total_assets", "TOTAL ASSETS",
                             values=make_values(bs_data, "total_assets"), bold=True))

    # Liabilities
    bs_block.append(make_row("spacer_liab", "", row_type="spacer"))
    bs_block.append(make_row("accounts_payable", "Accounts Payable",
                             values=make_values(bs_data, "accounts_payable"), indent=1))
    bs_block.append(make_row("accrued_employee_compensation", "Accrued Employee Compensation",
                             values=make_values(bs_data, "accrued_employee_compensation"), indent=1))
    bs_block.append(make_row("deferred_revenue_current", "Deferred Revenue (Current)",
                             values=make_values(bs_data, "deferred_revenue_current"), indent=1))
    bs_block.append(make_row("other_current_liabilities", "Other Current Liabilities",
                             values=make_values(bs_data, "other_current_liabilities"), indent=1))
    bs_block.append(make_row("total_current_liabilities", "Total Current Liabilities",
                             values=make_values(bs_data, "total_current_liabilities"), bold=True))

    bs_block.append(make_row("spacer_ncl", "", row_type="spacer"))
    bs_block.append(make_row("lease_liabilities", "Lease Liabilities (Non-current)",
                             values=make_values(bs_data, "lease_liabilities"), indent=1))
    bs_block.append(make_row("convertible_notes", "Convertible Senior Notes, Net",
                             values=make_values(bs_data, "convertible_notes"), indent=1))
    bs_block.append(make_row("deferred_revenue_noncurrent", "Deferred Revenue (Non-current)",
                             values=make_values(bs_data, "deferred_revenue_noncurrent"), indent=1))
    bs_block.append(make_row("other_liabilities", "Other Liabilities",
                             values=make_values(bs_data, "other_liabilities"), indent=1))
    bs_block.append(make_row("total_liabilities", "Total Liabilities",
                             values=make_values(bs_data, "total_liabilities"), bold=True))

    # Equity
    bs_block.append(make_row("spacer_eq", "", row_type="spacer"))
    bs_block.append(make_row("common_stock", "Common Stock",
                             values=make_values(bs_data, "common_stock"), indent=1))
    bs_block.append(make_row("additional_paid_in_capital", "Additional Paid-in Capital",
                             values=make_values(bs_data, "additional_paid_in_capital"), indent=1))
    bs_block.append(make_row("aoci", "Accumulated Other Comprehensive Income (Loss)",
                             values=make_values(bs_data, "aoci"), indent=1))
    bs_block.append(make_row("retained_earnings", "Retained Earnings (Accumulated Deficit)",
                             values=make_values(bs_data, "retained_earnings"), indent=1))
    bs_block.append(make_row("total_stockholders_equity", "Total Stockholders' Equity",
                             values=make_values(bs_data, "total_stockholders_equity"), bold=True))
    bs_block.append(make_row("total_liabilities_and_equity", "TOTAL LIABILITIES AND STOCKHOLDERS' EQUITY",
                             values=make_values(bs_data, "total_liabilities_and_equity"), bold=True))

    # BS CHECK
    bs_check_block = [
        make_row("bs_check", "BS Check (should be 0)", row_type="check",
                 expr="{total_assets}-{total_liabilities}-{total_stockholders_equity}")
    ]

    bs_sheet = {
        "id": "BS",
        "label": "Balance Sheet",
        "blocks": [
            {"label": "BALANCE SHEET", "rows": bs_block},
            {"label": "BS CHECK", "rows": bs_check_block},
        ]
    }

    # ============================================================
    # CASH FLOW STATEMENT
    # ============================================================
    cf_block = []

    # Operating Activities
    cf_block.append(make_row("cf_net_income", "Net Income (Loss)",
                             values=make_values(cf_data, "cf_net_income")))
    cf_block.append(make_row("spacer_cfo_adj", "", row_type="spacer"))
    cf_block.append(make_row("depreciation_and_amortization", "Depreciation and Amortization",
                             values=make_values(cf_data, "depreciation_and_amortization"), indent=1))
    cf_block.append(make_row("amortization_of_debt_costs", "Amortization of Debt Issuance Costs",
                             values=make_values(cf_data, "amortization_of_debt_costs"), indent=1))
    cf_block.append(make_row("amortization_of_contract_costs", "Amortization of Contract Costs",
                             values=make_values(cf_data, "amortization_of_contract_costs"), indent=1))
    cf_block.append(make_row("stock_based_compensation", "Stock-based Compensation",
                             values=make_values(cf_data, "stock_based_compensation"), indent=1))
    cf_block.append(make_row("changes_allowances", "Changes to Allowances / Credit Losses",
                             values=make_values(cf_data, "changes_allowances"), indent=1))
    cf_block.append(make_row("deferred_income_tax", "Deferred Income Tax",
                             values=make_values(cf_data, "deferred_income_tax"), indent=1))
    cf_block.append(make_row("amortization_of_premium_on_securities", "Amortization of Premium on Securities",
                             values=make_values(cf_data, "amortization_of_premium_on_securities"), indent=1))
    cf_block.append(make_row("gains_losses_strategic_investments", "Gains/Losses on Strategic Investments",
                             values=make_values(cf_data, "gains_losses_strategic_investments"), indent=1))
    cf_block.append(make_row("changes_fair_value_strategic", "Changes in Fair Value of Strategic Investments",
                             values=make_values(cf_data, "changes_fair_value_strategic"), indent=1))
    cf_block.append(make_row("loss_on_retirement_of_debt", "Loss on Retirement of Debt",
                             values=make_values(cf_data, "loss_on_retirement_of_debt"), indent=1))
    cf_block.append(make_row("accelerated_depreciation_lease", "Accelerated Depreciation (Lease)",
                             values=make_values(cf_data, "accelerated_depreciation_lease"), indent=1))
    cf_block.append(make_row("gain_from_lease_assignment", "Gain from Lease Assignment",
                             values=make_values(cf_data, "gain_from_lease_assignment"), indent=1))
    cf_block.append(make_row("excess_tax_benefit", "Excess Tax Benefit from Stock Options/RSUs",
                             values=make_values(cf_data, "excess_tax_benefit"), indent=1))
    cf_block.append(make_row("other_noncash_items", "Other Non-cash Items",
                             values=make_values(cf_data, "other_noncash_items"), indent=1))

    # Working capital changes
    cf_block.append(make_row("spacer_wc", "", row_type="spacer"))
    cf_block.append(make_row("change_accounts_receivable", "Change in Accounts Receivable",
                             values=make_values(cf_data, "change_accounts_receivable"), indent=1))
    cf_block.append(make_row("change_unbilled_ar", "Change in Unbilled Accounts Receivable",
                             values=make_values(cf_data, "change_unbilled_ar"), indent=1))
    cf_block.append(make_row("change_prepaid_and_other", "Change in Prepaid Expenses and Other Assets",
                             values=make_values(cf_data, "change_prepaid_and_other"), indent=1))
    cf_block.append(make_row("change_operating_lease_assets", "Change in Operating Lease Assets",
                             values=make_values(cf_data, "change_operating_lease_assets"), indent=1))
    cf_block.append(make_row("change_accounts_payable", "Change in Accounts Payable",
                             values=make_values(cf_data, "change_accounts_payable"), indent=1))
    cf_block.append(make_row("change_accrued_compensation", "Change in Accrued Employee Compensation",
                             values=make_values(cf_data, "change_accrued_compensation"), indent=1))
    cf_block.append(make_row("change_deferred_revenue", "Change in Deferred Revenue",
                             values=make_values(cf_data, "change_deferred_revenue"), indent=1))
    cf_block.append(make_row("change_lease_liabilities", "Change in Lease Liabilities",
                             values=make_values(cf_data, "change_lease_liabilities"), indent=1))
    cf_block.append(make_row("change_other_liabilities", "Change in Other Liabilities",
                             values=make_values(cf_data, "change_other_liabilities"), indent=1))
    cf_block.append(make_row("cfo_total", "Net Cash from Operating Activities",
                             values=make_values(cf_data, "cfo_total"), bold=True))

    # Investing Activities
    cf_block.append(make_row("spacer_cfi", "", row_type="spacer"))
    cf_block.append(make_row("purchases_of_afs_securities", "Purchases of Available-for-Sale Securities",
                             values=make_values(cf_data, "purchases_of_afs_securities"), indent=1))
    cf_block.append(make_row("maturities_sales_afs_securities", "Maturities and Sales of AFS Securities",
                             values=make_values(cf_data, "maturities_sales_afs_securities"), indent=1))
    cf_block.append(make_row("purchases_of_ppe", "Purchases of Property and Equipment",
                             values=make_values(cf_data, "purchases_of_ppe"), indent=1))
    cf_block.append(make_row("capitalized_software", "Capitalized Software Development Costs",
                             values=make_values(cf_data, "capitalized_software"), indent=1))
    cf_block.append(make_row("acquisition_strategic_investments", "Acquisition of Strategic Investments",
                             values=make_values(cf_data, "acquisition_strategic_investments"), indent=1))
    cf_block.append(make_row("sale_strategic_investments", "Sale of Strategic Investments",
                             values=make_values(cf_data, "sale_strategic_investments"), indent=1))
    cf_block.append(make_row("acquisitions_net_of_cash", "Acquisitions, Net of Cash",
                             values=make_values(cf_data, "acquisitions_net_of_cash"), indent=1))
    cf_block.append(make_row("cfi_total", "Net Cash from Investing Activities",
                             values=make_values(cf_data, "cfi_total"), bold=True))

    # Financing Activities
    cf_block.append(make_row("spacer_cff", "", row_type="spacer"))
    cf_block.append(make_row("proceeds_convertible_notes", "Proceeds from Convertible Notes",
                             values=make_values(cf_data, "proceeds_convertible_notes"), indent=1))
    cf_block.append(make_row("payment_retirement_notes", "Payment for Retirement of Convertible Notes",
                             values=make_values(cf_data, "payment_retirement_notes"), indent=1))
    cf_block.append(make_row("payment_maturity_notes", "Payment for Maturity of Convertible Notes",
                             values=make_values(cf_data, "payment_maturity_notes"), indent=1))
    cf_block.append(make_row("purchase_capped_calls", "Purchase of Capped Calls",
                             values=make_values(cf_data, "purchase_capped_calls"), indent=1))
    cf_block.append(make_row("payment_revolving_credit", "Payment of Revolving Credit Facility Costs",
                             values=make_values(cf_data, "payment_revolving_credit"), indent=1))
    cf_block.append(make_row("proceeds_common_stock_net", "Proceeds from Common Stock, Net",
                             values=make_values(cf_data, "proceeds_common_stock_net"), indent=1))
    cf_block.append(make_row("proceeds_espp", "Proceeds from ESPP",
                             values=make_values(cf_data, "proceeds_espp"), indent=1))
    cf_block.append(make_row("proceeds_stock_options", "Proceeds from Stock Option Exercises",
                             values=make_values(cf_data, "proceeds_stock_options"), indent=1))
    cf_block.append(make_row("repurchase_stock", "Repurchase and Retirement of Common Stock",
                             values=make_values(cf_data, "repurchase_stock"), indent=1))
    cf_block.append(make_row("taxes_remitted_rsu", "Taxes Remitted on RSU Vesting",
                             values=make_values(cf_data, "taxes_remitted_rsu"), indent=1))
    cf_block.append(make_row("excess_tax_benefit_financing", "Excess Tax Benefit (Financing)",
                             values=make_values(cf_data, "excess_tax_benefit_financing"), indent=1))
    cf_block.append(make_row("cff_total", "Net Cash from Financing Activities",
                             values=make_values(cf_data, "cff_total"), bold=True))

    # Bottom
    cf_block.append(make_row("spacer_cfbot", "", row_type="spacer"))
    cf_block.append(make_row("fx_effect", "Effect of Foreign Exchange on Cash",
                             values=make_values(cf_data, "fx_effect")))
    cf_block.append(make_row("net_change_in_cash", "Net Change in Cash",
                             values=make_values(cf_data, "net_change_in_cash"), bold=True))
    cf_block.append(make_row("cash_beginning", "Cash, Beginning of Period",
                             values=make_values(cf_data, "cash_beginning")))
    cf_block.append(make_row("cash_ending", "Cash, End of Period",
                             values=make_values(cf_data, "cash_ending"), bold=True))

    # FCF Analytics
    fcf_block = []
    fcf_block.append(make_row("fcf", "Free Cash Flow", row_type="calc",
                              expr="{cfo_total}+{purchases_of_ppe}+{capitalized_software}", bold=True))
    fcf_block.append(make_row("fcf_yoy", "FCF Growth YoY", row_type="growth_yoy",
                              source="fcf", fmt="pct"))
    fcf_block.append(make_row("capex_total", "Total Capex", row_type="calc",
                              expr="{purchases_of_ppe}+{capitalized_software}"))
    fcf_block.append(make_row("capex_pct", "Capex % of Revenue", row_type="calc",
                              expr="({purchases_of_ppe}+{capitalized_software})/{total_revenue}*-1", fmt="pct"))
    fcf_block.append(make_row("fcf_margin", "FCF Margin", row_type="calc",
                              expr="({cfo_total}+{purchases_of_ppe}+{capitalized_software})/{total_revenue}", fmt="pct"))
    fcf_block.append(make_row("fcf_conversion", "FCF Conversion (FCF/Net Income)", row_type="calc",
                              expr="({cfo_total}+{purchases_of_ppe}+{capitalized_software})/{net_income}", fmt="pct"))

    # CF CHECK
    cf_check_block = [
        make_row("cf_check", "CF Check (should be 0)", row_type="check",
                 expr="{cfo_total}+{cfi_total}+{cff_total}+{fx_effect}-{net_change_in_cash}")
    ]

    cf_sheet = {
        "id": "CF",
        "label": "Cash Flow Statement",
        "blocks": [
            {"label": "CASH FLOW STATEMENT", "rows": cf_block},
            {"label": "FCF ANALYTICS", "rows": fcf_block},
            {"label": "CF CHECK", "rows": cf_check_block},
        ]
    }

    # ============================================================
    # DERIVED METRICS (DM)
    # ============================================================
    dm_blocks = []

    # Profitability
    prof_rows = [
        make_row("dm_gross_margin", "Gross Margin", row_type="calc",
                 expr="{total_gross_profit}/{total_revenue}", fmt="pct"),
        make_row("dm_op_margin", "Operating Margin", row_type="calc",
                 expr="{operating_income}/{total_revenue}", fmt="pct"),
        make_row("dm_net_margin", "Net Margin", row_type="calc",
                 expr="{net_income}/{total_revenue}", fmt="pct"),
        make_row("dm_effective_tax_rate", "Effective Tax Rate", row_type="calc",
                 expr="{income_tax_expense}/{income_before_taxes}", fmt="pct"),
        make_row("dm_sub_support_gm", "Subscription & Support Gross Margin", row_type="calc",
                 expr="{subscription_and_support_gp}/{subscription_and_support_rev}", fmt="pct"),
    ]
    dm_blocks.append({"label": "PROFITABILITY", "rows": prof_rows})

    # Returns
    returns_rows = [
        make_row("dm_roa", "Return on Assets (ROA)", row_type="calc",
                 expr="{net_income}/{total_assets}", fmt="pct"),
        make_row("dm_roe", "Return on Equity (ROE)", row_type="calc",
                 expr="{net_income}/{total_stockholders_equity}", fmt="pct"),
        make_row("dm_asset_turnover", "Asset Turnover", row_type="calc",
                 expr="{total_revenue}/{total_assets}", fmt="x"),
    ]
    dm_blocks.append({"label": "RETURNS", "rows": returns_rows})

    # Solvency
    solv_rows = [
        make_row("dm_equity_ratio", "Equity Ratio", row_type="calc",
                 expr="{total_stockholders_equity}/{total_assets}", fmt="pct"),
        make_row("dm_debt_to_assets", "Debt to Assets", row_type="calc",
                 expr="{convertible_notes}/{total_assets}", fmt="pct"),
    ]
    dm_blocks.append({"label": "SOLVENCY", "rows": solv_rows})

    # Liquidity
    liq_rows = [
        make_row("dm_current_ratio", "Current Ratio", row_type="calc",
                 expr="{total_current_assets}/{total_current_liabilities}", fmt="x"),
        make_row("dm_cash_ratio", "Cash Ratio", row_type="calc",
                 expr="({cash_and_equivalents}+{short_term_investments})/{total_current_liabilities}", fmt="x"),
    ]
    dm_blocks.append({"label": "LIQUIDITY", "rows": liq_rows})

    # Coverage
    cov_rows = [
        make_row("dm_interest_coverage", "Interest Coverage", row_type="calc",
                 expr="{operating_income}/{interest_expense}*-1", fmt="x"),
    ]
    dm_blocks.append({"label": "COVERAGE", "rows": cov_rows})

    # Cash Conversion
    cc_rows = [
        make_row("dm_cfo_margin", "CFO Margin", row_type="calc",
                 expr="{cfo_total}/{total_revenue}", fmt="pct"),
        make_row("dm_capex_intensity", "Capex Intensity", row_type="calc",
                 expr="({purchases_of_ppe}+{capitalized_software})/{total_revenue}*-1", fmt="pct"),
        make_row("dm_fcf_margin", "FCF Margin", row_type="calc",
                 expr="({cfo_total}+{purchases_of_ppe}+{capitalized_software})/{total_revenue}", fmt="pct"),
        make_row("dm_fcf_conversion", "FCF Conversion (FCF/Net Income)", row_type="calc",
                 expr="({cfo_total}+{purchases_of_ppe}+{capitalized_software})/{net_income}", fmt="pct"),
        make_row("dm_da_capex", "D&A / Capex", row_type="calc",
                 expr="{depreciation_and_amortization}/({purchases_of_ppe}+{capitalized_software})*-1", fmt="x"),
    ]
    dm_blocks.append({"label": "CASH CONVERSION", "rows": cc_rows})

    # Earnings Quality
    eq_rows = [
        make_row("dm_cfo_ni", "CFO / Net Income", row_type="calc",
                 expr="{cfo_total}/{net_income}", fmt="x"),
        make_row("dm_accrual_ratio", "Accrual Ratio", row_type="calc",
                 expr="({net_income}-{cfo_total})/{total_assets}", fmt="pct"),
    ]
    dm_blocks.append({"label": "EARNINGS QUALITY", "rows": eq_rows})

    # Growth
    growth_rows = [
        make_row("dm_rev_growth", "Revenue Growth YoY", row_type="growth_yoy",
                 source="total_revenue", fmt="pct"),
        make_row("dm_ni_growth", "Net Income Growth YoY", row_type="growth_yoy",
                 source="net_income", fmt="pct"),
        make_row("dm_cfo_growth", "CFO Growth YoY", row_type="growth_yoy",
                 source="cfo_total", fmt="pct"),
    ]
    dm_blocks.append({"label": "GROWTH", "rows": growth_rows})

    # Working Capital
    wc_rows = [
        make_row("dm_dso", "Days Sales Outstanding (DSO)", row_type="calc",
                 expr="{accounts_receivable}/{total_revenue}*365", fmt="num"),
    ]
    dm_blocks.append({"label": "WORKING CAPITAL", "rows": wc_rows})

    dm_sheet = {
        "id": "DM",
        "label": "Derived Metrics",
        "blocks": dm_blocks,
    }

    # ============================================================
    # SEGMENTS (SEG) — Geographic Revenue
    # ============================================================
    seg_block_rows = []
    for geo_field, geo_label in [
        ("us_revenue", "U.S. Revenue"),
        ("canada_revenue", "Canada Revenue"),
        ("other_americas_revenue", "Other Americas Revenue"),
        ("americas_revenue", "Total Americas Revenue"),
        ("emea_revenue", "Total EMEA Revenue"),
        ("apac_revenue", "Total APAC Revenue"),
        ("geo_total_revenue", "Total Revenue (Geographic)"),
    ]:
        vals = {}
        for fy, gdata in geo_data.items():
            if geo_field in gdata:
                vals[fy] = gdata[geo_field]
        if vals:
            seg_block_rows.append(make_row(f"seg_{geo_field}", geo_label, values=vals))

    # Add geographic mix calculations
    seg_calc_rows = [
        make_row("seg_americas_pct", "Americas % of Revenue", row_type="calc",
                 expr="{seg_americas_revenue}/{seg_geo_total_revenue}", fmt="pct"),
        make_row("seg_emea_pct", "EMEA % of Revenue", row_type="calc",
                 expr="{seg_emea_revenue}/{seg_geo_total_revenue}", fmt="pct"),
        make_row("seg_apac_pct", "APAC % of Revenue", row_type="calc",
                 expr="{seg_apac_revenue}/{seg_geo_total_revenue}", fmt="pct"),
    ]

    seg_sheet = {
        "id": "SEG",
        "label": "Segments",
        "blocks": [
            {"label": "GEOGRAPHIC REVENUE", "rows": seg_block_rows},
            {"label": "GEOGRAPHIC MIX", "rows": seg_calc_rows},
        ]
    }

    # ============================================================
    # NOTE SCHEDULES (NS)
    # ============================================================
    ns_blocks = []

    # Convertible Notes (from Table 1031)
    conv_notes_rows = [
        make_row("ns_conv_notes_principal", "2029 Convertible Senior Notes - Principal",
                 values={"FY2026": 690000, "FY2025": 690000}),
        make_row("ns_conv_notes_unamortized", "Less: Unamortized Debt Issuance Costs",
                 values={"FY2026": -11906, "FY2025": -15432}),
        make_row("ns_conv_notes_carrying", "Net Carrying Amount",
                 values={"FY2026": 678094, "FY2025": 674568}, bold=True),
    ]
    ns_blocks.append({"label": "CONVERTIBLE SENIOR NOTES", "rows": conv_notes_rows})

    # Intangible Assets (from Table 1022)
    intang_rows = [
        make_row("ns_intang_acquired_tech", "Acquired Technology, Net",
                 values={"FY2026": 11942, "FY2025": 8117}),
        make_row("ns_intang_customer_rel", "Customer Contracts & Relationships, Net",
                 values={"FY2026": 4201, "FY2025": 3533}),
        make_row("ns_intang_trademarks", "Trademarks, Net",
                 values={"FY2026": 263, "FY2025": 392}),
        make_row("ns_intang_total", "Total Intangible Assets, Net",
                 values={"FY2026": 16406, "FY2025": 12042}, bold=True),
    ]
    ns_blocks.append({"label": "INTANGIBLE ASSETS", "rows": intang_rows})

    # Operating Leases (from Tables 1034, 1036)
    lease_rows = [
        make_row("ns_lease_cost", "Operating Lease Costs",
                 values={"FY2026": 14042, "FY2025": 13167, "FY2024": 12537}),
        make_row("ns_lease_variable", "Variable Lease Costs",
                 values={"FY2026": 3777, "FY2025": 2428, "FY2024": 2344}),
        make_row("ns_lease_net_cost", "Net Operating Lease Costs",
                 values={"FY2026": 17819, "FY2025": 15595, "FY2024": 14881}),
        make_row("ns_lease_assets", "Operating Lease Assets",
                 values={"FY2026": 34404, "FY2025": 39309}),
        make_row("ns_lease_current", "Current Lease Liabilities",
                 values={"FY2026": 11687, "FY2025": 10438}),
        make_row("ns_lease_noncurrent", "Non-current Lease Liabilities",
                 values={"FY2026": 25206, "FY2025": 30687}),
        make_row("ns_lease_total", "Total Lease Liabilities",
                 values={"FY2026": 36893, "FY2025": 41125}, bold=True),
    ]
    ns_blocks.append({"label": "OPERATING LEASES", "rows": lease_rows})

    # Revenue Contract Balances (from Table 1012)
    contract_rows = [
        make_row("ns_unbilled_ar_net", "Unbilled Accounts Receivable, Net",
                 values={"FY2026": 140832, "FY2025": 131629}),
        make_row("ns_contract_acq_costs", "Contract Acquisition Costs, Net",
                 values={"FY2026": 79376, "FY2025": 67922}),
        make_row("ns_costs_fulfill", "Costs to Fulfill a Contract, Net",
                 values={"FY2026": 12318, "FY2025": 9415}),
        make_row("ns_deferred_rev_total", "Deferred Revenue, Net (Total)",
                 values={"FY2026": 438814, "FY2025": 344786}),
    ]
    ns_blocks.append({"label": "REVENUE CONTRACT BALANCES", "rows": contract_rows})

    ns_sheet = {
        "id": "NS",
        "label": "Note Schedules",
        "blocks": ns_blocks,
    }

    # ============================================================
    # ASSEMBLE model.json
    # ============================================================
    model = {
        "company": {
            "name": "Guidewire Software, Inc.",
            "ticker": "GWRE",
            "exchange": "NYSE",
            "currency": "USD",
            "units": "$ in thousands except per-share data",
            "reporting_framework": "US GAAP",
            "fiscal_year_end": "July 31",
            "sic": "7372",
            "as_of_date": "2026-07-31",
            "model_date": "2026-09-17",
        },
        "periods": {
            "annual": annual_periods,
            "scrap_cols": 5,
            "quarterly": quarterly_periods,
        },
        "sheets": [is_sheet, bs_sheet, cf_sheet, dm_sheet, seg_sheet, ns_sheet],
    }

    # ---- Strip empty rows (rows with no values for any period) ----
    for sheet in model["sheets"]:
        for block in sheet["blocks"]:
            cleaned = []
            for row in block["rows"]:
                if row["type"] in ("spacer", "calc", "check", "growth_yoy"):
                    cleaned.append(row)
                elif row.get("values"):
                    cleaned.append(row)
                # else skip rows with no data
            block["rows"] = cleaned

    # ---- Write output ----
    with open(OUTPUT_PATH, "w") as f:
        json.dump(model, f, indent=2, ensure_ascii=False)

    print(f"\nmodel.json written to {OUTPUT_PATH}")
    print(f"File size: {os.path.getsize(OUTPUT_PATH):,} bytes")

    # ---- Summary ----
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)

    # Count IS periods with data
    is_annual_count = sum(1 for p in annual_periods if p in is_data and len(is_data[p]) > 5)
    is_quarterly_count = sum(1 for p in quarterly_periods if p in is_data and len(is_data[p]) > 5)
    print(f"\nIncome Statement:")
    print(f"  Annual periods with data: {is_annual_count}/10")
    print(f"  Quarterly periods with data: {is_quarterly_count}/9")
    for p in annual_periods:
        if p in is_data:
            print(f"    {p}: {len(is_data[p])} fields")
    for p in quarterly_periods:
        if p in is_data:
            print(f"    {p}: {len(is_data[p])} fields")

    bs_annual_count = sum(1 for p in annual_periods if p in bs_data and len(bs_data[p]) > 5)
    bs_quarterly_count = sum(1 for p in quarterly_periods if p in bs_data and len(bs_data[p]) > 5)
    print(f"\nBalance Sheet:")
    print(f"  Annual periods with data: {bs_annual_count}/10")
    print(f"  Quarterly periods with data: {bs_quarterly_count}/9")
    for p in annual_periods:
        if p in bs_data:
            print(f"    {p}: {len(bs_data[p])} fields")
    for p in quarterly_periods:
        if p in bs_data:
            print(f"    {p}: {len(bs_data[p])} fields")

    cf_annual_count = sum(1 for p in annual_periods if p in cf_data and len(cf_data[p]) > 5)
    cf_quarterly_count = sum(1 for p in quarterly_periods if p in cf_data and len(cf_data[p]) > 5)
    print(f"\nCash Flow:")
    print(f"  Annual periods with data: {cf_annual_count}/10")
    print(f"  Quarterly periods with data: {cf_quarterly_count}/9")
    for p in annual_periods:
        if p in cf_data:
            print(f"    {p}: {len(cf_data[p])} fields")
    for p in quarterly_periods:
        if p in cf_data:
            print(f"    {p}: {len(cf_data[p])} fields")

    # Sheet row counts
    print(f"\nSheet Row Counts:")
    for sheet in model["sheets"]:
        total_rows = sum(len(b["rows"]) for b in sheet["blocks"])
        print(f"  {sheet['label']}: {total_rows} rows across {len(sheet['blocks'])} blocks")

    # Data gaps
    print(f"\nData Gaps:")
    for p in annual_periods:
        gaps = []
        if p not in is_data or len(is_data.get(p, {})) < 10:
            gaps.append(f"IS({len(is_data.get(p, {}))} fields)")
        if p not in bs_data or len(bs_data.get(p, {})) < 10:
            gaps.append(f"BS({len(bs_data.get(p, {}))} fields)")
        if p not in cf_data or len(cf_data.get(p, {})) < 5:
            gaps.append(f"CF({len(cf_data.get(p, {}))} fields)")
        if gaps:
            print(f"  {p}: {', '.join(gaps)}")

    for p in quarterly_periods:
        gaps = []
        if p not in is_data or len(is_data.get(p, {})) < 10:
            gaps.append(f"IS({len(is_data.get(p, {}))} fields)")
        if p not in bs_data or len(bs_data.get(p, {})) < 10:
            gaps.append(f"BS({len(bs_data.get(p, {}))} fields)")
        if p not in cf_data or len(cf_data.get(p, {})) < 5:
            gaps.append(f"CF({len(cf_data.get(p, {}))} fields)")
        if gaps:
            print(f"  {p}: {', '.join(gaps)}")

    # Verify key check values
    print(f"\nCheck Verification:")
    for p in annual_periods + quarterly_periods:
        # IS check: revenue - cost - opex - operating_income should = 0
        if p in is_data:
            d = is_data[p]
            if all(k in d for k in ["total_revenue", "total_cost_of_revenue", "total_operating_expenses", "operating_income"]):
                chk = d["total_revenue"] - d["total_cost_of_revenue"] - d["total_operating_expenses"] - d["operating_income"]
                if abs(chk) > 1:
                    print(f"  IS CHECK FAIL {p}: {chk}")

        # BS check: assets - liabilities - equity should = 0
        if p in bs_data:
            d = bs_data[p]
            if all(k in d for k in ["total_assets", "total_liabilities", "total_stockholders_equity"]):
                chk = d["total_assets"] - d["total_liabilities"] - d["total_stockholders_equity"]
                if abs(chk) > 1:
                    print(f"  BS CHECK FAIL {p}: {chk}")

        # CF check: cfo + cfi + cff + fx - net_change should = 0
        if p in cf_data:
            d = cf_data[p]
            if all(k in d for k in ["cfo_total", "cfi_total", "cff_total", "fx_effect", "net_change_in_cash"]):
                chk = d["cfo_total"] + d["cfi_total"] + d["cff_total"] + d["fx_effect"] - d["net_change_in_cash"]
                if abs(chk) > 1:
                    print(f"  CF CHECK FAIL {p}: {chk}")

    print("\nDone.")


if __name__ == "__main__":
    main()
