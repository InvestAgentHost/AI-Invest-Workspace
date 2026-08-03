# Workspace Instructions

## Asset ownership

- Put durable research conclusions in `research/`.
- Put all externally acquired material in `sources/`; the entire directory stays outside Git.
- Put small reusable structured datasets in `data/curated/`; keep rebuildable datasets in `data/derived/`.
- Treat `knowledge/indexes`, `knowledge/databases`, collector state, and generated outputs as rebuildable artifacts.
- Keep tools independent from business data; tools may read and write the top-level data directories through configuration.
- Treat `sources/companies/<company-id>/inbox/` as a temporary drop zone. Organize its contents without requiring the user to classify files in advance.
- Keep company material originals in Workspace-relative paths. Do not redirect routine data writes to machine-specific external roots.

## Git and local data

- Track research Markdown, configuration examples, and small curated datasets.
- Do not newly track externally acquired PDF, Word, Excel, image, raw crawl, database, index, browser, or cache files.
- Keep ignored material discoverable through its company or platform directory and a tracked root-path note when useful.
- Preserve ignored materials when reorganizing. Never overwrite a same-name file; compare files and escalate conflicts.
- Manual archive transfer is the default cross-device method for ignored company materials. Do not introduce DVC, Git LFS, cloud storage, or automatic upload without an explicit user request.

## Research quality

- Record the as-of date for time-sensitive conclusions.
- Cite local source paths or original URLs for material claims.
- Separate source facts, analyst judgments, and model-generated inferences.
- Preserve contradictory evidence and unresolved questions.
- Do not overwrite raw source files during normalization.

## File conventions

- Use UTF-8 text files.
- Prefer stable ASCII directory identifiers and ISO dates.
- In company paths, use the investment or trading market rather than the issuer's incorporation country, such as `US` for a US ADR.
- Start new documents from `templates/` when a matching template exists.
- Do not commit secrets, local credentials, browser profiles, logs, indexes, or large generated databases.
- Use repository-relative paths in tracked files. Source-internal manifests may use paths relative to their own source root. Record original URLs separately from local paths.

## Obsidian

- The Obsidian Vault root is the parent of this repository; `.obsidian/` remains outside Git.
- Keep research notes and lightweight company entry notes readable in Obsidian.
- Keep `sources/`, indexes, browser profiles, and runtime files out of Obsidian search and graph through the Vault exclusion settings documented in `docs/obsidian-vault.md`.
- Do not use Obsidian Sync for `Workspace/` content; GitHub owns tracked content and manual archives own ignored material.

## Workspace skills

- Store repository-local skills under `.github/skills/`; do not create a parallel top-level `skills/` directory.
- Resolve Workspace-specific skills from `.github/skills/` before assuming they are unavailable.
- Keep `.github/` function-only: write Gangtise outputs under `sources/companies/`, never under `.github/workspace/`.
- Run vendored Gangtise scripts through the active Workspace interpreter and `tools/gangtise/run.py --output-subdir <market>/<ticker>-<slug> <skill> <script> [args...]`; do not invoke `.github/skills/gangtise-*/scripts/*.py` directly.
- Treat `tools/gangtise/run.py` as the durable Workspace policy layer: it loads `.env` and defaults `WORK_PATH` to `sources/companies`, so replacing or updating vendored Gangtise skills cannot redirect outputs into `.github/`.
- Update or restore vendored Gangtise skills by following `docs/gangtise-skill-update.md`; only the deterministic `tools/gangtise/normalize_skills.py` frontmatter adjustment is allowed inside `gangtise-*` directories.

## Python runtime

- Treat `.venv` as the canonical Python environment for Workspace tools, collectors, validators, tests, and scheduled tasks.
- On macOS/Linux use `.venv/bin/python`; on Windows use `.venv\Scripts\python.exe`.
- Run package installation through the selected `.venv` interpreter with `-m pip`; do not rely on an unverified system Python.
- Document and configure Workspace paths relative to the repository root; do not hardcode machine-specific absolute paths.
