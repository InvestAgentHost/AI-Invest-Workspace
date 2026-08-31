import tempfile
import unittest
from pathlib import Path

from tools.congressional_monitor.agent_review import apply_agent_review, load_agent_packet, prepare_agent_review, write_review_batches


class AgentReviewTests(unittest.TestCase):
    def _parse_payload(self):
        return {"source_manifest": "sync.json", "reports": [{
            "document_id": "2001", "year": "2026", "path": "sources/x.pdf", "report_kind": "original",
            "index": {"first_name": "Jane", "last_name": "Doe", "district": "CA01", "filing_date": "8/1/2026", "filing_type": "P"},
            "parsed": {"review_queue": [{"candidate_id": "c1", "asset_name": "Acme Common Stock", "asset_type_candidates": ["ST"], "transaction_codes": ["P"], "transaction_date": "2026-07-01", "ticker_candidates": [{"ticker": "ACME", "issuer": "Acme"}], "amount_range_candidates": ["$1,001 - $15,000"], "raw_text": "evidence"}]},
        }]}

    def test_prepare_writes_batches_with_context(self):
        packet = prepare_agent_review(self._parse_payload(), batch_size=1)
        self.assertEqual(packet["candidate_count"], 1)
        candidate = packet["batches"][0]["candidates"][0]
        self.assertEqual(candidate["report_id"], "2001")
        self.assertEqual(candidate["member_id"], "jane-doe")
        with tempfile.TemporaryDirectory() as directory:
            result = write_review_batches(packet, Path(directory) / "packets")
            self.assertTrue(Path(result["manifest"]).is_file())
            self.assertTrue(Path(result["batch_paths"][0]).is_file())
            loaded = load_agent_packet(result["manifest"])
            self.assertEqual(loaded["candidate_count"], 1)
            self.assertEqual(loaded["batches"][0]["candidates"][0]["candidate_id"], "c1")

    def test_apply_promotes_only_complete_agent_approval(self):
        packet = prepare_agent_review(self._parse_payload())
        result = apply_agent_review(packet, {"source": "agent-test", "decisions": [{"candidate_id": "c1", "status": "approved", "ticker": "ACME", "issuer": "Acme", "asset_type": "ST", "transaction_code": "P", "amount_range": "$1,001 - $15,000"}]})
        self.assertEqual(result["promoted_count"], 1)
        self.assertEqual(result["agent_review"]["unreviewed_count"], 0)

    def test_apply_accepts_batch_manifest(self):
        packet = prepare_agent_review(self._parse_payload(), batch_size=1)
        with tempfile.TemporaryDirectory() as directory:
            paths = write_review_batches(packet, Path(directory) / "packets")
            result = apply_agent_review(load_agent_packet(paths["manifest"]), {"decisions": [{"candidate_id": "c1", "status": "rejected", "notes": "ambiguous"}]})
            self.assertEqual(result["promoted_count"], 0)
            self.assertEqual(result["agent_review"]["decision_count"], 1)


if __name__ == "__main__":
    unittest.main()
