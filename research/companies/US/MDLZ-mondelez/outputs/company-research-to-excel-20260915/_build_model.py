#!/usr/bin/env python3
"""Build MDLZ model.json from scratch (bundle-only mode), per SKILL.md Phase 3-4.
All figures sourced from research/companies/US/MDLZ-mondelez SEC filings via
tables.json extraction (see _is_dump.txt, _bs_dump.txt, _cf_dump.txt, _q_dump.txt).
"""
import json

A = ["FY2016","FY2017","FY2018","FY2019","FY2020","FY2021","FY2022","FY2023","FY2024","FY2025"]
AEND = {"FY2016":"2016-12-31","FY2017":"2017-12-31","FY2018":"2018-12-31","FY2019":"2019-12-31",
        "FY2020":"2020-12-31","FY2021":"2021-12-31","FY2022":"2022-12-31","FY2023":"2023-12-31",
        "FY2024":"2024-12-31","FY2025":"2025-12-31"}
Q = ["3Q2024","1Q2025","2Q2025","3Q2025","1Q2026","2Q2026"]
QEND = {"3Q2024":"2024-09-30","1Q2025":"2025-03-31","2Q2025":"2025-06-30",
        "3Q2025":"2025-09-30","1Q2026":"2026-03-31","2Q2026":"2026-06-30"}

def av(vals):
    """annual list (10) -> dict, None dropped"""
    d = {}
    for lbl, v in zip(A, vals):
        if v is not None:
            d[lbl] = v
    return d

def qv(vals):
    d = {}
    for lbl, v in zip(Q, vals):
        if v is not None:
            d[lbl] = v
    return d

def merge(a, q):
    d = dict(a)
    d.update(q)
    return d

# ============================================================================
# INCOME STATEMENT  (sign-normalized: FY2016-2022 flipped to true economic
# sign so operating_income = SUM of components; FY2023-2025 and all quarters
# already filed in true-economic-sign / additive convention)
# ============================================================================

net_revenues = merge(av([25923,25896,25938,25868,26581,28720,31496,36016,36441,38537]),
                      qv([9204,9313,8984,9744,10080,9355]))

cost_of_sales = merge(av([-15795,-15831,-15586,-15531,-16135,-17466,-20184,-22252,-22184,-27602]),
                       qv([-6205,-6883,-6047,-7132,-7277,-5369]))

gross_profit = merge(av([10128,10065,10352,10337,10446,11254,11312,13764,14257,10935]),
                      qv([2999,2430,2937,2612,2803,3986]))

sga = merge(av([-6540,-5911,-6475,-6136,-6098,-6263,-7384,-8002,-7439,-7173]),
            qv([-1630,-1711,-1725,-1795,-1916,-2001]))

asset_impairment = merge(av([-852,-656,-389,-228,-301,-212,-262,-217,-324,-85]),
                          qv([-176,-2,-2,-41,-53,-13]))

gain_loss_divest = merge(av([9,186,None,44,None,8,None,108,4,13]),
                          qv([None,None,None,None,1,None]))

amortization_intangibles = merge(av([-176,-178,-176,-174,-194,-134,-132,-151,-153,-142]),
                                  qv([-40,-37,-38,-32,-27,-26]))

operating_income = merge(av([2569,3506,3312,3843,3853,4653,3534,5502,6345,3548]),
                          qv([1153,680,1172,744,808,1946]))

benefit_plan_nonservice = merge(av([None,None,50,60,138,163,117,82,96,-252]),
                                 qv([25,18,-264,-27,31,27]))

interest_other_expense = merge(av([-1115,-382,-520,-456,-608,-447,-423,-310,-180,-282]),
                                qv([-46,-153,-53,-22,-64,-74]))

gain_marketable_securities = merge(av([None,None,None,None,None,None,None,606,None,None]),
                                    qv([None]*6))

earnings_before_tax = merge(av([1454,3124,2842,3447,3383,4369,3228,5880,6261,3014]),
                             qv([1132,545,855,695,775,1899]))

income_tax_provision = merge(av([-129,-688,-773,-2,-1224,-1190,-865,-1537,-1469,-782]),
                              qv([-326,-154,-230,-137,-228,-364]))

gain_loss_equity_method = merge(av([43,40,778,-2,989,742,-22,465,-337,169]),
                                 qv([-4,None,None,169,-3,None]))

equity_method_investment_earnings = merge(av([301,460,548,442,421,393,385,160,168,65]),
                                           qv([54,16,19,19,20,17]))

net_earnings = merge(av([1669,2936,3395,3885,3569,4314,2726,4968,4623,2466]),
                      qv([856,407,644,746,564,1552]))

nci_earnings = merge(av([-10,-14,-14,-15,-14,-14,-9,-9,-12,-15]),
                      qv([-3,-5,-3,-3,-4,-4]))

net_earnings_attributable = merge(av([1659,2922,3381,3870,3555,4300,2717,4959,4611,2451]),
                                   qv([853,402,641,743,560,1548]))

basic_eps = merge(av([1.07,1.93,2.30,2.68,2.48,3.06,1.97,3.64,3.44,1.89]),
                   qv([0.64,0.31,0.49,0.57,0.44,1.21]))
diluted_eps = merge(av([1.05,1.91,2.28,2.65,2.47,3.04,1.96,3.62,3.42,1.89]),
                     qv([0.63,0.31,0.49,0.57,0.44,1.20]))
waso_basic = merge(av([1556,1513,1472,1445,1431,1403,1378,1363,1341,1294]),
                    qv([1339,1301,1295,1293,1283,1284]))
waso_diluted = merge(av([1573,1531,1486,1458,1441,1413,1385,1370,1347,1298]),
                      qv([1344,1305,1299,1296,1286,1287]))
dividends_declared = av([0.72,0.82,0.96,1.09,1.20,1.33,1.47,1.62,1.79,1.94])

is_blocks = [
  {"title": "INCOME STATEMENT — AS REPORTED", "rows": [
    {"id":"net_revenues","label":"Net revenues","type":"input","values":net_revenues,"bold":True,"fmt":"num"},
    {"id":"rev_yoy","label":"  YoY Growth","type":"growth_yoy","of":"net_revenues","fmt":"pct","memo":True},
    {"id":"cost_of_sales","label":"Cost of sales","type":"input","values":cost_of_sales,"indent":1,
     "note":"FY2016-22 sign-flipped from filed positive-subtract convention to true economic sign; FY2023-25 & quarters filed additive"},
    {"id":"gross_profit","label":"Gross profit","type":"input","values":gross_profit,"bold":True,"border_top":True},
    {"id":"gross_margin","label":"  Gross Margin","type":"calc","expr":"{gross_profit}/{net_revenues}","fmt":"pct","memo":True},
    {"type":"spacer"},
    {"id":"sga","label":"Selling, general and administrative expenses","type":"input","values":sga,"indent":1},
    {"id":"asset_impairment","label":"Asset impairment and exit costs","type":"input","values":asset_impairment,"indent":1},
    {"id":"gain_loss_divest","label":"Gain on divestitures and acquisitions, net","type":"input","values":gain_loss_divest,"indent":1},
    {"id":"amortization_intangibles","label":"Amortization of intangible assets","type":"input","values":amortization_intangibles,"indent":1},
    {"id":"operating_income","label":"Operating income","type":"input","values":operating_income,"bold":True,"border_top":True},
    {"id":"op_margin","label":"  Operating Margin","type":"calc","expr":"{operating_income}/{net_revenues}","fmt":"pct","memo":True},
    {"id":"oi_yoy","label":"  YoY Growth","type":"growth_yoy","of":"operating_income","fmt":"pct","memo":True},
    {"type":"spacer"},
    {"id":"benefit_plan_nonservice","label":"Benefit plan non-service income/(expense)","type":"input","values":benefit_plan_nonservice,"indent":1,
     "note":"Line does not exist in FY2016-2017 filings"},
    {"id":"interest_other_expense","label":"Interest and other expense, net","type":"input","values":interest_other_expense,"indent":1},
    {"id":"gain_marketable_securities","label":"Gain on marketable securities","type":"input","values":gain_marketable_securities,"indent":1,
     "note":"One-time item, FY2023 only (JDE Peet's share sale)"},
    {"id":"earnings_before_tax","label":"Earnings before income taxes","type":"input","values":earnings_before_tax,"bold":True,"border_top":True},
    {"id":"income_tax_provision","label":"Income tax provision","type":"input","values":income_tax_provision,"indent":1},
    {"id":"eff_tax_rate","label":"  Effective Tax Rate","type":"calc","expr":"0-{income_tax_provision}/{earnings_before_tax}","fmt":"pct","memo":True},
    {"id":"gain_loss_equity_method","label":"Gain/(loss) on equity method investment transactions","type":"input","values":gain_loss_equity_method,"indent":1,
     "note":"FY2024 value (-337) recovered from FY2025 10-K comparative column; corrupted in FY2024 filing's own raw table extraction"},
    {"id":"equity_method_investment_earnings","label":"Equity method investment net earnings","type":"input","values":equity_method_investment_earnings,"indent":1},
    {"id":"net_earnings","label":"Net earnings","type":"input","values":net_earnings,"bold":True,"border_top":True},
    {"id":"net_margin_pretax","label":"  Net Margin","type":"calc","expr":"{net_earnings}/{net_revenues}","fmt":"pct","memo":True},
    {"id":"nci_earnings","label":"Noncontrolling interest earnings","type":"input","values":nci_earnings,"indent":1},
    {"id":"net_earnings_attributable","label":"Net earnings attributable to Mondelez International","type":"input","values":net_earnings_attributable,"bold":True,"border_top":True},
    {"id":"ni_yoy","label":"  YoY Growth","type":"growth_yoy","of":"net_earnings_attributable","fmt":"pct","memo":True},
  ]},
  {"title": "EPS & SHARE COUNT", "rows": [
    {"id":"basic_eps","label":"Basic EPS","type":"input","values":basic_eps,"fmt":"ps","bold":True},
    {"id":"diluted_eps","label":"Diluted EPS","type":"input","values":diluted_eps,"fmt":"ps","bold":True},
    {"id":"eps_yoy","label":"  YoY Growth","type":"growth_yoy","of":"diluted_eps","fmt":"pct","memo":True},
    {"id":"waso_basic","label":"Weighted Avg Shares — Basic","type":"input","values":waso_basic,"fmt":"num"},
    {"id":"waso_diluted","label":"Weighted Avg Shares — Diluted","type":"input","values":waso_diluted,"fmt":"num"},
    {"id":"dividends_declared","label":"Dividends declared per share","type":"input","values":dividends_declared,"fmt":"ps",
     "note":"Quarterly dividend-per-share not separately tabulated by collector; annual only"},
  ]},
  {"title": "CHECKS", "rows": [
    {"id":"gross_profit_check","label":"Gross Profit Check (should be ~0)","type":"check",
     "expr":"{net_revenues}+{cost_of_sales}-{gross_profit}","fmt":"num","memo":True},
    {"id":"operating_income_check","label":"Operating Income Check (should be ~0)","type":"check",
     "expr":"{gross_profit}+{sga}+{asset_impairment}+{gain_loss_divest}+{amortization_intangibles}-{operating_income}","fmt":"num","memo":True},
    {"id":"bottomline_check","label":"Bottom-Line Check (should be ~0)","type":"check",
     "expr":"{operating_income}+{benefit_plan_nonservice}+{interest_other_expense}+{gain_marketable_securities}+{income_tax_provision}+{gain_loss_equity_method}+{equity_method_investment_earnings}+{nci_earnings}-{net_earnings_attributable}",
     "fmt":"num","memo":True},
  ]},
]

