# Financial Series Reconstruction

This reference defines the agent-facing contract behind
`prompts/04-financial-series-reconstruction.zh-CN.md`. Use it when the user
asks to rebuild or extend multi-year statements or note tables.

## 1. Scope resolution

Resolve these fields before extraction:

| field | required decision |
|---|---|
| issuer | legal issuer, ticker, market, CIK |
| reporting basis | fiscal year end, GAAP/IFRS, currency, units, consolidated perimeter |
| periods | fiscal years, interim periods, and whether later restated comparatives take precedence |
| statement set | income, balance sheet, cash flow, equity, segment or other |
| note set | debt, lease, pension, goodwill/intangibles, inventory, working capital, tax, segment, equity, other |
| output boundary | raw reported tables only, standardized series, derived metrics, or all three |

If the user says “five-year financial series” without further qualification,
use the latest five audited fiscal years plus the latest 10-Q and request
confirmation only when the issuer identity or fiscal calendar is ambiguous.

## 2. Two-layer data model

Keep the reported layer immutable and separate from the analytical layer:

```text
reported layer: one row per source table, filing, period, label, value, locator
analytical layer: one row per canonical field and period, with mapping/status
```

The reported layer preserves the issuer's row order and presentation. The
analytical layer may normalize labels or units, but every transformation must
be explicit. A canonical field may have multiple source rows across years;
that is a mapping decision, not a string replacement.

Minimum metadata for a reported value:

```text
source_id, accession, filing_date, fiscal_period, table_title, note_number,
source_label, value, unit, sign_convention, locator, status, extraction_method
```

Minimum metadata for a standardized value:

```text
canonical_field, period, value, unit, source_id, source_label, transformation,
scope, status, confidence, comparability_note
```

Use `reported`, `restated`, `reclassified`, `derived`, `unavailable`, and
`not_meaningful` as explicit statuses. Preserve `blank` separately from zero.

## 3. Extraction order

1. Confirm the filing inventory and hash each raw source.
2. Prepare/index each filing and search table headings, note numbers, and
   canonical concepts.
3. Read the full table range, including continuation tables and footnotes.
4. Capture table title, units and period headers before extracting values.
5. Extract the original table unchanged into `raw_statements/` or `raw_notes/`.
6. Map rows into the analytical schema only after checking footnotes and
   subtotal equations.
7. Reconcile the standardized series and write the validation artifact.

For HTML filings, cite the prepared-document line range and the original
accession. For PDFs or image-backed tables, also retain printed page and PDF
page when they differ. Use visual review when merged cells, continuation pages,
or OCR could change the interpretation.

## 4. Cross-year stitching rules

- Prefer a later filing's explicitly restated comparative for the analytical
  series, while retaining the earlier originally reported value.
- Never join rows solely because their labels are similar. Require consistent
  table context, unit, scope, sign and subtotal behavior.
- Treat a changed row label, note number, segment definition, accounting policy
  or unit as a comparability event and record it in the bridge.
- Do not silently mix continuing operations with total-company values.
- For point-in-time balances use the reported date; for flows use the stated
  fiscal or interim period. Do not convert a quarter into a year without an
  explicit calculation and status of `derived`.
- Keep company-defined APMs separate from GAAP/IFRS rows and calculated metrics.

## 5. Reconciliation gates

At minimum test:

- total assets against liabilities plus equity;
- cash-flow subtotals against beginning cash, ending cash, FX and scope effects;
- consolidated net income against parent and non-controlling interests;
- debt and lease Note totals against balance-sheet classifications;
- inventory, receivables, payables and other working-capital Notes against the
  corresponding statement rows where disclosed;
- segment totals against consolidated revenue/profit after eliminations;
- retained earnings, treasury stock and other equity roll-forwards where
  disclosed.

Every failed or unavailable test must carry an explanation, affected periods,
and an `attempt_id` or source locator. A failed material gate lowers the package
to `PARTIAL` or `BLOCKED`; it must not be hidden by rounding or filling values.

## 6. Agent interaction contract

The agent should return a short progress block before long extraction:

```text
scope: FY____-FY____ + latest 10-Q
statements: income / balance sheet / cash flow
notes: ...
filings found: ...
known gaps: ...
next action: extract / map / reconcile / request confirmation
```

After extraction, return paths and counts, not only prose: number of raw
tables, standardized fields, unmapped rows, restatement events, failed checks,
and final status. Ask the user only about an ambiguity that changes the
reporting perimeter, period selection, or economic interpretation.

