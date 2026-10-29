# PepsiCo cash flow, as of 2026-10-28

This module resumes the approved cash-flow analysis after the completed balance-sheet/working-capital chapter in Codex chat `01a15710-2dcb-7751-8258-ee4fed618ef6`. The original chat's next turn failed during remote context compaction with a disconnected response stream; a later retry was interrupted before any cash-flow output. No earlier cash-flow module was replaced. The research continues in the current chat using the same company source base and workbook. No report or workbook was edited.

## Figures

- `01_PEP_cash_generation_2016_2026.png` / `.svg`: FY2016–FY2025 and 2026Q3 TTM operating cash flow, capital spending and FCF; cash margins and capital intensity.
- `02_PEP_cash_flow_recovery_2026.png` / `.svg`: 36-week YTD comparisons and a bridge from FY2025Q3 YTD FCF to FY2026Q3 YTD FCF.
- `03_PEP_cumulative_cash_uses_2016_2025.png` / `.svg`: ten-year cumulative cash sources and uses, fully reconciled.
- `04_PEP_dividends_buybacks_coverage_2016_2026.png` / `.svg`: cash dividends, common repurchases, FCF coverage, declared DPS and Core earnings payout ratios.
- `05_PEP_buybacks_net_share_shrink_2016_2026.png` / `.svg`: original period-end common shares, gross repurchases, employee reissuances, actual net shrink and the ten-year compound annual net shrink rate.
- `PEP_Cash_Flow_Charts.zip`: all five figures in PNG and SVG.

## Findings and interpretation

Calculated FCF is consolidated operating cash flow less cash capital spending. It was USD7,623m in FY2016 and USD7,672m in FY2025, a 0.6% increase, versus 58.8% growth in company-defined Core parent net income. This comparison describes long-term growth, not a reconstruction of cash solely from Core profit. Historical cash flow includes pension payments, tax payments, working-capital movements and restructuring/integration payments. GAAP-to-Core expense exclusions do not remove the associated cash costs.

FY2025 calculated FCF improved by USD483m despite a USD420m decline in operating cash flow, because capital spending fell USD903m. The 2025 original MD&A attributes the CFO decline primarily to higher restructuring and acquisition/divestiture-related cash payments. FY2025 cash restructuring payments were USD796m and acquisition/divestiture-related cash payments were USD228m.

FY2026Q3 YTD calculated FCF increased USD2,799m: USD1,023m from less cash absorbed by four working-capital cash-flow lines, USD317m from lower capex and USD1,459m from all other operating cash-flow changes. The last category includes earnings, noncash adjustments, cash taxes and other operating items; it is not labeled pure earnings growth. Latest TTM calculated FCF is USD10,471m.

The 2026Q3 original 10-Q confirms the final USD965m TCJ transition-tax payment has been made. Its conclusion provides an identifiable reduction of a legacy cash obligation, not an increase in operating profit or a guarantee of equivalent future FCF growth. Current operations, capex and cash demands can offset that benefit. FY2025 cash dividends of USD7,638m consumed nearly all USD7,672m of calculated FCF. The historical shareholder-return and cumulative funds requirements were omitted from the first delivery and are completed below; further operating-capital returns and valuation remain separate questions.

## Completion: cumulative allocation and shareholder cash returns

FY2016–FY2025 CFO totaled USD110,833m. Capital spending used USD42,846m, leaving USD67,987m calculated FCF. Cash dividends totaled USD57,978m and common-share repurchases USD16,606m, a combined USD74,584m or109.7% of FCF. After dividends, USD10,009m of FCF remained versus USD16,606m buyback spending. The USD6,597m shortfall is before acquisitions. This does not assign every borrowed dollar to distributions: the full bridge also includes acquisition/investment uses of USD16,526m, business and PPE disposal proceeds USD7,193m, net borrowing/redemption cash inflow USD14,043m, short-term investment net recovery USD2,768m and other mapped flows.

Cumulative cash sources and uses each equal USD137,303m after netting borrowing and short-term investment flows. Other uses include employee-award withholding tax, preferred redemptions, other financing and FX effects; cash plus restricted cash increased USD85m. Acquisition contingent consideration is classified once with acquisition/investment uses, retaining its original financing-statement mapping. Taxes, pensions and operating restructuring/integration payments are already inside CFO. Net borrowing cash is not equated with the balance-sheet debt increase.

