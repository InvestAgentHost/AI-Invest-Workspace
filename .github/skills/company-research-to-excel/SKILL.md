---
name: company-research-to-excel
description: Build a polished financial model workbook (.xlsx) from curated research artifacts — three consolidated statements, operating KPIs, derived metrics, segment/geography data, and note schedules — with live formulas, tie-out checks, cross-sheet links, and professional formatting.
---

# Company Research To Excel

You are building the workbook an analyst starts company research from.  You —
the agent — are the architect.  You read the data, understand the company, and
make every design decision: what to bold, what to indent, where growth rows
go, which margins matter, how to wire cross-sheet links, and what checks to
add.  The scripts are your hands, not your brain.

---

## Source rules

Data integrity depends on strict source discipline.

| Tier | Source | Permitted use |
|------|--------|---------------|
| 1 | `financial_input.json` / `financial-input-*.json` | IS, BS, CF, Operating Metrics — curated, highest confidence |
| 2 | 10-K / 10-Q source HTML (via `--sec-source`) | Complete as-reported line items for gap-filling; always preferred over press releases |
| 3 | sec-cleaned files (press releases, S-1) | Latest unfiled quarter, non-GAAP tables, supplementary KPIs |
| **Banned** | Deep-research markdown report | NOT a data source — ever |
| **Banned** | Third-party sources | Never acceptable for filed numbers |

When the same line item appears in multiple sources, prefer the higher tier.
10-K/10-Q filings are authoritative; press releases may use condensed captions
that hide detail.

---

## Data sources

| Source | Provides | Required |
|---|---|---|
| `financial_input.json` (or `financial-input-*.json`) | IS, BS, CF, Operating Metrics | **recommended** (not required) |
| `segment-history-*.json` | Segment revenue, operating profit, backlog | optional |
| SEC source HTML (`source.html` in 10-K dirs) | Complete as-reported IS/BS/CF from filings | **strongly recommended** |
| sec-cleaned files | Segments, geography, products, supplementary data | optional |
| Collector bundle (`tables.json`) | Merged output from all above — used for gap-filling and segments/notes | built during Phase 2 |

At minimum you need **one** of: financial_input.json **or** SEC source HTML.
If both are absent, **ask the user** for the correct path to annual filings before
proceeding — do not guess or silently produce an empty model.

---

## Workflow

### Phase 0 — Scope

Before touching any data, establish the model's scope:

1. **Identify the company**: ticker, exchange, fiscal year end, currency, units.
2. **Map available filings**: search for 10-K source HTML in **both** path
   patterns (see Phase 1).  Note which fiscal years each covers.  A 10-K
   carries 2 years of BS data and 2-3 years of IS/CF data.
3. **Define the period window**: which annual and quarterly periods will appear
   in the workbook.  Use financial_input.json period_order if available;
   otherwise infer from the filing years found.
4. **Coverage check**: for every period in the window, confirm at least one
   source covers it.  Flag any period with no source — it will be empty in the
   model unless supplemented later.

This upfront mapping prevents the "silently missing data" problem.

### Phase 1 — Locate data

```
data/curated/companies/<market>/<company-id>/
├── financial_input.json            ← recommended (may also be named
│   (or financial-input-*.json)        financial-input-2016-2025.json etc.)
├── segment-history-*.json          ← optional, separate segment dataset
└── sec-cleaned/                    ← optional, feed to collector

# --- SEC source HTML: check BOTH path patterns ---

# Pattern A — sec/ directory
sources/companies/<market>/<company-id>/sec/
├── 10-k-2025/source.html
├── 10-k-2024/source.html
└── ...

# Pattern B — artifacts/ten_k/ directory (PSP-style)
sources/companies/<market>/<company-id>/artifacts/ten_k/<TICKER>/
├── FY2025/psp_<hash>/raw/source.html
├── FY2024/psp_<hash>/raw/source.html
└── ...

research/companies/<market>/<company-id>/data/
└── sec-cleaned/                    ← also check here
```

**Data discovery steps:**

1. Resolve the company-id.  Use `find` or `ls` to locate the company directory
   under both `data/curated/companies/` and `sources/companies/`.
2. Look for `financial_input.json` OR any file matching `financial-input*.json`.
   If found, this is your Tier 1 curated data source.
3. Look for `segment-history*.json` — a supplementary segment dataset with a
   different schema (`segments → {name → {sales, operating_profit, backlog}}`).
