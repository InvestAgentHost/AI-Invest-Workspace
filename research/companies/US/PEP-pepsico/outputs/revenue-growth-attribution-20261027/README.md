# PepsiCo revenue attribution chart, revised 2026-10-27

Version status, 2026-10-29: this is the current reading version. The previous 2026-10-26 PNG/SVG were permanently deleted at the user's explicit request. The initial small data and source records remain at their original paths.

Historical source cutoff: 2026-10-26. Chart revision: 2026-10-27. Scope: FY2016–FY2025 consolidated reported net revenue. No forecast or source refresh.

## Outputs and changes

- `PEP_revenue_growth_attribution.png`: revised high-resolution chart.
- `PEP_revenue_growth_attribution.svg`: vector version with embedded glyph paths.
- `PEP_revenue_growth_attribution.csv`: unchanged, source-linked historical growth bridge.
- `PEP_revenue_cagr.csv`: full-period and adjacent-subperiod revenue CAGRs, with end points and interval counts.
- `source_manifest.json`: original sources, locators, hashes and validation results.

The upper revenue bars now include a reported revenue YoY line on the secondary (right) axis, with every annual growth rate labeled. Four cards report the full-period CAGR and three continuous historical subperiods. All ten price/mix contributions are explicitly labeled within their bars and in a year-aligned numerical strip; volume and organic growth are also fully shown in that strip. FY2017 and FY2022 rounded-zero volume contributions are shown as green hollow circles and `0*`.

## Previously missing labels

FY2017 and FY2022 consolidated volume contributions are rounded zero in the original annual revenue bridges (shown as dashes by the issuer), so they have no nonzero bar height. They are not unavailable data, and do not imply that all physical food and beverage volumes were flat. In the previous chart, some price/mix labels were hidden by the plotting code to avoid overlap. That was a presentation limitation, not absent disclosure. The revised chart keeps these labels visible and supplies a consistently aligned value strip.

## CAGR and attribution definitions

CAGR = (ending reported revenue / starting reported revenue)^(1 / (ending fiscal year - starting fiscal year)) - 1. FY2016 to FY2025 has nine growth intervals. CAGRs describe reported revenue and include FX, M&A/disposals and fiscal-calendar effects; they are not organic revenue CAGRs or forecasts. The shorter intervals are adjacent and cover FY2016–FY2025 without gaps.

Volume is the issuer's consolidated revenue-growth contribution, not the physical volume growth separately reported for foods or beverages. Effective net pricing includes discrete prices, incentives and product/package/country mix. Organic growth is an overlapping subtotal and is shown as a line, not a second contribution bar. Company-rounded contribution points may not sum to exact reported growth; the explicit hatched residual is a reconciliation calculation without an independent business interpretation. Positive and negative contribution stacks must be netted. FX and M&A signs express contribution to reported growth, reversing the adjustment-to-organic signs where applicable.

At generation, the original chart, source originals and workbook were unchanged. During subsequent directory cleanup on2026-10-29, the superseded chart was deleted at the user's request; source originals and workbook contents remained unchanged.

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

