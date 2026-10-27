#!/usr/bin/env python3
"""Company initial screener v4 - HTML page with traffic lights for three separate factors (no chart of the factors). python3 make_html.py RUN_DIR -> RUN_DIR/<config.output or screener_scores.html>
Reads RUN_DIR/page_data.json (from screener.py build), RUN_DIR/config.json and RUN_DIR/page_text.json (run-specific text)."""
import json, html, datetime, os, re, sys, hashlib
from pathlib import Path
RUN = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
P = lambda *a: os.path.join(RUN, *a)
D = json.load(open(P('page_data.json')))
CFG = json.load(open(P('config.json')))
TXT = json.load(open(P('page_text.json'))) if os.path.exists(P('page_text.json')) else {}
if CFG.get('valuation_pipeline_required'):
    from valuation_pipeline import check_run
    _preflight = check_run(Path(RUN))
    if not _preflight['passed']:
        sys.exit('Delivery checks failed: ' + '; '.join(_preflight['errors']))
# v4.7.2: the rules version and engine come from the build that made page_data.json, never from hand-typed text
if not os.path.exists(P('run_meta.json')):
    sys.exit('run_meta.json is missing: run screener.py RUN_DIR build with this engine first (it writes the rules version the page prints)')
META = json.load(open(P('run_meta.json')))
RV, ENG = META['rules_version'], META['engine']
if CFG.get('rules_version') and CFG['rules_version'] != RV:
    sys.exit(f"config.json says rules_version {CFG['rules_version']}, but page_data.json was built under rules {RV}: rebuild, or correct config.json")
for _k in ('sub', 'sources'):
    _t = TXT.get(_k) or ''
    for _m in re.finditer(r'rules version (\d{4}-\d{2}-\d{2}[a-z]?)', _t):
        if _m.group(1) != RV: sys.exit(f"page_text.json {_k} says 'rules version {_m.group(1)}', but the build used rules {RV}: correct the text")
    for _m in re.finditer(r'engine (v\d+(?:\.\d+)*)', _t):
        if _m.group(1) != ENG: sys.exit(f"page_text.json {_k} says 'engine {_m.group(1)}', but the build used engine {ENG}: correct the text")
    for _m in re.finditer(r'engine v[\d.]+, rules (\d{4}-\d{2}-\d{2}[a-z]?)', _t):
        if _m.group(1) != RV: sys.exit(f"page_text.json {_k} says 'rules {_m.group(1)}' for this build, but the build used rules {RV}: correct the text")
REOPEN = json.load(open(P('reopen.json'))) if os.path.exists(P('reopen.json')) else None   # v4.3: from vault_records.py compare
AS_OF = CFG.get('as_of') or datetime.date.today().isoformat()
_y, _m, _d = AS_OF.split('-')
PE_DEFAULT_FROM = CFG.get('pe_default_from') or f"{int(_y) - 10}-{_m}-{_d}"
def _later(a, b, days=31):
    return (datetime.date.fromisoformat(a) - datetime.date.fromisoformat(b)).days > days
CATS = ['Research now', 'Quick look', 'Research at lower price', 'Not now']
CATCLS = {'Research now': 'r-now', 'Quick look': 'r-quick', 'Research at lower price': 'r-watch', 'Not now': 'r-pass'}
KINDS = ['good', 'average', 'early', 'weak', 'redflag']
def _rank(t):
    r = D[t].get('result') or {}
    sub = (KINDS.index(r.get('kind')) if r.get('kind') in KINDS else 9, r.get('pct') if r.get('pct') is not None else 999)
    return (CATS.index(r['cat']) if r.get('cat') in CATS else 9, bool(D[t]['removed']), sub)
def cap1(x): return x[:1].upper() + x[1:] if x else x
def result_cell(c, full=False):
    r = c.get('result') or {}
    if not r: return ''
    why = [cap1(w) for w in r['why']]
    tip = '. '.join(why) + ('. Re-look signal: ' + '; '.join(r['relook']) if r['relook'] else '') + ('. Note: ' + '; '.join(r['caution']) if r['caution'] else '')
    sub = ''.join(f"<div>{E(x)}</div>" for x in r.get('lines') or [])
    return f"<span class='res {CATCLS[r['cat']]}' title='{E(tip)}'>{E(r['cat'])}</span>" + (f"<div class='rwhy'>{sub}</div>" if sub else '')
