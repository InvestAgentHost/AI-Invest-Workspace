# Workflow and Phase Gates

## 1. Start with a bounded brief

Capture the following in `research-context.md` before collecting evidence:

| Field | Rule |
|---|---|
| Issuer and legal entity | Use the filing cover page and legal name; resolve parent versus subsidiaries. |
| Security | Ticker, exchange, share class, CIK, currency, and dated price boundary only when valuation is requested. |
| Reporting basis | Fiscal year end, US GAAP/IFRS, consolidated perimeter, continuing/discontinued operations, units, and restatement policy. |
| Time scope | Default to five audited fiscal years plus the latest 10-Q and relevant current events. Record the as-of date. |
| Decision question | State what could change the investment view; do not begin with a target price. |
| Output boundary | Report path, sources path, structured-data path, language, and whether a `PARTIAL` result is acceptable. |
| Terminal dependencies | Python 3.12+, bundled runtime dependencies, browser/network access, Workspace financial calculator, and any valuation tools selected by the user. |

If a reference report is supplied, record it as a methodology-only benchmark. It may influence sequence and evidence discipline but never target-company facts, assumptions, metrics, or valuation.

## 2. Phase sequence

Use a small checkpoint after each phase. A phase may be `complete`, `partial`, `blocked`, or `not_applicable`; never claim completion because a command ran.

1. **Identity and scope:** boundary fields and research questions accepted; initial ledgers created.
2. **Acquisition:** primary source set and attempts recorded; originals preserved; preparation artifacts inspected.
3. **Routing:** every material segment and revenue type has a selected archetype or an explicit unresolved route.
4. **Analysis:** industry mechanism and segment economics close through revenue, cost, capital, cash, and failure path.
5. **Fundamentals:** reported statements, mappings, reconciliations, and derived tables are available or honestly marked unavailable.
6. **Valuation:** method, boundary, assumptions, scenarios, sensitivities, and shareholder-return convention are explicit.
7. **Release:** report, source index, validation log, and clean review pass all mandatory checks or are downgraded to `PARTIAL`.

## 3. Confirmation and recovery

Ask for confirmation before:

- using an ambiguous source or event date;
- accessing a private provider or authenticated endpoint;
- overwriting a published artifact or changing a research boundary;
- adopting a materially different valuation method or share-count boundary.

Automatically retry transient network failures, inspect candidate files, rebuild run-local intermediates, and rerun validators. Record each recovery in `acquisition-attempt-log.md` or `validation-log.md`. Do not silently discard a failed source or replace it with a search snippet.

## 4. Minimum evidence packet

Before drafting conclusions, assemble the latest authoritative consolidated filing, five-year comparatives, relevant notes, segment disclosures, APM reconciliations, debt/lease/tax/impairment information, current IR guidance or Q&A, and sources for every route-critical unknown. If a category is irrelevant, mark `n.a.`; if relevant but not disclosed, check the required source categories and mark `unavailable` with an attempt ID.

## 5. Handoff

At the end of each phase, state:

- files created or updated;
- source IDs and locators added;
- calculations or validators run and their results;
- unresolved questions and the next evidence needed;
- whether the phase is complete or downgraded.