4. Search for SEC source HTML in **both** path patterns above.  Use:
   ```bash
   find sources/companies/<market>/<company-id> -name "source.html" -path "*/raw/*" -o -name "source.html" -path "*/10-k-*"
   ```
5. If **no SEC source HTML is found** in either pattern, **ask the user**:
   "I could not find 10-K source HTML at the expected paths.  Please provide
   the correct directory path to the annual filing source.html files."
   Do not proceed without at least one data source (financial_input or SEC HTML).
6. Check for `sec-cleaned/` directories.

### Phase 2 — Collect tables from filings

Run the collector with **both** sec-cleaned files and SEC source HTML.  The
`--sec-source` flag accepts the **parent directory** containing `source.html`
(or a `raw/source.html` subdirectory — both patterns are auto-detected).

```bash
python3 .github/skills/company-research-to-excel/scripts/collect_tables.py \
  [<sec-cleaned-dir>/] \
  --sec-source <path-to-10-K-dir-1>/ \
  --sec-source <path-to-10-K-dir-2>/ \
  --output <working-dir>/tables.json
```

Examples for the two path patterns:

```bash
# Pattern A (sec/ directory)
--sec-source sources/.../sec/10-k-2025/

# Pattern B (artifacts/ten_k/ PSP directory)
--sec-source sources/.../artifacts/ten_k/LMT/FY2025/psp_<hash>/
```

Pass multiple `--sec-source` flags for multiple filing years.  If no
sec-cleaned directory exists, the collector runs on SEC sources alone.

Review the output summary.  The collector classifies tables by topic.
**Important**: for SEC source HTML, the main financial statements (IS, BS, CF)
may be classified as `debt_liquidity`, `tax_shares`, or `other_notes` rather
than `financials` — always check all topics when searching for statement tables.
Match tables by their row content (Revenue, Total assets, Cash flows from...)
rather than relying solely on `topic_hint`.

### Phase 3 — Assemble the draft model.json

**Standard mode** (financial_input.json available):
```bash
python3 .github/skills/company-research-to-excel/scripts/assemble_model.py \
  <path-to-financial_input.json> \
  -o <working-dir>/model.json \
  [--bundle <working-dir>/tables.json]
```

**Bundle-only mode** (no financial_input.json — build from tables.json alone):
```bash
python3 .github/skills/company-research-to-excel/scripts/assemble_model.py \
  --bundle-only \
  --bundle <working-dir>/tables.json \
  --ticker <TICKER> --name "<Company Name>" \
  --periods FY2016,FY2017,...,FY2025 \
  -o <working-dir>/model.json
```

In bundle-only mode, the assembler builds IS/BS/CF from `financials`-topic
tables in the bundle and organizes non-financial tables into supplementary
sheets.  The result is thinner than the standard mode because the bundle
tables provide only what the filing contains — the agent's Phase 3.5 and
Phase 4 customization is even more important in this case.

The assembler produces a **bare draft** — every metric as a plain `input` row,
organized by statement.  No bold, no indent, no growth, no margins, no checks.
It also prints a DATA EXTRACTION SUMMARY showing every metric available.

**Read the summary carefully.**  This is your raw material.

### Phase 3.5 — Data completeness verification (SECOND ROUND)

The draft model.json was built from the assembler's mechanical extraction —
whether from financial_input.json (standard mode) or tables.json (bundle-only
mode).  Either way, it likely has gaps.  Now use the collector output to find
and fill missing line items.

**Step 1: Find the financial statement tables.**  Open `tables.json` and search
ALL topics — not just `financials`.  For SEC source tables, look at the actual
row labels to identify:
- **Income Statement**: rows containing Revenue, Cost of revenue, Income from
  operations, Net income, EPS
- **Balance Sheet**: rows containing Total assets, Total equity, Cash and cash
  equivalents
- **Cash Flow Statement**: rows containing Cash flows from operating/investing/
  financing activities, Net cash provided by

**Step 2: Compare line items.**  For each financial statement table from the
filing, compare its row labels against the rows already in model.json:
- List every line item in the filing table
- Check which ones have a matching row in model.json (match by label
  similarity, not exact string)
- Identify **missing items** — line items present in the filing but absent
  from model.json

Pay special attention to **Cash Flow** — this is the statement most likely to
have gaps because financial_input.json often captures only subtotals, while
the filing has 30+ individual line items under each activity section.

