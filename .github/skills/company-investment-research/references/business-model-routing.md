# Business-Model Routing

Use this file after the initial source inventory and before detailed industry or company analysis. The archetypes are heuristics, not mutually exclusive labels. Route each material segment separately, then add a group-level bridge for mixed businesses.

## 1. Routing questions

Answer these questions from filings and operating disclosures:

1. What is the economic unit that repeats or changes hands: customer contract, transaction, product/batch, project, site/asset, loan, policy, resource unit, drug candidate, property, or security?
2. What event creates revenue: activation, usage, shipment, acceptance, subscription period, origination, premium/service period, production/sale, milestone, rent, dividend, interest, or fair-value movement?
3. What must be funded before cash returns: CAC/contract costs, inventory, factory, construction, site, loan principal, reserves, R&D, land/property, or securities?
4. Which variable most changes value: price, volume, mix, utilization, retention, backlog, spread, credit/claims, probability of success, reserves/grade, NAV, or capital allocation?
5. Where can the model fail: churn, pricing pressure, defect, cost inflation, delay/overrun, default, claims, regulatory loss, commodity cycle, clinical failure, refinancing, dilution, or asset discount?

Select one primary archetype and any secondary archetypes. Do not let a familiar archetype override the evidence.

## 2. Archetype matrix

| Archetype | Economic unit / anchor | Primary value drivers | Balance-sheet and cash focus | Typical valuation lenses |
|---|---|---|---|---|
| Recurring / contracted service | contract, site, subscriber, usage account | retention, price/escalator, utilization, service cost | contract costs, receivables, maintenance capex, cash conversion | DCF/FCF, EV/EBITDA, sum-of-parts |
| Transaction / distribution | transaction, lead, shipment, commission event | volume, conversion, take rate, CAC, repeat rate | working capital, refunds, commissions, inventory | EV/sales, EV/EBIT, normalized FCF |
| Manufacturing / hardware | product, batch, installed base | volume, price, mix, yield, utilization, unit cost | inventory, receivables, PP&E, capex, warranty | EV/EBIT, EV/EBITDA, DCF |
| Project / engineering | awarded project or milestone | backlog, win rate, progress, margin, change orders | contract assets/liabilities, WIP, retention cash, guarantees | DCF, EV/EBIT, backlog cross-check |
| Software / platform / marketplace | seat, account, transaction, ecosystem | ARR/usage, retention, gross margin, CAC, take rate, network density | deferred revenue, capitalized development, working capital | EV/revenue, EV/FCF, DCF |
| Asset-heavy infrastructure / utility | site, capacity unit, regulated asset | availability, utilization, tariff, escalation, capex, leverage | PP&E, leases, debt, maintenance/growth capex, pass-through | DCF, EV/EBITDAaL, NAV |
| Lender / consumer finance | loan, vintage, borrower | loan growth, yield/spread, credit loss, funding, efficiency | loan book, ECL, liquidity, regulatory capital | P/E, P/B, residual income |
| Insurer | policy, cohort, claim | premium/service result, renewal, loss/combined ratio, investment yield | reserves, CSM, solvency, asset-liability matching | P/E, P/B, embedded value / SOTP |
| Resource / commodity | reserve, tonne, barrel, MWh, production unit | grade, volume, recovery, realized price, cost curve | reserves, inventory, sustaining/growth capex, reclamation | NAV, cycle-normalized FCF, EV/EBITDA |
| Pharma / biotech | candidate, indication, trial, milestone | probability of success, market access, price, launch timing | R&D, cash runway, intangibles, milestone obligations | rNPV, DCF, SOTP |
| Real estate / REIT | property, rentable area, lease | occupancy, rent, leasing spread, cap rate, development | property value, debt, LTV, capex, tenant deposits | NAV, FFO/AFFO, DCF |
| Investment holding / conglomerate | security, associate, fund, asset pool | NAV growth, distributions, realizations, allocation skill | securities, cash, debt, latent tax, holding costs | NAV/SOTP, look-through only as bridge |

## 3. Required route record

Add this table to `scope.yaml` or `segment-operating-units.md`:

| Field | Required content |
|---|---|
| Segment | reported segment or legal business |
| Primary archetype | one label from the matrix |
| Secondary archetypes | optional |
| Economic unit | what repeats, scales or changes hands |
| Value driver | most decision-useful operating variable |
| Cash/balance-sheet anchor | item that grows when the business grows |
| Risk carrier | entity or stakeholder bearing the downside |
| Preferred metrics | metrics to calculate or mark unavailable |
| Preferred valuation | method and why it fits |
| Excluded modules | modules intentionally not applied and reason |

## 4. Route-specific explanatory spine

- For recurring, transaction, software and distribution businesses, use the customer-event/channel/contract/cash path when the evidence supports it.
- For manufacturing and resources, use input -> production -> inventory -> shipment -> cash, with capacity, yield, cost curve and cycle analysis.
- For projects and real estate, use award/lease -> construction or occupancy -> progress/rent -> completion/renewal -> cash, with obligations and refinancing.
- For lenders and insurers, use origination/underwriting -> servicing/claims -> funding/reserves -> loss realization -> capital return; do not force revenue/CAC language where it obscures risk.
- For pharma/biotech, use discovery -> trial -> regulatory decision -> launch/royalty -> lifecycle, with probability-weighted milestones and runway.
- For investment holdings, use capital source -> asset purchase -> distributions/realizations/mark-to-market -> taxes and holding costs -> shareholder value.

## 5. Anti-overfitting rules

- The archetype is a routing hypothesis, not a conclusion. Reclassify if segment evidence contradicts it.
- Do not force every company to have a particular customer relationship, recurring revenue, CAC, cohort, moat, SOTP or IRR. Select only concepts that the evidence makes economically relevant.
- Do not force industry demand/supply into separate chapters when the company's value is primarily determined by reserves, credit underwriting, regulation, production constraints, clinical probabilities or asset NAV. Preserve the concepts, adapt the order.
- Mark fields `n.a.` when economically irrelevant and `unavailable` when relevant but undisclosed. These states must not be silently converted into zeros or assumptions.