# ============================================================================
# BALANCE SHEET
# ============================================================================
cash = merge(av([1741,761,1100,1291,3619,3546,1923,1810,1351,2125]),
             qv([1517,1561,1504,1367,1524,1716]))
trade_receivables = merge(av([2611,2691,2262,2212,2297,2337,3088,3634,3874,3903]),
                           qv([3800,4318,3528,4189,4397,4010]))
other_receivables = merge(av([859,835,744,715,657,851,819,878,937,955]),
                           qv([891,941,1103,1049,985,998]))
inventories = merge(av([2469,2557,2592,2546,2647,2708,3381,3615,3827,4419]),
                     qv([4270,4255,4951,5098,4079,4405]))
other_current_assets = merge(av([800,676,906,866,759,900,880,1766,3253,1549]),
                              qv([2723,1655,1664,1444,1760,1809]))
total_current_assets = merge(av([8480,7520,7604,7630,9979,10342,10091,11703,13242,12951]),
                              qv([13201,12730,12750,13147,12745,12938]))
ppe_net = merge(av([8229,8677,8482,8733,9026,8658,9020,9694,9481,10667]),
                qv([9696,9767,10313,10333,10567,10649]))
op_lease_rou = merge(av([None,None,None,568,638,613,660,683,767,731]),
                      qv([774,761,761,750,725,732]))
goodwill = merge(av([20276,21085,20725,20848,21895,21978,23450,23896,23017,24336]),
                 qv([23773,23439,24344,24250,24226,24180]))
intangibles_net = merge(av([18101,18639,18002,17957,18482,18291,19710,19836,18848,19628]),
                        qv([19459,19130,19729,19611,19533,19509]))
prepaid_pension = merge(av([159,158,132,516,672,1009,1016,1043,987,1220]),
                        qv([1146,993,1121,1132,1259,1251]))
deferred_tax_assets = merge(av([358,319,255,726,790,541,473,408,333,336]),
                            qv([372,400,415,437,316,184]))
equity_method_investments = merge(av([5585,6345,7123,7212,6036,5289,4879,3242,635,667]),
                                  qv([2576,610,665,669,610,619]))
other_assets = merge(av([350,366,406,359,292,371,1862,886,1187,951]),
                     qv([1194,1097,922,1029,1141,1185]))
total_assets = merge(av([61538,63109,62729,64549,67810,67092,71161,71391,68497,71487]),
                     qv([72191,68927,71020,71358,71122,71247]))

st_borrowings = merge(av([2531,3517,3192,2638,29,216,2299,420,71,2688]),
                      qv([1484,1914,1664,2645,2881,2327]))
current_ltd = merge(av([1451,1163,2648,1581,2741,1746,383,2101,2014,1295]),
                    qv([1821,1828,1107,1543,2675,2663]))
accounts_payable = merge(av([5318,5705,5794,5853,6209,6730,7562,8321,9433,10139]),
                         qv([9110,9921,9975,10022,9744,9411]))
accrued_marketing = merge(av([1745,1728,1756,1836,2130,2097,2370,2683,2558,2787]),
                          qv([2721,2697,2423,2650,2968,2612]))
accrued_employment = merge(av([736,721,701,769,834,822,949,1158,928,1000]),
                           qv([905,774,836,956,865,875]))
other_current_liabilities = merge(av([2636,2959,2646,2645,3216,2397,3168,4330,4545,3955]),
                                  qv([5032,3869,3878,3696,4368,3705]))
total_current_liabilities = merge(av([14417,15793,16737,15322,15159,14008,16731,19013,19549,21864]),
                                  qv([21073,21003,19883,21512,23501,21593]))
lt_debt = merge(av([13217,12972,12532,14207,17276,17550,20251,16887,15664,17222]),
               qv([16499,15796,18116,17134,15468,16460]))
lt_op_lease_liab = merge(av([None,None,None,403,470,459,514,537,623,599]),
                         qv([621,617,618,611,598,609]))
deferred_tax_liab = merge(av([4721,3376,3552,3338,3346,3444,3437,3292,3425,3530]),
                          qv([3423,3429,3550,3451,3549,3539]))
accrued_pension = merge(av([2014,1669,1221,1190,1257,681,403,437,391,422]),
                        qv([368,366,375,356,389,370]))
accrued_postretirement = merge(av([382,419,351,387,346,301,217,124,98,74]),
                               qv([125,95,98,95,72,72]))
other_liabilities = merge(av([1572,2689,2623,2351,2302,2326,2688,2735,1789,1885]),
                          qv([2191,1798,2133,1970,1741,1912]))
total_liabilities = merge(av([36323,36918,37016,37198,40156,38769,44241,43025,41539,45596]),
                          qv([44300,43104,44773,45129,45318,44555]))

additional_paid_in_capital = merge(av([31847,31915,31961,32019,32070,32097,32143,32216,32276,32322]),
                                   qv([32244,32233,32280,32299,32276,32333]))
retained_earnings = merge(av([21149,22749,24491,26653,28402,30806,31481,34236,36476,36413]),
                          qv([35331,36263,36293,36390,36329,37233]))
aoci = merge(av([-11122,-9998,-10630,-10258,-10690,-10624,-10947,-10946,-12471,-11364]),
            qv([-11579,-11979,-11561,-11464,-11406,-11283]))
treasury_stock = merge(av([-16713,-18555,-20185,-21139,-22204,-24010,-25794,-27174,-29349,-31533]),
                       qv([-28142,-30732,-30819,-31048,-31449,-31644]))
total_mdlz_equity = merge(av([25161,26111,25637,27275,27578,28269,26883,28332,26932,25838]),
                          qv([27854,25785,26193,26177,25750,26639]))
nci = merge(av([54,80,76,76,76,54,37,34,26,53]),
           qv([37,38,54,52,54,53]))
total_equity = merge(av([25215,26191,25713,27351,27654,28323,26920,28366,26958,25891]),
                     qv([27891,25823,26247,26229,25804,26692]))

