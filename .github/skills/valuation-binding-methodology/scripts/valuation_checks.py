"""Read-only independent checks. Stdlib only; JSON results on stdout."""
import argparse
from datetime import date, datetime, timedelta
import json
import math
import re
from pathlib import Path, PurePosixPath


METHOD = "dividend-pfcf-net-shares-v3"
CASH_USES = ("debt_principal", "finance_lease_principal", "acquisitions", "other_necessary_uses")
CASH_INFLOWS = ("financing_inflow", "other_inflows", "equity_issuance_cash")


def number(value, label, minimum=None, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label}: finite numeric value required; missing is not zero")
    if (positive and value <= 0) or (minimum is not None and value < minimum):
        raise ValueError(f"{label}: out of range")
    return float(value)


def iso(value):
    return date.fromisoformat(value)


def present_value(flows, rate):
    if rate <= -1:
        raise ValueError("discount rate must exceed -100%")
    return sum(amount / (1 + rate) ** years for amount, years in flows)


def solve_return(price, flows):
    """Unique root for positive holder inflows after the investment date."""
    if not flows or any(a < 0 or t <= 0 for a, t in flows) or not any(a > 0 for a, _ in flows):
        raise ValueError("this solver requires nonnegative future cash flows and a positive terminal")
    low, high = -0.9999, 1.0
    while present_value(flows, high) > price and high < 1e6:
        high = 2 * high + 1
    if present_value(flows, low) < price or present_value(flows, high) > price:
        raise ValueError("IRR root outside supported bracket")
    for _ in range(160):
        mid = (low + high) / 2
        if present_value(flows, mid) > price:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def cumulative_to_quarters(cumulative):
    """Amounts only, with identical scope; not EPS, ratios or stock balances."""
    values = [number(v, "cumulative amount") for v in cumulative]
    return [v - (values[i - 1] if i else 0) for i, v in enumerate(values)]


# Reject incompatible conventions rather than silently reinterpreting old packets.
LEGACY_FIELDS = {"market_cap", "exit_pe", "net_shrink", "fcf_conversion", "payout",
                 "buyback_pe", "dilution_rate", "budget_fcf", "dividend_after_valuation"}
VALUATION_INPUTS = ("exit_p_fcf", "fcf_conversion_start", "fcf_conversion_exit",
                    "payout_ratio", "net_share_change")


def reject_legacy(record, label):
    legacy = LEGACY_FIELDS.intersection(record)
    if legacy:
        raise ValueError(f"{label}: legacy fields unsupported: {', '.join(sorted(legacy))}")


def valuation_inputs(record, label):
    values = {k: number(record.get(k), f"{label}.{k}") for k in VALUATION_INPUTS}
    if values["exit_p_fcf"] <= 0:
        raise ValueError(f"{label}: exit P/FCF must be positive")
    if values["fcf_conversion_exit"] <= 0:
        raise ValueError(f"{label}: exit FCF conversion must be positive for this route")
    if min(values[k] for k in ("fcf_conversion_start", "fcf_conversion_exit", "payout_ratio")) < 0:
        raise ValueError(f"{label}: conversion and payout must be nonnegative")
    if values["net_share_change"] <= -1:
        raise ValueError(f"{label}: net share change must exceed -100%")
    return values


