# Acquisition attempt log

| ID | Research question | Categories checked | Result | Next step / consequence |
|---|---|---|---|---|
| A001 | Identity, ticker, reporting perimeter | SEC submissions, 10-K, Nasdaq | resolved [S01][S11][S12] | continue |
| A002 | Audited financial statements and opening stocks | 2025 10-K/annual report, 2024 10-K comparative | resolved [S01][S02] | strict normalized input built |
| A003 | Latest interim and subsequent events | Q1/Q2 10-Q, earnings release/deck/remarks, Aug.12 8-K | resolved [S03]-[S09] | valuation dated after offering |
| A004 | Quantitative Foundry utilization | 2025 10-K, Q1/Q2 10-Q, Q2 release/deck/remarks, Intel Foundry/18A page, TSMC 20-F | no Intel percentage disclosed | `unavailable`; C2 and A2 cannot be stronger than PARTIAL for this route-critical KPI |
| A005 | Quantitative 18A/14A yield | same audited/interim/IR/product categories plus competitor filing | Intel states yields improved but no absolute yield | `unavailable`; widen margin/capex scenarios |
| A006 | Wafer starts and capacity by Intel node | audited/interim, IR, product page, independent foundry filing | no comparable Intel node-level capacity series | `unavailable`; no fabricated market-share/capacity claim |
| A007 | Maintenance versus growth capex | cash-flow statements, capex/APM reconciliation, SCIP notes, Q2 remarks | total/gross/net capex available; maintenance split absent | `unavailable`; DCF uses explicit scenario assumptions |
| A008 | Product unit shipments, backlog and customer commitments | 10-K, 10-Q, IR deck/remarks, competitor filings | some demand commentary and design counts, no complete shipment/backlog series | `unavailable`; revenue modeled top-down with wider range |
| A009 | Warranty reserves | audited and interim notes, risk disclosures, keyword search | no decision-useful standalone warranty roll-forward found | `unavailable`; likely non-critical relative to fab economics, D2 limitation |
| A010 | Current market price and share class | Nasdaq API and Yahoo chart | matched at $104.56 Aug.13 close [S12][S13] | resolved |
| A011 | Post-offering diluted share count | 8-K/exhibits, Q2 10-Q, government-equity note | issued shares and escrow/warrant terms resolved; future contingent release unresolved [S03][S09] | scenario-test 71m + 241m |
| A012 | Industry fixed-cost/utilization mechanism | TSMC 20-F and Intel filings/remarks | independently triangulated [S03][S07][S14] | resolved mechanism, Intel magnitude unavailable |
| A013 | CPU/AI competition and spend concentration | AMD 10-K/Q2 10-Q, NVIDIA 10-K | independently triangulated [S15]-[S17] | resolved competitive direction |
| A014 | Mobileye impairment and subsidiary boundary | Intel Q2 10-Q and Mobileye Q2 10-Q | impairment and NCI perimeter resolved [S03][S18] | valuation subtracts total NCI proxy |

## Stop decisions

For A004-A009 the relevant audited, latest interim, official results/remarks, product/technology and independent categories were checked. No untried primary path reasonably promised a public quantitative series by the as-of date. These are honest disclosure gaps, not zeros; A004-A007 materially reduce confidence in foundry normalization and therefore cap the full-report release at `PARTIAL` even though a bounded valuation can be produced.