bs_blocks = [
  {"title": "ASSETS", "rows": [
    {"id":"cash","label":"Cash and cash equivalents","type":"input","values":cash},
    {"id":"trade_receivables","label":"Trade receivables, net","type":"input","values":trade_receivables},
    {"id":"other_receivables","label":"Other receivables, net","type":"input","values":other_receivables},
    {"id":"inventories","label":"Inventories, net","type":"input","values":inventories},
    {"id":"other_current_assets","label":"Other current assets","type":"input","values":other_current_assets},
    {"id":"total_current_assets","label":"Total current assets","type":"input","values":total_current_assets,"bold":True,"border_top":True},
    {"id":"ca_check","label":"Current Assets Check (should be ~0)","type":"check",
     "expr":"{cash}+{trade_receivables}+{other_receivables}+{inventories}+{other_current_assets}-{total_current_assets}","fmt":"num","memo":True},
    {"type":"spacer"},
    {"id":"ppe_net","label":"Property, plant and equipment, net","type":"input","values":ppe_net},
    {"id":"op_lease_rou","label":"Operating lease right-of-use assets","type":"input","values":op_lease_rou,
     "note":"Recognized starting FY2019 (ASU 2016-02 adoption)"},
    {"id":"goodwill","label":"Goodwill","type":"input","values":goodwill},
    {"id":"intangibles_net","label":"Intangible assets, net","type":"input","values":intangibles_net},
    {"id":"prepaid_pension","label":"Prepaid pension assets","type":"input","values":prepaid_pension},
    {"id":"deferred_tax_assets","label":"Deferred income taxes","type":"input","values":deferred_tax_assets},
    {"id":"equity_method_investments","label":"Equity method investments","type":"input","values":equity_method_investments},
    {"id":"other_assets","label":"Other assets","type":"input","values":other_assets},
    {"id":"total_assets","label":"TOTAL ASSETS","type":"input","values":total_assets,"bold":True,"border_top":True},
    {"id":"ta_check","label":"Total Assets Check (should be ~0)","type":"check",
     "expr":"{total_current_assets}+{ppe_net}+{op_lease_rou}+{goodwill}+{intangibles_net}+{prepaid_pension}+{deferred_tax_assets}+{equity_method_investments}+{other_assets}-{total_assets}",
     "fmt":"num","memo":True},
  ]},
  {"title": "LIABILITIES", "rows": [
    {"id":"st_borrowings","label":"Short-term borrowings","type":"input","values":st_borrowings},
    {"id":"current_ltd","label":"Current portion of long-term debt","type":"input","values":current_ltd},
    {"id":"accounts_payable","label":"Accounts payable","type":"input","values":accounts_payable},
    {"id":"accrued_marketing","label":"Accrued marketing","type":"input","values":accrued_marketing},
    {"id":"accrued_employment","label":"Accrued employment costs","type":"input","values":accrued_employment},
    {"id":"other_current_liabilities","label":"Other current liabilities","type":"input","values":other_current_liabilities},
    {"id":"total_current_liabilities","label":"Total current liabilities","type":"input","values":total_current_liabilities,"bold":True,"border_top":True},
    {"id":"cl_check","label":"Current Liabilities Check (should be ~0)","type":"check",
     "expr":"{st_borrowings}+{current_ltd}+{accounts_payable}+{accrued_marketing}+{accrued_employment}+{other_current_liabilities}-{total_current_liabilities}",
     "fmt":"num","memo":True},
    {"type":"spacer"},
    {"id":"lt_debt","label":"Long-term debt","type":"input","values":lt_debt},
    {"id":"lt_op_lease_liab","label":"Long-term operating lease liabilities","type":"input","values":lt_op_lease_liab,
     "note":"Recognized starting FY2019 (ASU 2016-02 adoption)"},
    {"id":"deferred_tax_liab","label":"Deferred income taxes","type":"input","values":deferred_tax_liab},
    {"id":"accrued_pension","label":"Accrued pension costs","type":"input","values":accrued_pension},
    {"id":"accrued_postretirement","label":"Accrued postretirement health care costs","type":"input","values":accrued_postretirement},
    {"id":"other_liabilities","label":"Other liabilities","type":"input","values":other_liabilities},
    {"id":"total_liabilities","label":"TOTAL LIABILITIES","type":"input","values":total_liabilities,"bold":True,"border_top":True},
    {"id":"tl_check","label":"Total Liabilities Check (should be ~0)","type":"check",
     "expr":"{total_current_liabilities}+{lt_debt}+{lt_op_lease_liab}+{deferred_tax_liab}+{accrued_pension}+{accrued_postretirement}+{other_liabilities}-{total_liabilities}",
     "fmt":"num","memo":True},
  ]},
  {"title": "EQUITY", "rows": [
    {"id":"additional_paid_in_capital","label":"Additional paid-in capital","type":"input","values":additional_paid_in_capital},
    {"id":"retained_earnings","label":"Retained earnings","type":"input","values":retained_earnings},
    {"id":"aoci","label":"Accumulated other comprehensive losses","type":"input","values":aoci},
    {"id":"treasury_stock","label":"Treasury stock, at cost","type":"input","values":treasury_stock},
    {"id":"total_mdlz_equity","label":"Total Mondelez International Shareholders' Equity","type":"input","values":total_mdlz_equity,"bold":True,"border_top":True},
    {"id":"parent_equity_check","label":"Parent Equity Check (should be ~0)","type":"check",
     "expr":"{additional_paid_in_capital}+{retained_earnings}+{aoci}+{treasury_stock}-{total_mdlz_equity}","fmt":"num","memo":True},
    {"id":"nci","label":"Noncontrolling interest","type":"input","values":nci},
    {"id":"total_equity","label":"TOTAL EQUITY","type":"input","values":total_equity,"bold":True,"border_top":True},
    {"id":"te_check","label":"Total Equity Check (should be ~0)","type":"check",
     "expr":"{total_mdlz_equity}+{nci}-{total_equity}","fmt":"num","memo":True},
  ]},
  {"title": "BALANCE CHECK", "rows": [
    {"id":"bs_check","label":"Balance Sheet Check: Assets = Liabilities + Equity (should be ~0)","type":"check",
     "expr":"{total_assets}-{total_liabilities}-{total_equity}","fmt":"num","bold":True},
  ]},
  {"title": "WORKING CAPITAL ANALYTICS", "rows": [
    {"id":"wc_dso","label":"Days Sales Outstanding","type":"calc",
     "expr":"{trade_receivables}/{IS:net_revenues}*365","expr_q":"{trade_receivables}/{IS:net_revenues}*91",
     "fmt":"num1","memo":True},
    {"id":"wc_dio","label":"Days Inventory Outstanding","type":"calc",
     "expr":"{inventories}/(0-{IS:cost_of_sales})*365","expr_q":"{inventories}/(0-{IS:cost_of_sales})*91",
     "fmt":"num1","memo":True},
    {"id":"wc_dpo","label":"Days Payable Outstanding","type":"calc",
     "expr":"{accounts_payable}/(0-{IS:cost_of_sales})*365","expr_q":"{accounts_payable}/(0-{IS:cost_of_sales})*91",
     "fmt":"num1","memo":True},
    {"id":"wc_ccc","label":"Cash Conversion Cycle","type":"calc","expr":"{wc_dso}+{wc_dio}-{wc_dpo}","fmt":"num1","memo":True},
  ]},
]

# ============================================================================
# CASH FLOW STATEMENT
# NOTE: quarterly CF columns are fiscal-year-to-date (YTD) cumulative per
# MDLZ's 10-Q presentation, not discrete-quarter figures -- documented on the
# sheet and in Sources.
# ============================================================================
cf_net_earnings = merge(av([1669,2936,3395,3885,3569,4314,2726,4968,4623,2466]),
                        qv([2875,407,1051,1797,564,2116]))
da = merge(av([823,816,811,1047,1116,1113,1107,1215,1302,1358]),
          qv([971,324,663,1006,343,693]))
sbc = merge(av([140,137,128,135,126,121,120,146,147,114]),
           qv([112,18,65,84,29,87]))
deferred_tax = merge(av([-141,-1206,233,-631,-70,205,-42,-37,257,16]),
                     qv([167,-96,-69,-158,8,149]))
us_tax_reform = av([None,1317,-38,5,None,None,None,None,None,None])
asset_impairments_cf = merge(av([446,334,141,109,136,128,233,128,267,85]),
                             qv([210,4,9,55,4,10]))
loss_early_extinguishment = av([428,11,140,None,185,110,38,1,None,None])
gain_div_acq_cf = merge(av([-9,-186,None,-44,None,-8,None,-108,-4,-13]),
                        qv([None,None,None,None,-1,-1]))
gain_loss_equity_method_cf = merge(av([-43,-40,-778,2,-989,-742,22,-465,337,None]),
                                   qv([669,None,None,None,3,3]))
equity_method_net_earnings_cf = merge(av([-301,-460,-548,-442,-421,-393,-385,-160,-175,-65]),
                                      qv([-140,-16,-35,-54,-20,-37]))
distributions_equity_method = merge(av([75,152,180,250,246,172,184,137,115,45]),
                                    qv([115,44,44,45,43,44]))
unrealized_deriv = merge(av([None,None,None,None,None,None,None,-171,-627,1379]),
                         qv([104,689,800,1161,257,-509]))
gain_marketable_securities_cf = av([None,None,None,None,None,None,None,-593,None,None])
contingent_consideration_adj = merge(av([None,None,None,None,None,None,None,None,-389,-34]),
                                     qv([-311,-12,-38,-26,-8,3]))
other_noncash = merge(av([-43,-225,381,97,243,-230,426,140,26,137]),
                      qv([93,56,105,109,-36,-5]))
wc_receivables = merge(av([31,-24,257,124,59,-197,-719,-628,-519,433]),
                       qv([-270,-379,536,-92,-728,-424]))
wc_inventories = merge(av([62,-18,-204,31,-24,-170,-635,-193,-458,-253]),
                       qv([-710,-300,-775,-967,314,-16]))
