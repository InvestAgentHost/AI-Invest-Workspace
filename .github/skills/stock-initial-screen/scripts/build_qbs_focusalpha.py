#!/usr/bin/env python3
"""FocusAlpha quarterly balance sheets for rebuild_multiples.py: raw/qbs.json in pull_qbs.js's format.

    python3 build_qbs_focusalpha.py RUN_DIR KEY TICKER --bs <saved get_balance_sheets quarterly> [...] --is <saved get_income_statements quarterly> [...] [--fye-month 12]

Debt = total debt + operating lease liability (as build_rows_focusalpha.py); cash = cash and equivalents; diluted shares = the quarter's
weighted diluted shares from the income statement; available = FocusAlpha `source_filed_at`.
"""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fa_common import rows_of, D, fy_of_quarter, M

a = sys.argv[1:]
run, key, ticker = a[0], a[1], a[2]
def grab(flag):
    if flag not in a: return []
    i = a.index(flag) + 1; out = []
    while i < len(a) and not a[i].startswith('--'): out.append(a[i]); i += 1
    return out
bsf, isf = grab('--bs'), grab('--is')
fm = int(a[a.index('--fye-month') + 1]) if '--fye-month' in a else 12
first = lambda r, *ks: next((r[k] for k in ks if r and r.get(k) is not None), None)
B, I = {}, {}
for store, files, name in ((B, bsf, 'balance_sheets'), (I, isf, 'income_statements')):
    for r in rows_of(files, name):
        if not str(r.get('fiscal_period', '')).startswith('Q') and r.get('period') != 'quarterly': continue
        rp = r['report_period']; old = store.get(rp)
        if old is None or (r.get('source_filed_at') or '') > (old.get('source_filed_at') or ''): store[rp] = r
rows = []
for rp in sorted(B):
    b = B[rp]; i = I.get(rp) or {}
    debt = first(b, 'total_debt', 'long_term_debt_incl_current')
    if debt is None: continue
    debt += first(b, 'operating_lease_liability') or 0
    fp = str(b.get('fiscal_period') or i.get('fiscal_period') or 'Q0')
    rows.append([fy_of_quarter(D(rp), fm), int(fp[1]) if fp[1:].isdigit() else None, rp, b.get('source_filed_at'), M(debt), M(first(b, 'cash_and_equivalents')), M(first(i, 'weighted_average_shares_diluted'))])
dst = os.path.join(run, 'raw', 'qbs.json'); old = json.load(open(dst)) if os.path.exists(dst) else {}
old[key] = dict(kind='quarterly balance sheet', cols=['fy', 'q', 'end', 'avail', 'debt', 'cash', 'dil'], rows=rows, src=f'FocusAlpha get_balance_sheets / get_income_statements (quarterly) for {ticker}')
os.makedirs(os.path.dirname(dst), exist_ok=True); json.dump(old, open(dst, 'w'))
print(f"{key}: {len(rows)} quarterly balance sheets {rows[0][2] if rows else ''} – {rows[-1][2] if rows else ''} -> raw/qbs.json")
