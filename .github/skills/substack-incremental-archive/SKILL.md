---
name: substack-incremental-archive
description: Fetch and archive new Substack posts through a manually authenticated visible Edge session, including paid-member content, incremental deduplication, local HTML/Markdown/image preservation, and metadata validation. Use when asked to scrape, update, or retrieve new posts from damnang2.substack.com or another configured Substack publication.
---

# Substack Incremental Archive

Use the repository's Substack collector. Keep browser authentication outside the
repository and keep article data under Workspace-relative `sources/` paths.

## Data Layout

The configured `damnnang` profile writes to:

`sources/publishers/substack/damnnang/`

- `raw/html/`: preserved article HTML.
- `normalized/markdown/`: cleaned Markdown with source URL frontmatter.
- `assets/images/`: downloaded article images.
- `state/manifest.json`: incremental URL/slug manifest.
- `state/posts/`: per-post metadata and plain extracted text.

Do not put cookies, browser profiles, tokens, or credentials in the repository.

## Workflow

1. Read `tools/collectors/substack/config.json`. Confirm the profile's
   `base_url`, `archive_url`, `output_dir`, and `cdp_url` are correct. The
   `damnnang` profile must use `https://damnang2.substack.com` and the relative
   output path above.

2. Start a visible isolated browser. Do not use headless mode for paid posts:

   ```powershell
   powershell -ExecutionPolicy Bypass -File tools/collectors/substack/start_debug_browser.ps1 `
     -Port 9222 `
     -UserDataDir "$env:TEMP\substack-member-browser" `
     -StartUrl "https://damnang2.substack.com/?utm_campaign=profile_chips"
   ```

   Reuse the same temporary user-data directory for future runs so the user
   does not need to log in every time. Never copy that directory into the repo.

3. Ask the user to log in manually in that window. Continue only after the user
   confirms login. Verify `http://127.0.0.1:9222/json/version` before running
   the collector.

4. Repair the newest post if it may have been captured before login or marked
   inaccessible:

   ```powershell
   python tools/collectors/substack/main.py `
     --config tools/collectors/substack/config.json latest --overwrite
   ```

   Use `latest` without `--overwrite` only when the manifest already contains a
   verified accessible newest post.

5. Fetch all new posts incrementally:

   ```powershell
   python tools/collectors/substack/main.py `
     --config tools/collectors/substack/config.json archive
   ```

   The collector uses `state/manifest.json` to skip existing slugs. Do not
   delete the manifest to force a refresh. Use `single URL --overwrite` for
   one explicitly requested article.

6. Validate the result. Check the command summary, then inspect each newly
   saved `state/posts/<slug>.json`. Require `is_accessible: true` for a paid
   article, a non-empty text length, the expected source URL, and a matching
   Markdown file. Treat an inaccessible result as a login/session problem and
   do not report it as a complete scrape.

7. Report the number fetched/skipped, titles, publication dates from the saved
   metadata or visible article header, and local Markdown paths. Mention any
   paywall, missing image, or archive-coverage limitation. Leave the isolated
   browser running if another incremental run is likely soon.

## Collector Details

The collector lives in `tools/collectors/substack/`. Its `archive` command is
the normal incremental operation; `latest --overwrite` is the recovery step
for content previously fetched without the member session. Its output is
rebuildable source data, not research conclusions: cite the saved original URL
and preserve contradictory or inaccessible source states rather than silently
replacing them.
