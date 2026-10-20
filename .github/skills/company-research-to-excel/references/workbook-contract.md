# Workbook Contract — initial historical export

## Structure and ownership

Use separate Income Statement (IS), Balance Sheet (BS) and Cash Flow (CF)
worksheets. Order the workbook **Contents → operating schedules (Segments,
KPI, Products & Geography, etc.) → Income Statement → Balance Sheet → Cash Flow
→ Derivate Metrics → Note and material note schedules**. Combine ordinary
supporting notes in Note; give material, substantial schedules their own tabs.
Do not add technical Sources/Evidence/index tabs by default. Match sheet language to the research
package. Never copy another company's extra tabs or leave empty placeholders.

Each section is a wide panel: metrics down rows, chronological annual periods
on the left and quarterly periods on the right. Use one unfilled narrow
separator when both blocks exist. Distinguish source YTD cash-flow data and
derived discrete-quarter cash flows in separately labeled sections.

Keep related notes with their economic owner. Separate incompatible units,
scopes, reporting bases and restated segment definitions into labeled blocks.
Complete face statements belong in the workbook even if report prose is selective.

## Approved design

The single machine-readable authority is
[style-profile.json](../assets/style-profile.json), approved 2026-10-19.
Use it in any authoring tool; do not clone uncoordinated constants.

| Role | Font and color | Minimum height |
|---|---|---:|
| Main title | Arial 14 bold, white on #1F4E79 | 28 pt |
| Section band | Arial 10 bold, white on #1F4E79 | 22 pt |
| Period header | Arial 10 bold, white; annual #18324F, quarter #20746C | 24 pt |
| Body | Arial 10.5, #243447 | 22 pt |
| Reported/formula totals | Arial 10.5 bold, pale #EAF0F8, thin top border | 24 pt |
| Ratios/growth | Arial 10.5 italic | 20 pt |
| Notes | Arial 9, #64748B | 18 pt |
| Dates | Arial 8.5, real date cells | 18 pt |

A two-line label needs at least 36 pt; three lines about 50 pt; longer content
grows further. Never shrink title/body fonts to force fit. Use adaptive heights,
including hidden notes if users expand them. Inspect at 100% zoom; estimated
text fit is not a substitute for rendering.

Contents uses uniform **22 pt directory rows**, short single-line descriptions,
and no oversized directory cards. Title/header rows keep their normal roles.
Use the profile's functional tab colors: slate Contents, teal operating,
blue three statements, purple metrics and muted ochre notes. Same-group tabs
share a color; do not make every tab the same color or use a rainbow per tab.

Widths: label 60, collapsed business note 34 when used, otherwise gutter 2.2, period 12.2,
separator 3. Source paths do not belong in metric names. Detailed source/evidence
locators stay in external model/review metadata, not worksheet cells. Keep periods wide enough for
real values; correct #### by widening columns without shrinking fonts.

Use blue #2454A4 for reported hardcoded numbers, dark body color for same-sheet
formulas and green #20746C for cross-sheet formulas. Official reported totals
remain blue; a total does not become a hardcoded calculated value for styling.
Display unavailable/not-disclosed/not-applicable numeric results as blank;
formulas return "" while preserving COUNT/denominator guards. Keep missing
reasons and applicability in metadata, and retain n.m. where a computed rate
is not meaningful. A blank is never a numeric zero. Keep failures visible and red. No universal body grid,
gradients, gray scratch blocks or decorative dashboard cards.

Formats: parenthesized negatives, dash for numerical zero, percentages one
decimal, per-share two decimals, multiples one decimal+x; stored precision is
unchanged. Real dates use yyyy-mm-dd. Hide gridlines; top/center-align wrapped
headers, left-align labels, right-align numbers. Freeze C6 on statement panels.

## Default statement layout

- Row 1: continuous blue worksheet title band.
- Row 2: secondary currency/scale/framework/as-of metadata.
- Row 3: annual and quarterly period headers.
- Row 4: real period-end dates.
- Row 5: period grain; block notes make row overrides explicit.
- Row 6: breathing room.
- Row 7 onward: section band, optional wrapped note, metric rows, one small gap.

Optional section contents shifts blocks by a deterministic offset. The shared
registry owns cell positions; do not duplicate a separate row-count algorithm.
Section bands may span the separator; body separators stay white and empty.

## Formulas and source display

Follow the economic ownership and comparability rules in
[semantic layout](semantic-layout.md#comparability-and-deduplication). Show filed
totals separately from calculated checks; links/subtotals guard missing numeric
cells instead of treating blanks as zero.

Retain original paths, SEC forms/dates/URLs/hashes, shared table context, compact
value coordinates and coverage in external model/review files. Do not create
per-cell source comments/notes or large technical indexes in the delivered
workbook. Include only brief business/accounting explanations needed to read
the figures. Traceability and full original-source verification remain required;
removing visual source clutter does not remove evidence or reduce checking.

## Authoring and release

The default build_workbook.py is the deterministic new-file builder and reads
the shared profile. It uses openpyxl for layout/formula serialization; setting
fullCalcOnLoad does not calculate results. Use the available platform spreadsheet
skill/runtime for engine recalculation, inspection and rendered QA, preserving
the profile and formulas. Verify the workbook again after engine saving.

Do not overwrite a manually edited workbook using the initial generator. Its
current save, manual inputs and native objects require authorized scoped edits.

For visual QA, inspect each sheet at 100% zoom, including the title/section
bands, long labels, expandable notes and both annual/quarter blocks. No clipped
text, unreadable contrast, undersized rows or ####. Increase content-fitted
heights/widths or correct authoring behavior while preserving the approved font,
palette and minimum heights. An engine save can change styles: inspect the final
saved artifact, not only the pre-recalculation version.

Render QA views in memory or a temporary directory; remove them after inspection.
Do not accumulate preview PNGs, one-off builder scripts, logs or duplicate
workbook versions in company outputs. Publish one current historical workbook;
keep reusable source mappings/review metadata under company data/derived paths.
Clean Agent-owned scratch files, preserving original sources, unrelated outputs
and user work; superseded user-edited files require the user's cleanup scope.

Data/formula gates are defined once in [source verification](source-verification.md);
independent-Agent semantic review and final-version binding are defined in
[Agent data review](agent-data-review.md). Script PASS does not certify visual QA.


### Valuation extension

Requested valuation sheets inherit the shared profile and Approved design above.
Their forecasting/valuation content, model layout and update rules belong to the
valuation skill's [workbook contract](../../valuation-binding-methodology/references/workbook-contract.md).
Use scoped edits on the current workbook, preserving historical data, manual
changes and native features; do not run the initial generator as an updater.
