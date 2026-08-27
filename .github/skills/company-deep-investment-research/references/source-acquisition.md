# Source Acquisition and Preparation

## 1. Source hierarchy

Use the narrowest authoritative source that answers the question:

1. SEC filings and footnotes, exchange filings, and audited annual reports.
2. SEC 8-K exhibits, earnings releases, investor presentations, and official Q&A.
3. Official product, organization, policy, and investor-relations pages.
4. Faithfully prepared earnings calls, conferences, and other transcripts.
5. Government, regulator, standards body, utility, customer, supplier, or independent industry data.
6. Dated market data used only for a valuation boundary.
7. Other provider or alternative data only when the user supplies the source and provenance.

Search-result snippets are discovery aids, not evidence. A company page is a company claim unless independently corroborated.

## 2. Source record

Use a stable ID such as `S001` for documents and `T0001` for transcript turns. `source-index.md` should contain at least:

```text
source_id | category | title | issuer/provider | content_date | accessed_at |
original_url_or_reference | local_path | sha256 | extraction_method |
locator_scheme | usability | notes
```

For PDFs record printed page and PDF page when they differ. For HTML record section, table, anchor, or line range. For transcripts cite the published artifact and `T####` turn.

## 3. Bundled ResearchFoundry bridge

Use the bundled `scripts/research_foundry_local.py` bridge. It locates the runtime relative to the skill, so no machine-specific checkout path is needed. Use these validated flows:

```text
ten-k sec-html: plan --confirm -> run -> inspect -> index/search/read
transcript: plan or plan-metadata --confirm -> run -> publish -> inspect
official-site: plan -> run -> publish -> inspect -> search/read
```

For manually uploaded transcript material, collect target, event date, event type, fiscal applicability, source path, and workspace before creating a plan. Never infer event dates from file modification time. Preserve wording, qualifications, numbers, repetitions, prepared remarks, and Q&A; use neutral speaker labels when identity is uncertain. A provider-prepared minutes source is not a raw transcript and must retain that limitation.

For SEC HTML and official-site snapshots, preserve raw input and use the prepared artifact only after inspect/validation. User-supplied PDFs may be retained as raw evidence or processed by a separately approved tool, but this skill does not infer or silently substitute a PDF text-extraction method.

## 4. Manual and web intake

For each search or acquisition attempt log:

```text
attempt_id | research_question | criticality | source_category |
query_or_page | accessed_at | result | selected_source_id |
rejection_or_failure | next_step
```

Keep rejected sources when they reveal a limitation, contradiction, blocked access, stale date, or wrong legal entity. Do not overwrite an earlier snapshot; add a date or run suffix.

## 5. File and quality checks

- Preserve original filename when safe and add a collision suffix instead of overwriting.
- Extract only the tables/pages needed, while retaining row order, labels, units, signs, blanks versus zero, comparative/restated status, and note references.
- Visually inspect tables when columns, footnotes, continuation pages, OCR, or translations can change meaning.
- Hash source files when practical and regenerate a manifest with `scripts/build_source_manifest.py`.
- Keep raw external files under `sources/` and rebuildable prepared artifacts out of Git according to repository policy.
- Before prose, ensure every material conclusion can point to a source ID plus locator or is explicitly labeled an analyst inference.
