# Fact-collector brief — company initial screener v2 (as of {AS_OF})

You collect FACTS for ONE company. You do not score anything and you do not give opinions. The screener's coordinator turns your facts into scores with fixed rules. Every number you report must come from a primary document (10-K, 10-Q, DEF 14A, 8-K, S-1, annual report, remuneration report, AGM voting results, SEC release), with the document name, date, a URL and a short verbatim quote (one sentence or one table row). If you cannot find a fact after a reasonable search, write `null` and say what you searched. Never estimate a missing number.

Run folder: `{RUN_DIR}`. Your scratch folder: `<RUN>/scratch/<TICKER>/` (create it; keep all your temporary files there, nowhere else). Output: `<RUN>/facts/<TICKER>.json`.

{PRIOR_FILES_NOTE}

## 1. CEO ownership (M1)
- CEO name, date in role.
- Every CEO change in the last 5 years (since {SINCE_AAER}): date the new CEO took office, outgoing CEO and the year they became CEO, incoming CEO, with the announcement (8-K Item 5.02, press release or ad hoc notice) as source. An empty list means you checked and found none.
- Shares the CEO owns directly or indirectly, EXCLUDING options (including those exercisable within 60 days) and unvested restricted shares / RSUs / PSUs. Show the subtraction from the beneficial ownership table and its footnotes.
- Latest annual base salary (Summary Compensation Table or CD&A; for non-US companies the remuneration report). Currency.
- Founder or founding-family holder of 5% or more with an active executive role: true/false.
- Last 24 months, open-market trades only (exclude option exercises, tax withholding, gifts, grants): were officers and directors together net open-market BUYERS (true/false)? Did the CEO sell more than 30% of directly held shares (true/false, with the share counts)?

## 2. Say-on-pay vote (M2)
- The latest shareholder vote on executive pay: US = advisory say-on-pay vote, results in the 8-K Item 5.07 after the annual meeting. UK = advisory vote on the directors' remuneration report at the AGM. Germany = vote on the remuneration report (Vergütungsbericht) at the AGM.
- Report meeting date, votes For, Against, Abstain/Withheld, broker non-votes, and `pct_for` = For ÷ (For + Against) as a decimal. If no vote has been held yet (for example a recent IPO), say so and give the reason.

