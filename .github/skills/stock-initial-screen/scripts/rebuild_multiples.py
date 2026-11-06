#!/usr/bin/env python3
"""Rebuild the daily multiples of one company when Fiscal.ai has no daily P/E or EV series for it (v4.11.2, Codex fallback), and for every
company in the FocusAlpha-only version (v4.11.4; prices from build_prices_focusalpha.py, quarters and balance sheets from the FocusAlpha converters).

    python3 rebuild_multiples.py RUN_DIR KEY --prices prices.csv --source "<where the prices came from>"
        [--unit 1] [--fx fx.csv] [--fy-end MM-DD] [--lag-days 60] [--fwd 18.4 --fwd-source "<page, date>"] [--dry]

Writes raw/pe.json[KEY] and raw/ev.json[KEY] in the format the engine reads (pull_pe.js / pull_ev.js), with a `src` line that the
page prints as the flag "Multiples rebuilt outside Fiscal.ai", and an audit table raw/rebuilt_<KEY>.csv with every input per day.

Only the share price comes from outside. Every other input is already in the run folder from Fiscal.ai or FocusAlpha:
  raw/main*.json (annual: op, da, debt incl. leases, cash, diluted shares, net income) and raw/quarters.json (the last 16 quarters: op, ni,
  period end, earnings date). Method, the same definitions as Fiscal.ai's series as far as the data allows:
  - trailing figures = the last 4 reported quarters when all 4 are available on that day (earnings date, or period end + lag), else the
    latest fiscal year available on that day (fiscal year end + lag);
  - P/E = price x diluted shares / trailing net income; EV = price x diluted shares + debt (leases included) - cash, from the latest
    year-end balance sheet available that day; EV/EBIT = EV / trailing operating profit; EV/EBITDA = EV / (trailing operating profit +
    the latest annual depreciation and amortization; quarterly D&A is not in the data);
  - prices.csv: `date,close[,source]`, one row per trading day, any order. Weekly or monthly closes are accepted only when no daily
    series can be found: each close is then held flat until the next one, and the source line says so.
Currency: the prices must be in the reporting currency, after --unit (0.01 for pence). When the listing trades in another currency, pass
--fx (`date,rate`, reporting currency per unit of trading currency); without it the script stops rather than mixing currencies.
"""
import argparse, csv, datetime as dt, glob, json, os, statistics as st, sys

ap = argparse.ArgumentParser()
ap.add_argument('run'); ap.add_argument('key')
ap.add_argument('--prices', required=True); ap.add_argument('--source', required=True)
ap.add_argument('--unit', type=float, default=1.0); ap.add_argument('--fx')
ap.add_argument('--fy-end'); ap.add_argument('--lag-days', type=int, default=60)
ap.add_argument('--bs-quarters', help='CSV avail_date,debt_m,cash_m,diluted_shares_m (from FocusAlpha get_balance_sheets or the 10-Q) when raw/qbs.json has no rows for the key')
ap.add_argument('--fwd', type=float); ap.add_argument('--fwd-source', default='')
ap.add_argument('--from', dest='frm'); ap.add_argument('--trading-currency')
ap.add_argument('--dry', action='store_true', help='write only the audit table, not pe.json / ev.json')
a = ap.parse_args()
P = lambda *x: os.path.join(a.run, *x)
D = lambda s: dt.date.fromisoformat(str(s)[:10])

main = {}
for f in sorted(glob.glob(P('raw', 'main*.json'))): main.update(json.load(open(f)))
if a.key not in main or 'rows' not in main[a.key]: sys.exit(f'{a.key}: no annual rows in raw/main*.json; pull the financials first (Fiscal.ai, else FocusAlpha)')
M = main[a.key]; rcur = M.get('cur')
ann = {r[0]: dict(zip(M['cols'], r)) for r in M['rows']}
Q = (json.load(open(P('raw', 'quarters.json'))) if os.path.exists(P('raw', 'quarters.json')) else {}).get(a.key) or {}
qs = [dict(zip(Q['cols'], r)) for r in Q.get('rows', [])] if Q.get('rows') else []
cfg = json.load(open(P('config.json'))) if os.path.exists(P('config.json')) else {}
asof = D(cfg.get('as_of') or dt.date.today().isoformat())
frm = D(a.frm) if a.frm else asof.replace(year=asof.year - 10)
tcur = a.trading_currency or ((json.load(open(P('raw', 'pe.json'))).get(a.key) or {}).get('cur') if os.path.exists(P('raw', 'pe.json')) else None)

