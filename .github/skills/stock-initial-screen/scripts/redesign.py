"""Score build-up redesign (rules 2026-10-21g; approved by the user on 2026-10-21 from a three-company sample).

make_html.py builds each company section as coloured panels; redesign() then rewrites each company
section: a Result card, a scorecard of tiles (1-5 score chip per measure, Pass/Fail for the two gates),
result-first measure rows, year series as small bar charts, rule text listed once per page, long inputs,
methods and sources behind links, every panel collapsible (Result, red flags, Business, Industry, Management
and the risk gate open by default; Information and Perimeter folded to one line, Perimeter opens when a
deal cut the window). Display only: no number, score, light or label changes.
Needs beautifulsoup4 (pip install beautifulsoup4 --break-system-packages).
"""
import re, html
from bs4 import BeautifulSoup

E = lambda x: html.escape(str(x), quote=True)
SHORT = {'B1': 'Return excl. goodwill', 'B2': 'Cash conversion', 'B3': 'Growth per share', 'B4': 'Return incl. goodwill',
         'I1': 'Industry returns', 'I2': 'Industry growth', 'I3': 'Worst industry year',
         'M1': 'CEO ownership', 'M2': 'Stock pay and vote', 'M3': 'Capital allocation', 'R1': 'Financial risk gate'}
PANEL = {'Business': 'bu', 'Industry': 'in', 'Management': 'ma', 'Financial risk gate': 'rk'}
SERIES_RE = re.compile(r'FY(\d{2,4})\s+([+\-−]?\d[\d,]*\.?\d*)(%?)')
RULES = {}


def txt(el):
    return re.sub(r'\s+', ' ', el.get_text(' ', strip=True)) if el else ''


def key_value(calc, kvs):
    head = calc.split('→')[0] if '→' in calc else calc
    m = re.findall(r'[-+−]?\d[\d,]*\.?\d*\s?[%×]', head)
    if m:
        return m[-1].replace(' ', '')
    for lab, val in kvs:
        if re.fullmatch(r'[-+−]?\d[\d,]*\.?\d*\s?[%×]', val.strip()):
            return val.strip()
    return ''


