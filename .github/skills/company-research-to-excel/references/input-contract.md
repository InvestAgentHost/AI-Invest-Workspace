# Input Contract

The exporter accepts prepared artifacts, not raw acquisition targets.

All exported tables use the canonical wide-panel orientation: metric/item names run down rows and reporting periods run across columns. `research_panel.v1` already declares this shape. A clearly detected legacy table whose first column is `period`/`date` and whose rows are periods is transposed once by the collector and marked with `orientation_transform`; arbitrary long-form event records are not silently pivoted.

## Supported files

| File | Interpretation | Default sheet behavior |
|---|---|---|
| `.csv` / `.tsv` | Header row plus records; values are kept in source column order | Group with related panels by economic topic |
| `.md` | GitHub-style pipe tables and cleaned filing HTML tables; heading hierarchy and line ranges are recorded | Group selected tables by economic topic |
| `.json` | A `research_panel.v1` panel, list of records, `data`/`rows` list, or a `periods` map with `values` | Group each logical table by economic topic |

`company.yaml`, `research-context.md`, source indexes, and coverage notes provide workbook metadata and provenance; do not export them as data panels unless the user asks. Binary SEC/IR originals remain outside this workflow.

## Company-directory discovery

When the request identifies a company, inspect its matching `data/curated/companies/<market>/<company-id>/` directory and company research package. First select explicit normalized/curated panel files. Only then select cleaned filing Markdown for missing panels or filing-native tables requested by the user. Pass the selected directories or files to one collector invocation; overlapping roots are de-duplicated by resolved path. This precedence prevents exporting the same disclosure twice from a canonical CSV/JSON panel and its cleaned filing source. Default discovery excludes raw/runtime directories, transcript/research-text directories, and standard context/coverage/evidence logs. Exclude forecasts, assumptions, valuation files, and calculated outputs unless the user explicitly includes them. An explicit `--include` may opt a skipped path back in; `--exclude` removes matching files even when another include matches. Do not infer that a PDF or HTML original is a cleaned panel.

Useful explicit filters:

```text
--include 'data/*.csv'
--include 'data/sec-cleaned/*.md'
--exclude '*forecast*'
--table 'financial|portfolio|kpi'
--period 'FY25/26|1QFY26/27'
```

Period regexes match a complete wide-table header or a complete value in a `period`/`date`/`fiscal`/`quarter`/`year` column. Use `.*` explicitly when substring matching is intended. Source and note text never determine period inclusion.

## Value typing

- A standalone integer/decimal, optionally with thousands separators, is typed as a number.
- A standalone percentage is stored as a decimal fraction and displayed as `0.0%`.
- Numeric fields whose column or metric name ends in `_pct`, `percent`, or `percentage` are interpreted as percentage points (`38.4` becomes `0.384` with `38.4%` display). Decimal-fraction inputs must carry explicit format metadata or a literal `%` representation instead of relying on that suffix.
- Parenthesized negatives and unambiguous currency-prefixed values are typed with the correct sign.
- Dates, period labels, units, source IDs, footnote markers, and strings containing multiple semantic values remain text.
- Preserve missing markers (`n.a.`, `n.m.`, `unavailable`, `not disclosed`, `—`, `-`) as text. An empty cell is not a reported zero.

## Provenance

Every table section records the repository-relative input path, logical table title, heading path when available, and source line range for Markdown. `Sources` repeats one row per logical table and includes a SHA-256 of the input file so a later export can be compared without changing the source.

The collector emits `company-research-excel-bundle.v2`. Each `tables[]` item has a deterministic `table_id`, advisory `topic_hint`, dimensions, `orientation`, `headers`, typed `rows`, and `typed_cells` with zero-based row/column coordinates and a number-format hint. For `research_panel.v1`, it also preserves panel metadata and zero-based `cell_evidence`, including disclosure status, formula note, narrative note, and exact source references. Date values remain ISO text in the JSON and must be converted to JavaScript `Date` values during workbook authoring. Topic hints accelerate planning but never override the table's actual content, accounting basis, or user instructions.
