import json
from pathlib import Path
import tempfile
import unittest

from tools.congressional_monitor.batch_parse import build_effective_view, detect_event_alerts, parse_sync_manifest, summarize_effective_trades
from tools.congressional_monitor.ptr_text import parse_text_layer_pdf


class BatchParseTests(unittest.TestCase):
    def test_text_layer_parser_extracts_real_ptr_rows(self):
        path = Path("sources/providers/house-clerk/2025/pelosi/20026590.pdf")
        result = parse_text_layer_pdf(path, report={"document_id": "20026590", "year": "2025"})
        self.assertEqual(len(result["validated_candidates"]), 9)
        self.assertEqual(result["validated_candidates"][0]["ticker_candidates"][0]["ticker"], "GOOGL")
        self.assertEqual(result["validated_candidates"][0]["quantity_unit"], "contracts")

    def test_batch_manifest_separates_ocr_queue_and_effective_trades(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "sync.json"
            manifest.write_text(json.dumps({"reports": [
                {"document_id": "20026590", "year": "2025", "status": "existing", "path": "sources/providers/house-clerk/2025/pelosi/20026590.pdf", "sha256": "abc", "text_layer": {"ocr_required": False}, "index": {"first_name": "Nancy", "last_name": "Pelosi", "district": "CA11", "filing_date": "1/17/2025", "filing_type": "P"}},
                {"document_id": "1001", "year": "2025", "status": "existing", "path": str(Path(directory) / "scan.pdf"), "text_layer": {"ocr_required": True}, "index": {"filing_type": "A"}},
            ]}), encoding="utf-8")
            result = parse_sync_manifest(manifest)
            self.assertEqual(result["counts"]["parsed"], 1)
            self.assertEqual(result["counts"]["ocr_queue"], 1)
            self.assertEqual(result["counts"]["effective_trade_count"], 9)

    def test_explicit_amendment_replaces_original_report(self):
        original = {"document_id": "P1", "report_kind": "original"}
        amendment = {"document_id": "A1", "report_kind": "amendment", "amends_report_id": "P1"}
        trades = [{"report_id": "P1", "ticker": "OLD"}, {"report_id": "A1", "ticker": "NEW"}]
        result = build_effective_view([original, amendment], trades)
        self.assertEqual([item["ticker"] for item in result["trades"]], ["NEW"])
        self.assertEqual(result["superseded_reports"], [{"report_id": "P1", "replaced_by": "A1"}])

    def test_event_summary_and_alerts_are_descriptive(self):
        trades = [
            {"member_id": "m1", "member_name": "Jane Doe", "ticker": "ACME", "transaction_code": "P", "asset_type": "ST", "transaction_date": "2026-01-01", "report_id": "P1"},
            {"member_id": "m2", "member_name": "John Roe", "ticker": "ACME", "transaction_code": "S", "asset_type": "ST", "transaction_date": "2026-01-20", "report_id": "P2"},
        ]
        parsed = {"effective": {"trades": trades}, "changes": {"new_reports": [{"document_id": "P1"}]}}
        summary = summarize_effective_trades(trades)
        self.assertEqual(summary["trade_count"], 2)
        alerts = detect_event_alerts(parsed)
        self.assertTrue(any(item["type"] == "multi_member_ticker" for item in alerts))
        self.assertTrue(any(item["type"] == "new_report" for item in alerts))
        distant = {"effective": {"trades": [{**trades[0], "transaction_date": "2026-01-01"}, {**trades[1], "transaction_date": "2026-03-15"}]}}
        self.assertFalse(any(item["type"] == "multi_member_ticker" for item in detect_event_alerts(distant, window_days=30)))


if __name__ == "__main__":
    unittest.main()