QL, QB, PEL = 3.5, 3.0, [33, 50, 67]
ORDER = sorted(D, key=_rank)
SYM = {'USD': '$', 'EUR': '€', 'GBP': '£'}
def money(x, cur='USD'): return '–' if x is None else f"{SYM.get(cur, (cur or '') + ' ')}{x:,.2f}"
E = lambda s: html.escape(str(s), quote=True)
def ordn(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"

def fnum(x):
    if x is None: return '–'
    return f"{x:.1f}" if isinstance(x, float) else str(x)

# ---------------- multiples: three percentiles and their median
MK = [('pe', 'P/E', 'mk-pe'), ('ebit', 'EV/EBIT', 'mk-ebit'), ('ebitda', 'EV/EBITDA', 'mk-ebitda')]
def mk_shape(cls, x, y, r=4.5):
    if cls == 'mk-pe': return f"<circle cx='{x:.1f}' cy='{y}' r='{r}' class='mk {cls}'/>"
    if cls == 'mk-ebit': return f"<rect x='{x - r:.1f}' y='{y - r}' width='{2 * r}' height='{2 * r}' class='mk {cls}'/>"
    return f"<path d='M{x:.1f} {y - r - 1} L{x + r + 1:.1f} {y + r} L{x - r - 1:.1f} {y + r} Z' class='mk {cls}'/>"

def mult_strip():
    rows = sorted([t for t in ORDER if D[t]['mult']['band']], key=lambda t: D[t]['mult']['pct']) + [t for t in ORDER if not D[t]['mult']['band']]
    x0, w = 230, 520; sx = lambda v: x0 + v / 100 * w
    h = 80 + 40 * len(rows)
    body = [f"<svg viewBox='0 0 1010 {h}' role='img' aria-label='Each stock\'s multiples against their own history, as percentiles'>",
            f"<text x='{x0}' y='18' class='muted'>Axis = percentile of the stock's own history (0 = lowest, 100 = highest) · shading = thirds · line = 50th</text>",
            f"<g transform='translate({x0},34)'>" + mk_shape('mk-pe', 6, 0) + "<text x='16' y='4' class='tick'>P/E</text>" + mk_shape('mk-ebit', 66, 0) + "<text x='76' y='4' class='tick'>EV/EBIT</text>"
            + mk_shape('mk-ebitda', 146, 0) + "<text x='156' y='4' class='tick'>EV/EBITDA</text><circle cx='246' cy='0' r='6' class='now'/><text x='256' y='4' class='tick'>median of the three</text></g>",
            f"<text x='{x0 + w + 110}' y='58' class='hdr' text-anchor='end'>Median</text><text x='{x0 + w + 250}' y='58' class='hdr' text-anchor='end'>Research line</text>"]
    for i, t in enumerate(rows):
        y = 84 + 40 * i; m = D[t]['mult']
        body.append(f"<a href='#{t}' data-open='{t}'><text x='0' y='{y + 4}' class='lbl'>{E(D[t]['name'])}</text></a>")
        if not m['band']:
            body.append(f"<text x='{x0}' y='{y + 4}' class='muted'>Not meaningful: {E(m['why'])}</text>"); continue
        body.append(f"<rect x='{sx(0):.1f}' y='{y - 7}' width='{w / 3:.1f}' height='14' class='b-bot' rx='2'/><rect x='{sx(100 / 3):.1f}' y='{y - 7}' width='{w / 3:.1f}' height='14' class='b-mid'/><rect x='{sx(200 / 3):.1f}' y='{y - 7}' width='{w / 3:.1f}' height='14' class='b-top' rx='2'/>"
                    f"<line x1='{sx(50):.1f}' x2='{sx(50):.1f}' y1='{y - 10}' y2='{y + 10}' class='med'/>")
        for k, nm, cls in MK:
            d = m['metrics'][k]
            if d['pct'] is None: continue
            body.append(f"<g>{mk_shape(cls, sx(d['pct']), y)}<title>{E(nm)} {d['now']}× today, {ordn(d['pct'])} percentile; median {d['p50']}×</title></g>")
        body.append(f"<g><circle cx='{sx(m['pct']):.1f}' cy='{y}' r='6' class='now {'now-bot' if m['pct'] <= 33 else ''}'/><title>Median of the three: {ordn(m['pct'])} percentile</title></g>")
        body.append(f"<text x='{x0 + w + 110}' y='{y + 5}' class='val {'acc' if m['pct'] <= 33 else ''}' text-anchor='end'>{ordn(m['pct'])}</text>")
        if m.get('trigger') and m.get('price'):
            body.append(f"<text x='{x0 + w + 250}' y='{y + 5}' class='val' text-anchor='end'>{money(m['trigger'], m.get('cur'))} ({(m['trigger'] / m['price'] - 1) * 100:+.0f}%)</text>")
    body.append('</svg>')
    return ''.join(body)

def trend_html(m, small=False):
    """EV/EBITDA change lines; the P/E split sits in the hover text."""
    out = ''
    one = m.get('one') or {}
    one_txt = (f" Last 12 months: EV/EBITDA {one['chg'] * 100:+.0f}% (EV {one['evChg'] * 100:+.0f}%, EBITDA {one['ebitdaChg'] * 100:+.0f}%)" + (f"; P/E {one['peChg'] * 100:+.0f}% (price {one['priceChg'] * 100:+.0f}%, EPS {one['epsChg'] * 100:+.0f}%)." if 'peChg' in one else '.')) if 'chg' in one else ''
    for j, r in enumerate(m.get('trends') or []):
        ex = one_txt if j == 0 else ''
        if 'chg' not in r:
            out += f"<div class='trend t-na' title='{E(r.get('na', '') + ex)}'>{E(r['label'])}: <span class='muted'>n/a, {E(r.get('short') or r.get('na', ''))}</span></div>"; continue
        arrow = {'falling': '↓', 'rising': '↑', 'steady': '→'}[r['dir']]
        tip = (f"From {r['date']}: EV/EBITDA {r['multY']}× → {r['mult']}× today ({r['chg'] * 100:+.0f}%) = enterprise value {r['evChg'] * 100:+.0f}% and EBITDA {r['ebitdaChg'] * 100:+.0f}%: "
               f"(1 {r['evChg']:+.3f}) ÷ (1 {r['ebitdaChg']:+.3f}) − 1. "
               + (f"P/E {r['peY']}× → today ({r['peChg'] * 100:+.0f}%) = price {r['priceChg'] * 100:+.0f}% and EPS {r['epsChg'] * 100:+.0f}%. " if 'peChg' in r else (r.get('peNa', '') + '. ' if r.get('peNa') else ''))
               + (r.get('why', '') + '. ' if r.get('why') else '') + "Source: normalized source data (see source_ledger.json) daily EV/EBITDA, enterprise value, P/E and share price." + ex)
        out += (f"<div class='trend t-{r['dir']}' title='{E(tip)}'>{arrow} {E(r['label'])}: EV/EBITDA {r['chg'] * 100:+.0f}% "
                f"<span class='muted'>(EV {r['evChg'] * 100:+.0f}%, EBITDA {r['ebitdaChg'] * 100:+.0f}%)</span></div>")
    return out

DIRW = {'cheaper': ('↓ Getting cheaper', 'dir dir-cheap'), 'dearer': ('↑ Getting dearer', 'dir dir-dear'), 'steady': ('→ Steady', 'dir dir-steady')}   # green / red / grey chips, same colours as the lights
def level_html(m):
    """Direction word plus today's multiples against their own median over 1, 3, 5, 10 years; single-day splits in the hover text."""
    L = m.get('level') or {}
    if not L: return ''
    one = L.get('1') or {}
    tip = []
    for n in ('1', '3', '5', '10'):
        x = L.get(n)
        if x: tip.append(f"{n}-yr: " + ', '.join(f"{MKN[k]} median {v['med']}× ({v['dev'] * 100:+.0f}%)" for k, v in x['per'].items()) + (f" — only {x['years']} clean years" if x['short'] else ''))
    if one.get('ago'): tip.append('A year ago: ' + ', '.join(f"{MKN[k]} {v['then']}× on {v['date']} ({v['chg'] * 100:+.0f}%)" for k, v in one['ago'].items()))
    t1 = m.get('one') or {}
    if 'peChg' in t1: tip.append(f"Last 12 months, single days: P/E {t1['peChg'] * 100:+.0f}% = price {t1['priceChg'] * 100:+.0f}% and EPS {t1['epsChg'] * 100:+.0f}%")
    if 'chg' in t1: tip.append(f"EV/EBITDA {t1['chg'] * 100:+.0f}% = enterprise value {t1['evChg'] * 100:+.0f}% and EBITDA {t1['ebitdaChg'] * 100:+.0f}%")
    tip.append('Each figure is the median across P/E, EV/EBIT and EV/EBITDA of (today ÷ own median over the period − 1). Getting cheaper = 10% or more below the 1-year median and below a year ago.')
    grp = []   # horizons cut to the same clean window collapse into one cell ("3–10 yr (2.5y) −2%")
    for n in ('1', '3', '5', '10'):
        if n not in L: continue
        if grp and L[n]['short'] and L[grp[-1][-1]]['short'] and L[n]['years'] == L[grp[-1][-1]]['years']: grp[-1].append(n)
        else: grp.append([n])
    cells = ' · '.join((f"{g[0]}–{g[-1]} yr" if len(g) > 1 else f"{g[0]} yr") + (f" ({L[g[0]]['years']:g}y)" if L[g[0]]['short'] else '') + f" {L[g[0]]['dev'] * 100:+.0f}%" for g in grp)
    dw = DIRW.get(m.get('direction'))
    head = f"<div class='trend'><span class='{dw[1]}'>{dw[0]}</span></div>" if dw else "<div class='trend t-na'><span class='muted'>Direction n/a (under 1 clean year)</span></div>"
    return f"<div title='{E(chr(10).join(tip))}'>{head}<div class='lvl'>vs own level: {cells}</div></div>"
MKN = {'pe': 'P/E', 'ebit': 'EV/EBIT', 'ebitda': 'EV/EBITDA'}

def mult_line(m):
    return ' · '.join(f"<span title='{E(nm)} {m['metrics'][k]['now']}× today; median {m['metrics'][k]['p50']}×'>{E(nm)} {ordn(m['metrics'][k]['pct'])}</span>" if m['metrics'][k]['pct'] is not None
                      else f"<span title='{E(m['metrics'][k]['why'])}'>{E(nm)} n/a</span>" for k, nm, _ in MK)

def mult_table(c):
    m = c['mult']; cur = m.get('cur')
    rows = ''.join(f"<tr><td>{E(nm)}</td><td class='num'>{'–' if d['now'] is None else str(d['now']) + '×'}</td><td class='num'>{'–' if d['p50'] is None else str(d['p50']) + '×'}</td>"
                   f"<td class='num'>{ordn(d['pct']) if d['pct'] is not None else '–'}</td><td class='num'>{money(d.get('implied'), cur) if d.get('implied') else '–'}</td><td>{E(d['why'] or d.get('note') or '')}</td></tr>"
                   for k, nm, _ in MK for d in [m['metrics'][k]])
    head = (f"Median {ordn(m['pct'])} percentile · research line {money(m['trigger'], cur)} vs price {money(m['price'], cur)}" if m['band'] else f"历史估值分位不可用：{m['why']}")
    return (f"<div class='pel'>{E(head)}</div><table class='mt mx'><thead><tr><th>Multiple</th><th>Today</th><th>Own median</th><th>Percentile</th><th>Price at its median</th><th>Note</th></tr></thead><tbody>{rows}</tbody></table>"
            f"<p class='cap'>Window from {E(m['window'])} ({E(m['windowWhy'])}). Research line = middle of the three share prices at which each multiple would sit at its own median "
            f"(enterprise value moves one for one with market value; net debt held at today's level). EV/EBIT and EV/EBITDA: normalized source data (see source_ledger.json) daily, trailing operating profit and EBITDA. Not a valuation.</p>"
            f"<h5>Against its own level</h5>{level_html(m)}<h5>EV/EBITDA change from single days</h5><div class='trends'>{trend_html(m)}</div>")

# ---------------- P/E range strip (all names, each row on its own scale)
def strip_row(t, y, w=560, x0=230):
    p = D[t]['pe']
    if p['band'] is None:
        why = p.get('why') or ('当前EPS缺项' if p['now'] is None else '利润分母非正' if p['now'] <= 0 else '历史分位不足')
        return (f"<a href='#{t}' data-open='{t}'><text x='0' y='{y + 5}' class='lbl'>{E(D[t]['name'])}</text></a>"
                f"<text x='{x0}' y='{y + 5}' class='muted'>Not meaningful: {why}</text>")
    lo, hi_true = p['p10'], p['p90']
    cap_hi = max(p['p67'] * 1.8, p['now'] * 1.1)
    hi = min(hi_true, cap_hi)
    span_lo = min(lo, p['now']) * 0.97; span_hi = max(hi, p['now']) * 1.03
    sx = lambda v: x0 + (v - span_lo) / (span_hi - span_lo) * w
    seg = lambda a, b, cls: f"<rect x='{sx(a):.1f}' y='{y - 7}' width='{max(sx(b) - sx(a), 0):.1f}' height='14' class='{cls}' rx='2'/>"
    band = p['band']
    win = ('since ' + p['from_'][:7] if _later(p['from_'], PE_DEFAULT_FROM) else '10 yrs') + (' · short' if p['short'] else '')
    lx = min(sx(lo), sx(p['now'])) - 10
    out = [f"<a href='#{t}' data-open='{t}'><text x='0' y='{y}' class='lbl'>{E(D[t]['name'])}</text></a>",
           f"<text x='0' y='{y + 15}' class='muted'>{win}</text>",
           seg(lo, p['p33'], 'b-bot'), seg(p['p33'], p['p67'], 'b-mid'), seg(p['p67'], hi, 'b-top'),
           f"<line x1='{sx(p['p50']):.1f}' x2='{sx(p['p50']):.1f}' y1='{y - 9}' y2='{y + 9}' class='med'/>",
           f"<text x='{lx:.1f}' y='{y + 4}' class='tick' text-anchor='end'>{lo:g}×</text>",
           f"<text x='{sx(hi) + 6:.1f}' y='{y + 4}' class='tick'>{'→ ' if hi_true > hi else ''}{hi_true:g}×</text>",
           f"<g><circle cx='{sx(p['now']):.1f}' cy='{y}' r='6' class='now {'now-bot' if p['pct'] <= 33 else ''}'><title>{E(D[t]['name'])}: today {p['now']}× trailing P/E, {ordn(p['pct'])} percentile of its own range. 10th–90th percentile {lo}×–{hi_true}×, median {p['p50']}×.</title></circle></g>",
           f"<text x='{x0 + w + 130}' y='{y + 5}' class='val' text-anchor='end'>{p['now']:.1f}×</text>",
           f"<text x='{x0 + w + 190}' y='{y + 5}' class='val {'acc' if p['pct'] <= 33 else ''}' text-anchor='end'>{ordn(p['pct'])}</text>"]
    return ''.join(out)

def strip_chart():
    rows = sorted([t for t in ORDER if D[t]['pe']['band']], key=lambda t: D[t]['pe']['pct']) + [t for t in ORDER if not D[t]['pe']['band']]
    h = 70 + 40 * len(rows)
    body = [f"<svg viewBox='0 0 1010 {h}' role='img' aria-label='Today\\'s trailing P/E against each stock\\'s own range'>",
            "<text x='230' y='20' class='muted'>Bar = 10th to 90th percentile of the stock's own trailing P/E · shading = thirds · tick = median · dot = today</text>",
            "<text x='920' y='44' class='hdr' text-anchor='end'>Today</text><text x='980' y='44' class='hdr' text-anchor='end'>Pctile</text>"]
    for i, t in enumerate(rows):
        body.append(strip_row(t, 70 + 40 * i))
    body.append('</svg>')
    return ''.join(body)

# ---------------- P/E history chart per company
def pe_chart(t):
    p = D[t]['pe']
    pts = []
    for s in (p.get('wk') or '').split(','):
        if '|' not in s: continue
        d, v = s.split('|')
        pts.append((d, float(v) if v else None))
    if not [v for _, v in pts if v is not None]:
        why = (D[t].get('mult') or {}).get('why') or 'no P/E history in the window'
        return "<p class='muted'>No P/E history to chart in the window.</p>", why
    W, H, L, R, T, B = 640, 230, 48, 150, 14, 28
    vals = [v for _, v in pts if v is not None]
    meaningful = p['band'] is not None
    if not vals:
        return "<p class='muted'>No positive trailing P/E in the window.</p>", f"Daily trailing GAAP P/E from normalized source data (see source_ledger.json) since {p['from_']}; the company has been loss-making throughout."
    if meaningful:
        ymax = max(p['p90'] * 1.35, p['now'] * 1.15); ymin = max(0, min(p['p10'] * 0.7, p['now'] * 0.85))
    else:
        sv = sorted(vals); ymax = sv[int(len(sv) * .9)] * 1.3; ymin = 0
    clipped = max(vals) > ymax
    n = len(pts)
    sx = lambda i: L + i / (n - 1) * (W - L - R)
    sy = lambda v: T + (1 - (min(v, ymax) - ymin) / (ymax - ymin)) * (H - T - B)
    out = [f"<svg viewBox='0 0 {W} {H}' role='img' aria-label='{E(D[t]['name'])} trailing P/E history against its own thirds'>"]
    n = max(n, 2)
    if meaningful:
        out.append(f"<rect x='{L}' y='{sy(p['p33']):.1f}' width='{W - L - R}' height='{sy(ymin) - sy(p['p33']):.1f}' class='z-bot'/>")
        out.append(f"<rect x='{L}' y='{sy(p['p67']):.1f}' width='{W - L - R}' height='{sy(p['p33']) - sy(p['p67']):.1f}' class='z-mid'/>")
        hb, hm = sy(ymin) - sy(p['p33']), sy(p['p33']) - sy(p['p67'])
        if hb >= 30: out.append(f"<text x='{W - R + 8}' y='{(sy(p['p33']) + sy(ymin)) / 2 + 4:.1f}' class='zl acc'>Bottom third</text><text x='{W - R + 8}' y='{(sy(p['p33']) + sy(ymin)) / 2 + 18:.1f}' class='zl'>below {p['p33']:g}×</text>")
        else: out.append(f"<text x='{W - R + 8}' y='{sy(ymin) - 2:.1f}' class='zl acc'>Bottom third &lt; {p['p33']:g}×</text>")
        if hm >= 30: out.append(f"<text x='{W - R + 8}' y='{(sy(p['p67']) + sy(p['p33'])) / 2 + 4:.1f}' class='zl'>Middle third</text><text x='{W - R + 8}' y='{(sy(p['p67']) + sy(p['p33'])) / 2 + 18:.1f}' class='zl'>{p['p33']:g}–{p['p67']:g}×</text>")
        out.append(f"<text x='{W - R + 8}' y='{max(sy(p['p67']) - 10, T + 12):.1f}' class='zl'>Top third, above {p['p67']:g}×</text>")
        out.append(f"<line x1='{L}' x2='{W - R}' y1='{sy(p['p50']):.1f}' y2='{sy(p['p50']):.1f}' class='medline'/>")
    # axis ticks
    import math
    step = next((c for c in (5, 10, 20, 25, 50, 100, 200, 250, 500, 1000) if (ymax - ymin) / c <= 8), 2000)
    v = math.ceil(ymin / step) * step
    while v <= ymax:
        out.append(f"<line x1='{L}' x2='{W - R}' y1='{sy(v):.1f}' y2='{sy(v):.1f}' class='grid'/><text x='{L - 6}' y='{sy(v) + 4:.1f}' class='tick' text-anchor='end'>{v:g}×</text>")
        v += step
    years = []
    for i, (d, _) in enumerate(pts):
        y = d[:4]
        if d[5:7] == '01' and (not years or years[-1][1] != y):
            years.append((i, y))
    if len(years) > 7: years = years[::2]
    for i, y in years:
        out.append(f"<text x='{sx(i):.1f}' y='{H - 8}' class='tick' text-anchor='middle'>{y}</text>")
    # line, broken at nulls
    seg, segs = [], []
    for i, (d, v) in enumerate(pts):
        if v is None:
            if seg: segs.append(seg); seg = []
        else:
            seg.append(f"{sx(i):.1f},{sy(v):.1f}")
    if seg: segs.append(seg)
    for s in segs:
        out.append(f"<polyline points='{' '.join(s)}' class='peline'/>")
    if meaningful:
        nx, ny = sx(n - 1), sy(p['now'])
        out.append(f"<circle cx='{nx:.1f}' cy='{ny:.1f}' r='5' class='now now-bot'><title>Today {p['now']}×, {ordn(p['pct'])} percentile</title></circle>")
        out.append(f"<text x='{L + 4}' y='{sy(p['p50']) - 5:.1f}' class='tick'>median {p['p50']:g}×</text>")
    out.append('</svg>')
    cap = f"Daily trailing GAAP P/E from normalized source data (see source_ledger.json), {p['from_']} to {p['to']} ({p['years']} years), sampled weekly." + (f" Thirds and median computed on the days with a positive P/E; the dot is today." if meaningful else '')
    if clipped: cap += f" Values above {ymax:.0f}× are cut at the top edge (high was {max(vals):g}×)."
    if not meaningful: cap += ' No range is drawn: ' + (p.get('why') or 'current input/history unavailable') + '; chart gaps can represent missing data or nonpositive profit, as distinguished in the coverage table.'
    return ''.join(out), cap

# ---------------- company section
HALF = '<svg class=\'half\' viewBox=\'0 0 14 14\' aria-hidden=\'true\'><circle cx=\'7\' cy=\'7\' r=\'5.6\' fill=\'none\' stroke=\'currentColor\' stroke-width=\'1.8\'/><path d=\'M7 1.4 A5.6 5.6 0 0 0 7 12.6 Z\' fill=\'currentColor\'/></svg>'
SYMB = {'g': '✓', 'y': HALF, 'r': '✗', 'na': '–'}
LWORD = {'g': 'green', 'y': 'yellow', 'r': 'red', 'na': 'no light'}
def mlight(code_or_none, s, lt=None):
    """Light for one measure: symbol in a coloured chip; the 1-5 score is in the tooltip and in the arithmetic."""
    lt = lt or ('na' if s is None else 'g' if s >= 4 else 'y' if s >= 3 else 'r')
    tip = (f"{code_or_none}: " if code_or_none else '') + (f"score {fnum(s)} of 5 → {LWORD[lt]}" if s is not None else 'not scored')
    return f"<span class='lt lt-{lt}' title='{E(tip)}'>{SYMB[lt]}</span>"
from decimal import Decimal as _D, ROUND_HALF_UP as _HU
def h1(x): return str(_D(str(x)).quantize(_D('0.1'), rounding=_HU))
def flight(f, name='', num=True):
    """Light for a factor. Green / yellow / red from the average of its measures.
    When a measure is missing and the answer depends on it (the range spans two colours), the light is a grey '?'.
    num=False (summary table, company headers): symbol only, no number."""
    if f is None or f.get('point') is None:
        return f"<span class='lt lt-na{' wide' if num else ' big'}' title='{E(name)}: not scored'>–{' n/a' if num else ''}</span>"
    if f['light'] == 'range':
        a, b = f['lightLo'], f['lightHi']
        tip = f"{name}: could be {LWORD[a]} or {LWORD[b]} ({h1(f['lo'])}–{h1(f['hi'])}). Missing: " + '; '.join((g if len(g) <= 230 else g[:230].rsplit(' ', 1)[0] + ' … (full reason in the company section)') for g in (f.get('gaps') or ['a measure'])) + '.'
        return f"<span class='lt lt-q{' wide' if num else ' big'}' title='{E(tip)}'>?{(' ' + h1(f['lo']) + '–' + h1(f['hi'])) if num else ''}</span>"
    rng = f" ({h1(f['lo'])}–{h1(f['hi'])})" if f['lo'] != f['hi'] else ''
    tip = f"{name}: {f['point']}{rng} → {LWORD[f['light']]}"
    return f"<span class='lt lt-{f['light']}{' wide' if num else ' big'}' title='{E(tip)}'>{SYMB[f['light']]}{(' ' + format(f['point'], '.1f')) if num else ''}</span>"
def minis(c, codes):
    return "<span class='minis'>" + ''.join(mlight(k, c['scores'].get(k)) for k in codes) + "</span>"

def measure_rows(m):
    ins = ''.join((f"<div class='kv'><span>{E(a)}</span><b>{E(b)}</b></div>" if len(str(b)) <= 34 else f"<div class='kv kvl'><span>{E(a)}</span><b>{E(b)}</b></div>") for a, b in m.get('inputs') or [])
    segs = m.get('segments') or []
    if segs:
        ins += "<div class='segs'>" + ''.join(f"<div class='kv'><span>{E(s['segment'])} (op. profit {E(s['op_profit'])})</span><b>{E(fnum(s['score']))}</b></div>" for s in segs) + "</div>"
    note = f"<div class='note'>{E(m['note'])}</div>" if m.get('note') else ''
    det = ''
    if m.get('evidence'):
        det = f"<details class='ev'><summary>Sources</summary><ul>{evlist(m['evidence'])}</ul></details>"
    return (f"<tr><td class='mcode'><b>{E(m['code'])}</b><div>{E(m['name'])}</div><span class='kind'>{E(m['kind'])}</span></td>"
            f"<td>{ins or '<span class=muted>–</span>'}</td>"
            f"<td><div class='calc'>{E(m['calc'])}</div>{note}<div class='rule'>Rule: {E(m['rule'])}</div>{det}</td>"
            f"<td class='scol'>{mlight(m['code'], m['score'], m.get('light') if m['factor'] == 'Risk' else None) if m['factor'] != 'Risk' else ('<span class=\'lt lt-r\' title=\'gate triggered\'>✗</span>' if m.get('light') == 'r' else '<span class=\'lt lt-g\' title=\'gate not triggered\'>✓</span>')}</td></tr>")

def verdict_cls(v):
    return 'v-now' if v.startswith('Research now') else 'v-watch' if v.startswith('Watch') else 'v-out' if v.startswith(('Removed', 'Fails', 'Manual')) else 'v-neutral'

def link(src, url):
    return f"<a href='{E(url)}' target='_blank' rel='noopener'>{E(src or 'source')}</a>" if str(url or '').startswith('http') else E(src or '')

def evlist(items):
    return ''.join(f"<li>{E(e.get('fact', ''))} <span class='src'>— {link(e.get('source', ''), e.get('url', ''))}</span></li>" for e in items or [])

def _s(x):
    if isinstance(x, dict):
        return ' · '.join(str(x[k]) for k in ('date', 'filing_date', 'fy', 'number', 'name', 'item', 'what', 'subject', 'description', 'reason', 'detail', 'type', 'status') if x.get(k))
    return str(x)

def redflag_block(c):
    rf = c.get('redflag_check') or {}
    rows = []
    if c.get('sec', True):
        a = rf.get('item_402_recent') or rf.get('item_402_since_2023_10_20') or []
        rows.append(('8-K Item 4.02 non-reliance, last 3 years', ('; '.join(_s(x) for x in a) or 'None found'), rf.get('item_402_how_checked', '')))
        ic = rf.get('icfr') or {}
        ev = (ic.get('evidence') or [{}])[0] if ic.get('evidence') else {}
        rows.append((f"Internal control at FY-end {ic.get('fiscal_year_end', '')}", f"Management: {ic.get('management_conclusion', '–')}; auditor: {ic.get('auditor_opinion', '–')}" + (f"; material weaknesses: {'; '.join(map(str, ic.get('material_weaknesses')))}" if ic.get('material_weaknesses') else ''),
                     link(ev.get('source', ''), ev.get('url', '')) if ev else ''))
        a = rf.get('aaer_recent') or rf.get('aaer_since_2021_10_20') or []
        flagged = any(r['label'] == 'SEC AAER' for r in c['redflags'])
        old_ = [x for x in a if isinstance(x, dict) and x.get('conduct_end')] if not flagged else []
        res = '; '.join(_s(x) for x in a) or 'None found'
        if old_: res = 'Not a red flag: the misconduct ended ' + ', '.join(str(x['conduct_end'])[:7] for x in old_) + ', more than 5 years ago (the horizon counts from the conduct, not the release date). Information only: ' + res
        rows.append(('SEC AAER, misconduct in the last 5 years', res, rf.get('aaer_how_checked', '')))
        o = rf.get('other_sec_enforcement') or []
        if o: rows.append(('Other SEC enforcement (not scored)', '; '.join(_s(x) for x in o), ''))
    else:
        ns = rf.get('non_sec') or {}
        rows.append(('SEC checks', 'Not applicable: not an SEC registrant', ''))
        _er = ns.get('error_restatement') or []   # v4.7.1: re-presentations the company does not call an error are listed as information, not as a restatement
        _err = [x for x in _er if not (isinstance(x, dict) and x.get('is_error_per_company') is False)]; _rep = [x for x in _er if x not in _err]
        rows.append(('Restatement to correct an error, last 3 years', ('; '.join(_s(x) for x in _err) if _err else 'None found') + (' (re-presented, not called an error by the company: ' + '; '.join(_s(x) for x in _rep) + ')' if _rep else ''), ''))
        rows.append(('Modified audit opinion on the latest accounts', _s(ns.get('modified_audit_opinion')) if ns.get('modified_audit_opinion') not in (None, False) else 'No', ''))
        rows.append(('Accounting regulator finding, last 5 years', '; '.join(_s(x) for x in ns.get('regulator_findings') or []) or 'None found', ''))
    body = ''.join(f"<tr><td>{E(a)}</td><td>{E(b)}</td><td class='src'>{s if s.startswith('<a') else E(s)}</td></tr>" for a, b, s in rows)
    past = [f for f in c.get('flags') or [] if f.startswith('Past SEC enforcement')]
    head = ("<b class='bad'>Red flag found: " + E('; '.join(r['label'] for r in c['redflags'])) + ' → removed</b>') if c['redflags'] else ("<b>No red flag found · highlighted: past SEC enforcement outside the horizon</b>" if past else "<b>No red flag found</b>")
    return f"<h4>Accounting red flags</h4><p class='note'>{head}</p><table class='mt small'><thead><tr><th>Check</th><th>Result</th><th>How checked / source</th></tr></thead><tbody>{body}</tbody></table>"

def info_block(c):
    i = c.get('info') or {}
    au = '; '.join(_s(x) for x in i.get('auditor_changes') or []) or 'None'
    cf = '; '.join(_s(x) for x in i.get('cfo_departures') or []) or 'None'
    dc = i.get('dual_class') or {}
    dcs = ('Yes: ' + str(dc.get('detail', ''))) if dc.get('exists') else ('No' + (f" ({dc.get('detail')})" if dc.get('detail') else ''))
    return (f"<h4>Shown for information (not scored)</h4><table class='mt small'><tbody><tr><td>Auditor changes, last 5 years</td><td>{E(au)}</td></tr>"
            f"<tr><td>CFO departures, last 5 years</td><td>{E(cf)}</td></tr><tr><td>Share classes with different votes</td><td>{E(dcs)}</td></tr></tbody></table>")

def perimeter_block(c):
    w = c['window']; per = c.get('perimeter') or {}
    fl = ''.join(f"<tr><td>FY{f['fy']}</td><td>{E(f['text'])}</td><td>{E((f.get('cause') or 'not explained').upper() if (f.get('cause') or '') in ('deal', 'no deal') else (f.get('cause') or 'not explained'))}</td><td>{E(f.get('why', ''))} <span class='src'>{link(f.get('src', ''), f.get('url', ''))}</span></td></tr>" for f in c['autoflags'])
    ev = ''.join(f"<li>{E(d.get('date', ''))} · {E(d.get('type', ''))} · {E(d.get('name', ''))}" + (f" · {d.get('revenue_effect_pct')}% of revenue" if d.get('revenue_effect_pct') not in (None, '') else '') + f" <span class='src'>{link(d.get('source', ''), d.get('url', ''))}</span></li>" for d in (per.get('events') or []) if isinstance(d, dict))
    ay = ''.join(f"<li>{E(_s(d))}" + (f" · {d.get('revenue_effect_pct')}% of revenue" if isinstance(d, dict) and d.get('revenue_effect_pct') not in (None, '') else '') + "</li>" for d in per.get('after_year_end') or [])
    rep = ''.join(f"<li>{E(x)}</li>" for x in c.get('repairs') or [])
    txt = (f"B1, B2 and B4 use FY{w.get('first') or w['start']}–FY{w['L']} ({w['n']} years)" + (', the current perimeter' if w['perim'] else ', the normal 10-year window') + '. '
           + (f"B3 uses FY{w['growth'][0]}–FY{w['growth'][1]}." if w.get('growth') else 'B3 has no growth window.') + (' ' + c['perimeter_note'] if c.get('perimeter_note') else ''))
    out = f"<h4>Perimeter and data</h4><p class='note'>{E(txt)}</p>"
    if fl: out += f"<table class='mt small'><thead><tr><th>Year</th><th>Automatic flag</th><th>Cause</th><th>Explanation (fact collector)</th></tr></thead><tbody>{fl}</tbody></table>"
    if ev: out += f"<details class='ev'><summary>Deals since FY{w['L'] - 10}</summary><ul>{ev}</ul></details>"
    if ay: out += f"<p class='note'>After the latest year-end:</p><ul class='small'>{ay}</ul>"
    if rep: out += f"<details class='ev'><summary>Data repaired from filings</summary><ul>{rep}</ul></details>"
    if c.get('notes'): out += f"<p class='note'>{E(c['notes'])}</p>"
    return out

def peer_block(c):
    p = c.get('peers')
    if not p: return ''
    g = p['group']
    pc = lambda v: '–' if v is None else ('>100%' if v == 'inf' else f"{v * 100:.1f}%")
    rows = ''.join(f"<tr{' class=run' if r.get('self') else ''}><td>{'<b>' + E(r['t']) + '</b>' if r.get('self') else E(r['t'])}</td><td>{E(r['name'])}{' (this company)' if r.get('self') else ''}</td><td>{E(r['tag'])}</td><td>{E(r['window'])}</td><td class='num'>{pc(r['roic'])}</td><td class='num'>{pc(r['revG'])}</td><td>{E(r['roicWhy'])}{'; ' if r['roicWhy'] and r['notes'] else ''}{E(r['notes'])}</td></tr>" for r in p['table'])
    yrs = ', '.join(f"FY{y}: {v * 100:+.1f}%" for y, v in sorted(p['byYear'].items()))
    thin = (f" Thin group: {p.get('nVal')} companies with an I1 value (under {6}); one company's data moves the median, so read the table." if p.get('thin') else '')
    return (f"<details class='ev'><summary>Group ({E(p.get('count') or str(p['n']) + ' companies')}) and how it was chosen</summary><p class='note'>Tag: {E(g['label'])}. {E(g['why'])}. "
            f"Every company in the tag is scored against the same group, this company included, so they all get the same Industry light.{E(thin)} "
            f"Group companies use normalized inputs (see source_ledger.json) plus filed settlement liabilities, with no other repairs from filings; {p['noAm']} of {p['n']} have no amortization of acquired intangibles in the data, so their returns are understated.</p>"
            f"<p class='note'>Median revenue change by year: {E(yrs.replace('-0.0%', '0.0%'))}</p>"
            f"<table class='mt small'><thead><tr><th>Ticker</th><th>Company</th><th>Tag</th><th>Window</th><th>ROIC incl. goodwill (median)</th><th>Revenue growth</th><th>Notes</th></tr></thead><tbody>{rows}</tbody></table></details>")

BLK = {'Business': 'bu', 'Industry': 'in', 'Management': 'ma', 'Risk': 'rk'}
def blk(kind, html):
    return f"<section class='blk blk-{kind}'>{html}</section>" if html else ''

def company(t, rank):
    c = D[t]
    chart, cap = pe_chart(t)
    facs = ''
    FK = {'Business': 'business', 'Industry': 'industry', 'Management': 'management'}
    for f, head in (('Business', 'Business'), ('Industry', 'Industry'), ('Management', 'Management'), ('Risk', 'Financial risk gate')):
        ms = [m for m in c['measures'] if m['factor'] == f]
        if not ms: continue
        facs += blk(BLK[f], f"<h4>{head} " + (flight(c[FK[f]], f) if f in FK else '') + "</h4>" + (ceo_note(c) if f == 'Management' else '') + ""
                 f"<table class='mt'><thead><tr><th>Measure</th><th>Inputs</th><th>How it is set</th><th>Light</th></tr></thead><tbody>{''.join(measure_rows(m) for m in ms)}</tbody></table>"
                 + (f"<div class='favg'>{f} = {E(c[FK[f]]['calc'])}</div>" if f in FK else '')
                 + (f"<div class='favg'><b>Missing:</b> {E('; '.join(c[FK[f]]['gaps']))}</div>" if f in FK and c[FK[f]].get('gaps') else '')
                 + (peer_block(c) if f == 'Industry' else ''))
    steps = ''.join(f"<li><span>{E(a)}</span><b>{E(b)}</b></li>" for a, b in c['steps'])
    p = c['pe']
    fw = f"{p['fwd']:.1f}×" if p['fwd'] else 'not available'
    mxt = mult_table(c)
    pe_line = (f"Today {p['now']}× trailing ({ordn(p['pct'])} percentile of its own history) · forward {fw} · price {money(p['price'], p.get('cur'))}" if p['band'] else (f"Trailing {p['now']}× (not meaningful)" if p.get('now') is not None else 'Trailing P/E not meaningful') + f" · forward {fw} · price {money(p['price'], p.get('cur'))}")
    extra = ''.join(f"<p class='note'>{E(x)}</p>" for x in TXT.get('notes', {}).get(t, []))
    fl = ''.join(f"<li{' class=warn' if x.startswith('Past SEC') else ''}>{E(x)}</li>" for x in c['flags'])
    fl = f"<h4>Flags</h4><ul class='flags'>{fl}</ul>" if fl else ''
    pill = (c.get('result') or {}).get('cat') or ''
    return (f"<details class='co' id='{t}'><summary><span class='rk'>{rank}</span><span class='cn'>{E(c['name'])} <small>{t} · {E(c['group'])}</small></span>"
            f"<span class='fx'>Business {flight(c['business'], 'Business', False)} Industry {flight(c['industry'], 'Industry', False)} Management {flight(c['management'], 'Management', False)} {ceo_tag(c, 'sm')}</span>"
            f"<span class='res {CATCLS.get(pill, '')}'>{E(pill)}</span></summary>"
            f"<div class='cobody'><section class='blk blk-ov'><div class='top2'><div><h4>Summary</h4><ol class='steps'>{steps}</ol>{fl}</div>"
            f"<div><h4>Multiples against their own history</h4>{mxt}<h4>P/E history</h4><div class='pel'>{E(pe_line)}</div>{chart}<p class='cap'>{E(cap)}</p>{extra}</div></div></section>"
            f"{blk('rf', redflag_block(c))}{facs}{blk('nf', info_block(c))}{blk('nf', perimeter_block(c))}</div></details>")

# ---------------- overview table
def gcls(g):
    if g is None: return 'gna'
    return 'g4' if g >= .12 else 'g3' if g >= .08 else 'g2' if g >= .05 else 'g1' if g >= .02 else 'g0'

def bus_txt(b):
    if b['point'] is None: return '–'
    return f"{b['point']:.1f}" + (f" <small class='muted'>({b['lo']:.2f}–{b['hi']:.2f})</small>" if b['lo'] != b['hi'] else '')

def quad_map():
    """Where each company lands: rows = Business light (good / average / weak), columns = median multiple percentile in the stock's own history,
    with the 50th as the divider between cheaper and dearer than usual and thin lines at the 33rd and 67th. Each box is titled with its action.
    A narrow right column holds companies without a meaningful multiple. A fourth, hatched band below the Weak row ("Not judged yet") holds the names
    with no Business row: accounting red flags, too-early names (fewer than 3 clean years after a deal) and open Business lights (a missing measure
    decides the colour). They sit at their real multiple percentile, with the reason under the ticker (red for a red flag, the revisit year for too early)."""
    W, LM, RM, NAW, GAP, PAD = 1000, 112, 4, 112, 10, 18
    PW = W - LM - RM - NAW - GAP
    X = lambda p: LM + PAD + p / 100 * (PW - 2 * PAD)
    XNA0 = LM + PW + GAP
    ROWS = [('g', 'Good'), ('y', 'Average'), ('r', 'Weak'), ('n', 'Not judged')]
    pts = {r: [] for r, _ in ROWS}; nam = {r: [] for r, _ in ROWS}
    for t in ORDER:
        c = D[t]; r = c['result']; k = r.get('kind'); bl = c['business']['light']; m = c['mult']
        row = 'n' if (k in ('redflag', 'early') or bl not in ('g', 'y', 'r')) else bl
        (pts if m.get('band') and m.get('pct') is not None else nam)[row].append(t)
    if not (pts['n'] or nam['n']): ROWS = ROWS[:3]
    LANE, TOPP = 24, 34
    NROW = set(pts['n'] + nam['n'])
    RF_PLAIN = {'material weakness': 'material weakness in controls', 'SEC enforcement (AAER)': 'SEC accounting case (AAER)',
                'restatement (8-K 4.02)': 'restated accounts (8-K 4.02)', 'error restatement': 'restated accounts',
                'modified audit opinion': 'auditor qualified the accounts'}
    def reasons(t):
        """Short reasons under the ticker, in plain words (user, 2026-10-23: see the issue at first glance, not only by hover).
        (text, css) in order of weight: red = accounting red flag; amber = past issue outside the horizon, financial risk;
        grey = too early, Business light open, business changing, new CEO (under 24 months), multiples disagree. At most 3 lines."""
        import re as _re
        c = D[t]; r = c['result']; k = r.get('kind'); l0 = r['lines'][0]; out = []; fl = c.get('flags') or []
        if t in NROW:
            if k == 'redflag':
                f = l0.split(':', 1)[1].split(';')[0].strip(); out.append(('red flag: ' + RF_PLAIN.get(f, f), 'q-whyr'))
            elif k == 'early':
                rv = next((x for x in r['lines'] if x.startswith('Revisit after')), '')
                out.append(('too early · revisit ' + rv.replace('Revisit after ', '').replace(' results', ''), 'q-why'))
            else:
                out.append(('Business light open', 'q-why'))
        for f in fl:
            if f.startswith('Past SEC enforcement'):
                m = _re.search(r'misconduct (\d{4})(?:[–-](\d{4}))?', f)
                yrs = (m.group(1) + ('–' + m.group(2)[2:] if m.group(2) and m.group(2) != m.group(1) else '')) if m else ''
                out.append(('past SEC case' + (f' ({yrs})' if yrs else '') + ', not a red flag', 'q-whya'))
        for f in fl:
            if f.startswith('Financial risk'):
                lev = _re.search(r'net debt ÷ EBITDA ([\d.]+)×', f); cov = _re.search(r'interest cover ([\d.]+)×', f)
                parts = ([f'net debt {lev.group(1)}× EBITDA'] if lev and float(lev.group(1)) > 5 else []) + \
                        ([f'interest cover {cov.group(1)}×'] if cov and float(cov.group(1)) < 2 else [])
                out.append(('high debt: ' + ', '.join(parts) if parts else 'financial risk: ' + f.split(': ', 1)[-1], 'q-whya'))
        for f in fl:
            if f.startswith('Business changing'):
                m = _re.search(r'about (\d+)% of revenue', f)
                out.append(('big deal after year-end' + (f' ({m.group(1)}% of revenue)' if m else ''), 'q-why'))
        x = c.get('ceo')
        if x and x.get('tier') == 'new':
            out.append((x['label'].replace('New CEO', 'new CEO'), 'q-why'))
        dz = next((l for l in r['lines'] if l.startswith('Multiples disagree')), '')
        if dz:
            out.append(('multiples disagree: ' + dz.split(':', 1)[1].split(';')[0].strip(), 'q-why'))
        return out
    REAS = {t: reasons(t) for t in ORDER}
    # v4.6.1 (user, 2026-10-23): the notes sit in a closed box around the ticker and open over the map, so they never move another ticker.
    # The band names keep their one reason line under the ticker (the band always had room for it); every other note goes in the box.
    def valuation_reason(t):
        c=D[t]
        if c['mult'].get('band'): return None
        qs=(c.get('valuation_quality') or {}).get('metrics') or {}
        states={q['state'] for q in qs.values()}
        if states=={'nonpositive_denominator'}: return ('亏损分母','q-why')
        if 'current_gap' in states: return ('当前输入缺项','q-why')
        if 'history_gap' in states: return ('历史资料不足','q-why')
        if states & {'short_history','positive_days_short'}: return ('比较历史不足','q-why')
        if states: return ('正值覆盖不足','q-why')
        return None
    VREAS={t:valuation_reason(t) for t in ORDER}
    BANDR = {t: (VREAS[t] or (REAS[t][0] if t in NROW and REAS[t] else None)) for t in ORDER}
    NOTES = {t: (REAS[t] if VREAS[t] else (REAS[t][1:] if t in NROW and REAS[t] else REAS[t])) for t in ORDER}
    SEV = {t: ('r' if any(c == 'q-whyr' for _, c in REAS[t]) else 'a' if any(c == 'q-whya' for _, c in REAS[t]) else 'g') for t in ORDER}
    CHIP = 24                                    # width of the '▸ n' toggle inside the box
    def tickw(t):
        return len(t) * 7.6 + (18 if D[t]['mult'].get('direction') in ('cheaper', 'dearer') else 0)
    def wid(t):
        w = tickw(t) + (CHIP if NOTES[t] else 0)
        return max(w, len(BANDR[t][0]) * 6.1) if BANDR[t] else w
    LN = {r: LANE + (14 if r == 'n' or any(BANDR[t] for t in nam[r]) else 0) for r, _ in ROWS}
    NOTE_SVG, NOTE_LOW = [], []                  # drawn last, so an open note lies over the map instead of pushing it
    lay, RH = {}, {}
    for r, _ in ROWS:
        lanes = []
        for t in sorted(pts[r], key=lambda t: D[t]['mult']['pct']):
            p = D[t]['mult']['pct']; x = X(p); w = wid(t) + 16; left = 40 < p <= 50 or x + w > LM + PW - 4
            a, b = (x - w, x + 7) if left else (x - 7, x + w)
            for i, l in enumerate(lanes):
                if all(b < q0 or a > q1 for q0, q1 in l): l.append((a, b)); lay[t] = (x, i, left); break
            else: lanes.append([(a, b)]); lay[t] = (x, len(lanes) - 1, left)
        na_lanes = len(nam[r]); ln = LN[r]
        RH[r] = TOPP + max(len(lanes), na_lanes, 1) * ln + 12 + (6 if r == 'n' else 0)
    TOP = 44; y = TOP; RY = {}
    for r, _ in ROWS:
        if r == 'n': y += 14
        RY[r] = y; y += RH[r]
    BOT = y; H = BOT + 28
    s = [f"<svg viewBox='0 0 {W} {H}' class='qmap' role='img' aria-label='Where each company lands: business quality against where its multiples sit in their own history'>"]
    def box(r, x0, x1, cls, title, sub=''):
        s.append(f"<rect x='{x0:.1f}' y='{RY[r]}' width='{x1 - x0:.1f}' height='{RH[r]}' class='{cls}'/>")
        s.append(f"<text x='{x0 + 12:.1f}' y='{RY[r] + 20}'><tspan class='qt {cls}-t'>{title}</tspan>" + (f"<tspan class='qs' dx='8'>{sub}</tspan>" if sub else '') + "</text>")
    L, M, Rr = LM, X(50), LM + PW
    box('g', L, M, 'q-now', 'RESEARCH NOW'); box('g', M, Rr, 'q-low', 'RESEARCH AT LOWER PRICE')
    box('y', L, M, 'q-ql', 'QUICK LOOK', 'below the 33rd'); box('y', M, Rr, 'q-not', 'NOT NOW', 'average, not cheap')
    box('r', L, Rr, 'q-not', 'NOT NOW', 'weak business')
    s.insert(1, "<defs><pattern id='qhatch' width='8' height='8' patternUnits='userSpaceOnUse' patternTransform='rotate(45)'><rect width='8' height='8' class='q-hb'/><line x1='0' y1='0' x2='0' y2='8' class='q-hl'/></pattern></defs>")
    if len(ROWS) == 4: box('n', L, Rr, 'q-np', 'NOT JUDGED YET', 'red flag, too early after a deal, or Business light open · the dot shows only where the multiples sit')
    for p in (33, 67):
        for r, _ in ROWS[:3]:
            s.append(f"<line x1='{X(p):.1f}' x2='{X(p):.1f}' y1='{RY[r] + 28}' y2='{RY[r] + RH[r]}' class='q-tick'/>")
    for r, _ in ROWS:
        s.append(f"<rect x='{XNA0}' y='{RY[r]}' width='{NAW}' height='{RH[r]}' class='q-na'/>")
    s.append(f"<text x='{XNA0 + NAW / 2:.1f}' y='{TOP - 22}' text-anchor='middle' class='q-ax'>历史估值分位</text><text x='{XNA0 + NAW / 2:.1f}' y='{TOP - 8}' text-anchor='middle' class='q-ax'>不可用</text>")
    LBL = {'g': ('Good', 'business'), 'y': ('Average', 'business'), 'r': ('Weak', 'business'), 'n': ('Not judged', 'yet')}
    for r, _ in ROWS:
        yc = RY[r] + RH[r] / 2
        s.append(f"<rect x='2' y='{RY[r] + 6}' width='4' height='{RH[r] - 12}' rx='2' class='q-sw-{r}'/>")
        s.append(f"<text x='{LM - 12}' y='{yc - 2}' text-anchor='end' class='q-rn'>{LBL[r][0]}</text><text x='{LM - 12}' y='{yc + 14}' text-anchor='end' class='q-rn2'>{LBL[r][1]}</text>")
    s.append(f"<text x='{X(25):.1f}' y='{TOP - 12}' text-anchor='middle' class='q-ax'>← cheaper than usual for this stock</text>")
    s.append(f"<text x='{X(75):.1f}' y='{TOP - 12}' text-anchor='middle' class='q-ax'>dearer than usual for this stock →</text>")
    for p, t_, an in ((0, 'lowest in its own history', 'start'), (33, '33rd', 'middle'), (50, 'usual level (50th)', 'middle'), (67, '67th', 'middle'), (100, 'highest', 'end')):
        s.append(f"<text x='{X(p):.1f}' y='{BOT + 17}' text-anchor='{an}' class='q-tk'>{t_}</text>")
    def dot(t, x, yy, left, band=None, narrow=False):
        c = D[t]; cat = c['result']['cat']; m = c['mult']
        cls = {'Research now': 'qd-now', 'Quick look': 'qd-ring', 'Research at lower price': 'qd-ring'}.get(cat, 'qd-not')
        dr = m.get('direction')
        arr = {'cheaper': "<tspan class='q-dc'> ↓</tspan>", 'dearer': "<tspan class='q-dd'> ↑</tspan>"}.get(dr, '')
        pos = f"{ordn(m['pct'])} percentile of its own history" if m.get('band') and m.get('pct') is not None else 'no meaningful multiple'
        tip = E(f"{c['name']} — {cat}. {pos}" + (f", getting {dr}" if dr in ('cheaper', 'dearer') else '') + '. ' + '; '.join(c['result']['lines'][:2]))
        notes = NOTES[t]
        if REAS[t]: tip += E(' — ' + '; '.join(x for x, _ in REAS[t]))
        tw = tickw(t); chip = CHIP if notes else 0
        # ticker text: starts right of the dot, or ends left of it (then the chip sits between the text and the dot)
        tx = (x - 9 - chip) if left else (x + 9)
        anchor = 'end' if left else 'start'
        bx0 = (tx - tw - 5) if left else (tx - 5)
        bw = tw + chip + 8
        out = (f"<a href='#{t}' data-open='{t}'><g class='q-pt'><title>{tip}</title>"
               f"<rect x='{(x - wid(t) - 16) if left else (x - 8):.1f}' y='{yy - 11}' width='{wid(t) + 24:.1f}' height='22' class='q-hit'/>"
               + (f"<rect x='{bx0:.1f}' y='{yy - 10}' width='{bw:.1f}' height='20' rx='4' class='q-bx q-bx-{SEV[t]}'/>" if notes else '') +
               f"<circle cx='{x:.1f}' cy='{yy}' r='{4 if cls == 'qd-not' else 5}' class='{cls}'/>"
               f"<text x='{tx:.1f}' y='{yy + 4}' text-anchor='{anchor}' class='q-lb{' q-lbn' if cls == 'qd-not' else ''}'>{t}{arr}</text>"
               + (f"<text x='{(x - 9) if left else (x + 9):.1f}' y='{yy + 18}' text-anchor='{anchor}' class='q-why{(' ' + band[1]) if band[1] != 'q-why' else ''}'>{E(band[0])}</text>" if band else '')
               + "</g></a>")
        if notes:
            cx0 = (x - 9 - chip + 2) if left else (tx + tw + 2)
            out += (f"<g class='q-tog q-tg-{SEV[t]}' data-n='{t}' role='button' tabindex='0' aria-label='{E(t)}: show notes'>"
                    f"<rect x='{cx0:.1f}' y='{yy - 8}' width='{chip - 4}' height='16' rx='3' class='q-tgb'/>"
                    f"<text x='{cx0 + (chip - 4) / 2:.1f}' y='{yy + 4}' text-anchor='middle' class='q-tgt'><tspan class='g-closed'>▸</tspan><tspan class='g-open'>▾</tspan>{len(notes)}</text></g>")
            lines = notes; nw = max(len(tx_) for tx_, _ in lines) * 6.3 + 20; nh = 14 * len(lines) + 12
            nx = bx0 if not left else (bx0 + bw - nw)
            nx = max(4, min(nx, W - nw - 4)); ny = yy + (26 if band else 12)   # below the band's reason line when there is one
            NOTE_LOW.append(ny + nh)
            NOTE_SVG.append(f"<g class='q-note' id='qn-{t}'><rect x='{nx:.1f}' y='{ny:.1f}' width='{nw:.1f}' height='{nh}' rx='5' class='q-nb q-bx-{SEV[t]}'/>"
                            + ''.join(f"<text x='{nx + 10:.1f}' y='{ny + 17 + 14 * i:.1f}' class='q-why{(' ' + cl) if cl != 'q-why' else ''}'>{E(tx_)}</text>" for i, (tx_, cl) in enumerate(lines)) + "</g>")
        return out
    for r, _ in ROWS:
        for t in pts[r]:
            x, lane, left = lay[t]; s.append(dot(t, x, RY[r] + TOPP + lane * LN[r] + 6, left, BANDR[t]))
        for i, t in enumerate(nam[r]):   # narrow column: the band line is cut to fit (full text in the hover); notes open over the map as elsewhere
            bl = BANDR[t]; bl = ((bl[0].split(' · ')[0] if len(bl[0]) > 15 else bl[0]), bl[1]) if bl else None
            s.append(dot(t, XNA0 + 16, RY[r] + TOPP + i * LN[r] + 6, False, bl))
    s.extend(NOTE_SVG)
    if NOTE_LOW and max(NOTE_LOW) + 4 > H:      # room for the lowest open note, so it is not cut off at the bottom of the map
        s[0] = s[0].replace(f"viewBox='0 0 {W} {H}'", f"viewBox='0 0 {W} {max(NOTE_LOW) + 4:.0f}'")
    s.append('</svg>')
    key = ("<p class='q-key'><svg width='10' height='10'><circle cx='5' cy='5' r='4.5' class='qd-now'/></svg> Research now &nbsp; "
           "<svg width='12' height='12'><circle cx='6' cy='6' r='4.5' class='qd-ring'/></svg> Research at lower price or Quick look &nbsp; "
           "<svg width='10' height='10'><circle cx='5' cy='5' r='3.5' class='qd-not'/></svg> Not now &nbsp; "
           "<b class='q-dc'>↓</b> getting cheaper &nbsp; <b class='q-dd'>↑</b> getting dearer. "
           "Left to right: the median of P/E, EV/EBIT and EV/EBITDA as a percentile of the stock's own history; the line between the boxes is its usual level (50th). "
           "Rows: the Business light" + ("; the hatched band holds names not judged yet (accounting red flag, too early after a deal, or a Business light that a missing measure decides), placed by their multiples only. " if len(ROWS) == 4 else ". ") +
           ("A box around a ticker holds its notes; click <b>▸</b> to open them over the map (they never move another ticker), or use Show all notes. Box colour: <b class='q-keyr'>red</b> = accounting red flag; <b class='q-keya'>amber</b> = a past issue outside the red-flag horizon (for example an SEC case for misconduct that ended more than 5 years ago; not a red flag) or high debt; grey = business changing, new CEO or multiples that disagree. " if any(NOTES.values()) else '') +
           "右列表示历史估值分位不可用，仍可能有当前倍数；亏损、历史不足与取数缺口分别列示。Hover a ticker for its label and reason; click to open its section.</p>")
    tools = "<div class='q-tools'><button type='button' class='q-allnotes'>Show all notes</button></div>" if any(NOTES.values()) else ''
    return f"<div class='wrap qwrap'>{tools}{''.join(s)}</div>{key}"

def valuation_coverage():
    audited=[t for t in ORDER if D[t].get('valuation_quality')]
    if not audited:return ''
    usable=sum(bool(D[t]['mult']['band']) for t in audited)
    rows=[]
    for t in audited:
        c=D[t];a=c['valuation_quality'];m=c['mult'];approx=a.get('approximate_current') or {}
        values=approx.get('values') or {}
        cells=[]
        for k,nm,_ in MK:
            q=a['metrics'][k];v=m['metrics'][k]['now'];is_approx=v is None and k in values
            if is_approx:v=values[k]
            shown='—' if v is None else f'{v:.2f}×'+('（分母≤0）' if v<=0 else '')+(' ≈' if is_approx else '')
            note=(f"第{m['metrics'][k]['pct']}分位" if m['metrics'][k]['pct'] is not None else q['reason'])
            cells.append(f"<td title='{E(note)}'>{E(shown)}<div class='grp'>{E(note)}</div></td>")
        extra=approx.get('reason') or '; '.join(a.get('limitations') or [])
        rows.append(f"<tr><td><a href='#{t}' data-open='{t}'>{E(t)}</a></td>{''.join(cells)}<td>{E(extra)}</td></tr>")
    return (f"<details class='valuation-coverage'><summary>估值覆盖：{usable}/{len(audited)}家公司有合格历史分位；查看当前倍数与逐项原因</summary>"
            "<p class='muted'>当前倍数与历史分位分开判断。正值、非正值、缺失交易日分别统计；缺失不等于亏损。≈为单列近似值，不参与分位。具体来源与日期见估值底稿。</p>"
            "<div class='wrap'><table class='probs'><thead><tr><th>公司</th><th>P/E</th><th>EV/EBIT</th><th>EV/EBITDA</th><th>口径与限制</th></tr></thead><tbody>"+''.join(rows)+"</tbody></table></div>"
            "<p><a href='valuation_coverage.csv'>下载逐项覆盖</a> · <a href='valuation_audit.json'>原始输入与来源</a> · <a href='source_ledger.json'>来源总索引</a></p></details>")

def overview():
    rows = ''
    for i, t in enumerate(ORDER, 1):
        c = D[t]; p = c['pe']; m = c['mult']; sc = c['scores']
        if not m['band']:
            mini = "<span class='muted'>not meaningful</span>"
        else:
            x = m['pct']
            mini = (f"<svg viewBox='0 0 120 16' class='mini' aria-label='{ordn(x)} percentile'><rect x='0' y='5' width='40' height='6' class='b-bot'/><rect x='40' y='5' width='40' height='6' class='b-mid'/><rect x='80' y='5' width='40' height='6' class='b-top'/>"
                    f"<circle cx='{min(max(x * 1.2, 5), 115):.1f}' cy='8' r='4.5' class='now {'now-bot' if x <= 33 else ''}'/></svg> <span class='pct'>{ordn(x)}</span>")
        fl = ''.join(f"<div class='flag{' warn' if x.startswith('Past SEC') else ''}' title='{E(next((f for f in c['flags'] if f.startswith(x)), x))}'>{E(x)}</div>" for x in dict.fromkeys(x.split(':')[0] for x in c['flags'] if not x.startswith('Business changing')))
        rf = ''
        pe_txt = f"<div class='mline'>{mult_line(m)}</div>" + level_html(m)
        rows += (f"<tr><td>{i}</td><td><a href='#{t}' data-open='{t}'>{E(c['name'])}</a> <small class='muted'>{t}</small></td><td class='rc'>{result_cell(c)}</td>"
                 f"<td class='lc'>{flight(c['business'], 'Business', False)}</td><td class='lc'>{flight(c['industry'], 'Industry', False)}{("<div class='grp'>" + E(c['industry'].get('count') or '') + "</div>") if c['industry'].get('count') else ''}</td><td class='lc'>{flight(c['management'], 'Management', False)}{('<div>' + ceo_tag(c) + '</div>') if c.get('ceo') else ''}</td>"
                 f"<td>{mini}<div class='grp'>{pe_txt}</div></td><td>{rf}{fl or ('' if rf else '<span class=muted>–</span>')}</td></tr>")
    return ("<table class='ov'><thead><tr><th>#</th><th>Company</th><th>Result</th><th class='lc'>Business</th><th class='lc'>Industry</th><th class='lc'>Management</th><th>Multiples in their own history</th><th>Other flags</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>")

def ceo_tag(c, cls=''):
    """CEO change within 5 years: amber tag under 24 months in office, grey tag from 2 to 5 years. Hover = the full sentence."""
    x = c.get('ceo')
    if not x: return ''
    lab = x['label'] + (f" · {x['count']} changes in 5 yrs" if x.get('count', 0) >= 2 else '')
    return f"<span class='ceo {'ceo-new' if x['tier'] == 'new' else 'ceo-recent'} {cls}' title='{E(x['text'])}'>{E(lab)}</span>"

def ceo_note(c):
    x = c.get('ceo')
    if not x: return ''
    return f"<p class='ceo-note {'cn-new' if x['tier'] == 'new' else 'cn-recent'}'>{E(x['text'])}</p>"

def lights_legend():
    return ("<div class='legend'><span>Result = should research time go here now?</span>"
            "<span><span class='res r-now'>Research now</span> yes: good business, and its multiples sit at or below their usual level (median percentile 50th or lower) or are getting cheaper</span>"
            "<span><span class='res r-quick'>Quick look</span> a short check now: average business, but its multiples are low in their own history (median percentile 33rd or lower); the line says what to check</span>"
            "<span><span class='res r-watch'>Research at lower price</span> not yet: good business, but its multiples are above their usual level and not getting cheaper; research has not started; the line gives the share price at which to start</span>"
            "<span><span class='res r-pass'>Not now</span> no: average business with multiples not low, too early to judge, weak business, or an accounting red flag; the first line says which, and when to revisit</span></div>"
            "<div class='legend'>"
            "<span>Multiples: P/E, EV/EBIT and EV/EBITDA, each placed in the stock's own daily history (10 years; after a merger or separation, from 12 months after it). The bar shows the median of the three percentiles; the line under it shows each one. When they differ by 30 points or more, one of them is distorted and the Result says so.</span>"
            "<span>Direction: <span class='dir dir-cheap'>↓ Getting cheaper</span> <span class='dir dir-steady'>→ Steady</span> <span class='dir dir-dear'>↑ Getting dearer</span>. ↓ Getting cheaper = today's multiples 10% or more below their own median of the last year and below where they stood a year ago; ↑ Getting dearer = the mirror; → Steady otherwise. 'vs own level' compares today with the stock's own median over 1, 3, 5 and 10 years (shorter after a deal or listing, length in brackets). Hover for the medians and the single-day split into price and EPS.</span>"
            "<span>The multiples compare the stock only with its own past. They are not a valuation: whether a price is attractive is decided later, against the 15% hurdle.</span></div>"
            "<div class='legend'><span>Lights:</span><span><span class='lt lt-g'>✓</span> green (good)</span><span><span class='lt lt-y'>" + HALF + "</span> yellow (average)</span><span><span class='lt lt-r'>✗</span> red (weak)</span><span><span class='lt lt-q'>?</span> grey = a measure is missing and the light depends on it</span><span><span class='lt lt-na'>–</span> not scored</span><span><span class='ceo ceo-new'>New CEO · month</span> CEO in office under 2 years; <span class='ceo ceo-recent'>CEO since month</span> 2 to 5 years. Hover for how many of the years behind M2 and M3 fall under this CEO.</span>"
            "<span>Each light is the average of its measures: 3.5 or more green, 3.0–3.5 yellow, below 3.0 red. Hover a light for its number; open the company for every measure.</span></div>")

def reopen_section():
    """v4.3: the run against each company's screening record (初筛记录) in the vault: reopen conditions met, and what changed with its cause."""
    if not REOPEN: return ''
    it = REOPEN.get('items') or []
    trig = [i for i in it if i['status'] == 'Look again']; first = [i for i in it if i.get('first')]
    chg = [i for i in it if i.get('changes') and i['status'] != 'Look again']
    nm = lambda i: f"<a href='#{E(i['t'])}' data-open='{E(i['t'])}'>{E(D[i['t']]['name'] if i['t'] in D else i['t'])}</a>"
    cz = lambda i: '<br>'.join(f"{E(c['what'])}: {E(str(c['before']))} → {E(str(c['now']))} <span class='muted'>({E(c['cause'])})</span>" for c in i['changes']) or '–'
    you = lambda i: E(' · '.join(x for x in (i.get('our_decision') or 'not reviewed', i.get('our_reason') or '') if x))
    rows = ''.join(f"<tr><td>{nm(i)}</td><td>{E(i.get('before') or '')}</td><td>{E(i['now'])}</td><td>{E('; '.join(i['why']))}</td><td>{you(i)}</td><td>{cz(i)}</td></tr>" for i in trig)
    rows2 = ''.join(f"<tr><td>{nm(i)}</td><td>{E(i.get('before') or '')}</td><td>{E(i['now'])}</td><td>{cz(i)}</td></tr>" for i in chg)
    head = (f"<h2>Look again: checks against the screening records</h2><p class='muted'>{len(it)} compan{'ies' if len(it) != 1 else 'y'} compared with their records in the vault (08 Screener/初筛记录): "
            f"{len(trig)} to look again at (reopen condition met), {len(chg)} other record{'s' if len(chg) != 1 else ''} with changes, {len(first)} first record{'s' if len(first) != 1 else ''}. "
            "Each change carries its cause: business (a new fiscal year in the data, a CEO change), price, rules, data, filing or peers. Only business changes can mean the case for the company has changed; "
            "a rules change is separated by rebuilding the last run under the new rules.</p>")
    t1 = (f"<div class='wrap'><table class='probs'><thead><tr><th>Company</th><th>Recorded label</th><th>Now</th><th>Why look again (reopen condition met)</th><th>Your decision</th><th>What changed (cause)</th></tr></thead><tbody>{rows}</tbody></table></div>"
          if trig else "<p class='muted'>No company to look again at in this run: no reopen condition met.</p>")
    t2 = (f"<details><summary>Other changes since the last record ({len(chg)})</summary><div class='wrap'><table class='probs'><thead><tr><th>Company</th><th>Recorded label</th><th>Now</th><th>What changed (cause)</th></tr></thead><tbody>{rows2}</tbody></table></div></details>"
          if chg else '')
    return head + t1 + t2

def moves_table():
    mv = TXT.get('moves') or []
    if not mv: return ''
    rows = ''.join(f"<tr><td><a href='#{m['t']}' data-open='{m['t']}'>{E(D[m['t']]['name'] if m['t'] in D else m['t'])}</a></td><td>{E(m['v1'])}</td><td>{E(D[m['t']]['result']['cat'] + ' — ' + D[m['t']]['result']['lines'][0]) if m['t'] in D else ''}</td><td>{E(m['why'])}</td></tr>" for m in mv)
    return (f"<h2>{E(TXT.get('moves_title') or 'What changed from the last run')}</h2><p class='muted'>{E(TXT.get('moves_intro', ''))}</p>"
            f"<div class='wrap'><table class='probs'><thead><tr><th>Company</th><th>Before</th><th>Now</th><th>What changed</th></tr></thead><tbody>{rows}</tbody></table></div>")

CSS = """
:root{--bk-ov:#6f6e69;--bk-ov-t:#f6f5f2;--bk-rf:#4a5568;--bk-rf-t:#eef1f5;--bk-bu:#2457a6;--bk-bu-t:#ebf2fc;--bk-in:#0f7a78;--bk-in-t:#e6f5f4;--bk-ma:#6b44b8;--bk-ma-t:#f1ecfb;--bk-rk:#8a4b22;--bk-rk-t:#f8eee6;--bk-nf:#8a8984;--bk-nf-t:#f7f7f5}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bk-ov:#a9a8a0;--bk-ov-t:#262624;--bk-rf:#9fb0c8;--bk-rf-t:#232830;--bk-bu:#7fb0f0;--bk-bu-t:#1b2638;--bk-in:#5fcdc8;--bk-in-t:#162d2c;--bk-ma:#b79cf0;--bk-ma-t:#28213a;--bk-rk:#e0a375;--bk-rk-t:#33251b;--bk-nf:#8f8e86;--bk-nf-t:#252524}}
:root[data-theme="dark"]{--bk-ov:#a9a8a0;--bk-ov-t:#262624;--bk-rf:#9fb0c8;--bk-rf-t:#232830;--bk-bu:#7fb0f0;--bk-bu-t:#1b2638;--bk-in:#5fcdc8;--bk-in-t:#162d2c;--bk-ma:#b79cf0;--bk-ma-t:#28213a;--bk-rk:#e0a375;--bk-rk-t:#33251b;--bk-nf:#8f8e86;--bk-nf-t:#252524}
.blk{--k:var(--bk-nf);--kt:var(--bk-nf-t);margin:16px 0 0;padding:4px 14px 14px;border:1px solid var(--line);border-left:5px solid var(--k);border-radius:8px;background:var(--kt);overflow-x:auto}
.blk>h4:first-child,.blk>.top2>div>h4:first-child{margin-top:10px}.blk h4{color:var(--k)}.blk table{background:var(--panel)}
.blk-ov{--k:var(--bk-ov);--kt:var(--bk-ov-t)}.blk-rf{--k:var(--bk-rf);--kt:var(--bk-rf-t)}.blk-bu{--k:var(--bk-bu);--kt:var(--bk-bu-t)}.blk-in{--k:var(--bk-in);--kt:var(--bk-in-t)}.blk-ma{--k:var(--bk-ma);--kt:var(--bk-ma-t)}.blk-rk{--k:var(--bk-rk);--kt:var(--bk-rk-t)}.blk-nf{--k:var(--bk-nf);--kt:var(--bk-nf-t)}
.cobody>.blk:first-child{margin-top:14px}@media (max-width:600px){.blk{padding:2px 10px 10px}}
:root{--bg:#fcfcfb;--panel:#ffffff;--ink:#0b0b0b;--ink2:#52514e;--ink3:#8a8984;--line:#e4e3de;--grid:#eeede9;--acc:#2a78d6;--acc-t:rgba(42,120,214,.16);--mid-t:rgba(82,81,78,.10);--top-t:rgba(82,81,78,.04);--chip:#f3f2ef;}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#1a1a19;--panel:#222221;--ink:#f0efec;--ink2:#c3c2b7;--ink3:#8f8e86;--line:#3a3a37;--grid:#2e2e2c;--acc:#3987e5;--acc-t:rgba(57,135,229,.24);--mid-t:rgba(195,194,183,.12);--top-t:rgba(195,194,183,.05);--chip:#2c2c2a;}}
:root[data-theme="dark"]{--bg:#1a1a19;--panel:#222221;--ink:#f0efec;--ink2:#c3c2b7;--ink3:#8f8e86;--line:#3a3a37;--grid:#2e2e2c;--acc:#3987e5;--acc-t:rgba(57,135,229,.24);--mid-t:rgba(195,194,183,.12);--top-t:rgba(195,194,183,.05);--chip:#2c2c2a;}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px 16px 80px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:40px 0 6px}h4{font-size:14px;margin:18px 0 8px;text-transform:uppercase;letter-spacing:.04em;color:var(--ink2)}
.lead{font-size:16px;max-width:900px}.sub,.muted,.cap{color:var(--ink2)}.cap{font-size:12.5px;margin:4px 0 0}
a{color:var(--acc);text-decoration:none}a:hover{text-decoration:underline}
table{border-collapse:collapse;width:100%;background:var(--panel)}th,td{border-bottom:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
th{font-size:12.5px;color:var(--ink2);font-weight:600;background:var(--bg)}.num{text-align:right;font-variant-numeric:tabular-nums}
.ov td{vertical-align:middle}.ov{font-size:14px}.mini{width:120px;height:16px;vertical-align:middle}.pct{font-variant-numeric:tabular-nums;font-size:13px;color:var(--ink2)}
.sc{display:inline-block;min-width:34px;text-align:center;padding:1px 7px;border-radius:6px;font-weight:650;font-variant-numeric:tabular-nums;background:var(--chip);border:1px solid var(--line)}
.sc.na{color:var(--ink3)}
.verdict{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12.5px;font-weight:600;border:1px solid var(--line);white-space:nowrap}
.v-now{background:var(--acc);color:#fff;border-color:var(--acc)}.v-watch{border-color:var(--acc);color:var(--acc)}.v-out{color:var(--ink3)}
.wrap{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px;overflow-x:auto}
svg text{font-family:inherit}.lbl{font-size:13.5px;fill:var(--ink);font-weight:600}.muted{fill:var(--ink2);font-size:12.5px}.hdr{fill:var(--ink2);font-size:12px;font-weight:600}
.tick{fill:var(--ink2);font-size:11.5px}.val{fill:var(--ink);font-size:12.5px;font-weight:600;font-variant-numeric:tabular-nums}.val.acc,.zl.acc{fill:var(--acc)}
.b-bot{fill:var(--acc-t)}.b-mid{fill:var(--mid-t)}.b-top{fill:var(--top-t);stroke:var(--line)}
.med{stroke:var(--ink2);stroke-width:2}.now{fill:var(--ink);stroke:var(--panel);stroke-width:2}.now-bot{fill:var(--acc)}
.z-bot{fill:var(--acc-t)}.z-mid{fill:var(--mid-t)}.zl{fill:var(--ink2);font-size:11.5px}.grid{stroke:var(--grid)}.medline{stroke:var(--ink2);stroke-dasharray:4 4}
.peline{fill:none;stroke:var(--ink2);stroke-width:1.6}
details.co{background:var(--panel);border:1px solid var(--line);border-radius:10px;margin:10px 0}
details.co>summary{cursor:pointer;list-style:none;display:flex;gap:14px;align-items:center;padding:12px 16px;flex-wrap:wrap}
details.co>summary::-webkit-details-marker{display:none}details.co>summary:before{content:'▸';color:var(--ink3)}details.co[open]>summary:before{content:'▾'}
.rk{color:var(--ink3);font-variant-numeric:tabular-nums;width:20px}.cn{font-weight:650;font-size:16px;flex:1;min-width:180px}.cn small{color:var(--ink3);font-weight:500}
.fx{color:var(--ink2);font-size:13px;display:flex;gap:6px;align-items:center}
.cobody{padding:0 16px 18px;border-top:1px solid var(--line)}.top2{display:grid;grid-template-columns:minmax(260px,1fr) minmax(320px,1.6fr);gap:24px}
@media (max-width:820px){.top2{grid-template-columns:1fr}}
.steps{margin:0;padding-left:20px}.steps li{margin:0 0 8px}.steps li span{display:block;color:var(--ink2);font-size:12.5px}.steps li b{font-weight:600;font-size:14px}
.pel{font-size:13px;color:var(--ink2);margin-bottom:4px}
.mt{font-size:13.5px}.mt td{padding:9px 10px}.mcode{width:170px}.mcode div{font-weight:600}.kind{font-size:11px;color:var(--ink3);text-transform:uppercase;letter-spacing:.04em}
.kv{display:flex;justify-content:space-between;gap:10px;border-bottom:1px dashed var(--grid);padding:2px 0}.kv span{color:var(--ink2)}.kv.kvl{display:block}.kv.kvl b{display:block;text-align:left;font-weight:500}.kv b{font-weight:600;text-align:right;font-variant-numeric:tabular-nums}
.segs{margin-top:6px}.calc{font-weight:600}.note{font-size:12.5px;margin-top:4px;color:var(--ink)}.rule{font-size:12px;color:var(--ink3);margin-top:4px}
.scol{width:64px;text-align:center}.favg{font-size:13px;color:var(--ink2);margin:6px 0 4px}
.ev{margin-top:6px}.ev summary{cursor:pointer;color:var(--acc);font-size:12.5px}.ev p{margin:6px 0}.ev ul{margin:0;padding-left:18px;font-size:12.5px}.ev li{margin-bottom:4px}
.tag{font-size:10.5px;text-transform:uppercase;border:1px solid var(--line);border-radius:4px;padding:0 4px;color:var(--ink2)}.src{color:var(--ink2)}
.tools{display:flex;gap:8px;margin:10px 0}.tools button{font:inherit;font-size:13px;padding:5px 12px;border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--ink);cursor:pointer}
:root{--q1:#e4eefb;--q2:#f1f6fd}@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--q1:#1a2a40;--q2:#1f252d}}:root[data-theme="dark"]{--q1:#1a2a40;--q2:#1f252d}.qwrap{overflow-x:auto}.qmap{width:100%;min-width:760px;display:block}.q-now{fill:var(--q1);stroke:var(--line)}.q-low,.q-ql{fill:var(--q2);stroke:var(--line)}.q-not{fill:var(--panel);stroke:var(--line)}.q-na{fill:var(--chip);stroke:var(--line)}.qt{font-size:12.5px;font-weight:700;letter-spacing:.06em}.q-now-t,.q-low-t,.q-ql-t{fill:var(--acc)}.q-not-t{fill:var(--ink3)}.qs{font-size:11.5px;fill:var(--ink3)}.q-tick{stroke:var(--grid);stroke-width:1}.q-rn{font-size:14px;font-weight:650;fill:var(--ink)}.q-rn2{font-size:12px;fill:var(--ink2)}.q-sw-g{fill:var(--lg)}.q-sw-y{fill:var(--ly)}.q-sw-r{fill:var(--lr)}.q-ax{font-size:12px;fill:var(--ink2);font-weight:600}.q-tk{font-size:11px;fill:var(--ink3)}.qd-now{fill:var(--acc)}.qd-ring{fill:var(--panel);stroke:var(--acc);stroke-width:2}.qd-not{fill:var(--ink3)}.q-lb{font:650 12.5px ui-monospace,Menlo,monospace;fill:var(--ink)}.q-lbn{fill:var(--ink2);font-weight:500}.q-dc{fill:var(--lg);color:var(--lg);font-weight:800}.q-dd{fill:var(--lr);color:var(--lr);font-weight:800}.q-hit{fill:transparent}.q-hlw{fill:var(--ly-t);stroke:var(--ly);stroke-width:1.2}.q-np{fill:url(#qhatch);stroke:var(--line)}.q-np-t{fill:var(--ink3)}.q-hb{fill:var(--panel)}.q-hl{stroke:var(--chip);stroke-width:5}.q-sw-n{fill:var(--ink3)}.q-why{font-size:11px;fill:var(--ink3)}.q-whyr{fill:var(--lr);font-weight:600}.q-whya{fill:var(--ly);font-weight:600}.q-bx{stroke-width:1.2}.q-bx-r{fill:var(--lr-t);stroke:var(--lr)}.q-bx-a{fill:var(--ly-t);stroke:var(--ly)}.q-bx-g{fill:var(--chip);stroke:var(--ink3)}.q-tog{cursor:pointer}.q-tgb{fill:var(--panel);stroke:var(--line)}.q-tog:hover .q-tgb,.q-tog:focus .q-tgb{stroke:var(--ink2)}.q-tog:focus{outline:none}.q-tgt{font:700 10.5px -apple-system,Segoe UI,sans-serif;fill:var(--ink2)}.q-tg-r .q-tgt{fill:var(--lr)}.q-tg-a .q-tgt{fill:var(--ly)}.q-tog .g-open,.q-tog.open .g-closed,.qmap.notes-all .q-tog .g-closed{display:none}.q-tog.open .g-open,.qmap.notes-all .q-tog .g-open{display:inline}.q-note{display:none}.q-note.open,.qmap.notes-all .q-note{display:inline}.q-nb{stroke-width:1.2;filter:drop-shadow(0 2px 3px rgba(0,0,0,.18))}.q-tools{display:flex;justify-content:flex-end;margin:-4px 0 6px}.q-allnotes{font:600 12px -apple-system,Segoe UI,sans-serif;padding:4px 10px;border-radius:6px;border:1px solid var(--line);background:var(--panel);color:var(--ink2);cursor:pointer}.q-allnotes:hover{border-color:var(--ink3)}.q-keyr{color:var(--lr)}.q-keya{color:var(--ly)}.q-pt:hover .q-lb{text-decoration:underline}.q-key{margin:6px 0 0;font-size:12px;color:var(--ink3)}.q-hlk{font:650 11px ui-monospace,Menlo,monospace;color:var(--ink);background:var(--ly-t);border:1px solid var(--ly);border-radius:3px;padding:0 4px}.ceo{display:inline-block;margin-top:4px;font-size:11px;font-weight:600;line-height:1.25;padding:2px 6px;border-radius:4px;border:1px solid;white-space:normal;max-width:120px}.ceo.sm{margin-top:0;vertical-align:middle;max-width:none;white-space:nowrap}.ceo-new{color:var(--ly);background:var(--ly-t);border-color:var(--ly)}.ceo-recent{color:var(--ink2);background:var(--chip);border-color:var(--line)}.ceo-note{margin:4px 0 8px;padding:7px 10px;border-left:3px solid;font-size:13px;line-height:1.45}.cn-new{border-color:var(--ly);background:var(--ly-t)}.cn-recent{border-color:var(--line);background:var(--chip)}.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:12.5px;color:var(--ink2);margin:8px 0}.sw{display:inline-block;width:14px;height:10px;border-radius:2px;margin-right:5px;vertical-align:middle}
.method li{margin-bottom:6px}.grp{font-size:11.5px;color:var(--ink3)}.ov td:nth-child(6){white-space:nowrap}.probs td{font-size:13.5px}
.flag{font-size:11.5px;color:var(--ink2);margin-top:3px}.flag.warn{display:inline-block;font-weight:600;color:var(--ink);background:var(--ly-t);border-left:3px solid var(--ly);padding:2px 6px;border-radius:3px}.flags{margin:0;padding-left:18px;font-size:13px}.flags li{margin-bottom:4px}
.small{font-size:12.5px}.mt.small td{padding:6px 8px}.bad{color:#c4342b}
:root{--g0:#86b6ef;--g1:#5598e7;--g2:#2a78d6;--g3:#1c5cab;--g4:#104281;--gna:#b9b8b2}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--g0:#184f95;--g1:#2a78d6;--g2:#5598e7;--g3:#86b6ef;--g4:#b7d3f6;--gna:#5a5a56}}
:root[data-theme="dark"]{--g0:#184f95;--g1:#2a78d6;--g2:#5598e7;--g3:#86b6ef;--g4:#b7d3f6;--gna:#5a5a56}
.g0{fill:var(--g0);stroke:var(--g0)}.g1{fill:var(--g1);stroke:var(--g1)}.g2{fill:var(--g2);stroke:var(--g2)}.g3{fill:var(--g3);stroke:var(--g3)}.g4{fill:var(--g4);stroke:var(--g4)}.gna{fill:var(--gna);stroke:var(--gna)}
i.gsw{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:middle}i.g0{background:var(--g0)}i.g1{background:var(--g1)}i.g2{background:var(--g2)}i.g3{background:var(--g3)}i.g4{background:var(--g4)}i.gna{background:var(--gna)}
.quad{width:100%;min-width:720px;height:auto}.qband{fill:var(--mid-t)}.qline{stroke:var(--ink2);stroke-width:1.5}.qline2{stroke:var(--ink3);stroke-width:1;stroke-dasharray:4 4}
.frame{fill:none;stroke:var(--line)}.qlab{fill:var(--ink3);font-size:12px}.ptl{fill:var(--ink);font-size:12.5px;font-weight:650}
.dot{stroke:var(--panel);stroke-width:2}.dot.hollow{fill:var(--panel);stroke-width:2.5}.dot.hollow.g0{stroke:var(--g0)}.dot.hollow.g1{stroke:var(--g1)}.dot.hollow.g2{stroke:var(--g2)}.dot.hollow.g3{stroke:var(--g3)}.dot.hollow.g4{stroke:var(--g4)}.dot.hollow.gna{stroke:var(--ink2)}.dot.gone{fill:var(--gna);stroke:var(--panel)}.ring{fill:none;stroke:var(--ink);stroke-width:1.6}
.xmark{stroke:#c4342b;stroke-width:2.4;stroke-linecap:round}.rbar{stroke:var(--ink2);stroke-width:1.5}.pt{cursor:pointer}.pt:hover .ptl{text-decoration:underline}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .bad{color:#ec6a5e}}:root[data-theme="dark"] .bad{color:#ec6a5e}
@media print{details.co{break-inside:avoid}.tools{display:none}}
:root{--lg:#1a7f46;--lg-t:#e2f3e8;--ly:#8a5a00;--ly-t:#fbefcf;--lr:#b3261e;--lr-t:#fbe2df;--ln:#8a8984;--ln-t:#f0efec}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--lg:#71d39c;--lg-t:#173523;--ly:#f0c35e;--ly-t:#3a2f12;--lr:#f2897f;--lr-t:#401d1a;--ln:#8f8e86;--ln-t:#2c2c2a}}
:root[data-theme="dark"]{--lg:#71d39c;--lg-t:#173523;--ly:#f0c35e;--ly-t:#3a2f12;--lr:#f2897f;--lr-t:#401d1a;--ln:#8f8e86;--ln-t:#2c2c2a}
.lt{display:inline-flex;align-items:center;justify-content:center;gap:3px;min-width:24px;height:22px;padding:0 6px;border-radius:6px;font-weight:700;font-size:13px;font-variant-numeric:tabular-nums;border:1px solid transparent;white-space:nowrap;cursor:default}
.lt.wide{min-width:58px}.lt-g{color:var(--lg);background:var(--lg-t);border-color:var(--lg)}.lt-y{color:var(--ly);background:var(--ly-t);border-color:var(--ly)}.lt-r{color:var(--lr);background:var(--lr-t);border-color:var(--lr)}.lt-na{color:var(--ln);background:var(--ln-t);border-color:var(--line)}
.res{display:inline-block;padding:3px 10px;border-radius:999px;font-size:13px;font-weight:650;white-space:nowrap;border:1.5px solid var(--line)}
.r-now{background:var(--acc);border-color:var(--acc);color:#fff}.r-watch{border-color:var(--acc);color:var(--acc)}.r-border{border-color:var(--ink3);color:var(--ink2)}.r-quick{border-color:var(--acc);border-style:dashed;color:var(--acc)}.r-pass{border-style:dashed;color:var(--ink3)}
.rwhy{font-size:12px;color:var(--ink2);margin-top:4px;max-width:300px;line-height:1.35}td.rc{min-width:230px}
.trend{font-size:12px;margin-top:3px;color:var(--ink)}.trend .muted{font-size:11.5px}.t-falling{color:var(--acc)}.dir{display:inline-block;font-size:11.5px;font-weight:600;line-height:1;padding:3px 7px;border-radius:10px;border:1px solid;white-space:nowrap}.dir-cheap{color:var(--lg);background:var(--lg-t);border-color:var(--lg)}.dir-dear{color:var(--lr);background:var(--lr-t);border-color:var(--lr)}.dir-steady{color:var(--ink2);background:var(--chip);border-color:var(--line)}.lvl{font-size:11.5px;color:var(--ink2)}.t-rising{color:var(--ink)}.t-steady{color:var(--ink2)}h5{margin:10px 0 4px;font-size:12px;color:var(--ink2);text-transform:uppercase;letter-spacing:.04em}.peerboxes{display:grid;gap:12px;margin:8px 0}.parbox{border:1px solid var(--line);border-radius:8px;padding:10px;background:var(--panel)}.pb-h{font-weight:600;margin-bottom:8px}.tagrow{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px}.tagbox{border:1px solid var(--grid);border-radius:6px;padding:8px}.tb-h{font-size:13px;margin-bottom:6px}.tb-h .wide{font-size:11px;color:var(--acc)}.chips{display:flex;flex-wrap:wrap;gap:4px}.chip{font:12px/1 ui-monospace,Menlo,monospace;border:1px solid var(--line);border-radius:4px;padding:4px 6px;background:var(--chip)}.chip.run{font-weight:700;border-color:var(--ink2)}.chip.nodata{color:var(--ink3);background:transparent;border-style:dashed}.mline{font-size:12px;color:var(--ink2);margin-top:2px}.mk{fill:var(--panel);stroke:var(--ink2);stroke-width:1.5}.trends{margin-top:6px}table.mx td,table.mx th{font-size:12.5px}.t-one{font-size:11.5px;margin-top:2px}.t-na{color:var(--ink2)}
svg.half{width:14px;height:14px;display:block}
.lt-q{color:var(--ink2);background:var(--chip);border-color:var(--ink3)}.lt.big{min-width:34px;height:28px;font-size:16px}td.lc,th.lc{text-align:center}
.minis{display:inline-flex;gap:3px;margin-top:4px}.minis .lt{min-width:20px;height:18px;font-size:11px;padding:0 4px}
.uni td{font-size:13px}.uni .run{font-weight:700}
"""

JS = """
document.querySelectorAll('[data-open]').forEach(a=>a.addEventListener('click',()=>{const d=document.getElementById(a.dataset.open);if(d)d.open=true;}));
document.querySelectorAll('.qmap .q-tog').forEach(g=>{const f=()=>{const n=document.getElementById('qn-'+g.dataset.n);if(n){n.classList.toggle('open');g.classList.toggle('open');}};g.addEventListener('click',f);g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();f();}});});
document.querySelectorAll('.q-allnotes').forEach(b=>b.addEventListener('click',()=>{const m=document.querySelector('.qmap');const on=m.classList.toggle('notes-all');b.textContent=on?'Hide all notes':'Show all notes';}));
document.getElementById('openall').onclick=()=>document.querySelectorAll('details.co').forEach(d=>d.open=true);
document.getElementById('closeall').onclick=()=>document.querySelectorAll('details.co').forEach(d=>d.open=false);
if(location.hash){const d=document.getElementById(location.hash.slice(1));if(d&&d.tagName==='DETAILS')d.open=true;}
"""


# ---------------- page assembly (generic text; run-specific text from page_text.json)
def problems_table():
    probs = TXT.get('problems') or []
    if not probs: return ''
    rows = ''.join(f"<tr><td>{i}</td><td><b>{E(p['title'])}</b></td><td>{E(p['what'])}</td><td>{E(p['fix'])}</td></tr>" for i, p in enumerate(probs, 1))
    return (f"<h2>{E(TXT.get('problems_title') or 'What the run shows about the definitions')}</h2><p class='muted'>{E(TXT.get('problems_intro', ''))}</p>"
            f"<div class='wrap'><table class='probs'><thead><tr><th>#</th><th>Problem</th><th>What happened in this run</th><th>Proposed fix</th></tr></thead><tbody>{rows}</tbody></table></div>")

def windows_note():
    late = [(D[t]['name'], D[t]['mult']['window'], D[t]['mult'].get('windowWhy')) for t in ORDER if _later(D[t]['mult']['window'], PE_DEFAULT_FROM) and D[t]['mult'].get('windowWhy') != '10 years']
    if not late: return ''
    return ' Windows that start later: ' + '; '.join(f"{n} since {f[:7]}" + (f" ({w})" if w else '') for n, f, w in late) + '.'

METHOD = [
    ('Facts only.', 'Every measure is calculated from reported numbers or read as a fact from a primary document (10-K, proxy, 8-K, annual report, AGM results, SEC release). No judgment scores and no verdict labels.'),
    ('Lights.', 'Each measure is still set on 1–5 by a fixed rule (the arithmetic is shown); 4–5 shows green ✓ (good), 3 yellow half circle (average), 1–2 red ✗ (weak). A factor light is the average of its measures: 3.5 or more green, 3.0–3.5 yellow, below 3.0 red. A missing measure makes a range (missing = 1 to missing = 5); if the light is the same colour at both ends it is shown, and if the colour depends on the missing measure the light is a grey ?.'),
    ('Three factors, never combined.', 'Business (B1–B4), Industry (I1–I3) and Management (M1–M3) each get their own light in the results table. Each company section shows every measure behind them.'),
    ('Industry.', 'Groups come from a tagged coverage universe: each company carries one sub-industry tag. The Industry light is computed once per tag, over every company in the tag with data, the run company included, so every company in a tag gets the same Industry light; the number of companies sits under the light, and a group with fewer than 6 companies with data is marked thin. A tag keeps its own group when at least 4 of its companies have data; otherwise the whole tag widens to its parent group. I1 = median of the group\'s 10-year median ROIC including goodwill (same formula as B4): ≥12% green, 9–12% yellow, <9% red. I2 = median of the group\'s 10-year revenue growth: ≥7% green, 4–7% yellow, <4% red. I3 = the worst of the last 10 years for the group\'s median revenue change: better than −10% green, −10% to −20% yellow, worse than −20% red. Group companies use normalized inputs (see source_ledger.json) plus filed settlement liabilities (the same debt definition as the run companies); a company\'s window starts after a separation or a share-count jump above 50%, and acquisitions stay in. The line "Returns X% vs peers Y%" still compares the company with the others only.'),
    ('Business.', 'Average of B1 (return on capital excluding goodwill), B2 (cash conversion), B3 (growth in NOPAT per share, median end points) and B4 (return on all capital including goodwill). A missing measure is not averaged away: it gives a range from "missing = 1" to "missing = 5".'),
    ('Multiples.', "P/E, EV/EBIT and EV/EBITDA, each as a percentile of the stock's own daily history: 10 years, or from 12 months after a merger or separation above 25% of revenue (trailing earnings then cover only the current business), or since listing. A multiple needs at least 250 positive days and a positive value on 60% of days. The reading is the median of the percentiles available, so one distorted multiple cannot move it. Research line = the middle of the three share prices at which each multiple would sit at its own median."),
    ('Accounting red flags.', 'An 8-K Item 4.02 non-reliance in the last 3 years, a material weakness at the latest fiscal year-end, or an SEC Accounting and Auditing Enforcement Release (AAER) in the last 5 years. Non-SEC filers: a restatement the company calls an error correction, a modified audit opinion, or an accounting-regulator finding. These names should not get research time until the issue is resolved.'),
    ('Financial risk gate.', 'Net debt ÷ EBITDA above 5× (or EBITDA ≤ 0 with net debt), or operating income ÷ gross interest below 2×, latest fiscal year.'),
    ('Short history.', 'Fewer than 3 clean years on the current business. A year counts only if its income statement and both balance sheets are on the current business; a deal that moves revenue more than 25%, a separation, or a share-count jump above 50% starts the window after it. A deal flagged only by goodwill + intangibles (>25% of invested capital) keeps the window, and B1 and B4 take the lower of the full window and the years after the deal. Short history is tested before a weak Business light.'),
    ('Management.', 'CEO ownership as a multiple of base salary (M1: ≥15× green, 6–15× yellow; the −1 for a CEO selling more than 30% of held shares never takes M1 below 2), stock comp ÷ operating income and the pay vote (M2: lower of the two), impairments plus losses on businesses sold or held for sale, and the share count (M3), over the current CEO\'s years when there are at least 5 of them, otherwise over the full window. A CEO change in the last 5 years puts a tag under the Management light (amber under 2 years in office, grey from 2 to 5 years) and a line at the top of the Management block: who changed and when, and how many of the years behind M2 and M3 fall under the current CEO (a year counts when the CEO held the job for at least 6 of its 12 months; the pay vote covers the last fiscal year before the meeting). The tag itself changes no light; M3 uses the same year count to choose its window.'),
    ('Flags.', '"P/E distorted" = trailing P/E ÷ forward P/E above 1.5. "EV multiple rebuilt" = the daily series stopped updating, so today\'s value scales the last value by the change in enterprise value. "Business changing" = a deal above 25% of revenue after the latest year-end.'),
]

def universe_section():
    if not os.path.exists(P('universe_page.json')): return ''
    U = json.load(open(P('universe_page.json')))
    pc = lambda v: '–' if v is None else ('>100%' if v == 'inf' else f"{v * 100:.1f}%")
    tg = ''.join(f"<tr><td><b>{E(x['label'])}</b><div class='grp'>{E(x['parent'])}</div></td><td>{E(x['definition'])}</td><td class='num'>{x['n']}</td><td class='num'>{x['nRoic']}</td><td class='num'>{pc(x['roic'])}</td><td class='num'>{pc(x['revG'])}</td></tr>" for x in U['tags'])
    co = ''.join(f"<tr class='{'run' if c['run'] else ''}'><td>{E(c['t'])}</td><td>{E(c['name'])}</td><td>{E(c['tag'])}</td><td>{E(c['why'])}" + (f"<div class='grp'>Window: {E(c['window'])}</div>" if c['window'] else '') + f"</td><td>{E(c['gics'])}</td></tr>" for c in sorted(U['companies'], key=lambda c: (c['tag'], c['t'])))
    ex = ''.join(f"<li>{E(v)}</li>" for v in U['excluded'].values())
    boxes = ''
    for par in dict.fromkeys(x['parent'] for x in U['tags']):
        cards = ''
        for x in [x for x in U['tags'] if x['parent'] == par]:
            mem = sorted([c for c in U['companies'] if c.get('tagCode') == x['tag']], key=lambda c: (not c['run'], not c.get('data'), c['t']))
            chips = ''.join(f"<span class='chip{' run' if c['run'] else ''}{'' if c.get('data') else ' nodata'}' title='{E(c['name'] + ' — ' + c['why'])}'>{E(c['t'])}</span>" for c in mem)
            ok = sum(1 for c in mem if c.get('data'))
            cards += (f"<div class='tagbox'><div class='tb-h'><b>{E(x['label'])}</b> <span class='muted'>{len(mem)} companies · {ok} with data</span>"
                      + (f" <span class='wide'>under {U.get('tag_min', U['min_peers'] + 1)}: widens to the parent</span>" if ok < U.get('tag_min', U['min_peers'] + 1) else (f" <span class='wide'>thin group</span>" if ok < U.get('thin', 6) else '')) + f"</div><div class='chips'>{chips}</div></div>")
        boxes += f"<div class='parbox'><div class='pb-h'>{E(par)}</div><div class='tagrow'>{cards}</div></div>"
    boxes = (f"<div class='peerboxes'>{boxes}</div><p class='cap'>Bold = company in this run · grey = not enough clean years to count as a peer · hover a ticker for the company and the reason for its tag. "
             f"Every company in a box is scored against the whole box, itself included; a box with fewer than {U.get('tag_min', 4)} companies with data widens to its whole parent group.</p>")
    return (f"<h2>Peer groups: the coverage universe</h2>{boxes}<p class='muted'>{E(U.get('name') or '')} · {len(U['companies'])} companies · {E(U.get('status') or '')}. "
            f"A tag with fewer than {U.get('tag_min', 4)} companies that have data widens to its parent group; under {U.get('thin', 6)} it is marked thin. Bold rows are companies in this run.</p>"
            f"<div class='wrap'><table class='uni'><thead><tr><th>Tag</th><th>What belongs here</th><th>Companies</th><th>With ROIC data</th><th>Median ROIC incl. goodwill</th><th>Median revenue growth</th></tr></thead><tbody>{tg}</tbody></table></div>"
            f"<details class='ev'><summary>Every company, its tag and the reason (correct a tag in universe.json and rerun)</summary><table class='uni'><thead><tr><th>Ticker</th><th>Company</th><th>Tag</th><th>Why this tag</th><th>GICS sub-industry</th></tr></thead><tbody>{co}</tbody></table>"
            + (f"<p class='note'>Left out of the universe:</p><ul class='small'>{ex}</ul>" if ex else '') + "</details>")

def method_list():
    extra = TXT.get('method_notes') or []
    items = ''.join(f"<li><b>{E(a)}</b> {E(b)}</li>" for a, b in METHOD) + ''.join(f"<li>{E(x)}</li>" for x in extra)
    return f"<h2>How the rules work</h2><ol class='method'>{items}</ol>"

title = TXT.get('title') or CFG.get('title') or 'Screener scores'
n = len(D)
sub = TXT.get('sub') or f"{n} companies · rules version {RV} (engine {ENG}) · prices and P/E to {max((D[t]['pe'].get('to') or '') for t in D) or AS_OF}"
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="screen-data-sha256" content="{hashlib.sha256(Path(P('page_data.json')).read_bytes()).hexdigest()}">
<meta name="screen-config-sha256" content="{hashlib.sha256(Path(P('config.json')).read_bytes()).hexdigest()}">
<title>{E(TXT.get('tab_title') or 'Screener Scores')}</title><style>{CSS}</style></head><body><main>
<h1>{E(title)}</h1>
<div class="sub">{E(sub)}</div>
<p class="lead">{E(TXT.get('lead', ''))}</p>
<h2>Where each company lands</h2>
{quad_map()}
{valuation_coverage()}
<h2>Results</h2>
<p class="muted">One light per factor; the three are never combined. Click a company to open its section with every measure behind the lights. Order: no red flag first, then by Business.</p>
<div class="wrap">{overview()}</div>
{lights_legend()}
{reopen_section()}
<h2>Multiples today against each stock's own history</h2>
<p class="muted">One row per company, on a percentile axis. The three shapes are P/E, EV/EBIT and EV/EBITDA; the dot is their median, which the Result uses. Shapes far apart mean one multiple is distorted. Research line = the share price at which the median would reach the 50th percentile, with its distance from today's price.{E(windows_note())}</p>
<div class="wrap">{mult_strip()}</div>
<p class="cap">P/E = price ÷ diluted GAAP EPS of the last four quarters. EV/EBIT and EV/EBITDA = enterprise value ÷ trailing operating profit and EBITDA. Daily series use the sources recorded in source_ledger.json; derived ratios are analysis calculations. Forward P/E is in each company section.</p>
{moves_table()}
{problems_table()}
{universe_section()}
<h2>Score build-up by company</h2>
<p class="muted">Each company opens with its Result and a scorecard: one tile per measure with its 1–5 score (Pass or Fail for the financial risk gate and the red-flag check) and its key number; click a tile to jump to its row. Below are the panels: accounting red flags, Business, Industry (with the peer table), Management and the financial risk gate, each row led by its result, with year-by-year series drawn as small bar charts. Full inputs, the rule and the sources sit behind links in each row; Information and Perimeter are folded to one line and Perimeter opens when a deal cut the window.</p>
<div class="tools"><button id="openall">Open all</button><button id="closeall">Close all</button></div>
{''.join(company(t, i) for i, t in enumerate(ORDER, 1))}
{method_list()}
<p class="cap">{E(TXT.get('sources') or f"Sources: see source_ledger.json for actual providers, exact tools, periods and documents (report cutoff {AS_OF}). Derived values are analysis calculations. Company filings and governance facts are cited under each item. Built {AS_OF}.")}</p>
</main><script>{JS}</script></body></html>"""
from redesign import redesign
page, _nco = redesign(page)
assert _nco == len(ORDER), f'redesign rewrote {_nco} of {len(ORDER)} company sections'
out = P(CFG.get('output') or 'screener_scores.html')
open(out, 'w').write(page)
print(out, len(page))
