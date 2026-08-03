---
name: company-material-intake
description: Organize user-dropped PDF, Word, Excel, image, Markdown, and other research materials from a company's source inbox; classify originals within the isolated source tree; preserve provenance when available; and report the folder to transfer. Use when the user asks to organize, archive, check, or clean up newly added company research materials.
---

# Company Material Intake

Follow `docs/company-materials.md` and the target company's `company.yaml`.

## Resolve the company

1. Find the company under `research/companies/<market>/<ticker>-<slug>/`, using the investment or trading market.
2. Read `company.yaml` and `materials.md` when present.
3. If either file is missing, create it from `templates/company.yaml` or `templates/materials.md` using known company facts. Ask only when the stable identity or ticker cannot be determined safely.
4. Use only Workspace-relative paths. Do not introduce an external data root.

## Inspect the source inbox

1. List every file recursively, excluding `.gitkeep`.
2. Detect the real file type; do not rely only on the extension.
3. Detect obvious duplicates by filename, size, and content hash when needed to avoid overwriting; do not build a permanent hash catalog.
4. Read enough content to classify the material. Use the relevant PDF, document, or spreadsheet capability when available.
5. Never print credentials, hidden workbook secrets, browser data, or unrelated personal content.

## Classify and archive

Use the destinations declared in `company.yaml`:

- External filing, announcement, report, presentation, transcript, manual, or article: the matching company subtree under `sources/companies/`.
- External structured table or exported dataset: company `structured-data/` or the matching provider subtree under `sources/providers/`.
- User-created binary valuation or forecast model: company `models/` under `sources/`.
- User-created Markdown analysis and durable conclusions: company research directory.
- Delivery report, one-page brief, presentation, or export: `outputs/`.
- Unclear external material: company `user-materials/` with incomplete provenance.

Preserve the original file. Do not normalize over it. Never overwrite a same-name file; compare hashes and, if different, keep both with a stable date or hash suffix. Ask the user only when the choice between external material and a user-created model is materially ambiguous.

## Record provenance

Preserve provenance already present in filenames, companion files, download metadata, or source URLs. Do not require a row, manifest, or hash entry for every file. Keep `materials.md` limited to the Workspace-relative company source root and genuinely useful unresolved notes.

## Finish safely

1. Confirm `inbox/` contains only unresolved files and `.gitkeep`.
2. Run `git status --short` and `git check-ignore -v` for moved source files.
3. Confirm all files under `sources/` remain ignored by Git.
4. Report organized, duplicate, unresolved, and conflicting items separately.
5. List the exact Workspace-relative directories that the user should manually compress for cross-device transfer. Do not upload, delete, or create a transfer archive unless explicitly requested.
