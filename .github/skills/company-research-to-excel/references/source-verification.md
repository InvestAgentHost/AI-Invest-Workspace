# Source Verification — compact data, full checks

## Verification scope

This reference owns automatic check objectives. The concrete schema fields and
script gates describe the bundled route. Alternative methods and tool-limit
resolution follow [Agent judgment](../SKILL.md#agent-judgment-and-tool-boundaries).

Original 10-K/10-Q files remain authoritative and immutable. The compact schema
changes where metadata is stored, not the evidence standard:

- source file metadata once;
- table/view unit, scope, basis, version, period columns and row labels once;
- physical value coordinates generated automatically;
- only unusual sign/scale/period/mapping cases receive overrides and reasons.

Resolved evidence exists in memory during generation/audit. Do not serialize it
back as a mandatory full evidence object for each number.

## Automated checks

1. Reopen originals, verify hashes and native SEC forms.
2. Verify each shared table's original unit/scope context and exact row labels/
   period headings. Check unambiguous XBRL dates against the chosen interval;
   otherwise exact original heading locators and Agent semantic review are required.
3. Re-read EVERY mapped reported numeric value from the raw original, including
   native non-period schedules. Verify coordinates against the shared expanded
   fiscal column, then sign, percentage and scale normalization. Do not compare
   only against the same JSON used to generate the workbook.
4. Check numeric financial-body coverage in each selected table. data_rows defines
   the body once; title/blank/label-only rows require no manual disposition.
   Excluded financial rows need a reason. Unsupported shapes remain visible.
5. Check period continuity, original/recast selection, missing-value propagation,
   additive-quarter derivations, statement/segment/cash bridges and unit-specific
   rounding tolerances. Arithmetic agreement does not prove semantic correctness.
6. Compare all workbook inputs/formulas and engine-calculated caches. A
   recalculation flag or Python recomputation is not an Excel-engine result.

The auditor uses a separate raw read from the extraction bundle. Two parsers
agreeing is not proof that the right table, scope or year was chosen. Final
Review by an independent Agent is a required additional layer.

## Coverage without duplicated paperwork

The default coverage topics and configurable required_topics are documented in
[model schema](model-schema.md#one-coverage-matrix). Topic names are open; they
organize the review rather than prescribe a company's disclosure taxonomy.
Review the full requested history and latest interim. Note significant gaps,
scope/definition changes and replaced versions. Every selected source view must
appear in the same coverage record. Do not add row-count targets, a second layout
ledger or a status record for every HTML header.

Agent review must inspect relevant financial sections of every covered original
and each selected financial view; it must
challenge the coverage matrix, including what the extractor never selected.
A source/table catalog alone cannot prove completeness.

## Missing and exceptional data

Unknown is not zero. One missing subtotal input makes the result unavailable.
YTD is not a quarter. EPS/WASO/ratios/balances are not additive flows.
Official organic growth is not volume growth plus price/mix unless that exact
official disclosure exists. Keep GAAP, company-defined and analyst calculations
separate. Do not change tolerances or remove a failing row merely to obtain PASS.

Correct source/mapping/formula errors and repeat the affected checks. When the
tool itself is unsuitable, use the equivalent-check route in SKILL.md and retain
its actual results; a confirmed data conflict cannot be waived.

## Release gates

build_workbook.py performs declaration and raw-source gates before a normal
new-file build. --draft is a visible unverified preview. It does not perform the
final Agent review or calculate Excel caches.

verify_model.py reports automated_status and agent_review_status separately.
Without the actual Agent review file, overall status is UNVERIFIABLE even when
automated checks pass. PASS covers the scripted checks and review-record
binding and distinct declared producer/reviewer IDs, not proof that the review
occurred or that the workbook renders well. A different Agent must actually
perform the source-to-Excel review; visual QA also remains required before delivery.
A changed model/workbook invalidates the bound review.

After engine recalculation/save, the default automatic pass is:

~~~sh
.venv/bin/python .github/skills/company-research-to-excel/scripts/verify_model.py \
  <model.json> <final.xlsx> --report-json <verification.json>
~~~

It reports automated_status and supplies review_binding while Agent review is
pending. Complete [Agent data review](agent-data-review.md) and use its final
invocation to bind the reviewed artifact. Never auto-create a passed review
from these script results.

These script gates target an initial historical workbook, including its declared
sheet set and whole-file hash. An extended valuation workbook uses scoped checks
under the valuation skill. Preserve the earlier record's actual version/scope;
do not claim its old hash covers a changed file or add forecast data to the
historical model merely to satisfy this verifier.