Common missing items:
- **IS**: individual opex lines (Operations and support, Sales and marketing,
  R&D, G&A), Other income/expense, Interest expense, Interest income, EPS
  (basic & diluted), weighted average shares outstanding
- **BS**: individual current asset/liability lines, AOCI, Additional paid-in
  capital, Retained earnings, Treasury stock
- **CF**: all adjustments to reconcile net income (D&A, SBC, deferred taxes,
  gains/losses, impairments), all working capital changes, all investing
  detail, all financing detail

**Step 3: Add missing items to model.json.**  For each missing line item:

1. Create a metric key slug from the label (e.g., "Operations and support" →
   `operations_and_support`)
2. Extract the values from the collector table — match the table's period
   headers to the model's period labels
3. Insert a new `input` row at the correct position in the appropriate
   statement block, matching the filing's own ordering
4. Values from filings may cover fewer periods than financial_input.json —
   partial coverage is better than omission

**Step 4: Print a gap report.**  After supplementing, print:
- Number of items added per statement (target: IS 15+, BS 15+, CF 25+)
- Items that could not be matched (ambiguous labels)

Filing tables may use different labels for the same metric (e.g., "Income from
operations" vs. "Operating income").  Use judgment to avoid duplicates.

### Phase 4 — Customize model.json (THIS IS THE CORE STEP)

Open model.json and apply your analytical judgment.  See the full schema in
`references/model-schema.md`.

#### 4a. Read the data and understand the company

Before touching the model, read financial_input.json (if available) and the
draft model.json to understand:
- What kind of company is this? (tech, industrial, financial, etc.)
- Which metrics are headline aggregates vs. sub-line items?
- What is the sign convention for cash flow items?
- Are there non-GAAP metrics? Which ones does the company emphasize?
- Do quarterly periods exist?
- If `segment-history-*.json` exists, read it — its structure is
  `segments → {name → {sales, operating_profit, backlog → {year: value}}}`.
  Use this to build / enrich the Segments sheet in Phase 4f.

#### 4b. Income Statement layout

The IS should have these sections in order:

1. **As-reported IS** — every filed line item in filed order.  Bold headline
   aggregates (revenue, gross profit, operating income, net income).  Indent
   components under their totals.
2. **EPS & Share Count block** — if EPS data is available:
   ```json
   {"type": "spacer"},
   {"id": "basic_eps", "label": "Basic EPS", "type": "input",
    "values": {...}, "fmt": "ps", "bold": true},
   {"id": "diluted_eps", "label": "Diluted EPS", "type": "input",
    "values": {...}, "fmt": "ps", "bold": true},
   {"id": "waso_basic", "label": "Weighted Avg Shares — Basic", "type": "input",
    "values": {...}, "fmt": "num"},
   {"id": "waso_diluted", "label": "Weighted Avg Shares — Diluted", "type": "input",
    "values": {...}, "fmt": "num"}
   ```
3. **Non-GAAP bridge** — if the company reports adjusted EBITDA or similar:
   ```json
   {"type": "spacer"},
   {"id": "adj_ebitda", "label": "Adjusted EBITDA", "type": "input",
    "values": {...}, "bold": true},
   {"id": "adj_ebitda_margin", "label": "  Adjusted EBITDA Margin", "type": "calc",
    "expr": "{adj_ebitda}/{total_revenue}", "fmt": "pct", "memo": true}
   ```
   Include the company's own reconciliation items (SBC, D&A, restructuring,
   etc.) as input rows between net income and adjusted EBITDA, with indent 1.
4. **Margins & growth** — after each headline aggregate, insert growth and
   margin rows:
   ```json
   {"id": "rev_yoy", "label": "  YoY Growth", "type": "growth_yoy",
    "of": "total_revenue", "fmt": "pct", "memo": true},
   {"id": "gross_margin", "label": "  Gross Margin", "type": "calc",
    "expr": "{gross_profit}/{total_revenue}", "fmt": "pct", "memo": true},
   {"id": "op_margin", "label": "  Operating Margin", "type": "calc",
    "expr": "{operating_income}/{total_revenue}", "fmt": "pct", "memo": true},
   {"id": "net_margin", "label": "  Net Margin", "type": "calc",
    "expr": "{net_income}/{total_revenue}", "fmt": "pct", "memo": true}
   ```