# fiscal year end: from a Q4 period end in the quarters, else --fy-end, else 31 Dec
fye = None
for q in qs:
    if q.get('q') == 4 and q.get('end'): fye = D(q['end']).strftime('%m-%d')
fye = a.fy_end or fye or '12-31'
def fy_end_date(fy):
    m, d = int(fye[:2]), int(fye[3:])
    y = fy if m >= 6 else fy + 1        # a fiscal year ending Jan-May is named for the year before in most data (fiscal 2025 ends Jan 2026)
    try: return dt.date(y, m, d)
    except ValueError: return dt.date(y, m, 28)
q4earn = {q['fy']: D(q['earn']) for q in qs if q.get('q') == 4 and q.get('earn')}
avail_ann = {fy: q4earn.get(fy) or fy_end_date(fy) + dt.timedelta(days=a.lag_days) for fy in ann}
def q_avail(q):
    if q.get('earn'): return D(q['earn'])
    return D(q['end']) + dt.timedelta(days=a.lag_days) if q.get('end') else None

# prices
px = {}
for row in csv.reader(open(a.prices)):
    if not row or not row[0][:4].isdigit(): continue
    try: px.setdefault(D(row[0]), float(row[1]) * a.unit)
    except ValueError: continue
if not px: sys.exit('no prices read from ' + a.prices)
fx = {}
if a.fx:
    for row in csv.reader(open(a.fx)):
        if row and row[0][:4].isdigit(): fx[D(row[0])] = float(row[1])
if tcur and rcur and tcur != rcur and not fx: sys.exit(f'the listing trades in {tcur} and reports in {rcur}: pass --fx (date,rate) or use a listing in {rcur}')
days = sorted(px)
gaps = [(b - c).days for c, b in zip(days, days[1:])]
held = bool(gaps) and st.median(gaps) > 4
if held:   # weekly or monthly closes: hold each close until the next one, on weekdays
    full = {}; d0 = days[0]; i = 0
    while d0 <= days[-1]:
        while i + 1 < len(days) and days[i + 1] <= d0: i += 1
        if d0.weekday() < 5: full[d0] = px[days[i]]
        d0 += dt.timedelta(days=1)
    px = full; days = sorted(px)
fxd = sorted(fx)
def fx_on(d):
    if not fx: return 1.0
    prior = [x for x in fxd if x <= d]
    return fx[prior[-1]] if prior else fx[fxd[0]]

def ttm(d):
    """Trailing operating profit and net income on day d: last 4 quarters if all available, else the latest fiscal year."""
    av = sorted([q for q in qs if q_avail(q) and q_avail(q) <= d and q.get('op') is not None and q.get('ni') is not None], key=lambda q: (q['fy'], q['q']))
    if len(av) >= 4:
        l4 = av[-4:]
        seq = [(q['fy'] * 4 + q['q']) for q in l4]
        if seq == list(range(seq[0], seq[0] + 4)):
            return sum(q['op'] for q in l4), sum(q['ni'] for q in l4), f"4Q to FY{l4[-1]['fy']} Q{l4[-1]['q']}"
    fy = max([y for y, ad in avail_ann.items() if ad <= d and ann[y].get('op') is not None], default=None)
    if fy is None: return None, None, ''
    return ann[fy]['op'], ann[fy].get('nicf'), f"FY{fy}"
QB = (json.load(open(P('raw', 'qbs.json'))) if os.path.exists(P('raw', 'qbs.json')) else {}).get(a.key) or {}
qpts = []   # (available date, debt, cash, diluted shares, label): quarterly balance sheets, so net debt and shares move each quarter
for r in QB.get('rows') or []:
    x = dict(zip(QB['cols'], r))
    av = D(x['avail']) if x.get('avail') else (D(x['end']) + dt.timedelta(days=a.lag_days) if x.get('end') else None)
    if av and x.get('debt') is not None and x.get('cash') is not None: qpts.append((av, x['debt'], x['cash'], x.get('dil'), f"FY{x['fy']} Q{x['q']} balance sheet"))
if a.bs_quarters:
    for row in csv.reader(open(a.bs_quarters)):
        if row and row[0][:4].isdigit(): qpts.append((D(row[0]), float(row[1]), float(row[2]), float(row[3]) if len(row) > 3 and row[3] else None, f"balance sheet available {row[0]} (--bs-quarters)"))
