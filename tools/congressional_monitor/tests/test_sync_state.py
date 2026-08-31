import tempfile
import unittest
from pathlib import Path
import zipfile
import hashlib
from unittest.mock import patch

from tools.congressional_monitor.dedupe import deduplicate_trades
from tools.congressional_monitor.sync import sync_house_ptrs
from tools.congressional_monitor.sync_state import build_state, diff_states, load_state, write_state


def sync_result(*reports):
    return {"index_file": "index.zip", "member": None, "requested_count": len(reports), "reports": list(reports)}


class SyncStateTests(unittest.TestCase):
    def test_first_run_marks_all_reports_new(self):
        current = build_state(sync_result({"document_id": "1", "year": "2026", "status": "existing", "index": {"filing_date": "8/1/2026"}}), generated_at="2026-08-31T00:00:00Z")
        changes = diff_states(None, current)
        self.assertTrue(changes["first_run"])
        self.assertEqual(changes["counts"]["new_reports"], 1)

    def test_same_report_status_transition_is_not_business_change(self):
        old = build_state(sync_result({"document_id": "1", "year": "2026", "status": "downloaded", "path": "a.pdf", "sha256": "abc", "bytes": 10, "index": {"filing_date": "8/1/2026"}}), generated_at="old")
        new = build_state(sync_result({"document_id": "1", "year": "2026", "status": "existing", "path": "a.pdf", "sha256": "abc", "bytes": 10, "index": {"filing_date": "8/1/2026"}}), generated_at="new")
        changes = diff_states(old, new)
        self.assertEqual(changes["counts"]["new_reports"], 0)
        self.assertEqual(changes["counts"]["changed_reports"], 0)
        self.assertEqual(changes["counts"]["status_changes"], 1)

    def test_file_hash_change_is_report_change(self):
        old = build_state(sync_result({"document_id": "1", "year": "2026", "status": "existing", "sha256": "abc", "index": {"filing_date": "8/1/2026"}}))
        new = build_state(sync_result({"document_id": "1", "year": "2026", "status": "existing", "sha256": "def", "index": {"filing_date": "8/1/2026"}}))
        changes = diff_states(old, new)
        self.assertEqual(changes["counts"]["changed_reports"], 1)

    def test_candidate_ids_are_diffed(self):
        base_report = {"document_id": "1", "year": "2026", "status": "review_ready", "index": {}, "parsed": {"pages": [{"candidates": [{"candidate_id": "c1", "review_required": True}]}]}}
        old = build_state(sync_result(base_report))
        updated_report = {**base_report, "parsed": {"pages": [{"candidates": [{"candidate_id": "c1", "review_required": True}, {"candidate_id": "c2", "valid_for_curated": True}]}]}}
        new = build_state(sync_result(updated_report))
        changes = diff_states(old, new)
        self.assertEqual(changes["counts"]["new_candidates"], 1)
        self.assertEqual(changes["new_candidate_ids"], ["c2"])

    def test_state_write_is_readable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "state.json"
            state = build_state(sync_result())
            write_state(path, state)
            self.assertEqual(load_state(path)["schema_version"], 1)

    def test_different_limits_do_not_infer_removed_reports(self):
        old = build_state({"index_file": "index.zip", "member": "Pelosi", "limit": None, "reports": [{"document_id": "1", "year": "2026", "status": "existing", "index": {}}]})
        new = build_state({"index_file": "index.zip", "member": "Pelosi", "limit": 1, "reports": []})
        changes = diff_states(old, new)
        self.assertEqual(changes["counts"]["removed_reports"], 0)

    def test_state_uses_document_id_across_years_and_migrates_old_key(self):
        current = build_state(sync_result({"document_id": "2001", "year": "2026", "status": "existing", "index": {}}))
        self.assertEqual(sorted(current["reports"]), ["2001"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            write_state(path, {"schema_version": 1, "generated_at": "x", "reports": {"2025:2001": {"document_id": "2001"}}})
            loaded = load_state(path)
            self.assertEqual(sorted(loaded["reports"]), ["2001"])

    def test_batch_sync_deduplicates_indexes_and_keeps_amendment_lineage(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "2025FD.zip"
            second = Path(directory) / "2026FD.zip"
            text = "Prefix\tLast\tFirst\tSuffix\tFilingType\tStateDst\tYear\tFilingDate\tDocID\n\tDoe\tJane\t\tP\tCA01\t2025\t6/1/2025\t20012345\n\tDoe\tJane\t\tA\tCA01\t2025\t7/1/2025\t10012345\n"
            with zipfile.ZipFile(first, "w") as archive:
                archive.writestr("2025FD.txt", text)
            with zipfile.ZipFile(second, "w") as archive:
                archive.writestr("2026FD.txt", text.replace("2025", "2026"))
            result = sync_house_ptrs([first, second], output_root=Path(directory) / "pdfs")
            self.assertEqual(result["requested_count"], 2)
            self.assertEqual(result["duplicate_index_rows"], 2)
            self.assertEqual(result["counts"], {"discovered": 2})
            amendment = next(item for item in result["reports"] if item["report_kind"] == "amendment")
            self.assertEqual(amendment["lineage_status"], "unlinked_amendment")

    def test_incremental_reuses_text_layer_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            index = Path(directory) / "2025FD.zip"
            with zipfile.ZipFile(index, "w") as archive:
                archive.writestr("2025FD.txt", "Prefix\tLast\tFirst\tSuffix\tFilingType\tStateDst\tYear\tFilingDate\tDocID\n\tDoe\tJane\t\tP\tCA01\t2025\t6/1/2025\t20012345\n")
            root = Path(directory) / "pdfs"
            report = root / "2025" / "20012345.pdf"
            report.parent.mkdir(parents=True)
            report.write_bytes(b"not-a-real-pdf")
            first = sync_house_ptrs(index, output_root=root, filing_types=("P",))
            state = build_state(first)
            second = sync_house_ptrs(index, output_root=root, filing_types=("P",), previous_state=state, incremental=True)
            self.assertEqual(second["reports"][0].get("incremental_reused"), ["text_layer"])

    def test_incremental_reuse_preserves_review_ready_status(self):
        with tempfile.TemporaryDirectory() as directory:
            index = Path(directory) / "2025FD.zip"
            with zipfile.ZipFile(index, "w") as archive:
                archive.writestr("2025FD.txt", "Prefix\tLast\tFirst\tSuffix\tFilingType\tStateDst\tYear\tFilingDate\tDocID\n\tDoe\tJane\t\tP\tCA01\t2025\t6/1/2025\t20012345\n")
            root = Path(directory) / "pdfs"
            report = root / "2025" / "20012345.pdf"
            report.parent.mkdir(parents=True)
            report.write_bytes(b"scan")
            digest = hashlib.sha256(b"scan").hexdigest()
            previous = {"reports": {"20012345": {
                "document_id": "20012345", "year": "2025", "status": "review_ready",
                "sha256": digest, "bytes": 4, "text_layer": {"ocr_required": True},
                "candidate_ids": ["c1"], "review_candidate_ids": ["c1"],
                "validated_candidate_ids": [], "candidate_count": 1,
                "review_count": 1, "validated_count": 0,
            }}}
            with patch("tools.congressional_monitor.sync._text_layer_status", return_value={"ocr_required": True}):
                result = sync_house_ptrs(index, output_root=root, filing_types=("P",), previous_state=previous, incremental=True, ocr=True)
            self.assertEqual(result["reports"][0]["status"], "review_ready")

    def test_cross_year_trade_duplicates_are_removed(self):
        row = {"id": "generated-1", "member_id": "member", "transaction_date": "2025-01-01", "ticker": "ACME", "asset_type": "ST", "transaction_code": "P", "owner_code": "SP", "amount_range": "A", "issuer": "Acme", "description": "100 shares", "quantity": 100, "quantity_unit": "shares", "report_id": "R1"}
        result = deduplicate_trades([row, {**row, "id": "generated-2", "report_id": "R2", "source_file": "other.json"}])
        self.assertEqual(result["duplicate_count"], 1)
        self.assertEqual(len(result["trades"]), 1)


if __name__ == "__main__":
    unittest.main()