5. **IS check** — verify a subtotal ties:
   ```json
   {"id": "is_check", "label": "IS Check (should be ~0)", "type": "check",
    "expr": "{revenue}-{total_costs_and_expenses}-{operating_income}",
    "fmt": "num", "memo": true}
   ```

#### 4c. Balance Sheet layout

1. **As-reported BS** — every filed line item in filed order.  Bold major
   totals (total current assets, total assets, total current liabilities,
   total liabilities, total equity).
2. **Balance check** — immediately after the last BS item:
   ```json
   {"id": "bs_check", "label": "Balance Check (should be ~0)",
    "type": "check", "expr": "{total_assets}-{total_liabilities}-{total_equity}",
    "fmt": "num", "memo": true}
   ```
3. **Working capital analytics** — if quarterly data exists and sufficient BS
   detail is available:
   ```json
   {"type": "spacer"},
   {"id": "wc_dso", "label": "Days Sales Outstanding", "type": "calc",
    "expr": "{accounts_receivable}/{IS:total_revenue}*365",
    "expr_q": "{accounts_receivable}/{IS:total_revenue}*91",
    "fmt": "num1", "memo": true},
   {"id": "wc_dio", "label": "Days Inventory Outstanding", "type": "calc",
    "expr": "{inventories}/{IS:cost_of_revenue}*365",
    "expr_q": "{inventories}/{IS:cost_of_revenue}*91",
    "fmt": "num1", "memo": true},
   {"id": "wc_dpo", "label": "Days Payable Outstanding", "type": "calc",
    "expr": "{accounts_payable}/{IS:cost_of_revenue}*365",
    "expr_q": "{accounts_payable}/{IS:cost_of_revenue}*91",
    "fmt": "num1", "memo": true},
   {"id": "wc_ccc", "label": "Cash Conversion Cycle", "type": "calc",
    "expr": "{wc_dso}+{wc_dio}-{wc_dpo}", "fmt": "num1", "memo": true}
   ```
   Only add working capital analytics if the company has inventory (skip for
   pure-software/platform companies).

#### 4d. Cash Flow layout

1. **As-reported CF** — every filed line item in filed order.  Bold section
   totals (CFO, CFI, CFF).  Indent individual items under each section.
   This is where Phase 3.5 gap-filling matters most — the CF should have
   25-40 individual line items, not just 3-5 subtotals.
2. **Cash walk check** — net change in cash should tie:
   ```json
   {"id": "cf_check", "label": "Cash Walk Check (should be ~0)",
    "type": "check",
    "expr": "{cfo_total}+{cfi_total}+{cff_total}+{fx_effect}-{net_change_in_cash}",
    "fmt": "num", "memo": true}
   ```
3. **FCF analytics block**:
   ```json
   {"type": "spacer"},
   {"id": "fcf", "label": "Free Cash Flow", "type": "calc",
    "expr": "{cfo_total}+{capex_ppe}", "bold": true, "fmt": "num"},
   {"id": "fcf_yoy", "label": "  YoY Growth", "type": "growth_yoy",
    "of": "fcf", "fmt": "pct", "memo": true},
   {"id": "capex_pct", "label": "  Capex % of Revenue", "type": "calc",
    "expr": "0-{capex_ppe}/{IS:total_revenue}",
    "fmt": "pct", "memo": true},
   {"id": "fcf_margin", "label": "  FCF Margin", "type": "calc",
    "expr": "{fcf}/{IS:total_revenue}", "fmt": "pct", "memo": true},
   {"id": "fcf_conversion", "label": "  FCF Conversion (FCF/Net Income)",
    "type": "calc", "expr": "{fcf}/{IS:net_income}", "fmt": "pct", "memo": true}
   ```
   Check capex sign: if capex is negative (outflow), use `+`; if positive, use `-`.

#### 4e. BS Detail sheet (optional, for large companies)

If the collector captured disaggregated footnote tables (goodwill by segment,
intangibles by class, PP&E, debt schedules, etc.), create a BS Detail sheet
(`short: "BSD"`):
- One block per disaggregated face line
- Component rows as `input` with `"group": true` for collapsible detail
- Inline check tying components back to the face line:
  ```json
  {"id": "goodwill_check", "label": "Check vs Face (should be ~0)",
   "type": "check", "expr": "{goodwill_total}-{BS:goodwill}", "fmt": "num",
   "memo": true}
  ```
- Set `"contents": true` on the sheet for a clickable section index.

#### 4f. Segment sheets

