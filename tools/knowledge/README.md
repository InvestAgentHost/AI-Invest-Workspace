# LLM Knowledge Tools

## Article tags

`llm_tag_articles.py` sends one complete Markdown source article at a time to
the DeepSeek chat-completions endpoint and writes the returned free-form tags
into the article frontmatter.

The tool owns only tags beginning with `llm/`. Existing tags without that
prefix are preserved. A content/model/prompt-version cache is stored under
`knowledge/indexes/llm-tags/`, which is rebuildable and ignored by Git.

The workspace `.env` contains the local configuration keys. Put the actual
DeepSeek key in `DEEPSEEK_API_KEY`; `.env` is ignored by Git. The defaults are
the endpoint documented by DeepSeek, `deepseek-v4-flash`, JSON Output mode, and
enabled thinking with high reasoning effort.

```dotenv
DEEPSEEK_API_KEY=your-key-here
DEEPSEEK_API_URL=https://api.deepseek.com/chat/completions
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_THINKING=enabled
DEEPSEEK_REASONING_EFFORT=high
```

Validate the selected batch without calling the API:

```bash
python3 tools/knowledge/llm_tag_articles.py --dry-run --limit 3
```

Run one article first:

```bash
python3 tools/knowledge/llm_tag_articles.py \
  --slug nokia-nok-the-market-is-still-putting
```

Run the full current archive:

```bash
python3 tools/knowledge/llm_tag_articles.py
```

DeepSeek JSON Output must return an object containing a `tags` array. The model
is free to choose the tag vocabulary, but the prompt limits tags to short core
concepts and the tool normalizes formatting and rejects outputs outside the
3-8 tag range. Use `--thinking disabled` when a low-latency non-reasoning call
is preferred.
