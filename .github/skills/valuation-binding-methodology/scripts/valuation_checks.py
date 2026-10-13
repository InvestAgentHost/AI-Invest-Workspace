"""Read-only independent checks. Stdlib only; JSON results on stdout."""
import argparse
from datetime import date
import json
import math
from pathlib import Path, PurePosixPath


METHOD = "direct-pe-net-shares-v2"
CASH_USES = ("debt_principal", "finance_lease_principal", "other_necessary_uses")
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


def calculate(model):
    if model.get("method_version") != METHOD:
        raise ValueError("unsupported/legacy method; migrate explicitly before calculation")
    for key in ("currency", "amount_unit", "share_unit"):
        if not model.get(key):
            raise ValueError(f"{key}: required")
    if model["amount_unit"] != model["share_unit"]:
        raise ValueError("amount/share scale must match for per-share outputs")
    start = iso(model["valuation_date"])
    price = number(model["market_cap"], "market cap", positive=True)
    n0 = number(model["current_shares"], "current outstanding shares", positive=True)
    required = number(model["required_return"], "required return")
    if required <= -1:
        raise ValueError("required return must exceed -100%")
    if not model.get("years"):
        raise ValueError("no forecast periods")
    cash_balance = model.get("opening_available_cash")
    gaps = []
    if cash_balance is None:
        gaps.append("opening available cash missing")
    else:
        cash_balance = number(cash_balance, "opening available cash", minimum=0)
    shares, prior_end, prior_payment = n0, None, start
    dividends, rows, failures = [], [], []
    for i, year in enumerate(model["years"]):
        tag = f"period {i + 1}"
        end, begin, payment = (iso(year[k]) for k in ("period_end", "period_start", "cashflow_date"))
        if not begin <= end or not 350 <= (end - begin).days + 1 <= 380:
            raise ValueError(f"{tag}: annual profit period required (including 52/53-week years)")
        if end <= start or payment < end or payment <= prior_payment:
            raise ValueError(f"{tag}: invalid terminal/cashflow ordering")
        if prior_end is not None and (begin - prior_end).days != 1:
            raise ValueError(f"{tag}: forecast periods must be contiguous")
        if i == 0 and (begin - start).days > 1:
            raise ValueError("missing transition period between valuation date and forecast")
        residual = i == 0 and begin <= start
        if residual and not all(k in year for k in ("dividend_after_valuation", "budget_fcf")):
            raise ValueError("residual fiscal year requires future-only dividends and FCF budget")
        ni = number(year["net_income"], tag + " net income", positive=True)
        shrink = number(year["net_shrink"], tag + " net shrink")
        if shrink >= 1:
            raise ValueError("net shrink must be below 100%")
        c = number(year["fcf_conversion"], tag + " conversion", minimum=0)
        payout = number(year["payout"], tag + " payout", minimum=0)
        pe = number(year["exit_pe"], tag + " direct exit PE", positive=True)
        shares *= 1 - shrink
        fcf = number(year.get("fcf", ni * c), tag + " FCF")
        if not math.isclose(fcf / ni, c, rel_tol=1e-7, abs_tol=1e-9):
            failures.append(f"{tag}: independently forecast FCF conflicts with conversion")
        dividend = number(year.get("dividend_after_valuation", ni * payout), tag + " future dividend", minimum=0)
        budget_fcf = number(year.get("budget_fcf", fcf), tag + " budget FCF")
        if not residual and not math.isclose(budget_fcf, fcf, rel_tol=1e-7, abs_tol=1e-9):
            failures.append(f"{tag}: full-year cash budget conflicts with annual FCF")
        if not residual and "dividend_after_valuation" in year and not math.isclose(dividend, ni * payout):
            failures.append(f"{tag}: annual dividend differs from payout assumption")
        cash = year.get("cash", {})
        if residual and "gross_buyback_cash" not in cash:
            raise ValueError("residual fiscal year requires residual gross buyback cash")
        needed = CASH_USES + CASH_INFLOWS + ("minimum_cash", "dilution_rate")
        if "gross_buyback_cash" not in cash:
            needed += ("buyback_pe",)
        missing = [k for k in needed if k not in cash or cash[k] is None]
        if missing:
            gaps.append(f"{tag}: missing cash fields {', '.join(missing)}")
        for key in needed:
            if key not in missing:
                number(cash[key], tag + " " + key, minimum=0)
        dilution = cash.get("dilution_rate")
        if dilution is not None and shrink + dilution < -1e-12:
            raise ValueError(f"{tag}: shrink/issuance cannot imply negative gross buybacks")
        if "gross_buyback_cash" in cash:
            buyback = number(cash["gross_buyback_cash"], tag + " gross buyback", minimum=0)
        elif dilution is not None and cash.get("buyback_pe") is not None:
            buy_pe = number(cash["buyback_pe"], tag + " buyback PE", positive=True)
            buyback = (shrink + dilution) / (1 - shrink) * ni * buy_pe
        else:
            buyback = None
        before_cash = cash_balance
        if missing or cash_balance is None:
            cash_balance, budget_status = None, "PARTIAL"
        else:
            cash_balance += (budget_fcf + sum(cash[k] for k in CASH_INFLOWS)
                             - dividend - buyback - sum(cash[k] for k in CASH_USES))
            budget_status = "PASS" if cash_balance + 1e-8 >= cash["minimum_cash"] else "FAIL"
            if budget_status == "FAIL":
                failures.append(f"{tag}: cash below minimum liquidity")
        average = year.get("diluted_average_shares")
        eps = None if average is None else ni / number(average, tag + " diluted weighted shares", positive=True)
        if eps is None:
            gaps.append(f"{tag}: diluted weighted shares missing; EPS unavailable")
        tau = (payment - start).days / 365.0
        # Holder aggregate uses N0 fixed shares; company dividend is not the holder total.
        holder_dividend = dividend * n0 / shares
        dividends.append((holder_dividend, tau))
        terminal = ni * pe * n0 / shares
        flows = dividends[:-1] + [(holder_dividend + terminal, tau)]
        target = present_value(flows, required)
        rows.append({"period_end": end.isoformat(), "cashflow_date": payment.isoformat(),
                     "holding_years": tau, "net_income": ni, "shares_end": shares,
                     "eps": eps, "end_share_earnings": ni / shares,
                     "company_dividend": dividend, "holder_dividend": holder_dividend,
                     "holder_exit_value": terminal, "company_exit_market_cap": ni * pe,
                     "irr": solve_return(price, flows), "target_market_cap": target,
                     "target_price": target / n0, "fcf": fcf,
                     "budget_fcf": budget_fcf, "gross_buyback_cash": buyback,
                     "cash_open": before_cash, "cash_close": cash_balance,
                     "funding_status": budget_status})
        prior_end, prior_payment = end, payment
    return {"method_version": METHOD, "status": "FAIL" if failures else "PARTIAL" if gaps else "PASS",
            "rows": rows, "failures": failures, "gaps": gaps,
            "limitations": ["Cash feasibility depends on completeness and evidence of supplied budgets.",
                            "Annual-end shareholder payments/share counts are approximations.",
                            "This calculation does not verify Excel cells, evidence or visual layout."]}


