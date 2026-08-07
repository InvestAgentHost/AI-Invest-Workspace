# Statement Mapping

## Contents

1. Evidence model
2. Sign and unit conventions
3. Balance-sheet mapping
4. Income-statement mapping
5. Cash-flow mapping
6. Restatements and comparability
7. Mapping confidence and refusal rules

## 1. Evidence model

Maintain three layers. Never collapse them into one table during extraction.

| Layer | Purpose | Example |
|---|---|---|
| Source | Preserve exactly what the issuer printed | `Operating income`, EUR 4,418.346m, annual report p.5 |
| Canonical | Express the economic role needed by a formula | `revenue`, composed of services plus other operating income |
| Derived | Apply a named formula to canonical inputs | operating margin = operating profit / revenue |

Each canonical value must retain a link to one or more source rows. A translated label is commentary, not evidence.

## 2. Sign and unit conventions

Preserve raw signs exactly. In normalized calculator inputs use these conventions:

- Asset, liability, debt, lease, equity, cash, receivable, inventory, and payable balances: positive stock values.
- Revenue, profit, CFO, CFI, CFF, and net cash change: signed values.
- Expense magnitudes used in formulas, including cost of revenue, capex, D&A, interest paid, and dividends paid: positive values.
- Net income and operating profit: signed, so losses remain negative.
- Treasury shares may be negative in the source equity statement; do not treat the negative balance as cash.

Record `currency` and `scale` once and convert all normalized values to one scale. Do not mix thousands and millions. Do not translate a comma/decimal convention without checking the report locale.

Use separate null states:

- `0`: issuer reported zero or a defensible aggregation equals zero.
- missing key: not available for the metric engine.
- `not_disclosed`: source has no value.
- `not_applicable`: the concept does not apply.
- `not_comparable`: a value exists but should not be trended without adjustment.

## 3. Balance-sheet mapping

### Assets

| Canonical key | Economic content | Mapping cautions |
|---|---|---|
| `cash_and_equivalents` | Unrestricted cash and qualifying cash equivalents | Do not include restricted cash or short-term investments without disclosure. |
| `liquid_investments` | Current investments defensibly available for debt netting | Keep separate from cash; exclude strategic or restricted investments. |
| `trade_receivables` | Customer receivables related to revenue | Exclude loans, tax receivables, derivatives, and related-party balances unless intentionally included. |
| `inventory` | Inventory held for sale or production | Often immaterial or structurally absent in services. |
| `quick_assets` | Cash, eligible liquid investments, and collectible current receivables | Prefer an explicit constructed field to assuming every current financial asset is liquid. |
| `current_assets` | Issuer's current-asset subtotal | State whether held-for-sale assets sit outside the subtotal. |
| `ppe` | Property, plant and equipment | Distinguish gross, accumulated depreciation, and net carrying amount. Use net carrying amount for asset mix. |
| `right_of_use_assets` | IFRS 16/ASC 842 right-of-use assets | Keep separate from owned PPE when analyzing capital intensity. |
| `goodwill` | Acquisition goodwill | Do not combine with finite-life intangibles when discussing amortization. |
| `intangible_assets` | Identifiable intangible assets, usually net | State whether goodwill is included in the issuer's subtotal. |
| `total_assets` | Consolidated asset total | Verify held-for-sale assets and discontinued operations. |

### Liabilities and equity

| Canonical key | Economic content | Mapping cautions |
|---|---|---|
| `short_term_debt` | Current interest-bearing bank debt, notes, and bonds | Exclude trade payables and derivatives unless economically debt-like and disclosed. |
| `long_term_debt` | Non-current interest-bearing borrowings | Use carrying value unless the metric explicitly calls for principal or fair value. |
| `current_lease_liabilities` | Current lease obligations | Keep separate from debt excluding leases. |
| `noncurrent_lease_liabilities` | Non-current lease obligations | Match with after-lease earnings only when definitions align. |
| `trade_payables` | Supplier balances arising from operations | Exclude capex payables when separately disclosed if calculating operating working capital. |
| `current_liabilities` | Issuer's current-liability subtotal | State whether held-for-sale liabilities sit outside the subtotal. |
| `total_liabilities` | Consolidated liability total | Derive from assets minus equity only for a reconciliation check, not as a sourced value. |
| `parent_equity` | Equity attributable to owners of the parent | Required denominator for parent-attributable ROE. |
| `nci` | Non-controlling interests | Do not include in parent ROE. |
| `total_equity` | Parent equity plus NCI | Match with consolidated net income if used for ROE. |

### Debt composition

Build debt from interest-bearing instruments, not from total liabilities:

```text
gross debt excluding leases = short-term debt + long-term debt
gross debt including leases = gross debt excluding leases
                              + current lease liabilities
                              + non-current lease liabilities
net debt excluding leases   = gross debt excluding leases
                              - cash and equivalents
                              - eligible liquid investments
net debt including leases   = gross debt including leases
                              - cash and equivalents
                              - eligible liquid investments
```

Do not net derivatives, restricted cash, supplier finance, pension deficits, or asset-retirement obligations by default. Add them only in a separately named adjusted-debt measure with a rationale.

## 4. Income-statement mapping

