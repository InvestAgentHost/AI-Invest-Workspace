"""Behavioral tests using synthetic companies, without touching research files."""
import copy
import unittest

from valuation_checks import (calculate, cumulative_to_quarters, present_value,
                              proposed_input_changes, validate)


def model():
    # Synthetic manufacturer; no franchise/region/strategy assumptions.
    periods = []
    for i in range(3):
        y = 2031 + i
        periods.append({"period_start": f"{y}-01-01", "period_end": f"{y}-12-31",
                        "cashflow_date": f"{y}-12-31", "net_income": 100 * 1.05 ** (i + 1),
                        "net_shrink": 0.01, "fcf_conversion": 0.9,
                        "payout": 0.5, "exit_pe": 20, "diluted_average_shares": 99 - i,
                        "cash": {"dilution_rate": 0.002, "buyback_pe": 20,
                                 "debt_principal": 0, "financing_inflow": 0,
                                 "finance_lease_principal": 0, "other_necessary_uses": 0,
                                 "other_inflows": 0, "equity_issuance_cash": 0,
                                 "minimum_cash": 0}})
    return {"method_version": "direct-pe-net-shares-v2", "valuation_date": "2030-12-31",
            "currency": "USD", "amount_unit": "million", "share_unit": "million",
            "market_cap": 2000, "current_shares": 100, "required_return": 0.1,
            "opening_available_cash": 100, "years": periods}


def handoff():
    periods = ["FY2028", "FY2029", "2030Q1", "2030Q2"]
    history = [{"period": p, "value": 100 + i, "disclosure_status": "reported",
                "source_ids": ["filing"]} for i, p in enumerate(periods)]
    layouts = [{"section": section, "sheet": "Drivers", "row": row,
                "forecast_columns": [3, 4],
                "history_cells": [{"period": p, "column": 7 + i,
                                   "actual_sheet": "Financials", "actual_cell": f"{chr(67 + i)}8"}
                                  for i, p in enumerate(periods)]}
               for section, row in (("remaining_quarters", 8), ("future_years", 20))]
    return {
        "schema_version": "valuation-handoff.v1",
        "config": {"company_id": "TEST-industrial", "market": "US", "as_of": "2030-08-01",
                   "valuation_date": "2030-08-01", "fiscal_year_end": "12-31",
                   "fiscal_calendar_note": "calendar year", "currency": "USD",
                   "amount_unit": "million", "share_unit": "million",
                   "method_version": "direct-pe-net-shares-v2", "latest_actual_period": "2030Q2",
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
                     "adopted": [{"period": "FY2031", "value": 120, "status": "adopted",
                                  "decision_id": "decision1", "evidence_ids": ["filing"]}]}],
        "decisions": [{"id": "decision1", "metric_id": "revenue", "date": "2030-08-01",
                       "origin": "analyst", "reason": "capacity and volume assumptions reviewed",
                       "values": {"FY2031": 120}, "locked": True}]}