def repo_path(value):
    return (isinstance(value, str) and bool(value) and "\\" not in value
            and not PurePosixPath(value).is_absolute() and ".." not in PurePosixPath(value).parts
            and not value.startswith("~") and ":" not in value)


def validate(packet):
    """Structural handoff checks; not source authentication or workbook inspection."""
    errors, gaps = [], []
    if packet.get("schema_version") != "valuation-handoff.v1":
        errors.append("unsupported handoff schema")
    config = packet.get("config", {})
    for key in ("company_id", "market", "currency", "amount_unit", "share_unit", "method_version",
                "fiscal_year_end", "fiscal_calendar_note", "latest_actual_period"):
        if not config.get(key):
            errors.append(f"config.{key} missing")
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
    sources, metrics, decisions = {}, {}, {}
    for name, store in (("sources", sources), ("metrics", metrics), ("decisions", decisions)):
        for item in packet.get(name, []):
            identity = item.get("id")
            if not isinstance(identity, str) or not identity or identity in store:
                errors.append(f"{name}: missing or duplicate ID")
            else:
                store[identity] = item
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
            annual, quarters = expected.get("annual_periods", []), expected.get("quarter_periods", [])
            if not annual or not quarters:
                errors.append(f"{mid}: annual/quarter history windows required")
            layouts = metric.get("forecast_layout", [])
            for section in ("remaining_quarters", "future_years"):
                blocks = [b for b in layouts if b.get("section") == section]
                if not blocks:
                    errors.append(f"{mid}: missing {section} history-right layout")
                for block in blocks:
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
                    if not set(annual + quarters) <= seen:
                        errors.append(f"{mid}/{section}: selected annual/quarter history omitted")
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
