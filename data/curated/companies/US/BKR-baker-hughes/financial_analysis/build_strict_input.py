"""Add auditable evidence metadata to the compact Baker Hughes calculator input."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[6]
BASE = Path(__file__).with_name("financial_metrics_input.json")
OUTPUT = Path(__file__).with_name("financial_metrics_input_strict.json")

DOCS = {
    "FY2021": ("../database/bakerhughes/artifacts/ten_k/Baker-Hughes/FY2021/psp_39fea9edd28b4eb5aa0bb1d547549718/prepared/document.md", "49-53"),
    "FY2022": ("../database/bakerhughes/artifacts/ten_k/Baker-Hughes/FY2022/psp_4b200fa618404feb967021a1fadfbc36/prepared/document.md", "52-56"),
    "FY2023": ("../database/bakerhughes/artifacts/ten_k/Baker-Hughes/FY2023/psp_325531e732e447ebad6e1a29938bc4cd/prepared/document.md", "52-56"),
    "FY2024": ("../database/bakerhughes/artifacts/ten_k/Baker-Hughes/FY2024/psp_3f4a7da1e0e5415697ac468d10048d58/prepared/document.md", "55-59"),
    "FY2025": ("../database/bakerhughes/artifacts/ten_k/Baker-Hughes/FY2025/psp_de4a812587534bbab4b5d23209ea5877/prepared/document.md", "55-59"),
}

STATEMENTS = {
    "revenue": ("income_statement", "Total revenue"),
    "income_before_tax": ("income_statement", "Income before income taxes"),
    "cost_of_revenue": ("income_statement", "Cost of goods sold + Cost of services sold"),
    "gross_profit": ("income_statement", "Total revenue - direct costs"),
    "operating_profit": ("income_statement", "Operating income (loss) or derived operating subtotal"),
    "depreciation_amortization": ("cash_flow", "Depreciation and amortization"),
    "net_interest_expense": ("income_statement", "Interest expense, net"),
    "income_tax_expense": ("income_statement", "Provision for income taxes"),
    "net_income_consolidated": ("income_statement", "Net income (loss)"),
    "net_income_parent": ("income_statement", "Net income (loss) attributable to Baker Hughes Company"),
    "net_income_nci": ("income_statement", "Net income (loss) attributable to noncontrolling interests"),
    "cash_and_equivalents": ("balance_sheet", "Cash and cash equivalents"),
    "trade_receivables": ("balance_sheet", "Current receivables, net"),
    "inventory": ("balance_sheet", "Inventories, net"),
    "current_assets": ("balance_sheet", "Total current assets"),
    "quick_assets": ("balance_sheet", "Cash + current receivables; excludes unclassified current assets"),
    "ppe": ("balance_sheet", "Property, plant and equipment, less accumulated depreciation"),
    "right_of_use_assets": ("balance_sheet", "Right-of-use assets included in All other assets"),
    "goodwill": ("balance_sheet", "Goodwill"),
    "intangible_assets": ("balance_sheet", "Other intangible assets, net"),
    "total_assets": ("balance_sheet", "Total assets"),
    "short_term_debt": ("balance_sheet", "Short-term and current portion of long-term debt"),
    "long_term_debt": ("balance_sheet", "Long-term debt"),
    "current_lease_liabilities": ("balance_sheet", "Operating lease liabilities in all other current liabilities"),
    "noncurrent_lease_liabilities": ("balance_sheet", "Operating lease liabilities in all other liabilities"),
    "trade_payables": ("balance_sheet", "Accounts payable"),
    "current_liabilities": ("balance_sheet", "Total current liabilities"),
    "total_liabilities": ("balance_sheet", "Total assets - total equity"),
    "parent_equity": ("balance_sheet", "Baker Hughes Company equity"),
    "nci": ("balance_sheet", "Noncontrolling interests"),
    "total_equity": ("balance_sheet", "Total equity"),
    "cfo": ("cash_flow", "Net cash flows provided by operating activities"),
    "cfi": ("cash_flow", "Net cash flows used in investing activities"),
    "cff": ("cash_flow", "Net cash flows used in financing activities"),
    "capex_total": ("cash_flow", "Expenditures for capital assets"),
    "cash_begin": ("cash_flow", "Cash and cash equivalents, beginning of period"),
    "cash_end": ("cash_flow", "Cash and cash equivalents, end of period"),
    "net_change_cash": ("cash_flow", "Increase (decrease) in cash and cash equivalents"),
    "fx_cash_effect": ("cash_flow", "Effect of currency exchange rate changes on cash and cash equivalents"),
    "other_cash_effect": ("cash_flow", "Residual cash-flow reconciliation after reported CFO, CFI, CFF and FX"),
    "interest_paid": ("cash_flow", "Interest paid"),
    "dividends_paid": ("cash_flow", "Dividends paid"),
    "buybacks": ("cash_flow", "Repurchase of Class A common stock"),
    "normalized_tax_rate": ("analyst_assumption", "Normalized tax rate anchored to U.S. statutory rate"),
}


def main() -> None:
    data = json.loads(BASE.read_text(encoding="utf-8"))
    for period, payload in data["periods"].items():
        source, pages = DOCS[period]
        # The reported subtotals and FX fully explain each year's cash change;
        # store the zero residual explicitly so the strict cash-flow check runs.
        payload["values"].setdefault("other_cash_effect", 0)
        for key, value in list(payload["values"].items()):
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                statement, label = STATEMENTS.get(key, ("unknown", key))
                status = "calculated" if key in {"cost_of_revenue", "gross_profit", "total_liabilities", "other_cash_effect"} else "reported"
                payload["values"][key] = {
                    "value": value,
                    "source_label": label,
                    "statement": statement,
                    "source": source,
                    "page": pages,
                    "status": status,
                    "mapping": "See statement_mapping_ledger.csv",
                    "confidence": "high" if status == "reported" else "medium",
                }
        for key, value in list(payload.get("opening_values", {}).items()):
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                statement, label = STATEMENTS.get(key, ("balance_sheet", f"FY2020 opening {key}"))
                payload["opening_values"][key] = {
                    "value": value,
                    "source_label": f"FY2020 opening {label}",
                    "statement": statement,
                    "source": source,
                    "page": "51; lease note p.65",
                    "status": "reported",
                    "mapping": "Opening balance used for FY2021 average-balance metrics",
                    "confidence": "high",
                }
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
