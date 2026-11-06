# Source Acquisition and Preparation

## 1. Source boundary

### Filing and financial-data acquisition: SEC originals only

- Discover the issuer, filing inventory and latest actual period directly through SEC official public endpoints (`www.sec.gov`, `data.sec.gov`). Acquire original EDGAR filings, notes and exhibits, including 10-K/10-Q/8-K, amendments, relevant IPO registration statements/prospectuses and, where applicable, 20-F/6-K.
- Do not call FocusAlpha or any other third-party service for identity/filing discovery, coverage checks, normalized financials, extracted sections or missing periods. Do not use third-party mirrors, transcripts, search snippets or provider-processed caches to populate this acquisition package. This skill's SEC route takes precedence over generic provider-first routing.
- A prior local file is reusable only when its provenance establishes a direct SEC download of the original document. Record the official URL, accession, filing/report dates and hash; preserve it unchanged. A provider excerpt that cites SEC is not a SEC original. Reacquire unverifiable files directly from SEC or record the gap.
- Use complete filed HTML/iXBRL and exhibits as the evidence base. Official SEC XBRL datasets may assist discovery and checking but do not replace the original filing, statement tables or notes. Local extraction is permitted when every value remains traceable to the original.
- If SEC access fails, record attempts and retries and report the remaining gap. If the issuer has no SEC coverage, disclose that scope limitation; do not silently change to a provider or a different filing regime.

### First-party supplements and later analysis

- When requested, acquire company/brand website pages, IR releases, presentations and company-published transcripts from verified official domains. Keep them separate from SEC originals and label them as company-reported. Use an EDGAR exhibit for financial disclosure when available; website material does not substitute for the filed actuals.
- Independent industry, government, regulatory or market evidence may be scoped in a later analysis module; it is not an automatic third-party fallback for this acquisition route. A task-level prohibition on third-party sources applies to the whole task. Processing a specifically supplied transcript in a separately authorized task does not authorize acquiring third-party minutes here.
- Search-result snippets are discovery aids, not evidence. A company page is a company claim unless independently corroborated.

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

- Check source eligibility before accepting coverage: every financial filing must resolve to its SEC original and accession; company-site supplements must resolve to an official domain. Quarantine references to ineligible provider-derived material from the new package without deleting historical files.
- Preserve original filename when safe and add a collision suffix instead of overwriting.
- Extract only the tables/pages needed, while retaining row order, labels, units, signs, blanks versus zero, comparative/restated status, and note references.
- Visually inspect tables when columns, footnotes, continuation pages, OCR, or translations can change meaning.
- Hash source files when practical and regenerate a manifest with `scripts/build_source_manifest.py`.
- Keep raw external files under `sources/` and rebuildable prepared artifacts out of Git according to repository policy.
- Before prose, ensure every material conclusion can point to a source ID plus locator or is explicitly labeled an analyst inference.
