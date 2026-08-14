# Validation log

## Environment check

| Check | Result | Decision / limitation |
|---|---|---|
| Workspace root | PASS | `/Users/tccc/Desktop/AI Invest/Workspace` |
| Canonical Python | PASS | `.venv/bin/python`, Python 3.12.13 |
| Network / SEC HTTPS | PASS | SEC submissions endpoint returned Intel registrant metadata on 2026-08-14 |
| HTTP client | PASS | `/usr/bin/curl` |
| PDF text extraction | PASS / bundled fallback | SEC HTML was primary; bundled PDF runtime was used where layout/page verification mattered |
| PDF page rendering | PASS | bundled `pdftoppm` available |
| Structured data | PASS | `jq` and `.venv` Python available |
| Financial calculator | PASS | Both annual and H1 inputs pass `--include-missing --strict`; regenerated outputs match byte-for-byte |
| Git preservation | PASS | pre-existing dirty worktree recorded; no staging, commit, push, deletion, or overwrite authorized |

## Clean-room boundary

- A unique isolation ID was generated before intake: `INTC-intel-cleanroom-20260814-d0f06ac0`.
- Existing Intel-specific paths disclosed incidentally by `git status --short` were not opened, parsed, copied, compared, or reused.
- All source acquisition and derived outputs for this task stay within the four isolation roots recorded in `research-context.md`.
- No target-company benchmark is selected.

## Acquisition attempts

The complete route-critical acquisition record is in `acquisition-attempt-log.md`. SEC submissions and company facts are preserved and indexed as [S11]. Missing utilization, yield, capacity, maintenance/growth capex, unit/backlog and warranty details were checked across audited, interim, IR/product and independent categories before being classified unavailable.

## Command and validation record

| Check | Command / method | Result |
|---|---|---|
| Annual financial calculation | `calculate_metrics.py ...intc-financials-2023-2025.json --format markdown --include-missing --strict` | PASS; regenerated file exactly matches clean-room output |
| H1 financial calculation | `calculate_metrics.py ...intc-financials-2026-h1.json --format markdown --include-missing --strict` | PASS; regenerated file exactly matches clean-room output |
| DCF recalculation | Standard-library recalculation from `intc-dcf-assumptions.json` with EV/equity assertions | PASS: low/base/high EV and equity values match model |
| JSON parse | `jq empty` on all curated JSON | PASS |
| Source integrity | `shasum -a 256 -c .../SHA256SUMS.txt` | PASS for all 71 acquired files |
| PDF visual review | bundled `pdftoppm`, annual PDF pages 27-38, 66-69, 83-84; all Q2 deck and prepared-remarks pages | PASS; no clipping, overlap, blank pages or illegible tables observed |
| Source IDs / local paths | local resolution check | PASS: 16 unique report source IDs resolved; cited local paths exist |
| Release validator first run | `validate_research_release.py --full-report --strict` | one mechanical failure: acquisition log lacked literal `next` field; header corrected without changing evidence |
| Git whitespace | `git diff --check` | PASS |

## Release decision

The independent gate review is recorded in `release-review.md`. Final status is `PARTIAL` because A2 and C2 are `PARTIAL`; this is an evidence-sufficiency limitation, not a failed calculation or missing supported chapter.