def annual_parameters(inputs, periods, overrides=None, issuance=None):
    """Resolve defaults plus dated overrides; shared by calculation and snapshots."""
    fields = {"fcf_conversion", "payout_ratio", "net_share_change", "annual_issuance_rate"}
    changes = {}
    if overrides is None:
        overrides = []
    if not isinstance(overrides, list):
        raise ValueError("annual_overrides must be an array")
    for entry in overrides:
        if not isinstance(entry, dict) or set(entry) - fields - {"period_end"}:
            raise ValueError("annual_overrides: unknown field or invalid entry")
        period = entry.get("period_end")
        if period not in periods or period in changes or not (set(entry) & fields):
            raise ValueError("annual_overrides: period must be unique, in the forecast, and have values")
        changes[period] = entry
    resolved = []
    for i, period in enumerate(periods):
        c0, cH = inputs["fcf_conversion_start"], inputs["fcf_conversion_exit"]
        row = {"fcf_conversion": cH if len(periods) == 1 else c0 + (cH - c0) * i / (len(periods) - 1),
               "payout_ratio": inputs["payout_ratio"], "net_share_change": inputs["net_share_change"],
               "annual_issuance_rate": issuance}
        for key, value in changes.get(period, {}).items():
            if key != "period_end":
                row[key] = number(value, f"{period}.{key}")
        if row["payout_ratio"] < 0 or row["net_share_change"] <= -1:
            raise ValueError(f"{period}: payout must be nonnegative and net share change exceed -100%")
        d = row["annual_issuance_rate"]
        if d is not None:
            number(d, f"{period} issuance", minimum=0)
            if row["net_share_change"] > d:
                raise ValueError(f"{period}: net share change exceeds gross issuance; supported share bridge required")
        resolved.append(row)
    if resolved and resolved[-1]["fcf_conversion"] <= 0:
        raise ValueError("exit FCF conversion must be positive for this route")
    return resolved


