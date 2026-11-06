#!/usr/bin/env python3
"""FocusAlpha daily closes for rebuild_multiples.py, on the same share basis as FocusAlpha's statements.

    python3 build_prices_focusalpha.py RUN_DIR TICKER --prices <saved get_market_data prices pages> [...] --splits <saved get_market_data splits>
                                        [--web web.csv] [--symbol DOV]

Writes RUN_DIR/scratch/px_<TICKER>.csv (date,close,source) for rebuild_multiples.py --prices.
Price basis: FocusAlpha statements restate share counts for whole-number splits only, so the close used is `close_as_traded` divided by
every later split with `restates_per_share` true. `close` (adjusted) is not used: it is also restated for spin-offs (Dover's 2018 Apergy
spin-off is listed as a 619:500 "split" that does not restate per-share figures), which would understate the P/E of the years before.
History: FocusAlpha prices start on 2018-09-01. --web adds earlier closes from a CSV (date,close[,source]) found on the web, used only when it
agrees with the FocusAlpha series on the overlapping days (median difference within 1% over at least 20 days, after the same split basis);
a dividend-adjusted series fails the check and is not used.
"""
import csv, os, statistics as st, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fa_common import rows_of, D

a = sys.argv[1:]; run, ticker = a[0], a[1]
def grab(flag):
    if flag not in a: return []
    i = a.index(flag) + 1; out = []
    while i < len(a) and not a[i].startswith('--'): out.append(a[i]); i += 1
    return out
sym = grab('--symbol')[0] if grab('--symbol') else None
px = {}
for r in rows_of(grab('--prices'), 'data'):
    if sym and r.get('symbol') != sym: continue
    if r.get('close_as_traded') is None: continue
    px[D(r['date'])] = float(r['close_as_traded'])
if not px: sys.exit('no FocusAlpha prices read')
splits = [(D(r['date']), r['numerator'] / r['denominator']) for r in rows_of(grab('--splits'), 'data') if r.get('restates_per_share') and (not sym or r.get('symbol') == sym)]
factor = lambda d: __import__('math').prod([x for sd, x in splits if sd > d] or [1.0])
ser = {d: round(v / factor(d), 4) for d, v in px.items()}
src = {d: 'FocusAlpha get_market_data close_as_traded' + (' ÷ later splits' if factor(d) != 1 else '') for d in ser}
note = f"FocusAlpha get_market_data, {min(ser)}–{max(ser)}"
for w in grab('--web'):
    web = {}
    for row in csv.reader(open(w)):
        if row and row[0][:4].isdigit():
            try: web[D(row[0])] = (float(row[1]), row[2] if len(row) > 2 else w)
            except ValueError: pass
    adj = {d: (v / factor(d), s) for d, (v, s) in web.items()}
    ov = [abs(adj[d][0] / ser[d] - 1) for d in adj if d in ser]
    if len(ov) < 20 or st.median(ov) > .01:
        print(f"web prices {w} NOT used: {len(ov)} overlapping days, median difference {st.median(ov) * 100 if ov else float('nan'):.2f}% (needs >= 20 days within 1%)"); continue
    early = {d: v for d, v in adj.items() if d < min(ser)}
    for d, (v, s) in early.items(): ser[d] = round(v, 4); src[d] = 'web: ' + s
    note += f"; web closes {min(early)}–{max(early)} ({len(early)} days, overlap check {len(ov)} days, median difference {st.median(ov) * 100:.2f}%)" if early else ''
os.makedirs(os.path.join(run, 'scratch'), exist_ok=True)
out = os.path.join(run, 'scratch', f'px_{ticker}.csv')
with open(out, 'w', newline='') as f:
    wr = csv.writer(f); wr.writerow(['date', 'close', 'source'])
    for d in sorted(ser): wr.writerow([d.isoformat(), ser[d], src[d]])
print(f"{ticker}: {len(ser)} days {min(ser)}–{max(ser)}; splits applied: {', '.join(f'{d} {x:g}' for d, x in splits if d > min(ser)) or 'none in the window'} -> {out}")
print('source line for rebuild_multiples.py --source:', note)