wc_ap = merge(av([409,5,236,4,436,702,715,264,1682,-145]),
             qv([951,222,-177,-159,-320,-538]))
wc_other_curr_assets = merge(av([-176,14,-25,-77,-207,-169,-286,-120,-591,-225]),
                             qv([-287,196,108,-30,-1,142]))
wc_other_curr_liab = merge(av([60,-637,-136,-362,-208,-502,630,376,-932,-1026]),
                           qv([-992,-58,-1125,-903,83,-296]))
wc_pension_cf = merge(av([-592,-333,-225,-168,-233,-313,-226,-186,-151,242]),
                      qv([-106,-7,238,249,-67,-99]))
cfo_total = merge(av([2838,2593,3948,3965,3964,4141,3908,4714,4910,4514]),
                  qv([3451,1092,1400,2117,467,1322]))

capex = merge(av([-1224,-1014,-1095,-925,-863,-965,-906,-1112,-1387,-1279]),
             qv([-982,-277,-582,-881,-312,-654]))
acquisitions = merge(av([-246,None,-528,-284,-1136,-833,-5286,19,-240,-15]),
                     qv([None,-15,-15,-15,None,None]))
proceeds_divestitures = merge(av([303,604,1,167,2489,1539,601,4099,2294,127]),
                              qv([4,4,4,4,1,1]))
proceeds_deriv_settle = merge(av([None,None,None,None,None,None,703,177,320,54]),
                              qv([191,14,19,54,52,179]))
payments_deriv_settle = merge(av([None,None,None,None,None,None,None,-81,-199,-165]),
                              qv([-150,None,-55,-165,-179,-270]))
contributions_investments = merge(av([None,None,None,None,None,None,None,-309,-278,73]),
                                  qv([-249,22,30,65,16,25]))
ppe_sale = merge(av([138,109,398,82,10,233,None,19,16,9]),
                 qv([16,1,8,8,None,3]))
cfi_total = merge(av([-1029,-301,-1224,-960,500,-26,-4888,2812,526,-1196]),
                  qv([-1170,-251,-591,-930,-422,-716]))

issuance_cp = merge(av([1540,1808,3981,1306,677,None,None,67,None,None]),
                    qv([None,None,None,None,586,1584]))
repayments_cp = merge(av([-1031,-1911,-2856,-2367,-1174,None,None,-67,None,None]),
                      qv([None,None,None,None,None,-587]))
net_other_st_borrow = merge(av([1741,1027,-1413,524,-2116,194,1914,-1869,-343,2609]),
                            qv([1065,1841,1589,2569,-368,-1313]))
lt_debt_proceeds = merge(av([5640,350,2948,3136,7213,5921,4490,277,1671,1594]),
                         qv([1671,None,1594,1594,None,1074]))
lt_debt_repayments = merge(av([-6186,-1470,-1821,-2677,-3878,-6247,-3032,-2432,-2554,-2077]),
                           qv([-2517,-453,-1242,-1782,-262,-304]))
repurchases = merge(av([-2601,-2174,-2020,-1480,-1390,-2110,-2017,-1547,-2334,-2385]),
                    qv([-1187,-1522,-1653,-1893,None,-212]))
dividends_paid = merge(av([-1094,-1198,-1359,-1542,-1678,-1826,-1985,-2160,-2349,-2487]),
                       qv([-1722,-623,-1233,-1842,-644,-1287]))
other_financing = merge(av([129,207,211,313,131,-1,174,173,129,-13]),
                        qv([132,53,83,8,84,6]))
cff_total = merge(av([-1862,-3361,-2329,-2787,-2215,-4069,-456,-7558,-5780,-2759]),
                  qv([-2558,-704,-862,-1346,-604,-1039]))

fx_effect = merge(av([-76,89,-56,10,73,-143,-169,-32,-140,236]),
                  qv([-34,88,240,225,-5,-3]))
net_change_cash = merge(av([-129,-980,339,228,2322,-97,-1605,-64,-484,795]),
                        qv([-311,225,187,66,-564,-436]))
cash_beginning = merge(av([1870,1741,761,1100,1328,3650,3553,1948,1884,1400]),
                       qv([1884,1400,1400,1400,2195,2195]))
cash_ending = merge(av([1741,761,1100,1328,3650,3553,1948,1884,1400,2195]),
                    qv([1573,1625,1587,1466,1631,1759]))
interest_paid = av([630,398,491,486,413,426,551,568,554,570])
income_taxes_paid = av([527,848,864,981,1264,1556,1103,1607,1474,1074])

