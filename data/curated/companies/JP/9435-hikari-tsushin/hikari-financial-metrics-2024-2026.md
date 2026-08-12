# Derived Financial Metrics

- Entity: Hikari Tsushin, Inc.
- Currency/scale: JPY million
- Periods: FY2024, FY2025, FY2026

## Reconciliation Checks

| Period | Check | Status | Difference | Formula |
|---|---|---|---:|---|
| FY2024 | Assets = liabilities + equity | pass | 0.000000 | total assets = total liabilities + total equity |
| FY2024 | Consolidated income = parent + NCI | pass | 0.000000 | consolidated net income = parent net income + NCI net income |
| FY2024 | Ending cash = beginning cash + net change | pass | 0.000000 | cash_end = cash_begin + net_change_cash |
| FY2024 | Net cash change = CFO + CFI + CFF + FX + other | pass | 1.000000 | net_change_cash = CFO + CFI + CFF + FX + other_cash_effect |
| FY2024 | Cash-flow ending cash = balance-sheet cash | pass | 0.000000 | cash_end = cash_and_equivalents |
| FY2025 | Assets = liabilities + equity | pass | 1.000000 | total assets = total liabilities + total equity |
| FY2025 | Consolidated income = parent + NCI | pass | 1.000000 | consolidated net income = parent net income + NCI net income |
| FY2025 | Ending cash = beginning cash + net change | pass | 0.000000 | cash_end = cash_begin + net_change_cash |
| FY2025 | Net cash change = CFO + CFI + CFF + FX + other | pass | 0.000000 | net_change_cash = CFO + CFI + CFF + FX + other_cash_effect |
| FY2025 | Cash-flow ending cash = balance-sheet cash | pass | 0.000000 | cash_end = cash_and_equivalents |
| FY2026 | Assets = liabilities + equity | pass | 0.000000 | total assets = total liabilities + total equity |
| FY2026 | Consolidated income = parent + NCI | pass | 1.000000 | consolidated net income = parent net income + NCI net income |
| FY2026 | Ending cash = beginning cash + net change | pass | 0.000000 | cash_end = cash_begin + net_change_cash |
| FY2026 | Net cash change = CFO + CFI + CFF + FX + other | pass | 2.000000 | net_change_cash = CFO + CFI + CFF + FX + other_cash_effect |
| FY2026 | Cash-flow ending cash = balance-sheet cash | pass | 0.000000 | cash_end = cash_and_equivalents |

## Metrics