def calculate(model):
    """One adopted case, per-share holder flows; FCF is not a holder cash flow."""
    if model.get("method_version") != METHOD:
        raise ValueError("unsupported/legacy method; replace inputs explicitly before calculation")
    reject_legacy(model, "model")
    for key in ("currency", "amount_unit", "share_unit"):
        if not model.get(key):
            raise ValueError(f"{key}: required")
    if model["amount_unit"] != model["share_unit"]:
        raise ValueError("amount/share scale must match for per-share outputs")
    start = iso(model["valuation_date"])
    base_ni = number(model.get("base_net_income"), "base net income", positive=True)
    n0 = number(model.get("current_shares"), "adopted valuation-date shares", positive=True)
    required = number(model.get("required_return"), "required return")
    if required <= -1:
        raise ValueError("required return must exceed -100%")
    inputs = valuation_inputs(model, "model")
    multiple = inputs["exit_p_fcf"]
    issuance = (None if model.get("annual_issuance_rate") is None else
                number(model["annual_issuance_rate"], "annual issuance rate", minimum=0))
    periods = model.get("years")
    if not isinstance(periods, list) or not periods:
        raise ValueError("no forecast periods")
    parameters = annual_parameters(inputs, [year["period_end"] for year in periods],
                                   model.get("annual_overrides"), issuance)
    cash_balance = model.get("opening_available_cash")
    gaps, failures, rows, dividends = [], [], [], []
    if cash_balance is None:
        gaps.append("opening available cash missing")
    else:
        cash_balance = number(cash_balance, "opening available cash", minimum=0)
    shares, prior_end = n0, start
    for i, year in enumerate(periods):
        tag = f"period {i + 1}"
        reject_legacy(year, tag)
        end, begin, payment = (iso(year[k]) for k in ("period_end", "period_start", "cashflow_date"))
        if not 350 <= (end - begin).days + 1 <= 380:
            raise ValueError(f"{tag}: annual profit period required (including 52/53-week years)")
        if begin != prior_end + timedelta(days=1):
            raise ValueError(f"{tag}: forecast periods must begin one day after base/prior fiscal end")
        if payment != end:
            raise ValueError(f"{tag}: cashflow date must equal annual fiscal end approximation")
        ni = number(year.get("net_income"), tag + " net income", positive=True)
        adopted = parameters[i]
        conversion, payout, change, issuance = (adopted[k] for k in
            ("fcf_conversion", "payout_ratio", "net_share_change", "annual_issuance_rate"))
        shares *= 1 + change
        fcf = ni * conversion
        if "fcf" in year and not math.isclose(number(year["fcf"], tag + " FCF"), fcf,
                                              rel_tol=1e-7, abs_tol=1e-9):
            failures.append(f"{tag}: independently forecast FCF conflicts with conversion")
        dividend = ni * payout
        dps = dividend / shares
        cash = year.get("cash", {})
        if not isinstance(cash, dict):
            raise ValueError(f"{tag}: cash must be an object")
        reject_legacy(cash, tag + " cash")
        proxy_buyback = (None if issuance is None or fcf < 0 else
                         fcf * multiple * (issuance - change) / (1 + change))
        buyback = (number(cash["gross_buyback_cash"], tag + " gross buyback", minimum=0)
                   if "gross_buyback_cash" in cash else proxy_buyback)
        distribution = None if buyback is None else dividend + buyback
        coverage_status = ("PARTIAL" if distribution is None else
                           "PASS" if fcf + 1e-8 >= distribution else "FAIL")
        if buyback is None:
            gaps.append(f"{tag}: gross buyback budget missing; proxy needs issuance and nonnegative FCF")
        needed = CASH_USES + CASH_INFLOWS + ("minimum_cash",)
        missing = [k for k in needed if k not in cash or cash[k] is None]
        if missing:
            gaps.append(f"{tag}: missing cash fields {', '.join(missing)}")
        for key in needed:
            if key not in missing:
                number(cash[key], tag + " " + key, minimum=0)
        before_cash = cash_balance
        if missing or cash_balance is None or distribution is None:
            cash_balance, funding_status = None, "PARTIAL"
        else:
            cash_balance += (fcf + sum(cash[k] for k in CASH_INFLOWS)
                             - distribution - sum(cash[k] for k in CASH_USES))
            funding_status = "PASS" if cash_balance + 1e-8 >= cash["minimum_cash"] else "FAIL"
            if funding_status == "FAIL":
                failures.append(f"{tag}: cash below minimum liquidity")
        average = year.get("diluted_average_shares")
        eps = None if average is None else ni / number(average, tag + " diluted weighted shares", positive=True)
        tau = (payment - start).days / 365.0
        dividends.append((dps, tau))
        rows.append({"period_start": begin.isoformat(), "period_end": end.isoformat(),
                     "cashflow_date": payment.isoformat(), "holding_years": tau,
                     "net_income": ni, "fcf_conversion": conversion, "fcf": fcf,
                     "payout_ratio": payout, "net_share_change": change, "annual_issuance_rate": issuance,
                     "shares_end": shares, "eps": eps, "end_share_earnings": ni / shares,
                     "company_dividend": dividend, "dividend_per_share": dps,
                     "dividend_pv": dps / (1 + required) ** tau,
                     "gross_buyback_proxy": proxy_buyback, "gross_buyback_cash": buyback,
                     "distribution_cash": distribution,
                     "dividend_coverage": fcf / dividend if dividend else None,
                     "distribution_coverage": fcf / distribution if distribution else None,
                     "distribution_coverage_status": coverage_status,
                     "cash_open": before_cash, "cash_close": cash_balance,
                     "funding_status": funding_status})
        prior_end = end
    terminal = fcf * multiple / shares
    terminal_pv = terminal / (1 + required) ** tau
    dividend_pv = present_value(dividends, required)
    target = dividend_pv + terminal_pv
    summary = {"valuation_date": start.isoformat(), "forecast_years": len(periods),
               "holding_years": tau, "base_net_income": base_ni,
               "net_income_cagr": (ni / base_ni) ** (1 / len(periods)) - 1,
               "current_shares": n0, "terminal_price": terminal,
               "terminal_market_cap": fcf * multiple,
               "dividend_pv": dividend_pv, "terminal_pv": terminal_pv,
               "target_price": target, "target_market_cap": target * n0,
               "distribution_coverage_status": ("FAIL" if any(r["distribution_coverage_status"] == "FAIL" for r in rows)
                                                else "PARTIAL" if any(r["distribution_coverage_status"] == "PARTIAL"
                                                                      for r in rows) else "PASS"),
               "funding_status": ("FAIL" if any(r["funding_status"] == "FAIL" for r in rows)
                                  else "PARTIAL" if any(r["funding_status"] == "PARTIAL" for r in rows) else "PASS")}
    if model.get("market_price") is not None:
        price = number(model["market_price"], "market price at valuation date", positive=True)
        summary["market_price"] = price
        summary["irr"] = solve_return(price, dividends + [(terminal, tau)])
    if model.get("research_date") is not None:
        research = iso(model["research_date"])
        if research > start:
            raise ValueError("research date must not follow valuation date")
        if research < start and "pre_base_dividends" not in model:
            raise ValueError("earlier research date requires explicit pre_base_dividends, including [] for zero")
        stubs = model.get("pre_base_dividends", [])
        if not isinstance(stubs, list):
            raise ValueError("pre_base_dividends must be an array")
        stub_flows = []
        for stub in stubs:
            when = iso(stub["date"])
            if not research < when <= start:
                raise ValueError("stub dividend dates must satisfy research < dividend <= valuation date")
            stub_flows.append((number(stub.get("amount_per_share"), "stub dividend", minimum=0),
                               (when - research).days / 365.0))
        summary["research_date"] = research.isoformat()
        summary["research_date_target_price"] = present_value(
            [(target, (start - research).days / 365.0)] + stub_flows, required)
    elif model.get("pre_base_dividends") is not None:
        raise ValueError("pre_base_dividends require research_date")
    return {"method_version": METHOD, "status": "FAIL" if failures else "PARTIAL" if gaps else "PASS",
            "rows": rows, "summary": summary, "failures": failures, "gaps": gaps,
            "limitations": ["Cash feasibility depends on completeness and evidence of supplied budgets.",
                            "Annual-end shareholder payments/share counts are approximations.",
                            "Gross repurchase proxy uses annual FCF and the adopted exit P/FCF.",
                            "This calculation does not verify Excel cells, evidence or visual layout."]}