cf_blocks = [
  {"title": "CASH FLOW FROM OPERATING ACTIVITIES", "rows": [
    {"id":"cf_net_earnings","label":"Net earnings","type":"input","values":cf_net_earnings,"bold":True,
     "note":"Quarterly CF columns are fiscal-YTD cumulative (per MDLZ 10-Q presentation), not discrete-quarter"},
    {"id":"da","label":"Depreciation and amortization","type":"input","values":da,"indent":1},
    {"id":"sbc","label":"Stock-based compensation expense","type":"input","values":sbc,"indent":1},
    {"id":"deferred_tax","label":"Deferred income tax provision/(benefit)","type":"input","values":deferred_tax,"indent":1},
    {"id":"us_tax_reform","label":"U.S. tax reform transition tax","type":"input","values":us_tax_reform,"indent":1,
     "note":"FY2017-2019 only (Tax Cuts and Jobs Act transition tax)"},
    {"id":"asset_impairments_cf","label":"Asset impairments and accelerated depreciation","type":"input","values":asset_impairments_cf,"indent":1},
    {"id":"loss_early_extinguishment","label":"Loss on early extinguishment of debt","type":"input","values":loss_early_extinguishment,"indent":1,
     "note":"FY2016-2023 only"},
    {"id":"gain_div_acq_cf","label":"Gain on divestitures and acquisitions, net","type":"input","values":gain_div_acq_cf,"indent":1},
    {"id":"gain_loss_equity_method_cf","label":"Loss/(gain) on equity method investment transactions","type":"input","values":gain_loss_equity_method_cf,"indent":1},
    {"id":"equity_method_net_earnings_cf","label":"Equity method investment net earnings","type":"input","values":equity_method_net_earnings_cf,"indent":1},
    {"id":"distributions_equity_method","label":"Distributions from equity method investments","type":"input","values":distributions_equity_method,"indent":1},
    {"id":"unrealized_deriv","label":"Unrealized loss/(gain) on derivative contracts","type":"input","values":unrealized_deriv,"indent":1,
     "note":"FY2023 onward only"},
    {"id":"gain_marketable_securities_cf","label":"Gain on marketable securities","type":"input","values":gain_marketable_securities_cf,"indent":1,
     "note":"FY2023 only"},
    {"id":"contingent_consideration_adj","label":"Contingent consideration adjustments","type":"input","values":contingent_consideration_adj,"indent":1,
     "note":"FY2024 onward only"},
    {"id":"other_noncash","label":"Other non-cash items, net","type":"input","values":other_noncash,"indent":1},
    {"type":"spacer"},
    {"id":"wc_receivables","label":"Change in receivables","type":"input","values":wc_receivables,"indent":1},
    {"id":"wc_inventories","label":"Change in inventories","type":"input","values":wc_inventories,"indent":1},
    {"id":"wc_ap","label":"Change in accounts payable","type":"input","values":wc_ap,"indent":1},
    {"id":"wc_other_curr_assets","label":"Change in other current assets","type":"input","values":wc_other_curr_assets,"indent":1},
    {"id":"wc_other_curr_liab","label":"Change in other current liabilities","type":"input","values":wc_other_curr_liab,"indent":1},
    {"id":"wc_pension_cf","label":"Change in pension and postretirement assets/liabilities","type":"input","values":wc_pension_cf,"indent":1},
    {"id":"cfo_total","label":"Net cash provided by operating activities","type":"input","values":cfo_total,"bold":True,"border_top":True},
    {"id":"cfo_check","label":"CFO Check (should be ~0)","type":"check",
     "expr":"{cf_net_earnings}+{da}+{sbc}+{deferred_tax}+{us_tax_reform}+{asset_impairments_cf}+{loss_early_extinguishment}+{gain_div_acq_cf}+{gain_loss_equity_method_cf}+{equity_method_net_earnings_cf}+{distributions_equity_method}+{unrealized_deriv}+{gain_marketable_securities_cf}+{contingent_consideration_adj}+{other_noncash}+{wc_receivables}+{wc_inventories}+{wc_ap}+{wc_other_curr_assets}+{wc_other_curr_liab}+{wc_pension_cf}-{cfo_total}",
     "fmt":"num","memo":True},
  ]},
  {"title": "CASH FLOW FROM INVESTING ACTIVITIES", "rows": [
    {"id":"capex","label":"Capital expenditures","type":"input","values":capex,"indent":1},
    {"id":"acquisitions","label":"Acquisitions, net of cash acquired","type":"input","values":acquisitions,"indent":1},
    {"id":"proceeds_divestitures","label":"Proceeds from divestitures","type":"input","values":proceeds_divestitures,"indent":1},
    {"id":"proceeds_deriv_settle","label":"Proceeds from settlement of derivatives","type":"input","values":proceeds_deriv_settle,"indent":1},
    {"id":"payments_deriv_settle","label":"Payments for settlement of derivatives","type":"input","values":payments_deriv_settle,"indent":1},
    {"id":"contributions_investments","label":"Contributions to (proceeds from) other investments","type":"input","values":contributions_investments,"indent":1},
    {"id":"ppe_sale","label":"Proceeds from sale of property, plant and equipment","type":"input","values":ppe_sale,"indent":1},
    {"id":"cfi_total","label":"Net cash provided by/(used in) investing activities","type":"input","values":cfi_total,"bold":True,"border_top":True},
    {"id":"cfi_check","label":"CFI Check (should be ~0)","type":"check",
     "expr":"{capex}+{acquisitions}+{proceeds_divestitures}+{proceeds_deriv_settle}+{payments_deriv_settle}+{contributions_investments}+{ppe_sale}-{cfi_total}",
     "fmt":"num","memo":True},
  ]},
  {"title": "CASH FLOW FROM FINANCING ACTIVITIES", "rows": [
    {"id":"issuance_cp","label":"Issuances of commercial paper, net","type":"input","values":issuance_cp,"indent":1},
    {"id":"repayments_cp","label":"Repayments of commercial paper, net","type":"input","values":repayments_cp,"indent":1},
    {"id":"net_other_st_borrow","label":"Net issuance/(repayment) of other short-term borrowings","type":"input","values":net_other_st_borrow,"indent":1},
    {"id":"lt_debt_proceeds","label":"Long-term debt proceeds","type":"input","values":lt_debt_proceeds,"indent":1},
    {"id":"lt_debt_repayments","label":"Long-term debt repayments","type":"input","values":lt_debt_repayments,"indent":1},
    {"id":"repurchases","label":"Repurchases of common stock","type":"input","values":repurchases,"indent":1},
    {"id":"dividends_paid","label":"Dividends paid","type":"input","values":dividends_paid,"indent":1},
    {"id":"other_financing","label":"Other financing activities, net","type":"input","values":other_financing,"indent":1},
    {"id":"cff_total","label":"Net cash used in financing activities","type":"input","values":cff_total,"bold":True,"border_top":True},
    {"id":"cff_check","label":"CFF Check (should be ~0)","type":"check",
     "expr":"{issuance_cp}+{repayments_cp}+{net_other_st_borrow}+{lt_debt_proceeds}+{lt_debt_repayments}+{repurchases}+{dividends_paid}+{other_financing}-{cff_total}",
     "fmt":"num","memo":True},
  ]},
  {"title": "NET CHANGE IN CASH & FCF ANALYTICS", "rows": [
    {"id":"fx_effect","label":"Effect of exchange rate changes on cash","type":"input","values":fx_effect,"indent":1},
    {"id":"net_change_cash","label":"Increase/(decrease) in cash and cash equivalents","type":"input","values":net_change_cash,"bold":True,"border_top":True},
    {"id":"cash_beginning","label":"Cash and cash equivalents, beginning of period","type":"input","values":cash_beginning},
    {"id":"cash_ending","label":"Cash and cash equivalents, end of period","type":"input","values":cash_ending,"bold":True,"border_top":True},
    {"id":"cf_check","label":"Cash Walk Check (should be ~0)","type":"check",
     "expr":"{cfo_total}+{cfi_total}+{cff_total}+{fx_effect}-{net_change_cash}","fmt":"num","memo":True},
    {"id":"cash_roll_check","label":"Cash Rollforward Check (should be ~0)","type":"check",
     "expr":"{cash_beginning}+{net_change_cash}-{cash_ending}","fmt":"num","memo":True},
    {"type":"spacer"},
    {"id":"fcf","label":"Free Cash Flow","type":"calc","expr":"{cfo_total}+{capex}","bold":True,"fmt":"num"},
    {"id":"fcf_yoy","label":"  YoY Growth","type":"growth_yoy","of":"fcf","fmt":"pct","memo":True},
    {"id":"capex_pct","label":"  Capex % of Revenue","type":"calc","expr":"0-{capex}/{IS:net_revenues}","fmt":"pct","memo":True},
    {"id":"fcf_margin","label":"  FCF Margin","type":"calc","expr":"{fcf}/{IS:net_revenues}","fmt":"pct","memo":True},
    {"id":"fcf_conversion","label":"  FCF Conversion (of Net Earnings)","type":"calc","expr":"{fcf}/{IS:net_earnings}","fmt":"pct","memo":True},
    {"type":"spacer"},
    {"id":"interest_paid","label":"Memo: Cash paid for interest","type":"input","values":interest_paid,"indent":1,"memo":True},
    {"id":"income_taxes_paid","label":"Memo: Cash paid for income taxes","type":"input","values":income_taxes_paid,"indent":1,"memo":True},
  ]},
]

# ============================================================================
# SEGMENTS  (geographic reportable segments, identical FY2016-2025)
# ============================================================================
seg_latam_rev = av([3392,3566,3202,3018,2477,2797,3629,5006,4926,4899])
seg_amea_rev = av([5816,5739,5729,5770,5740,6465,6767,7075,7296,7932])
seg_europe_rev = av([9755,9794,10122,9972,10207,11156,11420,12857,13309,15027])
seg_na_rev = av([6960,6797,6885,7108,8157,8302,9680,11078,10910,10679])
q_seg_rev = {
  "latam": qv([1204,1203,1194,1238,1348,1374]),
  "amea": qv([1851,2016,1821,2017,2304,1971]),
  "europe": qv([3323,3550,3412,3674,3871,3377]),
  "na": qv([2826,2544,2557,2815,2557,2633]),
}
seg_latam_rev = merge(seg_latam_rev, q_seg_rev["latam"])
seg_amea_rev = merge(seg_amea_rev, q_seg_rev["amea"])
seg_europe_rev = merge(seg_europe_rev, q_seg_rev["europe"])
seg_na_rev = merge(seg_na_rev, q_seg_rev["na"])

seg_latam_oi = merge(av([271,565,410,341,189,261,388,529,532,569]), qv([125,139,133,147,149,166]))
seg_amea_oi = merge(av([506,516,702,691,821,1054,929,1113,1192,985]), qv([335,343,271,199,326,254]))
seg_europe_oi = merge(av([1267,1680,1734,1732,1775,2092,1481,1978,2068,1820]), qv([605,462,514,275,294,382]))
seg_na_oi = merge(av([1078,1120,849,1451,1587,1371,1769,2092,2492,1904]), qv([918,485,454,547,384,431]))

mark_to_market = merge(av([-94,-96,141,91,16,279,-326,189,543,-1341]), qv([-710,-669,-93,-348,-273,827]))
general_corporate = merge(av([-291,-287,-335,-330,-326,-253,-245,-356,-330,-260]), qv([-78,-43,-69,-44,-46,-88]))
amortization_seg = merge(av([-176,-178,-176,-174,-194,-134,-132,-151,-153,-142]), qv([-40,-37,-38,-32,-27,-26]))
gain_divest_seg = merge(av([9,186,0,44,0,8,0,108,4,13]), qv([None,None,None,None,1,None]))
acq_costs_seg = merge(av([-1,0,-13,-3,-15,-25,-330,0,-3,0]), qv([-2,None,None,None,None,None]))

