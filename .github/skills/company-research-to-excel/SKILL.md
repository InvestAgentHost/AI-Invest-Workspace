---
name: company-research-to-excel
description: Build historical research Excel from original 10-K/10-Q filings, with source-linked actuals, formula-derived metrics, financial checks and data review by an independent Agent. Adapt extraction and workbook organization to issuer disclosures while preserving accuracy and the approved style. Valuation extensions use their separate route.
---

# Company Research To Excel

Build the historical workbook an analyst can use as the main window into the
company's official disclosures. Understand what each disclosure measures, cover
the requested history and latest interim, and connect statements, operating
data and material notes. Scripts assist the Agent; they do not determine
economic comparability or disclosure completeness.

## Scope and fixed requirements

This route covers **original 10-K/10-Q → historical actuals and derived metrics**.
Use the available data-preparation package. Do not expand into source acquisition,
8-K/releases, transcripts, forecasts or valuation unless separately requested.
This skill owns historical actuals, historical derived metrics, data quality and
the shared workbook visual profile. [valuation-binding-methodology](../valuation-binding-methodology/SKILL.md)
owns forecasts, valuation methods, assumptions, model formulas and valuation
checks. Spreadsheet tools execute file edits for either task. The valuation
section below is a handoff, not an additional forecasting or valuation rulebook.

- **Source authority.** Original filings and identified amendments outrank cleaned
  Markdown, JSON/CSV, previous reports and previous Agent output. Bind every
  reported value to its original location and period/unit/scope/version. Another
  company's workbook supplies layout ideas only.
- **Language.** For English-language filings, keep the workbook in English by
  default, regardless of the conversation or research report language. Retain
  original English captions for reported accounts, segments and disclosures;
  do not automatically translate them into Chinese. Use concise English for
  sheet names, navigation, units, analyst-defined metrics and explanatory notes.
  Preserve meaningful source wording and scope differences when harmonizing
  comparable rows; distinguish analyst-added labels from issuer disclosures.
  Follow an explicit user language preference when provided.
- **Coverage.** Preserve the requested history, complete in-scope face statements
  and economically material supporting disclosures. Do not silently replace a
  long history with the latest three comparative years. Review relevant MD&A,
  segment, geography/product and note sections; an extractor's selections do
  not establish completeness.
- **Financial meaning.** Separate reported figures, company-defined measures and
  analyst calculations. Missing is not zero; YTD is not a discrete quarter.
  Keep incompatible units, scopes, reporting axes and recast definitions
  distinct. Do not manufacture an official organic-growth figure from volume
  growth plus price/mix.
- **Accuracy.** Reopen originals for all mapped reported values, apply appropriate
  financial reconciliations, and check formulas and engine-calculated results.
  Have a different, independent Agent directly review originals and the final
  workbook, following [Agent data review](references/agent-data-review.md).
  Script success alone is insufficient.
