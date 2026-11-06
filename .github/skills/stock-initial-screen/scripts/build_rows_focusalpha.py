#!/usr/bin/env python3
"""FocusAlpha annual rows in pull_main.js's columns (v4.11.3; v4.11.4 adds `fye`). Fiscal.ai versions of the skill: only for a company
Fiscal.ai lacks (screener.py stops when most run companies lack Fiscal.ai, unless config.json `data_route` records the user's approval).
FocusAlpha-only version (config.json `data_route` set): every run company and every peer (peers: --out raw/peers_fa.json with the
universe folder as RUN_DIR).

    python3 build_rows_focusalpha.py RUN_DIR KEY TICKER <saved get_all_financials output> [more saved outputs ...] [--out raw/main_fa.json]

Input: FocusAlpha `get_all_financials` (period annual, limit 12) saved to files. Pass every saved part; the newest value of a period wins.
Rules (Codex run of 27 industrials, 3 Nov 2026: dropping every year FocusAlpha marks `not_comparable` left Dover, IDEX and Lincoln Electric
with 1-2 years and moved their labels):
  - every fiscal year is kept, including figures FocusAlpha marks `not_comparable` (on an earlier basis, before a later restatement).
    Fiscal.ai keeps those years too; the engine's own perimeter flags and the fact collectors decide whether a break cuts the window.
    The years and fields on an earlier basis are listed in `basis_note`, and save_raw.py prints the note.
  - a null is never read as zero, except amortization and impairments, where the engine's own rule (blank = 0, page note) applies.
Columns, millions of reporting currency (as pull_main.js): fy, rev, op, gp, am, imp, debt, eq, cash, gw, ia, cfo, capex, sbc, nicf, int,
intInc, pt, tax, dil, cfoCont, cfoDisc, da. debt = total debt + operating lease liability (finance leases sit in total debt in most filings).
am = the cash-flow `amortization` line (all intangibles amortization; the fact collector replaces it with acquired-only where filed).
"""
import json, os, re, sys
args = [a for a in sys.argv[1:] if not a.startswith('--')]
out_rel = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else 'raw/main_fa.json'
if '--out' in sys.argv: args.remove(out_rel)
run, key, ticker, files = args[0], args[1], args[2], args[3:]
if not files: sys.exit(__doc__)

def load(p):
    t = open(p).read(); i = t.find('{'); return json.loads(t[i:t.rfind('}') + 1])
IS, BS, CF, basis = {}, {}, {}, []
for p in files:
    d = load(p); f = d.get('financials', d)
    for name, store in (('income_statements', IS), ('balance_sheets', BS), ('cash_flow_statements', CF)):
        for r in f.get(name) or []:
            if r.get('fiscal_period') not in (None, 'FY') or r.get('period') not in (None, 'annual'): continue
            rp = r['report_period']; old = store.get(rp)
            if old is None or (r.get('source_filed_at') or '') > (old.get('source_filed_at') or ''): store[rp] = r
    basis += d.get('basis_changes') or []
fy = lambda rp: int(rp[:4]) if int(rp[5:7]) >= 6 else int(rp[:4]) - 1      # fiscal year ending Jan-May is named for the year before
M = lambda v: None if v is None else round(v / 1e6, 1)
A = lambda v: None if v is None else round(abs(v) / 1e6, 1)
def first(r, *ks):
    for k in ks:
        if r and r.get(k) is not None: return r[k]
    return None
def imp(r):
    if not r: return None
    ks = [k for k in r if re.search(r'impairment', k) and re.search(r'goodwill|intangible', k) and r[k] is not None]
    return round(sum(abs(r[k]) for k in ks) / 1e6, 1) if ks else None
rows, early = [], {}
for rp in sorted(set(IS) | set(BS) | set(CF)):
    i, b, c = IS.get(rp), BS.get(rp), CF.get(rp)
    for r in (i, b, c):
        for fld, why in ((r or {}).get('not_comparable') or {}).items():
            if why: early.setdefault(fy(rp), set()).add(fld)
    debt = first(b, 'total_debt', 'long_term_debt_incl_current')
    if debt is not None: debt = debt + (first(b, 'operating_lease_liability') or 0)
    capex = first(c, 'capital_expenditure', 'total_capex_ex_acquisitions')
    rows.append([fy(rp), M(first(i, 'revenue')), M(first(i, 'operating_income', 'ebit')), M(first(i, 'gross_profit')),
                 A(first(c, 'amortization')), imp(i), M(debt), M(first(b, 'total_equity', 'shareholders_equity')), M(first(b, 'cash_and_equivalents')),
                 M(first(b, 'goodwill')), M(first(b, 'intangible_assets')), M(first(c, 'net_cash_flow_from_operations')),
                 None if capex is None else -A(capex), M(first(c, 'share_based_compensation')), M(first(c, 'cf_net_income', 'net_income')),
                 A(first(i, 'interest_expense')), A(first(i, 'interest_income')), M(first(i, 'pretax_income')), M(first(i, 'income_tax_expense')),
                 M(first(i, 'weighted_average_shares_diluted')), M(first(c, 'cfo_continuing')), M(first(c, 'cfo_discontinued')),
                 M(first(c, 'depreciation_and_amortization'))])
rows = [r for r in rows if r[1] is not None]
if not rows: sys.exit('no annual income statements in the saved files')
cur = next((r.get('currency') for r in IS.values() if r.get('currency')), None)
note = '; '.join(f"FY{y}: {len(f)} fields on an earlier basis (kept)" for y, f in sorted(early.items()))
entry = dict(L=rows[-1][0], cur=cur, cols=['fy', 'rev', 'op', 'gp', 'am', 'imp', 'debt', 'eq', 'cash', 'gw', 'ia', 'cfo', 'capex', 'sbc', 'nicf', 'int', 'intInc', 'pt', 'tax', 'dil', 'cfoCont', 'cfoDisc', 'da'],
             rows=rows[-21:], amSrc='FocusAlpha cash flow: amortization (all intangibles)', impSrc='FocusAlpha income statement: ' + (', '.join(sorted({k for r in IS.values() for k in r if re.search(r'impairment', k) and re.search(r'goodwill|intangible', k)})) or 'none'),
             cfoSrc='FocusAlpha cash flow: cfo_continuing / cfo_discontinued', fye=max(IS)[5:10], src=f'FocusAlpha get_all_financials (annual) for {ticker}; built by build_rows_focusalpha.py', basis_note=note)
dst = os.path.join(run, out_rel); old = json.load(open(dst)) if os.path.exists(dst) else {}
old[key] = entry; os.makedirs(os.path.dirname(dst), exist_ok=True); json.dump(old, open(dst, 'w'))
print(f"{key}: FY{rows[0][0]}–FY{rows[-1][0]} ({len(rows)} years), {cur}; earlier-basis years kept: {', '.join(f'FY{y}' for y in sorted(early)) or 'none'} -> {out_rel}")
