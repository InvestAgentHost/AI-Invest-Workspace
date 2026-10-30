"""Behavioral tests using synthetic companies, without touching research files."""
import copy
from datetime import date, timedelta
import unittest

from valuation_checks import (calculate, cumulative_to_quarters, present_value,
                              proposed_input_changes, validate)


def model():
    # Synthetic manufacturer, using equal amount/share scales.
    periods = []
    for i in range(3):
        y = 2031 + i
        periods.append({"period_start": f"{y}-01-01", "period_end": f"{y}-12-31",
                        "cashflow_date": f"{y}-12-31", "net_income": 100 * 1.05 ** (i + 1),
                        "diluted_average_shares": 99 - i,
                        "cash": {"debt_principal": 0, "financing_inflow": 0,
                                 "finance_lease_principal": 0, "acquisitions": 0,
                                 "other_necessary_uses": 0, "other_inflows": 0,
                                 "equity_issuance_cash": 0, "minimum_cash": 0}})
    return {"method_version": "dividend-pfcf-net-shares-v3", "valuation_date": "2030-12-31",
            "currency": "USD", "amount_unit": "million", "share_unit": "million",
            "base_net_income": 100, "market_price": 20, "current_shares": 100,
            "required_return": 0.1, "exit_p_fcf": 20,
            "fcf_conversion_start": 0.9, "fcf_conversion_exit": 0.9,
            "payout_ratio": 0.5, "net_share_change": -0.01, "annual_issuance_rate": 0.002,
            "opening_available_cash": 100, "years": periods}


def handoff():
    periods = ["FY2028", "FY2029", "2030Q1", "2030Q2"]
    history = [{"period": p, "value": 100 + i, "disclosure_status": "reported",
                "source_ids": ["filing"]} for i, p in enumerate(periods)]
    layouts = [{"section": section, "sheet": "Drivers", "row": row,
                "forecast_columns": [3, 4] if section == "remaining_quarters" else [3, 4, 5, 6, 7],
                "history_cells": [{"period": p, "column": 9 + i,
                                   "actual_sheet": "Financials", "actual_cell": f"{chr(67 + i)}8"}
                                  for i, p in enumerate(periods)]}
               for section, row in (("remaining_quarters", 8), ("future_years", 20))]
    return {
        "schema_version": "valuation-handoff.v2",
        "config": {"company_id": "TEST-industrial", "market": "US", "as_of": "2030-08-01",
                   "valuation_date": "2030-12-31", "fiscal_year_end": "12-31",
                   "fiscal_calendar_note": "calendar year", "currency": "USD",
                   "amount_unit": "million", "share_unit": "million",
                   "method_version": "dividend-pfcf-net-shares-v3", "latest_actual_period": "2030Q2",
                   "scope": "forecast", "operation": "initial", "forecast_sheet": "Profit Forecast",
                   "valuation_sheet": "Valuation Model", "common_basis_version": "synthetic-v1",
                   "net_income_basis": "consolidated attributable to common shareholders",
                   "base_net_income": 100,
                   "forecast_periods": [f"{year}-12-31" for year in range(2031, 2036)],
                   "base_period_end": "2030-12-31", "workbook_path": "research/test/model.xlsx",
                   "source_index_path": "research/test/data/sources.md",
                   "thesis": ["existing capacity supports volume growth"],
                   "review_triggers": ["persistent utilization below adopted range"]},
        "sources": [{"id": "filing", "path": "sources/companies/US/TEST/sec/report.html",
                     "locator": "Income Statement", "content_date": "2030-07-31",
                     "access_date": "2030-08-01", "url": "https://example.com/filing",
                     "evidence_type": "source_fact"}],
        "metrics": [{"id": "revenue", "label": "Revenue", "definition": "consolidated net revenue",
                     "unit": "USD million", "scope": "consolidated", "kind": "input",
                     "dependencies": [], "formula": None, "update_policy": "locked",
                     "update_rule": "analyst approval retained until capacity thesis review",
                     "needs_forecast_history": True,
                     "history_window": {"annual_periods": periods[:2], "quarter_periods": periods[2:]},
                     "history": history, "forecast_layout": layouts,
                     "workbook_mapping": [{"sheet": "Profit Forecast", "section": "future_years",
                                           "period": f"FY{2031 + i}", "cell": f"{chr(67 + i)}20",
                                           "role": "input"} for i in range(5)],
                     "adopted": [{"period": "FY2031", "value": 120, "status": "adopted",
                                  "decision_id": "decision1", "evidence_ids": ["filing"]}]}],
        "decisions": [{"id": "decision1", "metric_id": "revenue", "date": "2030-08-01",
                       "origin": "analyst", "reason": "capacity and volume assumptions reviewed",
                       "values": {"FY2031": 120}, "locked": True}]}


