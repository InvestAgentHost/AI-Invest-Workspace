#!/usr/bin/env python3
"""Calculate auditable financial metrics from normalized statement data."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


EVIDENCE_FIELDS = ("value", "source_label", "statement", "source", "page", "status")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate financial metrics from normalized statement JSON."
    )
    parser.add_argument("input", type=Path, help="Normalized JSON input file")
    parser.add_argument(
        "--format", choices=("markdown", "json"), default="markdown"
    )
    parser.add_argument("--output", type=Path, help="Write output to this file")
    parser.add_argument(
        "--include-missing",
        action="store_true",
        help="Include metrics that cannot be calculated and list missing inputs",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on reconciliation errors or incomplete source metadata",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.001,
        help="Relative reconciliation tolerance (default: 0.001)",
    )
    return parser.parse_args()


def load_input(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON at line {exc.lineno}: {exc.msg}") from exc

    if not isinstance(data, dict):
        raise ValueError("Top-level JSON value must be an object")
    periods = data.get("periods")
    if not isinstance(periods, dict) or not periods:
        raise ValueError("Input must contain a non-empty 'periods' object")
    for period, payload in periods.items():
        if not isinstance(payload, dict) or not isinstance(payload.get("values"), dict):
            raise ValueError(f"Period {period!r} must contain a 'values' object")
    return data


def number_from(item: Any) -> float | None:
    if isinstance(item, bool):
        return None
    if isinstance(item, (int, float)):
        value = float(item)
    elif isinstance(item, dict):
        raw = item.get("value")
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            return None
        value = float(raw)
    else:
        return None
    return value if math.isfinite(value) else None


def get_value(data: dict[str, Any], period: str, key: str) -> float | None:
    item = data["periods"][period]["values"].get(key)
    return number_from(item)


def period_order(data: dict[str, Any]) -> list[str]:
    periods = list(data["periods"])
    explicit = data.get("period_order")
    if explicit is None:
        return sorted(periods)
    if not isinstance(explicit, list) or set(explicit) != set(periods):
        raise ValueError("'period_order' must list every period exactly once")
    return [str(period) for period in explicit]


def metric(
    period: str,
    category: str,
    metric_id: str,
    label: str,
    value: float | None,
    unit: str,
    formula: str,
    inputs: dict[str, float] | None = None,
    status: str = "computed",
    note: str = "",
    missing: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "period": period,
        "category": category,
        "id": metric_id,
        "label": label,
        "value": value,
        "unit": unit,
        "formula": formula,
        "inputs": inputs or {},
        "status": status,
        "note": note,
        "missing": missing or [],
    }


def ratio_metric(
    period: str,
    category: str,
    metric_id: str,
    label: str,
    numerator: float | None,
    denominator: float | None,
    numerator_name: str,
    denominator_name: str,
    unit: str,
    formula: str,
    *,
    require_positive_denominator: bool = False,
    note: str = "",
) -> dict[str, Any]:
    missing = []
    if numerator is None:
        missing.append(numerator_name)
    if denominator is None:
        missing.append(denominator_name)
    if missing:
        return metric(
            period,
            category,
            metric_id,
            label,
            None,
            unit,
            formula,
            status="missing",
            missing=missing,
            note=note,
        )
    assert numerator is not None and denominator is not None
    if denominator == 0 or (require_positive_denominator and denominator <= 0):
        return metric(
            period,
            category,
            metric_id,
            label,
            None,
            unit,
            formula,
            inputs={numerator_name: numerator, denominator_name: denominator},
            status="not_meaningful",
            note=(note + "; " if note else "")
            + "denominator is zero or non-positive",
        )
    return metric(
        period,
        category,
        metric_id,
        label,
        numerator / denominator,
        unit,
        formula,
        inputs={numerator_name: numerator, denominator_name: denominator},
        note=note,
    )


def average(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None:
        return None
    return (current + previous) / 2


def add_if_visible(
    output: list[dict[str, Any]], item: dict[str, Any], include_missing: bool
) -> None:
    if item["status"] == "missing" and not include_missing:
        return
    output.append(item)


def derive_period_values(
    data: dict[str, Any], period: str
) -> tuple[dict[str, float | None], list[str]]:
    get = lambda key: get_value(data, period, key)
    notes: list[str] = []

    capex_total = get("capex_total")
    if capex_total is None:
        capex_ppe = get("capex_ppe")
        capex_intangibles = get("capex_intangibles")
        if capex_ppe is not None and capex_intangibles is not None:
            capex_total = capex_ppe + capex_intangibles
            notes.append("capex_total calculated from capex_ppe + capex_intangibles")

    gross_profit = get("gross_profit")
    if gross_profit is None:
        revenue = get("revenue")
        cost = get("cost_of_revenue")
        if revenue is not None and cost is not None:
            gross_profit = revenue - cost
            notes.append("gross_profit calculated from revenue - cost_of_revenue")

    ebitda = get("ebitda_reported")
    ebitda_label = "ebitda_reported"
    if ebitda is None:
        operating_profit = get("operating_profit")
        da = get("depreciation_amortization")
        if operating_profit is not None and da is not None:
            ebitda = operating_profit + da
            ebitda_label = "ebitda_calculated"
            notes.append("ebitda_calculated = operating_profit + depreciation_amortization")

    quick_assets = get("quick_assets")
    if quick_assets is None:
        quick_parts = [
            get("cash_and_equivalents"),
            get("liquid_investments"),
            get("trade_receivables"),
        ]
        if all(value is not None for value in quick_parts):
            quick_assets = sum(value for value in quick_parts if value is not None)
            notes.append(
                "quick_assets calculated from cash + liquid investments + trade receivables"
            )

    short_debt = get("short_term_debt")
    long_debt = get("long_term_debt")
    gross_debt_ex_lease = None
    if short_debt is not None and long_debt is not None:
        gross_debt_ex_lease = short_debt + long_debt

    current_lease = get("current_lease_liabilities")
    noncurrent_lease = get("noncurrent_lease_liabilities")
    lease_liabilities = None
    if current_lease is not None and noncurrent_lease is not None:
        lease_liabilities = current_lease + noncurrent_lease

    gross_debt_incl_lease = None
    if gross_debt_ex_lease is not None and lease_liabilities is not None:
        gross_debt_incl_lease = gross_debt_ex_lease + lease_liabilities

    cash = get("cash_and_equivalents")
    liquid = get("liquid_investments")
    nettable_liquidity = None
    if cash is not None:
        nettable_liquidity = cash + (liquid if liquid is not None else 0.0)
        if liquid is None:
            notes.append("net debt subtracts cash only; liquid_investments not supplied")

    net_debt_ex_lease = None
    if gross_debt_ex_lease is not None and nettable_liquidity is not None:
        net_debt_ex_lease = gross_debt_ex_lease - nettable_liquidity

    net_debt_incl_lease = None
    if gross_debt_incl_lease is not None and nettable_liquidity is not None:
        net_debt_incl_lease = gross_debt_incl_lease - nettable_liquidity

    cfo = get("cfo")
    cash_after_capex = None
    if cfo is not None and capex_total is not None:
        cash_after_capex = cfo - capex_total

    return {
        "gross_profit": gross_profit,
        "ebitda": ebitda,
        "ebitda_label": ebitda_label,
        "quick_assets": quick_assets,
        "capex_total": capex_total,
        "gross_debt_ex_lease": gross_debt_ex_lease,
        "lease_liabilities": lease_liabilities,
        "gross_debt_incl_lease": gross_debt_incl_lease,
        "net_debt_ex_lease": net_debt_ex_lease,
        "net_debt_incl_lease": net_debt_incl_lease,
        "cash_after_capex": cash_after_capex,
    }, notes


def calculate_metrics(
    data: dict[str, Any], periods: list[str], include_missing: bool
) -> tuple[list[dict[str, Any]], list[str]]:
    results: list[dict[str, Any]] = []
    warnings: list[str] = []
    derived: dict[str, dict[str, Any]] = {}

    for period in periods:
        derived[period], notes = derive_period_values(data, period)
        warnings.extend(f"{period}: {note}" for note in notes)

    for index, period in enumerate(periods):
        previous = periods[index - 1] if index else None
        get = lambda key: get_value(data, period, key)
        d = derived[period]
        revenue = get("revenue")
        operating_profit = get("operating_profit")
        consolidated_income = get("net_income_consolidated")
        parent_income = get("net_income_parent")
        current_assets = get("current_assets")
        current_liabilities = get("current_liabilities")
        cash = get("cash_and_equivalents")
        total_assets = get("total_assets")
        total_equity = get("total_equity")
        parent_equity = get("parent_equity")
        cfo = get("cfo")
        capex = d["capex_total"]
        ebitda = d["ebitda"]

        if previous is not None:
            prior_revenue = get_value(data, previous, "revenue")
            item = ratio_metric(
                period,
                "growth",
                "revenue_growth",
                "Revenue growth",
                None if revenue is None or prior_revenue is None else revenue - prior_revenue,
                prior_revenue,
                "revenue change",
                "prior revenue",
                "percent",
                "current revenue / prior revenue - 1",
                require_positive_denominator=True,
            )
            if item["status"] == "computed":
                item["inputs"] = {
                    "current revenue": revenue,
                    "prior revenue": prior_revenue,
                }
            current_months = data["periods"][period].get("period_length_months")
            prior_months = data["periods"][previous].get("period_length_months")
            if (
                current_months is not None
                and prior_months is not None
                and current_months != prior_months
            ):
                item["status"] = "not_comparable"
                item["value"] = None
                item["note"] = (
                    f"period lengths differ: {current_months} months versus {prior_months} months"
                )
            add_if_visible(results, item, include_missing)

        standard_ratios = [
            ("profitability", "gross_margin", "Gross margin", d["gross_profit"], revenue, "gross profit", "revenue", "gross profit / revenue"),
            ("profitability", "operating_margin", "Operating margin", operating_profit, revenue, "operating profit", "revenue", "operating profit / revenue"),
            ("profitability", "ebitda_margin", "EBITDA margin", ebitda, revenue, str(d["ebitda_label"]), "revenue", "EBITDA / revenue"),
            ("profitability", "consolidated_net_margin", "Consolidated net margin", consolidated_income, revenue, "consolidated net income", "revenue", "consolidated net income / revenue"),
            ("profitability", "parent_net_margin", "Parent net margin", parent_income, revenue, "parent net income", "revenue", "parent net income / revenue"),
            ("liquidity", "current_ratio", "Current ratio", current_assets, current_liabilities, "current assets", "current liabilities", "current assets / current liabilities"),
            ("liquidity", "quick_ratio", "Quick ratio", d["quick_assets"], current_liabilities, "quick assets", "current liabilities", "quick assets / current liabilities"),
            ("liquidity", "cash_only_ratio", "Cash-only ratio", cash, current_liabilities, "cash and equivalents", "current liabilities", "cash and equivalents / current liabilities"),
            ("solvency", "equity_ratio", "Equity ratio", total_equity, total_assets, "total equity", "total assets", "total equity / total assets"),
            ("solvency", "gross_debt_ex_lease_assets", "Gross debt ex leases / assets", d["gross_debt_ex_lease"], total_assets, "gross debt ex leases", "total assets", "gross debt excluding leases / total assets"),
            ("solvency", "gross_debt_incl_lease_assets", "Gross debt incl leases / assets", d["gross_debt_incl_lease"], total_assets, "gross debt incl leases", "total assets", "gross debt including leases / total assets"),
            ("solvency", "debt_equity_ex_lease", "Debt / equity ex leases", d["gross_debt_ex_lease"], total_equity, "gross debt ex leases", "total equity", "gross debt excluding leases / total equity"),
            ("solvency", "debt_equity_incl_lease", "Debt / equity incl leases", d["gross_debt_incl_lease"], total_equity, "gross debt incl leases", "total equity", "gross debt including leases / total equity"),
            ("cash_conversion", "cfo_margin", "CFO margin", cfo, revenue, "CFO", "revenue", "CFO / revenue"),
            ("cash_conversion", "cfo_ebitda", "CFO / EBITDA", cfo, ebitda, "CFO", str(d["ebitda_label"]), "CFO / EBITDA"),
            ("cash_conversion", "capex_intensity", "Capex intensity", capex, revenue, "capex", "revenue", "capex / revenue"),
            ("cash_conversion", "cfo_capex", "CFO / capex", cfo, capex, "CFO", "capex", "CFO / capex"),
            ("cash_conversion", "cash_after_capex_margin", "Cash flow after capex margin", d["cash_after_capex"], revenue, "cash flow after capex", "revenue", "(CFO - capex) / revenue"),
        ]
        for category, metric_id, label, num, den, num_name, den_name, formula in standard_ratios:
            require_positive = metric_id in {"cfo_ebitda", "cfo_capex"}
            ratio_units = {
                "current_ratio",
                "quick_ratio",
                "cash_only_ratio",
                "debt_equity_ex_lease",
                "debt_equity_incl_lease",
                "cfo_ebitda",
                "cfo_capex",
            }
            add_if_visible(
                results,
                ratio_metric(
                    period,
                    category,
                    metric_id,
                    label,
                    num,
                    den,
                    num_name,
                    den_name,
                    "ratio" if metric_id in ratio_units else "percent",
                    formula,
                    require_positive_denominator=require_positive,
                ),
                include_missing,
            )

        add_if_visible(
            results,
            ratio_metric(
                period,
                "profitability",
                "adjusted_ebitda_margin",
                "Reported adjusted EBITDA margin",
                get("adjusted_ebitda_reported"),
                get("revenue_ex_pass_through"),
                "reported adjusted EBITDA",
                "revenue ex pass-through",
                "percent",
                "reported adjusted EBITDA / revenue ex pass-through",
                note="issuer-defined APM",
            ),
            include_missing,
        )
        add_if_visible(
            results,
            ratio_metric(
                period,
                "issuer_apm",
                "company_net_debt_adjusted_ebitda",
                "Company NFD / reported adjusted EBITDA",
                get("net_financial_debt_company_reported"),
                get("adjusted_ebitda_reported"),
                "company-reported net financial debt",
                "reported adjusted EBITDA",
                "ratio",
                "company-reported net financial debt / reported adjusted EBITDA",
                require_positive_denominator=True,
                note="issuer-defined debt and earnings APMs; verify whether debt includes leases while earnings are pre-lease",
            ),
            include_missing,
        )
        add_if_visible(
            results,
            ratio_metric(
                period,
                "leverage",
                "company_net_debt_ebitdaal",
                "Company NFD / reported EBITDAaL",
                get("net_financial_debt_company_reported"),
                get("ebitdaal_reported"),
                "company-reported net financial debt",
                "reported EBITDAaL",
                "ratio",
                "company-reported net financial debt / reported EBITDAaL",
                require_positive_denominator=True,
                note="analyst lease-matched ratio using issuer-reported APM inputs; not a company-reported ratio",
            ),
            include_missing,
        )

        debt_bridge = [
            (
                "gross_financial_debt_company_reported",
                "Company-reported gross financial debt",
                get("gross_financial_debt_company_reported"),
                "issuer APM reconciliation",
                {
                    "company-reported gross financial debt": get(
                        "gross_financial_debt_company_reported"
                    )
                },
            ),
            (
                "net_financial_debt_company_reported",
                "Company-reported net financial debt",
                get("net_financial_debt_company_reported"),
                "issuer APM reconciliation",
                {
                    "company-reported net financial debt": get(
                        "net_financial_debt_company_reported"
                    )
                },
            ),
            (
                "gross_debt_ex_lease",
                "Gross debt excluding leases",
                d["gross_debt_ex_lease"],
                "short-term debt + long-term debt",
                {
                    "short-term debt": get("short_term_debt"),
                    "long-term debt": get("long_term_debt"),
                },
            ),
            (
                "lease_liabilities",
                "Lease liabilities",
                d["lease_liabilities"],
                "current lease liabilities + non-current lease liabilities",
                {
                    "current lease liabilities": get("current_lease_liabilities"),
                    "non-current lease liabilities": get("noncurrent_lease_liabilities"),
                },
            ),
            (
                "net_debt_ex_lease",
                "Net debt excluding leases",
                d["net_debt_ex_lease"],
                "gross debt excluding leases - cash - eligible liquid investments",
                {
                    "gross debt excluding leases": d["gross_debt_ex_lease"],
                    "cash and equivalents": cash,
                    "eligible liquid investments": get("liquid_investments"),
                },
            ),
            (
                "net_debt_incl_lease",
                "Net debt including leases",
                d["net_debt_incl_lease"],
                "gross debt including leases - cash - eligible liquid investments",
                {
                    "gross debt including leases": d["gross_debt_incl_lease"],
                    "cash and equivalents": cash,
                    "eligible liquid investments": get("liquid_investments"),
                },
            ),
        ]
        for metric_id, label, value, formula, inputs in debt_bridge:
            if value is not None:
                results.append(
                    metric(
                        period,
                        "debt_bridge",
                        metric_id,
                        label,
                        value,
                        "currency",
                        formula,
                        inputs={key: val for key, val in inputs.items() if val is not None},
                        note="analyst calculation",
                    )
                )
            elif include_missing:
                results.append(
                    metric(
                        period,
                        "debt_bridge",
                        metric_id,
                        label,
                        None,
                        "currency",
                        formula,
                        status="missing",
                        missing=[key for key, val in inputs.items() if val is None],
                    )
                )
        add_if_visible(
            results,
            ratio_metric(
                period,
                "profitability",
                "ebitdaal_margin",
                "Reported EBITDAaL margin",
                get("ebitdaal_reported"),
                get("revenue_ex_pass_through"),
                "reported EBITDAaL",
                "revenue ex pass-through",
                "percent",
                "reported EBITDAaL / revenue ex pass-through",
                note="issuer-defined APM; verify lease definition",
            ),
            include_missing,
        )

        add_if_visible(
            results,
            ratio_metric(
                period,
                "leverage",
                "net_debt_ebitda_ex_lease",
                "Net debt ex leases / EBITDA",
                d["net_debt_ex_lease"],
                ebitda,
                "net debt ex leases",
                str(d["ebitda_label"]),
                "ratio",
                "net debt excluding leases / pre-lease EBITDA",
                require_positive_denominator=True,
                note="analyst calculation; cash and eligible liquid investments are netted",
            ),
            include_missing,
        )
        add_if_visible(
            results,
            ratio_metric(
                period,
                "leverage",
                "net_debt_incl_lease_ebitdaal",
                "Net debt incl leases / EBITDAaL",
                d["net_debt_incl_lease"],
                get("ebitdaal_reported"),
                "net debt incl leases",
                "reported EBITDAaL",
                "ratio",
                "net debt including leases / reported EBITDAaL",
                require_positive_denominator=True,
                note="analyst calculation; use only after verifying the issuer's EBITDAaL definition",
            ),
            include_missing,
        )

        add_if_visible(
            results,
            ratio_metric(
                period,
                "coverage",
                "ebit_interest_coverage",
                "EBIT interest coverage",
                operating_profit,
                get("net_interest_expense"),
                "operating profit",
                "net interest expense",
                "ratio",
                "operating profit / net interest expense",
                require_positive_denominator=True,
            ),
            include_missing,
        )
        add_if_visible(
            results,
            ratio_metric(
                period,
                "coverage",
                "cfo_interest_coverage",
                "CFO cash-interest coverage",
                cfo,
                get("interest_paid"),
                "CFO",
                "cash interest paid",
                "ratio",
                "CFO / cash interest paid",
                require_positive_denominator=True,
                note="inspect whether interest paid is classified within CFO",
            ),
            include_missing,
        )

        cfo_net_income = ratio_metric(
            period,
            "earnings_quality",
            "cfo_net_income",
            "CFO / consolidated net income",
            cfo,
            consolidated_income,
            "CFO",
            "consolidated net income",
            "ratio",
            "CFO / consolidated net income",
            require_positive_denominator=True,
        )
        if cfo_net_income["status"] == "not_meaningful":
            cfo_net_income["note"] = "net income is zero or negative; use the CFO bridge instead"
        add_if_visible(results, cfo_net_income, include_missing)

        if d["cash_after_capex"] is not None:
            results.append(
                metric(
                    period,
                    "cash_conversion",
                    "cash_flow_after_capex",
                    "Cash flow after capex",
                    d["cash_after_capex"],
                    "currency",
                    "CFO - capex_total",
                    inputs={"CFO": cfo, "capex_total": capex},
                    note="analyst calculation; not automatically the issuer's FCF",
                )
            )
        elif include_missing:
            missing = [name for name, value in (("CFO", cfo), ("capex_total", capex)) if value is None]
            results.append(
                metric(
                    period,
                    "cash_conversion",
                    "cash_flow_after_capex",
                    "Cash flow after capex",
                    None,
                    "currency",
                    "CFO - capex_total",
                    status="missing",
                    missing=missing,
                )
            )

        da = get("depreciation_amortization")
        add_if_visible(
            results,
            ratio_metric(
                period,
                "cash_conversion",
                "da_capex",
                "D&A / capex",
                da,
                capex,
                "D&A",
                "capex",
                "ratio",
                "D&A / capex_total",
                require_positive_denominator=True,
            ),
            include_missing,
        )

        if previous is not None:
            prior_assets = get_value(data, previous, "total_assets")
            prior_parent_equity = get_value(data, previous, "parent_equity")
            prior_total_equity = get_value(data, previous, "total_equity")
            avg_assets = average(total_assets, prior_assets)
            avg_parent_equity = average(parent_equity, prior_parent_equity)
            avg_total_equity = average(total_equity, prior_total_equity)

            return_metrics = [
                ("roa", "ROA", consolidated_income, avg_assets, "consolidated net income", "average total assets", "consolidated net income / average total assets"),
                ("parent_roe", "Parent ROE", parent_income, avg_parent_equity, "parent net income", "average parent equity", "parent net income / average parent equity"),
                ("consolidated_roe", "Consolidated ROE", consolidated_income, avg_total_equity, "consolidated net income", "average total equity", "consolidated net income / average total equity"),
                ("asset_turnover", "Asset turnover", revenue, avg_assets, "revenue", "average total assets", "revenue / average total assets"),
            ]
            for metric_id, label, num, den, num_name, den_name, formula in return_metrics:
                add_if_visible(
                    results,
                    ratio_metric(
                        period,
                        "returns",
                        metric_id,
                        label,
                        num,
                        den,
                        num_name,
                        den_name,
                        "ratio" if metric_id == "asset_turnover" else "percent",
                        formula,
                    ),
                    include_missing,
                )

            if consolidated_income is not None and cfo is not None:
                accrual_num = consolidated_income - cfo
            else:
                accrual_num = None
            add_if_visible(
                results,
                ratio_metric(
                    period,
                    "earnings_quality",
                    "accrual_ratio",
                    "Accrual ratio",
                    accrual_num,
                    avg_assets,
                    "net income minus CFO",
                    "average total assets",
                    "percent",
                    "(consolidated net income - CFO) / average total assets",
                ),
                include_missing,
            )

            avg_receivables = average(
                get("trade_receivables"),
                get_value(data, previous, "trade_receivables"),
            )
            avg_inventory = average(
                get("inventory"), get_value(data, previous, "inventory")
            )
            avg_payables = average(
                get("trade_payables"), get_value(data, previous, "trade_payables")
            )
            cost = get("cost_of_revenue")
            days = 365.0
            dso = None if avg_receivables is None or revenue in (None, 0) else avg_receivables / revenue * days
            dio = None if avg_inventory is None or cost in (None, 0) else avg_inventory / cost * days
            dpo = None if avg_payables is None or cost in (None, 0) else avg_payables / cost * days

            working_metrics = [
                ("dso", "Days sales outstanding", dso, "average trade receivables / revenue * 365", {"average trade receivables": avg_receivables, "revenue": revenue}),
                ("dio", "Days inventory outstanding", dio, "average inventory / cost of revenue * 365", {"average inventory": avg_inventory, "cost of revenue": cost}),
                ("dpo", "Days payables outstanding", dpo, "average trade payables / cost of revenue * 365", {"average trade payables": avg_payables, "cost of revenue": cost}),
            ]
            for metric_id, label, value, formula, inputs in working_metrics:
                if value is not None:
                    results.append(metric(period, "working_capital", metric_id, label, value, "days", formula, inputs=inputs))
                elif include_missing:
                    missing = [key for key, val in inputs.items() if val is None]
                    results.append(metric(period, "working_capital", metric_id, label, None, "days", formula, status="missing", missing=missing))

            if dso is not None and dio is not None and dpo is not None:
                results.append(
                    metric(
                        period,
                        "working_capital",
                        "cash_conversion_cycle",
                        "Cash conversion cycle",
                        dso + dio - dpo,
                        "days",
                        "DSO + DIO - DPO",
                        inputs={"DSO": dso, "DIO": dio, "DPO": dpo},
                        note="DPO uses cost of revenue unless purchases are supplied separately",
                    )
                )
            elif include_missing:
                results.append(
                    metric(
                        period,
                        "working_capital",
                        "cash_conversion_cycle",
                        "Cash conversion cycle",
                        None,
                        "days",
                        "DSO + DIO - DPO",
                        status="missing",
                        missing=[name for name, value in (("DSO", dso), ("DIO", dio), ("DPO", dpo)) if value is None],
                    )
                )

        add_if_visible(
            results,
            ratio_metric(
                period,
                "issuer_apm",
                "company_fcf_margin",
                "Company-reported FCF margin",
                get("fcf_company_reported"),
                revenue,
                "company-reported FCF",
                "revenue",
                "percent",
                "company-reported FCF / revenue",
                note="issuer-defined APM; preserve the issuer reconciliation",
            ),
            include_missing,
        )

    return results, warnings


def close_enough(left: float, right: float, tolerance: float) -> bool:
    return math.isclose(left, right, rel_tol=tolerance, abs_tol=max(0.01, tolerance))


def check_item(
    period: str,
    check_id: str,
    label: str,
    left: float,
    right: float,
    tolerance: float,
    formula: str,
) -> dict[str, Any]:
    difference = left - right
    return {
        "period": period,
        "id": check_id,
        "label": label,
        "status": "pass" if close_enough(left, right, tolerance) else "fail",
        "left": left,
        "right": right,
        "difference": difference,
        "formula": formula,
    }


def reconciliation_checks(
    data: dict[str, Any], periods: list[str], tolerance: float
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for period in periods:
        get = lambda key: get_value(data, period, key)

        assets, liabilities, equity = get("total_assets"), get("total_liabilities"), get("total_equity")
        if assets is not None and liabilities is not None and equity is not None:
            checks.append(check_item(period, "balance_sheet", "Assets = liabilities + equity", assets, liabilities + equity, tolerance, "total assets = total liabilities + total equity"))

        consolidated, parent, nci = get("net_income_consolidated"), get("net_income_parent"), get("net_income_nci")
        if consolidated is not None and parent is not None and nci is not None:
            checks.append(check_item(period, "income_attribution", "Consolidated income = parent + NCI", consolidated, parent + nci, tolerance, "consolidated net income = parent net income + NCI net income"))

        cash_begin, cash_end, net_change = get("cash_begin"), get("cash_end"), get("net_change_cash")
        if cash_begin is not None and cash_end is not None and net_change is not None:
            checks.append(check_item(period, "cash_change", "Ending cash = beginning cash + net change", cash_end, cash_begin + net_change, tolerance, "cash_end = cash_begin + net_change_cash"))

        cfo, cfi, cff = get("cfo"), get("cfi"), get("cff")
        fx, other = get("fx_cash_effect"), get("other_cash_effect")
        if all(value is not None for value in (cfo, cfi, cff, fx, other, net_change)):
            cash_components = cfo + cfi + cff + fx + other
            checks.append(check_item(period, "cash_flow", "Net cash change = CFO + CFI + CFF + FX + other", net_change, cash_components, tolerance, "net_change_cash = CFO + CFI + CFF + FX + other_cash_effect"))

        balance_cash = get("cash_and_equivalents")
        if cash_end is not None and balance_cash is not None:
            checks.append(check_item(period, "cash_to_balance_sheet", "Cash-flow ending cash = balance-sheet cash", cash_end, balance_cash, tolerance, "cash_end = cash_and_equivalents"))
    return checks


def metadata_issues(data: dict[str, Any], periods: list[str]) -> list[str]:
    issues: list[str] = []
    for period in periods:
        for key, item in data["periods"][period]["values"].items():
            if isinstance(item, (int, float)) and not isinstance(item, bool):
                issues.append(f"{period}.{key}: bare number has no source metadata")
            elif isinstance(item, dict):
                missing = [field for field in EVIDENCE_FIELDS if field not in item]
                if missing:
                    issues.append(f"{period}.{key}: missing evidence fields {', '.join(missing)}")
            else:
                issues.append(f"{period}.{key}: value is not numeric or an evidence object")
    return issues


def evidence_index(data: dict[str, Any], periods: list[str]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for period in periods:
        for key, item in data["periods"][period]["values"].items():
            if not isinstance(item, dict) or number_from(item) is None:
                continue
            evidence.append(
                {
                    "period": period,
                    "key": key,
                    "value": number_from(item),
                    "source_label": item.get("source_label", ""),
                    "statement": item.get("statement", ""),
                    "source": item.get("source", ""),
                    "page": item.get("page", ""),
                    "status": item.get("status", ""),
                    "mapping": item.get("mapping", ""),
                    "confidence": item.get("confidence", ""),
                }
            )
    return evidence


def format_number(value: float | None, unit: str, scale: str) -> str:
    if value is None:
        return "n/a"
    if unit == "percent":
        return f"{value * 100:.2f}%"
    if unit == "ratio":
        return f"{value:.2f}x"
    if unit == "days":
        return f"{value:.1f} days"
    if unit == "currency":
        return f"{value:,.3f} {scale}"
    return f"{value:.4f}"


def input_summary(inputs: dict[str, float]) -> str:
    return "; ".join(f"{key}={value:,.3f}" for key, value in inputs.items())


def render_markdown(payload: dict[str, Any]) -> str:
    metadata = payload["metadata"]
    lines = [
        "# Derived Financial Metrics",
        "",
        f"- Entity: {metadata['entity']}",
        f"- Currency/scale: {metadata['currency']} {metadata['scale']}",
        f"- Periods: {', '.join(metadata['periods'])}",
        "",
        "## Reconciliation Checks",
        "",
    ]
    checks = payload["checks"]
    if checks:
        lines.extend([
            "| Period | Check | Status | Difference | Formula |",
            "|---|---|---|---:|---|",
        ])
        for check in checks:
            lines.append(
                f"| {check['period']} | {check['label']} | {check['status']} | {check['difference']:,.6f} | {check['formula']} |"
            )
    else:
        lines.append("No reconciliation check had all required inputs.")

    lines.extend(["", "## Metrics", ""])
    if payload["metrics"]:
        lines.extend([
            "| Period | Category | Metric | Result | Status | Formula and inputs |",
            "|---|---|---|---:|---|---|",
        ])
        for item in payload["metrics"]:
            result = format_number(item["value"], item["unit"], metadata["scale"])
            details = item["formula"]
            if item["inputs"]:
                details += "; " + input_summary(item["inputs"])
            if item["missing"]:
                details += "; missing: " + ", ".join(item["missing"])
            if item["note"]:
                details += "; " + item["note"]
            lines.append(
                f"| {item['period']} | {item['category']} | {item['label']} | {result} | {item['status']} | {details} |"
            )
    else:
        lines.append("No metrics could be calculated from the supplied inputs.")

    if payload["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in payload["warnings"])

    if payload["evidence_issues"]:
        lines.extend(["", "## Evidence Metadata Issues", ""])
        lines.extend(f"- {issue}" for issue in payload["evidence_issues"])

    if payload["evidence"]:
        lines.extend(
            [
                "",
                "## Evidence Index",
                "",
                "| Period | Canonical key | Value | Source label | Statement | Source locator | Status |",
                "|---|---|---:|---|---|---|---|",
            ]
        )
        for item in payload["evidence"]:
            locator = item["source"]
            if item["page"]:
                locator += f"; {item['page']}"
            lines.append(
                f"| {item['period']} | {item['key']} | {item['value']:,.3f} | "
                f"{item['source_label']} | {item['statement']} | {locator} | {item['status']} |"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    try:
        data = load_input(args.input)
        periods = period_order(data)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    metrics, warnings = calculate_metrics(data, periods, args.include_missing)
    checks = reconciliation_checks(data, periods, args.tolerance)
    evidence_issues = metadata_issues(data, periods)
    if evidence_issues:
        warnings.append(
            f"{len(evidence_issues)} input value(s) lack complete source metadata; "
            "use --strict for the itemized list and a failing exit status"
        )

    payload = {
        "metadata": {
            "entity": data.get("entity", "Unknown entity"),
            "currency": data.get("currency", "unspecified currency"),
            "scale": data.get("scale", "unspecified scale"),
            "periods": periods,
        },
        "checks": checks,
        "metrics": metrics,
        "warnings": warnings,
        "evidence_issues": evidence_issues if args.strict else [],
        "evidence": evidence_index(data, periods),
    }

    if args.format == "json":
        rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    else:
        rendered = render_markdown(payload)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)

    strict_failures = [check for check in checks if check["status"] == "fail"]
    if args.strict and (strict_failures or evidence_issues):
        print(
            f"strict validation failed: {len(strict_failures)} reconciliation error(s), "
            f"{len(evidence_issues)} evidence metadata issue(s)",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
