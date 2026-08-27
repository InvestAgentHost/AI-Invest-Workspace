# Evidence, Claims, and Ledgers

## 1. Claim taxonomy

Use explicit labels in notes and prose:

| Label | Meaning | Required support |
|---|---|---|
| `FACT` | Directly reported or independently observed | Source ID and locator. |
| `COMPANY_CLAIM` | Management, IR, or website assertion | Source ID, attribution, and corroboration status. |
| `CALC` | Arithmetic derived from sourced inputs | Formula, input IDs, units, and period. |
| `JUDGMENT` | Analyst interpretation of persistence, quality, or risk | Evidence, counterargument, and monitoring KPI. |
| `ASSUMPTION` | Model choice not directly disclosed | Rationale, range/scenario, and sensitivity. |
| `UNRESOLVED` | Contradiction or missing evidence that could change the view | Competing sources or acquisition attempts and consequence. |

Do not convert a company claim into a fact by repeating it. Do not present a calculation as a reported figure. Do not bury an assumption in narrative.

## 2. Evidence ledger schema

Use one row per material claim or model input:

```text
claim_id | section | claim_or_input | type | source_ids | locators |
period | scope | value_or_status | confidence | counterevidence |
analysis_implication | monitoring_kpi | unresolved_or_attempt_id
```

For calculations, `source_ids` point to all inputs and `value_or_status` contains the formula output. For a missing KPI, set status to `unavailable`, cite the acquisition attempts, and explain how the gap affects operations or valuation.

## 3. Coverage matrix

Cover every material segment, legal entity, product/revenue type, statement exposure, capital action, strategic claim, risk, and valuation component:

```text
item | route | evidence_ids | analysis_section | mechanism |
quant_anchor | counterargument_or_failure | monitoring_kpi |
attempt_id | gap_consequence | status
```

`covered` requires a mechanism, quantitative anchor where available, counterargument or failure path, and monitoring KPI. `unavailable` means relevant but not disclosed after the required searches. `unresolved` means contradictory or not yet adjudicated.

## 4. Citation style

Use inline citations such as `[S012]`, `[S012 p.47]`, `[T0042]`, and `[calc:fcf-margin-2025]`. Keep the source index authoritative. A local path without a source ID is not sufficient; a source ID without a resolvable path or URL is incomplete.

## 5. Contradiction handling

When sources disagree:

1. Preserve both statements and dates.
2. Prefer audited statutory data for reported amounts and official filings for legal boundaries.
3. Use later restated comparatives where the filing explicitly restates them, while preserving the originally reported value in a reconciliation note.
4. Treat management guidance as a claim, not as a realized result.
5. State the adjudication or leave the item `unresolved`; never silently choose the convenient figure.