qpts.sort()
def bs(d):
    fy = max([y for y, ad in avail_ann.items() if ad <= d and ann[y].get('dil')], default=None)
    if fy is None: return None
    x = ann[fy]; o = dict(fy=fy, sh=x['dil'], nd=(x.get('debt') or 0) - (x.get('cash') or 0), da=x.get('da'), lab=f"FY{fy} balance sheet", av=avail_ann[fy])
    qp = [q for q in qpts if q[0] <= d]
    if qp and qp[-1][0] > o['av']:   # a later quarter-end balance sheet replaces the year-end one
        q = qp[-1]; o.update(nd=q[1] - q[2], lab=q[4], sh=q[3] or o['sh'])
    return o

y6 = lambda d: d.strftime('%y%m%d')
out = dict(d=[], pe=[], ebit=[], ebitda=[], tev=[], px=[]); audit = []
for d in days:
    if d < frm or d > asof: continue
    b = bs(d); op, ni, basis = ttm(d)
    if not b or op is None: continue
    p = px[d] * fx_on(d)                       # price in reporting currency
    mcap = p * b['sh']                          # millions (shares in millions)
    ev = mcap + b['nd']
    pe = round(mcap / ni, 1) if ni not in (None, 0) else ''
    ebit = round(ev / op, 1) if op else ''
    ebitda = round(ev / (op + (b['da'] or 0)), 1) if (op + (b['da'] or 0)) else ''
    out['d'].append(y6(d)); out['pe'].append(pe); out['ebit'].append(ebit); out['ebitda'].append(ebitda); out['tev'].append(round(ev, 1)); out['px'].append(round(px[d], 4))
    audit.append([d.isoformat(), round(px[d], 4), round(fx_on(d), 6), b['sh'], round(mcap, 1), b['nd'], round(ev, 1), op, ni, b['da'], basis, b['lab'], pe, ebit, ebitda])
if len(out['d']) < 250: print(f"warning: only {len(out['d'])} days rebuilt; the engine needs 250 positive days for a range")
with open(P('raw', f"rebuilt_{a.key}.csv"), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['date', 'close', 'fx', 'diluted_shares_m', 'market_value_m', 'net_debt_m', 'ev_m', 'op_ttm_m', 'ni_ttm_m', 'da_annual_m', 'trailing_basis', 'balance_sheet', 'pe', 'ev_ebit', 'ev_ebitda'])
    w.writerows(audit)
src = (f"{a.source}; daily multiples rebuilt by rebuild_multiples.py = close x diluted shares ÷ trailing net income (P/E), EV = market value + debt incl. leases − cash "
       f"÷ trailing operating profit (EV/EBIT) and ÷ operating profit + annual D&A (EV/EBITDA); net debt and shares from the latest balance sheet available that day" + (" (quarterly)" if qpts else " (year-end only: no quarterly balance sheets)") + f"; fundamentals from the run's Fiscal.ai/FocusAlpha data, available {a.lag_days} days after period end "
       f"unless an earnings date is known" + ("; weekly or monthly closes held flat between dates" if held else '') + (f"; forward P/E {a.fwd} from {a.fwd_source}" if a.fwd else ''))
print(f"{a.key}: {len(out['d'])} days {out['d'][0] if out['d'] else ''}–{out['d'][-1] if out['d'] else ''}; today P/E {out['pe'][-1] if out['pe'] else '–'}, EV/EBIT {out['ebit'][-1] if out['ebit'] else '–'}, EV/EBITDA {out['ebitda'][-1] if out['ebitda'] else '–'}; audit raw/rebuilt_{a.key}.csv")
if a.dry: sys.exit(0)
J = lambda xs: ','.join('' if v == '' else str(v) for v in xs)
pej = json.load(open(P('raw', 'pe.json'))) if os.path.exists(P('raw', 'pe.json')) else {}
evj = json.load(open(P('raw', 'ev.json'))) if os.path.exists(P('raw', 'ev.json')) else {}
last = audit[-1] if audit else None
pej[a.key] = dict(d=J(out['d']), r=J(out['pe']), price=last[1] if last else None, mcap=(last[4] * 1e6 / (last[2] or 1)) if last else None,
                  fwd=a.fwd, ttm=out['pe'][-1] if out['pe'] and out['pe'][-1] != '' else None, cur=tcur or rcur, src=src)
evj[a.key] = dict(ebit=dict(d=J(out['d']), r=J(out['ebit'])), ebitda=dict(d=J(out['d']), r=J(out['ebitda'])), tev=dict(d=J(out['d']), r=J(out['tev'])),
                  px=dict(d=J(out['d']), r=J(out['px'])), pxCur=tcur or rcur, pxListing=a.key, src=src)
json.dump(pej, open(P('raw', 'pe.json'), 'w')); json.dump(evj, open(P('raw', 'ev.json'), 'w'))
print('written: raw/pe.json and raw/ev.json for', a.key)
