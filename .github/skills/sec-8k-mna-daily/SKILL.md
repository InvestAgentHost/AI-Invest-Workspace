---
name: sec-8k-mna-daily
description: Run, diagnose, or schedule the AI Invest Workspace SEC 8-K merger and restructuring monitor. Use when the user asks to scan a watchlist for SEC 8-K M&A or material restructuring events, retry failed classifications, inspect the resulting Chinese daily report, or create a Codex recurring task for this monitor.
---

# SEC 8-K M&A Daily

Use the existing workflow. Do not recreate the collector or move its state.

Workspace root: `.`

## Run

1. Confirm `python` exists and uses Python 3.12. Do not print `.env` or API keys.
2. Run from the Workspace root:

```bash
python -m tools.sec_8k_mna.cli daily --lookback-hours 36
```

3. Read `research/sec_8k_mna_daily/<Asia-Shanghai-date>.md` and report the high-confidence events in Chinese. Preserve SEC evidence quotes in their original language.
4. State whether the daily report was updated and identify failures separately. Do not disclose local absolute paths, source directories, credentials, or other host information. Do not claim that a zero-candidate deduplicated run means the report has no historical event; the report is rebuilt from the classification index.

## Retry

Use this only when the user asks to retry failed LLM or request errors:

```bash
python -m tools.sec_8k_mna.cli daily --lookback-hours 36 --retry-failed
```

## Configuration

- Watchlist: `data/watchlists/sec_8k_targets.txt`
- LLM configuration: Workspace `.env`; keep credentials private.
- Current Aigocode model ID: `gpt-5.6-luna`. Do not substitute `gpt-5.6-luna-high`; it is not returned by Aigocode's `/v1/models` endpoint for this key.
- Relevant filings are archived under the data root configured by `config.yaml`; only high-confidence relevant filings are saved.

## Scheduling

For Codex “已安排”, create a standalone local recurring job against this Workspace. Its prompt must invoke this Skill's Run procedure, read the daily report, and send a concise Chinese result. Use the user's requested time and Asia/Shanghai timezone; ask for the time if it is not provided. Do not create duplicate automations.
