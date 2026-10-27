# Workbook Contract — initial historical export

## Structure and ownership

Use separate Income Statement (IS), Balance Sheet (BS) and Cash Flow (CF)
worksheets. Order the workbook **Contents → operating schedules (Segments,
KPI, Products & Geography, etc.) → Income Statement → Balance Sheet → Cash Flow
→ Derivate Metrics → Note and material note schedules**. Combine ordinary
supporting notes in Note; give material, substantial schedules their own tabs.
Do not add technical Sources/Evidence/index tabs by default. Follow the skill's
Language requirement: preserve original English disclosure captions and use
English workbook text by default. Never copy another company's extra tabs or
leave empty placeholders.

Each section is a wide panel: metrics down rows, chronological annual periods
on the left and quarterly periods on the right. Use one unfilled narrow
separator when both blocks exist. Distinguish source YTD cash-flow data and
derived discrete-quarter cash flows in separately labeled sections.

Keep related notes with their economic owner. Separate incompatible units,
scopes, reporting bases and restated segment definitions into labeled blocks.
Complete face statements belong in the workbook even if report prose is selective.

## Reading hierarchy

The operating-sheet hierarchy accepted on 2026-10-21 is the presentation baseline
for this skill. Adapt the actual groups and accounts to the issuer. Use the
following layers to make the workbook readable before applying colors:

1. **Worksheet title and shared period axis.** Show the company, the schedule,
   essential units and the financial-information as-of date once.
2. **Topic or reporting-basis section.** Separate subjects such as sales channels,
   customer countries, EBITDA reconciliations, and current versus legacy segments.
3. **Region or account subheading.** Choose the dimension the reader should hold
   constant while reading the following rows.
4. **Metric rows and meaningful totals.** Use concise account labels, aligned
   numbers, growth rows near their owning revenue and clearly styled subtotals.

Choose **region-first** when the reader needs a complete set of accounts for one
region. Choose **account-first** when comparison across regions is more useful.
Within a panel use one grouping consistently and present all applicable members.
Do not duplicate a complete view solely to show both orientations.

For example, replace repeated labels such as
`Europe & International | Revenue from external customers` with:

```text
Europe & International                 [region heading]
  Revenue                              [account subgroup]
    Revenue from external customers
    YoY change
    Intersegment revenue
    Total segment revenue
  EBITDA and adjustments               [account subgroup]
    Adjusted EBITDA
    Share-based compensation expense
    ...complete applicable accounts...
    EBITDA
```

An account-first panel instead places an account such as `Adjusted EBITDA` in
the heading and lists the regions below it. Pipes, slashes or repeated prefixes
must not serve as a substitute for these visible groups. Keep composite IDs and
full scope keys in the mapping metadata; preserve meaningful punctuation in an
actual account name. A short row label inherits its scope from the heading.

### Operating schedules and revenue bridges

| Schedule | Preferred reading structure |
|---|---|
| Segments | Separate reporting bases, then regional account panels or account panels containing the regions. Distinguish revenue, earnings/adjustments and totals within each panel. |
| Revenue and operations | Separate channel cross-classifications, country-of-customer geography, company-defined reconciliations and physical operating measures. A consolidated channel panel may precede regional channel panels. |
| Recurring revenue bridges | Comparable years/quarters across columns, with a region/scope heading and rows for reported revenue, the prior-year comparison, filed FX impact and constant-currency revenue. Put reported growth, constant-currency growth, volume and price/mix in a separate rate subgroup. |

For repeated annual/interim bridge disclosures, build the longitudinal matrix
rather than stack a copy of each filing's multi-level table. Align comparable
periods with the rest of the workbook. Use a distinct, clearly labelled YTD
panel and a local cumulative-period row when quarterly column headings otherwise
could be mistaken for discrete-quarter measures. Keep legacy reporting axes in
their own panel. Essential unit or sign-convention explanations belong once
beside the affected panel.

Remove redundant *presentations* when they repeat the same economic fact, such
as current reported revenue appearing twice in one bridge or an identical
schedule repeated in the same filing. Give it one visible owner and retain the
original locators in metadata, following the existing comparability rules.
Keep independently meaningful comparisons and components. Do not relabel a
repeated reported-revenue amount as a revenue increment.

Irregular schedules such as maturities, equity movements and instrument counts
may require their disclosed non-period axes. Design clear grouped headers and
row sections for those axes; native geometry is not a reason to reproduce raw
filing formatting, repeated units, note-reference columns or generic boilerplate.

## Approved design

The single machine-readable authority is
[style-profile.json](../assets/style-profile.json), approved 2026-10-19.
Use it in any authoring tool; do not clone uncoordinated constants.

| Role | Font and color | Minimum height |
|---|---|---:|
| Main title | Arial 14 bold, white on #1F4E79 | 28 pt |
| Section band | Arial 10 bold, white on #1F4E79 | 22 pt |
| Region/scope heading | Arial 10 bold, white on the profile's #20746C | 24 pt |
| Account subgroup | Arial 10.5 bold, #243447, thin light bottom rule, no fill | 24 pt |
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
Use a small gap between complete regional/account panels. Avoid a new colored
band for every ordinary metric. A color role should identify the same level of
hierarchy throughout the schedule.

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

Accept the layout only after checking representative openings, later groups and
long-label sections in the rendered saved workbook:

- The region/account grouping is evident without reading a concatenated key on
  every row. Headings identify the following complete group, not just its first
  item; labels return to the same left edge within each level.
- Annual/quarter columns line up across comparable panels. Cumulative periods,
  reporting bases and non-period axes are visible where they differ.
- Monetary bridge rows and percentage-driver rows are distinct. Repeated filing
  headers and duplicate presentations do not interrupt period comparisons.
- Labels wrap inside their own column at word boundaries. Increase only the row
  heights that need it; use explicit line breaks if the renderer lets text spill.
  Do not squeeze type, overlap a blank numeric column or stretch every row.
- Totals, group boundaries and modest whitespace make the reading order clear.
  Repeated unit/source boilerplate does not crowd out the financial content.

An opening range alone does not establish these checks: include another region
or account group, a legacy/YTD section when present, and a dense bridge or note
header. During a scoped restyle, review the changed views and preserve the
unrelated sheets rather than redesigning the whole workbook.

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