Segment data is critical.  The assembler extracts segment tables from 10-K
filings, but they come in two formats that require different handling:

**Format A — Period-column tables** (most common for revenue/EBITDA by segment):
The assembler handles these automatically.  Tables like "Segment Revenue" have
periods as columns and segments as rows.  They appear in the draft model under
topic-based sheets (e.g., "Other Notes", "Operating Kpis").

**Format B — Segment-column tables** (one table per fiscal year):
Some 10-K filings put segments as COLUMNS with one table per year:
```
Year Ended December 31, 2023
             Mobility  Delivery  Freight  Total
Revenue       18,727    12,204    5,246   36,177
Adjusted...    5,210     1,505     (274)   6,441
```
These tables CANNOT be directly assembled into time-series blocks because each
year's data is in a separate table.  When you see this pattern:

1. Find all segment-column tables in `tables.json` (look for tables where
   headers contain "Year Ended December 31, YYYY" and the first data row has
   segment names)
2. Manually restructure by extracting each metric across all year-tables:
   - Read Mobility Revenue from FY2023, FY2024, FY2025 tables
   - Combine into one `input` row with multi-year values
3. Repeat for all segment metrics (Revenue, Adjusted EBITDA, etc.)

**Building the Segments sheet** (`short: "SEG"`, `tab_color: "548235"`):

1. One block for **Segment Revenue**:
   - Per-segment revenue as `input` rows
   - Subtotal as `subtotal` row
   - YoY growth per segment
   - Revenue mix (%) per segment: `{seg_X_rev}/{seg_total_rev}`
   - Tie-out check:
   ```json
   {"id": "seg_rev_check", "label": "Segment Rev Check (should be ~0)",
    "type": "check",
    "expr": "{seg_total_rev}-{IS:total_revenue}",
    "fmt": "num", "memo": true}
   ```

2. One block for **Segment Profitability** (if available):
   - Per-segment Adjusted EBITDA (or operating income)
   - Segment margins: `{seg_X_ebitda}/{seg_X_rev}`

3. Use `min_label`/`max_label` if segment definitions changed mid-window
   (e.g., a segment was added, divested, or renamed).

Also check the **geography revenue** tables — the assembler typically extracts
these correctly (they use period-column format).  Create a geography block on
the Segments sheet or a separate Geography sheet.

#### 4g. Operating Metrics

Company-specific KPIs with growth rows for the 2-3 most important ones.
Use `min_label`/`max_label` if a KPI started mid-window.

#### 4h. Derived Metrics sheet (DM) — computed from model data

The DM sheet is built **entirely from calc formulas** referencing IS/BS/CF rows.
Do NOT rely on metrics.md — compute every ratio directly so the DM sheet is
self-contained and always consistent with the source statements.

Create a DM sheet (`short: "DM"`, `tab_color: "7030A0"`).  Include every
category below where the required inputs exist in the model.  Skip a ratio
only when the denominator row is missing from the model — never skip a whole
category without checking.

All DM rows use `"type": "calc"`, `"memo": true`, and the format shown.
Adapt the `{row_id}` tokens to match the actual IDs in your IS/BS/CF sheets.

```json
{
  "name": "Derived Metrics", "short": "DM",
  "kind": "statement", "tab_color": "7030A0",
  "blocks": [...]
}
```

**Block 1 — PROFITABILITY** (requires: IS revenue, gross profit, operating
income, EBITDA or D&A, net income)
```json
{"id": "dm_gross_margin", "label": "Gross Margin",
 "type": "calc", "expr": "{IS:gross_profit}/{IS:total_revenue}", "fmt": "pct"},
{"id": "dm_op_margin", "label": "Operating Margin",
 "type": "calc", "expr": "{IS:operating_income}/{IS:total_revenue}", "fmt": "pct"},
{"id": "dm_ebitda_margin", "label": "EBITDA Margin",
 "type": "calc", "expr": "({IS:operating_income}+{CF:depreciation_amortization})/{IS:total_revenue}", "fmt": "pct"},
{"id": "dm_net_margin", "label": "Net Margin",
 "type": "calc", "expr": "{IS:net_income}/{IS:total_revenue}", "fmt": "pct"},
{"id": "dm_eff_tax", "label": "Effective Tax Rate",
 "type": "calc", "expr": "{IS:income_tax_expense}/{IS:earnings_before_tax}", "fmt": "pct"}
```

