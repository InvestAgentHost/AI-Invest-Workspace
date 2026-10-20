# Independent Agent Data Review

A different Agent reviews the final workbook directly against original
10-K/10-Q files after construction and applicable automatic checks. The producing
Agent's own second pass does not satisfy this independent review. One reviewer
is sufficient; a different model or a new user-facing chat is unnecessary.

## Lightweight handoff and independence

Delegate to a fresh Agent with the requested period/as-of scope, original filing
index/paths, final recalculated Excel path, relevant metric rules and the existing
review-record path. Supply the actual producer Agent ID. When using spawn_agent,
use fork_turns="none" and pass these inputs explicitly. Do not pass the full
production conversation, expected conclusions or the producer's reasoning.

The reviewer first forms its own reading from the ORIGINAL filings and Excel.
Source mappings/model.json and automatic findings are navigation and follow-up
aids, not the authority for deciding whether data are correct or complete.
Use targeted source-section/table reads and search; a second full extraction or
workbook build is unnecessary. The reviewer may choose its own parsing and
calculations for direct checks. It reads original data and workbook values/formulas
without editing them, and writes one concise
review.json containing findings and its conclusion. Existing source catalogs,
locators and final-version hashes are reused; no separate handoff dossier,
per-cell checklist, extra workbook copy or additional approval is required.

If another Agent is unavailable, report independent review as pending. Do not
label self-review independent or manufacture reviewer identity. Tooling cannot
prove that a reviewer actually inspected files; a generated record is not review.

## Review focus

The following themes guide judgment; they are not six ordered production stages
or a requirement to invent inapplicable metrics.

1. **Coverage.** For every source, inspect face statements and the material MD&A/
   segment/product/geography/note disclosures. Compare original financial rows
   with the exported base, covering the whole requested history and latest
   interim. Look for tables the extractor omitted, not only misplaced exports.
2. **Periods, units, scope.** Read all heading levels. Distinguish annual,
   three-month, YTD and instant data; millions/thousands/shares/per-share values;
   consolidated, segment, Corporate and eliminations; crossing geography/product
   axes. Check actual fiscal calendars and start/end stock dates.
3. **Versions and labels.** Verify recast/reclassification precedence and evolving
   segment definitions. Check that similarly named accounts are economically
   comparable and that company-defined/non-GAAP figures are genuinely reported.
4. **Derivations.** Inspect signs, source-normalization exceptions, Q4/TTM logic,
   share/EPS nonadditivity, actual-tax NOPAT, operating IC investment/cash
   deductions and overlap, NWC classification, capex/FCF and average-balance dates.
   Adapt to the issuer rather than force irrelevant metrics.
5. **Anomalies.** Challenge order-of-magnitude jumps, sign reversals, flat repeated
   series, zero/missing clusters, unusual margins/growth and nonreconciling
   segments. Return to notes for plausible transaction/reclassification causes;
   a plausible explanation does not excuse a wrong source mapping.
6. **Workbook consistency.** Inspect the final Excel against the originals,
   including headline revenue/profit/assets/cash flows, taxes, debt/cash,
   investments, shares/EPS/SBC, major cash distributions and source exceptions.
   Verify first/middle/latest history and recent periods. All mapped numbers
   remain subject to automated full reread; manual inspection adds semantic
   judgment rather than replacing it with a smaller sample.

Read each selected source view's original headings and financial rows. Ordinary,
consistent data needs no cell-by-cell written confirmation. Put effort and notes
into material ambiguities, transformations and anomalies. Keep one concise
review record; do not recreate the large per-value evidence schema.

## Corrections and recheck

A discrepancy must lead to a correction or a precise unresolved finding.
The producer fixes the data/mapping/exception/formula and reruns affected
automatic checks. The same reviewer then rechecks the changed scope and related
totals in the final saved/recalculated workbook, closes supported findings and
updates the bound record. Unchanged areas need no repeated full review. The
producer cannot approve its own fixes on the reviewer's behalf. Never edit the
original filing, invent a reported metric or approve a numeric conflict because a trend seems
plausible. If a parser cannot represent the source, manually establish the
correct interpretation and record its exact evidence/remaining limitation.

Resolve tool limitations under [Agent judgment](../SKILL.md#agent-judgment-and-tool-boundaries).
The review record can hold the scope, locator, replacement check and result;
do not create another exception ledger. Genuine remaining uncertainty stays open.

## Minimal record

The following review.json is the bundled verifier's format. An alternative
route may reuse its existing concise review record, identifying the final
artifact/version, distinct producer/reviewer identities, source coverage, actual
checks, exceptions and conclusion. Do not create a second record only to satisfy
a tool-specific schema. Independent-Agent review applies on both routes.

Get data_fingerprint and workbook_sha256 from the verification report's
review_binding. They are generated, not hand-invented. The reviewer creates or
updates review.json from its actual checks; status stays pending until complete.
Use actual runtime Agent/session identifiers, not fictional role labels.

~~~json
{
  "status":"pass",
  "reviewer":{"agent_id":"<reviewer Agent ID>","producer_agent_id":"<producer Agent ID>"},
  "data_fingerprint":"<copy current generated fingerprint>",
  "workbook_sha256":"<copy final workbook hash>",
  "reviewed_sources":["F_2025_10K"],
  "reviewed_tables":["IS_2025","BS_2025","CF_2025"],
  "checks":[
    "coverage","periods_units_scope","versions_and_labels",
    "derivations","anomalies","workbook_consistency"
  ],
  "findings":[],
  "summary":"Concise actual review conclusion; mention important corrections, source exceptions or remaining limitations."
}
~~~

List ALL sources/tables in the requested model, not only these examples.
For an issue record location, issue, status and resolution. Open findings block
PASS. Resolved findings state what changed and why. No issue requires no
fabricated finding. Do not auto-populate pass or all check themes from script
results; the reviewer records them only after its independent semantic review.

Final invocation:
~~~sh
.venv/bin/python .github/skills/company-research-to-excel/scripts/verify_model.py \
  <model.json> <final.xlsx> --agent-review <review.json> \
  --report-json <verification.json>
~~~

Any changed model data/mapping/formula/source or saved workbook invalidates the
old binding. Review the changed scope and bind the final version again; do not
copy old hashes into a new approval record without reviewing the affected data.
