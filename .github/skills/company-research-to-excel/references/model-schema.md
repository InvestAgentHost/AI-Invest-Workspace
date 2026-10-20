# Compact historical model.json — v4

This is the interface to the bundled builder/verifier, not a universal schema
for every issuer. Use it for the default route. When a disclosure is poorly
represented, the Agent may use a company-specific mapping or another authoring
route with equivalent source traceability and verification; it need not expand
the common schema or convert every exception into this representation. The
Agent judgment section in SKILL.md governs that choice.

Use **table-level context, value coordinates, documented exceptions, automated
checks**. The agent declares a source view once; the assembler generates compact
value bindings. Do not expand the resolved evidence back into model.json.

## Root

~~~json
{
  "schema": "historical-research-model.v4",
  "export_scope": "historical_10k_10q",
  "status": "mapped",
  "draft_gaps": [],
  "company": {
    "name": "Example", "ticker": "EXAMPLE", "currency": "USD",
    "units": "USD million, except EPS/shares as labeled",
    "reporting_framework": "US GAAP", "as_of_date": "2026-10-19"
  },
  "periods": {
    "annual": [
      {"label":"FY2025","fiscal_year":2025,"start":"2025-01-01","end":"2025-12-31","grain":"annual"}
    ],
    "quarterly": [], "scrap_cols": 0
  },
  "sources": [],
  "tables": [],
  "coverage": [],
  "sheets": []
}
~~~

Examples are fictional. A release cannot leave sources/tables/coverage empty.
Use issuer fiscal dates, including 52/53-week years. Each (fiscal_year,
fiscal_quarter) is unique; annual fiscal_quarter is null. Same-quarter YoY uses
fiscal keys, not visible column positions. Optional comparatives maps justified
calendar changes. Default required_statements is IS/BS/CF. Optional
required_topics/coverage_scope_reason and required_check_groups/
check_group_periods/check_scope_reason adapt coverage and checks as described
below; they need no separate approval or layout ledger.

sources registers each original ONCE: source_id, Workspace-relative path,
sha256, filing_type, filing_date, url, optional accession/version. Non-inline
filings may need form_evidence (submission header path/hash/exact_text).
Do not duplicate file metadata in every table or numeric fact.

## Shared source view

tables stores each selected financial view once:

~~~json
{
  "table_id": "IS_2025", "source_id": "F_2025_10K",
  "topic": "IS", "html_table_index": 38,
  "defaults": {
    "unit":"USD million","currency":"USD","scope":"consolidated",
    "basis":"gaap","version":"as-filed-2025"
  },
  "periods": {
    "FY2025": {
      "column":6,
      "headers":[{"r":1,"c":6,"text":"2025"}]
    }
  },
  "context": {
    "unit":{"r":2,"c":0,"text":"In millions except per-share data"},
    "scope":{"kind":"text","start":100,"end":125,"text":"<exact original substring>"}
  },
  "data_rows":[8,40],
  "rows":{
    "revenue":{"r":8,"c":0,"label":"Net operating revenues"},
    "eps":{"r":35,"c":0,"label":"Diluted earnings per share","unit":"USD/share"}
  }
}
~~~

All locators are illustrative. html_table_index/r/c are zero-based PHYSICAL
original HTML elements. periods.*.column is the EXPANDED source-grid column,
preserving blank cells and spans. Exact headers/unit/scope locators are shared,
not repeated for every value. A short locator r/c/text defaults to this table;
a text locator uses decoded-original HTML character offsets and exact text.

Metadata inheritance:
1. table.defaults;
2. table.rows[metric] exceptions (EPS unit, special normalization, etc.);
3. value binding overrides, only if needed and with reason.

periods keys inherit global dates/grain; declare only differences such as
start/end/grain=ytd or grain=instant. Source and exported intervals must agree.
A row may use period_rule=opening_balance/closing_balance for cash reconciliation
stocks inside a flow table. The assembler computes the matching instant dates;
the raw auditor checks them against original XBRL/context. Unusual calendars
may use row period_overrides instead.

data_rows=[first,last] defines the financial body once. Scripts skip blank,
title and label-only rows mechanically. A genuinely excluded financial row
requires exclude_rows={"14":"reason"}, with replacement information when
superseded. No per-HTML-row header/nonnumeric disposition ledger is required.

Three-month and nine-month views of the same HTML table receive different
table_ids, shared-context periods and distinct canonical metric IDs. Do not put
two columns with different grain into one fiscal-label slot.

## Numeric owners and compact bindings

~~~json
{
  "id":"revenue","label":"Net operating revenues","type":"input",
  "unit":"USD million","currency":"USD","scope":"consolidated",
  "measure_basis":"gaap","metric_kind":"flow","additive":true,
  "bold":true,
  "values":{"FY2025":1234},
  "evidence":{"FY2025":{"table":"IS_2025","r":8,"c":6}}
}
~~~

A normal fact needs ONLY the shared table ID and physical value coordinates.
The assembler generates these from the source grid. The original token is
reopened from the immutable source during audit; it is not manually copied
into a second per-value dossier. No per-value reviewed/status/hash/period/
unit/source-label object is needed.