seg_blocks = [
  {"title": "SEGMENT REVENUE (Latin America / AMEA / Europe / North America)", "rows": [
    {"id":"seg_latam_rev","label":"Latin America","type":"input","values":seg_latam_rev,"indent":1},
    {"id":"seg_amea_rev","label":"Asia, Middle East and Africa (AMEA)","type":"input","values":seg_amea_rev,"indent":1},
    {"id":"seg_europe_rev","label":"Europe","type":"input","values":seg_europe_rev,"indent":1},
    {"id":"seg_na_rev","label":"North America","type":"input","values":seg_na_rev,"indent":1},
    {"id":"seg_total_rev","label":"Total Segment Net Revenues","type":"subtotal",
     "children":["seg_latam_rev","seg_amea_rev","seg_europe_rev","seg_na_rev"],"bold":True,"border_top":True},
    {"id":"seg_rev_check","label":"vs IS Net Revenues (should be ~0)","type":"check",
     "expr":"{seg_total_rev}-{IS:net_revenues}","fmt":"num","memo":True},
    {"type":"spacer"},
    {"id":"seg_latam_mix","label":"  Latin America % of total","type":"calc","expr":"{seg_latam_rev}/{seg_total_rev}","fmt":"pct","memo":True},
    {"id":"seg_amea_mix","label":"  AMEA % of total","type":"calc","expr":"{seg_amea_rev}/{seg_total_rev}","fmt":"pct","memo":True},
    {"id":"seg_europe_mix","label":"  Europe % of total","type":"calc","expr":"{seg_europe_rev}/{seg_total_rev}","fmt":"pct","memo":True},
    {"id":"seg_na_mix","label":"  North America % of total","type":"calc","expr":"{seg_na_rev}/{seg_total_rev}","fmt":"pct","memo":True},
  ]},
  {"title": "SEGMENT OPERATING INCOME", "rows": [
    {"id":"seg_latam_oi","label":"Latin America","type":"input","values":seg_latam_oi,"indent":1},
    {"id":"seg_amea_oi","label":"Asia, Middle East and Africa (AMEA)","type":"input","values":seg_amea_oi,"indent":1},
    {"id":"seg_europe_oi","label":"Europe","type":"input","values":seg_europe_oi,"indent":1},
    {"id":"seg_na_oi","label":"North America","type":"input","values":seg_na_oi,"indent":1},
    {"id":"seg_total_oi","label":"Total Segment Operating Income","type":"subtotal",
     "children":["seg_latam_oi","seg_amea_oi","seg_europe_oi","seg_na_oi"],"bold":True,"border_top":True},
  ]},
  {"title": "RECONCILIATION TO CONSOLIDATED OPERATING INCOME", "rows": [
    {"id":"mark_to_market","label":"Mark-to-market gains/(losses) on hedging activities","type":"input","values":mark_to_market,"indent":1},
    {"id":"general_corporate","label":"General corporate expenses","type":"input","values":general_corporate,"indent":1},
    {"id":"amortization_seg","label":"Amortization of intangible assets","type":"input","values":amortization_seg,"indent":1},
    {"id":"gain_divest_seg","label":"Gain on divestitures","type":"input","values":gain_divest_seg,"indent":1},
    {"id":"acq_costs_seg","label":"Acquisition-related costs","type":"input","values":acq_costs_seg,"indent":1},
    {"id":"recon_operating_income","label":"Operating Income (reconciled)","type":"subtotal",
     "children":["seg_total_oi","mark_to_market","general_corporate","amortization_seg","gain_divest_seg","acq_costs_seg"],
     "bold":True,"border_top":True},
    {"id":"seg_oi_check","label":"vs IS Operating Income (should be ~0)","type":"check",
     "expr":"{recon_operating_income}-{IS:operating_income}","fmt":"num","memo":True},
  ]},
  {"title": "RECONCILIATION TO EARNINGS BEFORE TAX", "rows": [
    {"id":"benefit_plan_seg","label":"Benefit plan non-service income/(expense)","type":"link","ref":"IS:benefit_plan_nonservice","indent":1},
    {"id":"interest_other_seg","label":"Interest and other expense, net","type":"link","ref":"IS:interest_other_expense","indent":1},
    {"id":"gain_mktsec_seg","label":"Gain on marketable securities","type":"link","ref":"IS:gain_marketable_securities","indent":1},
    {"id":"ebt_seg","label":"Earnings Before Income Taxes (reconciled)","type":"subtotal",
     "children":["recon_operating_income","benefit_plan_seg","interest_other_seg","gain_mktsec_seg"],"bold":True,"border_top":True},
    {"id":"seg_ebt_check","label":"vs IS Earnings Before Tax (should be ~0)","type":"check",
     "expr":"{ebt_seg}-{IS:earnings_before_tax}","fmt":"num","memo":True},
  ]},
]

# ============================================================================
# GEOGRAPHY & PRODUCTS  (product category revenue by segment; FY2023-2025 &
# 3Q2024 only -- earlier years use an incompatible product-category scheme
# with no separate Gum & Candy category and only % breakdown disclosed)
# ============================================================================
def pv(fy23, fy24, fy25, q3_24=None):
    d = {}
    if fy23 is not None: d["FY2023"] = fy23
    if fy24 is not None: d["FY2024"] = fy24
    if fy25 is not None: d["FY2025"] = fy25
    if q3_24 is not None: d["3Q2024"] = q3_24
    return d

biscuits_latam = pv(1193,1199,1155,312); biscuits_amea = pv(2488,2573,2935,661)
biscuits_europe = pv(4429,4425,4970,1162); biscuits_na = pv(9519,9605,9331,2470)
biscuits_total = pv(17629,17802,18391,4605)

choc_latam = pv(1357,1276,1414,299); choc_amea = pv(2690,2831,3047,752)
choc_europe = pv(6225,6773,7799,1640); choc_na = pv(347,368,436,92)
choc_total = pv(10619,11248,12696,2783)

gum_latam = pv(1509,1512,1507,374); gum_amea = pv(893,947,989,240)
gum_europe = pv(812,644,652,145); gum_na = pv(1212,937,912,264)
gum_total = pv(4426,4040,4060,1023)

bev_latam = pv(457,454,344,104); bev_amea = pv(593,525,517,105)
bev_europe = pv(135,117,145,28); bev_na = pv(None,None,None,None)
bev_total = pv(1185,1096,1006,237)

cheese_latam = pv(490,485,479,115); cheese_amea = pv(411,420,444,93)
cheese_europe = pv(1256,1350,1461,348); cheese_na = pv(None,None,None,None)
cheese_total = pv(2157,2255,2384,556)

# Restrict the entire Geography & Products sheet to the contiguous window
# FY2023..FY2025 (annual) + 3Q2024 (first quarterly period) -- the only
# periods with compatible product-category disclosure. min_label/max_label
# select a contiguous span in the combined annual+quarterly period order,
# and FY2023->FY2024->FY2025->3Q2024 is exactly that contiguous span.
GEO_MIN, GEO_MAX = "FY2023", "3Q2024"

def geo_row(**kw):
    kw.setdefault("min_label", GEO_MIN)
    kw.setdefault("max_label", GEO_MAX)
    return kw

geo_blocks = [
  {"title": "PRODUCT CATEGORY REVENUE — TOTAL COMPANY", "rows": [
    geo_row(id="prod_biscuits",label="Biscuits & Baked Snacks",type="input",values=biscuits_total,indent=1,
     note="FY2023-2025 & 3Q2024 only; earlier years use an incompatible product-category taxonomy (no separate Gum & Candy category, $ not disclosed)"),
    geo_row(id="prod_chocolate",label="Chocolate",type="input",values=choc_total,indent=1),
    geo_row(id="prod_gum",label="Gum & Candy",type="input",values=gum_total,indent=1),
    geo_row(id="prod_beverages",label="Beverages",type="input",values=bev_total,indent=1),
    geo_row(id="prod_cheese",label="Cheese & Grocery",type="input",values=cheese_total,indent=1),
    geo_row(id="prod_total",label="Total Net Revenues (product categories)",type="subtotal",
     children=["prod_biscuits","prod_chocolate","prod_gum","prod_beverages","prod_cheese"],bold=True,border_top=True),
    geo_row(id="prod_check",label="vs IS Net Revenues (should be ~0)",type="check",
     expr="{prod_total}-{IS:net_revenues}",fmt="num",memo=True),
  ]},
  {"title": "BISCUITS & BAKED SNACKS BY SEGMENT", "rows": [
    geo_row(id="biscuits_latam",label="Latin America",type="input",values=biscuits_latam,indent=1,group=True),
    geo_row(id="biscuits_amea",label="AMEA",type="input",values=biscuits_amea,indent=1,group=True),
    geo_row(id="biscuits_europe",label="Europe",type="input",values=biscuits_europe,indent=1,group=True),
    geo_row(id="biscuits_na",label="North America",type="input",values=biscuits_na,indent=1,group=True),
  ]},
  {"title": "CHOCOLATE BY SEGMENT", "rows": [
    geo_row(id="choc_latam",label="Latin America",type="input",values=choc_latam,indent=1,group=True),
    geo_row(id="choc_amea",label="AMEA",type="input",values=choc_amea,indent=1,group=True),
    geo_row(id="choc_europe",label="Europe",type="input",values=choc_europe,indent=1,group=True),
    geo_row(id="choc_na",label="North America",type="input",values=choc_na,indent=1,group=True),
  ]},
  {"title": "GUM & CANDY BY SEGMENT", "rows": [
    geo_row(id="gum_latam",label="Latin America",type="input",values=gum_latam,indent=1,group=True),
    geo_row(id="gum_amea",label="AMEA",type="input",values=gum_amea,indent=1,group=True),
    geo_row(id="gum_europe",label="Europe",type="input",values=gum_europe,indent=1,group=True),
    geo_row(id="gum_na",label="North America",type="input",values=gum_na,indent=1,group=True),
  ]},
  {"title": "BEVERAGES & CHEESE/GROCERY BY SEGMENT", "rows": [
    geo_row(id="bev_latam",label="Beverages — Latin America",type="input",values=bev_latam,indent=1,group=True),
    geo_row(id="bev_amea",label="Beverages — AMEA",type="input",values=bev_amea,indent=1,group=True),
    geo_row(id="bev_europe",label="Beverages — Europe",type="input",values=bev_europe,indent=1,group=True),
    geo_row(id="cheese_latam",label="Cheese & Grocery — Latin America",type="input",values=cheese_latam,indent=1,group=True),
    geo_row(id="cheese_amea",label="Cheese & Grocery — AMEA",type="input",values=cheese_amea,indent=1,group=True),
    geo_row(id="cheese_europe",label="Cheese & Grocery — Europe",type="input",values=cheese_europe,indent=1,group=True),
  ]},
]