**Block 2 — RETURNS** (requires: BS total assets, total equity, IS operating
income, net income, CF D&A; uses average BS = (current + prior year) / 2)
```json
{"id": "dm_roa", "label": "ROA",
 "type": "calc", "expr": "{IS:net_income}/({BS:total_assets}+{BS:total_assets@-1})*2", "fmt": "pct"},
{"id": "dm_roe", "label": "ROE",
 "type": "calc", "expr": "{IS:net_income}/({BS:total_equity}+{BS:total_equity@-1})*2", "fmt": "pct"},
{"id": "dm_roic", "label": "ROIC",
 "type": "calc", "expr": "{IS:operating_income}*(1-{dm_eff_tax})/(({BS:total_equity}+{BS:long_term_debt}+{BS:total_equity@-1}+{BS:long_term_debt@-1})/2)", "fmt": "pct"},
{"id": "dm_asset_turnover", "label": "Asset Turnover",
 "type": "calc", "expr": "{IS:total_revenue}/({BS:total_assets}+{BS:total_assets@-1})*2", "fmt": "x"}
```

**Block 3 — LEVERAGE** (requires: BS long-term debt, current portion of debt,
cash; IS operating income, CF D&A)
```json
{"id": "dm_net_debt", "label": "Net Debt",
 "type": "calc", "expr": "{BS:long_term_debt}+{BS:current_debt}-{BS:cash_and_equivalents}", "fmt": "num"},
{"id": "dm_net_debt_ebitda", "label": "Net Debt / EBITDA",
 "type": "calc", "expr": "{dm_net_debt}/({IS:operating_income}+{CF:depreciation_amortization})", "fmt": "x"},
{"id": "dm_debt_equity", "label": "Debt / Equity",
 "type": "calc", "expr": "({BS:long_term_debt}+{BS:current_debt})/{BS:total_equity}", "fmt": "x"}
```

**Block 4 — SOLVENCY** (requires: BS total equity, total assets, debt)
```json
{"id": "dm_equity_ratio", "label": "Equity Ratio",
 "type": "calc", "expr": "{BS:total_equity}/{BS:total_assets}", "fmt": "pct"},
{"id": "dm_debt_assets", "label": "Debt / Total Assets",
 "type": "calc", "expr": "({BS:long_term_debt}+{BS:current_debt})/{BS:total_assets}", "fmt": "pct"}
```

**Block 5 — LIQUIDITY** (requires: BS current assets, current liabilities,
cash, inventories)
```json
{"id": "dm_current_ratio", "label": "Current Ratio",
 "type": "calc", "expr": "{BS:current_assets}/{BS:current_liabilities}", "fmt": "x"},
{"id": "dm_quick_ratio", "label": "Quick Ratio",
 "type": "calc", "expr": "({BS:current_assets}-{BS:inventories})/{BS:current_liabilities}", "fmt": "x"},
{"id": "dm_cash_ratio", "label": "Cash Ratio",
 "type": "calc", "expr": "{BS:cash_and_equivalents}/{BS:current_liabilities}", "fmt": "x"}
```

**Block 6 — COVERAGE** (requires: IS operating income, interest expense;
CF CFO)
```json
{"id": "dm_interest_coverage", "label": "Interest Coverage (EBIT / Interest)",
 "type": "calc", "expr": "{IS:operating_income}/{IS:interest_expense}", "fmt": "x"},
{"id": "dm_cfo_interest", "label": "CFO / Interest Expense",
 "type": "calc", "expr": "{CF:cfo_total}/{IS:interest_expense}", "fmt": "x"}
```

**Block 7 — CASH CONVERSION** (requires: CF CFO, capex; IS revenue, net
income; CF D&A)
```json
{"id": "dm_cfo_margin", "label": "CFO Margin",
 "type": "calc", "expr": "{CF:cfo_total}/{IS:total_revenue}", "fmt": "pct"},
{"id": "dm_cfo_ebitda", "label": "CFO / EBITDA",
 "type": "calc", "expr": "{CF:cfo_total}/({IS:operating_income}+{CF:depreciation_amortization})", "fmt": "x"},
{"id": "dm_capex_intensity", "label": "Capex Intensity",
 "type": "calc", "expr": "0-{CF:capex_ppe}/{IS:total_revenue}", "fmt": "pct"},
{"id": "dm_fcf_margin", "label": "FCF Margin",
 "type": "calc", "expr": "{CF:fcf}/{IS:total_revenue}", "fmt": "pct"},
{"id": "dm_fcf_conversion", "label": "FCF / Net Income",
 "type": "calc", "expr": "{CF:fcf}/{IS:net_income}", "fmt": "x"},
{"id": "dm_da_capex", "label": "D&A / Capex",
 "type": "calc", "expr": "0-{CF:depreciation_amortization}/{CF:capex_ppe}", "fmt": "x"}
```