Dividends represented77.7% of cumulative dividends plus common buybacks. Declared DPS rose from USD2.9600 in FY2016 to USD5.6225 in FY2025, a7.4% CAGR across nine intervals. These are original disclosed declared DPS, distinct from cash dividends paid. Cash dividends divided by company Core parent income rose from60.0% to68.3%; every annual denominator was reopened in original GAAP/Core reconciliation tables.

The original stockholders' equity statements show common shares of1,448m at FY2015 year-end and1,367m at FY2025 year-end, a net decrease of approximately81m or5.6% across ten fiscal years. Gross repurchase shares sum to approximately133m, employee option/RSU/PSU conversions reissued approximately51m, and a preferred conversion added approximately1m in FY2018. Each annual and latest YTD share rollforward independently reconciles to its source; all quantities inherit the source's million-share rounding. Approximately39% of gross repurchased shares were offset by those issuance/conversion flows. Cash spending and gross share repurchases are different dimensions, not an inferred average repurchase price.

The compound annual net share shrink rate is approximately0.57% per year: 1 − (1,367 / 1,448)^(1 / 10), using FY2015 year-end to FY2025 year-end across ten complete fiscal years. The latest 2026 YTD observation is excluded from this annualization. The EPS denominator uses diluted weighted-average shares, separately: FY2016 1,452m versus FY2025 1,373m. Holding earnings fixed, this denominator difference increases EPS by approximately5.8%. It does not establish whether buyback prices were attractive. The period-end share bridge is not replaced by weighted-average EPS shares.

FY2026Q3 YTD cash dividends were USD5,935m, common cash buybacks USD739m, and shares declined approximately3m from1,367m to1,364m. The same equity table reports USD749m recognized repurchase cost; that USD10m difference from cash paid is retained without inventing a precise settlement/cost bridge. Latest comparable TTM FCF USD10,471m exceeds dividends plus common buybacks USD8,868m by USD1,603m before acquisitions and net debt payments. YTD is not treated as a full year.

Completion evidence is `shareholder-returns-manifest.json`, `shareholder-returns-history.csv` and `shareholder-returns-calculator-results.json` under the same company `data/derived/.../cash-flow-20261028/` directory. The added pass reopened288 present cash-flow/share-count input cells, eleven original equity tables and ten original Core net-income tables; prior cash-generation checks remain separately scoped. The strict financial calculator passed twenty cash reconciliations with zero source-metadata issues. All saved figures were visually inspected, and the source workbook remained unchanged. This completes the cash-flow generation, cumulative allocation and historical shareholder cash-return module; it does not constitute a forecast or investment-return valuation.

## Evidence and limitations

Inputs were read from `research/companies/US/PEP-pepsico/outputs/company-research-to-excel/PEP_model.xlsx`, Cash Flow rows14–72 and Core Reconciliations rows16–20. A total of204 present numeric cash-flow cells were reread from original HTML table coordinates using the existing source bindings. Company-defined FCF equals the calculated FCF plus PPE sale proceeds; it is retained as a separate reconciliation. Historical Core parent net income reuses the original-source-verified profitability module under `data/derived/companies/US/PEP-pepsico/consolidated-profitability-20261028/`.

Original cash-flow sources and explanations are the local immutable 10-K/10-Q originals listed in `data/derived/companies/US/PEP-pepsico/cash-flow-20261028/manifest.json`. Material explanations were independently reopened in FY2018, FY2024, FY2025 and 2026Q3 original HTML. Official Q3 2026 prepared management remarks were reviewed as company commentary; their capital-spending and FCF-conversion targets are guidance, not reported cash.

All chart amounts are USD hundred millions (亿美元); input CSV values remain USD millions. Annual values, 36-week YTD values and derived TTM values are explicitly separate. TTM equals FY2025 plus FY2026Q3 YTD less FY2025Q3 YTD. Working-capital contribution is the sum of cash-flow changes in receivables, inventory, prepaids and payables; it is not the negative change in balance-sheet NWC. Blank source rows are not turned into cash-flow actuals. There is no forecast, normalized-FCF estimate or maintenance/growth-capex split.

Cash-flow data, calculations, original-source checks and the builder are under `data/derived/companies/US/PEP-pepsico/cash-flow-20261028/`. Saved figure inspection found readable labels and no clipping. The workbook SHA-256 was checked before and after generation and remains unchanged. Scoped validation: PASS. Broader assumptions about the persistence of the recovery remain research judgments.
