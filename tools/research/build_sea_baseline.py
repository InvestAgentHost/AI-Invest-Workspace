#!/usr/bin/env python3
"""Build Sea Limited research baselines from verified official disclosures."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "sources/companies/US/SE-sea/official-website/2026-08-12"
OUT = ROOT / "data/curated/companies/US/SE-sea"
FINANCIAL_SOURCE = {year: "Sea-FY2023-Form-20-F.pdf" if year in {"2021", "2022"} else "Sea-FY2025-Form-20-F.pdf" for year in ("2021", "2022", "2023", "2024", "2025")}

SOURCE_LABELS = {
    "revenue": "Revenue", "cost_of_revenue": "Cost of revenue", "gross_profit": "Gross profit",
    "operating_profit": "Operating income (loss)", "depreciation_amortization": "Depreciation and amortization expenses",
    "income_before_tax": "Income (loss) before income tax", "income_tax_expense": "Income tax expense",
    "net_income_consolidated": "Net income (loss)", "net_income_parent": "Net income (loss) attributable to Sea Limited's ordinary shareholders",
    "net_income_nci": "Net income (loss) attributable to non-controlling interests", "cash_and_equivalents": "Cash and cash equivalents",
    "liquid_investments": "Short-term investments", "trade_receivables": "Accounts receivable, net", "inventory": "Inventories, net",
    "current_assets": "Total current assets", "ppe": "Property and equipment, net", "right_of_use_assets": "Operating lease right-of-use assets, net",
    "goodwill": "Goodwill", "intangible_assets": "Intangible assets, net", "total_assets": "Total assets",
    "short_term_debt": "Borrowings + current convertible notes", "long_term_debt": "Non-current borrowings + non-current convertible notes",
    "current_lease_liabilities": "Current operating lease liabilities", "noncurrent_lease_liabilities": "Non-current operating lease liabilities",
    "trade_payables": "Accounts payable", "current_liabilities": "Total current liabilities", "total_liabilities": "Total liabilities",
    "parent_equity": "Total Sea Limited shareholders' equity", "nci": "Non-controlling interests", "total_equity": "Total equity",
    "cfo": "Net cash generated from (used in) operating activities", "cfi": "Net cash used in investing activities",
    "cff": "Net cash generated from financing activities", "capex_ppe": "Purchase of property and equipment",
    "capex_intangibles": "Purchase of intangible assets", "interest_paid": "Interest paid",
    "cash_begin": "Cash, cash equivalents and restricted cash at beginning of year", "cash_end": "Cash, cash equivalents and restricted cash at end of year",
    "net_change_cash": "Net increase (decrease) in cash, cash equivalents and restricted cash", "fx_cash_effect": "Effect of foreign exchange rate changes on cash, cash equivalents and restricted cash",
}


FINANCIALS = {
    "2021": dict(revenue=9955.190, cost_of_revenue=6059.455, gross_profit=3895.735, operating_profit=-1583.060,
        depreciation_amortization=279.032, income_before_tax=-1715.184, income_tax_expense=332.865,
        net_income_consolidated=-2043.030, net_income_parent=-2046.759, net_income_nci=3.729,
        cash_and_equivalents=9247.762, liquid_investments=911.281, trade_receivables=388.308,
        inventory=117.499, current_assets=15135.397, ppe=1029.963, right_of_use_assets=649.680,
        goodwill=539.624, intangible_assets=52.517, total_assets=18756.025, short_term_debt=100.000,
        long_term_debt=3475.708, current_lease_liabilities=186.494, noncurrent_lease_liabilities=491.313,
        trade_payables=213.580, current_liabilities=7176.436, total_liabilities=11331.616,
        parent_equity=7398.697, nci=25.712, total_equity=7424.409, cfo=208.649, cfi=-3767.273,
        cff=7401.589, capex_ppe=772.177, capex_intangibles=34.999, interest_paid=44.981,
        cash_begin=7053.393, cash_end=10838.140, net_change_cash=3784.747, fx_cash_effect=-58.218),
    "2022": dict(revenue=12449.705, cost_of_revenue=7264.428, gross_profit=5185.277, operating_profit=-1487.508,
        depreciation_amortization=428.344, income_before_tax=-1500.533, income_tax_expense=168.395,
        net_income_consolidated=-1657.772, net_income_parent=-1651.421, net_income_nci=-6.351,
        cash_and_equivalents=6029.859, liquid_investments=864.258, trade_receivables=268.814,
        inventory=109.668, current_assets=12688.012, ppe=1387.895, right_of_use_assets=957.840,
        goodwill=230.208, intangible_assets=65.019, total_assets=17002.796, short_term_debt=119.647,
        long_term_debt=3338.750, current_lease_liabilities=269.968, noncurrent_lease_liabilities=756.818,
        trade_payables=258.648, current_liabilities=6935.692, total_liabilities=11191.972,
        parent_equity=5715.705, nci=95.119, total_equity=5810.824, cfo=-1055.692, cfi=-2428.809,
        cff=400.256, capex_ppe=924.178, capex_intangibles=52.105, interest_paid=103.335,
        cash_begin=10838.140, cash_end=7610.384, net_change_cash=-3227.756, fx_cash_effect=-143.511),
    "2023": dict(revenue=13063.560, cost_of_revenue=7229.913, gross_profit=5833.647, operating_profit=224.778,
        depreciation_amortization=440.845, income_before_tax=432.394, income_tax_expense=262.680,
        net_income_consolidated=162.682, net_income_parent=150.726, net_income_nci=11.956,
        cash_and_equivalents=2811.056, liquid_investments=2547.644, trade_receivables=262.716,
        inventory=125.395, current_assets=11773.934, ppe=1207.698, right_of_use_assets=1015.982,
        goodwill=112.782, intangible_assets=50.821, total_assets=18883.232, short_term_debt=298.425,
        long_term_debt=3069.108, current_lease_liabilities=290.788, noncurrent_lease_liabilities=789.514,
        trade_payables=342.547, current_liabilities=8168.941, total_liabilities=12185.647,
        parent_equity=6593.830, nci=103.755, total_equity=6697.585, cfo=2079.688, cfi=-5804.462,
        cff=366.011, capex_ppe=241.605, capex_intangibles=16.656, interest_paid=119.471,
        cash_begin=7610.384, cash_end=4243.657, net_change_cash=-3366.727, fx_cash_effect=-7.964),
    "2024": dict(revenue=16819.866, cost_of_revenue=9614.778, gross_profit=7205.088, operating_profit=662.152,
        depreciation_amortization=389.673, income_before_tax=778.783, income_tax_expense=321.168,
        net_income_consolidated=447.827, net_income_parent=444.321, net_income_nci=3.506,
        cash_and_equivalents=2405.153, liquid_investments=6215.423, trade_receivables=306.657,
        inventory=143.246, current_assets=16857.668, ppe=1097.699, right_of_use_assets=1054.785,
        goodwill=107.625, intangible_assets=27.310, total_assets=22625.469, short_term_debt=1278.599,
        long_term_debt=1728.258, current_lease_liabilities=300.274, noncurrent_lease_liabilities=803.502,
        trade_payables=350.021, current_liabilities=11296.152, total_liabilities=14147.893,
        parent_equity=8372.335, nci=105.241, total_equity=8477.576, cfo=3277.420, cfi=-5040.846,
        cff=1684.493, capex_ppe=318.153, capex_intangibles=3.440, interest_paid=144.700,
        cash_begin=4243.657, cash_end=4081.585, net_change_cash=-162.072, fx_cash_effect=-83.139),
    "2025": dict(revenue=22938.469, cost_of_revenue=12694.732, gross_profit=10243.737, operating_profit=1985.306,
        depreciation_amortization=372.171, income_before_tax=2280.859, income_tax_expense=651.081,
        net_income_consolidated=1610.894, net_income_parent=1578.149, net_income_nci=32.745,
        cash_and_equivalents=4158.920, liquid_investments=6413.261, trade_receivables=378.047,
        inventory=222.578, current_assets=23249.495, ppe=1306.837, right_of_use_assets=1425.198,
        goodwill=104.462, intangible_assets=12.210, total_assets=29370.979, short_term_debt=1333.252,
        long_term_debt=510.396, current_lease_liabilities=368.115, noncurrent_lease_liabilities=1118.682,
        trade_payables=467.807, current_liabilities=14680.550, total_liabilities=16722.651,
        parent_equity=12526.503, nci=121.825, total_equity=12648.328, cfo=5024.523, cfi=-4408.668,
        cff=1623.183, capex_ppe=513.809, capex_intangibles=10.690, interest_paid=170.151,
        cash_begin=4081.585, cash_end=6419.467, net_change_cash=2337.882, fx_cash_effect=98.844),
}


SEGMENTS = {
    "2021": [("Shopee", 5122.959, -2766.566), ("Monee", 469.774, -640.422), ("Garena", 4320.013, 2500.081), ("Other", 42.444, -177.633)],
    "2022": [("Shopee", 7288.677, -2013.360), ("Monee", 1221.996, -277.264), ("Garena", 3877.163, 1971.416), ("Other", 61.869, -252.162)],
    "2023": [("Shopee", 9000.848, -550.470), ("Monee", 1759.422, 490.209), ("Garena", 2172.009, 1177.871), ("Other", 131.281, -56.728)],
    "2024": [("Shopee", 12415.231, -139.431), ("Monee", 2367.739, 657.502), ("Garena", 1910.589, 978.821), ("Other", 126.307, -43.903)],
    "2025": [("Shopee", 16564.605, 581.052), ("Monee", 3791.641, 972.682), ("Garena", 2408.765, 1184.071), ("Other", 173.458, -90.537)],
}


KPI = {
    "2021": dict(shopee_gmv=62.5, shopee_orders=6.1, shopee_adjusted_ebitda=-2.6, garena_bookings=4.6, garena_adjusted_ebitda=2.8, monee_adjusted_ebitda=-0.617),
    "2022": dict(shopee_gmv=73.5, shopee_orders=7.6, shopee_adjusted_ebitda=-1.7, garena_bookings=2.8, garena_adjusted_ebitda=1.3, monee_adjusted_ebitda=-0.229),
    "2023": dict(shopee_gmv=78.5, shopee_orders=8.2, shopee_adjusted_ebitda=-0.214, garena_bookings=1.8, garena_adjusted_ebitda=0.921, monee_adjusted_ebitda=0.550),
    "2024": dict(shopee_gmv=100.5, shopee_orders=10.9, shopee_adjusted_ebitda=0.156, garena_bookings=2.1, garena_adjusted_ebitda=1.199, monee_adjusted_ebitda=0.712, monee_loans=5.1, monee_npl90=1.2),
    "2025": dict(shopee_gmv=127.4, shopee_orders=13.9, shopee_adjusted_ebitda=0.881, garena_bookings=2.9, garena_adjusted_ebitda=1.656, monee_adjusted_ebitda=1.018, monee_loans=9.2, monee_npl90=1.1),
}

RESTRICTED_CASH = {
    "2021": (1551.635, 38.743, 0.0), "2022": (1549.574, 17.724, 13.227),
    "2023": (1410.365, 22.236, 0.0), "2024": (1655.171, 21.261, 0.0), "2025": (2216.733, 43.814, 0.0),
}

GEOGRAPHY = {
    "2021": {"Southeast Asia including Singapore": 6316.782, "Latin America": 1850.861, "Rest of Asia": 1394.342, "Rest of world": 393.205},
    "2022": {"Southeast Asia including Singapore": 8321.249, "Latin America": 2043.918, "Rest of Asia": 1727.187, "Rest of world": 357.351},
    "2023": {"Singapore": 506.482, "Southeast Asia excluding Singapore": 8673.045, "Latin America": 2193.758, "Rest of Asia": 1496.433, "Rest of world": 193.842},
    "2024": {"Singapore": 659.107, "Southeast Asia excluding Singapore": 11114.896, "Latin America": 3276.281, "Rest of Asia": 1591.487, "Rest of world": 178.095},
    "2025": {"Singapore": 792.705, "Southeast Asia excluding Singapore": 14379.011, "Latin America": 5532.738, "Rest of Asia": 2005.721, "Rest of world": 228.294},
}

MONEE = {
    "2021": dict(net_loans=1529.918, allowance=97.676, provision=117.427, deposits=465.850, escrow=1545.399),
    "2022": dict(net_loans=2075.430, allowance=238.819, provision=513.690, deposits=1316.395, escrow=1862.325),
    "2023": dict(net_loans=2485.213, allowance=321.568, provision=633.942, deposits=1706.299, escrow=2199.464),
    "2024": dict(net_loans=4160.809, allowance=449.335, provision=776.937, deposits=2711.693, escrow=2498.094, consumer_sme_principal=5.1, on_book_principal=4.2, off_book_principal=0.9, npl90_pct=1.2, gross_writeoffs=614.199),
    "2025": dict(net_loans=7964.077, allowance=841.972, provision=1372.616, deposits=3798.250, escrow=3096.764, consumer_sme_principal=9.2, on_book_principal=8.2, off_book_principal=1.0, npl90_pct=1.1, gross_writeoffs=992.892),
}

# Latest audited comparative presentation in the FY2025 20-F. Values are USD
# millions unless noted otherwise. These inputs support Sea-specific derived
# metrics that are not part of the generic three-statement calculator.
SEGMENT_EXPENSES = {
    "2023": {
        "Shopee": dict(revenue=9000.848, cost_of_revenue=6194.900, sales_marketing=2510.693, provision=0.0, other_operating=845.725, segment_profit=-550.470),
        "Monee": dict(revenue=1759.422, cost_of_revenue=279.745, sales_marketing=116.445, provision=630.300, other_operating=242.723, segment_profit=490.209),
        "Garena": dict(revenue=2172.009, cost_of_revenue=672.481, sales_marketing=104.721, provision=0.0, other_operating=216.936, segment_profit=1177.871),
    },
    "2024": {
        "Shopee": dict(revenue=12415.231, cost_of_revenue=8611.530, sales_marketing=2966.084, provision=0.0, other_operating=977.048, segment_profit=-139.431),
        "Monee": dict(revenue=2367.739, cost_of_revenue=348.424, sales_marketing=298.386, provision=771.407, other_operating=292.020, segment_profit=657.502),
        "Garena": dict(revenue=1910.589, cost_of_revenue=610.586, sales_marketing=117.556, provision=0.0, other_operating=203.626, segment_profit=978.821),
    },
    "2025": {
        "Shopee": dict(revenue=16564.605, cost_of_revenue=11380.266, sales_marketing=3546.753, provision=0.0, other_operating=1056.534, segment_profit=581.052),
        "Monee": dict(revenue=3791.641, cost_of_revenue=475.024, sales_marketing=614.228, provision=1365.556, other_operating=364.151, segment_profit=972.682),
        "Garena": dict(revenue=2408.765, cost_of_revenue=791.378, sales_marketing=174.104, provision=0.0, other_operating=259.212, segment_profit=1184.071),
    },
}

CASH_FLOW_BRIDGE = {
    "2023": dict(net_income=162.682, provision=633.942, share_based_compensation=685.030, deferred_revenue_change=-325.160, escrow_payables_change=396.757, accrued_payables_change=455.088, prepaids_other_assets_change=-344.845, cfo=2079.688, loan_receivable_deployment=999.850, deposits_payable_inflow=389.276, securitization_proceeds=119.687, securitization_repayment=0.0),
    "2024": dict(net_income=447.827, provision=776.937, share_based_compensation=715.839, deferred_revenue_change=281.899, escrow_payables_change=467.424, accrued_payables_change=522.785, prepaids_other_assets_change=-39.411, cfo=3277.420, loan_receivable_deployment=2532.291, deposits_payable_inflow=1292.099, securitization_proceeds=185.215, securitization_repayment=0.0),
    "2025": dict(net_income=1610.894, provision=1372.616, share_based_compensation=624.995, deferred_revenue_change=576.100, escrow_payables_change=474.359, accrued_payables_change=650.148, prepaids_other_assets_change=-603.611, cfo=5024.523, loan_receivable_deployment=4707.248, deposits_payable_inflow=1051.423, securitization_proceeds=478.286, securitization_repayment=124.793),
}

GARENA_USERS = {
    "2023": dict(qau_m=527.2, qpu_m=40.2),
    "2024": dict(qau_m=622.3, qpu_m=50.5),
    "2025": dict(qau_m=657.7, qpu_m=62.6),
}

SHARE_DATA = {
    "2023": dict(basic_weighted_average_m=566.612815, diluted_weighted_average_m=594.405604),
    "2024": dict(basic_weighted_average_m=574.966327, diluted_weighted_average_m=604.713980),
    "2025": dict(basic_weighted_average_m=595.023879, diluted_weighted_average_m=638.227141),
}

SHOPEE_SERVICE_MONETIZATION = {"2023": 10.0, "2024": 10.8, "2025": 11.4}
GARENA_ADJUSTED_EBITDA_BOOKINGS = {"2023": 50.9, "2024": 55.8, "2025": 56.1}

BUSINESSES = [
    ("Shopee", "Marketplace", "Third-party buyer-seller marketplace", "Transaction-based fees; advertising; value-added services", "Southeast Asia, Taiwan, Brazil and other disclosed markets", "20-F Item 4 and revenue recognition notes"),
    ("Shopee", "Advertising", "Seller advertising and visibility products", "Advertising fees", "Shopee markets", "20-F Item 4"),
    ("Shopee", "Logistics and fulfillment", "Integrated logistics, fulfillment and related value-added services", "Service fees; some costs may be subsidized", "Shopee markets", "20-F Item 4"),
    ("Shopee", "Direct sales", "Goods sold directly by Sea entities", "Gross product sales", "Selected markets", "20-F revenue recognition notes"),
    ("Shopee", "Affiliate and live commerce", "Creator, affiliate and livestream discovery channels", "Marketplace monetization and advertising support", "Selected Shopee markets", "20-F Item 4"),
    ("Monee", "Wallet and payments", "Mobile wallet and payment processing", "Transaction and service fees", "Southeast Asia and selected markets", "20-F Item 4"),
    ("Monee", "Consumer credit", "On- and off-platform consumer lending", "Interest and fees", "Selected licensed markets", "20-F Item 4 and Note 6"),
    ("Monee", "SME credit", "Working-capital and other loans to sellers and SMEs", "Interest and fees", "Selected licensed markets", "20-F Item 4 and Note 6"),
    ("Monee", "Banking", "Deposit-taking and digital banking through licensed entities", "Net interest and banking fees", "Selected markets", "20-F Item 4"),
    ("Monee", "Insurance and wealth", "Insurance distribution/underwriting and wealth services", "Fees, commissions and premiums", "Selected markets", "20-F Item 4"),
    ("Garena", "Publishing", "Localize, distribute and operate third-party games", "In-game virtual item sales; licensing economics", "Southeast Asia, Taiwan, Latin America and other markets", "20-F Item 4"),
    ("Garena", "Free Fire", "Self-developed global mobile battle royale franchise", "In-game virtual item sales", "Global", "20-F Item 4"),
    ("Garena", "Esports", "Professional leagues and tournaments", "Primarily engagement; standalone revenue not disclosed", "Southeast Asia, Taiwan, Latin America and global events", "20-F Item 4"),
    ("Garena", "Community and platform", "Game discovery, community, operations and payment channels", "Supports bookings and retention; standalone revenue not disclosed", "Garena markets", "20-F Item 4"),
]


def evidence(value: float, key: str, period: str) -> dict:
    filename = FINANCIAL_SOURCE[period]
    statement = "balance_sheet" if key in {"cash_and_equivalents", "liquid_investments", "trade_receivables", "inventory", "current_assets", "ppe", "right_of_use_assets", "goodwill", "intangible_assets", "total_assets", "short_term_debt", "long_term_debt", "current_lease_liabilities", "noncurrent_lease_liabilities", "trade_payables", "current_liabilities", "total_liabilities", "parent_equity", "nci", "total_equity"} else "cash_flow_statement" if key in {"cfo", "cfi", "cff", "capex_ppe", "capex_intangibles", "interest_paid", "cash_begin", "cash_end", "net_change_cash", "fx_cash_effect"} else "income_statement"
    page = "F-7 to F-10" if statement == "balance_sheet" else "F-14 to F-15" if statement == "cash_flow_statement" else "F-11 to F-12"
    mapping = "none"
    if key == "short_term_debt": mapping = "current borrowings plus current convertible notes"
    if key == "long_term_debt": mapping = "non-current borrowings plus non-current convertible notes"
    return {"value": value, "source_label": SOURCE_LABELS[key], "statement": statement, "source": f"sources/companies/US/SE-sea/official-website/2026-08-12/raw/pdfs/{filename}", "page": page, "status": "reported", "mapping": mapping, "confidence": "high"}


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def pdf_pages(path: Path) -> int:
    output = subprocess.run(["pdfinfo", str(path)], check=True, capture_output=True, text=True).stdout
    return int(next(line.split(":", 1)[1].strip() for line in output.splitlines() if line.startswith("Pages:")))


def write_pdf_manifest() -> None:
    current = {}
    manifest_path = SOURCE_ROOT / "pdf-manifest.jsonl"
    if manifest_path.exists():
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            current[Path(row["raw_path"]).name] = row

    api = json.loads((SOURCE_ROOT / "raw/api/financial-resource.json").read_text(encoding="utf-8"))
    urls = {}
    field_to_suffix = {"press_release": "Results", "presentation": "Deck", "transcript": "Transcript", "infographic": "Infographic"}
    for year_entry in api:
        year = int(year_entry["year"])
        if year not in {2021, 2022, 2023, 2024, 2025, 2026}:
            continue
        for item in year_entry["data"]:
            quarter = item.get("quarter")
            if not (quarter == "Q4" and year <= 2025) and not (year == 2026 and quarter == "Q2"):
                continue
            prefix = f"Sea-FY{year}" if quarter == "Q4" else f"Sea-{year}{quarter}"
            for field, suffix in field_to_suffix.items():
                url = (item.get(field) or "").strip()
                if url:
                    urls[f"{prefix}-{suffix}.pdf"] = url
            annual = (item.get("full_year_report") or "").strip()
            if annual:
                urls[f"Sea-FY{year}-Form-20-F.pdf"] = annual

    governance = {
        "Sea-Audit-Committee-Charter.pdf": "Sea%20Limited%20Amended%20and%20Restated%20Audit%20Committee%20Charter.pdf",
        "Sea-Compensation-Committee-Charter.pdf": "Sea%20Limited%20Compensation%20Committee%20Charter.pdf",
        "Sea-Governance-Nominating-Committee-Charter.pdf": "Sea%20Limited%20Corporate%20Governance%20and%20Nominating%20Committee%20Charter.pdf",
        "Sea-Corporate-Governance-Guidelines.pdf": "Sea%20Limited%20Corporate%20Governance%20Guidelines.pdf",
        "Sea-Code-of-Business-Conduct-and-Ethics.pdf": "Sea%20Limited%20Code%20of%20Business%20Conduct%20and%20Ethics.pdf",
    }
    for filename, remote in governance.items():
        urls[filename] = f"https://cdn.sea.com/webmain/static/resource/seagroup/governance/{remote}"

    rows = []
    for path in sorted((SOURCE_ROOT / "raw/pdfs").glob("**/*.pdf")):
        rel = path.relative_to(SOURCE_ROOT).as_posix()
        text_rel = rel.replace("raw/pdfs/", "text/pdfs/").removesuffix(".pdf") + ".txt"
        name = path.name
        fiscal_year = int(name.split("FY", 1)[1][:4]) if "-FY" in name else None
        quarter = "Q2" if "2026Q2" in name else "FY" if fiscal_year else None
        if "Form-20-F" in name: doc_type = "Form 20-F"
        elif "Results" in name: doc_type = "results release"
        elif "Deck" in name: doc_type = "results presentation"
        elif "Transcript" in name: doc_type = "earnings call transcript"
        elif "Infographic" in name: doc_type = "results infographic"
        else: doc_type = "governance document"
        old = current.get(name, {})
        row = {
            "url": urls.get(name, old.get("url", "")), "raw_path": rel, "text_path": text_rel,
            "bytes": path.stat().st_size, "pages": pdf_pages(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "retrieved_at": old.get("retrieved_at", datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")), "content_type": "application/pdf",
            "usable_as_pdf": True, "document_type": doc_type, "fiscal_year": fiscal_year, "quarter": quarter, "error": "",
        }
        for field in ("filing_date", "sec_accession", "sec_primary_document"):
            if field in old: row[field] = old[field]
        rows.append(row)
    with manifest_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    calculator = {"entity": "Sea Limited", "currency": "USD", "scale": "million", "reporting_framework": "US GAAP", "fiscal_year_end": "December 31", "consolidation_scope": "consolidated", "sector": "marketplace, payments and lending, digital entertainment", "as_of_date": "2026-08-12", "period_order": list(FINANCIALS), "notes": ["Monee makes generic liquidity and net-debt metrics incomplete for regulatory analysis.", "Short-term debt includes current convertible notes; long-term debt includes non-current convertible notes."], "periods": {}}
    statement_rows = []
    for period, values in FINANCIALS.items():
        calculator_values = {key: evidence(value, key, period) for key, value in values.items() if key not in {"cash_begin", "cash_end", "net_change_cash"}}
        calculator["periods"][period] = {"period_length_months": 12, "end_date": f"{period}-12-31", "comparability": "comparable", "values": calculator_values}
        for key, value in values.items():
            ev = evidence(value, key, period)
            statement_rows.append({"period": period, "canonical_key": key, "source_label": ev["source_label"], "value_usd_m": value, "source": FINANCIAL_SOURCE[period], "page": ev["page"], "status": "reported", "confidence": "high"})
    (OUT / "sea-financials-normalized-2021-2025.json").write_text(json.dumps(calculator, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv(OUT / "sea-financial-statements-2021-2025.csv", list(statement_rows[0]), statement_rows)

    segment_rows = []
    for period, rows in SEGMENTS.items():
        for segment, revenue, profit in rows:
            segment_rows.append({"period": period, "segment": segment, "revenue_usd_m": revenue, "operating_segment_profit_usd_m": profit, "margin_pct": round(profit / revenue * 100, 2), "source": "FY2025 20-F F-74 to F-75" if period in {"2023", "2024", "2025"} else "FY2023 20-F F-74 to F-76"})
    write_csv(OUT / "sea-segment-financials-2021-2025.csv", list(segment_rows[0]), segment_rows)

    kpi_rows = []
    for period, values in KPI.items():
        for key, value in values.items():
            unit = "percent" if key.endswith("npl90") else "USD billion" if key not in {"shopee_orders"} else "billion orders"
            kpi_rows.append({"period": period, "metric": key, "value": value, "unit": unit, "status": "issuer_apm", "source": f"Sea-FY{period}-Results.pdf"})
    write_csv(OUT / "sea-operating-kpis-2021-2025.csv", list(kpi_rows[0]), kpi_rows)

    cash_rows = []
    for period, (current, noncurrent, held_for_sale) in RESTRICTED_CASH.items():
        v = FINANCIALS[period]
        cash_rows.append({"period": period, "balance_sheet_cash_usd_m": v["cash_and_equivalents"], "current_restricted_cash_usd_m": current, "noncurrent_restricted_cash_usd_m": noncurrent, "held_for_sale_cash_usd_m": held_for_sale, "cash_flow_ending_cash_usd_m": v["cash_end"], "reconciled_difference_usd_m": round(v["cash_end"] - v["cash_and_equivalents"] - current - noncurrent - held_for_sale, 3), "source": FINANCIAL_SOURCE[period], "page": "F-7 and F-15"})
    write_csv(OUT / "sea-cash-reconciliation-2021-2025.csv", list(cash_rows[0]), cash_rows)

    geo_rows = []
    for period, regions in GEOGRAPHY.items():
        for region, value in regions.items():
            geo_rows.append({"period": period, "region": region, "revenue_usd_m": value, "source": FINANCIAL_SOURCE[period], "page": "Note 21, Segment Reporting", "comparability_note": "2021-2022 include Singapore in Southeast Asia; 2023-2025 split Singapore separately"})
    write_csv(OUT / "sea-geographic-revenue-2021-2025.csv", list(geo_rows[0]), geo_rows)

    monee_rows = []
    for period, values in MONEE.items():
        row = {"period": period, **{key: values.get(key, "not disclosed") for key in ("net_loans", "allowance", "provision", "deposits", "escrow", "consumer_sme_principal", "on_book_principal", "off_book_principal", "npl90_pct", "gross_writeoffs")}, "balance_sheet_unit": "USD million", "principal_unit": "USD billion", "source": FINANCIAL_SOURCE[period], "results_source": f"Sea-FY{period}-Results.pdf", "comparability_note": "Results principal and NPL include on- and off-book consumer/SME loans; balance-sheet net loans include other loans and exclude allowance"}
        monee_rows.append(row)
    write_csv(OUT / "sea-monee-credit-funding-2021-2025.csv", list(monee_rows[0]), monee_rows)

    segment_economics_rows = []
    for period, segments in SEGMENT_EXPENSES.items():
        previous_period = str(int(period) - 1)
        for segment, values in segments.items():
            previous = SEGMENT_EXPENSES.get(previous_period, {}).get(segment)
            incremental_margin = "not applicable"
            if previous and values["revenue"] != previous["revenue"]:
                incremental_margin = round((values["segment_profit"] - previous["segment_profit"]) / (values["revenue"] - previous["revenue"]) * 100, 2)
            segment_economics_rows.append({
                "period": period, "segment": segment, **values,
                "segment_margin_pct": round(values["segment_profit"] / values["revenue"] * 100, 2),
                "cost_of_revenue_pct": round(values["cost_of_revenue"] / values["revenue"] * 100, 2),
                "sales_marketing_pct": round(values["sales_marketing"] / values["revenue"] * 100, 2),
                "provision_pct": round(values["provision"] / values["revenue"] * 100, 2),
                "other_operating_pct": round(values["other_operating"] / values["revenue"] * 100, 2),
                "incremental_segment_margin_pct": incremental_margin,
                "source": "Sea-FY2025-Form-20-F.pdf", "page": "F-73 to F-75", "status": "reported inputs; analyst-calculated ratios",
            })
    write_csv(OUT / "sea-segment-economics-2023-2025.csv", list(segment_economics_rows[0]), segment_economics_rows)

    cash_bridge_rows = []
    for period, values in CASH_FLOW_BRIDGE.items():
        capex = FINANCIALS[period]["capex_ppe"] + FINANCIALS[period]["capex_intangibles"]
        cash_after_capex = values["cfo"] - capex
        cash_after_capex_and_loans = cash_after_capex - values["loan_receivable_deployment"]
        cash_bridge_rows.append({
            "period": period, **values, "traditional_capex": round(capex, 3),
            "cash_after_traditional_capex": round(cash_after_capex, 3),
            "cash_after_traditional_capex_and_net_loan_deployment": round(cash_after_capex_and_loans, 3),
            "loan_deployment_pct_revenue": round(values["loan_receivable_deployment"] / FINANCIALS[period]["revenue"] * 100, 2),
            "deposits_plus_net_securitization": round(values["deposits_payable_inflow"] + values["securitization_proceeds"] - values["securitization_repayment"], 3),
            "source": "Sea-FY2025-Form-20-F.pdf", "page": "F-14 to F-15", "status": "reported inputs; analyst-calculated bridge",
        })
    write_csv(OUT / "sea-cfo-capital-bridge-2023-2025.csv", list(cash_bridge_rows[0]), cash_bridge_rows)

    derived_rows = []
    metric_metadata = {
        "incremental_gross_margin_pct": ("percent", "change in gross profit / change in revenue", "analyst_calculated", "2023 is not meaningful because the revenue increment was small and the cost base was reset"),
        "incremental_operating_margin_pct": ("percent", "change in operating profit / change in revenue", "analyst_calculated", "2023 is not meaningful because the revenue increment was small and the cost base was reset"),
        "sbc_pct_revenue": ("percent", "share-based compensation / revenue", "analyst_calculated", "non-cash expense remains an economic dilution cost"),
        "diluted_basic_share_gap_pct": ("percent", "diluted weighted-average shares / basic weighted-average shares - 1", "analyst_calculated", "potential dilution proxy; not a forecast issuance rate"),
        "shopee_gmv_per_order_usd": ("USD per order", "GMV / orders", "analyst_calculated", "market and category mix affect comparability"),
        "shopee_service_monetization_pct": ("percent", "e-commerce service revenue / GMV", "issuer_disclosed", "mixed service monetization proxy; not a commission take rate"),
        "shopee_segment_profit_pct_gmv": ("percent", "statutory segment profit / GMV", "analyst_calculated", "segment revenue includes sales of goods and GMV is an issuer APM"),
        "shopee_adjusted_ebitda_pct_gmv": ("percent", "issuer-adjusted EBITDA / GMV", "analyst_calculated_from_issuer_apm", "not a US GAAP margin"),
        "monee_allowance_pct_gross_loans": ("percent", "allowance / (net loans + allowance)", "analyst_calculated", "gross-loan proxy differs from consumer/SME principal"),
        "monee_provision_pct_average_gross_loans": ("percent", "provision / average(net loans + allowance)", "analyst_calculated", "high-turnover short-duration loans make this unlike an NPL ratio"),
        "monee_writeoffs_pct_average_gross_loans": ("percent", "gross write-offs / average(net loans + allowance)", "analyst_calculated", "2023 comparable gross write-offs not included"),
        "monee_deposits_pct_net_loans": ("percent", "deposits payable / net loans", "analyst_calculated", "not a regulatory funding or liquidity ratio"),
        "monee_revenue_pct_average_gross_loans_proxy": ("percent", "Monee revenue / average(net loans + allowance)", "analyst_calculated", "mixed monetization proxy; must not be called NIM or loan yield"),
        "garena_paying_ratio_pct": ("percent", "average QPU / average QAU", "analyst_calculated", "account counts may duplicate across games or markets"),
        "garena_bookings_per_qpu_usd_account_proxy": ("USD per average quarterly paying account", "annual bookings / average QPU", "analyst_calculated", "not cohort ARPPU; denominator is an average quarterly account metric"),
        "garena_adjusted_ebitda_pct_bookings": ("percent", "adjusted EBITDA / bookings", "issuer_disclosed", "issuer APM definition changes from 2026Q3"),
    }
    for period in ("2023", "2024", "2025"):
        financial = FINANCIALS[period]
        previous = FINANCIALS.get(str(int(period) - 1))
        garena = GARENA_USERS[period]
        shares = SHARE_DATA[period]
        monee = MONEE[period]
        gross_loans = monee["net_loans"] + monee["allowance"]
        prior_monee = MONEE.get(str(int(period) - 1))
        average_gross_loans = None if not prior_monee else (gross_loans + prior_monee["net_loans"] + prior_monee["allowance"]) / 2
        metrics = {
            "incremental_gross_margin_pct": None if not previous else (financial["gross_profit"] - previous["gross_profit"]) / (financial["revenue"] - previous["revenue"]) * 100,
            "incremental_operating_margin_pct": None if not previous else (financial["operating_profit"] - previous["operating_profit"]) / (financial["revenue"] - previous["revenue"]) * 100,
            "sbc_pct_revenue": CASH_FLOW_BRIDGE[period]["share_based_compensation"] / financial["revenue"] * 100,
            "diluted_basic_share_gap_pct": (shares["diluted_weighted_average_m"] / shares["basic_weighted_average_m"] - 1) * 100,
            "shopee_gmv_per_order_usd": KPI[period]["shopee_gmv"] / KPI[period]["shopee_orders"],
            "shopee_service_monetization_pct": SHOPEE_SERVICE_MONETIZATION[period],
            "shopee_segment_profit_pct_gmv": SEGMENT_EXPENSES[period]["Shopee"]["segment_profit"] / (KPI[period]["shopee_gmv"] * 1000) * 100,
            "shopee_adjusted_ebitda_pct_gmv": KPI[period]["shopee_adjusted_ebitda"] / KPI[period]["shopee_gmv"] * 100,
            "monee_allowance_pct_gross_loans": monee["allowance"] / gross_loans * 100,
            "monee_provision_pct_average_gross_loans": None if average_gross_loans is None else monee["provision"] / average_gross_loans * 100,
            "monee_writeoffs_pct_average_gross_loans": None if average_gross_loans is None or "gross_writeoffs" not in monee else monee["gross_writeoffs"] / average_gross_loans * 100,
            "monee_deposits_pct_net_loans": monee["deposits"] / monee["net_loans"] * 100,
            "monee_revenue_pct_average_gross_loans_proxy": None if average_gross_loans is None else SEGMENT_EXPENSES[period]["Monee"]["revenue"] / average_gross_loans * 100,
            "garena_paying_ratio_pct": garena["qpu_m"] / garena["qau_m"] * 100,
            "garena_bookings_per_qpu_usd_account_proxy": KPI[period]["garena_bookings"] * 1000 / garena["qpu_m"],
            "garena_adjusted_ebitda_pct_bookings": GARENA_ADJUSTED_EBITDA_BOOKINGS[period],
        }
        for metric, value in metrics.items():
            unit, formula, status, applicability_note = metric_metadata[metric]
            if period == "2023" and metric in {"incremental_gross_margin_pct", "incremental_operating_margin_pct"}:
                applicability = "not meaningful"
            elif value is None:
                applicability = "not calculable"
            else:
                applicability = "applicable with stated limitation"
            derived_rows.append({
                "period": period, "metric": metric, "value": "not calculable" if value is None else round(value, 2),
                "unit": unit, "formula": formula, "status": status, "applicability": applicability,
                "applicability_note": applicability_note, "source": "FY2025 20-F F-11 to F-15 and F-73 to F-75; annual Results for issuer APMs",
            })
    write_csv(OUT / "sea-derived-fundamental-metrics-2023-2025.csv", list(derived_rows[0]), derived_rows)

    catalog_rows = [{"business": b, "offering": o, "description": d, "monetization": m, "geography": g, "source": s, "as_of": "2026-08-12", "evidence_class": "official fact"} for b, o, d, m, g, s in BUSINESSES]
    write_csv(OUT / "sea-business-catalog-2026-08-12.csv", list(catalog_rows[0]), catalog_rows)

    mapping_rows = []
    for key, label in SOURCE_LABELS.items():
        mapping_rows.append({"canonical_key": key, "source_label": label, "transformation": "sum" if key in {"short_term_debt", "long_term_debt"} else "none", "economic_scope": "current borrowings and current convertible notes" if key == "short_term_debt" else "non-current borrowings and non-current convertible notes" if key == "long_term_debt" else "as reported", "confidence": "high", "comparability_note": "latest audited comparative presentation used", "source_pages": "F-7 to F-10" if key in {"cash_and_equivalents", "liquid_investments", "trade_receivables", "inventory", "current_assets", "ppe", "right_of_use_assets", "goodwill", "intangible_assets", "total_assets", "short_term_debt", "long_term_debt", "current_lease_liabilities", "noncurrent_lease_liabilities", "trade_payables", "current_liabilities", "total_liabilities", "parent_equity", "nci", "total_equity"} else "F-14 to F-15" if key in {"cfo", "cfi", "cff", "capex_ppe", "capex_intangibles", "interest_paid", "cash_begin", "cash_end", "net_change_cash", "fx_cash_effect"} else "F-11 to F-12"})
    write_csv(OUT / "sea-financial-mapping-ledger.csv", list(mapping_rows[0]), mapping_rows)
    write_pdf_manifest()


if __name__ == "__main__":
    main()
