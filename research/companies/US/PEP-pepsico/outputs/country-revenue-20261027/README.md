# PepsiCo country revenue, FY2016–FY2025

Prepared as of 2026-10-27 from the country-revenue table supplied by the user. Every country revenue cell, available growth/share calculation, consolidated total and residual was cross-checked against `research/companies/US/PEP-pepsico/outputs/company-research-to-excel/PEP_model.xlsx`, worksheet `Products & Geography`, range `A13:L50`. The workbook was read only and its hash was checked before and after chart generation. This visualization does not refresh or independently re-audit the original filings.

The single four-panel figure is available as `PEP_country_revenue_2016_2025.png` and `PEP_country_revenue_2016_2025.svg`:

- A: consolidated revenue split between the United States and all non-US markets.
- B: FY2025 revenue by individually disclosed country and the calculated residual, with revenue shares and amounts.
- C: individually disclosed non-US country revenue trends, retaining disclosure gaps.
- D: country revenue YoY growth for FY2017–FY2025. Color intensity is capped at +30%; the printed values retain actual growth, including South Africa's +216.5% in FY2020.

Source amounts are USD millions. Chart amounts are USD hundred millions (亿美元), dividing the source by 100. Displayed values use conventional half-up rounding. Rates retain one decimal except Canada's near-zero FY2017 growth, which is shown to two decimals rather than as negative zero. Printed amounts and rates can differ slightly from sums of rounded labels.

Undisclosed country amounts remain missing: China FY2016, South Africa FY2016–FY2017 and Brazil FY2020. Brazil's FY2020 gap breaks the line; FY2020 and FY2021 YoY rates remain unavailable. The residual excludes every individually shown country for each year, so its historical country coverage changes. It is not plotted as a comparable historical country-growth series. Revenue changes are reported in USD and include FX and transactions; they are not organic growth.

The data, source hash, validation results and reusable builder are under `data/derived/companies/US/PEP-pepsico/country-revenue-20261027/`.