# ============================================================================
# DERIVED METRICS  (10 categories per SKILL.md 4h)
# ============================================================================
dm_blocks = [
  {"title": "1. PROFITABILITY", "rows": [
    {"id":"dm_gross_margin","label":"Gross Margin","type":"link","ref":"IS:gross_margin","fmt":"pct"},
    {"id":"dm_op_margin","label":"Operating Margin","type":"link","ref":"IS:op_margin","fmt":"pct"},
    {"id":"dm_ebitda","label":"EBITDA","type":"calc","expr":"{IS:operating_income}+{CF:da}","fmt":"num","bold":True},
    {"id":"dm_ebitda_margin","label":"  EBITDA Margin","type":"calc","expr":"{dm_ebitda}/{IS:net_revenues}","fmt":"pct","memo":True},
    {"id":"dm_net_margin","label":"Net Margin (attributable)","type":"calc","expr":"{IS:net_earnings_attributable}/{IS:net_revenues}","fmt":"pct"},
    {"id":"dm_eff_tax_rate","label":"Effective Tax Rate","type":"link","ref":"IS:eff_tax_rate","fmt":"pct"},
  ]},
  {"title": "2. RETURNS", "rows": [
    {"id":"dm_avg_assets","label":"Average Total Assets","type":"calc","expr":"({BS:total_assets}+{BS:total_assets@-1})/2","fmt":"num","memo":True},
    {"id":"dm_avg_equity","label":"Average Total Equity","type":"calc","expr":"({BS:total_equity}+{BS:total_equity@-1})/2","fmt":"num","memo":True},
    {"id":"dm_roa","label":"Return on Assets (ROA)","type":"calc","expr":"{IS:net_earnings_attributable}/{dm_avg_assets}","fmt":"pct"},
    {"id":"dm_roe","label":"Return on Equity (ROE)","type":"calc","expr":"{IS:net_earnings_attributable}/{dm_avg_equity}","fmt":"pct"},
    {"id":"dm_roic","label":"Return on Invested Capital (ROIC, approx.)","type":"calc",
     "expr":"{IS:operating_income}*(1-{IS:eff_tax_rate})/({BS:total_equity}+{BS:lt_debt}+{BS:current_ltd}+{BS:st_borrowings}-{BS:cash})","fmt":"pct"},
    {"id":"dm_asset_turnover","label":"Asset Turnover","type":"calc","expr":"{IS:net_revenues}/{dm_avg_assets}","fmt":"x"},
  ]},
  {"title": "3. LEVERAGE", "rows": [
    {"id":"dm_total_debt","label":"Total Debt (ST borrowings + Current LTD + LT debt)","type":"calc",
     "expr":"{BS:st_borrowings}+{BS:current_ltd}+{BS:lt_debt}","fmt":"num"},
    {"id":"dm_net_debt","label":"Net Debt","type":"calc","expr":"{dm_total_debt}-{BS:cash}","fmt":"num","bold":True},
    {"id":"dm_net_debt_ebitda","label":"Net Debt / EBITDA","type":"calc","expr":"{dm_net_debt}/{dm_ebitda}","fmt":"x"},
    {"id":"dm_debt_equity","label":"Debt / Equity","type":"calc","expr":"{dm_total_debt}/{BS:total_equity}","fmt":"x"},
  ]},
  {"title": "4. SOLVENCY", "rows": [
    {"id":"dm_equity_ratio","label":"Equity Ratio (Equity / Assets)","type":"calc","expr":"{BS:total_equity}/{BS:total_assets}","fmt":"pct"},
    {"id":"dm_debt_assets","label":"Debt / Assets","type":"calc","expr":"{dm_total_debt}/{BS:total_assets}","fmt":"pct"},
  ]},
  {"title": "5. LIQUIDITY", "rows": [
    {"id":"dm_current_ratio","label":"Current Ratio","type":"calc","expr":"{BS:total_current_assets}/{BS:total_current_liabilities}","fmt":"x"},
    {"id":"dm_quick_ratio","label":"Quick Ratio","type":"calc",
     "expr":"({BS:cash}+{BS:trade_receivables}+{BS:other_receivables})/{BS:total_current_liabilities}","fmt":"x"},
    {"id":"dm_cash_ratio","label":"Cash Ratio","type":"calc","expr":"{BS:cash}/{BS:total_current_liabilities}","fmt":"x"},
  ]},
  {"title": "6. COVERAGE", "rows": [
    {"id":"dm_interest_coverage","label":"Interest Coverage (EBIT / Interest)","type":"calc",
     "expr":"{IS:operating_income}/(0-{IS:interest_other_expense})","fmt":"x"},
    {"id":"dm_cfo_interest","label":"CFO / Interest Paid","type":"calc","expr":"{CF:cfo_total}/{CF:interest_paid}","fmt":"x"},
  ]},
  {"title": "7. CASH CONVERSION", "rows": [
    {"id":"dm_cfo_margin","label":"CFO Margin","type":"calc","expr":"{CF:cfo_total}/{IS:net_revenues}","fmt":"pct"},
    {"id":"dm_cfo_ebitda","label":"CFO / EBITDA","type":"calc","expr":"{CF:cfo_total}/{dm_ebitda}","fmt":"pct"},
    {"id":"dm_capex_intensity","label":"Capex Intensity (Capex / Revenue)","type":"link","ref":"CF:capex_pct","fmt":"pct"},
    {"id":"dm_fcf_margin","label":"FCF Margin","type":"link","ref":"CF:fcf_margin","fmt":"pct"},
    {"id":"dm_fcf_conversion","label":"FCF Conversion","type":"link","ref":"CF:fcf_conversion","fmt":"pct"},
    {"id":"dm_da_capex","label":"D&A / Capex","type":"calc","expr":"{CF:da}/(0-{CF:capex})","fmt":"x"},
  ]},
  {"title": "8. EARNINGS QUALITY", "rows": [
    {"id":"dm_cfo_ni","label":"CFO / Net Earnings","type":"calc","expr":"{CF:cfo_total}/{IS:net_earnings}","fmt":"x"},
    {"id":"dm_accrual_ratio","label":"Accrual Ratio ((NI - CFO) / Avg Assets)","type":"calc",
     "expr":"({IS:net_earnings}-{CF:cfo_total})/{dm_avg_assets}","fmt":"pct"},
  ]},
  {"title": "9. GROWTH", "rows": [
    {"id":"dm_rev_growth","label":"Revenue Growth","type":"growth_yoy","of":"dm_rev_link","fmt":"pct"},
    {"id":"dm_rev_link","label":"  (Revenue, memo)","type":"link","ref":"IS:net_revenues","fmt":"num","memo":True},
    {"id":"dm_ni_growth","label":"Net Earnings Growth","type":"growth_yoy","of":"dm_ni_link","fmt":"pct"},
    {"id":"dm_ni_link","label":"  (Net Earnings, memo)","type":"link","ref":"IS:net_earnings_attributable","fmt":"num","memo":True},
    {"id":"dm_cfo_growth","label":"CFO Growth","type":"growth_yoy","of":"dm_cfo_link","fmt":"pct"},
    {"id":"dm_cfo_link","label":"  (CFO, memo)","type":"link","ref":"CF:cfo_total","fmt":"num","memo":True},
  ]},
  {"title": "10. WORKING CAPITAL", "rows": [
    {"id":"dm_dso","label":"Days Sales Outstanding","type":"link","ref":"BS:wc_dso","fmt":"num1"},
    {"id":"dm_dio","label":"Days Inventory Outstanding","type":"link","ref":"BS:wc_dio","fmt":"num1"},
    {"id":"dm_dpo","label":"Days Payable Outstanding","type":"link","ref":"BS:wc_dpo","fmt":"num1"},
    {"id":"dm_ccc","label":"Cash Conversion Cycle","type":"link","ref":"BS:wc_ccc","fmt":"num1","bold":True},
  ]},
]

# ============================================================================
# COVER & SOURCES
# ============================================================================
cover_table = [
  [{"text":"Mondelez International, Inc.","bold":True,"size":16}],
  [{"text":"Financial Model — Historical As-Reported Statements","italic":True}],
  [],
  ["Ticker", "MDLZ"],
  ["CIK", "0001103982"],
  ["Exchange", "Nasdaq"],
  ["Fiscal Year End", "December 31"],
  ["Currency / Units", "USD, $ in millions except per-share data"],
  ["Reporting Framework", "US GAAP"],
  [],
  ["Annual periods covered", "FY2016 - FY2025 (10 fiscal years)"],
  ["Quarterly periods covered", "3Q2024, 1Q2025, 2Q2025, 3Q2025, 1Q2026, 2Q2026"],
  ["Model date", "2026-09-15"],
  [],
  [{"text":"Scope note","bold":True}],
  [{"text":"This workbook is a mechanical financial model / data-prep artifact built directly from SEC filings (10-K and 10-Q source HTML). It contains no valuation opinion, price target, investment thesis, or buy/sell/hold recommendation."}],
]

