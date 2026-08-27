#!/usr/bin/env python3
"""Initialize a portable public-company research package.

Only missing files are created. Existing research notes and sources are never
overwritten by this helper.
"""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path


LEDGER_TEMPLATES = {
    "source-index.md": """# Source Index\n\n| Source ID | Category | Title | Content date | Accessed at | Original URL/reference | Local path | SHA-256 | Locator | Usability | Notes |\n|---|---|---|---|---|---|---|---|---|---|---|\n""",
    "evidence-ledger.md": """# Evidence Ledger\n\n| Claim ID | Section | Claim or input | Type | Source IDs | Locators | Period/scope | Value/status | Confidence | Counterevidence | Implication | Monitoring KPI | Attempt ID |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|\n""",
    "acquisition-attempt-log.md": """# Acquisition Attempt Log\n\n| Attempt ID | Research question | Criticality | Source category | Query/page | Accessed at | Result | Selected source ID | Rejection/failure | Next step |\n|---|---|---|---|---|---|---|---|---|---|---|---|\n""",
    "coverage-matrix.md": """# Coverage Matrix\n\n| Item | Route | Evidence IDs | Analysis section | Mechanism | Quantitative anchor | Counterargument/failure | Monitoring KPI | Attempt ID | Gap consequence | Status |\n|---|---|---|---|---|---|---|---|---|---|---|\n""",
    "validation-log.md": """# Validation Log\n\n- Package initialized; record tool checks, recovery actions, calculations, and validator results here.\n""",
    "release-review.md": """# Release Review\n\n- Status: `PENDING`\n- Record a clean second-pass review for gates A1-E2 and R1-R3 before release.\n""",
}


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    if not value:
        raise ValueError("slug/ticker must contain at least one ASCII letter or digit")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, default=Path("."))
    parser.add_argument("--issuer", required=True)
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--market", required=True)
    parser.add_argument("--slug", help="Optional stable ASCII slug; defaults to issuer")
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument("--fiscal-year-end", default="unknown")
    parser.add_argument("--history-start", default="")
    parser.add_argument("--history-end", default="")
    parser.add_argument("--latest-interim", default="unknown")
    parser.add_argument("--language", default="en")
    return parser.parse_args()


def write_if_missing(path: Path, text: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    args = parse_args()
    market = slugify(args.market).upper()
    ticker = slugify(args.ticker).upper()
    slug = slugify(args.slug or args.issuer)
    company_id = f"{ticker}-{slug}"
    root = args.workspace_root.resolve()
    research_dir = root / "research" / "companies" / market / company_id
    sources_dir = root / "sources" / "companies" / market / company_id
    curated_dir = root / "data" / "curated" / "companies" / market / company_id
    derived_dir = root / "data" / "derived" / "companies" / market / company_id
    research_data_dir = research_dir / "data"

    for directory in (research_dir, research_data_dir, sources_dir, curated_dir, derived_dir):
        directory.mkdir(parents=True, exist_ok=True)

    context = f"""# Research Context\n\n- Status: `INITIALIZED`\n- Issuer: {args.issuer}\n- Ticker: `{args.ticker}`\n- Market: `{args.market}`\n- Research as-of date: {args.as_of}\n- Fiscal year end: {args.fiscal_year_end}\n- Historical window: {args.history_start or 'to be confirmed'} to {args.history_end or 'to be confirmed'}\n- Latest interim: {args.latest_interim}\n- Report language: {args.language}\n- Research directory: `{research_dir.relative_to(root)}`\n- Sources directory: `{sources_dir.relative_to(root)}`\n- Curated data directory: `{curated_dir.relative_to(root)}`\n- Derived data directory: `{derived_dir.relative_to(root)}`\n\n## Scope decisions\n\n- Accounting basis, consolidation perimeter, share class, currency, units, legal entity, and fiscal comparability: to be verified from authoritative filings.\n- Reference reports, if supplied, may inform method and evidence organization only; target-company facts, assumptions, numbers, and conclusions must be independently sourced.\n- Record all optional dependency checks and limitations in `validation-log.md`.\n"""
    created: list[Path] = []
    if write_if_missing(research_data_dir / "research-context.md", context):
        created.append(research_data_dir / "research-context.md")
    for name, template in LEDGER_TEMPLATES.items():
        if write_if_missing(research_data_dir / name, template):
            created.append(research_data_dir / name)

    print(f"Initialized {company_id}")
    print(f"research: {research_dir.relative_to(root)}")
    print(f"research data: {research_data_dir.relative_to(root)}")
    print(f"sources: {sources_dir.relative_to(root)}")
    print(f"curated: {curated_dir.relative_to(root)}")
    print(f"derived: {derived_dir.relative_to(root)}")
    print(f"created_files: {len(created)}")
    if created:
        for path in created:
            print(f"  + {path.relative_to(root)}")
    else:
        print("No files created; existing package preserved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