def bars(points, kind):
    # points: list of (label, value, pct)
    n = len(points); bw = 22; gap = 5; W = n * (bw + gap) + 10; H = 108; top = 16; base_h = 68
    vals = [v for _, v, _ in points]
    lo, hi = min(0, min(vals)), max(0, max(vals))
    rng = (hi - lo) or 1
    y = lambda v: top + (hi - v) / rng * base_h
    srt = sorted(vals); med = (srt[(n - 1) // 2] + srt[n // 2]) / 2
    pct = points[0][2]
    fmt = (lambda v: f"{v:.0f}%" if abs(v) >= 10 or v == int(v) else f"{v:.1f}%") if pct else (lambda v: f"{v:.2f}" if abs(v) < 10 else f"{v:,.0f}")
    out = [f"<svg class='spark' viewBox='0 0 {W} {H}' width='{W}' height='{H}' role='img' aria-label='{E(kind)} by year'>"]
    out.append(f"<line class='sp-zero' x1='0' x2='{W}' y1='{y(0):.1f}' y2='{y(0):.1f}'/>")
    labels = []
    for i, (lab, v, _) in enumerate(points):
        x = 5 + i * (bw + gap); y0, y1 = sorted((y(0), y(v)))
        out.append(f"<g><title>FY{lab}: {fmt(v)}</title><rect class='sp-bar{' sp-neg' if v < 0 else ''}' x='{x}' y='{y0:.1f}' width='{bw}' height='{max(y1 - y0, 1):.1f}' rx='2'/>"
                   f"<text class='sp-y' x='{x + bw / 2}' y='{H - 2}'>{lab[-2:]}</text></g>")
        labels.append(f"<text class='sp-v' x='{x + bw / 2}' y='{(y0 - 3) if v >= 0 else (y1 + 10):.1f}'>{fmt(v).replace('%', '')}</text>")
    out.append(f"<line class='sp-med' x1='2' x2='{W - 2}' y1='{y(med):.1f}' y2='{y(med):.1f}'><title>Median {fmt(med)}</title></line>")
    out.extend(labels)
    out.append('</svg>')
    unit = ' (%)' if pct else ''
    return f"<figure class='sp'>{''.join(out)}<figcaption>{E(kind)}{unit} · dashed line = median {fmt(med)}</figcaption></figure>"


def parse_row(tr):
    tds = tr.find_all('td', recursive=False)
    mc = tds[0]
    code = txt(mc.find('b')); name = txt(mc.find('div')); kind = txt(mc.find('span', class_='kind'))
    kvs = []
    for kv in tds[1].find_all('div', class_='kv'):
        kvs.append((txt(kv.find('span')), txt(kv.find('b'))))
    calc = txt(tds[2].find('div', class_='calc'))
    notes = [txt(n) for n in tds[2].find_all('div', class_='note', recursive=False)]
    rule = txt(tds[2].find('div', class_='rule'))
    srcs = tds[2].find('details', class_='ev')
    src_ul = srcs.find('ul') if srcs else None
    light = tds[3].find('span')
    return dict(code=code, name=name, kind=kind, kvs=kvs, calc=calc, notes=notes, rule=rule,
                src=(str(src_ul) if src_ul else ''), nsrc=(len(src_ul.find_all('li')) if src_ul else 0),
                light=(str(light) if light else ''), lcls=(' '.join(light.get('class', [])) if light else ''), ltitle=(light.get('title', '') if light else ''),
                lsym=(light.get_text() if light else ''))


def short_label(lab):
    s = re.split(r' \(', lab, maxsplit=1)[0]
    return s, (lab if s != lab else '')


def render_row(T, m, drop=()):
    if m['rule']:
        RULES.setdefault(m['code'], (m['name'], m['rule'].removeprefix('Rule: ')))
    shortkv, longkv, chart = [], [], ''
    for lab, val in m['kvs']:
        if lab in drop:
            continue
        pts = SERIES_RE.findall(val)
        if len(pts) >= 4 and not chart:
            chart = bars([(y, float(v.replace(',', '').replace('−', '-')), p == '%') for y, v, p in pts], short_label(lab)[0])
            continue
        if len(val) <= 34:
            shortkv.append((lab, val))
        else:
            longkv.append((lab, val))
    kvh = ''.join(f"<div class='kv2'><span{(" class=abbr title='" + E(full) + "'") if full else ''}>{E(s)}</span><b>{E(val)}</b></div>"
                  for lab, val in shortkv for s, full in [short_label(lab)])
    more = []
    if longkv:
        more.append(f"<details><summary>Full inputs ({len(longkv)})</summary>" + ''.join(f"<div class='kvl2'><span>{E(l)}</span><div>{E(v)}</div></div>" for l, v in longkv) + "</details>")
    if m['rule']:
        more.append(f"<details><summary>Rule</summary><p class='rtxt'>{E(m['rule'].removeprefix('Rule: '))}</p></details>")
    if m['src']:
        more.append(f"<details><summary>Sources ({m['nsrc']})</summary>{m['src']}</details>")
    notes = ''.join(f"<p class='mnote'>{E(n)}</p>" for n in m['notes'])
    big = m['light'].replace("class='", "class='big ") if m['light'] else ''
    big = re.sub(r"class=\"([^\"]*)\"", lambda g: f'class="{g.group(1)} big"', m['light'], count=1) if m['light'] else ''
    return (f"<div class='mrow' id='{T}-{m['code']}'>"
            f"<div class='mhead'>{big}<div><b class='code'>{E(m['code'])}</b> <span class='mname'>{E(m['name'])}</span><div class='kind'>{E(m['kind'])}</div></div></div>"
            f"<div class='mbody'><div class='mres'>{E(m['calc'])}</div>{notes}"
            f"<div class='mdata'>{chart}{('<div class=kvs>' + kvh + '</div>') if kvh else ''}</div>"
            f"{('<div class=more>' + ''.join(more) + '</div>') if more else ''}</div></div>")


def tile(T, m, grp):
    v = key_value(m['calc'], m['kvs']) if 'lt-n' not in m['lcls'] else 'n/a'
    if m['code'] == 'R1':
        v = next((val for lab, val in m['kvs'] if lab.startswith('Net debt ÷')), v)
    if m['code'] == 'M3':
        pick = [val for lab, val in m['kvs'] if lab.startswith(('Impairments', '(Impairments')) or lab.startswith('Diluted share change')]   # v4.7: the ratio and the share change, wherever they sit in the row
        vs = [val for val in (pick if len(pick) == 2 else [val for lab, val in m['kvs'][:2]]) if val.strip() not in ('–', '-', '')]
        v = ' / '.join(vs) if len(vs) == 2 else 'n/a'
    lc = next((c for c in m['lcls'].split() if c.startswith('lt-')), 'lt-na')
    sm = re.search(r'score (\d+(?:\.\d+)?) of 5', m['ltitle'])
    if sm:
        chip = sm.group(1)
    elif m['code'] == 'R1':
        chip = 'Fail' if lc == 'lt-r' else '待核验' if lc in ('lt-na','lt-q') else 'Pass'
    else:
        chip = '–'
    return (f"<a class='tile t-{grp}' href='#{T}-{m['code']}' title='{E(m['ltitle'])}. {E(m['name'])}: {E(m['calc'])}'>"
            f"<span class='tl'><span class='lt {lc} tsc'>{E(chip)}</span></span><span class='tc'>{E(m['code'])}</span><span class='tv'>{E(v) or '&nbsp;'}</span>"
            f"<span class='tn'>{E(SHORT.get(m['code'], m['name']))}</span></a>")


def company(co):
    T = co.get('id')
    summ = co.find('summary')
    body = co.find('div', class_='cobody')
    secs = body.find_all('section', recursive=False)
    ov = secs[0]
    left, right = ov.find('div', class_='top2').find_all('div', recursive=False)[:2]
    steps = {txt(li.find('span')): txt(li.find('b')) for li in left.find('ol').find_all('li')}
    flags = left.find('ul', class_='flags')
    res = steps.get('Result', '')
    label, _, rest = res.partition(' — ')
    rest = rest.split(' Detail:')[0]
    lines = [x.strip().rstrip('.') for x in re.split(r';\s+', rest) if x.strip()]
    _m = []                                   # keep 'Research line $X; price Y% below it' on one line (the split cut it in two)
    for x in lines:
        if _m and ((x.startswith('price ') and _m[-1].startswith('Research line')) or (x.startswith('check why') and _m[-1].startswith('Multiples disagree'))): _m[-1] += '; ' + x
        else: _m.append(x)
    lines = _m
    rescls = ' '.join(c for c in summ.find('span', class_='res').get('class', []) if c != 'res')

    # factor panels
    rf_sec = None; factors = []; nf = []
    for s in secs[1:]:
        h = s.find('h4'); head = txt(h)
        if 'blk-rf' in s.get('class', []): rf_sec = s
        elif 'blk-nf' in s.get('class', []): nf.append(s)
        else: factors.append(s)

    # red flags
    rf_head = txt(rf_sec.find('p', class_='note')) if rf_sec else ''
    rf_bad = rf_head.startswith('Red flag found')
    flagged = [x.strip() for x in rf_head.removeprefix('Red flag found:').split('→')[0].split(';')] if rf_bad else []
    ROWKEY = {'8-K Item 4.02': '8-K Item 4.02', 'Material weakness': 'Internal control', 'SEC AAER': 'SEC AAER',
              'Restatement to correct an error': 'Restatement to correct an error', 'Modified audit opinion': 'Modified audit opinion',
              'Accounting regulator finding': 'Accounting regulator finding'}
    rowflags = [v for f in flagged for k, v in ROWKEY.items() if f.startswith(k)]
    rfrows = []
    for tr in (rf_sec.find('tbody').find_all('tr') if rf_sec and rf_sec.find('tbody') else []):
        a, b, c = tr.find_all('td')
        res_t = txt(b); clean = res_t in ('None found', 'No') or (res_t.startswith('Management: effective') and 'material weakness' not in res_t.lower()) or res_t.startswith('Not applicable')
        link = c.find('a')
        how = '' if (link and len(txt(c)) == len(txt(link))) else txt(c)
        is_flag = any(txt(a).startswith(k) for k in rowflags)
        st = 'bad' if is_flag else ('ok' if clean else ('warn' if res_t.startswith('Not a red flag: the misconduct ended') else 'info'))
        rfrows.append(f"<div class='rfrow {st}'><span class='lt {dict(ok='lt-g', info='lt-na', bad='lt-r', warn='lt-y')[st]}' title='{dict(ok='clean', info='not a red flag under the rule; shown for information', bad='red flag', warn='past issue outside the horizon: highlighted, not a red flag')[st]}'>{dict(ok='✓', info='–', bad='✗', warn='!')[st]}</span>"
                      f"<div><b>{E(txt(a))}</b> <span class='rfres'>{E(res_t)}</span>{(' <span class=src>' + str(link) + '</span>') if link else ''}"
                      f"{('<details' + (' open' if st in ('bad', 'warn') else '') + '><summary>How checked</summary><p>' + E(how) + '</p></details>') if how else ''}</div></div>")

    # tiles + panels
    groups = []; panels = []
    for s in factors:
        h = s.find('h4'); hl = h.find('span'); head = txt(h).replace(txt(hl) if hl else '', '').strip()
        grp = PANEL.get(head, 'rk')
        rows = [parse_row(tr) for tr in s.find('table', class_='mt').find('tbody').find_all('tr', recursive=False)]
        favgs = [txt(d) for d in s.find_all('div', class_='favg')]
        ceo = s.find('div', class_='ceo-note')
        peers = s.find('details', class_='ev', recursive=False)
        drop = (); sub = ''
        if head == 'Industry':
            g = next((v for l, v in rows[0]['kvs'] if l in ('Group', 'Peer group')), '')
            n = next((v for l, v in rows[0]['kvs'] if l in ('Companies with a value', 'Peers with a value')), '')
            sub = f"<div class='psub'>Group: <b>{E(g)}</b>{(' · companies with a value: ' + E(n)) if n else ''}</div>"
            drop = ('Group', 'Companies with a value', 'Peer group', 'Peers with a value')
        calcline = next((f.split(' = ', 1)[1] for f in favgs if not f.startswith('Missing')), '')
        if head == 'Financial risk gate' and rows and not calcline:   # no average line: summarise the gate for the collapsed header
            kv = dict(rows[0]['kvs'])
            nd = next((v for l, v in kv.items() if l.startswith('Net debt ÷')), '')
            ic = next((v for l, v in kv.items() if l.startswith('Operating income ÷')), '')
            calcline = ' · '.join(x for x in [rows[0]['calc'], ('net debt ÷ EBITDA ' + nd) if nd else '', ('interest cover ' + ic) if ic else ''] if x)
        missing = [f for f in favgs if f.startswith('Missing')]
        hlh = str(hl) if hl else ''
        panels.append(f"<details class='blk blk-{grp} fold' open><summary><div class='phead'><h4>{E(head)} {hlh}</h4>{('<span class=pcalc>' + E(calcline) + '</span>') if calcline else ''}</div></summary>{sub}"
                      f"{str(ceo) if ceo else ''}{''.join(render_row(T, m, drop) for m in rows)}"
                      f"{''.join('<div class=favg>' + E(x) + '</div>' for x in missing)}{str(peers) if peers else ''}</details>")
        groups.append(f"<div class='tg t-{grp}'><div class='tgh'>{E(head if head != 'Financial risk gate' else 'Checks')} {hlh.replace('wide', '') if head != 'Financial risk gate' else ''}</div><div class='tiles'>"
                      + ''.join(tile(T, m, grp) for m in rows)
                      + (f"<a class='tile t-rf' href='#{T}-rf' title='{E(rf_head)}'><span class='tl'><span class='lt {'lt-r' if rf_bad else 'lt-g'} tsc'>{'Fail' if rf_bad else 'Pass'}</span></span><span class='tc'>RF</span><span class='tv'>{'Found' if rf_bad else ('<span class=\"rfwarn\">Past AAER</span>' if 'past SEC enforcement' in rf_head else 'None')}</span><span class='tn'>Accounting red flags</span></a>" if head == 'Financial risk gate' else '')
                      + "</div></div>")

    # info + perimeter, folded
    folds = []
    for s in nf:
        h = s.find('h4'); head = txt(h); h.decompose()
        if head.startswith('Shown'):
            cells = {txt(r.find_all('td')[0]): txt(r.find_all('td')[1]) for r in s.find_all('tr')}
            au = cells.get('Auditor changes, last 5 years', ''); cf = cells.get('CFO departures, last 5 years', ''); dc = cells.get('Share classes with different votes', '')
            ncf = len(re.findall(r'(?:^|; )\d{4}-\d{2}(?:-\d{2})? ·', cf))
            line = f"Auditor changes: {'none' if au in ('None', '') else 'yes'} · CFO departures: {ncf if cf not in ('None', '') else 'none'} · share classes with different votes: {'yes' if dc.startswith('Yes') else 'no'}"
            folds.append(f"<details class='blk blk-nf fold'><summary><h4>Shown for information</h4><span class='fline'>{E(line)}</span></summary>{s.decode_contents()}</details>")
        else:
            note = txt(s.find('p', class_='note'))
            first = note.split('. ')[0] + '.'
            nflag = len(s.find('table').find('tbody').find_all('tr')) if s.find('table') else 0
            ndeal = len(s.find('details').find_all('li')) if s.find('details') and 'Deals' in txt(s.find('details').find('summary')) else 0
            rep = any('repaired' in txt(d.find('summary')) for d in s.find_all('details'))
            cut = 'current perimeter' in first
            line = f"{'' if cut else first + ' · '}{nflag} automatic flag{'s' if nflag != 1 else ''} · {ndeal} deal{'s' if ndeal != 1 else ''} listed{' · data repaired from filings' if rep else ''}"
            folds.append(f"<details class='blk blk-nf fold'{' open' if cut else ''}><summary><h4>Perimeter and data{' <span class=cut>window cut by a deal</span>' if cut else ''}</h4><span class='fline'>{E(line)}</span></summary>{s.decode_contents()}</details>")

    fl = (f"<div class='flagsx'><b>Flags</b>{str(flags)}</div>") if flags else ''
    rcard = (f"<div class='rcard'><span class='res {rescls}'>{E(label)}</span><ul class='rlines'>{''.join('<li>' + E(x) + '</li>' for x in lines[:6])}</ul>{fl}</div>")
    right_h = right.decode_contents()
    return (f"<details class='co' id='{T}'>{str(summ)}<div class='cobody'>"
            f"<details class='blk blk-ov fold' open><summary><div class='phead'><h4>Result</h4><span class='pcalc fl-closed'><span class='res {rescls}'>{E(label)}</span> {E(lines[0]) if lines else ''}</span></div></summary>"
            f"<div class='top2'><div>{rcard}<h4>Scorecard</h4><div class='scard'>{''.join(groups)}</div>"
            f"<p class='cap'>Click a tile to jump to its row. Hover for the arithmetic.</p></div><div>{right_h}</div></div></details>"
            f"<details class='blk blk-rf fold' open id='{T}-rf'><summary><div class='phead'><h4>Accounting red flags</h4><span class='pcalc'>{E(rf_head)}</span></div></summary>{''.join(rfrows)}</details>"
            f"{''.join(panels)}{''.join(folds)}</div></details>")


CSS = """
.big.lt{font-size:15px}.mrow{display:grid;grid-template-columns:220px 1fr;gap:6px 18px;background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin:10px 0}
.mhead{display:flex;gap:10px;align-items:flex-start}.mhead .code{font-size:15px}.mname{font-weight:600}.mhead .kind{font-size:10.5px;color:var(--ink3);text-transform:uppercase;letter-spacing:.05em;margin-top:2px}
.mres{font-size:15px;font-weight:650;line-height:1.4}.mnote{margin:4px 0 0;font-size:13px;color:var(--ink2)}
.mdata{display:flex;flex-wrap:wrap;gap:8px 28px;align-items:flex-start;margin-top:8px}
.kvs{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:2px 22px;flex:1;min-width:220px}
.kv2{display:flex;justify-content:space-between;gap:10px;border-bottom:1px dashed var(--grid);padding:3px 0;font-size:13px}.kv2 span{color:var(--ink2)}.kv2 .abbr{text-decoration:underline dotted var(--ink3);text-underline-offset:3px;cursor:help}.kv2 b{font-weight:500;font-variant-numeric:tabular-nums;text-align:right}
.more{display:flex;flex-wrap:wrap;gap:4px 18px;margin-top:8px;font-size:12.5px}.more details>summary{cursor:pointer;color:var(--acc)}.more details[open]{flex-basis:100%}
.more ul{margin:6px 0;padding-left:18px;font-size:12.5px}.rtxt{margin:6px 0;color:var(--ink2);font-size:12.5px}
.kvl2{padding:6px 0;border-bottom:1px dashed var(--grid);font-size:12.5px}.kvl2 span{color:var(--ink2);display:block}.kvl2 div{color:var(--ink)}
.sp{margin:0}.sp figcaption{font-size:11.5px;color:var(--ink3)}.spark{display:block;overflow:visible}
.sp-bar{fill:var(--k);opacity:.55}.sp-neg{opacity:.3}.sp-zero{stroke:var(--line)}.sp-med{stroke:var(--ink2);stroke-dasharray:3 3;stroke-width:1.2}
.sp-v{font-size:9.5px;fill:var(--ink2);paint-order:stroke;stroke:var(--panel);stroke-width:3px;stroke-linejoin:round;text-anchor:middle;font-variant-numeric:tabular-nums}.sp-y{font-size:9.5px;fill:var(--ink3);text-anchor:middle}
.phead{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 14px}.phead h4{margin-bottom:4px}.pcalc{font-size:12.5px;color:var(--ink2)}.psub{font-size:13px;color:var(--ink2);margin:0 0 4px}
.rcard{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px 12px}.rcard .res{font-size:13px}
.rlines{margin:8px 0 0;padding-left:18px;font-size:13.5px}.rlines li{margin:2px 0}.flagsx{margin-top:8px;font-size:12.5px}.flagsx ul{margin:2px 0 0;padding-left:18px}
.scard{display:flex;flex-direction:column;gap:8px}.tg{border-left:4px solid var(--k);padding-left:8px}.tgh{font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--k);margin-bottom:4px}
.t-bu{--k:var(--bk-bu)}.t-in{--k:var(--bk-in)}.t-ma{--k:var(--bk-ma)}.t-rk{--k:var(--bk-rk)}.t-rf{--k:var(--bk-rf)}
.tiles{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px}
.tile{display:grid;grid-template-columns:auto 1fr;grid-template-areas:'l c' 'v v' 'n n';gap:0 6px;align-items:center;background:var(--panel);border:1px solid var(--line);border-top:3px solid var(--k);border-radius:6px;padding:5px 7px;color:var(--ink);text-decoration:none}
.tile:hover{border-color:var(--k);text-decoration:none}.tl{grid-area:l}.lt.tsc{min-width:24px;padding:0 6px;font-weight:700;font-size:13px;font-variant-numeric:tabular-nums}.tc{grid-area:c;font-weight:700;font-size:12px;color:var(--k)}.tv{grid-area:v;font-size:15px;font-weight:650;font-variant-numeric:tabular-nums;line-height:1.25}.tn{grid-area:n;font-size:11px;color:var(--ink3);line-height:1.2}
.rfrow{display:flex;gap:10px;align-items:flex-start;background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px 12px;margin:6px 0;font-size:13.5px}
.rfrow.info{color:var(--ink2)}.rfrow.bad{border-color:var(--lr);background:var(--lr-t)}.rfrow.warn{border-color:var(--ly);background:var(--ly-t)}.rfwarn{background:var(--ly-t);border-left:3px solid var(--ly);padding:0 5px;border-radius:3px}.flags li.warn{background:var(--ly-t);border-left:3px solid var(--ly);padding:2px 6px;border-radius:3px;list-style:none;margin-left:-18px}.rfrow.warn .rfres{color:var(--ink)}.rfres{color:var(--ink2)}.rfrow.bad .rfres{color:var(--ink)}.rfrow details>summary{cursor:pointer;color:var(--acc);font-size:12.5px}.rfrow details p{margin:4px 0;font-size:12.5px;color:var(--ink2)}
details.fold>summary{cursor:pointer;list-style:none;padding:2px 0}details.fold>summary::-webkit-details-marker{display:none}details.fold>summary h4{display:inline-block;margin:10px 0 2px}
details.fold>summary h4:before{content:'▸ ';color:var(--ink3)}details.fold[open]>summary h4:before{content:'▾ '}.fline{display:block;font-size:13px;color:var(--ink2);margin-bottom:6px}
details.fold>summary .phead h4{margin:10px 0 4px}details.fold[open]>summary .fl-closed{display:none}.fl-closed .res{font-size:12px;margin-right:4px}details.fold:not([open]){padding-bottom:4px}
.cut{font-size:11px;font-weight:600;text-transform:none;letter-spacing:0;color:var(--ly);background:var(--ly-t);border:1px solid var(--ly);border-radius:4px;padding:1px 6px;margin-left:6px}
.intro{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 16px;font-size:14px}.intro ol{margin:6px 0;padding-left:20px}
@media (max-width:820px){.mrow{grid-template-columns:1fr}.tiles{grid-template-columns:repeat(2,minmax(0,1fr))}.top2>div{min-width:0}.top2 table,.blk table{display:block;overflow-x:auto;max-width:100%}}
.top2>div{min-width:0}.mrow>*{min-width:0}.kvs{min-width:0}
@media (max-width:820px){.kvs{grid-template-columns:1fr}.spark{max-width:100%;height:auto}}
"""

JS_OPEN = """<script>
document.addEventListener('click', function (e) {
  var a = e.target.closest && e.target.closest('a[href^="#"]');
  if (!a) return;
  var el = document.getElementById(decodeURIComponent(a.getAttribute('href').slice(1)));
  if (!el) return;
  for (var d = el; d; d = d.parentElement) { if (d.tagName === 'DETAILS') d.open = true; }
  if (el.tagName === 'DETAILS') el.open = true;
  e.preventDefault(); el.scrollIntoView({behavior: 'smooth', block: 'start'}); history.replaceState(null, '', '#' + el.id);
});
</script>"""

CO_RE = re.compile(r"<details class='co' id='([^']+)'>.*?</div></details>", re.S)


def redesign(page):
    RULES.clear()
    def one(mt):
        co = BeautifulSoup(mt.group(0), 'html.parser').find('details')
        return company(co)
    page, n = CO_RE.subn(one, page)
    order = 'BIMR'
    rules_html = ''.join(f"<div class='kvl2'><span><b>{E(c)}</b> {E(nm)}</span><div>{E(r)}</div></div>"
                         for c, (nm, r) in sorted(RULES.items(), key=lambda x: (order.index(x[0][0]) if x[0][0] in order else 9, x[0])))
    box = (f"<details class='ev rules1'><summary>How each measure is set (each rule listed once; also behind the Rule link in each row)</summary>{rules_html}</details>")
    page = page.replace('<div class="tools">', box + '<div class="tools">', 1)
    page = page.replace('</style>', CSS + '</style>', 1)
    page = page.replace('</body>', JS_OPEN + '</body>', 1)
    return page, n
