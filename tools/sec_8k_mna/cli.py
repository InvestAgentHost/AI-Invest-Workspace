"""Command-line entry point for the SEC 8-K merger and restructuring workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from tools.sec_8k_mna.core import (
    WorkflowError,
    company_ticker_map,
    load_runtime_config,
    read_watchlist,
    recent_filings_for_company,
    filing_is_candidate,
    run_daily,
    validate_sec_config,
)
from datetime import datetime, timedelta, timezone


def public_result(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: public_result(item)
            for key, item in value.items()
            if key not in {"report_path", "source_path"}
        }
    if isinstance(value, list):
        return [public_result(item) for item in value]
    return value


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--config", type=Path, help="Optional non-secret JSON configuration.")
    result.add_argument("--dotenv", type=Path, help="Optional local .env path. Defaults to workspace .env.")
    result.add_argument("--provider", choices=("deepseek", "aigocode"), help="Override LLM_PROVIDER.")
    result.add_argument("--watchlist", type=Path, help="Override the default ticker watchlist path.")
    commands = result.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("daily", "Fetch metadata, classify candidates, archive relevant filings, and write a daily report."),
        ("candidates", "List metadata-derived candidates without fetching filing text or calling an LLM."),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--lookback-hours", type=int, default=36)
        command.add_argument(
            "--accession",
            action="append",
            default=[],
            help="Restrict the run to an exact SEC accession number. Repeatable.",
        )
        if name == "daily":
            command.add_argument("--dry-run", action="store_true", help="List candidates only; make no writes or LLM calls.")
            command.add_argument("--retry-failed", action="store_true", help="Retry accessions marked analysis_failed.")
            command.add_argument("--reclassify", action="store_true", help="Reclassify specified accessions, including completed filings.")
    return result


def main() -> int:
    args = parser().parse_args()
    workspace = Path.cwd().resolve()
    try:
        config = load_runtime_config(workspace, args.config, args.dotenv, args.provider, args.watchlist)
        if args.command == "daily":
            if args.reclassify and not args.accession:
                raise WorkflowError("--reclassify requires at least one --accession")
            result = run_daily(config, args.lookback_hours, args.dry_run, args.retry_failed, args.accession, args.reclassify)
        else:
            validate_sec_config(config)
            cutoff = datetime.now(timezone.utc) - timedelta(hours=args.lookback_hours)
            mappings = company_ticker_map(config)
            candidates = []
            failures = []
            for ticker in read_watchlist(config.watchlist_path):
                mapped = mappings.get(ticker)
                if not mapped:
                    failures.append(f"{ticker}: CIK mapping not found")
                    continue
                try:
                    filings = recent_filings_for_company(config, ticker, mapped["cik"], mapped["company_name"], cutoff)
                    candidates.extend(
                        filing.as_dict()
                        for filing in filings
                        if filing_is_candidate(filing) and (not args.accession or filing.accession_number in args.accession)
                    )
                except WorkflowError as error:
                    failures.append(f"{ticker}: {error}")
            result = {"candidates": candidates, "failures": failures}
        print(json.dumps(public_result(result), ensure_ascii=False, indent=2))
        return 1 if result.get("failures") else 0
    except WorkflowError as error:
        print(f"sec-8k-mna: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