def valuation_handoff():
    p = handoff()
    p["config"]["scope"] = "valuation"
    p["cases"] = [{"id": cid, "status": "adopted", "captured_at": "2030-08-01T10:00:00Z",
                   "basis_version": "synthetic-v1", "net_income_path": [100, 105, 110, 115, 120, 125],
                   "driver_values": {"revenue": [120, 130, 140, 150, 160]},
                   "valuation_inputs": {k: model()[k] for k in
                                        ("exit_p_fcf", "fcf_conversion_start", "fcf_conversion_exit",
                                         "payout_ratio", "net_share_change")}}
                  for cid in ("pessimistic", "base", "optimistic")]
    return p


def refresh_handoff():
    p = handoff()
    p["config"]["operation"] = "refresh"
    p["previous_snapshot_path"] = "data/derived/companies/US/TEST/valuation/2030-07-01/snapshot.json"
    p["updates"] = [{"as_of": p["config"]["as_of"], "new_source_ids": ["filing"],
                     "actual_vs_forecast": [], "input_changes": [], "valuation_attribution": [],
                     "checks": [{"kind": "independent_calculation", "status": "PASS"}], "unresolved": []}]
    return p


class CalculationTests(unittest.TestCase):
    def test_final_conversion_changes_terminal_and_price(self):
        a, b = model(), model()
        b["fcf_conversion_exit"] = 0.75
        ra, rb = calculate(a), calculate(b)
        self.assertNotEqual(ra["summary"]["terminal_price"], rb["summary"]["terminal_price"])
        self.assertNotEqual(ra["summary"]["target_price"], rb["summary"]["target_price"])
        self.assertAlmostEqual(rb["rows"][0]["fcf_conversion"], 0.9)
        self.assertAlmostEqual(rb["rows"][1]["fcf_conversion"], 0.825)
        self.assertAlmostEqual(rb["rows"][-1]["fcf_conversion"], 0.75)

    def test_initial_conversion_alone_changes_budget_not_terminal(self):
        a, b = model(), model()
        b["fcf_conversion_start"] = 0.75
        ra, rb = calculate(a), calculate(b)
        self.assertEqual(ra["summary"]["terminal_price"], rb["summary"]["terminal_price"])
        self.assertEqual(ra["summary"]["target_price"], rb["summary"]["target_price"])
        self.assertNotEqual(ra["rows"][0]["fcf"], rb["rows"][0]["fcf"])

    def test_shrink_and_terminal_only_at_horizon(self):
        m = model()
        r = calculate(m)
        self.assertAlmostEqual(r["rows"][0]["shares_end"], 99)
        self.assertAlmostEqual(r["rows"][0]["dividend_per_share"], 105 * 0.5 / 99)
        self.assertAlmostEqual(r["summary"]["terminal_price"], 100 * 1.05 ** 3 * 0.9 * 20 / (100 * 0.99 ** 3))
        self.assertTrue(all("terminal_price" not in row and "irr" not in row for row in r["rows"]))

    def test_no_interim_fcf_double_count_or_debt_deduction(self):
        m = model()
        r = calculate(m)
        flows = [(row["dividend_per_share"], row["holding_years"]) for row in r["rows"]]
        flows.append((r["summary"]["terminal_price"], r["summary"]["holding_years"]))
        self.assertAlmostEqual(present_value(flows, 0.1), r["summary"]["target_price"])
        self.assertAlmostEqual(present_value(flows, r["summary"]["irr"]), m["market_price"], places=9)
        m["years"][0]["cash"]["debt_principal"] = 20
        self.assertEqual(calculate(m)["summary"]["target_price"], r["summary"]["target_price"])

    def test_gross_repurchase_uses_fcf_and_includes_issuance(self):
        row = calculate(model())["rows"][0]
        self.assertAlmostEqual(row["gross_buyback_cash"], 105 * 0.9 * 20 * (0.002 + 0.01) / 0.99)
        m = model()
        m["years"][0]["cash"]["gross_buyback_cash"] = 11
        self.assertEqual(calculate(m)["rows"][0]["gross_buyback_cash"], 11)

    def test_missing_issuance_does_not_block_price_or_fake_buyback(self):
        m = model()
        original = calculate(m)
        del m["annual_issuance_rate"]
        partial = calculate(m)
        self.assertEqual(partial["summary"]["target_price"], original["summary"]["target_price"])
        self.assertEqual(partial["status"], "PARTIAL")
        self.assertEqual(partial["summary"]["funding_status"], "PARTIAL")
        self.assertEqual(partial["summary"]["distribution_coverage_status"], "PARTIAL")
        for row in partial["rows"]:
            for key in ("gross_buyback_proxy", "gross_buyback_cash", "distribution_cash", "distribution_coverage"):
                self.assertIsNone(row[key])
        for year in m["years"]:
            year["cash"]["gross_buyback_cash"] = 10
        complete = calculate(m)
        self.assertEqual(complete["status"], "PASS")
        self.assertEqual(complete["summary"]["distribution_coverage_status"], "PASS")

    def test_positive_exit_fcf_required_but_start_can_be_zero(self):
        m = model()
        m["fcf_conversion_exit"] = 0
        with self.assertRaisesRegex(ValueError, "exit FCF conversion"):
            calculate(m)
        m["fcf_conversion_exit"], m["fcf_conversion_start"] = 0.9, 0
        r = calculate(m)
        self.assertEqual(r["rows"][0]["fcf"], 0)
        self.assertGreater(r["summary"]["terminal_price"], 0)

    def test_debt_can_break_funding(self):
        m = model()
        m["years"][0]["cash"]["debt_principal"] = 500
        r = calculate(m)
        self.assertEqual(r["status"], "FAIL")
        self.assertEqual(r["rows"][0]["funding_status"], "FAIL")

    def test_coverage_separate_from_funding_and_financing_can_fund(self):
        m = model()
        m["payout_ratio"] = 1.2
        for y in m["years"]:
            y["cash"]["financing_inflow"] = 100
        r = calculate(m)
        self.assertEqual(r["status"], "PASS")
        self.assertEqual(r["summary"]["distribution_coverage_status"], "FAIL")
        self.assertEqual(r["summary"]["funding_status"], "PASS")

    def test_missing_cash_uses_or_opening_cash_never_zero(self):
        for key in ("debt_principal", "finance_lease_principal", "acquisitions", "other_necessary_uses"):
            m = model()
            del m["years"][0]["cash"][key]
            r = calculate(m)
            self.assertEqual(r["status"], "PARTIAL")
            self.assertIsNone(r["rows"][0]["cash_close"])
            self.assertEqual(r["rows"][1]["funding_status"], "PARTIAL")
        m = model()
        del m["opening_available_cash"]
        self.assertEqual(calculate(m)["summary"]["funding_status"], "PARTIAL")

    def test_independent_fcf_crosscheck_does_not_replace_formula(self):
        m = model()
        expected = calculate(m)["summary"]["target_price"]
        m["years"][0]["fcf"] = 900
        r = calculate(m)
        self.assertEqual(r["status"], "FAIL")
        self.assertEqual(r["summary"]["target_price"], expected)
        self.assertAlmostEqual(r["rows"][0]["fcf"], 94.5)

    def test_eps_optional_and_uses_diluted_average(self):
        m = model()
        m["years"][0]["diluted_average_shares"] = 101
        row = calculate(m)["rows"][0]
        self.assertAlmostEqual(row["eps"], 105 / 101)
        self.assertNotEqual(row["eps"], row["end_share_earnings"])
        del m["years"][0]["diluted_average_shares"]
        self.assertEqual(calculate(m)["status"], "PASS")
        self.assertIsNone(calculate(m)["rows"][0]["eps"])

    def test_zero_change_and_positive_dilution_sign(self):
        m = model()
        m["net_share_change"] = 0
        self.assertAlmostEqual(calculate(m)["rows"][0]["shares_end"], 100)
        m["net_share_change"], m["annual_issuance_rate"] = 0.01, 0.02
        self.assertAlmostEqual(calculate(m)["rows"][0]["shares_end"], 101)
        m["annual_issuance_rate"] = 0
        with self.assertRaisesRegex(ValueError, "issuance"):
            calculate(m)
        m["net_share_change"] = -1
        with self.assertRaises(ValueError):
            calculate(m)

    def test_legacy_method_and_fields_rejected(self):
        m = model()
        m["method_version"] = "direct-pe-net-shares-v2"
        with self.assertRaises(ValueError):
            calculate(m)
        for where, key in (("model", "exit_pe"), ("year", "net_shrink"), ("cash", "buyback_pe")):
            m = model()
            record = m if where == "model" else m["years"][0] if where == "year" else m["years"][0]["cash"]
            record[key] = 0
            with self.assertRaisesRegex(ValueError, "legacy"):
                calculate(m)

    def test_base_date_cannot_leave_gap_or_partial_first_year(self):
        for valuation_date in ("2030-08-01", "2031-01-01"):
            m = model()
            m["valuation_date"] = valuation_date
            with self.assertRaisesRegex(ValueError, "one day"):
                calculate(m)

    def test_actual_days_non_december_and_53_week_year(self):
        m = model()
        start = date(2030, 6, 29)
        m["valuation_date"] = start.isoformat()
        prior = start
        for days, year in zip((371, 364, 364), m["years"]):
            year["period_start"] = (prior + timedelta(days=1)).isoformat()
            prior += timedelta(days=days)
            year["period_end"] = year["cashflow_date"] = prior.isoformat()
        r = calculate(m)
        self.assertEqual(r["status"], "PASS")
        self.assertAlmostEqual(r["rows"][0]["holding_years"], 371 / 365)
        self.assertAlmostEqual(r["summary"]["holding_years"], 1099 / 365)

    def test_market_price_optional_cagr_derived_and_one_year_allowed(self):
        m = model()
        del m["market_price"]
        m["years"] = m["years"][:1]
        m["fcf_conversion_start"], m["fcf_conversion_exit"] = 0.3, 0.8
        r = calculate(m)
        self.assertNotIn("irr", r["summary"])
        self.assertAlmostEqual(r["summary"]["net_income_cagr"], 0.05)
        self.assertAlmostEqual(r["rows"][0]["fcf_conversion"], m["fcf_conversion_exit"])

    def test_research_date_requires_and_adds_stub_dividends(self):
        m = model()
        m["research_date"] = "2030-08-01"
        with self.assertRaisesRegex(ValueError, "pre_base_dividends"):
            calculate(m)
        m["pre_base_dividends"] = []
        r = calculate(m)
        tau = (date(2030, 12, 31) - date(2030, 8, 1)).days / 365
        self.assertAlmostEqual(r["summary"]["research_date_target_price"], r["summary"]["target_price"] / 1.1 ** tau)
        m["pre_base_dividends"] = [{"date": "2030-11-01", "amount_per_share": 0.6}]
        with_stub = calculate(m)
        stub_tau = (date(2030, 11, 1) - date(2030, 8, 1)).days / 365
        self.assertAlmostEqual(with_stub["summary"]["research_date_target_price"], r["summary"]["research_date_target_price"] + 0.6 / 1.1 ** stub_tau)
        self.assertEqual(with_stub["summary"]["irr"], r["summary"]["irr"])
        m["pre_base_dividends"][0]["date"] = "2030-08-01"
        with self.assertRaisesRegex(ValueError, "stub dividend dates"):
            calculate(m)

    def test_units_and_annual_end_cash_dates_required(self):
        m = model()
        m["share_unit"] = "billion"
        with self.assertRaisesRegex(ValueError, "scale"):
            calculate(m)
        m = model()
        m["years"][0]["cashflow_date"] = "2032-01-02"
        with self.assertRaisesRegex(ValueError, "annual fiscal end"):
            calculate(m)

    def test_q4_difference_is_deterministic(self):
        self.assertEqual(cumulative_to_quarters([20, 45, 80, 110]), [20, 25, 35, 30])
        with self.assertRaises(ValueError):
            cumulative_to_quarters([20, None])


