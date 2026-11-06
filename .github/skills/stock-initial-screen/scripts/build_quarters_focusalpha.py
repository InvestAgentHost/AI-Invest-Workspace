#!/usr/bin/env python3
"""FocusAlpha quarters for the recent-quarter check (E1) and trailing figures: raw/quarters.json in pull_q.js's format.

    python3 build_quarters_focusalpha.py RUN_DIR KEY TICKER <saved get_income_statements quarterly output> [...] [--fye-month 12]

Input: FocusAlpha `get_income_statements` (period quarterly, limit 20) saved to files. The fiscal-year end month comes from the annual rows
already in raw/main*.json for KEY (the last annual period end), or --fye-month. The 'earn' date is FocusAlpha's `source_filed_at`
(the 10-Q or 10-K filing date; the earnings release is usually a few days to weeks earlier).
"""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fa_common import rows_of, D, fy_of_quarter, imp_fields, M

args = [a for a in sys.argv[1:] if not a.startswith('--')]
fm = int(sys.argv[sys.argv.index('--fye-month') + 1]) if '--fye-month' in sys.argv else None
if fm is not None: args.remove(str(fm))
run, key, ticker, files = args[0], args[1], args[2], args[3:]
if fm is None:
    main = {}
    for f in sorted(glob.glob(os.path.join(run, 'raw', 'main*.json'))): main.update(json.load(open(f)))
    fm = int(((main.get(key) or {}).get('fye') or '12-31')[:2]) if (main.get(key) or {}).get('fye') else 12
rows = {}
for r in rows_of(files, 'income_statements'):
    if r.get('period') not in (None, 'quarterly') or not str(r.get('fiscal_period', '')).startswith('Q'): continue
    rp = r['report_period']; old = rows.get(rp)
    if old is None or (r.get('source_filed_at') or '') > (old.get('source_filed_at') or ''): rows[rp] = r
out = []
for rp in sorted(rows):
    r = rows[rp]; ks = imp_fields(r)
    out.append([fy_of_quarter(D(rp), fm), int(r['fiscal_period'][1]), rp, r.get('source_filed_at'), M(r.get('revenue')), M(r.get('gross_profit')),
                M(r.get('operating_income') if r.get('operating_income') is not None else r.get('ebit')),
                round(sum(abs(r[k]) for k in ks) / 1e6, 1) if ks else 0, M(r.get('net_income_common_stock') if r.get('net_income_common_stock') is not None else r.get('net_income'))])
out = out[-16:]
cur = next((r.get('currency') for r in rows.values() if r.get('currency')), None)
dst = os.path.join(run, 'raw', 'quarters.json'); old = json.load(open(dst)) if os.path.exists(dst) else {}
old[key] = dict(kind='quarterly', cur=cur, impSrc='FocusAlpha: ' + (', '.join(sorted({k for r in rows.values() for k in imp_fields(r)})) or 'none'),
                cols=['fy', 'q', 'end', 'earn', 'rev', 'gp', 'op', 'imp', 'ni'], rows=out, src=f'FocusAlpha get_income_statements (quarterly) for {ticker}')
os.makedirs(os.path.dirname(dst), exist_ok=True); json.dump(old, open(dst, 'w'))
print(f"{key}: {len(out)} quarters, FY{out[0][0]} Q{out[0][1]} – FY{out[-1][0]} Q{out[-1][1]} (fiscal year ends month {fm}) -> raw/quarters.json" if out else f"{key}: no quarters")