**Block 8 — EARNINGS QUALITY** (requires: CF CFO; IS net income; BS total
assets)
```json
{"id": "dm_cfo_ni", "label": "CFO / Net Income",
 "type": "calc", "expr": "{CF:cfo_total}/{IS:net_income}", "fmt": "x"},
{"id": "dm_accrual_ratio", "label": "Accrual Ratio",
 "type": "calc", "expr": "({IS:net_income}-{CF:cfo_total})/({BS:total_assets}+{BS:total_assets@-1})*2", "fmt": "pct"}
```

**Block 9 — GROWTH** (requires: IS revenue, net income; CF CFO)
```json
{"id": "dm_rev_growth", "label": "Revenue Growth",
 "type": "calc", "expr": "{IS:total_revenue}/{IS:total_revenue@-1}-1", "fmt": "pct"},
{"id": "dm_ni_growth", "label": "Net Income Growth",
 "type": "calc", "expr": "{IS:net_income}/{IS:net_income@-1}-1", "fmt": "pct"},
{"id": "dm_cfo_growth", "label": "CFO Growth",
 "type": "calc", "expr": "{CF:cfo_total}/{CF:cfo_total@-1}-1", "fmt": "pct"}
```

**Block 10 — WORKING CAPITAL** (same formulas as BS analytics, but
cross-referenced here for the DM view; skip if BS already has these)
```json
{"id": "dm_dso", "label": "Days Sales Outstanding",
 "type": "calc", "expr": "{BS:accounts_receivable}/{IS:total_revenue}*365", "fmt": "num1"},
{"id": "dm_dio", "label": "Days Inventory Outstanding",
 "type": "calc", "expr": "{BS:inventories}/{IS:cost_of_revenue}*365", "fmt": "num1"},
{"id": "dm_dpo", "label": "Days Payable Outstanding",
 "type": "calc", "expr": "{BS:accounts_payable}/{IS:cost_of_revenue}*365", "fmt": "num1"},
{"id": "dm_ccc", "label": "Cash Conversion Cycle",
 "type": "calc", "expr": "{dm_dso}+{dm_dio}-{dm_dpo}", "fmt": "num1"}
```

**Adaptation rules:**
- The `{row_id}` tokens above are templates — replace with the actual IDs
  from your IS/BS/CF sheets (e.g., `total_revenue` might be `total_sales`
  for LMT, `net_revenues` for another company).
- If EBITDA is reported as a separate input row, reference it directly
  instead of computing as operating income + D&A.
- If a BS row is missing (e.g., no `inventories` for a software company),
  skip the ratios that need it (Quick Ratio, DIO, DPO, CCC).
- For `@-1` (prior-year) references in average calculations, the first
  period will show a formula error — this is expected and acceptable.
- If a denominator could be zero or negative (e.g., negative equity), the
  formula will produce a misleading result.  Add a note or skip that ratio.
- Target: **25-40 DM rows** across 8-10 categories.  More is better than
  fewer, but skip ratios with missing denominators rather than producing
  errors.

#### 4i. Formatting rules

Apply these across all sheets:

- **Bold**: headline aggregates only — revenue, gross profit, operating income,
  net income, total assets, total equity, CFO, FCF, adjusted EBITDA.
  Don't bold everything.
- **Indent**: components under totals get `"indent": 1`.  Sub-components get
  `"indent": 2` (rare).
- **Group**: set `"group": true` on detail rows that should be collapsible
  (BS Detail components, individual adjustments to reconcile net income in CF).
- **Spacer**: insert between logical sections within a block.
- **Number formats**: `"num"` (default), `"pct"` (margins/growth), `"ps"`
  (per-share), `"x"` (multiples), `"num1"` (1 decimal).

#### 4j. Review and validate

After editing, scan the model for:
- Every `calc`/`check` expression references valid row IDs
- Every `growth_yoy`/`growth_qoq` references a valid row via `"of"`
- Every `link` references a valid `"SHEET:row_id"`
- No duplicate row IDs within a sheet
- Numbers live in exactly ONE place — everywhere else is formula or link

