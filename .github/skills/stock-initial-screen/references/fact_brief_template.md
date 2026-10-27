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
- Deals of more than 25% of revenue closed or announced AFTER the latest fiscal year-end (date, status: closed / pending, revenue effect).
- The coordinator's data flagged the years listed in your prompt (revenue change above 25% in a year; goodwill + intangibles change above 25% of prior-year invested capital; diluted shares up more than 50% in a year). For EACH flagged year say what caused it: a named deal (acquisition / merger / spin-off / separation / disposal / IPO / share conversion), or no deal (organic swing, a one-off charge, an accounting reclassification, a data error) — with the source sentence.
- For a company whose last qualifying deal was a separation, spin-off or disposal: which fiscal years' income statements and which year-end balance sheets the company has restated to the current business (discontinued operations removed). The coordinator counts a year only when its income statement and both balance sheets (opening and closing) are on the current business.
- Held for sale: name every year-end balance sheet in the window that still carries a sold or demerged unit as held for sale (assets and liabilities held for sale), with the amounts and the source. The coordinator counts such a year as clean when the income statement is restated to continuing operations, because the held-for-sale assets can only lower the returns.
- For each deal-flagged year, give the deal's revenue as a % of the company's revenue in the year before, even when it is far below 25%: the screener keeps the window for a deal that fails only the goodwill test, so the coordinator needs the revenue share to tell the two cases apart.

## 6. Data facts (to repair gaps in the normalized financial data)
For each fiscal year FY(L−9) to FY(L) (the prompt gives L), from the 10-K / annual report notes (intangible assets note, segment note, non-GAAP reconciliation, cash flow statement):
- `amortization_acquired_intangibles`: amortization expense of intangible assets acquired in business combinations (customer relationships, technology, trade names, backlog, acquired program assets). Exclude capitalized software, capitalized development costs, deferred financing costs and contract assets. If the company discloses only total "amortization of intangible assets", use that and say so. Each 10-K usually states three years ("amortization expense was $x, $y and $z for fiscal 2025, 2024 and 2023"), so about four 10-Ks cover ten years.
- `impairments_gw_intangibles`: impairment charges on goodwill or intangible assets (not PP&E, not right-of-use assets, not equity investments). Write 0 for a year with none, but only after checking that year's filing.
- `cfo_continuing`: net cash from operating activities from CONTINUING operations, only for years in which the cash flow statement shows discontinued operations. Leave the other years out.
- `debt_like`: litigation or regulatory settlement liabilities that the company pays on a fixed schedule over several years (for example opioid settlements), as `{"label", "years": {FY: {"noncurrent": amount, "current": amount or null, "current_why": ""}}, "source", "url"}`, year-end balances. Both parts count (v4.7): the non-current part is usually its own balance-sheet line; the current part usually sits inside accrued liabilities, so take it from the litigation or contingencies note. If the filing does not disclose the current part, write `null` and say why in `current_why`; the page then says debt is understated in that year. The screener adds both parts to debt in invested capital and in net debt. Leave it empty when there are none; do not include ordinary accrued liabilities, pensions, leases (already in debt), insurance or self-insurance reserves, environmental or landfill obligations, or contingent liabilities that are not yet settled.
- `business_disposal_losses` (v4.7, used by M3 only): losses booked on businesses sold or held for sale (remeasurement to fair value less costs to sell, loss on sale), FY(L−10) to FY(L), as `{"years": {FY: {"loss": amount, "cta_release_included": amount or null, "cta_why": "", "items": ["business, amount"], "filing", "url", "quote"}}, "gains": {FY: amount}}`. `cta_release_included` = the part of the loss that is the release of accumulated other comprehensive loss (past currency translation) where the filing states it; M3 counts the loss less that part. Gains go in `gains` for information; they do not offset losses. Write `{"years": {}}` when the company booked none, but only after checking each year's filing, so the page can say the item was checked.
Give amounts in millions of the reporting currency, as positive numbers, keyed by fiscal year (the company's own fiscal year, which may not end in December). Cite the document for each group of years.

## Tools and how to read filings

- **FA = FocusAlpha; check it first.** Discover relevant current tools, resolve issuer/listing, then inspect filing/statement/ownership/compensation/insider/event coverage. Use `list_datasets`, `list_coverage` or `list_documents` if routing is unclear. Keep all relevant periods, currency, unit and original disclosure metadata.
- **Original disclosures fill gaps.** After an empty, stale, inaccessible or incompatible FocusAlpha result, record tool/query and gap; fetch regulator, exchange or company IR originals. Do not assume an old access failure still applies. Preserve full documents and search text in your scratch folder. Fiscal.ai is disabled: do not discover it, connect, install dependencies, run `fiscal_exec.py`, or use a Fiscal.ai fallback.
- **Gangtise is optional context.** Where useful, use `report` / `foreign_report`, `summary` and `stock_one_pager` for industry context, contradictions or leads. Treat forecasts, expert statements and generated summaries as attributed views. Verify a score-changing fact against its primary disclosure; if unverified, keep it outside scoring and state the gap. Follow `SKILL_DIR/references/gangtise-screening.md`.
- **Trace every figure.** In JSON `source`/`evidence`, name `FocusAlpha (exact tool)` or the actual source, original document/date/URL, reporting period, unit and local raw path. Label calculations and list input sources. Store query/results/fallbacks in `scratch/<TICKER>/source_ledger.json` for merging by the coordinator. Preserve conflicting evidence. Missing is null, never an assumed zero.
- All source material remains within the assigned run's source/scratch directory. Never put personal information in request headers, URLs or User-Agent strings.

## Output

Write `<RUN>/facts/<TICKER>.json`:

```json
{
  "ticker": "", "company": "", "as_of": "{AS_OF}", "sec_registrant": true, "fiscal_year_L": 2025, "fiscal_year_end_latest": "YYYY-MM-DD (end date of FY L, from the annual report cover or statement headings)", "currency": "USD",
  "m1": {"ceo": "", "ceo_since": "", "shares_owned_excl_options": null, "shares_calc": "322,388 − 5,722 restricted − 15,200 options = 301,466",
         "base_salary": null, "base_salary_currency": "", "salary_year": "", "founder_family_5pct_active": null,
         "ceo_changes_5y": [{"date": "", "from": "", "from_since": "", "to": "", "source": "", "url": ""}],
         "insiders_net_buyers_24m": null, "ceo_sold_over_30pct_24m": null, "trades_note": "", "evidence": [{"fact": "", "quote": "", "source": "", "url": ""}]},
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
           "impairments_gw_intangibles": {"2016": 0}, "cfo_continuing": {}, "debt_like": {}, "business_disposal_losses": {"years": {}}, "evidence": [{"years": "2023-2025", "fact": "", "quote": "", "source": "", "url": ""}]},
  "notes": "anything that makes a fact uncertain or the history not comparable"
}
```

Validate with the Workspace interpreter: `"$PY" -c "import json;json.load(open('<path>'))"`. Then reply in 5–8 lines: the say-on-pay %, any red flag found, the CEO multiple inputs, what caused each flagged year, and which data facts you could not find. Do not paste the JSON.
