# Inputs — original 10-K/10-Q and compact source mappings

The file/view structures below serve the bundled default pipeline. The Agent
may select another reliable extraction/mapping method when the source requires
it, keeping the same original evidence, period/unit discipline and review.

Start with the company's original-source index/research context. Originals are
authoritative. Prepared JSON/CSV/Markdown can accelerate organization but must
resolve to the original. Do not acquire new sources or add 8-K, releases,
transcripts, forecasts or valuation inputs for this historical route.

The bundled tools use the Workspace .venv with openpyxl and beautifulsoup4.
Repeated --sec-source accepts actual files or directories containing
source.html/raw/source.html. Inputs may be collected together or in batches;
keep source IDs stable and reconcile duplicate/versioned facts when merging.

## File catalog — once

--filing-manifest supplies sources with source_id, Workspace-relative path,
filing_type, filing_date, url and optional accession/version. Collector computes
sha256. Identify native dei:DocumentType/submission header; a declared form alone
does not prove a filing is a 10-K/10-Q. Preserve immutable originals and hashes.

For a non-inline original, form_evidence may point to its submission-header
path/hash/exact_text. Metadata is reused by every table, never copied per value.

## Native candidates and selected views

collect_tables.py emits company-research-excel-bundle.v4, status=draft.
It preserves native geometry, raw tokens and physical value coordinates.
File metadata lives once in sources; table metadata references source_id.
No financial_input.json is required.

The first HTML row is not assumed to be the whole heading. Read all heading
levels and add selected metadata.views; unselected layout/header tables require
no individual disposition paperwork. Example:

~~~json
{
  "metadata":{
    "source_id":"F_2025_10K","html_table_index":38,
    "views":[{
      "table_id":"IS_2025","sheet_short":"IS","topic":"IS",
      "defaults":{
        "unit":"USD million","currency":"USD","scope":"consolidated",
        "basis":"gaap","version":"as-filed-2025"
      },
      "periods":{"FY2025":{"column":6,"headers":[{"r":1,"c":6,"text":"2025"}]}},
      "context":{
        "unit":{"r":2,"c":0,"text":"In millions except per-share data"},
        "scope":{"kind":"text","start":100,"end":125,"text":"<exact original substring>"}
      },
      "data_rows":[8,40],
      "metrics":[
        {"source_row":8,"source_column":0,"id":"revenue","bold":true,"metric_kind":"flow","additive":true},
        {"source_row":35,"source_column":0,"id":"eps","unit":"USD/share","metric_kind":"eps","fmt":"ps"}
      ]
    }]
  }
}
~~~

Illustrative indices must be replaced. source_row/source_column/period.column
refer to the EXPANDED bundle grid. The collector's cell map supplies physical
original r/c automatically. Table context locators r/c instead refer to PHYSICAL
original elements. Keep this distinction when there are spans/blank columns.

The assembler produces shared table definitions and compact value bindings.
Do not handwrite a full evidence record for every number. Only exceptional
facts use view.exceptions keyed by metric/period; these need reason and narrow
overrides (sign, scale, exact interval, etc.). Original/recast precedence is an
explicit selection: overlapping canonical metric/period facts are not silently
overwritten. Compatible disjoint periods merge by explicit metric ID, never by
label similarity alone.

Separate three-month/nine-month or incompatible scope views of the same native
table into different IDs/series. Pick only intended fiscal columns. A native
period filter is deferred until that mapping exists.

## Prepared inputs

The direct financial_input.json route retains period_order/period_metadata,
sources, shared tables, the single coverage matrix, and each metric's value/
statement/canonical definition plus compact evidence={table,r,c}. Model drafts
with old expanded v3 evidence need explicit conversion, not silent acceptance.

research_panel.v1 and generic tables may help discovery; source_refs alone are
not enough for a final value binding. --metrics is disabled: derived metrics
are linked formulas, not imported hardcoded Markdown results.

## Typing

Standalone numbers, explicit percentages and parenthesized negatives are typed;
preserve precision. Do not infer percentage scale from field names. Missing is
not zero; a source dash requires a reviewed shared zero convention or remains
unresolved. Multi-number/ambiguous tokens are not guessed.

For value normalization and checks, see [source verification](source-verification.md).
For the default model interface, see [schema](model-schema.md).

## Default tool commands

These are examples, not a mandatory command sequence. Replace placeholders with
actual Workspace-relative paths and issuer fiscal labels. Native collection
does not need financial_input.json. The collector and assembler produce drafts;
map selected metadata.views, resolve gaps and add linked formulas before normal
build. The assembler does not infer accounting comparability from labels.
Use a company data/derived build directory for mappings and intermediate files.
Set `<research-workbook-dir>` to
`research/companies/<market>/<company-id>/outputs/company-research-to-excel/`
for the single current research workbook; `outputs/workbooks/` is reserved for
user-requested finalized workbooks.

~~~sh
.venv/bin/python .github/skills/company-research-to-excel/scripts/collect_tables.py \
  --sec-source sources/companies/<market>/<company-id>/<filing-dir> \
  --filing-manifest <build-dir>/filings.json --output <build-dir>/tables.json

.venv/bin/python .github/skills/company-research-to-excel/scripts/assemble_model.py \
  --bundle-only --bundle <build-dir>/tables.json \
  --periods <fiscal-labels> --period-metadata <build-dir>/periods.json \
  --name <company-name> --ticker <ticker> -o <build-dir>/model.json

.venv/bin/python .github/skills/company-research-to-excel/scripts/build_workbook.py \
  <build-dir>/model.json <research-workbook-dir>/<ticker>_model.xlsx
~~~

The prepared-input alternative is assemble_model.py <financial_input.json>
--bundle <tables.json> -o <model.json>. --strict on the collector makes warnings
fatal; without it, inspect and resolve warnings affecting the requested data.
--draft on the builder creates a visibly unverified style preview only. Neither
option replaces final checks. The builder creates new files and sets calculation
flags; it does not calculate caches or update a manually edited workbook.

An optional separate layout plan may be checked with validate_layout.py, but
the shared views/model usually make that additional file unnecessary.
Recalculation and verification follow [source verification](source-verification.md).

### Valuation handoff inputs

For an explicit valuation request, pass the latest workbook, historical period/
unit/metric definitions, source and verification records, known gaps and manual
edits to [valuation-binding-methodology](../../valuation-binding-methodology/SKILL.md).
Reuse the existing files. Forecast inputs and adoption/update rules belong to
that skill; none are required by this historical input contract.
