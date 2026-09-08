# Workbook Contract

Use Artifact Tool for authoring, recalculation, inspection, rendering, and `.xlsx` export. Read the platform spreadsheet skill before using its runtime.

## Workbook structure

Build an investment-research workbook, not a collection of mechanically generated tabs. Use only the worksheets supported by the selected data. A normal order is:

Every section is a wide panel: metric/item labels are in the identifying columns on the left, and periods run left to right across the numeric columns. Keep this orientation in every worksheet section, even when several sections are stacked on one sheet.

1. `Contents` when the workbook has four or more data worksheets
2. `Financials`
3. `Segments`
4. `Products & Geography`
5. `Operating KPIs`
6. Relevant note schedules such as `Capital & Returns`, `Debt & Liquidity`, `Assets & Intangibles`, or `Tax & Shares`
7. `Sources`

Do not create empty placeholder worksheets. Combine sparse adjacent topics when that improves navigation. Split a topic only when the result would be hard to scan, such as a worksheet exceeding roughly 140 populated rows, more than 20 period columns, or several tables with incompatible column structures. One table per worksheet is an exception, not the default.

`Contents` is a compact index, not a marketing cover. Show company name, ticker, reporting currency/scale, fiscal year end, research as-of date, latest covered period, and linked worksheet/section names when those facts are available. Do not add narrative conclusions, KPI cards, or charts unless requested.

Match worksheet and section language to the user's request and the research package. For a Chinese workbook, use concise equivalents such as `目录`, `合并报表`, `分部`, `产品与地区`, `经营指标`, `资本配置`, `债务与流动性`, `资产与无形资产`, `税务与股本`, and `来源`.

## Sheet composition

Place related tables as vertical sections on the same worksheet. Do not place unrelated tables side by side merely to use space.

- Row 1: blank.
- Row 2: worksheet title, 14 pt, dark text, no fill.
- Row 3: concise scope line with periods, currency/units, or as-of date when relevant.
- Row 4: thin rule and spacing.
- Row 6 onward: repeated table sections.

Each section contains:

1. A continuous dark navy section band with the economic table title.
2. A compact metadata line below it: filing/report period, units/basis, and source locator. Keep this visually secondary.
3. The original or normalized column headers.
4. The complete data rows.
5. Two blank rows before the next section.

Use one common left edge and align comparable period columns across sections when the existing panels share the same period grain. Keep periods chronological from left to right. When annual and quarterly series coexist, keep each as a clearly labeled block separated by one blank unfilled column. Do not stitch tables across different units, consolidation scopes, segment definitions, or accounting bases; place them in separate labeled sections and preserve the break.

## Financial presentation

- Use Arial throughout: 14 pt worksheet titles and 10 pt headers/body. Use 9 pt italic grey for scope and source metadata.
- Use a white background, dark charcoal text, navy section bands, dark blue column headers with white text, and restrained light blue/grey fills for period headers or alternating rows. Avoid gradients and decorative blocks.
- Use blue font for hardcoded reported numeric values. Use black for labels and any explicitly requested formulas. Keep passing checks neutral; use light red fill and bold red text only for actual failures or missing required inputs.
- Hide gridlines. Use thin structural borders only around headers, totals, and section boundaries; do not box every body cell.
- Left-align labels, right-align numbers, center headers, and top-align wrapped descriptions. Use indentation for reported sub-lines and bold top borders for issuer-reported totals where the source structure identifies them.
- Use accounting formats with parenthesized negatives and dash zeros. Display percentages with one decimal, per-share values with two decimals, and multiples with one decimal plus `x`. Preserve the stored precision.
- Use real date cells with `yyyy-mm-dd`. Preserve fiscal labels such as `FY2025` or `1QFY2026` when those are the issuer's labels; do not relabel periods without knowing the fiscal calendar.
- Set widths and only the necessary row heights explicitly after autofit. Long headers may wrap to two lines; values, labels, source IDs, and units must not be clipped or display `####`.
- Freeze the smallest useful header area and first identifying column on long sheets. A multi-section worksheet may use a short contents block with internal hyperlinks near the top when it materially improves navigation.

Convert every `typed_cells` entry before writing:

- `number`: keep the numeric JSON value and use the accounting-compatible format.
- `percentage`: keep the decimal value (for example `0.375`) and use `0.0%`.
- `date`: replace the ISO string with a JavaScript `Date` and use `yyyy-mm-dd`.

Apply formats to exact cells because one section or column can mix identifiers, dates, numbers, and missing markers. Never convert missing text to zero.

## Sources

`Sources` contains one row per exported logical table: table ID, worksheet, section, table title, filing/report period when known, repository-relative input path, source line/page/locator, kind, and SHA-256. Preserve any cell-level evidence table emitted from normalized financial JSON. Do not repeat the same citation in every data cell when a complete table shares one source.

For `research_panel.v1`, use the bundle's panel metadata and `cell_evidence` to preserve disclosure status, derivation formulas, comparability notes, missing periods, and exact source references. Keep this evidence in compact source/evidence sections rather than expanding every value into a separate worksheet or crowding every data cell with citations.

## Verification

Before export:

1. Confirm that every selected table ID appears exactly once in the layout plan and workbook. No table may be silently omitted or duplicated.
2. Recalculate once.
3. Inspect every worksheet's key ranges and representative typed cells. Check units, period order, labels, negative signs, missing markers, totals, and any restatement/reclassification boundary.
4. Scan for `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, `#N/A`, `#NUM!`, `#NULL!`, `#SPILL!`, and `#CALC!`. Distinguish deliberate text markers from formula errors.
5. Render every created worksheet at normal zoom. Fix clipped content, `####`, excessive whitespace, accidental overlaps, poor contrast, broken section hierarchy, and visually ambiguous period blocks.
6. Export one final `.xlsx`. Do not deliver previews or the intermediate bundle/layout plan unless requested.
