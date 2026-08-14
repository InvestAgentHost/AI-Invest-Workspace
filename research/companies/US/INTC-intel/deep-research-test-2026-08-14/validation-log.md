# Validation log

## 2026-08-14 initial environment and isolation check

- Research root, report target, source root, curated-data target, and derived-data target were tested with `test -e`; all requested targets were free before creation.
- Existing `research/companies/US/INTC-intel/`, `sources/companies/US/INTC-intel/`, and Intel-specific data may exist, but their contents were not opened, listed, searched, summarized, copied, or modified.
- Isolation mechanism: all new work uses the exact `deep-research-test-2026-08-14` namespace. No fallback to old Intel materials is permitted.
- `curl`, `jq`, Node.js, `pdftoppm`, and the Workspace `.venv` path check were attempted. `pdftotext` was not found; HTML/XBRL plus Python parsing will be preferred, with PDF rendering if a PDF table requires layout verification.
- Repository rules and all references required by `company-investment-research`, `financial-statement-analysis`, and `valuation-binding-methodology` were read before intake/calculation/valuation.
- Git policy: do not stage, commit, or push.

## Gate status at initialization

- Gate A evidence ready: FAIL (intake not started)
- Gate B industry intelligible: FAIL (routing not yet evidenced)
- Gate C operating model coherent: FAIL
- Gate D statements reconcile: FAIL
- Gate E valuation bound: FAIL

## Evidence intake and analysis

- Newly acquired SEC company ticker inventory, submissions, company facts, 2025 10-K, Q2 2026 10-Q, Q2 earnings 8-K/release, 2026 proxy, 2026-08-12 equity-offering 8-K, and Nasdaq quote JSON.
- All acquired source files are contained under `sources/companies/US/INTC-intel/deep-research-test-2026-08-14/`; SHA-256 values are recorded in `source-index.md`.
- HTML/XBRL was inspected through SEC inline facts, `xmllint` table/body extraction, and SEC company facts. `textutil` HTML conversion failed because the helper application was unavailable; no derived text snapshot was treated as evidence.
- The repository `.venv` is absent. The repository calculator was run with `/usr/bin/python3` in strict mode. This is a runtime-policy deviation, not a formula substitution.
- The annual normalized input is `data/curated/companies/US/INTC-intel-deep-research-test-2026-08-14.json`; strict output is `data/derived/companies/US/INTC-intel-deep-research-test-2026-08-14-metrics.md`.
- FY2023-FY2025 assets = liabilities + equity and consolidated income = parent + NCI all passed with zero difference.
- H1 2026 manual checks passed: assets 202,439 = calculated liabilities 99,296 + equity 103,143; consolidated loss (15,129) = parent loss (14,761) + NCI loss (368); CFO 8,102 + CFI (669) + CFF (8,548) = cash decrease (1,115); segment revenue and operating income bridge to 29,705 and (1,340).
- Valuation method decision: SOTP/DCF preferred, P/E/IRR invalid because normalized positive parent earnings are unavailable. Absolute value remains pending.

## Gate status after analysis

- Gate A evidence ready: PASS
- Gate B industry intelligible: PASS with limitation (issuer evidence only; no independent market-share dataset)
- Gate C operating model coherent: PASS
- Gate D statements reconcile: PASS
- Gate E valuation bound: PARTIAL

## Final publishing checks

- `python3 -m json.tool` passed for the curated financial input and Nasdaq market JSON.
- The repository financial calculator was rerun with `--strict --include-missing`; output matched the saved derived metrics byte-for-byte.
- All `[Sxx]` identifiers used across the report and work records resolve to `source-index.md`; no undefined IDs were found.
- All 21 repository-relative `sources/`, `research/`, and `data/` paths cited in the report/work records exist.
- Markdown fence balance and table pipe-count checks passed for the report and every auxiliary Markdown file.
- Pandoc rendered the report from GFM to standalone HTML in `/tmp`; `xmllint` parsed it without errors. Render contained 11 H2 headings and 15 tables and no Unicode replacement characters. Temporary render was not retained as a research artifact.
- `git diff --check` passed. `git diff --no-index --check` passed for every new tracked candidate, including the untracked report, work records, and curated JSON.
- Git HEAD at handoff: `93f812965f2b7001c91ff61da7f1bef62938d770`. `git diff --cached --name-only` was empty. Work remains unstaged and uncommitted; no push was performed.

## Final status

- Report: PARTIAL because Gate E remains PARTIAL.
- Gates A, C and D: PASS. Gate B: PASS with the stated independent-industry-evidence limitation.
- Existing Intel material was not read or modified. Evidence acquisition and all analysis stayed inside the `deep-research-test-2026-08-14` namespace plus newly named structured-data files.

## Main Workspace synchronization

- User requested synchronization to `/Users/tccc/Desktop/AI Invest/Workspace` while preserving independence from prior Intel work.
- Before synchronization, only the five exact destination targets were checked with `test -e`; all were free. No pre-existing Intel file or directory contents were opened, enumerated, searched, or used.
- Synchronization scope is limited to the isolated report, isolated work-record directory, isolated raw-source directory, and the two structured-data files carrying the `deep-research-test-2026-08-14` identifier.
- The operation is additive only: no overwrite, merge into an old Intel subdirectory, deletion, or movement of existing Intel material is permitted.
