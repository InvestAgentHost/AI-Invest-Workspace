# PepsiCo revenue growth attribution, FY2016–FY2025

As of: 2026-10-26. Scope: consolidated PepsiCo revenue, full fiscal years. No forecast or workbook changes.

## Outputs

- `PEP_revenue_growth_attribution.png`: high-resolution chart for research reading and Word insertion.
- `PEP_revenue_growth_attribution.svg`: vector chart with embedded glyph paths.
- `PEP_revenue_growth_attribution.csv`: source-linked numerical series; revenue in USD millions, growth in percent and contribution in percentage points.
- `source_manifest.json`: original URLs, source paths, hashes, locators and validation results.

## Definitions and calculation limits

- The upper panel shows revenue in USD 100 million. Revenue and precise organic growth are from `research/companies/US/PEP-pepsico/outputs/company-research-to-excel/PEP_model.xlsx`, `Operating Metrics!C17:L32`.
- Reported revenue growth is calculated from annual revenue. FY2016 uses the FY2015 comparative revenue of USD 63,056 million in the 2016 10-K.
- Volume is the company's consolidated contribution to revenue growth in its annual revenue bridge. It is not a weighted average of separately disclosed food weight growth and beverage case growth. The historical label changes from Volume to Organic Volume; each year's original bridge and its footnotes govern.
- Price/mix is effective net pricing, including discrete price actions, sales incentives and product, package and country mix. It is not a same-product selling-price index.
- FX and acquisitions/divestitures are shown as contributions to reported growth. The adjustment-to-organic signs in the later annual tables are reversed. Zero means company-rounded zero, not necessarily an exactly zero economic impact.
- Organic growth is an overlapping subtotal, approximately volume plus price/mix. It is shown only as a line and is not added as a separate contribution bar.
- Structural contributions include separately disclosed 53rd-week effects and the FY2016 Venezuela deconsolidation. FY2018 sales-tax presentation rounds to zero at group level; no unsupported exact figure has been inferred.
- Company contribution disclosures generally use 0.5- or 1-point rounding, while headline organic rates and calculated reported rates have finer precision. The hatched residual is `reported growth - sum(company-rounded driver contributions)`. It is a reconciliation calculation, not an additional business driver. Organic growth may also differ from disclosed volume plus price/mix due to rounding; this difference is retained in the CSV rather than silently assigned to volume.
- Positive and negative factors are stacked separately. Their net, including the explicit residual, equals reported growth. The top of only the positive stack is not total growth.
- Phase labels are analyst interpretation. Sources support a particularly large price/mix contribution in FY2022–FY2023 and negative volume contributions in FY2023–FY2025. Neither history nor chart implies a future growth forecast.

## Source locations

| Fiscal year | Original filing | Prepared local source, Workspace-relative | Locator |
| --- | --- | --- | --- |
| FY2016 | [SEC-10K-2016-12-31](https://www.sec.gov/Archives/edgar/data/77476/000007747617000010/pepsico201610-k.htm) | `sources/companies/US/PEP-pepsico/sec/prepared-v3/SEC-10K-2016-12-31/document.md` | document.md lines 1652-1658; Total column/row |
| FY2017 | [SEC-10K-2017-12-30](https://www.sec.gov/Archives/edgar/data/77476/000007747618000012/pepsico201710-k.htm) | `sources/companies/US/PEP-pepsico/sec/prepared-v3/SEC-10K-2017-12-30/document.md` | document.md lines 1541-1546; Total column/row |
| FY2018 | [SEC-10K-2018-12-29](https://www.sec.gov/Archives/edgar/data/77476/000007747619000017/pepsico201810-k.htm) | `sources/companies/US/PEP-pepsico/sec/prepared-v3/SEC-10K-2018-12-29/document.md` | document.md lines 1515-1529; Total column/row |
| FY2019 | [SEC-10K-2019-12-28](https://www.sec.gov/Archives/edgar/data/77476/000007747620000015/pepsico201910-k.htm) | `sources/companies/US/PEP-pepsico/sec/prepared-v3/SEC-10K-2019-12-28/document.md` | document.md lines 1202-1217; Total column/row |
| FY2020 | [SEC-10K-2020-12-26](https://www.sec.gov/Archives/edgar/data/77476/000007747621000007/pep-20201226.htm) | `sources/companies/US/PEP-pepsico/sec/prepared-v3/SEC-10K-2020-12-26/document.md` | document.md lines 938-953; Total column/row |
| FY2021 | [SEC-10K-2021-12-25](https://www.sec.gov/Archives/edgar/data/77476/000007747622000010/pep-20211225.htm) | `sources/companies/US/PEP-pepsico/sec/prepared-v3/SEC-10K-2021-12-25/document.md` | document.md lines 925-940; Total column/row |
| FY2022 | [SEC-10K-2022-12-31](https://www.sec.gov/Archives/edgar/data/77476/000007747623000007/pep-20221231.htm) | `sources/companies/US/PEP-pepsico/sec/prepared-v3/SEC-10K-2022-12-31/document.md` | document.md lines 970-985; Total column/row |
| FY2023 | [SEC-10K-2023-12-30](https://www.sec.gov/Archives/edgar/data/77476/000007747624000008/pep-20231230.htm) | `sources/companies/US/PEP-pepsico/sec/prepared-v3/SEC-10K-2023-12-30/document.md` | document.md lines 1025-1040; Total column/row |
| FY2024 | [SEC-10K-2024-12-28](https://www.sec.gov/Archives/edgar/data/77476/000007747625000007/pep-20241228.htm) | `sources/companies/US/PEP-pepsico/sec/prepared-v3/SEC-10K-2024-12-28/document.md` | document.md lines 1043-1058; Total column/row |
| FY2025 | [SEC-10K-2025-12-27](https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/pep-20251227.htm) | `sources/companies/US/PEP-pepsico/sec/prepared-v3/SEC-10K-2025-12-27/document.md` | document.md lines 1014-1028; Total column/row |

## Verification

All ten years are present; annual revenue matches the workbook; pricing, FX and M&A signs/values were cross-checked with the workbook; each charted bridge reconciles after the explicit residual. The workbook was read only and its content was not changed. Original source files were not modified.
