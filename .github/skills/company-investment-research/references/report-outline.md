# Adaptive Report Outline and Quality Checklist

## 1. Architecture principle

Use a two-layer structure:

1. **Universal spine**: identity and reporting boundary; industry/economic context; business model and operating units; financial statements and accounting bridge; capital allocation/governance/risk; valuation; evidence gaps; balanced synthesis; source index.
2. **Route modules**: insert only the modules selected in `business-model-routing.md`, in the order that explains the company's economics. Do not create empty chapters to satisfy a fixed template.

The first chapter must be introductory and begin with one sentence explaining what kind of company this is. It should not lead with a valuation conclusion. Industry demand/supply should precede detailed company conclusions when they clarify the business; for a resource, lender, insurer, property, pipeline or asset-value company, the relevant production/risk/development/NAV context may come before or replace a generic demand/supply chapter.

## 2. Universal spine

### 1. Company identity and boundary

Legal entity, ticker/market/share class, history, ownership, subsidiaries, reporting segments, geography, accounting perimeter, one-sentence company summary and reading path.

### 2. Economic context and competitive structure

Explain the relevant customer, asset, production, credit, regulatory, pipeline or portfolio context. Cover demand, supply, bottlenecks, substitutes, industry economics and cycle position only to the degree material to the company.

### 3. Business model and operating map

For each material segment show the routed archetype, economic unit, value driver, revenue recognition, cost stack, capital occupation, risk carrier, cash timing and verification KPI. For groups, explain shared capabilities and non-transferable boundaries.

### 4. Fundamental statements and accounting bridge

Show audited consolidated balance sheet, income statement and cash-flow statement in reported order, then segment reconciliation, accounting policies, APM bridge, restatements, tax, impairment, debt and leases.

### 5. Derived fundamentals and balance-sheet economics

Show only defensible metrics selected by the route: profitability/returns, unit economics, utilization, retention, backlog, production/cost curve, credit/claims, liquidity/leverage, cash conversion, capital intensity, working capital and earnings quality. Explain unavailable metrics.

### 6. Capital allocation, management and governance

Analyze reinvestment, acquisitions/disposals, R&D, inventory/capacity, lending growth, reserves, debt, dividends, buybacks, incentives, related parties and management actions versus claims.

### 7. Strategy, competition and advantages/limits

Separate targets from evidence. Identify scarce inputs, switching costs, scale, network effects, cost position, IP, permits, distribution or capital access only when verified. State where the advantage does not transfer.

### 8. Risk, stress paths and monitoring

Map each major risk to the causal chain, statement line, KPI, trigger and falsification condition. Include regulation, credit/claims, commodity, execution, product, cyber/data, refinancing, FX, dilution and governance as relevant.

### 9. Valuation

Select DCF/FCF, EV multiples, P/E/P/B/residual income, NAV/SOTP, rNPV, reserve valuation or another route-appropriate method. Show market boundary, assumptions before results, scenario ranges, sensitivity, double-count treatment and upgrade/downgrade conditions. Use 2-year scenarios only when near-term catalysts or constraints are decision-relevant.

### 10. Evidence gaps and balanced synthesis

State what is established, attractive, fragile, contradicted, unmodeled and capable of changing the view. End with investment thesis/anti-thesis only after evidence and valuation.

### 11. Source index and reproducibility handoff

List source IDs, local paths, original URLs, document dates, access dates, page locators, extraction method, usability, derived-data paths, tests and Git status.

## 3. Route modules

Add only relevant modules:

- **Recurring/contracted/service**: cohorts, churn, renewal, CAC payback, contract escalation, service cost and deferred/contract costs.
- **Transaction/distribution/marketplace**: funnel, take rate, conversion, repeat, refunds, partner concentration, working capital and contribution after acquisition cost.
- **Manufacturing/hardware**: capacity, utilization, yield, price/mix, unit cost, inventory, lead times, warranty, installed base and maintenance capex.
- **Project/engineering/real estate**: backlog, award/win rate, progress, change orders, completion, occupancy, rent, development capex, guarantees and refinancing.
- **Software/platform**: ARR/usage, retention, bookings/backlog, gross margin, CAC, R&D capitalization, deferred revenue, take rate and network density.
- **Infrastructure/utility**: contracted versus merchant, pass-through, availability, escalation, maintenance/growth capex, leases, debt matching and regulatory returns.
- **Lender**: vintage, yield/spread, funding, delinquency/NPL, ECL/stage, coverage, write-offs/recoveries, liquidity, capital and P/B/P/E logic.
- **Insurer**: premium/service result, renewal, loss/combined ratio, claims, CSM, acquisition costs, solvency, investment yield and asset-liability matching.
- **Resource/commodity**: reserves, grade, production, recovery, realized price, cost curve, sustaining/growth capex, reclamation, cycle sensitivity and NAV.
- **Pharma/biotech**: pipeline, trial stage, probability of success, indication, market access, milestones, patent/lifecycle, runway and rNPV.
- **Investment holding/conglomerate**: asset bridge, listed/equity-method holdings, distributions versus fair value, tax/liquidity/control discounts, holding costs, debt and SOTP.

## 4. Writing and layout rules

- Write for a professional investor unfamiliar with the company's industry.
- State facts first, calculations second, judgments third, and assumptions/unresolved items visibly.
- Use concrete economic units and mechanisms instead of generic labels. Mark hypothetical examples as illustrative.
- Use tables for comparisons, reconciliations, route maps, KPIs, scenarios and evidence status; keep units, periods, scope, formulas and source IDs visible.
- Avoid repeating the same judgment in operations, strategy, advantages, risks and conclusion. Each section answers one question.
- Preserve missing disclosure as an investment risk. Use `n.a.` for economically irrelevant fields and `unavailable` for relevant but undisclosed fields.

## 5. Final quality checklist

### Evidence

- [ ] scope, as-of date, accounting, units and consolidation boundary visible;
- [ ] source IDs, URLs, local paths and page locators resolve;
- [ ] facts, company claims, calculations, judgments, assumptions and unresolved items separated;
- [ ] contradictory evidence preserved and adjudicated transparently.

### Routing and coverage

- [ ] primary and secondary business-model archetypes recorded for each material segment;
- [ ] economic unit, value driver, balance-sheet anchor and risk carrier identified;
- [ ] every material segment, legal entity, revenue type, risk, capital action and valuation component covered or explicitly unavailable;
- [ ] irrelevant modules were excluded rather than filled mechanically.

### Fundamentals and valuation

- [ ] statements reconcile and APMs remain separate;
- [ ] route-appropriate metrics appear before narrative;
- [ ] material movements have bridges or explicit unresolved status;
- [ ] valuation method matches the business model and avoids double counting;
- [ ] assumptions precede results and sensitivities are directionally coherent;
- [ ] no IRR, target price or precision is shown when inputs are invalid.

### Publishing

- [ ] Markdown headings, tables, links and code fences render correctly;
- [ ] units, periods and share counts are consistent;
- [ ] `git diff --check` and available parsers/calculators pass;
- [ ] handoff states source scope, limitations, tests, derived paths and Git status.