| Period | Category | Metric | Result | Status | Formula and inputs |
|---|---|---|---:|---|---|
| FY2024 | profitability | Gross margin | 52.36% | computed | gross profit / revenue; gross profit=315,170.000; revenue=601,948.000 |
| FY2024 | profitability | Operating margin | 15.71% | computed | operating profit / revenue; operating profit=94,546.000; revenue=601,948.000 |
| FY2024 | profitability | EBITDA margin | 18.12% | computed | EBITDA / revenue; ebitda_calculated=109,102.000; revenue=601,948.000 |
| FY2024 | profitability | Consolidated net margin | 20.56% | computed | consolidated net income / revenue; consolidated net income=123,745.000; revenue=601,948.000 |
| FY2024 | profitability | Parent net margin | 20.30% | computed | parent net income / revenue; parent net income=122,225.000; revenue=601,948.000 |
| FY2024 | liquidity | Current ratio | 1.91x | computed | current assets / current liabilities; current assets=840,810.000; current liabilities=439,195.000 |
| FY2024 | liquidity | Cash-only ratio | 1.13x | computed | cash and equivalents / current liabilities; cash and equivalents=494,850.000; current liabilities=439,195.000 |
| FY2024 | solvency | Equity ratio | 39.41% | computed | total equity / total assets; total equity=819,249.000; total assets=2,078,956.000 |
| FY2024 | solvency | Gross debt ex leases / assets | 39.56% | computed | gross debt excluding leases / total assets; gross debt ex leases=822,493.000; total assets=2,078,956.000 |
| FY2024 | solvency | Debt / equity ex leases | 1.00x | computed | gross debt excluding leases / total equity; gross debt ex leases=822,493.000; total equity=819,249.000 |
| FY2024 | cash_conversion | CFO margin | 21.63% | computed | CFO / revenue; CFO=130,200.000; revenue=601,948.000 |
| FY2024 | cash_conversion | CFO / EBITDA | 1.19x | computed | CFO / EBITDA; CFO=130,200.000; ebitda_calculated=109,102.000 |
| FY2024 | cash_conversion | Capex intensity | 3.04% | computed | capex / revenue; capex=18,283.000; revenue=601,948.000 |
| FY2024 | cash_conversion | CFO / capex | 7.12x | computed | CFO / capex; CFO=130,200.000; capex=18,283.000 |
| FY2024 | cash_conversion | Cash flow after capex margin | 18.59% | computed | (CFO - capex) / revenue; cash flow after capex=111,917.000; revenue=601,948.000 |
| FY2024 | debt_bridge | Gross debt excluding leases | 822,493.000 million | computed | short-term debt + long-term debt; short-term debt=156,386.000; long-term debt=666,107.000; analyst calculation |
| FY2024 | debt_bridge | Net debt excluding leases | 327,643.000 million | computed | gross debt excluding leases - cash - eligible liquid investments; gross debt excluding leases=822,493.000; cash and equivalents=494,850.000; analyst calculation |
| FY2024 | leverage | Net debt ex leases / EBITDA | 3.00x | computed | net debt excluding leases / pre-lease EBITDA; net debt ex leases=327,643.000; ebitda_calculated=109,102.000; analyst calculation; cash and eligible liquid investments are netted |
| FY2024 | coverage | CFO cash-interest coverage | 13.54x | computed | CFO / cash interest paid; CFO=130,200.000; cash interest paid=9,619.000; inspect whether interest paid is classified within CFO |
| FY2024 | earnings_quality | CFO / consolidated net income | 1.05x | computed | CFO / consolidated net income; CFO=130,200.000; consolidated net income=123,745.000 |
| FY2024 | cash_conversion | Cash flow after capex | 111,917.000 million | computed | CFO - capex_total; CFO=130,200.000; capex_total=18,283.000; analyst calculation; not automatically the issuer's FCF |
| FY2024 | cash_conversion | D&A / capex | 0.80x | computed | D&A / capex_total; D&A=14,556.000; capex=18,283.000 |
| FY2025 | growth | Revenue growth | 14.06% | computed | current revenue / prior revenue - 1; current revenue=686,553.000; prior revenue=601,948.000 |
| FY2025 | profitability | Gross margin | 50.00% | computed | gross profit / revenue; gross profit=343,298.000; revenue=686,553.000 |
| FY2025 | profitability | Operating margin | 15.30% | computed | operating profit / revenue; operating profit=105,036.000; revenue=686,553.000 |
| FY2025 | profitability | EBITDA margin | 17.35% | computed | EBITDA / revenue; ebitda_calculated=119,112.000; revenue=686,553.000 |
| FY2025 | profitability | Consolidated net margin | 17.67% | computed | consolidated net income / revenue; consolidated net income=121,288.000; revenue=686,553.000 |
| FY2025 | profitability | Parent net margin | 17.12% | computed | parent net income / revenue; parent net income=117,523.000; revenue=686,553.000 |
| FY2025 | liquidity | Current ratio | 1.68x | computed | current assets / current liabilities; current assets=848,880.000; current liabilities=505,183.000 |
| FY2025 | liquidity | Cash-only ratio | 0.93x | computed | cash and equivalents / current liabilities; cash and equivalents=470,273.000; current liabilities=505,183.000 |
| FY2025 | solvency | Equity ratio | 39.80% | computed | total equity / total assets; total equity=943,569.000; total assets=2,371,026.000 |
| FY2025 | solvency | Gross debt ex leases / assets | 39.41% | computed | gross debt excluding leases / total assets; gross debt ex leases=934,320.000; total assets=2,371,026.000 |
| FY2025 | solvency | Debt / equity ex leases | 0.99x | computed | gross debt excluding leases / total equity; gross debt ex leases=934,320.000; total equity=943,569.000 |
| FY2025 | cash_conversion | CFO margin | 12.36% | computed | CFO / revenue; CFO=84,836.000; revenue=686,553.000 |
| FY2025 | cash_conversion | CFO / EBITDA | 0.71x | computed | CFO / EBITDA; CFO=84,836.000; ebitda_calculated=119,112.000 |
| FY2025 | cash_conversion | Capex intensity | 3.14% | computed | capex / revenue; capex=21,553.000; revenue=686,553.000 |
| FY2025 | cash_conversion | CFO / capex | 3.94x | computed | CFO / capex; CFO=84,836.000; capex=21,553.000 |
| FY2025 | cash_conversion | Cash flow after capex margin | 9.22% | computed | (CFO - capex) / revenue; cash flow after capex=63,283.000; revenue=686,553.000 |
| FY2025 | debt_bridge | Gross debt excluding leases | 934,320.000 million | computed | short-term debt + long-term debt; short-term debt=179,876.000; long-term debt=754,444.000; analyst calculation |
| FY2025 | debt_bridge | Net debt excluding leases | 464,047.000 million | computed | gross debt excluding leases - cash - eligible liquid investments; gross debt excluding leases=934,320.000; cash and equivalents=470,273.000; analyst calculation |
| FY2025 | leverage | Net debt ex leases / EBITDA | 3.90x | computed | net debt excluding leases / pre-lease EBITDA; net debt ex leases=464,047.000; ebitda_calculated=119,112.000; analyst calculation; cash and eligible liquid investments are netted |
| FY2025 | coverage | CFO cash-interest coverage | 7.74x | computed | CFO / cash interest paid; CFO=84,836.000; cash interest paid=10,957.000; inspect whether interest paid is classified within CFO |
| FY2025 | earnings_quality | CFO / consolidated net income | 0.70x | computed | CFO / consolidated net income; CFO=84,836.000; consolidated net income=121,288.000 |
| FY2025 | cash_conversion | Cash flow after capex | 63,283.000 million | computed | CFO - capex_total; CFO=84,836.000; capex_total=21,553.000; analyst calculation; not automatically the issuer's FCF |
| FY2025 | cash_conversion | D&A / capex | 0.65x | computed | D&A / capex_total; D&A=14,076.000; capex=21,553.000 |
| FY2025 | returns | ROA | 5.45% | computed | consolidated net income / average total assets; consolidated net income=121,288.000; average total assets=2,224,991.000 |
| FY2025 | returns | Parent ROE | 13.78% | computed | parent net income / average parent equity; parent net income=117,523.000; average parent equity=852,623.000 |
| FY2025 | returns | Consolidated ROE | 13.76% | computed | consolidated net income / average total equity; consolidated net income=121,288.000; average total equity=881,409.000 |
| FY2025 | returns | Asset turnover | 0.31x | computed | revenue / average total assets; revenue=686,553.000; average total assets=2,224,991.000 |
| FY2025 | earnings_quality | Accrual ratio | 1.64% | computed | (consolidated net income - CFO) / average total assets; net income minus CFO=36,452.000; average total assets=2,224,991.000 |
| FY2026 | growth | Revenue growth | 7.03% | computed | current revenue / prior revenue - 1; current revenue=734,791.000; prior revenue=686,553.000 |
| FY2026 | profitability | Gross margin | 49.53% | computed | gross profit / revenue; gross profit=363,956.000; revenue=734,791.000 |
| FY2026 | profitability | Operating margin | 15.88% | computed | operating profit / revenue; operating profit=116,664.000; revenue=734,791.000 |
| FY2026 | profitability | EBITDA margin | 18.12% | computed | EBITDA / revenue; ebitda_calculated=133,139.000; revenue=734,791.000 |
| FY2026 | profitability | Consolidated net margin | 21.26% | computed | consolidated net income / revenue; consolidated net income=156,229.000; revenue=734,791.000 |
| FY2026 | profitability | Parent net margin | 20.55% | computed | parent net income / revenue; parent net income=151,014.000; revenue=734,791.000 |
| FY2026 | liquidity | Current ratio | 2.11x | computed | current assets / current liabilities; current assets=1,019,640.000; current liabilities=482,597.000 |
| FY2026 | liquidity | Cash-only ratio | 1.12x | computed | cash and equivalents / current liabilities; cash and equivalents=539,854.000; current liabilities=482,597.000 |
| FY2026 | solvency | Equity ratio | 42.67% | computed | total equity / total assets; total equity=1,217,650.000; total assets=2,853,866.000 |
| FY2026 | solvency | Gross debt ex leases / assets | 38.14% | computed | gross debt excluding leases / total assets; gross debt ex leases=1,088,472.000; total assets=2,853,866.000 |
| FY2026 | solvency | Debt / equity ex leases | 0.89x | computed | gross debt excluding leases / total equity; gross debt ex leases=1,088,472.000; total equity=1,217,650.000 |
| FY2026 | cash_conversion | CFO margin | 7.77% | computed | CFO / revenue; CFO=57,073.000; revenue=734,791.000 |
| FY2026 | cash_conversion | CFO / EBITDA | 0.43x | computed | CFO / EBITDA; CFO=57,073.000; ebitda_calculated=133,139.000 |
| FY2026 | cash_conversion | Capex intensity | 2.64% | computed | capex / revenue; capex=19,399.000; revenue=734,791.000 |
| FY2026 | cash_conversion | CFO / capex | 2.94x | computed | CFO / capex; CFO=57,073.000; capex=19,399.000 |
| FY2026 | cash_conversion | Cash flow after capex margin | 5.13% | computed | (CFO - capex) / revenue; cash flow after capex=37,674.000; revenue=734,791.000 |
| FY2026 | debt_bridge | Gross debt excluding leases | 1,088,472.000 million | computed | short-term debt + long-term debt; short-term debt=161,307.000; long-term debt=927,165.000; analyst calculation |
| FY2026 | debt_bridge | Net debt excluding leases | 548,618.000 million | computed | gross debt excluding leases - cash - eligible liquid investments; gross debt excluding leases=1,088,472.000; cash and equivalents=539,854.000; analyst calculation |
| FY2026 | leverage | Net debt ex leases / EBITDA | 4.12x | computed | net debt excluding leases / pre-lease EBITDA; net debt ex leases=548,618.000; ebitda_calculated=133,139.000; analyst calculation; cash and eligible liquid investments are netted |
| FY2026 | coverage | CFO cash-interest coverage | 3.58x | computed | CFO / cash interest paid; CFO=57,073.000; cash interest paid=15,944.000; inspect whether interest paid is classified within CFO |
| FY2026 | earnings_quality | CFO / consolidated net income | 0.37x | computed | CFO / consolidated net income; CFO=57,073.000; consolidated net income=156,229.000 |
| FY2026 | cash_conversion | Cash flow after capex | 37,674.000 million | computed | CFO - capex_total; CFO=57,073.000; capex_total=19,399.000; analyst calculation; not automatically the issuer's FCF |
| FY2026 | cash_conversion | D&A / capex | 0.85x | computed | D&A / capex_total; D&A=16,475.000; capex=19,399.000 |
| FY2026 | returns | ROA | 5.98% | computed | consolidated net income / average total assets; consolidated net income=156,229.000; average total assets=2,612,446.000 |
| FY2026 | returns | Parent ROE | 14.38% | computed | parent net income / average parent equity; parent net income=151,014.000; average parent equity=1,050,218.000 |
| FY2026 | returns | Consolidated ROE | 14.46% | computed | consolidated net income / average total equity; consolidated net income=156,229.000; average total equity=1,080,609.500 |
| FY2026 | returns | Asset turnover | 0.28x | computed | revenue / average total assets; revenue=734,791.000; average total assets=2,612,446.000 |
| FY2026 | earnings_quality | Accrual ratio | 3.80% | computed | (consolidated net income - CFO) / average total assets; net income minus CFO=99,156.000; average total assets=2,612,446.000 |