## 3. Accounting red flags (any one removes the company)
US SEC registrants:
- (a) Any 8-K Item 4.02 (non-reliance on previously issued financial statements) filed on or after {SINCE_402}. List each with date and URL. If none, write `[]` and say how you checked (for example: EDGAR full-text search for "Item 4.02" with the company name; 10-K "restatement" search).
- (b) Internal control over financial reporting at the LATEST fiscal year-end (latest 10-K, Item 9A and the auditor's report): management's conclusion (effective / not effective), the auditor's ICFR opinion (unqualified / adverse / not required, with the reason if not required), and any material weaknesses named. Quote the conclusion sentence.
- (c) Any SEC Accounting and Auditing Enforcement Release (AAER) naming the company, a subsidiary or a current/former officer, issued on or after {SINCE_AAER}. The SEC prints "Accounting and Auditing Enforcement Release No. ####" in the header of the order or litigation release. List each with number, date, URL and one-line subject, plus `conduct_start` and `conduct_end` (YYYY-MM-DD, the first and last period of the misconduct the order describes; for a quarter use its last day) with `conduct_quote`, the order or press-release sentence that states the period. The screener counts the 5-year horizon from `conduct_end`. Also list any other SEC enforcement action in that period, marked "not an AAER".
Non-SEC filers (Germany, UK): ICFR and AAERs do not apply; write "not applicable (not an SEC registrant)". Instead report: (d) any restatement of prior-year figures to correct an ERROR (IAS 8; list each with `"is_error_per_company": true/false` — a re-presentation or change of accounting policy that the company does not call an error is `false` and does not count) in annual reports for fiscal years ending on or after {SINCE_402}; (e) whether the auditor's opinion on the latest annual accounts is modified (qualified, adverse, disclaimer) — quote the opinion paragraph heading; (f) any finding against the company's accounts by the accounting regulator (Germany: BaFin / FREP; UK: FRC Corporate Reporting Review with a published finding, or FCA) on or after {SINCE_AAER}.

## 4. Shown as information only (not scored)
- Auditor changes since {SINCE_AAER} (US: 8-K Item 4.01), with the reason given.
- CFO departures since {SINCE_AAER}: names, dates, reason given (interim CFOs count).
- Share classes with different voting rights: yes/no, and a sunset if any.

## 5. Perimeter facts
- Every acquisition, merger, disposal, spin-off, separation or IPO since the start of fiscal year L−10, with date, type, revenue effect (% of the company's revenue in the fiscal year before the event, with the figures used) and source. Include deals of 10% of revenue or more; smaller deals only if they explain a flagged year below.
- Deals of 10% of revenue or more closed or announced AFTER the latest fiscal year-end (date, status: closed / pending, type: acquisition / disposal / spin-off, revenue effect). The screener flags those above 25% as "business changing" and uses all of them to judge whether recent quarters are like for like.
- The coordinator's data flagged the years listed in your prompt (revenue change above 25% in a year; goodwill + intangibles change above 25% of prior-year invested capital; diluted shares up more than 50% in a year). For EACH flagged year say what caused it: a named deal (acquisition / merger / spin-off / separation / disposal / IPO / share conversion), or no deal (organic swing, a one-off charge, an accounting reclassification, a data error) — with the source sentence.
- For a company whose last qualifying deal was a separation, spin-off or disposal: which fiscal years' income statements and which year-end balance sheets the company has restated to the current business (discontinued operations removed). The coordinator counts a year only when its income statement and both balance sheets (opening and closing) are on the current business.
- Held for sale: name every year-end balance sheet in the window that still carries a sold or demerged unit as held for sale (assets and liabilities held for sale), with the amounts and the source. The coordinator counts such a year as clean when the income statement is restated to continuing operations, because the held-for-sale assets can only lower the returns.
- For each deal-flagged year, give the deal's revenue as a % of the company's revenue in the year before, even when it is far below 25%: the screener keeps the window for a deal that fails only the goodwill test, so the coordinator needs the revenue share to tell the two cases apart.

## 6. Data facts (to repair gaps in the Fiscal.ai data)
One pass through the filings for these items, then stop. A figure you cannot find stays out of the file: leave that year out. Never write "unresolved", `null`, text or a range as a value, and never mark a measure as blocked; the screener keeps the Fiscal.ai value and the page says the figure was not found (Codex rules, 2026-11-04). Put what you could not find, and why, in the summary.
For each fiscal year FY(L−9) to FY(L) (the prompt gives L), from the 10-K / annual report notes (intangible assets note, segment note, non-GAAP reconciliation, cash flow statement):
- `amortization_acquired_intangibles`: amortization expense of intangible assets acquired in business combinations (customer relationships, technology, trade names, backlog, acquired program assets). Exclude capitalized software, capitalized development costs, deferred financing costs and contract assets. If the company discloses only total "amortization of intangible assets", use that and say so. Each 10-K usually states three years ("amortization expense was $x, $y and $z for fiscal 2025, 2024 and 2023"), so about four 10-Ks cover ten years.
- `impairments_gw_intangibles`: impairment charges on goodwill or intangible assets (not PP&E, not right-of-use assets, not equity investments). Write 0 for a year whose filing you read and that shows none; leave out a year you did not read.
- `cfo_continuing`: net cash from operating activities from CONTINUING operations, only for years in which the cash flow statement shows discontinued operations. Leave the other years out.
- `operating_profit_bridge` (only when the prompt says operating profit is more than 15% above earnings before tax + net interest, or the income statement has no operating-profit subtotal): from the face income statement of each year FY(L−9) to FY(L), `{"years": {FY: {"pretax": earnings before income taxes (continuing operations), "net_interest": net interest expense as a positive number (net interest income negative), "remove": [{"line": "<face-statement line>", "amount": <its effect on pretax: gain positive, loss negative>}], "source": "<10-K, page>"}}, "checked": true, "why": ""}`. The screener sets operating profit = pretax + net_interest − the removed amounts, then adds back acquired amortization and impairments as for every company. Remove only lines the face statement shows separately and that are not operating: gains or losses on selling businesses or investments, debt extinguishment, pension and other post-retirement items other than service cost, equity-method income. Keep everything inside an "Other deductions" or "Other operating" line unless its note splits out such an item (then remove that part and cite the note). Emerson: no operating subtotal; FY2025 pretax 2,934 + interest 237 = 3,171, against Fiscal.ai's 4,416 (gross profit less SG&A, before "Other deductions, net" 1,245, which includes the acquired-intangibles amortization). When the gap turns out to be non-operating items only, write `{"years": {}, "checked": true, "why": "<what the gap is>"}` and the flag goes away.

- `debt_like`: litigation or regulatory settlement liabilities that the company pays on a fixed schedule over several years (for example opioid settlements), as `{"label", "years": {FY: {"noncurrent": amount, "current": amount or null, "current_why": ""}}, "source", "url"}`, year-end balances. Both parts count (v4.7): the non-current part is usually its own balance-sheet line; the current part usually sits inside accrued liabilities, so take it from the litigation or contingencies note. If the filing does not disclose the current part, write `null` and say why in `current_why`; the page then says debt is understated in that year. The screener adds both parts to debt in invested capital and in net debt. Leave it empty when there are none; do not include ordinary accrued liabilities, pensions, leases (already in debt), insurance or self-insurance reserves, environmental or landfill obligations, or contingent liabilities that are not yet settled.
- `business_disposal_losses` (v4.7, used by M3 only): losses booked on businesses sold or held for sale (remeasurement to fair value less costs to sell, loss on sale), FY(L−10) to FY(L), as `{"years": {FY: {"loss": amount, "cta_release_included": amount or null, "cta_why": "", "items": ["business, amount"], "filing", "url", "quote"}}, "gains": {FY: amount}}`. `cta_release_included` = the part of the loss that is the release of accumulated other comprehensive loss (past currency translation) where the filing states it; M3 counts the loss less that part. Gains go in `gains` for information; they do not offset losses. Write `{"years": {}}` when the company booked none, but only after checking each year's filing, so the page can say the item was checked.
Give amounts in millions of the reporting currency, as positive numbers, keyed by fiscal year (the company's own fiscal year, which may not end in December). Cite the document for each group of years.

## 7. Guidance changes (E2, v4.8)
- Call FocusAlpha `get_guidance_changes` with the company (load it with ToolSearch `select:mcp__FocusAlpha__get_guidance_changes`). It lists each guided metric that moved against the previous earnings event, with both values. Keep the PROFIT metrics (EBITDA, EBIT, operating income, EPS, net income, adjusted versions included) for full fiscal years AFTER FY L (FY L is the latest reported year; the prompt names the guidance year, FY L+1). Leave out revenue, margin, capex and cash flow guides, and quarterly or half-year guides. Write `period` in the screener's fiscal-year numbering, the FY<L+1> the prompt gives, even when the company names its year differently (a year ending March 2027 is FY2027 when the prompt says so). Record each change once, even when the release and the call both state it. Collect this section again on every run: guidance changes every quarter.
- Set `"checked"` to today's date. Write each change as `{"metric": "adjusted EBITDA", "kind": "level" | "growth", "period": "FY2026", "date": "YYYY-MM-DD", "prior": [low, high], "current": [low, high], "unit": "USD m" | "USD per share" | "%", "source": "<release name> (FocusAlpha get_guidance_changes)", "url": ""}`. A single number is `[x, x]`. A growth guide ("EPS growth 7% to 9%") is `"kind": "growth"` with the percent numbers (`[7, 9]`). Include the first guide as the `prior` of the first change.
- If FocusAlpha has no row for the company, check the latest two earnings releases (8-K Exhibit 99.1) for an outlook table and write the changes the same way; if the company gives no profit guidance, write `"changes": []` and say how you checked. If FocusAlpha is rate-limited, wait and retry; do not skip it silently.

## 8. Concentration and sales channel (D and C, v4.8)
From the latest 10-K (Item 1 Business, the customers or concentration paragraph, the revenue note) or annual report:
- `top_customers`: the customers the filing names as large (for example "Walmart, Costco and Amazon"), and `top_customers_pct`: their share of net sales in the latest fiscal year as filed (one combined number; if the filing gives each, add them). `null` if the filing names no customer above 10%.
- `largest_product_line` and `largest_product_line_pct`: the largest product line or brand and its share of net sales as filed.
- `production`: `own`, `contract` (mainly third-party or contract manufacturers) or `mixed`, with the sentence.
- `main_channel`: how most sales reach the customer, one of: `mass retail, club and e-commerce`, `grocery and convenience`, `foodservice`, `direct selling`, `own stores or restaurants`, `distributors or dealers`, `direct to industrial or OEM customers`, `government`, `regulated or contracted (utilities, waste, rail)`, `other` (say which). The coordinator uses it to check that a peer group does not mix channels.

## Tools and how to read filings (tested)
- WebSearch to find the document on sec.gov (search for example `site:sec.gov <company> 10-K 2025 amortization expense intangible`), then WebFetch the sec.gov Archives URL with a NARROW question (one table or one sentence). WebFetch cuts long documents at about 110–120k characters: pass `offset` to read further into the same document (for example offset 120000, then 240000). Do this rather than giving up when a table is past the cut.
- The EDGAR company browse pages (`/cgi-bin/browse-edgar`), data.sec.gov and efts full-text search are not reachable. Use WebSearch for filing URLs; the filing index page `https://www.sec.gov/Archives/edgar/data/<CIK>/<accession-without-dashes>/` lists the documents in a filing.
- Fiscal.ai: load with ToolSearch `select:mcp__Fiscal_ai__execute_code`. Do not call api_docs; grep `<RUN>/fiscal_api_docs.txt` for signatures. Useful: `company_filings`, `filing_pdf` (full documents; print as base64 so the tool saves the output to a file, then decode and `pdftotext` it inside YOUR scratch folder and grep), `company_insider_transactions`, `company_financials_as_reported` (as-reported lines with source pages). Run code as `async () => { ... }`.
- Base64 recipe: `async () => { const b = await codemode.filing_pdf({ companyKey: "<KEY>", filingId: "<ID>" }); console.log("B64START" + b + "B64END"); }` then `python3 -I -c "import base64,sys; s=open(sys.argv[1]).read(); open(sys.argv[2],'wb').write(base64.b64decode(s[s.find('B64START')+8:s.find('B64END')]))" <saved file> <RUN>/scratch/<TICKER>/f.pdf && pdftotext -layout <RUN>/scratch/<TICKER>/f.pdf <RUN>/scratch/<TICKER>/f.txt && grep -n -i "<keyword>" <RUN>/scratch/<TICKER>/f.txt`.
- Never put any email address or personal data in request headers, URLs or User-Agent strings.
- Aim to finish within about 60–80 tool calls.

## Output

Write `<RUN>/facts/<TICKER>.json`:

```json
{
  "ticker": "", "company": "", "as_of": "{AS_OF}", "sec_registrant": true, "fiscal_year_L": 2025, "fiscal_year_end_latest": "YYYY-MM-DD (end date of FY L, from the annual report cover or statement headings)", "currency": "USD",
  "m1": {"ceo": "", "ceo_since": "", "shares_owned_excl_options": 0, "shares_calc": "322,388 − 5,722 restricted − 15,200 options = 301,466",
         "base_salary": 0, "salary_year": "", "founder_family_5pct_active": false,
         "ceo_changes_5y": [{"date": "", "from": "", "from_since": "", "to": "", "source": "", "url": ""}],
         "insiders_net_buyers_24m": false, "ceo_sold_over_30pct_24m": false, "trades_note": "", "evidence": [{"fact": "", "quote": "", "source": "", "url": ""}]},
  "say_on_pay": {"meeting_date": "", "for": 0, "against": 0, "abstain": 0, "broker_non_votes": 0, "pct_for": 0.0, "status": "found | no vote held", "evidence": []},
  "red_flags": {
    "item_402_recent": [], "item_402_how_checked": "",
    "icfr": {"fiscal_year_end": "", "management_conclusion": "effective", "auditor_opinion": "unqualified", "material_weaknesses": [], "evidence": []},
    "aaer_recent": [], "other_sec_enforcement": [], "aaer_how_checked": "",
    "non_sec": {"error_restatement": [], "modified_audit_opinion": null, "regulator_findings": [], "evidence": []}
  },
  "info": {"auditor_changes": [], "cfo_departures": [{"name": "", "date": "", "reason": "", "url": ""}], "dual_class": {"exists": false, "detail": ""}},
  "perimeter": {"events": [{"date": "", "type": "", "name": "", "revenue_effect_pct": 0, "figures": "", "source": "", "url": ""}],
                "after_year_end": [], "flagged_years": {"2024": {"cause": "deal | no deal", "explanation": "", "source": "", "url": ""}},
                "restated": {"income_statement_fys": [], "balance_sheet_fys": [], "source": ""}},
  "data": {"amortization_acquired_intangibles": {"2016": 0}, "amortization_basis": "acquired only | total intangibles amortization",
           "impairments_gw_intangibles": {"2016": 0}, "cfo_continuing": {}, "operating_profit_bridge": {}, "debt_like": {}, "business_disposal_losses": {"years": {}}, "evidence": [{"years": "2023-2025", "fact": "", "quote": "", "source": "", "url": ""}]},
  "guidance": {"checked": "YYYY-MM-DD", "how_checked": "FocusAlpha get_guidance_changes", "changes": [{"metric": "", "kind": "level", "period": "FY2026", "date": "", "prior": [0, 0], "current": [0, 0], "unit": "", "source": "", "url": ""}]},
  "business": {"fy": 2025, "top_customers": "", "top_customers_pct": null, "largest_product_line": "", "largest_product_line_pct": null, "production": "own | contract | mixed", "main_channel": "", "quote": "", "source": "", "url": ""},
  "notes": "anything that makes a fact uncertain or the history not comparable"
}
```

Validate: `python3 -c "import json;json.load(open('<path>'))"`. Then reply in 5–8 lines: the say-on-pay %, any red flag found, the CEO multiple inputs, what caused each flagged year, the profit guidance changes for the current year, the concentration facts, and which data facts you could not find. Do not paste the JSON.