class CrossCompanyTests(unittest.TestCase):
    """Synthetic economic patterns, not forecasts of named real issuers."""

    def five_year_model(self):
        m = model()
        m["years"] = [copy.deepcopy(m["years"][0]) for _ in range(5)]
        for year, y in zip(m["years"], range(2031, 2036)):
            year.update(period_start=f"{y}-01-01", period_end=f"{y}-12-31",
                        cashflow_date=f"{y}-12-31", net_income=100)
        return m

    def test_subscription_company_issuance_then_buybacks_and_dividends(self):
        m = self.five_year_model()
        profits = [100, 120, 140, 165, 190]
        conversions = [1.1, .95, 1.2, 1.1, 1.05]
        payouts, changes = [0, 0, 0, .1, .2], [.02, .02, -.01, -.02, -.02]
        m["annual_overrides"] = []
        for i, year in enumerate(m["years"]):
            year["net_income"] = profits[i]
            m["annual_overrides"].append({"period_end": year["period_end"],
                "fcf_conversion": conversions[i], "payout_ratio": payouts[i],
                "net_share_change": changes[i], "annual_issuance_rate": .02 if i < 2 else 0})
        result = calculate(m)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual([r["company_dividend"] for r in result["rows"]], [0, 0, 0, 16.5, 38])
        self.assertEqual([r["gross_buyback_cash"] for r in result["rows"][:2]], [0, 0])
        final_shares = 100 * 1.02**2 * .99 * .98**2
        self.assertAlmostEqual(result["summary"]["terminal_price"], 199.5 * 20 / final_shares)
        # Terminal and earlier distributions must use the same resolved path.
        days4 = (date(2034, 12, 31) - date(2030, 12, 31)).days / 365
        days5 = (date(2035, 12, 31) - date(2030, 12, 31)).days / 365
        expected = 16.5 / (final_shares / .98) / 1.1**days4 + (38 + 199.5 * 20) / final_shares / 1.1**days5
        self.assertAlmostEqual(result["summary"]["target_price"], expected)

    def test_expansion_company_negative_cash_then_recovery(self):
        m = self.five_year_model()
        m.update(opening_available_cash=200, net_share_change=0, payout_ratio=0, annual_issuance_rate=0)
        m["annual_overrides"] = [{"period_end": year["period_end"], "fcf_conversion": c}
                                 for year, c in zip(m["years"], [-.3, .1, .8, 1.2, .9])]
        for year in m["years"]:
            year["cash"]["gross_buyback_cash"] = 0  # Explicit adopted pause, not a missing value.
        result = calculate(m)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["rows"][0]["fcf"], -30)
        self.assertEqual(result["rows"][0]["cash_close"], 170)
        self.assertIsNone(result["rows"][0]["gross_buyback_proxy"])
        self.assertEqual(result["summary"]["terminal_price"], 18)
        self.assertEqual(result["summary"]["distribution_coverage_status"], "FAIL")
        del m["years"][0]["cash"]["gross_buyback_cash"]
        self.assertEqual(calculate(m)["summary"]["funding_status"], "PARTIAL")

    def test_partial_overrides_keep_defaults_and_invalid_paths_reject(self):
        m = model()
        before = calculate(m)
        m["annual_overrides"] = [{"period_end": "2032-12-31", "payout_ratio": 0}]
        after = calculate(m)
        self.assertEqual(after["summary"]["terminal_price"], before["summary"]["terminal_price"])
        self.assertAlmostEqual(before["summary"]["target_price"] - after["summary"]["target_price"],
                               before["rows"][1]["dividend_pv"])
        for bad in ([{"period_end": "2099-12-31", "payout_ratio": 0}],
                    [{"period_end": "2032-12-31", "net_share_change": -1}],
                    [{"period_end": "2032-12-31", "payout_ratio": None}],
                    [{"period_end": "2032-12-31", "payout_ration": .2}],
                    [{"period_end": "2033-12-31", "fcf_conversion": 0}],
                    m["annual_overrides"] * 2):
            with self.subTest(bad=bad):
                m["annual_overrides"] = bad
                with self.assertRaises(ValueError):
                    calculate(m)

    def test_half_year_issuer_history_without_invented_quarters(self):
        p = handoff()
        metric = p["metrics"][0]
        p["config"].update(market="HK", company_id="TEST-half-year", latest_actual_period="2030H1")
        metric["history_window"] = {"annual_periods": ["FY2028", "FY2029"],
                                    "interim_periods": ["2029H1", "2030H1"]}
        for entry, period in zip(metric["history"][2:], ["2029H1", "2030H1"]):
            entry["period"] = period
        for block in metric["forecast_layout"]:
            if block["section"] == "remaining_quarters":
                block["section"] = "current_year"
            for cell, period in zip(block["history_cells"][2:], ["2029H1", "2030H1"]):
                cell["period"] = period
        self.assertEqual(validate(p)["status"], "PASS")
        metric["forecast_layout"][0]["history_cells"].pop()
        self.assertEqual(validate(p)["status"], "FAIL")  # Still requires the selected evidence.

    def test_annual_only_issuer_complete_base_needs_no_quarter_block(self):
        p = handoff()
        p["config"].update(company_id="TEST-annual-only", latest_actual_period="FY2030")
        metric = p["metrics"][0]
        metric["history_window"] = {"annual_periods": ["FY2029", "FY2030"], "interim_periods": []}
        metric["history"] = metric["history"][:2]
        for entry, period in zip(metric["history"], ["FY2029", "FY2030"]):
            entry["period"] = period
        metric["forecast_layout"] = metric["forecast_layout"][1:]
        block = metric["forecast_layout"][0]
        block["history_cells"] = block["history_cells"][:2]
        for cell, period in zip(block["history_cells"], ["FY2029", "FY2030"]):
            cell["period"] = period
        self.assertEqual(validate(p)["status"], "PASS")

    def test_snapshot_restores_annual_overrides_and_rejects_wrong_dates(self):
        p = valuation_handoff()
        values = p["cases"][0]["valuation_inputs"]
        values["annual_overrides"] = [{"period_end": "2031-12-31", "payout_ratio": 0},
                                      {"period_end": "2035-12-31", "fcf_conversion": .8}]
        self.assertEqual(validate(p)["status"], "PASS")
        captured = copy.deepcopy(values)
        m = self.five_year_model()
        m.update(values)
        expected = calculate(m)["summary"]["target_price"]
        m["annual_overrides"] = []
        self.assertNotEqual(calculate(m)["summary"]["target_price"], expected)
        m.update(captured)
        self.assertEqual(calculate(m)["summary"]["target_price"], expected)
        values["annual_overrides"][0]["period_end"] = "2099-12-31"
        self.assertEqual(validate(p)["status"], "FAIL")


