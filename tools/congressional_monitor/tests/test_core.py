import unittest
from pathlib import Path

import json
import tempfile

from tools.congressional_monitor.core import cross_chamber_report, filter_trades, infer_positions, load_dataset, summarize, validate_dataset


class CongressionalMonitorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = load_dataset(Path(__file__).parents[3] / "data" / "curated")

    def test_loads_current_snapshot(self):
        self.assertEqual(len(self.dataset["members"]), 4)
        self.assertEqual(len(self.dataset["trades"]), 54)

    def test_filters_member_and_direction(self):
        rows = filter_trades(self.dataset["trades"], member="CA11", direction="P")
        self.assertEqual(len(rows), 19)
        self.assertTrue(all(row["member_id"] == "pelosi-nancy" for row in rows))

    def test_filters_ticker_and_asset(self):
        rows = filter_trades(self.dataset["trades"], ticker="BE", asset_type="OP")
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["asset_type"] == "OP" for row in rows))

    def test_summary_counts(self):
        stats = summarize(self.dataset["trades"])
        self.assertEqual(stats["trade_count"], 54)
        self.assertEqual(stats["member_count"], 4)
        self.assertEqual(stats["asset_types"]["ST"], 40)

    def test_quality_check_accepts_generated_ids(self):
        quality = validate_dataset(self.dataset)
        self.assertTrue(quality["ok"])
        self.assertEqual(quality["missing_required_fields"], [])

    def test_infers_explicit_be_share_and_option_changes(self):
        rows = filter_trades(self.dataset["trades"], member="CA11", ticker="BE")
        positions = infer_positions(rows)
        shares = next(item for item in positions if item["asset_type"] == "ST")
        options = next(item for item in positions if item["asset_type"] == "OP")
        self.assertEqual(shares["known_net_quantity_change"], 15000)
        self.assertEqual(shares["quantity_unit"], "shares")
        self.assertEqual(options["known_net_quantity_change"], 200)
        self.assertEqual(options["quantity_unit"], "contracts")

    def test_does_not_turn_unknown_quantity_into_zero(self):
        rows = filter_trades(self.dataset["trades"], member="Gottheimer", direction="P")
        unknown = next(item for item in infer_positions(rows) if item["ticker"] == "CRWD")
        self.assertIsNone(unknown["known_net_quantity_change"])
        self.assertEqual(unknown["confidence"], "partial")

    def test_loads_senate_efd_and_cross_chamber_report(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "senate.json"
            path.write_text(json.dumps({"data": [{"member_id": "senator-doe", "member_name": "Jane Doe", "transaction_date": "2026-07-01", "filing_date": "2026-07-10", "ticker": "BE", "issuer": "Bloom Energy", "transaction_type": "Purchase", "amount_range": "$1,001 - $15,000", "asset_type": "ST", "owner_code": "SP", "report_id": "S1"}]}), encoding="utf-8")
            dataset = load_dataset(Path(__file__).parents[3] / "data" / "curated", senate_files=[path])
            self.assertEqual(len(dataset["trades"]), 55)
            self.assertEqual(dataset["trades"][-1]["chamber"], "Senate")
            report = cross_chamber_report(dataset["trades"], from_date="2026-07-01")
            self.assertIn("Senate", report["chambers"])
            self.assertTrue(any(item["ticker"] == "BE" for item in report["joint_tickers"]))


if __name__ == "__main__":
    unittest.main()
