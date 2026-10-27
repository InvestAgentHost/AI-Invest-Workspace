import unittest
from tools.stock_screen.audit_run import audit, load_engine


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.engine = load_engine()
        self.payload = {
            "rule_version": "reverse-v1", "as_of": "2026-10-20", "price_date": "2026-10-19",
            "companies": [{"company_id": "US/TEST", "name": "Test", "perimeter_years": 10,
                "scores": {k: 4 for k in self.engine.SCORE_KEYS}, "missing_reasons": {},
                "blocking_issues": [], "review_flags": [],
                "price": {"trailing_pe": 20, "percentile": 20, "history_years": 10}}],
        }

    def evaluate(self, results=None, ledger=None):
        if results is None:
            results = self.engine.aggregate(self.payload)
        if ledger is None:
            ledger = [{"company_id": c["company_id"], "metric_id": k, "score": v}
                      for c in self.payload["companies"] for k, v in c["scores"].items()]
        return audit(self.payload, results, ledger, self.engine)

    def test_valid_aggregation_does_not_imply_complete_screen(self):
        c = self.payload["companies"][0]
        for k in ("B1", "B2", "B4", "M3", "M4", "I2", "I4"):
            c["scores"][k] = None
            c["missing_reasons"][k] = "not_retrieved: calculation pending"
        r = self.evaluate()
        self.assertTrue(r["consistency_pass"])
        self.assertEqual(r["delivery_status"], "incomplete")
        self.assertEqual(r["stage_1_determined"], 0)
        self.assertEqual(r["factor_counts"], {"B": 0, "M": 0, "I": 0})

    def test_complete_scores_are_structure_ready(self):
        self.assertEqual(self.evaluate()["delivery_status"], "structure_ready")

    def test_removed_company_does_not_require_all_factors(self):
        c = self.payload["companies"][0]
        c["scores"]["M5"] = 1
        c["scores"]["B1"] = None
        c["missing_reasons"]["B1"] = "not_retrieved: pending"
        self.assertEqual(self.evaluate()["delivery_status"], "structure_ready")

    def test_stale_results_and_disappearing_repairs_are_detected(self):
        results = self.engine.aggregate(self.payload)
        c = self.payload["companies"][0]
        c["scores"]["B1"] = None
        c["missing_reasons"]["B1"] = "not_retrieved: overwritten"
        self.assertFalse(self.evaluate(results=results)["consistency_pass"])

    def test_ledger_mismatch_is_detected(self):
        records = [{"company_id": "US/TEST", "metric_id": k, "score": v}
                   for k, v in self.payload["companies"][0]["scores"].items()]
        records[0]["score"] = 2
        self.assertFalse(self.evaluate(ledger=records)["consistency_pass"])


if __name__ == "__main__":
    unittest.main()
