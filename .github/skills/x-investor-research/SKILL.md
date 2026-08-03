---
name: x-investor-research
description: Retrieve and analyze cited X posts from the local investor archive. Use when asked about ShanghaoJin or another configured X investor's historical views, thesis changes, statements on companies, sectors, macro themes, or evidence-backed comparisons over time.
---

# X Investor Research

Use the local SQLite index as the evidence source. Do not treat the Skill file,
search snippets, or model memory as source evidence.

## Retrieve

Run `scripts/retrieve_posts.py` from the workspace. It reads
`tools/collectors/x/config.json` and returns JSON with target-author posts,
dates, URLs, source paths, media, and optional relationship context.

```powershell
python .github/skills/x-investor-research/scripts/retrieve_posts.py --query "AI 资本开支" --top-k 10 --include-context
```

Defaults retrieve only `original,quote`, which are the active-post research
set. Add replies only when the question requires conversation detail:

```powershell
python .github/skills/x-investor-research/scripts/retrieve_posts.py --query "ORCL" --types original,quote,reply --start 2025-01-01 --top-k 12 --include-context
```

Use a narrow time range for period comparisons. If the first retrieval is not
specific enough, refine terms or run separate queries; do not increase
`--top-k` before refining the query.

## Analyze

1. Separate the investor's stated view from model interpretation.
2. Order evidence by `created_at` before describing a change in view.
3. Cite each material claim with the post date and `url`.
4. State contradictions, missing periods, and archive coverage limits.
5. Do not infer a position from a repost unless it is explicitly requested.
6. Treat quoted or parent-post text as context, not as the investor's own
   statement unless the target-author post states the view.

Use this response shape when it fits the question:

```text
金老师观点
- ... [date, URL]

证据
- ... [date, URL]

AI 分析
- ...

不确定性
- ...
```

## Token Control

Keep `--top-k` at 8-12 by default and use the script's snippets. Expand a
specific post with `--snippet-chars` only when its full wording is necessary.
Use `--include-context` only for replies or quotes that need interpretation.