def repo_path(value):
    return (isinstance(value, str) and bool(value) and "\\" not in value
            and not PurePosixPath(value).is_absolute() and ".." not in PurePosixPath(value).parts
            and not value.startswith("~") and ":" not in value)


def workbook_cell(value):
    """Single A1 address within Excel's worksheet bounds, optionally absolute."""
    match = re.fullmatch(r"\$?([A-Z]{1,3})\$?([1-9][0-9]{0,6})", value.upper()) if isinstance(value, str) else None
    if not match:
        return False
    column = 0
    for char in match[1]:
        column = column * 26 + ord(char) - ord("A") + 1
    return column <= 16384 and int(match[2]) <= 1048576


def validate_cases(packet, config, metrics, errors, gaps):
    """Check restorable case snapshots against one shared forecast basis."""
    scope = config.get("scope")
    if scope not in {"forecast", "valuation"}:
        errors.append("config.scope must be forecast/valuation")
    for key in ("forecast_sheet", "common_basis_version", "net_income_basis"):
        if not isinstance(config.get(key), str) or not config[key].strip():
            errors.append(f"config.{key} missing")
    if scope == "valuation" and not config.get("valuation_sheet"):
        errors.append("config.valuation_sheet missing")
    try:
        base = number(config.get("base_net_income"), "config.base_net_income", positive=scope == "valuation")
    except ValueError as exc:
        errors.append(str(exc))
        base = None
    periods = config.get("forecast_periods")
    if not isinstance(periods, list) or not periods:
        errors.append("config.forecast_periods must list annual fiscal ends excluding base")
        periods = []
    reason = config.get("forecast_horizon_reason")
    if len(periods) != 5 and (not isinstance(reason, str) or not reason.strip()):
        errors.append("five forecast periods required unless config.forecast_horizon_reason explains the horizon")
    try:
        prior = iso(config.get("base_period_end"))
        if iso(config.get("valuation_date")) != prior:
            errors.append("valuation_date must equal base_period_end")
        for period in periods:
            end = iso(period)
            if not 350 <= (end - prior).days <= 380:
                errors.append("config.forecast_periods must be contiguous annual fiscal ends")
            prior = end
    except (ValueError, TypeError):
        errors.append("invalid fiscal end in config.forecast_periods/base_period_end")
    cases = packet.get("cases", [])
    if not isinstance(cases, list):
        errors.append("cases must be an array")
        return
    expected = {"pessimistic", "base", "optimistic"}
    seen, adopted, driver_ids = set(), [], set()
    for case in cases:
        if not isinstance(case, dict):
            errors.append("case must be an object")
            continue
        cid, state = case.get("id"), case.get("status")
        if cid not in expected or cid in seen:
            errors.append("case ID must be unique pessimistic/base/optimistic")
        seen.add(cid)
        if state not in {"adopted", "pending"}:
            errors.append(f"{cid}: case status must be adopted/pending")
            continue
        if state == "pending":
            gaps.append(f"{cid}: case not adopted")
            path = case.get("net_income_path")
            if path is not None and (not isinstance(path, list) or any(v is not None for v in path)):
                errors.append(f"{cid}: pending case profit path must be null/empty/null markers, never invented zero")
            if case.get("driver_values") or case.get("valuation_inputs"):
                errors.append(f"{cid}: pending case must not masquerade as adopted driver/valuation inputs")
            continue
        adopted.append(case)
        try:
            datetime.fromisoformat(case.get("captured_at", "").replace("Z", "+00:00"))
        except (ValueError, AttributeError, TypeError):
            errors.append(f"{cid}: captured_at must be ISO timestamp")
        if case.get("basis_version") != config.get("common_basis_version"):
            errors.append(f"{cid}: stale common basis; recapture before restoration")
        path = case.get("net_income_path")
        if not isinstance(path, list) or len(path) != len(periods) + 1:
            errors.append(f"{cid}: net_income_path must contain base plus each shared forecast period")
        else:
            try:
                values = [number(v, f"{cid} net income", positive=scope == "valuation") for v in path]
                if base is not None and not math.isclose(values[0], base, rel_tol=1e-9, abs_tol=1e-9):
                    errors.append(f"{cid}: case base profit differs from shared base")
            except ValueError as exc:
                errors.append(str(exc))
        drivers = case.get("driver_values")
        if not isinstance(drivers, dict) or not drivers:
            gaps.append(f"{cid}: restore driver_values missing")
        else:
            driver_ids.update(drivers)
            for mid, values in drivers.items():
                if mid not in metrics:
                    errors.append(f"{cid}: restore driver has unknown metric ID {mid}")
                if not isinstance(values, list) or len(values) != len(periods):
                    errors.append(f"{cid}/{mid}: restore driver period length differs from common forecast")
                    continue
                try:
                    for value in values:
                        number(value, f"{cid}/{mid} restore driver")
                except ValueError as exc:
                    errors.append(str(exc))
        values = case.get("valuation_inputs")
        if not isinstance(values, dict):
            errors.append(f"{cid}: valuation_inputs missing")
        else:
            try:
                reject_legacy(values, f"{cid} valuation inputs")
                inputs = valuation_inputs(values, f"{cid} valuation inputs")
                annual_parameters(inputs, periods, values.get("annual_overrides"),
                                  values.get("annual_issuance_rate"))
            except ValueError as exc:
                errors.append(str(exc))
    for case in adopted:
        drivers = case.get("driver_values")
        missing = driver_ids - (set(drivers) if isinstance(drivers, dict) else set())
        if missing:
            gaps.append(f"{case.get('id')}: restore driver values missing for {', '.join(sorted(missing))}")
    if scope == "valuation":
        for cid in sorted(expected - seen):
            gaps.append(f"{cid}: full valuation case snapshot missing")