class CalculationTests(unittest.TestCase):
    def test_conversion_changes_funding_not_direct_pe_value(self):
        a, b = model(), model()
        b["years"][0]["fcf_conversion"] = 0.75
        ra, rb = calculate(a), calculate(b)
        self.assertEqual(ra["rows"][0]["irr"], rb["rows"][0]["irr"])
        self.assertEqual(ra["rows"][0]["holder_exit_value"], rb["rows"][0]["holder_exit_value"])
        self.assertNotEqual(ra["rows"][0]["cash_close"], rb["rows"][0]["cash_close"])

    def test_shrink_increases_holder_value_without_buyback_cashflow(self):
        m = model()
        row = calculate(m)["rows"][0]
        self.assertAlmostEqual(row["shares_end"], 99)
        self.assertAlmostEqual(row["holder_dividend"], 105 * 0.5 / 0.99)
        self.assertAlmostEqual(row["holder_exit_value"], 105 * 20 / 0.99)
        flows = [(row["holder_dividend"] + row["holder_exit_value"], row["holding_years"])]
        self.assertAlmostEqual(present_value(flows, row["irr"]), 2000, places=8)

    def test_gross_repurchase_includes_dilution(self):
        row = calculate(model())["rows"][0]
        self.assertAlmostEqual(row["gross_buyback_cash"], (0.01 + 0.002) / 0.99 * 105 * 20)

    def test_debt_can_break_cash_feasibility(self):
        m = model()
        m["years"][0]["cash"]["debt_principal"] = 500
        r = calculate(m)
        self.assertEqual(r["status"], "FAIL")
        self.assertEqual(r["rows"][0]["funding_status"], "FAIL")

    def test_missing_debt_is_not_zero(self):
        m = model()
        del m["years"][0]["cash"]["debt_principal"]
        r = calculate(m)
        self.assertEqual(r["status"], "PARTIAL")
        self.assertIsNone(r["rows"][0]["cash_close"])
        self.assertEqual(r["rows"][1]["funding_status"], "PARTIAL")

    def test_explicit_cashflow_conversion_conflict(self):
        m = model()
        m["years"][0]["fcf"] = 90
        self.assertEqual(calculate(m)["status"], "FAIL")

    def test_full_year_cash_budget_cannot_ignore_annual_fcf(self):
        m = model()
        m["years"][0]["budget_fcf"] = 500
        self.assertEqual(calculate(m)["status"], "FAIL")

    def test_eps_uses_diluted_weighted_shares(self):
        m = model()
        m["years"][0]["diluted_average_shares"] = 101
        row = calculate(m)["rows"][0]
        self.assertAlmostEqual(row["eps"], 105 / 101)
        self.assertNotEqual(row["eps"], row["end_share_earnings"])

    def test_zero_shrink_and_net_dilution(self):
        m = model()
        m["years"][0]["net_shrink"] = 0
        self.assertAlmostEqual(calculate(m)["rows"][0]["shares_end"], 100)
        m["years"][0]["net_shrink"] = -0.01
        m["years"][0]["cash"]["dilution_rate"] = 0.02
        self.assertAlmostEqual(calculate(m)["rows"][0]["shares_end"], 101)

    def test_legacy_formula_rejected(self):
        m = model()
        m["method_version"] = "ni-times-c-times-pe"
        with self.assertRaises(ValueError):
            calculate(m)

    def test_transition_cannot_be_skipped(self):
        m = model()
        m["valuation_date"] = "2030-08-01"
        with self.assertRaisesRegex(ValueError, "transition"):
            calculate(m)

    def test_residual_fiscal_year_needs_residual_cash_budget(self):
        m = model()
        m["valuation_date"] = "2031-10-01"
        with self.assertRaisesRegex(ValueError, "residual"):
            calculate(m)
        y = m["years"][0]
        y.update(dividend_after_valuation=12, budget_fcf=20)
        y["cash"]["gross_buyback_cash"] = 5
        row = calculate(m)["rows"][0]
        self.assertLess(row["holding_years"], 0.3)
        self.assertEqual(row["company_dividend"], 12)
        self.assertEqual(row["cash_close"], 103)

    def test_non_december_fiscal_year(self):
        m = model()
        m["valuation_date"] = "2030-06-30"
        for i, y in enumerate(m["years"]):
            y["period_start"] = f"{2030 + i}-07-01"
            y["period_end"] = y["cashflow_date"] = f"{2031 + i}-06-30"
        self.assertEqual(calculate(m)["status"], "PASS")

    def test_q4_difference_is_deterministic(self):
        self.assertEqual(cumulative_to_quarters([20, 45, 80, 110]), [20, 25, 35, 30])
        with self.assertRaises(ValueError):
            cumulative_to_quarters([20, None])


class HandoffTests(unittest.TestCase):
    def test_complete_synthetic_handoff(self):
        self.assertEqual(validate(handoff())["status"], "PASS")

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
