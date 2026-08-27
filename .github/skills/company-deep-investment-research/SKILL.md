---
name: company-deep-investment-research
description: Build, refresh, or audit a provenance-preserving deep investment research package for a public company, including language-triggered reconstruction of multi-year statements and note-table time series. Use when the task needs multi-year SEC filings, latest interim disclosure, official IR and website evidence, cleaned earnings or conference transcripts, business-model routing, three-statement reconstruction, industry or theme analysis, SOTP or route-appropriate valuation, shareholder IRR, and an independent release review. This skill includes a bundled ResearchFoundry data-preparation runtime and local bridge; it is not for a quick company summary, a website crawl alone, or an isolated ratio calculation.
---

# Company Deep Investment Research

Use this skill as the research lead for a public-company deep dive. The output is a durable Markdown report under `research/`, supported by raw external material under `sources/` and small, reproducible data under `data/curated/` or `data/derived/`.

## Operating contract

- Read the repository `AGENTS.md` before changing files and preserve unrelated user work.
- Establish issuer identity, ticker, market, CIK, fiscal year end, accounting basis, consolidation perimeter, currency, units, history window, latest interim filing, as-of date, output paths, and research questions before acquisition.
- Prefer SEC filings and official IR material. Treat the company website and management statements as company-reported; use independent sources for corroboration, contradiction checks, industry context, and dated market inputs.
- Keep raw inputs immutable. Every material source needs a stable source ID, original URL or provider reference, local path, access date, content date, SHA-256 when practical, extraction method, and page/turn/line locator.
- Separate `source fact`, `company claim`, `analyst calculation`, `analyst judgment`, `model assumption`, and `unresolved question` in both ledgers and prose.
- Adapt the economic route to the issuer. Do not assume SaaS, market share, cohorts, customer concentration, backlog conversion, product margins, utilization, or a theme-specific revenue split without evidence.
- Use `unavailable` for relevant but undisclosed metrics and `n.a.` for economically irrelevant metrics. A real evidence gap must remain visible and lower the affected gate to `PARTIAL` where material.
- Do not copy facts, business assumptions, numbers, valuation, or conclusions from a reference company. A reference report may inform sequence, evidence organization, table design, and review criteria only. Run a reference-leakage scan before release.
- Do not ask the user to execute internal ResearchFoundry commands. The agent invokes available tools and reports outcomes; ask for confirmation only when source identity, metadata, permissions, or a materially different valuation boundary is ambiguous.

## Workflow

Follow the stages in order. Load the linked reference only when that stage is active.

1. **Stage 0 - identity and scope.** Inspect tools, permissions, current files, and any approved reference report. Create the rebuildable `research-context.md`, `source-index.md`, `evidence-ledger.md`, `acquisition-attempt-log.md`, `coverage-matrix.md`, `validation-log.md`, and `release-review.md` under the company-local `data/` directory. See [workflow.md](references/workflow.md) and [evidence-and-ledger.md](references/evidence-and-ledger.md).
2. **Stage 1 - source acquisition and preparation.** Build the source plan, obtain SEC 10-K/10-Q/8-K, IR releases and presentations, official-site evidence, transcripts or meeting minutes, and relevant independent industry or market material. Preserve failures and retries. See [source-acquisition.md](references/source-acquisition.md).
3. **Stage 2 - business-model routing.** Map legal/reporting segments to economic units, customers, revenue recognition, cost stack, capital occupation, cash timing, risk carrier, verification KPI, and failure path. See [business-model-routing.md](references/business-model-routing.md).
4. **Stage 3 - industry and operating analysis.** Explain the demand event, value chain, supply constraints, competition, customer choice, and cycle. Add only route-relevant modules. Separate company claims from independently verified facts. See [industry-and-theme-analysis.md](references/industry-and-theme-analysis.md).
5. **Stage 4 - fundamentals and derived metrics.** Extract reported consolidated statements first, then build a source-linked mapping ledger, restatement bridge, segment bridge, APM bridge, and auditable derived metrics. Use the Workspace financial calculator with `--strict` when available. See [financial-reconstruction.md](references/financial-reconstruction.md).
6. **Stage 5 - capital allocation, governance, risk, and monitoring.** Trace acquisitions, disposals, capex, inventory/capacity, debt, leases, pensions, goodwill, dividends, buybacks, incentives, controls, and stress paths to statements and cash.
7. **Stage 6 - valuation and shareholder return.** Select a route-appropriate primary method before assumptions. Prefer SOTP for heterogeneous groups; use EV/EBITDA or FCF as cross-checks only when perimeter and denominator match. Model dividends and buybacks under one explicit convention. See [valuation-and-shareholder-return.md](references/valuation-and-shareholder-return.md).
8. **Stage 7 - report assembly and release review.** Draft the adaptive report spine, show reported tables before interpretation, cite claims inline, run deterministic checks, conduct a clean second-pass review, and publish `PASS`, `PARTIAL`, or `BLOCKED`. See [output-contract.md](references/output-contract.md) and [release-gates.md](references/release-gates.md).

