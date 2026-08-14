# Independent release review

## Review packet and decision

The second-pass review used the draft report, source index, evidence ledger, acquisition-attempt log, coverage matrix, normalized financial inputs, strict metric outputs and DCF packet. No target-company prior report or benchmark was selected. **Release status: PARTIAL.** The weakest mandatory sub-gates are A2 and C2, both `PARTIAL`; the release decision is not better than those gates.

## Gate decisions

| Gate | Status | Review basis |
|---|---|---|
| A1 provenance | PASS | Identity, periods, perimeter, URLs, local paths, locators, access date and SHA-256 manifest are present. |
| A2 evidence sufficiency | PARTIAL | All source categories were covered, but absolute Foundry utilization/yield, node capacity and maintenance capex remain unavailable after exhaustive attempts and can change valuation. |
| B1 economic intelligibility | PASS | A qualified product/wafer cycle is traced from demand and design through WIP, yield/utilization, shipment, receivable and cash, including failure paths. |
| B2 triangulation | PASS | TSMC tests foundry mechanics/scale; AMD and NVIDIA test CPU/AI competition and spend concentration. Intel technology statements remain labeled company claims. |
| C1 segment coverage | PASS | CCPG, DCAI, Foundry, All Other/Mobileye, Altera, corporate/eliminations and SCIP/NCI bridges are covered. |
| C2 economic closure | PARTIAL | The causal cycle closes, but route-critical quantitative yield/utilization and maintenance/growth capex values are missing; honest unavailability does not pass this gate. |
| D1 reconciliation | PASS | Assets equal liabilities plus equity; parent/NCI income reconciles; restricted-cash differences are preserved; annual and H1 calculator runs pass strict mode. |
| D2 analytical coverage | PASS WITH LIMITATION | Statements precede analysis; segment, tax, impairment, working capital, debt and APM bridges are addressed. Warranty roll-forward and lease liabilities are unavailable/non-separate. |
| E1 method/boundary validity | PASS WITH LIMITATION | FCFF DCF fits capital-intensive manufacturing; market price, post-offering shares, NCI and dilution are dated. Lease debt and final offering fees remain incomplete. P/E IRR is correctly rejected. |
| E2 model completeness | PASS WITH LIMITATION | Low/base/high five-year DCF, two-year checkpoints, reverse DCF, dilution, NCI/net-cash and double-count tests are present. Altera is explicitly unmodeled rather than assigned an invented value. |
| R1 coverage/depth | PASS | Every material supported topic has mechanism, quantitative anchor, counterargument/failure path and monitoring. The PARTIAL label was not used to shorten supported sections. |
| R2 benchmark calibration | N.A. | No benchmark was selected; clean-room rules precluded Intel prior research and none was needed. |
| R3 independent review/publishing | PASS | Clean second pass completed; strict financial regeneration, DCF assertions, source/hash/path checks, PDF rendering, release validator and Git whitespace checks pass. |

## Coverage challenges

1. `Foundry internal/external bridge` remains covered for disclosed mechanics and reported segment reconciliation, but does not imply C2 closure; attempts A004-A006 explicitly cap the route at PARTIAL.
2. `Capex split` is correctly unavailable, not covered. Total cash/gross/net capex exists, but no maintenance/growth split was found.
3. `Warranty` is correctly unavailable after filing review. It is a D2 limitation, but available evidence indicates it is less material than fab yield/utilization and does not independently block a bounded DCF.
4. `Altera associate` is unresolved, not silently valued at zero. No value is added to DCF/SOTP; the omission is identified as possible conservatism.
5. The report does not call relative 18A output versus an undisclosed target a quantitative yield measure.
6. The H1 CFO-capex metric is not called recurring FCF and is kept separate from Intel's adjusted FCF bridge.

## Valuation challenge

The DCF is formula-complete but highly terminal-value sensitive. The high case still lies below the market boundary, and reverse DCF exposes the required 2031 FCFF rather than asserting the market is irrational. Consolidated NCI is subtracted; matching escrow derivative liability and shares are not double counted; warrant exercise cash is added only in the relevant dilution case. The model does not claim a target price or recommendation.

## Corrections made in review

- Kept A2 and C2 at PARTIAL despite exhaustive acquisition attempts.
- Required post-offering share count and non-contingent escrow shares in the base denominator.
- Kept issuer adjusted FCF separate from GAAP CFO-capex.
- Added explicit lease, Altera, warranty and final-offering-proceeds limitations.
- Added reverse DCF and quarterly falsification conditions so the valuation is testable.

## Remaining limitations

To upgrade the release, obtain reliable Intel-specific absolute utilization, node yield/capacity and maintenance/growth capex data, then update the DCF and reassess C2/A2. A complete lease-liability bridge, Altera stand-alone value/distribution evidence and final equity-offering net proceeds would improve E1/E2 but do not replace the missing Foundry operating KPIs.