- **Appearance.** Design a research workbook with a visible reading hierarchy:
  topic/reporting basis → region or account group → concise metric rows. Put a
  repeated region/account dimension in a heading rather than concatenate it into
  every metric label. Organize recurring disclosures into comparable period
  panels instead of reproducing filing tables. Retain the accepted visual profile,
  readable content-fitted heights, functional tab colors and compact Contents.
  Keep unavailable values blank and technical evidence outside the reader-facing
  workbook; no mass source comments or index tabs. Read the
  [workbook contract](references/workbook-contract.md#reading-hierarchy) before
  authoring; it owns layout and visual acceptance.
  [style-profile.json](assets/style-profile.json) owns design constants.
- **Assets.** Keep originals immutable under sources/, company outputs under the
  company's outputs/, and durable metadata paths Workspace-relative. Do not
  newly track generated XLSX or rebuild a user-edited workbook from stale JSON.

## Agent judgment and tool boundaries

The Agent chooses material notes/KPIs, comparable series, supporting sheets,
extraction/authoring tools and economically applicable checks. Default categories,
check groups, model.json v4 and the bundled expression language are **tool
interfaces**, not a universal financial ontology or compulsory production path.
Routine choices need no new approval; explain meaningful departures briefly.

Use native HTML/XBRL/text, original-page reads, company-local adapters or another
spreadsheet authoring method when appropriate. Preserve the same source-to-value
trail, approved formatting and equivalent checks. Keep one-off adaptations with
company outputs rather than turn them into rules for every issuer. Do not create
extra metadata or intermediate files merely to satisfy a generic script.

A wrong value, missing evidence or unexplained material bridge is a data problem.
An unsupported layout or inapplicable generic check is a tool limitation. Resolve
the latter using a suitable check or direct original-source verification of the
affected values and related totals, then include it in Agent review. Record the
scope, locator, method and result concisely. Preserve the script's actual result;
distinguish automatic verification, Agent-verified exceptions and unresolved
data. A tool limitation alone does not block a properly verified workbook, and
a review cannot waive a confirmed data conflict.

## Working approach

Establish the requested period/source window and original/recast precedence
before organizing data. If no window is specified, use the package's supported
history and latest interim, and state that window. Use **one coverage record**, shared table context,
value-level coordinates and reasoned exceptions. Do not maintain duplicate
coverage ledgers or full audit dossiers for every cell.

Construct the workbook around separate IS/BS/CF sheets, adding economically
useful schedules supported by the filings. Choose regional or account grouping,
the visible subheadings and the time axis before populating cells; a separate
layout-plan file is optional. Each comparable fact has one
calculation owner; link repeated presentations while retaining independently
reported totals for reconciliation. Equal numbers alone do not prove equal
scope. Headline revenue/profit series include formula YoY rows; other ratios
should explain the business rather than decorate every line.

Derived metrics link reported cells through Excel formulas. Follow
[derived metrics](references/derived-metrics.md) and its authoritative research
definitions for operating IC/ROIC, NWC, cash flow and returns. Do not silently
replace an agreed definition with a conventional alternative.

On the default route, collect native candidates, map selected financial views,
assemble a draft, resolve gaps and build a new workbook. Recalculate with an
available spreadsheet engine, check the saved workbook, then delegate independent
data review and complete visual QA. Adapt or combine operations when another route fits;
the dependencies and quality objectives matter, not a fixed sequence of
commands. Setting recalculation flags is not engine recalculation.

Read supporting resources only when needed:

| Task | Resource |
|---|---|
| Discover originals; use collector/assembler/build commands | [Input contract](references/input-contract.md) |
| Map default v4 data, periods, formulas and configurable coverage/checks | [Model schema](references/model-schema.md) |
| Place disclosures and preserve economic ownership | [Semantic layout](references/semantic-layout.md) |
| Implement agreed financial definitions | [Derived metrics](references/derived-metrics.md) |
| Apply approved styling and inspect rendered sheets | [Workbook contract](references/workbook-contract.md) |
| Reopen sources; verify values, bridges and formula caches | [Source verification](references/source-verification.md) |
| Review omissions/meaning and bind the final artifact | [Agent data review](references/agent-data-review.md) |

When actually authoring/recalculating/rendering a workbook, also use the platform
spreadsheet skill and available runtime. They must preserve this skill's profile.

## Completion

Deliver one current research workbook under the company's
`outputs/company-research-to-excel/` directory, without dated duplicate export
folders, and a concise coverage/status note with material unresolved items.
Reserve `outputs/workbooks/` for finalized workbooks when the user requests
finalization. Keep necessary mappings/evidence/review metadata discoverable
under company data/derived paths. Use temporary rendering and clean preview
PNGs, one-off scripts and Agent-owned superseded exports from outputs; preserve
unrelated outputs and the user's edits. Do not send intermediate files by default.

The bundled verifier reports automatic checks and the bound Agent-review record
separately. Its PASS does not certify rendered appearance; the Agent completes
visual QA before delivery. Another route supplies equivalent evidence and
review, without a second ledger solely for serializer compatibility. Missing
engine results, unreviewed disclosures and unresolved source conflicts remain
explicit limitations, never implied passes.

## Valuation handoff

For an explicit valuation request, transfer to
[valuation-binding-methodology](../valuation-binding-methodology/SKILL.md) and its
[workbook contract](../valuation-binding-methodology/references/workbook-contract.md).
Historical export needs no forecast parameters or valuation sheets.

- Reuse the latest saved workbook, historical source/index records, metric
  definitions and period/unit metadata. Include known gaps and manual edits;
  reuse existing records rather than create a new handoff dossier.
- Valuation sheets link the existing actual/derived cells. Correct historical
  gaps under this skill's data requirements; keep forecasts distinct from actuals.
- New or modified valuation sheets use the same
  [visual profile](assets/style-profile.json) and approved design in this skill's
  [workbook contract](references/workbook-contract.md). Their content and layout
  are owned by the valuation skill; do not reimplement its rules here.
- Use scoped spreadsheet edits with a recoverable version, preserving manual
  inputs, historical sheets and native features. The initial generator is not
  an updater for an extended workbook. Recalculate and verify the changed scope;
  retain the historical verification's version boundary rather than claim its
  old whole-file hash validates the extended workbook.