## Warnings

- FY2024: ebitda_calculated = operating_profit + depreciation_amortization
- FY2024: net debt subtracts cash only; liquid_investments not supplied
- FY2025: ebitda_calculated = operating_profit + depreciation_amortization
- FY2025: net debt subtracts cash only; liquid_investments not supplied
- FY2026: ebitda_calculated = operating_profit + depreciation_amortization
- FY2026: net debt subtracts cash only; liquid_investments not supplied

## Evidence Index

| Period | Canonical key | Value | Source label | Statement | Source locator | Status |
|---|---|---:|---|---|---|---|
| FY2024 | revenue | 601,948.000 | Revenue | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2024 | cost_of_revenue | 286,778.000 | Cost of sales | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2024 | gross_profit | 315,170.000 | Gross profit | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2024 | operating_profit | 94,546.000 | Operating profit | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2024 | depreciation_amortization | 14,556.000 | Depreciation and amortization | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2024 | income_before_tax | 168,000.000 | Profit before tax | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2024 | income_tax_expense | 44,255.000 | Income tax expense | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2024 | net_income_consolidated | 123,745.000 | Profit | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2024 | net_income_parent | 122,225.000 | Owners of parent | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2024 | net_income_nci | 1,520.000 | Non-controlling interests | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2024 | cash_and_equivalents | 494,850.000 | Cash and cash equivalents | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-38th-fy2025_consolidated_financial_statements.pdf; printed p.1 | reported |
| FY2024 | current_assets | 840,810.000 | Total current assets | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-38th-fy2025_consolidated_financial_statements.pdf; printed p.1 | reported |
| FY2024 | total_assets | 2,078,956.000 | Total assets | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-38th-fy2025_consolidated_financial_statements.pdf; printed p.1 | reported |
| FY2024 | short_term_debt | 156,386.000 | Interest-bearing liabilities - current | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-38th-fy2025_consolidated_financial_statements.pdf; printed p.2 | reported |
| FY2024 | long_term_debt | 666,107.000 | Interest-bearing liabilities - non-current | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-38th-fy2025_consolidated_financial_statements.pdf; printed p.2 | reported |
| FY2024 | current_liabilities | 439,195.000 | Total current liabilities | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-38th-fy2025_consolidated_financial_statements.pdf; printed p.2 | reported |
| FY2024 | total_liabilities | 1,259,707.000 | Total liabilities | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-38th-fy2025_consolidated_financial_statements.pdf; printed p.2 | reported |
| FY2024 | parent_equity | 790,478.000 | Total equity attributable to owners of parent | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-38th-fy2025_consolidated_financial_statements.pdf; printed p.2 | reported |
| FY2024 | nci | 28,771.000 | Non-controlling interests | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-38th-fy2025_consolidated_financial_statements.pdf; printed p.2 | reported |
| FY2024 | total_equity | 819,249.000 | Total equity | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-38th-fy2025_consolidated_financial_statements.pdf; printed p.2 | reported |
| FY2024 | cfo | 130,200.000 | Net cash provided by operating activities | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2024 | cfi | -94,718.000 | Net cash used in investing activities | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2024 | cff | 55,322.000 | Net cash provided by financing activities | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2024 | capex_total | 18,283.000 | Purchase of property plant equipment and intangible assets | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2024 | interest_paid | 9,619.000 | Interest paid | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2024 | dividends_paid | 25,958.000 | Dividends paid | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2024 | buybacks | 13,003.000 | Purchase of treasury shares | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2024 | cash_begin | 389,366.000 | Cash and cash equivalents at beginning of period | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2024 | cash_end | 494,850.000 | Cash and cash equivalents at end of period | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2024 | net_change_cash | 105,484.000 | Change including transfer to assets held for sale | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.6 | calculated |
| FY2024 | fx_cash_effect | 18,336.000 | Effect of exchange rate changes | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2024 | other_cash_effect | -3,657.000 | Transfer to assets held for sale | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-37th-fy2024_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2025 | revenue | 686,553.000 | Revenue | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2025 | cost_of_revenue | 343,254.000 | Cost of sales | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2025 | gross_profit | 343,298.000 | Gross profit | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2025 | operating_profit | 105,036.000 | Operating profit | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2025 | depreciation_amortization | 14,076.000 | Depreciation and amortization | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2025 | income_before_tax | 150,718.000 | Profit before tax | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2025 | income_tax_expense | 29,430.000 | Income tax expense | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2025 | net_income_consolidated | 121,288.000 | Profit | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2025 | net_income_parent | 117,523.000 | Owners of parent | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2025 | net_income_nci | 3,764.000 | Non-controlling interests | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2025 | cash_and_equivalents | 470,273.000 | Cash and cash equivalents | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.1 | reported |
| FY2025 | current_assets | 848,880.000 | Total current assets | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.1 | reported |
| FY2025 | total_assets | 2,371,026.000 | Total assets | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.1 | reported |
| FY2025 | short_term_debt | 179,876.000 | Interest-bearing liabilities - current | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.2 | reported |
| FY2025 | long_term_debt | 754,444.000 | Interest-bearing liabilities - non-current | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.2 | reported |
| FY2025 | current_liabilities | 505,183.000 | Total current liabilities | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.2 | reported |
| FY2025 | total_liabilities | 1,427,456.000 | Total liabilities | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.2 | reported |
| FY2025 | parent_equity | 914,768.000 | Total equity attributable to owners of parent | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.2 | reported |
| FY2025 | nci | 28,800.000 | Non-controlling interests | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.2 | reported |
| FY2025 | total_equity | 943,569.000 | Total equity | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.2 | reported |
| FY2025 | cfo | 84,836.000 | Net cash provided by operating activities | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2025 | cfi | -177,251.000 | Net cash used in investing activities | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2025 | cff | 66,718.000 | Net cash provided by financing activities | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2025 | capex_total | 21,553.000 | Purchase of property plant equipment and intangible assets | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2025 | interest_paid | 10,957.000 | Interest paid | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2025 | dividends_paid | 30,222.000 | Dividends paid | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2025 | buybacks | 10,001.000 | Purchase of treasury shares | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2025 | cash_begin | 494,850.000 | Cash and cash equivalents at beginning of period | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2025 | cash_end | 470,273.000 | Cash and cash equivalents at end of period | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2025 | net_change_cash | -24,577.000 | Change including transfer from held-for-sale classification | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | calculated |
| FY2025 | fx_cash_effect | -2,537.000 | Effect of exchange rate changes | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2025 | other_cash_effect | 3,657.000 | Transfer from assets held for sale | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2026 | revenue | 734,791.000 | Revenue | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2026 | cost_of_revenue | 370,835.000 | Cost of sales | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2026 | gross_profit | 363,956.000 | Gross profit | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2026 | operating_profit | 116,664.000 | Operating profit | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2026 | depreciation_amortization | 16,475.000 | Depreciation and amortization | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2026 | income_before_tax | 199,081.000 | Profit before tax | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2026 | income_tax_expense | 42,852.000 | Income tax expense | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2026 | net_income_consolidated | 156,229.000 | Profit | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2026 | net_income_parent | 151,014.000 | Owners of parent | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2026 | net_income_nci | 5,214.000 | Non-controlling interests | income_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.3 | reported |
| FY2026 | cash_and_equivalents | 539,854.000 | Cash and cash equivalents | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.1 | reported |
| FY2026 | current_assets | 1,019,640.000 | Total current assets | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.1 | reported |
| FY2026 | total_assets | 2,853,866.000 | Total assets | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.1 | reported |
| FY2026 | short_term_debt | 161,307.000 | Interest-bearing liabilities - current | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.2 | reported |
| FY2026 | long_term_debt | 927,165.000 | Interest-bearing liabilities - non-current | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.2 | reported |
| FY2026 | current_liabilities | 482,597.000 | Total current liabilities | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.2 | reported |
| FY2026 | total_liabilities | 1,636,216.000 | Total liabilities | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.2 | reported |
| FY2026 | parent_equity | 1,185,668.000 | Total equity attributable to owners of parent | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.2 | reported |
| FY2026 | nci | 31,982.000 | Non-controlling interests | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.2 | reported |
| FY2026 | total_equity | 1,217,650.000 | Total equity | balance_sheet | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.2 | reported |
| FY2026 | cfo | 57,073.000 | Net cash provided by operating activities | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2026 | cfi | -104,100.000 | Net cash used in investing activities | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2026 | cff | 104,685.000 | Net cash provided by financing activities | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2026 | capex_total | 19,399.000 | Purchase of property plant equipment and intangible assets | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2026 | interest_paid | 15,944.000 | Interest paid | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2026 | dividends_paid | 32,141.000 | Dividends paid | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2026 | buybacks | 6,143.000 | Purchase of treasury shares | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2026 | cash_begin | 470,273.000 | Cash and cash equivalents at beginning of period | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2026 | cash_end | 539,854.000 | Cash and cash equivalents at end of period | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2026 | net_change_cash | 69,581.000 | Cash end minus cash begin | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | calculated |
| FY2026 | fx_cash_effect | 11,921.000 | Effect of exchange rate changes | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
| FY2026 | other_cash_effect | 0.000 | No other cash scope effect reported | cash_flow_statement | sources/companies/JP/9435-hikari-tsushin/official-website/2026-08-13/raw/pdfs/en-39th-fy2026_consolidated_financial_statements.pdf; printed p.6 | reported |