sources_table = [
  [{"text":"Sources & Methodology","bold":True,"size":14}],
  [],
  [{"text":"Data provenance","bold":True}],
  ["All figures extracted from SEC EDGAR filings (10-K / 10-Q primary financial statement HTML tables) collected under research/companies/US/MDLZ-mondelez/outputs/company-research-to-excel-20260915/tables.json (1,598 tables). No financial_input.json existed for this company; the model was built in bundle-only mode directly from the collector output."],
  [],
  [{"text":"Filings used","bold":True}],
  ["10-K FY2016 (period end 2016-12-31)"], ["10-K FY2017 (2017-12-31)"], ["10-K FY2018 (2018-12-31)"],
  ["10-K FY2019 (2019-12-31)"], ["10-K FY2020 (2020-12-31)"], ["10-K FY2021 (2021-12-31)"],
  ["10-K FY2022 (2022-12-31)"], ["10-K FY2023 (2023-12-31)"], ["10-K FY2024 (2024-12-31)"],
  ["10-K FY2025 (2025-12-31)"],
  ["10-Q 3Q2024 (period end 2024-09-30, accession 0001103982-24-000104)"],
  ["10-Q 1Q2025 (2025-03-31, accession 0001103982-25-000127)"],
  ["10-Q 2Q2025 (2025-06-30, accession 0001103982-25-000188)"],
  ["10-Q 3Q2025 (2025-09-30, accession 0001628280-25-046773)"],
  ["10-Q 1Q2026 (2026-03-31, accession 0001628280-26-027937)"],
  ["10-Q 2Q2026 (2026-06-30, accession 0001628280-26-050179)"],
  [],
  [{"text":"Own-year sourcing convention","bold":True}],
  ["Every figure is sourced from each fiscal period's own primary filing (its own-year / own-quarter column), never from a later filing's comparative column. This was necessary because MDLZ has retrospectively restated multiple historical line items (e.g., FY2016-2018 Net earnings under ASU 2017-07 pension cost presentation; FY2019 'Equity method investment net earnings' reported as $442M in the FY2019 10-K vs. $501M as a comparative in the FY2020 10-K). Using each year's own-year column avoids contaminating the historical series with retroactive restatements."],
  [],
  [{"text":"Income Statement sign-convention normalization","bold":True}],
  ["MDLZ changed its Income Statement sign presentation between the FY2022 and FY2023 10-Ks. FY2016-2022 filings store Cost of sales, SG&A, Asset impairment and exit costs, Amortization of intangibles, and Interest and other expense net as POSITIVE magnitudes meant to be subtracted, and store the divestiture/acquisition gain and Benefit plan non-service income lines as NEGATIVE values also meant to be subtracted (double-negative = addback). FY2023-2025 filings and all six 10-Q filings present these same lines with their true economic sign directly (expenses negative, gains/income positive), added rather than subtracted. This model normalizes ALL periods to the true-economic-sign / additive convention: FY2016-2022 Cost of sales, SG&A, Asset impairment, Amortization, and Interest expense are sign-flipped to negative; the divestiture gain/loss line and Benefit plan non-service income (FY2018-2022 only) are sign-flipped to positive. Provision for income taxes, Noncontrolling interest earnings, and both equity-method lines were confirmed already additive in every year (no flip applied). This normalization was independently verified by reconstructing the full filed arithmetic chain (Gross profit -> Operating income -> EBT -> Net earnings -> Net earnings attributable) for FY2016, FY2023, FY2025 and 3Q2024, all of which tie exactly to the reported bottom line."],
  [],
  [{"text":"FY2024 data-recovery note","bold":True}],
  ["In the FY2024 10-K's Income Statement table, the row 'Gain/(loss) on equity method investment transactions' had its FY2024 numeric value accidentally concatenated into the row's label text during table extraction. The correct FY2024 value (-337) was recovered by cross-referencing the FY2025 10-K's comparative column for FY2024 in the same row, which independently confirms -337."],
  [],
  [{"text":"Quarterly Cash Flow Statement — fiscal-year-to-date (YTD) basis","bold":True}],
  ["MDLZ presents its Condensed Consolidated Statement of Cash Flows in each 10-Q on a fiscal-year-to-date cumulative basis, not a discrete-quarter basis. For example, the 3Q2025 CF column reflects 9 months of activity (Jan-Sep 2025), not just Q3 alone. This was confirmed by reconciling CF 'Net earnings' to the sum of the corresponding discrete-quarter IS 'Net earnings' figures (e.g., 2Q2025 CF Net earnings of $1,051M = Q1 2025 IS Net earnings $407M + Q2 2025 IS Net earnings $644M). As a result, quarterly CF columns in this model are NOT directly comparable to the quarterly IS/BS columns on a discrete-quarter basis; 1Q columns (1Q2025, 1Q2026) are the exception since Q1 YTD equals the discrete quarter."],
  [],
  [{"text":"Non-GAAP reconciliation — intentionally not modeled","bold":True}],
  ["MDLZ discloses non-GAAP measures narratively in its MD&A (Adjusted Operating Income, Adjusted EPS, Organic Net Revenue growth) but does not present a single consistent multi-year Adjusted EBITDA-style bridge table. A search of the full tables.json dataset (1,598 tables) found zero tables containing 'EBITDA' and only one fragmented 'Adjusted Operating Income' bridge (FY2016 10-K only, T033), containing 15+ one-off reconciling items (legacy restructuring programs, Venezuela deconsolidation, JDE coffee transaction, divestiture/acquisition items, intangible impairments) whose composition changes materially every year. Building a reliable 10-year Non-GAAP bridge from this fragmented disclosure would require re-verifying a different, evolving set of one-off items each year, with high risk of inconsistency or fabrication. This model therefore presents only a computed EBITDA proxy (Operating income + D&A) on the Derived Metrics sheet, not a GAAP-to-non-GAAP bridge matching MDLZ's own reported Adjusted metrics."],
  [],
  [{"text":"BS Detail sheet — not built","bold":True}],
  ["An optional BS Detail (footnote disaggregation) sheet was considered per the skill's Phase 4e pattern (goodwill by segment, intangibles by class, debt maturity schedule) but was not built in this pass given the scope of the 10-year + 6-quarter core statement build; the as-reported Balance Sheet face captures all consolidated line items needed for the balance and working-capital checks."],
  [],
  [{"text":"Segments","bold":True}],
  ["MDLZ reports four geographic operating segments — Latin America, AMEA (Asia, Middle East & Africa), Europe, and North America — unchanged throughout FY2016-2025. Segment revenue ties exactly to consolidated Net revenues; the reconciliation to consolidated Operating income and Earnings before tax uses MDLZ's own reported bridge items (mark-to-market gains/losses on hedging, general corporate expenses, amortization of intangibles, gain on divestitures, acquisition-related costs)."],
  [],
  [{"text":"Product categories","bold":True}],
  ["Product-category revenue by segment is presented for FY2023-FY2025 and 3Q2024 only. Prior years (FY2016-FY2022) use an incompatible product taxonomy in MDLZ's filings (no separate Gum & Candy category, and only percentage-of-revenue breakdowns disclosed rather than dollar figures), so they are excluded rather than approximated."],
  [],
  [{"text":"Scope","bold":True}],
  ["This workbook is a mechanical financial-model / data-preparation artifact only. It contains no investment thesis, valuation opinion, price target, or buy/sell/hold recommendation."],
]

# ============================================================================
# ASSEMBLE
# ============================================================================
model = {
  "company": {
    "name": "Mondelez International, Inc.",
    "ticker": "MDLZ",
    "currency": "USD",
    "units": "$ in millions except per-share data",
    "reporting_framework": "US GAAP",
    "fiscal_year_end": "December 31",
    "consolidation_scope": "",
    "as_of_date": "2025-12-31",
    "model_date": "2026-09-15",
  },
  "periods": {
    "annual": [{"label": lbl, "end": AEND[lbl]} for lbl in A],
    "scrap_cols": 3,
    "quarterly": [{"label": lbl, "end": QEND[lbl]} for lbl in Q],
  },
  "sheets": [
    {"name": "Cover", "kind": "table", "col_widths": [30, 60], "tab_color": "1F4E79", "table": cover_table},
    {"name": "Income Statement", "short": "IS", "kind": "statement", "tab_color": "1F4E79", "contents": True, "blocks": is_blocks},
    {"name": "Balance Sheet", "short": "BS", "kind": "statement", "tab_color": "1F4E79", "contents": True, "blocks": bs_blocks},
    {"name": "Cash Flow", "short": "CF", "kind": "statement", "tab_color": "1F4E79", "contents": True, "blocks": cf_blocks},
    {"name": "Segments", "short": "SEG", "kind": "statement", "tab_color": "548235", "contents": True, "blocks": seg_blocks},
    {"name": "Geography & Products", "short": "GEO", "kind": "statement", "tab_color": "548235", "contents": True, "blocks": geo_blocks},
    {"name": "Derived Metrics", "short": "DM", "kind": "statement", "tab_color": "7030A0", "contents": True, "blocks": dm_blocks},
    {"name": "Sources", "kind": "table", "col_widths": [100], "tab_color": "1F4E79", "table": sources_table},
  ],
}

if __name__ == "__main__":
    out_path = "/Users/tccc/Desktop/AI Invest/Workspace/research/companies/US/MDLZ-mondelez/outputs/company-research-to-excel-20260915/model.json"
    with open(out_path, "w") as f:
        json.dump(model, f, indent=2)
    print("Wrote", out_path)
    # quick row/sheet counts
    for s in model["sheets"]:
        if s.get("kind") == "statement":
            n = sum(len(b["rows"]) for b in s["blocks"])
            print(f"  {s['short']}: {len(s['blocks'])} blocks, {n} rows")
