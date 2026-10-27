"""Independent synthetic checks of screen-v2 gate and missing-data semantics."""
from copy import deepcopy
from decimal import Decimal
from itertools import product
import json
import unittest

from tools.stock_screen import engine_v2 as engine


def company():
    return {
        "company_id": "US/SYNTHETIC", "name": "Synthetic",
        "perimeter_years": 5, "provisional_history": False,
        "scores": {key: 4 for key in engine.SCORE_KEYS},
        "metric_review": {key: "reviewed" for key in engine.SCORE_KEYS},
        "missing_reasons": {}, "blocking_issues": [],
        "price": {"trailing_pe": 20, "percentile": 10, "history_years": 5},
    }


class ForwardTests(unittest.TestCase):
    def test_unknown_metric_requires_worst_case_quality_before_priority(self):
        c=company();c['scores']['B5']=None
        c['metric_review']['B5']='evidence_limited';c['missing_reasons']['B5']='Reviewed disclosure lacks concentration detail'
        result=engine.evaluate(c)
        self.assertTrue(result['quality_pass'])
        self.assertFalse(result['quality_robust_to_unscored'])
        self.assertEqual(result['status'],'quality_sensitive')
        self.assertEqual(result['completion_status'],'complete_limited')
        self.assertIsNone(result['scores']['B5'])
        for k in ('B1','B2','B3','B4'):c['scores'][k]=5
        self.assertEqual(engine.evaluate(c)['status'],'research_now')

    def test_invalid_capital_is_serializable_and_not_a_high_score(self):
        rows=[{'year':2025,'equity':-1,'debt_leases':0,'liquid_assets':0,
               'goodwill':0,'intangibles':0,'ebit':1}]
        result=engine.capital_return(rows,0)
        self.assertTrue(result['invalid_capital'])
        self.assertIsNone(result['score'])
        json.dumps(result,allow_nan=False)

    def test_unknown_sbc_can_only_determine_low_score_from_upper_bound(self):
        row={'year':2025,'cfo':45,'capex':0,'net_income':100,'sbc':None}
        self.assertEqual(engine.cash_conversion([row])['score'],1)
        row['cfo']=95
        self.assertIsNone(engine.cash_conversion([row])['score'])
        row['sbc']=5
        self.assertEqual(engine.cash_conversion([row])['score'],4)
        row['net_income']=0
        self.assertIsNone(engine.cash_conversion([row])['score'])
        row.update(cfo=90,net_income=100,sbc=-10)
        result=engine.cash_conversion([row])
        self.assertEqual(result['fcf_after_sbc'],90)
        self.assertEqual(result['raw_sbc'],-10)
        self.assertEqual(result['score'],4)

    def test_stage_bounds_match_every_legal_completion(self):
        keys = ("B1", "B2", "B3a")
        for values in product((None, 1, 2, 3, 4, 5), repeat=3):
            c = company()
            for key, value in zip(keys, values):
                c["scores"][key] = value
                if value is None:
                    c["metric_review"][key] = "not_applicable"
                    c["missing_reasons"][key] = "not_disclosed: synthetic"
            possible = {
                b1 >= 3 and b1 + b2 + b3a >= 9
                for b1, b2, b3a in product(
                    *((range(1, 6) if value is None else (value,)) for value in values)
                )
            }
            expected = possible.pop() if len(possible) == 1 else None
            before = deepcopy(c["scores"])
            result = engine.evaluate(c)
            with self.subTest(values=values):
                self.assertIs(result["stage_1"], expected)
                self.assertEqual(c["scores"], before)
                self.assertEqual(result["scores"], before)

    def test_any_pending_metric_prevents_automatic_priority(self):
        for key in engine.SCORE_KEYS:
            c = company()
            c["metric_review"][key] = "pending_work"
            with self.subTest(key=key):
                result = engine.evaluate(c)
                self.assertEqual(result["status"], "pending_work")
                self.assertEqual(result["completion_status"], "pending_work")

    def test_provisional_b1_one_is_not_confirmed_hard_failure(self):
        c = company()
        c["scores"]["B1"] = 1
        c["metric_review"]["B1"] = "provisional"
        result = engine.evaluate(c)
        self.assertEqual(result["status"], "provisional_review")
        self.assertEqual(result["comparability"], "provisional")

    def test_na_review_pairing_and_complete_unscorable(self):
        c = company()
        c["metric_review"]["M1"] = "not_applicable"
        with self.assertRaises(ValueError):
            engine.evaluate(c)
        c = company()
        c["scores"]["M1"] = None
        c["missing_reasons"]["M1"] = "not_disclosed: synthetic"
        with self.assertRaises(ValueError):
            engine.evaluate(c)
        for key in ("M1", "M4"):
            c["scores"][key] = None
            c["missing_reasons"][key] = "not_disclosed: synthetic"
            c["metric_review"][key] = "not_applicable"
        result = engine.evaluate(c)
        self.assertEqual(result["status"], "complete_unscorable")
        self.assertEqual(result["completion_status"], "complete")
        self.assertIsNone(result["average"])

    def test_capital_fallback_switches_entire_window(self):
        rows = [
            {"year": 2020 + i, "equity": invested, "debt_leases": 0,
             "liquid_assets": 0, "goodwill": invested - operating,
             "intangibles": 0, "ebit": 2}
            for i, (invested, operating) in enumerate(
                zip((10, 100, 100), (-1, 10, 10))
            )
        ]
        result = engine.capital_return(rows, 0)
        self.assertTrue(result["whole_window_fallback"])
        self.assertEqual(result["score"], 1)
        self.assertEqual([r["scoring_roic"] for r in result["annual"]], [.2, .02, .02])

    def test_exact_numeric_boundaries_and_half_up(self):
        rows = [
            {"year": year, "equity": 3, "debt_leases": 0,
             "liquid_assets": 0, "goodwill": 0, "intangibles": 0, "ebit": .3}
            for year in range(2020, 2023)
        ]
        self.assertEqual(engine.capital_return(rows, 0)["score"], 3)
        for end, expected in ((85, 5), (95, 4), (105, 3), (120, 2)):
            result = engine.allocation(
                {"including_goodwill_median": .1},
                [{"filing_shares": 100}, {"filing_shares": end}],
            )
            with self.subTest(shares_end=end):
                self.assertEqual(result["share_subscore"], expected)
        for delta, expected in (("-2", 2), ("-.5", 3), (".5", 4), ("2", 5)):
            self.assertEqual(engine.gross_score(Decimal(delta)), expected)
        scores = {"I1": 2.9, "I2": 2.9, "I3": 2.9, "I4": 3, "I5": 3.05}
        result = engine.factor(scores, list(scores))
        self.assertEqual(result["mean_unrounded"], "2.95")
        self.assertEqual(result["score"], 3.0)


if __name__ == "__main__":
    unittest.main()