class HandoffTests(unittest.TestCase):
    def test_complete_synthetic_handoff(self):
        self.assertEqual(validate(handoff())["status"], "PASS")

    def test_complete_three_case_handoff(self):
        self.assertEqual(validate(valuation_handoff())["status"], "PASS")

    def test_full_valuation_pending_case_is_partial_not_zero(self):
        p = valuation_handoff()
        p["cases"][0] = {"id": "pessimistic", "status": "pending", "net_income_path": None}
        self.assertEqual(validate(p)["status"], "PARTIAL")
        p["cases"][0]["net_income_path"] = [0, 0, 0, 0]
        self.assertEqual(validate(p)["status"], "FAIL")

    def test_stale_snapshot_different_base_or_period_length_fails(self):
        for field, value in (("basis_version", "old-basis"), ("net_income_path", [99, 105, 110, 115, 120, 125]),
                             ("net_income_path", [100, 105, 110])):
            p = valuation_handoff()
            p["cases"][0][field] = value
            self.assertEqual(validate(p)["status"], "FAIL")

    def test_missing_case_or_restore_drivers_is_partial(self):
        p = valuation_handoff()
        p["cases"].pop()
        self.assertEqual(validate(p)["status"], "PARTIAL")
        p = valuation_handoff()
        del p["cases"][0]["driver_values"]
        self.assertEqual(validate(p)["status"], "PARTIAL")
        p = valuation_handoff()
        p["cases"][0]["driver_values"]["revenue"] = [120]
        self.assertEqual(validate(p)["status"], "FAIL")

    def test_old_schema_method_and_mismatched_base_date_fail(self):
        for section, key, value in ((None, "schema_version", "valuation-handoff.v1"),
                                    ("config", "method_version", "direct-pe-net-shares-v2"),
                                    ("config", "valuation_date", "2030-08-01")):
            p = handoff()
            (p if section is None else p[section])[key] = value
            self.assertEqual(validate(p)["status"], "FAIL")

    def test_forecast_can_preserve_base_losses_but_valuation_route_cannot(self):
        for base in (0, -100):
            p = handoff()
            p["config"]["base_net_income"] = base
            self.assertEqual(validate(p)["status"], "PASS")
            p["config"]["scope"] = "valuation"
            self.assertEqual(validate(p)["status"], "FAIL")

    def test_handoff_horizon_requires_five_years_or_explicit_reason(self):
        p = handoff()
        p["config"]["forecast_periods"] = p["config"]["forecast_periods"][:3]
        self.assertEqual(validate(p)["status"], "FAIL")
        p["config"]["forecast_horizon_reason"] = "  "
        self.assertEqual(validate(p)["status"], "FAIL")
        p["config"]["forecast_horizon_reason"] = "Explicit three-year contract expiry analysis"
        self.assertEqual(validate(p)["status"], "PASS")

    def test_refresh_requires_prior_snapshot_and_current_update_record(self):
        p = handoff()
        p["config"]["operation"] = "refresh"
        self.assertEqual(validate(p)["status"], "FAIL")
        p["previous_snapshot_path"] = "data/derived/companies/US/TEST/valuation/2030-07-01/snapshot.json"
        self.assertEqual(validate(p)["status"], "FAIL")
        p["updates"] = [{"as_of": "2030-07-31"}]
        self.assertEqual(validate(p)["status"], "FAIL")
        p["updates"].append(refresh_handoff()["updates"][0])
        self.assertEqual(validate(p)["status"], "PASS")
        p["previous_snapshot_path"] = "../outside.json"
        self.assertEqual(validate(p)["status"], "FAIL")

    def test_refresh_date_only_does_not_prove_update_content(self):
        p = refresh_handoff()
        p["updates"] = [{"as_of": p["config"]["as_of"]}]
        self.assertEqual(validate(p)["status"], "FAIL")

    def test_refresh_missing_dimensions_differ_from_explicit_empty(self):
        for field in ("new_source_ids", "actual_vs_forecast", "input_changes", "valuation_attribution", "unresolved"):
            p = refresh_handoff()
            del p["updates"][0][field]
            self.assertEqual(validate(p)["status"], "FAIL")
            p["updates"][0][field] = []
            self.assertEqual(validate(p)["status"], "PASS")

    def test_refresh_checks_are_structured_and_affect_result(self):
        for recorded, expected in (("PASS", "PASS"), ("PARTIAL", "PARTIAL"),
                                   ("BLOCKED", "PARTIAL"), ("FAIL", "FAIL")):
            p = refresh_handoff()
            p["updates"][0]["checks"][0]["status"] = recorded
            self.assertEqual(validate(p)["status"], expected)
        for checks in ([], ["PASS"], [{"status": "PASS"}], [{"kind": "review", "status": "unknown"}]):
            p = refresh_handoff()
            p["updates"][0]["checks"] = checks
            self.assertEqual(validate(p)["status"], "FAIL")

    def test_refresh_new_sources_must_be_declared(self):
        p = refresh_handoff()
        p["updates"][0]["new_source_ids"] = ["unknown-source"]
        self.assertEqual(validate(p)["status"], "FAIL")

    def test_operation_must_be_explicit(self):
        p = handoff()
        del p["config"]["operation"]
        self.assertEqual(validate(p)["status"], "FAIL")

    def test_material_metrics_require_valid_workbook_mapping(self):
        p = handoff()
        del p["metrics"][0]["workbook_mapping"]
        self.assertEqual(validate(p)["status"], "FAIL")
        for field, value in (("sheet", ""), ("sheet", "invalid/sheet"),
                             ("cell", "A0"), ("cell", "XFE1"), ("cell", "A1048577"),
                             ("cell", "C20:D20"), ("role", "unknown")):
            p = handoff()
            p["metrics"][0]["workbook_mapping"][0][field] = value
            self.assertEqual(validate(p)["status"], "FAIL")
        p = handoff()
        p["metrics"][0]["workbook_mapping"][0]["cell"] = "$XFD$1048576"
        self.assertEqual(validate(p)["status"], "PASS")

    def test_zero_exit_conversion_invalid_in_adopted_case(self):
        p = valuation_handoff()
        p["cases"][0]["valuation_inputs"]["fcf_conversion_exit"] = 0
        self.assertEqual(validate(p)["status"], "FAIL")

    def test_history_must_be_right_of_forecast(self):
        p = handoff()
        p["metrics"][0]["forecast_layout"][0]["history_cells"][0]["column"] = 3
        self.assertEqual(validate(p)["status"], "FAIL")

    def test_both_forecast_blocks_need_complete_history(self):
        p = handoff()
        p["metrics"][0]["forecast_layout"][1]["history_cells"].pop()
        self.assertEqual(validate(p)["status"], "FAIL")

    def test_explicit_historical_gap_partial_not_invented(self):
        p = handoff()
        p["metrics"][0]["history"][0].update(value=None, disclosure_status="unavailable")
        self.assertEqual(validate(p)["status"], "PARTIAL")
        p["metrics"][0]["history"][0]["value"] = 0
        self.assertEqual(validate(p)["status"], "FAIL")

    def test_manual_input_divergence_preserved_and_flagged(self):
        p = handoff()
        before = copy.deepcopy(p)
        r = proposed_input_changes(p, {"revenue:FY2031": 125})
        self.assertEqual(p, before)
        self.assertEqual(r[0]["workbook"], 125)
        self.assertTrue(r[0]["locked"])

    def test_decision_lock_also_protects_manual_value(self):
        p = handoff()
        p["metrics"][0]["update_policy"] = "analyst_review"
        r = proposed_input_changes(p, {"revenue:FY2031": 125})
        self.assertTrue(r[0]["locked"])

    def test_pending_input_cannot_masquerade_as_zero(self):
        p = handoff()
        p["metrics"][0]["adopted"][0].update(status="pending", value=0)
        self.assertEqual(validate(p)["status"], "FAIL")

    def test_duplicate_adopted_period_is_rejected(self):
        p = handoff()
        p["metrics"][0]["adopted"].append(copy.deepcopy(p["metrics"][0]["adopted"][0]))
        self.assertEqual(validate(p)["status"], "FAIL")

    def test_adopted_value_must_match_analyst_decision(self):
        p = handoff()
        p["metrics"][0]["adopted"][0]["value"] = 130
        self.assertEqual(validate(p)["status"], "FAIL")

    def test_dependency_cycle_detected(self):
        p = handoff()
        p["metrics"][0]["dependencies"] = ["revenue"]
        self.assertEqual(validate(p)["status"], "FAIL")

    def test_sources_cannot_escape_workspace(self):
        p = handoff()
        p["sources"][0]["path"] = "../../external/source.html"
        self.assertEqual(validate(p)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