### Phase 5 — Build the workbook

```bash
python3 .github/skills/company-research-to-excel/scripts/build_workbook.py \
  <working-dir>/model.json \
  <output-path>/<Ticker>_model.xlsx
```

### Phase 6 — Verify (multi-layer)

**Layer 1: Automated verification**

```bash
python3 .github/skills/company-research-to-excel/scripts/verify_model.py \
  <working-dir>/model.json \
  <output-path>/<Ticker>_model.xlsx
```

The verifier runs numeric checks (re-evaluates all formulas, flags check rows
with |value| > 0.5) and structural checks (sheets exist, period headers match,
gridlines hidden, panes frozen).

If verification fails, fix model.json and rebuild.  **Never patch the .xlsx
directly.**

**Layer 2: Completeness gate** (you, the agent)

After verification passes, manually compare the workbook against the most
recent 10-K by checking:
- **Line-count parity**: every filed IS/BS/CF line item appears in the model
- **Window completeness**: every annual period has data (no hollow columns)
- **CF depth**: at least 25 individual line items, not just subtotals
- **EPS block**: present if the filing includes per-share data
- **Segment tie-out**: segment revenue sums match IS total revenue

If any gap is found, go back to Phase 3.5, supplement, and rebuild.

### Phase 7 — Deliver

Send the workbook to the user with:
- Periods covered (annual range, quarterly range if any)
- Sheets created and row counts
- Check results (all pass / any failures)
- Data completeness notes (which filing years were used for gap-filling)
- Comparability notes (restatements, re-segmentations, FYE changes if any)

---

## Expected sheet structure

| Sheet | Short | Tab Color | Source | Content |
|---|---|---|---|---|
| Cover | — | `1F4E79` | auto | Company info, color legend, sheet directory |
| Income Statement | IS | `1F4E79` | financial_input + filing | As-reported IS + EPS + Non-GAAP bridge + margins + growth |
| Balance Sheet | BS | `1F4E79` | financial_input + filing | As-reported BS + balance check + working capital |
| Cash Flow | CF | `1F4E79` | financial_input + filing | As-reported CF + cash walk check + FCF analytics |
| BS Detail | BSD | `1F4E79` | tables.json | Disaggregated footnote tables + inline checks |
| Operating Metrics | OM | `548235` | financial_input / filing | KPIs + growth |
| Derived Metrics | DM | `7030A0` | calc formulas (IS/BS/CF) | Ratios grouped by category — computed in Phase 4h |
| Segments | SEG | `548235` | tables.json | Revenue/profit by segment + tie-out |
| Geography & Products | GEO | `548235` | tables.json | Revenue by region/product |
| Note Schedules | NS | `548235` | tables.json | Debt, intangibles, tax, etc. |
| Sources | — | `1F4E79` | auto | Data provenance + spot-check log |

Sheets are created only when data exists.

## Operating rules

1. Resolve the company and locate its curated data directory, sec-cleaned
   filings (may be under `data/curated/` or `research/`), and SEC source
   directories (under `sources/companies/` — check both `sec/` and
   `artifacts/ten_k/` path patterns).
2. If no curated data files AND no SEC source HTML can be found, **stop and
   ask the user** for the correct file paths.  Do not proceed without data.
3. Create a working directory:
   `<company-dir>/outputs/company-research-to-excel-<date>/`.
4. Run the full pipeline:
   - **Phase 0**: Scope — map available filings and periods
   - **Phase 1-2**: Collect from all available sources (financial_input,
     SEC source HTML, sec-cleaned files)
   - **Phase 3**: Assemble draft (standard mode if financial_input exists,
     bundle-only mode otherwise)
   - **Phase 3.5**: Verify completeness against filing tables, supplement gaps
   - **Phase 4**: Customize — apply all analytical judgment
   - **Phase 5-6**: Build → verify (multi-layer)
   - **Phase 7**: Deliver
5. If verification fails, fix model.json and rebuild.
6. Deliver the workbook (SendUserFile).

## Boundaries

- Do not invent data.  Every number must trace to a source file.
- Do not use the deep-research markdown report as a data source.
- Never replace source files.  Keep outputs under `outputs/`.
- Never hand-format the .xlsx.  Fix model.json and rebuild.
- Do not annualize interim figures or convert issuer-defined APMs.
- Numbers live in exactly one place.  Everywhere else is formula or link.