## Automatic run and human handoff

The `prompts/full-research.zh-CN.md` prompt is the default autonomous entry. Show the Stage 0 plan first, request one confirmation for identity/scope and access, then run the confirmed stages in sequence using the bundled bridge and ordinary terminal web tools. Do not ask the user to copy internal commands. Pause only for a material ambiguity, missing authorization, unsafe source choice, or a valuation boundary that would change the decision. After deterministic validation and release review, deliver the report and ledgers, state `PASS`/`PARTIAL`/`BLOCKED`, and enter a human review turn with unresolved questions, key sensitivities, and explicit approval points.

For a focused data task, route natural-language requests such as “重建最近五年三表时序”“拼接债务和养老金 Note”“补齐缺失年份并检查重述” to [04-financial-series-reconstruction.zh-CN.md](prompts/04-financial-series-reconstruction.zh-CN.md). Load [financial-series-reconstruction.md](references/financial-series-reconstruction.md) for the two-layer raw/standardized data model, metadata contract, cross-year stitching rules, and reconciliation gates. This focused route may stop after structured data and validation; it does not imply that a valuation or narrative report is requested.

## Bundled data runtime

This skill ships a trimmed, portable ResearchFoundry runtime under `vendor/research_foundry/`. It includes SEC native HTML acquisition, official-site acquisition and preparation, manually supplied transcript preparation, research contracts, provenance manifests, immutable run records, indexing, and deterministic validation. The runtime is invoked through `scripts/research_foundry_local.py`, which adds the bundled package to `sys.path` and emits machine-readable JSON.

The terminal still supplies the execution environment: Python 3.12+, the dependencies listed in `vendor/requirements.txt`, network access, and writable roots from `examples/config.toml`. Install the bundled dependencies with the active terminal interpreter using `python -m pip install -r vendor/requirements.txt`; no external ResearchFoundry checkout is required. A separately installed ResearchFoundry may be used for comparison, but is not part of the normal path.

After installing the dependencies, run `python scripts/preflight.py --workspace <artifact-root>`. The agent normally invokes the bridge itself; direct inspection uses `python scripts/research_foundry_local.py doctor`, `... transcript ...`, `... ten-k sec-html ...`, `... official-site ...`, and `... research ...`.

Use the bundled stable flows:

```text
ten-k sec-html: plan --confirm -> run -> inspect -> index/search/read
transcript: plan or plan-metadata --confirm -> run -> publish -> inspect
official-site: plan -> run -> publish -> inspect -> search/read
```

Do not invent a prepared transcript. Preserve supplied provider-prepared minutes as a distinct representation and disclose that speaker attribution or completeness may not be independently verifiable. User-uploaded source files remain immutable; every cleaned output must retain source hash, coverage status, limitations, and line-addressable markers.

The bundled runtime deliberately excludes model-specific OCR executors and third-party data-provider adapters. When a source requires an excluded capability, preserve the raw source, record the gap, and continue only with evidence that can be independently validated.

## Report spine

Use the following order unless the issuer's economics require a documented change:

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

Insert only relevant route modules. For a structural-theme question, use the three-layer rule in [theme-demand-three-layer.md](references/theme-demand-three-layer.md): direct product/revenue, system or infrastructure indirect demand, and adjacent enabling indirect demand. Never turn a total segment, market TAM, external demand forecast, or management order target into theme revenue without a sourced revenue bridge.

## Tool and output handoff

- Use repository-relative paths in tracked Markdown. Keep external originals in `sources/`; keep rebuildable artifacts out of Git according to repository policy.
- Initialize a new project with `scripts/init_company_research.py` and build a file manifest with `scripts/build_source_manifest.py`. These scripts never overwrite existing files unless explicitly requested.
- Validate a package with `scripts/validate_research_package.py`, the available financial calculator, the full report validator, parsers for JSON/CSV, and `git diff --check`.
- Treat a mechanically clean report as necessary but not sufficient. The release decision is the weakest mandatory evidence, routing, fundamentals, valuation, or review gate.
- The package includes `examples/config.toml` for terminal setup and `prompts/` for user-friendly stage prompts. Replace placeholders before use; never paste secrets into the skill or prompts.
