# SEC 8-K M&A Workflow

This tool reads SEC submission metadata for tickers in the watchlist, checks
candidate 8-K filings with an OpenAI-compatible LLM provider, and only archives
filings classified as high-confidence merger or restructuring events.

It requires Python 3.12. The Workspace `.venv` is the canonical interpreter for
the commands below.

## Setup

1. Add tickers to `data/watchlists/sec_8k_targets.txt`.
2. Copy values from `config.example.json` into an optional local JSON config if
   non-default paths are required. Do not put secrets in that file.
3. Set these local environment variables or place them in the ignored workspace
   `.env` file:

```text
SEC_USER_AGENT=AI-Invest-SEC8K/1.0 contact@example.com
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=...
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=...
```

To use a GPT model through Aigocode, change `LLM_PROVIDER=aigocode` and set
`AIGOCODE_API_KEY`, `AIGOCODE_BASE_URL`, and `AIGOCODE_MODEL` according to the
Aigocode OpenAI-compatible API documentation.

## Commands

```bash
# Query SEC metadata only. No filing text or LLM request.
python -m tools.sec_8k_mna.cli candidates --lookback-hours 36

# Full daily workflow.
python -m tools.sec_8k_mna.cli daily --lookback-hours 36

# Verify candidates and configuration without writes or LLM calls.
python -m tools.sec_8k_mna.cli daily --lookback-hours 36 --dry-run
```

To test one historical filing without analyzing every candidate in a long time
window, add its accession number:

```bash
python -m tools.sec_8k_mna.cli daily \
  --lookback-hours 9000 \
  --accession 0000050863-25-000107
```

The full command creates raw and Markdown source files only for an
evidence-backed `high_confidence` event. A `needs_review` event is listed in the
daily report and index, but its filing text is not retained.

Run tests with:

```bash
python -m unittest discover -s tools/sec_8k_mna/tests -v
```