An exceptional fact adds overrides:
~~~json
{
  "table":"IS_2025","r":8,"c":6,
  "overrides":{
    "reason":"Original negative sign is in the preceding physical cell",
    "normalization":{"sign":-1,"reason":"Original parentheses"},
    "sign_locator":{"r":8,"c":5,"text":"("}
  }
}
~~~

Normalization defaults to multiplier=1/sign=1. Scale/sign changes need source
support and reason. A source dash is zero only if normalization.dash_means_zero
and its reason explicitly establish that convention; share it at table/metric
level when applicable. Never infer percentage scale from a metric name.

For a narrative figure, define a small shared view with locator_kind=text,
source_id/defaults/periods/rows. Its row mapping includes label and locator for
the original sentence; the value binding uses text={kind:text,start,end,text}
for the isolated numeric token. Unit/scope/period context is still shared.
No fictional HTML table is required.

Native non-period schedules use kind=table, table=[rows] and cell_evidence
entries: row/column (output positions), id/period_label, plus the same compact
table/r/c binding. The shared reporting period is the statement date; a maturity
year is a payment bucket. External strings remain literal, never formulas.

## Workbook rows and derived values

Statement sheets: kind=statement, short=IS/BS/CF/etc., name, blocks of title,
optional note, rows. Formatting fields and approved style are unchanged.
An optional sheet role (contents/operating/income_statement/balance_sheet/
cash_flow/metrics/notes) overrides name-based presentation grouping without
changing accounting meaning. The workbook contract owns tab order/colors.
Source/table/value mappings remain external; no generated Sources tab or mass
cell comments are needed. Missing-value states/reasons remain in metadata,
while numeric displays are blank and formula guards return ""; n.m. is retained.

| Row type | Wiring |
|---|---|
| input | values/evidence; reported hardcodes |
| link | ref="IS:revenue"; numeric/missing guard |
| subtotal | children; any missing component makes result unavailable |
| calc | expr, optional expr_q / expr_by_period |
| growth_yoy / growth_qoq | of metric; semantic fiscal comparison |
| check | expr, check_group, explicit source-unit tolerance |
| note / spacer | explanatory merged row / gap |

The bundled expression translator accepts arithmetic only: numeric constants,
`+ - * / **`, parentheses
and references {metric}, {IS:revenue}, {metric@-1}, {CF:ocf[FY2025]}.
@-1 means preceding fiscal year/quarter, never preceding visible column.
It does not execute arbitrary Python/Excel functions. A disclosure needing other
formula syntax can use a suitable authoring/checking route; this grammar is not
a restriction on financial analysis. Derived results remain linked formulas.

One input cell can instead have cell_expr[label], with no values[label] entry.
Its cell_meta.status is calculated; cross-period derivation supplies inputs and
reason. Quarter differences use kind=quarter_difference, additive=true and two
actual inputs in subtraction order. The auditor verifies matching basis/unit,
shared fiscal start and contiguous output interval. EPS/WASO/ratios/balances
cannot be annual-minus-nine-month calculations.

period_overrides on workbook rows are normally generated from shared source
periods. Explicit applicable_periods / min_label / max_label define genuine
applicability. Explain unavailable results via unavailable_reason_by_period;
do not use applicability to conceal missing required history.

Default check groups: income_bridge, balance_equation, cash_bridge. Missing
inputs never pass. Tolerance defaults to 1e-9 arithmetic noise; a larger amount
requires tolerance_reason in the metric's stored unit. expect_nonzero is invalid.
Use required_check_groups to name the economically applicable groups. A departure
from the defaults or narrower check_group_periods needs a brief check_scope_reason;
this explains the scope rather than authorizes omission of a substantive bridge.

## One coverage matrix

~~~json
[
  {"topic":"IS","tables":["IS_2025"]},
  {"topic":"BS","tables":["BS_2025"]},
  {"topic":"CF","tables":["CF_2025"]},
  {"topic":"segments","tables":["SEG_2025"]},
  {"topic":"products_geography","tables":["GEO_2025"]},
  {"topic":"operating_metrics","tables":["KPI_2025"]},
  {"topic":"material_notes","tables":["DEBT_2025","SBC_2025"]}
]
~~~

These topic names are defaults, not an enumeration. Custom non-empty topic names
are accepted, and every selected view must appear in the matrix under its topic.
required_topics defaults to required_statements plus segments,
products_geography, operating_metrics and material_notes. The Agent can set a
different list; a brief coverage_scope_reason explains any replaced default
groupings. Regrouping does not remove the obligation to search relevant original
disclosures across the requested history.

Use status=not_disclosed/not_applicable with reason only after reading the
originals. An unresolved gap uses gaps=[{period,reason}] and prevents full PASS.
No separate filing_coverage + disclosure_inventory + per-row disposition copies.
Agent review independently checks every original's coverage and the full history;
the matrix alone cannot prove that an omitted source topic was searched.

## Agent review and migration

The final semantic review is performed by a different, independent Agent directly
against originals and final Excel. Its compact review.json records distinct
producer/reviewer Agent IDs and binds the data fingerprint and final workbook
hash, reviewed source/table IDs, six review themes, findings and a concise conclusion. It does not
repeat every numeric fact. See [Agent review](agent-data-review.md).

Do not silently accept old v3 per-value evidence objects as v4 bindings. Convert
old DRAFT mappings to shared tables explicitly. Do not rebuild an existing
manually maintained company workbook as part of migration. Valuation extensions
keep their existing route.
