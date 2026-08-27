# Output Contract

## 1. Required files

At minimum, a full-company package contains the following. Keep the main report at the
company directory root; the rebuildable context, ledgers, validation records,
and release-support files belong under the company-local `data/` directory,
which is ignored by Git:

```text
research/companies/<market>/<ticker>-<slug>/
  <report>.md
  data/
    research-context.md
    source-index.md
    evidence-ledger.md
    acquisition-attempt-log.md
    coverage-matrix.md
    validation-log.md
    release-review.md
```

Use `data/curated/` for small normalized inputs, mappings, metrics, and meeting-minute digests. Keep raw external material and large rebuildable artifacts under the source/data policy chosen for the workspace.

## 2. Report architecture

Use one H1 title, stable H2 chapters, and H3 subsections. Each chapter opens with a scope sentence. The default spine is:

1. Company identity and research boundary
2. Industry/economic context and competitive structure
3. Business model and operating units
4. Fundamental statements and accounting bridge
5. Derived fundamentals and balance-sheet economics
6. Capital allocation, management, and governance
7. Strategy, competition, advantages, and limits
8. Risk, stress paths, and monitoring
9. Valuation and shareholder return
10. Evidence gaps, limitations, balanced synthesis, and release status

Insert only relevant route modules. Do not add empty chapters to imitate another company.

## 3. Writing and tables

- Put reported facts before calculations, calculations before judgments, and assumptions/unresolved items visibly.
- Use tables for statement rows, segment bridges, route cards, KPIs, scenarios, sensitivities, coverage, and evidence status.
- Include period, unit, scope, formula/definition, and source ID in or immediately below every table.
- Cite material claims inline with `[Sxxx]`, `[T####]`, or `[calc:...]`.
- Use plain declarative language. Avoid promotional labels without a mechanism and falsification condition.
- Preserve contradictions, unavailable metrics, accounting nuance, and negative evidence.

## 4. Handoff checklist

Before declaring release, list source scope, dates, assumptions, unresolved questions, derived-data paths, tests, validator output, Git status, and final `PASS`/`PARTIAL`/`BLOCKED` decision. State explicitly whether the report is suitable for investment use or only for further research.
