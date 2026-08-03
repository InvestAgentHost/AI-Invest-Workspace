from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.sec_8k_mna.core import (
    Classification,
    FilingMetadata,
    RuntimeConfig,
    archive_relevant,
    classification_system_prompt,
    filing_is_candidate,
    normalize_classification,
    report_markdown,
    run_daily,
    split_submission_documents,
)
from tools.sec_8k_mna.cli import public_result


def filing(items: str = "1.01") -> FilingMetadata:
    return FilingMetadata(
        ticker="TEST",
        cik="0000123456",
        company_name="Test Corporation",
        accession_number="0000123456-26-000001",
        filing_date="2026-07-28",
        acceptance_datetime="20260728150000",
        form="8-K",
        items=items,
        primary_document="form8k.htm",
        primary_description="Entry into a Material Definitive Agreement",
    )


class CoreTests(unittest.TestCase):
    def runtime_config(self, root: Path) -> RuntimeConfig:
        watchlist = root / "watchlist.txt"
        watchlist.write_text("TEST\n", encoding="utf-8")
        return RuntimeConfig(
            workspace_root=root,
            watchlist_path=watchlist,
            sources_root=root / "sources",
            knowledge_root=root / "knowledge",
            report_root=root / "research",
            state_path=root / "knowledge" / "state.json",
            classifications_root=root / "knowledge" / "classifications",
            logs_root=root / "logs",
            temp_root=root / ".cache",
            sec_user_agent="AI-Invest-Test/1.0 test@example.com",
            provider="deepseek",
            model="test-model",
            api_key="not-used",
            base_url="https://example.invalid",
        )

    def test_item_and_keyword_candidates(self) -> None:
        self.assertTrue(filing("1.01,9.01").items)
        self.assertTrue(filing_is_candidate(filing("1.01,9.01")))
        keyword_filing = filing("5.02")
        keyword_filing.primary_description = "Agreement and Plan of Merger"
        self.assertTrue(filing_is_candidate(keyword_filing))
        ordinary_filing = filing("5.02")
        ordinary_filing.primary_description = "Director appointment"
        self.assertFalse(filing_is_candidate(ordinary_filing))

    def test_split_submission_documents(self) -> None:
        raw = """<SEC-DOCUMENT>\n<DOCUMENT>\n<TYPE>8-K\n<FILENAME>form8k.htm\n<TEXT><html><body><p>Merger agreement</p></body></html>\n</DOCUMENT>\n<DOCUMENT>\n<TYPE>EX-2.1\n<FILENAME>merger.htm\n<TEXT><html><body>Agreement and Plan of Merger</body></html>\n</DOCUMENT>"""
        documents = split_submission_documents(raw)
        self.assertEqual([item[0] for item in documents], ["8-K", "EX-2.1"])

    def test_high_confidence_requires_evidence(self) -> None:
        classified = normalize_classification(
            {
                "is_relevant": True,
                "review_status": "high_confidence",
                "category": ["m_and_a"],
                "confidence": 0.95,
                "evidence": [],
            },
            filing(),
            "deepseek",
            "test-model",
        )
        self.assertEqual(classified.review_status, "not_relevant")
        self.assertFalse(classified.archive_allowed)

    def test_classification_prompt_requests_chinese_reporting(self) -> None:
        prompt = classification_system_prompt()
        self.assertIn("Simplified Chinese", prompt)
        self.assertIn("evidence.quote", prompt)

    def test_public_result_omits_local_paths(self) -> None:
        result = public_result({"report_path": "/private/report.md", "events": [{"source_path": "/private/source.md", "ticker": "TEST"}]})
        self.assertEqual(result, {"events": [{"ticker": "TEST"}]})

    def test_archive_only_accepts_high_confidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = self.runtime_config(root)
            classification = Classification(
                is_relevant=True,
                review_status="high_confidence",
                category=["m_and_a"],
                transaction_type="merger",
                status="announced",
                company="Test Corporation",
                counterparties=["Target Corporation"],
                target_or_asset="Target Corporation",
                consideration={},
                sec_items=["1.01"],
                effective_date=None,
                evidence=[{"quote": "signed a merger agreement", "section": "Item 1.01", "source_url": filing().filing_url}],
                confidence=0.95,
                uncertainties=[],
                provider="deepseek",
                model="test-model",
            )
            raw_path, markdown_path, digest = archive_relevant(
                config,
                filing(),
                "<SEC-DOCUMENT>raw</SEC-DOCUMENT>",
                [{"type": "8-K", "filename": "form8k.htm", "text": "signed a merger agreement"}],
                classification,
            )
            self.assertTrue(raw_path.is_file())
            self.assertTrue(markdown_path.is_file())
            self.assertEqual(len(digest), 64)
            self.assertIn("signed a merger agreement", markdown_path.read_text(encoding="utf-8"))

    def test_daily_run_archives_only_relevant_filing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = self.runtime_config(root)
            relevant = Classification(
                is_relevant=True,
                review_status="high_confidence",
                category=["m_and_a"],
                transaction_type="merger",
                status="announced",
                company="Test Corporation",
                counterparties=["Target Corporation"],
                target_or_asset="Target Corporation",
                consideration={"summary": "cash"},
                sec_items=["1.01"],
                effective_date=None,
                evidence=[{"quote": "signed a merger agreement", "section": "Item 1.01", "source_url": filing().filing_url}],
                confidence=0.95,
                uncertainties=[],
                provider="deepseek",
                model="test-model",
            )
            with patch("tools.sec_8k_mna.core.company_ticker_map", return_value={"TEST": {"cik": filing().cik, "company_name": filing().company_name}}), \
                 patch("tools.sec_8k_mna.core.recent_filings_for_company", return_value=[filing()]), \
                 patch("tools.sec_8k_mna.core.fetch_candidate_documents", return_value=("<SEC-DOCUMENT>raw</SEC-DOCUMENT>", [{"type": "8-K", "filename": "form8k.htm", "text": "signed a merger agreement"}])), \
                 patch("tools.sec_8k_mna.core.call_provider", return_value=relevant):
                result = run_daily(config, lookback_hours=36, dry_run=False, retry_failed=False)
                repeated = run_daily(config, lookback_hours=36, dry_run=False, retry_failed=False)
            self.assertEqual(result["summary"]["archived"], 1)
            self.assertTrue(
                (root / "sources" / "providers" / "sec" / "8-k" / "TEST").is_dir()
            )
            self.assertTrue(Path(result["report_path"]).is_file())
            self.assertEqual(repeated["summary"]["candidates"], 0)
            self.assertEqual(len(repeated["events"]), 1)
            self.assertEqual(repeated["events"][0]["filing"]["ticker"], "TEST")

    def test_daily_run_does_not_archive_irrelevant_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = self.runtime_config(root)
            irrelevant = Classification(
                is_relevant=False,
                review_status="not_relevant",
                category=[],
                transaction_type="",
                status="uncertain",
                company="Test Corporation",
                counterparties=[],
                target_or_asset="",
                consideration={},
                sec_items=[],
                effective_date=None,
                evidence=[],
                confidence=0.99,
                uncertainties=[],
                provider="deepseek",
                model="test-model",
            )
            with patch("tools.sec_8k_mna.core.company_ticker_map", return_value={"TEST": {"cik": filing().cik, "company_name": filing().company_name}}), \
                 patch("tools.sec_8k_mna.core.recent_filings_for_company", return_value=[filing()]), \
                 patch("tools.sec_8k_mna.core.fetch_candidate_documents", return_value=("<SEC-DOCUMENT>raw</SEC-DOCUMENT>", [{"type": "8-K", "filename": "form8k.htm", "text": "unrelated"}])), \
                 patch("tools.sec_8k_mna.core.call_provider", return_value=irrelevant):
                result = run_daily(config, lookback_hours=36, dry_run=False, retry_failed=False)
            self.assertEqual(result["summary"]["archived"], 0)
            self.assertFalse((root / "sources" / "sec" / "8-k").exists())

    def test_daily_run_accession_filter_avoids_other_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = self.runtime_config(root)
            with patch("tools.sec_8k_mna.core.company_ticker_map", return_value={"TEST": {"cik": filing().cik, "company_name": filing().company_name}}), \
                 patch("tools.sec_8k_mna.core.recent_filings_for_company", return_value=[filing()]), \
                 patch("tools.sec_8k_mna.core.call_provider") as classify:
                result = run_daily(
                    config,
                    lookback_hours=36,
                    dry_run=False,
                    retry_failed=False,
                    accessions=["0000123456-26-999999"],
                )
            self.assertEqual(result["summary"]["candidates"], 0)
            classify.assert_not_called()

    def test_report_separates_review_events(self) -> None:
        metadata = filing().as_dict()
        metadata["filing_url"] = filing().filing_url
        event = {
            "filing": metadata,
            "classification": {
                "review_status": "needs_review",
                "transaction_type": "asset_sale",
                "status": "uncertain",
                "category": ["divestiture"],
                "counterparties": [],
                "target_or_asset": "",
                "confidence": 0.6,
                "evidence": [{"quote": "may sell assets"}],
                "uncertainties": ["transaction status"],
                "consideration": {},
            },
            "source_path": "/private/example/filing.md",
        }
        report = report_markdown(
            "2026-07-28",
            {"tickers": 1, "window": "test", "filings": 1, "candidates": 1, "analyzed": 1, "archived": 0, "needs_review": 1, "failures": 0},
            [event],
        )
        self.assertIn("待人工复核事项", report)
        self.assertIn("asset_sale", report)
        self.assertNotIn("本地来源", report)
        self.assertNotIn("/private/example/filing.md", report)


if __name__ == "__main__":
    unittest.main()