def validate(packet):
    """Structural handoff checks; not source authentication or workbook inspection."""
    errors, gaps = [], []
    if packet.get("schema_version") != "valuation-handoff.v2":
        errors.append("unsupported handoff schema")
    config = packet.get("config", {})
    for key in ("company_id", "market", "currency", "amount_unit", "share_unit", "method_version",
                "fiscal_year_end", "fiscal_calendar_note", "latest_actual_period"):
        if not config.get(key):
            errors.append(f"config.{key} missing")
    if config.get("method_version") != METHOD:
        errors.append("unsupported/legacy method version")
    try:
        reject_legacy(config, "config")
    except ValueError as exc:
        errors.append(str(exc))
    if config.get("amount_unit") != config.get("share_unit"):
        errors.append("config amount/share scale must match")
    for key in ("as_of", "valuation_date", "base_period_end"):
        try:
            iso(config.get(key))
        except (TypeError, ValueError):
            errors.append(f"config.{key} must be an ISO date")
    for key in ("workbook_path", "source_index_path"):
        if not repo_path(config.get(key)):
            errors.append(f"config.{key} must be repository-relative")
    for key in ("report_path",):
        if config.get(key) is not None and not repo_path(config[key]):
            errors.append(f"config.{key} must be repository-relative")
    for key in ("thesis", "review_triggers"):
        if not config.get(key):
            gaps.append(f"config.{key} absent")
    for key in ("previous_snapshot_path",):
        if packet.get(key) is not None and not repo_path(packet[key]):
            errors.append(f"{key} must be repository-relative")
    operation = config.get("operation")
    if operation not in {"initial", "refresh"}:
        errors.append("config.operation must be initial/refresh")
    updates = packet.get("updates", [])
    if not isinstance(updates, list):
        errors.append("updates must be an array")
        updates = []
    update_dates = []
    latest_update, latest_date = None, None
    for update in updates:
        if not isinstance(update, dict):
            errors.append("update must be an object")
            continue
        try:
            update_date = iso(update.get("as_of"))
            update_dates.append(update_date)
            if latest_date is None or update_date >= latest_date:
                latest_update, latest_date = update, update_date
        except (TypeError, ValueError):
            errors.append("update.as_of must be an ISO date")
        if update.get("previous_snapshot_path") is not None and not repo_path(update["previous_snapshot_path"]):
            errors.append("update.previous_snapshot_path must be repository-relative")
    if operation == "refresh":
        if not repo_path(packet.get("previous_snapshot_path")):
            errors.append("refresh requires previous_snapshot_path")
        if not updates:
            errors.append("refresh requires nonempty updates")
        if not update_dates or max(update_dates).isoformat() != config.get("as_of"):
            errors.append("latest update.as_of must match config.as_of")
    sources, metrics, decisions = {}, {}, {}
    for name, store in (("sources", sources), ("metrics", metrics), ("decisions", decisions)):
        for item in packet.get(name, []):
            identity = item.get("id")
            if not isinstance(identity, str) or not identity or identity in store:
                errors.append(f"{name}: missing or duplicate ID")
            else:
                store[identity] = item
    if operation == "refresh" and latest_update is not None:
        for key in ("new_source_ids", "actual_vs_forecast", "input_changes", "valuation_attribution", "checks", "unresolved"):
            if not isinstance(latest_update.get(key), list):
                errors.append(f"latest update.{key} must be an explicit array (empty means none)")
        new_sources = latest_update.get("new_source_ids")
        if isinstance(new_sources, list):
            for sid in new_sources:
                if not isinstance(sid, str) or sid not in sources:
                    errors.append("latest update.new_source_ids contains an undeclared source")
        checks = latest_update.get("checks")
        if isinstance(checks, list):
            if not checks:
                errors.append("latest update.checks must contain structured checks")
            for check in checks:
                if (not isinstance(check, dict) or not isinstance(check.get("kind"), str)
                        or not check["kind"].strip() or check.get("status") not in {"PASS", "PARTIAL", "FAIL", "BLOCKED"}):
                    errors.append("latest update.checks entries require kind and PASS/PARTIAL/FAIL/BLOCKED status")
                elif check["status"] == "FAIL":
                    errors.append(f"latest update check {check['kind']}: recorded FAIL")
                elif check["status"] in {"PARTIAL", "BLOCKED"}:
                    gaps.append(f"latest update check {check['kind']}: recorded {check['status']}")
    for sid, source in sources.items():
        if not repo_path(source.get("path")) or not source.get("locator"):
            errors.append(f"{sid}: source path/locator missing")
        for key in ("content_date", "access_date"):
            try:
                iso(source.get(key))
            except (ValueError, TypeError):
                errors.append(f"{sid}: {key} invalid")
        if not source.get("url") and not source.get("provider_reference"):
            gaps.append(f"{sid}: original URL/provider reference missing")
        if source.get("evidence_type") not in {"source_fact", "company_claim", "guidance", "third_party"}:
            errors.append(f"{sid}: evidence type missing/invalid")
    policies = {"actual_or_formula", "guidance_rule", "analyst_review", "locked"}
    for mid, metric in metrics.items():
        for key in ("label", "definition", "unit", "scope", "update_rule"):
            if not metric.get(key):
                errors.append(f"{mid}: {key} missing")
        if metric.get("update_policy") not in policies:
            errors.append(f"{mid}: unknown update policy")
        if metric.get("kind") not in {"input", "formula"}:
            errors.append(f"{mid}: kind must be input/formula")
        if metric.get("kind") == "formula" and not metric.get("formula"):
            errors.append(f"{mid}: formula missing")
        if "material" in metric and not isinstance(metric["material"], bool):
            errors.append(f"{mid}: material must be boolean")
        mappings = metric.get("workbook_mapping", [])
        if not isinstance(mappings, list):
            errors.append(f"{mid}: workbook_mapping must be an array")
            mappings = []
        if metric.get("material", True) and not mappings:
            errors.append(f"{mid}: material metric workbook_mapping missing")
        for mapping in mappings:
            if not isinstance(mapping, dict):
                errors.append(f"{mid}: workbook_mapping entry must be an object")
                continue
            sheet = mapping.get("sheet")
            if (not isinstance(sheet, str) or not sheet.strip() or len(sheet) > 31
                    or sheet.startswith("'") or sheet.endswith("'")
                    or any(char in sheet for char in "[]:*?/\\")):
                errors.append(f"{mid}: workbook_mapping sheet invalid")
            if not workbook_cell(mapping.get("cell")):
                errors.append(f"{mid}: workbook_mapping cell must be a valid single Excel A1 address")
            if mapping.get("role") not in {"actual", "input", "formula", "output"}:
                errors.append(f"{mid}: workbook_mapping role invalid")
        for dependency in metric.get("dependencies", []):
            if dependency not in metrics:
                errors.append(f"{mid}: unknown dependency {dependency}")
        history = {}
        for entry in metric.get("history", []):
            period = entry.get("period")
            if not period or period in history:
                errors.append(f"{mid}: missing/duplicate history period")
            history[period] = entry
            state = entry.get("disclosure_status")
            if state not in {"reported", "calculated", "unavailable", "n.a."}:
                errors.append(f"{mid}/{period}: invalid disclosure status")
            if state in {"reported", "calculated"}:
                try:
                    number(entry.get("value"), mid + " historical value")
                except ValueError as exc:
                    errors.append(str(exc))
                if not entry.get("source_ids") or any(s not in sources for s in entry["source_ids"]):
                    errors.append(f"{mid}/{period}: historical source unknown/missing")
                if state == "calculated" and not entry.get("formula"):
                    errors.append(f"{mid}/{period}: historical derivation missing")
            elif entry.get("value") is not None:
                errors.append(f"{mid}/{period}: missing marker must not have a numeric value")
            elif state == "unavailable":
                gaps.append(f"{mid}/{period}: historical value unavailable")
        adopted_periods = set()
        for entry in metric.get("adopted", []):
            period, decision = entry.get("period"), entry.get("decision_id")
            if period in adopted_periods:
                errors.append(f"{mid}/{period}: duplicate adopted input")
            adopted_periods.add(period)
            if not period or decision not in decisions:
                errors.append(f"{mid}: adopted period/decision missing")
            if entry.get("status") not in {"adopted", "pending", "unavailable"}:
                errors.append(f"{mid}/{period}: invalid adoption status")
            if entry.get("status") == "adopted":
                try:
                    number(entry.get("value"), mid + " adopted value")
                except ValueError as exc:
                    errors.append(str(exc))
                if not entry.get("evidence_ids") or any(s not in sources for s in entry["evidence_ids"]):
                    errors.append(f"{mid}/{period}: adopted evidence missing")
                if decision in decisions:
                    record = decisions[decision]
                    if record.get("metric_id") != mid or record.get("values", {}).get(period) != entry.get("value"):
                        errors.append(f"{mid}/{period}: adopted input conflicts with decision")
            else:
                gaps.append(f"{mid}/{period}: assumption not adopted")
                if entry.get("value") is not None:
                    errors.append(f"{mid}/{period}: non-adopted value must be null")
        if metric.get("needs_forecast_history"):
            expected = metric.get("history_window", {})
            annual = expected.get("annual_periods", [])
            interim = expected.get("interim_periods", expected.get("quarter_periods", []))
            if (not isinstance(annual, list) or not isinstance(interim, list)
                    or not all(isinstance(p, str) for p in annual + interim) or not annual + interim):
                errors.append(f"{mid}: select available annual/interim history periods")
                annual, interim = [], []
            layouts = metric.get("forecast_layout", [])
            if not any(b.get("section") == "future_years" for b in layouts):
                errors.append(f"{mid}: missing future_years history-right layout")
            for block in layouts:
                section = block.get("section")
                if section not in {"current_year", "remaining_quarters", "future_years"}:
                    errors.append(f"{mid}: unknown forecast section")
                columns = block.get("forecast_columns", [])
                cells = block.get("history_cells", [])
                if (not columns or any(not isinstance(c, int) or isinstance(c, bool) or c < 1 for c in columns)
                        or not isinstance(block.get("row"), int) or block["row"] < 1
                        or not block.get("sheet")):
                    errors.append(f"{mid}: invalid forecast coordinates")
                    continue
                seen = set()
                for cell in cells:
                    period = cell.get("period")
                    seen.add(period)
                    col = cell.get("column")
                    if not isinstance(col, int) or isinstance(col, bool) or col <= max(columns):
                        errors.append(f"{mid}: history must be to right of forecasts")
                    if period not in history:
                        errors.append(f"{mid}/{period}: right history not bound to a value/marker")
                    elif history[period].get("disclosure_status") in {"reported", "calculated"}:
                        if not cell.get("actual_sheet") or not cell.get("actual_cell"):
                            errors.append(f"{mid}/{period}: right history actual link missing")
                if not set(annual + interim) <= seen:
                    errors.append(f"{mid}/{section}: selected annual/interim history omitted")
            if not metric.get("adopted"):
                gaps.append(f"{mid}: no adopted forecast inputs")
    for did, decision in decisions.items():
        if decision.get("metric_id") not in metrics or not decision.get("reason") or not decision.get("origin"):
            errors.append(f"{did}: decision binding/reason/origin missing")
        if not isinstance(decision.get("locked"), bool):
            errors.append(f"{did}: locked flag required")
        try:
            iso(decision.get("date"))
        except (ValueError, TypeError):
            errors.append(f"{did}: invalid decision date")
    visited, active = set(), set()
    def visit(mid):
        if mid in active:
            errors.append(f"dependency cycle at {mid}")
            return
        if mid in visited:
            return
        active.add(mid)
        for dep in metrics[mid].get("dependencies", []):
            if dep in metrics:
                visit(dep)
        active.remove(mid)
        visited.add(mid)
    for mid in metrics:
        visit(mid)
    validate_cases(packet, config, metrics, errors, gaps)
    if not metrics:
        errors.append("no metric records")
    return {"status": "FAIL" if errors else "PARTIAL" if gaps else "PASS",
            "errors": errors, "gaps": gaps,
            "limitations": ["Structural check only: source authenticity, Excel mappings, coverage selection and visuals require inspection."]}


def proposed_input_changes(packet, current_values):
    """Detect workbook/adopted divergence without overwriting either side."""
    changes = []
    decisions = {d["id"]: d for d in packet.get("decisions", [])}
    for metric in packet.get("metrics", []):
        for entry in metric.get("adopted", []):
            key = f"{metric['id']}:{entry['period']}"
            if key in current_values and current_values[key] != entry.get("value"):
                changes.append({"key": key, "adopted": entry.get("value"),
                                "workbook": current_values[key],
                                "locked": (metric.get("update_policy") == "locked"
                                           or decisions.get(entry.get("decision_id"), {}).get("locked", False)),
                                "action": "register_workbook_decision_before_refresh"})
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("calculate", "validate"))
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        packet = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(packet, dict):
            raise ValueError("input must be a JSON object")
        result = calculate(packet) if args.command == "calculate" else validate(packet)
    except (ValueError, TypeError, KeyError, OSError, OverflowError) as exc:
        result = {"status": "FAIL", "errors": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