| Canonical key | Economic content | Mapping cautions |
|---|---|---|
| `revenue` | Consideration from ordinary activities before operating costs | `Operating income` may be revenue or profit. Verify the subtotal equation and note definition. |
| `revenue_ex_pass_through` | Issuer-defined revenue excluding pass-through items | Store as APM; preserve the reconciliation to statutory revenue. |
| `cost_of_revenue` | Direct cost attributable to delivered goods/services | Required for gross-margin and inventory-day analysis. A nature-of-expense P&L may not disclose it. |
| `gross_profit` | Revenue less cost of revenue | Do not manufacture from total operating expenses. |
| `depreciation_amortization` | D&A expense magnitude | Separate impairment when disclosed; adding impairment creates an adjusted metric, not EBITDA. |
| `operating_profit` | Statutory profit from operations/EBIT when definitions align | Check whether finance items, associate results, or disposals sit above or below it. |
| `ebitda_reported` | Issuer-reported statutory or non-GAAP EBITDA | Preserve definition. EBITDA is not an IFRS line item. |
| `adjusted_ebitda_reported` | Issuer-adjusted EBITDA | Preserve every adjustment and do not silently recreate it. |
| `ebitdaal_reported` | Issuer-defined EBITDA after leases | Use only with verified lease treatment. |
| `net_interest_expense` | Interest expense less interest income | Exclude FX, fair-value, refinancing, and other finance costs unless the issuer combines them and no cleaner measure exists. |
| `income_before_tax` | Profit/loss before income tax | Confirm discontinued operations and associate results. |
| `income_tax_expense` | Signed tax expense or benefit | Do not use a one-year tax benefit as a normalized tax rate without analysis. |
| `net_income_consolidated` | Profit/loss attributable to all equity holders | Match with total equity or total assets. |
| `net_income_parent` | Profit/loss attributable to parent shareholders | Match with parent equity and per-share analysis. |
| `net_income_nci` | Profit/loss attributable to NCI | Reconcile parent plus NCI to consolidated income. |

### EBITDA construction

If no reported EBITDA exists, calculate only an unadjusted measure:

```text
calculated EBITDA = operating profit + D&A
```

Label it `ebitda_calculated`. Do not add impairment, restructuring, share-based compensation, disposal losses, or other items unless producing a separately named adjusted measure with an explicit bridge.

## 5. Cash-flow mapping

| Canonical key | Economic content | Mapping cautions |
|---|---|---|
| `cfo` | Net cash from operating activities | IFRS permits interest and dividends in different sections; inspect policy before comparison. |
| `cfi` | Net cash from investing activities | Includes acquisitions and disposals, not only capex. |
| `cff` | Net cash from financing activities | Includes borrowing, repayment, leases, dividends, buybacks, and equity issuance. |
| `capex_ppe` | Cash purchases of PPE, positive magnitude | Do not use accounting additions when cash purchases are available. |
| `capex_intangibles` | Cash purchases of intangibles, positive magnitude | Include capitalized development only if classified here. |
| `capex_total` | PPE plus intangible cash purchases | Exclude acquisitions unless the metric explicitly includes them. |
| `interest_paid` | Cash interest paid, positive magnitude | Check whether included in CFO or CFF. |
| `lease_payments` | Principal and/or total lease cash payments | Separate principal from interest when possible. |
| `acquisitions_paid` | Cash paid for business combinations, net or gross as labeled | Do not call this organic capex. |
| `asset_disposal_proceeds` | Cash proceeds from asset/business disposals | Not recurring operating cash generation. |
| `dividends_paid` | Cash dividends to parent shareholders | Keep NCI dividends separate. |
| `buybacks` | Cash acquisition of treasury shares | Distinguish gross buybacks from employee-share settlements. |
| `cash_begin`, `cash_end` | Cash-flow statement opening and closing cash | May differ from balance-sheet cash because of overdrafts or held-for-sale cash. |
| `fx_cash_effect` | Exchange-rate effect on cash | Include in cash reconciliation, not CFO. |
| `other_cash_effect` | Scope/reclassification effects | Require a source note. |

`CFO - capex_total` is an analyst calculation. Name it `cash_flow_after_capex`; do not automatically label it the issuer's FCF. Store issuer-defined `fcf_company_reported` separately.

## 6. Restatements and comparability

Use this precedence for a prior-year comparative:

1. Later audited filing's restated/reclassified comparative.
2. Same-period audited filing as originally reported.
3. Interim or preliminary figure only when audited data is unavailable.

Create a bridge when labels or rows change. Examples:

- one prior-year row is split into D&A and disposal results in the later filing;
- two tax cash-flow rows are combined in the comparative column;
- continuing operations are separated after a disposal;
- an acquisition changes the consolidation perimeter;
- IFRS 16 or another policy changes classification.

Do not force a row-level trend when only the subtotal is comparable. Mark the row `not_comparable` and analyze the common subtotal.

## 7. Mapping confidence and refusal rules

Use `high` confidence when the label, note, and subtotal relationship agree. Use `medium` when the economic role is clear but composition is partly aggregated. Use `low` when the mapping depends on an assumption.

Refuse or defer a metric when:

- the source is illegible or the sign cannot be verified;
- units or periods differ and cannot be reconciled;
- the numerator and denominator have different consolidation or ownership scopes;
- a non-GAAP input lacks a definition or reconciliation;
- a debt or lease perimeter cannot be matched to the earnings denominator;
- a required component is blank and zero would change the result materially.

Report the missing evidence needed to complete the calculation.
