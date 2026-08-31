import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.congressional_monitor.ocr import GLMOCRConfig, GLMOCRClient, assess_ocr_document, assess_ocr_page
from tools.congressional_monitor.ptr_ocr import parse_and_validate_page
from tools.congressional_monitor.house_index import read_house_index, summarize_house_index
from tools.congressional_monitor.review import apply_review_decisions, review_template
from tools.congressional_monitor.security_map import amount_range_candidates, ticker_candidates
from tools.congressional_monitor.house_download import download_ptr
from tools.congressional_monitor.sync import sync_house_ptrs
from tools.congressional_monitor.senate_efd import read_senate_efd, summarize_senate_efd


class OCRTests(unittest.TestCase):
    def test_config_requires_key(self):
        with self.assertRaises(Exception):
            GLMOCRClient(GLMOCRConfig(api_key=""))

    @patch("requests.post")
    def test_client_normalizes_text_and_probability(self, post):
        class Response:
            status_code = 200

            def json(self):
                return {"status": "succeeded", "words_result": [{"words": "AAPL", "probability": {"average": 0.9}}, {"words": "P", "probability": {"average": 0.8}}]}

        post.return_value = Response()
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "page.png"
            image.write_bytes(b"png")
            result = GLMOCRClient(GLMOCRConfig(api_key="test")).ocr_image(image)
        self.assertEqual(result["text"], "AAPL\nP")
        self.assertAlmostEqual(result["average_probability"], 0.85)
        post.assert_called_once()

    def test_page_assessment_flags_low_confidence_and_missing_row_signals(self):
        result = assess_ocr_page({
            "page": 2,
            "status": "succeeded",
            "words_result": [
                {"words": "Periodic Transaction Report", "probability": {"average": 0.99}},
                {"words": "Full Asset Name", "probability": {"average": 0.95}},
                {"words": "Date of Transaction", "probability": {"average": 0.95}},
                {"words": "AAPL", "probability": {"average": 0.65}, "location": {"left": 1, "top": 2}},
            ],
        })
        self.assertTrue(result["review_required"])
        self.assertIn("low_confidence_blocks", result["issues"])
        self.assertIn("no_date_candidate", result["issues"])
        self.assertEqual(result["low_confidence_blocks"][0]["words"], "AAPL")

    def test_document_assessment_accepts_ocr_pdf_wrapper(self):
        result = assess_ocr_document({
            "source_file": "sample.pdf",
            "page_count": 1,
            "pages": [{
                "page": 1,
                "status": "succeeded",
                "average_probability": 0.99,
                "words_result": [{"words": "Periodic Transaction Report Full Asset Name Date of Transaction Amount of Transaction 01/02/2026 $1,001 - $15,000 P", "probability": {"average": 0.99}}],
            }],
        })
        self.assertFalse(result["review_required"])
        self.assertEqual(result["pages"][0]["signals"]["date_candidates"], ["01/02/2026"])

    def test_ptr_parser_rebuilds_a_high_confidence_row(self):
        def block(left, top, words):
            return {"location": {"left": left, "top": top, "width": 20, "height": 14}, "words": words, "probability": {"average": 0.98}}

        result = parse_and_validate_page({
            "page": 2,
            "status": "succeeded",
            "words_result": [
                block(150, 600, "DC"),
                block(212, 600, "ACME CORPORATION CMN"),
                block(978, 600, "01/22/26"),
                block(1100, 600, "02/03/26"),
                block(628, 600, "x"),
                block(1229, 600, "x"),
            ],
        })
        self.assertEqual(len(result["validated_candidates"]), 1)
        candidate = result["validated_candidates"][0]
        self.assertEqual(candidate["asset_name"], "ACME CORPORATION CMN")
        self.assertEqual(candidate["transaction_date"], "2026-01-22")
        self.assertEqual(candidate["transaction_codes"], ["P"])
        self.assertEqual(candidate["amount_columns"], ["A"])
        self.assertEqual(candidate["asset_type_candidates"], ["ST"])

    def test_ptr_parser_keeps_ambiguous_rows_in_review_queue(self):
        def block(left, top, words, probability=0.98):
            return {"location": {"left": left, "top": top, "width": 20, "height": 14}, "words": words, "probability": {"average": probability}}

        result = parse_and_validate_page({
            "page": 2,
            "words_result": [
                block(150, 600, "DC"), block(212, 600, "ACME CORPORATION CMN"),
                block(978, 600, "01/22/26"), block(628, 600, "x"), block(681, 600, "x"),
            ],
        })
        self.assertEqual(len(result["validated_candidates"]), 0)
        self.assertIn("transaction_direction_ambiguous", result["review_queue"][0]["issues"])
        self.assertIn("amount_range_ambiguous", result["review_queue"][0]["issues"])

    def test_house_index_reads_ptr_rows_from_zip(self):
        import zipfile

        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "2025FD.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("2025FD.txt", "Prefix\tLast\tFirst\tSuffix\tFilingType\tStateDst\tYear\tFilingDate\tDocID\n\tPelosi\tNancy\t\tP\tCA11\t2025\t6/1/2025\t20012345\n\tPelosi\tNancy\t\tC\tCA11\t2025\t6/2/2025\t10012345\n")
            rows = read_house_index(archive_path, member="CA11")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["document_id"], "20012345")
            self.assertEqual(summarize_house_index(rows)["ptr_count"], 1)

    def test_house_member_date_range_is_chronological(self):
        rows = [
            {"first_name": "A", "last_name": "Member", "district": "CA01", "filing_date": "11/14/2025", "document_id": "1"},
            {"first_name": "A", "last_name": "Member", "district": "CA01", "filing_date": "7/24/2025", "document_id": "2"},
        ]
        member = summarize_house_index(rows)["members"][0]
        self.assertEqual(member["first_filing_date"], "7/24/2025")
        self.assertEqual(member["last_filing_date"], "11/14/2025")

    def test_review_template_and_promotion_require_complete_fields(self):
        review = {"source_file": "sample.pdf", "source_sha256": "abc", "review_queue": [{
            "candidate_id": "abc-p002-r001", "asset_name": "ACME CORPORATION CMN", "asset_type_candidates": ["ST"],
            "transaction_codes": ["P"], "transaction_date": "2026-01-22", "owner_code": "DC", "raw_blocks": [],
        }]}
        template = review_template(review)
        self.assertEqual(template["decisions"][0]["candidate_id"], "abc-p002-r001")
        result = apply_review_decisions(review, {"decisions": [{
            "candidate_id": "abc-p002-r001", "status": "approved", "ticker": "ACME", "issuer": "ACME Corporation",
            "amount_range": "$1,001 - $15,000", "member_id": "test-member", "member_name": "Test Member",
            "district": "CA01", "report_id": "20099999", "filing_date": "2026-02-01",
        }]})
        self.assertEqual(result["promoted_count"], 1)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["trades"][0]["transaction_code"], "P")

    def test_review_rejects_incomplete_approval(self):
        review = {"review_queue": [{"candidate_id": "c1", "asset_name": "ACME", "asset_type_candidates": ["ST"], "transaction_codes": ["P"], "transaction_date": "2026-01-22"}]}
        result = apply_review_decisions(review, {"decisions": [{"candidate_id": "c1", "status": "approved"}]})
        self.assertEqual(result["promoted_count"], 0)
        self.assertIn("missing_ticker", result["errors"][0]["issues"])

    def test_security_and_amount_mappings_are_conservative(self):
        self.assertEqual(ticker_candidates("KIMBERLY-CLARK CORPORATION CMN")[0]["ticker"], "KMB")
        self.assertEqual(amount_range_candidates(["A"]), ["$1,001 - $15,000"])
        self.assertEqual(ticker_candidates("UNKNOWN PRIVATE ASSET"), [])

    @patch("requests.get")
    def test_house_download_writes_checksum_and_refuses_overwrite(self, get):
        class Response:
            status_code = 200
            def iter_content(self, chunk_size=0):
                return iter([b"%PDF-test"])
            def close(self):
                pass
        get.return_value = Response()
        with tempfile.TemporaryDirectory() as directory:
            result = download_ptr("12345678", 2026, output_dir=directory)
            self.assertTrue(Path(result["path"]).is_file())
            self.assertEqual(result["bytes"], 9)
            with self.assertRaises(FileExistsError):
                download_ptr("12345678", 2026, output_dir=directory)

    def test_sync_discovers_existing_report_and_writes_status(self):
        import zipfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "sources"
            index = Path(directory) / "2025FD.zip"
            with zipfile.ZipFile(index, "w") as archive:
                archive.writestr("2025FD.txt", "Prefix\tLast\tFirst\tSuffix\tFilingType\tStateDst\tYear\tFilingDate\tDocID\n\tPelosi\tNancy\t\tP\tCA11\t2025\t6/1/2025\t20012345\n")
            report = root / "2025" / "20012345.pdf"
            report.parent.mkdir(parents=True)
            report.write_bytes(b"not-a-real-pdf")
            result = sync_house_ptrs(index, output_root=root, member="Pelosi")
            self.assertEqual(result["counts"], {"existing": 1})
            self.assertEqual(result["reports"][0]["text_layer"]["ocr_required"], True)

    @patch("tools.congressional_monitor.sync.download_ptr")
    def test_sync_uses_financial_pdf_url_for_amendments(self, download):
        import zipfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "sources"
            index = Path(directory) / "2025FD.zip"
            with zipfile.ZipFile(index, "w") as archive:
                archive.writestr("2025FD.txt", "Prefix\tLast\tFirst\tSuffix\tFilingType\tStateDst\tYear\tFilingDate\tDocID\n\tDoe\tJane\t\tA\tCA01\t2025\t6/1/2025\t10073311\n")
            pdf = root / "2025" / "10073311.pdf"
            def fake_download(*args, **kwargs):
                pdf.parent.mkdir(parents=True)
                pdf.write_bytes(b"pdf")
                return {"path": str(pdf), "sha256": "abc", "bytes": 3}
            download.side_effect = fake_download
            result = sync_house_ptrs(index, output_root=root, filing_types=("A",), download=True)
            self.assertEqual(result["counts"], {"downloaded": 1})
            self.assertIn("financial-pdfs", download.call_args.kwargs["url_template"])

    def test_senate_efd_csv_normalizes_transaction_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "efd.csv"
            path.write_text('senator,date_of_transaction,asset_name,symbol,type_of_transaction,amount,owner\nJane Doe,2026-01-20,Acme Common Stock,ACME,Purchase,"$1,001 - $15,000",SP\n', encoding="utf-8")
            rows = read_senate_efd(path)
            self.assertEqual(rows[0]["transaction_code"], "P")
            self.assertEqual(rows[0]["asset_type"], "ST")
            self.assertEqual(summarize_senate_efd(rows)["trade_count"], 1)


if __name__ == "__main__":
    unittest.main()
