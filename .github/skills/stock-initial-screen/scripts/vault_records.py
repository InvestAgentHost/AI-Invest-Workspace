#!/usr/bin/env python3
"""Screening records (初筛记录) in the Obsidian vault — company initial screener engine v4.3.

One permanent note per company that has ever been screened, in `08 Screener/初筛记录/` of the vault
("<Company> - 初筛记录.md"). The frontmatter holds the latest state (Bases reads only frontmatter);
the body holds a history table, newest row first, one row per run. The screener writes only its own
fields; it never changes the user's fields (our_decision, our_reason, our_reopen_if, our_check_date)
or the "Your notes" section. Vault rule: 写入规则 20 in the vault's CLAUDE.md.

  python3 vault_records.py snapshot RUN
        -> RUN/snapshot.json from RUN/page_data.json + RUN/config.json (after `screener.py build`)
  python3 vault_records.py snapshot-html PAGE.html OUT.json --as-of YYYY-MM-DD
        -> the same snapshot rebuilt from a delivered v4.x HTML page (backfill of runs made before v4.3)
  python3 vault_records.py read RUN NOTES_DIR
        -> RUN/prior_records.json: the frontmatter of the existing notes for the run's tickers
  python3 vault_records.py compare RUN [--baseline SNAPSHOT.json]
        -> RUN/reopen.json: for each company, what changed since its last record, the cause of each change,
           and whether its reopen condition is met (status Look again; otherwise No action; the weekly check sets Check now). --baseline = the previous run rebuilt under the new rules
           (needed only when the rules version changed; it separates the rules effect from everything else)
  python3 vault_records.py write RUN NOTES_DIR --run-file NAME --industry 航空航天 [--vault VAULT_ROOT] [--snapshot FILE] [--note TEXT]
        -> creates or updates one note per company in NOTES_DIR (a staged copy of the vault folder;
           commit the changed files back with an mtime guard)

stdlib only.
"""
import json, os, re, sys, glob, datetime, argparse

ENGINE = 'v4.7.2'   # the version of this script (writes the records); the scoring engine comes from run_meta.json
LIGHT = {'g': 'green', 'y': 'yellow', 'r': 'red', 'range': 'grey', 'q': 'grey', 'na': 'not scored'}
SYMBOL = {'green': '✓', 'yellow': '◐', 'red': '✗', 'grey': '?', 'not scored': '–', None: '–', '': '–'}
DIRW = {'cheaper': 'getting cheaper', 'steady': 'steady', 'dearer': 'getting dearer'}
# reopen_status values (vault rule 20; renamed by the user on 2026-10-22 from closed / due / triggered so each says what to do)
NO_ACTION, CHECK_NOW, LOOK = 'No action', 'Check now', 'Look again'
RANK = {'Not now': 0, 'Research at lower price': 1, 'Quick look': 1, 'Research now': 2}
REASONS = {   # screen_reason (closed list, vault rule 20) -> what the label means
    'good-cheap': 'Research now',
    'average-cheap': 'Quick look',
    'good-not-cheap': 'Research at lower price',
    'average-not-cheap': 'Not now: average business, multiples not low in their own history',
    'weak-business': 'Not now: weak business',
    'too-early': 'Not now: too early (short history after a deal, or a missing measure decides the Business light)',
    'red-flag': 'Not now: accounting red flag',
    'out-of-scope': 'Skipped sector (bank, insurer, asset manager, REIT, lessor, SPAC, fund, trust)',
}
SCREENER_KEYS = ['type', '生成方式', '核验状态', '来源说明', '行业', '更新日期', 'company', 'ticker', 'group', 'currency',
                 'first_screened', 'last_screened', 'rules_version', 'run_file', 'screener_label', 'screen_reason', 'reason_line',
                 'business_light', 'industry_light', 'management_light', 'ceo_tag', 'flags', 'median_pct', 'direction',
                 'price_at_screen', 'price_date', 'research_line', 'latest_fy', 'lead_fy', 'b1_latest', 'b1_median', 'b4_latest',
                 'b4_median', 'measure_scores', 'relook', 'reopen_if', 'next_check', 'next_check_why', 'reopen_status', 'reopen_why',
                 'last_price_check', 'last_price', 'decision_page']
USER_KEYS = ['our_decision', 'our_reason', 'our_reopen_if', 'our_check_date']
NOTE_SUFFIX = ' - 初筛记录.md'
M_LATEST = ('<!-- screener:latest:start -->', '<!-- screener:latest:end -->')
M_HISTORY = '<!-- screener:history -->'
HIST_HEAD = ('| Run | Rules | Label | B · I · M | Median pct | Direction | Price / research line | B1, B4: latest year vs median | Your decision then | Changed since last run (cause) |\n'
             '|---|---|---|---|---|---|---|---|---|---|')

# ---------------------------------------------------------------- small helpers
MONTHS = {m: i for i, m in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'], 1)}
def relkey(s):
    """A re-look signal reduced to what it is about, so a reworded signal from an older record matches:
    a CEO change -> 'ceo:YYYY-MM'; a deal -> 'deal:' + the first word of the deal name."""
    s = str(s).strip(); low = s.lower()
    if 'ceo' in low:
        m = re.search(r'(\d{4})-(\d{2})', s)
        if m: return f"ceo:{m.group(1)}-{m.group(2)}"
        m = re.search(r'([a-z]{3})[a-z]*\.? (\d{4})', low)
        if m and m.group(1) in MONTHS: return f"ceo:{m.group(2)}-{MONTHS[m.group(1)]:02d}"
        return 'ceo:' + low
    body = re.sub(r'^business changing:\s*', '', low)
    w = re.findall(r'[a-z0-9]+', body)
    return 'deal:' + (w[0] if w else body)

def ordn(n): return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"
def sym(cur): return {'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥'}.get(cur or '', (cur or '') + ' ')
def money(x, cur):
    return '–' if x in (None, '') else f"{sym(cur)}{float(x):,.2f}"
def pctx(x):
    return '–' if x in (None, '') else f"{float(x):.1f}%"
def d_(s):
    try: return datetime.date.fromisoformat(str(s)[:10])
    except Exception: return None
def add_years(d, n):
    try: return d.replace(year=d.year + n)
    except ValueError: return d.replace(year=d.year + n, day=28)

def screen_reason(label, kind):
    if label == 'Research now': return 'good-cheap'
    if label == 'Quick look': return 'average-cheap'
    if label == 'Research at lower price': return 'good-not-cheap'
    return {'average': 'average-not-cheap', 'weak': 'weak-business', 'early': 'too-early', 'redflag': 'red-flag',
            'scope': 'out-of-scope'}.get(kind, 'average-not-cheap')

def kind_from_lines(label, lines):
    if label in ('Research now', 'Research at lower price'): return 'good'
    if label == 'Quick look': return 'average'
    first = (lines or [''])[0]
    for pre, k in (('Accounting red flag', 'redflag'), ('Weak business', 'weak'), ('Too early', 'early'), ('Average business', 'average')):
        if first.startswith(pre): return k
    return 'average'

# ---------------------------------------------------------------- snapshot from page_data.json (v4.3 runs)
def _series_from_inputs(meas, label_start):
    for k, v in meas.get('inputs') or []:
        if k.startswith(label_start):
            out = {}
            for fy, val in re.findall(r'FY(\d{2}) (-?[\d.]+)%', v): out[2000 + int(fy)] = float(val)
            return out
    return {}

def snapshot_from_page_data(run):
    D = json.load(open(os.path.join(run, 'page_data.json')))
    C = json.load(open(os.path.join(run, 'config.json')))
    mp = os.path.join(run, 'run_meta.json')   # v4.7.2: written by screener.py build; older runs have none
    META = json.load(open(mp)) if os.path.exists(mp) else {}
    rules_v = META.get('rules_version') or C.get('rules_version')
    if META and C.get('rules_version') and C['rules_version'] != META['rules_version']:
        sys.exit(f"{run}: config.json says rules_version {C['rules_version']}, but page_data.json was built under rules {META['rules_version']}")
    snap = {}
    for t, c in D.items():
        res, mx, pe = c['result'], c.get('mult') or {}, c.get('pe') or {}
        meas = {m['code']: m for m in c['measures']}
        lead = c.get('lead') or {}
        if not lead:   # older page_data: rebuild from the B1/B4 inputs (whole-percent precision)
            b1s = _series_from_inputs(meas.get('B1', {}), 'ROIC by year'); L = (c.get('window') or {}).get('L')
            lead = dict(fy=L, b1Latest=(b1s.get(L) / 100 if L in b1s else None), b1Med=None, b4Latest=None, b4Med=None, fyEnd=None)
        lines = res.get('lines') or []
        rv = None
        m_ = re.search(r'Revisit after FY(\d{4})', ' '.join(lines))
        if m_: rv = int(m_.group(1))
        snap[t] = dict(
            ticker=t, name=c.get('name', t), group=c.get('group', ''), cur=mx.get('cur') or pe.get('cur') or c.get('cur'),
            as_of=C.get('as_of'), rules_version=rules_v, engine=META.get('engine'),
            label=res['cat'], kind=res.get('kind'), lines=lines,
            lights=dict(business=LIGHT.get(c['business']['light'], c['business']['light']), industry=LIGHT.get(c['industry']['light'], c['industry']['light']),
                        management=LIGHT.get(c['management']['light'], c['management']['light'])),
            ceo_tag=(c.get('ceo') or {}).get('label') or '', flags=c.get('flags') or [],
            redflags=[r['label'] for r in c.get('redflags') or []], relook=res.get('relook') or [],
            median_pct=mx.get('pct') if mx.get('band') else None, direction=DIRW.get(mx.get('direction'), mx.get('direction') or ''),
            price=mx.get('price') or pe.get('price'), price_date=pe.get('price_date') or pe.get('to') or C.get('as_of'), research_line=mx.get('trigger'),
            lead=dict(fy=lead.get('fy'), b1_latest=_p(lead.get('b1Latest')), b1_median=_p(lead.get('b1Med')),
                      b4_latest=_p(lead.get('b4Latest')), b4_median=_p(lead.get('b4Med'))),
            latest_fy=(c.get('window') or {}).get('L'), fy_end=lead.get('fyEnd'), revisit_fy=rv,
            scores={k: v for k, v in (c.get('scores') or {}).items() if k != 'R1'},
            precision='exact')
    return snap

def _p(x):   # fraction -> percent with one decimal
    return None if x is None else round(float(x) * 100, 1)

# ---------------------------------------------------------------- snapshot from a delivered HTML page (backfill)
def snapshot_from_html(path, as_of, fy_end_over=None):
    from bs4 import BeautifulSoup
    s = open(path, encoding='utf-8').read(); soup = BeautifulSoup(s, 'html.parser')
    sub = soup.find(class_='sub').get_text(' ', strip=True) if soup.find(class_='sub') else ''
    rv = (re.search(r'rules version (\S+)', sub) or [None, None])[1]
    eng = (re.search(r'\(engine (v[\d.]+)\)', sub) or [None, None])[1]
    pdate = (re.search(r'prices and P/E to (\d{4}-\d{2}-\d{2})', sub) or [None, None])[1]
    LT = {'lt-g': 'green', 'lt-y': 'yellow', 'lt-r': 'red', 'lt-q': 'grey', 'lt-na': 'not scored'}
    snap = {}
    for r in soup.find('table', class_='ov').find_all('tr')[1:]:
        a = r.find('a'); t = a['data-open']; tds = r.find_all('td')
        label = r.find('span', class_='res').get_text(strip=True)
        lines = [d.get_text(' ', strip=True) for d in r.find(class_='rwhy').find_all('div', recursive=False)] if r.find(class_='rwhy') else []
        lights = []
        for td in tds[3:6]:
            sp = td.find('span', class_='lt'); cl = [x for x in (sp.get('class') or []) if x in LT] if sp else []
            lights.append(LT[cl[0]] if cl else '')
        ceo = r.find('span', class_='ceo')
        pct = r.find('span', class_='pct'); dr = r.find('span', class_=re.compile(r'\bdir\b'))
        flags_txt = tds[-1].get_text(' | ', strip=True)
        sec = soup.find(id=t); stext = sec.get_text('\n', strip=True)
        g = re.search(re.escape(t) + r' · ([^\n]+)', stext)
        m_ = re.search(r'research line ([^\d\s-]*\s?)([\d,]+(?:\.\d+)?) vs price ([^\d\s-]*\s?)([\d,]+(?:\.\d+)?)', stext)
        rl = float(m_.group(2).replace(',', '')) if m_ else None; px = float(m_.group(4).replace(',', '')) if m_ else None
        if px is None:
            m2 = re.search(r'· price ([^\d\s-]*\s?)([\d,]+(?:\.\d+)?)', stext)
            if m2: px = float(m2.group(2).replace(',', ''))
        symb = (m_.group(3) if m_ else '').strip()
        cur = {'$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY'}.get(symb) or (symb or ('JPY' if t.endswith('.T') else 'USD'))
        scores = {}
        for code in ('B1', 'B2', 'B3', 'B4', 'I1', 'I2', 'I3', 'M1', 'M2', 'M3'):
            row = sec.find(id=f'{t}-{code}')
            lt = row.find('span', class_='lt') if row else None
            mm = re.search(r'score (\d) of 5', lt.get('title', '')) if lt else None
            scores[code] = int(mm.group(1)) if mm else None
        def lead_of(code):
            row = sec.find(id=f'{t}-{code}')
            if not row: return None, None, None
            med = re.search(r'Median (-?[\d.]+)%', row.find(class_='mres').get_text(' ', strip=True)) if row.find(class_='mres') else None
            bars = [re.match(r'FY(\d{2}): (-?[\d.]+)%', x.get_text(strip=True)) for x in row.select('svg.spark g > title')]
            bars = [b for b in bars if b]
            medv = float(med.group(1)) if med else None
            if not bars:   # short series: no bar chart; read the 'ROIC by year FY23 20%, ...' input line (whole %)
                kv = re.search(r'ROIC by year[^\n]*?((?:FY\d{2} -?[\d.]+%,? ?)+)', row.get_text('\n', strip=True).replace('\n', ' '))
                pairs = re.findall(r'FY(\d{2}) (-?[\d.]+)%', kv.group(1)) if kv else []
                if not pairs: return None, medv, None
                return float(pairs[-1][1]), medv, 2000 + int(pairs[-1][0])
            return float(bars[-1].group(2)), medv, 2000 + int(bars[-1].group(1))
        b1l, b1m, fy1 = lead_of('B1'); b4l, b4m, fy4 = lead_of('B4')
        fe = re.search(r'Internal control at FY-end (\d{4}-\d{2}-\d{2})', stext)
        fe_src = 'page' if fe else ''
        if not fe and t in (fy_end_over or {}): fe_src = (fy_end_over[t].get('source') or 'override'); fe = fy_end_over[t]['date']
        else: fe = fe.group(1) if fe else None
        pd_ = re.search(r'Daily trailing GAAP P/E from .*?, \d{4}-\d{2}-\d{2} to (\d{4}-\d{2}-\d{2})', stext)
        rvf = re.search(r'Revisit after FY(\d{4})', ' '.join(lines))
        kind = kind_from_lines(label, lines)
        relook = []
        for ln in lines:
            if ln.startswith('Re-look signal: '): relook = [x.strip() for x in ln[len('Re-look signal: '):].split(';')]
        rf = []
        if kind == 'redflag':
            rf = [x.strip() for x in re.sub(r'^Accounting red flag: ', '', lines[0]).replace('; revisit when resolved', '').split(',')]
        snap[t] = dict(
            ticker=t, name=a.get_text(strip=True), group=(g.group(1).strip() if g else ''), cur=cur,
            as_of=as_of, rules_version=rv, engine=eng, label=label, kind=kind, lines=lines,
            lights=dict(business=lights[0], industry=lights[1], management=lights[2]),
            ceo_tag=ceo.get_text(strip=True) if ceo else '', flags=[] if flags_txt in ('–', '') else [x for x in flags_txt.split(' | ') if x],
            redflags=rf, relook=relook,
            median_pct=int(re.match(r'\d+', pct.get_text(strip=True)).group()) if pct else None,
            direction=(dr.get_text(strip=True).lstrip('↓→↑ ').lower() if dr else ''),
            price=px, price_date=(pd_.group(1) if pd_ else pdate), research_line=rl,
            lead=dict(fy=fy1 or fy4, b1_latest=b1l, b1_median=b1m, b4_latest=b4l, b4_median=b4m),
            latest_fy=fy1 or fy4 or (d_(fe).year if d_(fe) else None), fy_end=fe, revisit_fy=int(rvf.group(1)) if rvf else None,
            scores=scores, precision='html', fy_end_source=fe_src)
    return snap

# ---------------------------------------------------------------- frontmatter (line-based, keeps every line it does not own)
def split_note(text):
    if not text.startswith('---'): return [], text
    end = text.find('\n---', 3)
    if end < 0: return [], text
    fm = text[4:end].split('\n') if text[3:4] == '\n' else text[3:end].split('\n')
    body = text[end + 4:]
    if body.startswith('\n'): body = body[1:]
    return fm, body

def fm_parse(lines):
    out, key = {}, None
    for ln in lines:
        m = re.match(r'^([^\s:#][^:]*):(?:\s(.*))?$', ln)
        if m:
            key = m.group(1).strip(); out[key] = _val((m.group(2) or '').strip())
        elif key and (ln.startswith(' ') or ln.startswith('-')):
            out[key] = (str(out[key]) + '\n' + ln) if out[key] not in (None, '') else ln
    return out

def _val(v):
    if v == '': return ''
    if v.startswith('"'):
        try: return json.loads(v)
        except Exception: return v.strip('"')
    if v.startswith("'") and v.endswith("'") and len(v) > 1: return v[1:-1].replace("''", "'")
    return v

def _yaml(v):
    if v is None or v == '': return ''
    if isinstance(v, bool): return 'true' if v else 'false'
    if isinstance(v, (int, float)): return f"{v:g}" if isinstance(v, float) else str(v)
    s = str(v)
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', s): return s
    if (s.strip() == s and not re.fullmatch(r'[\d.+-]+', s) and s.lower() not in ('true', 'false', 'null', 'yes', 'no', '~')
            and not re.match(r'[-?:,\[\]{}#&*!|>\'"%@`]', s) and ': ' not in s and ' #' not in s and not s.endswith(':') and '"' not in s and "'" not in s):
        return s
    return json.dumps(s, ensure_ascii=False)

def fm_set(lines, key, value, before=None):
    """Replace `key:` (and any continuation lines) or insert it before `before:` (else at the end)."""
    new = f"{key}: {_yaml(value)}".rstrip()
    i = next((k for k, ln in enumerate(lines) if re.match(rf'^{re.escape(key)}:(\s|$)', ln)), None)
    if i is not None:
        j = i + 1
        while j < len(lines) and (lines[j].startswith(' ') or lines[j].startswith('-')): j += 1
        lines[i:j] = [new]
    else:
        b = next((k for k, ln in enumerate(lines) if before and re.match(rf'^{re.escape(before)}:(\s|$)', ln)), None)
        lines.insert(b if b is not None else len(lines), new)
    return lines

# ---------------------------------------------------------------- reopen tests and next check
def fy_end_date(snap):
    return d_(snap.get('fy_end'))

def next_check(snap):
    """Date the next annual report should be out: fiscal year-end of the next year + 75 days; for too-early names the revisit year."""
    fe, L = fy_end_date(snap), snap.get('latest_fy')
    if fe and L:   # the fiscal year is named after the calendar year it ends in; align the year-end with the latest fiscal year
        fe = fe.replace(year=L) if not (fe.month == 2 and fe.day == 29) else fe.replace(year=L, day=28)
    asof = d_(snap.get('as_of')) or datetime.date.today()
    target = (snap.get('revisit_fy') if snap.get('reason') == 'too-early' and snap.get('revisit_fy') else None) or ((L + 1) if L else None)
    if fe and L and target:
        d = add_years(fe, target - L) + datetime.timedelta(days=75)
        while d < asof: d = add_years(d, 1); target += 1
        return d.isoformat(), f"FY{target} annual report: fiscal year ends {fe.strftime('%d %b')}, checked 75 days after"
    return add_years(asof, 1).isoformat(), 'fiscal year-end not on record: one year after this run'

def weak_codes(snap, factor='B'):
    return [k for k, v in (snap.get('scores') or {}).items() if k.startswith(factor) and isinstance(v, int) and v <= 2]

def reopen_text(snap):
    r = snap['reason']; cur = snap.get('cur')
    tail = '; or a new re-look signal (new CEO, deal above 25% of revenue)'
    if r in ('good-cheap', 'average-cheap'):
        return f"Not excluded: the label ({snap['label']}) already says spend research time now"
    if r == 'good-not-cheap':
        return (f"Price at or below the research line {money(snap.get('research_line'), cur)} (weekly price check), "
                f"or multiples getting cheaper, or the label becomes Research now on the next run") + tail
    if r == 'average-not-cheap':   # v4.7: say which light made the business 'average' (Business yellow, or Business green with Management red)
        if (snap.get('lights') or {}).get('business') == 'green':
            return 'Management light no longer red while the Business light stays green, or the median multiple percentile falls to the 33rd or below (Quick look), on the next run' + tail
        return 'Business light turns green with the Management light not red, or the median multiple percentile falls to the 33rd or below (Quick look), on the next run' + tail
    if r == 'weak-business':
        w = weak_codes(snap)
        return f"Business light no longer red, or a weak measure ({', '.join(w) or 'Business'}) scores higher, on the next run" + tail
    if r == 'too-early':
        if snap.get('revisit_fy'):
            return f"FY{snap['revisit_fy']} results reported (enough clean years): rerun; reopens when the label is no longer 'too early'" + tail
        return "The missing Business measure becomes available (a filed fact or a longer history): rerun; reopens when the Business light is no longer open" + tail
    if r == 'red-flag':
        return f"The red flag ({', '.join(snap.get('redflags') or []) or 'see the run page'}) is gone in the latest filing" + tail
    return 'Out of scope for this screen'

def leading_text(snap):
    ld = snap.get('lead') or {}
    def one(code):
        a, m = ld.get(f'{code.lower()}_latest'), ld.get(f'{code.lower()}_median')
        if a is None or m is None: return f"{code} –"
        return f"{code} {a:g}% vs {m:g}%"
    return f"FY{ld.get('fy') or '?'}: {one('B1')} · {one('B4')}"

# ---------------------------------------------------------------- compare a run with the records
SC_ORDER = ['B1', 'B2', 'B3', 'B4', 'I1', 'I2', 'I3', 'M1', 'M2', 'M3']
def scores_str(sc):
    return ' · '.join(f"{k} {sc.get(k) if sc.get(k) is not None else '–'}" for k in SC_ORDER)
def scores_parse(s):
    out = {}
    for k, v in re.findall(r'([BIM]\d) (\d|–)', str(s or '')): out[k] = int(v) if v.isdigit() else None
    return out

def diff(prev, now):
    """List of (what, before, now, cause) between a prior record (frontmatter dict) and a snapshot entry."""
    ch = []
    p_sc, n_sc = scores_parse(prev.get('measure_scores')), now.get('scores') or {}
    p_L = int(prev['latest_fy']) if str(prev.get('latest_fy') or '').isdigit() else None
    newyear = p_L is not None and now.get('latest_fy') and now['latest_fy'] != p_L
    def cause_for(codes):
        if newyear: return f"business: new fiscal year FY{now['latest_fy']} in the data"
        if any(c.startswith('M') for c in codes): return 'filing: new proxy, Form 4 or pay vote; check the fact file'
        if any(c.startswith('I') for c in codes): return 'peers: peer data changed; check the peer table'
        return 'data: revision or new filing with no new fiscal year; check raw data against the last archive'
    moved = [k for k in SC_ORDER if p_sc and p_sc.get(k) != n_sc.get(k)]
    if moved:
        ch.append(('measures', ', '.join(f"{k} {p_sc.get(k)}" for k in moved), ', '.join(f"{k} {n_sc.get(k)}" for k in moved), cause_for(moved)))
    for f in ('business', 'industry', 'management'):
        a, b = prev.get(f'{f}_light'), now['lights'].get(f)
        if a and b and a != b: ch.append((f'{f.capitalize()} light', a, b, cause_for([k for k in moved if k[0] == f[0].upper()]) if moved else ('business: new fiscal year' if newyear else 'data: light moved with no measure change; check')))
    pp, np_ = prev.get('median_pct'), now.get('median_pct')
    try: pp = int(pp) if pp not in (None, '') else None
    except ValueError: pp = None
    if pp != np_: ch.append(('median multiple percentile', ordn(pp) if pp is not None else 'n/a', ordn(np_) if np_ is not None else 'n/a', 'price: multiples moved with price and trailing earnings' if not newyear else 'price and business: new fiscal-year earnings and price'))
    if (prev.get('direction') or '') != (now.get('direction') or ''): ch.append(('direction', prev.get('direction') or '–', now.get('direction') or '–', 'price: multiples against their own past'))
    p_rf, n_rf = str(prev.get('flags') or ''), ' | '.join(now.get('flags') or [])
    if p_rf != n_rf and (p_rf or n_rf): ch.append(('flags', p_rf or 'none', n_rf or 'none', 'filing: new filing or perimeter change; check'))
    if (prev.get('ceo_tag') or '') != (now.get('ceo_tag') or '') and now.get('ceo_tag', '').startswith('New CEO'):
        ch.append(('CEO', prev.get('ceo_tag') or '–', now['ceo_tag'], 'business: CEO change (8-K Item 5.02)'))
    if prev.get('screener_label') != now['label']:
        causes = sorted({c[3].split(':')[0] for c in ch}) or ['no other change recorded: check']
        ch.insert(0, ('label', prev.get('screener_label'), now['label'], ', '.join(causes)))
    return ch

def reopen_test(prev, now, as_of):
    """Whether the prior record's reopen condition is met by this run. Returns (status, reasons)."""
    why = []; r = prev.get('screen_reason')
    pr, nr = RANK.get(prev.get('screener_label'), 0), RANK.get(now['label'], 0)
    if nr > pr: why.append(f"label improved: {prev.get('screener_label')} → {now['label']}")
    if r == 'good-not-cheap':
        if now.get('direction') == 'getting cheaper': why.append('multiples getting cheaper')
        try:
            if now.get('price') is not None and prev.get('research_line') not in (None, '') and float(now['price']) <= float(prev['research_line']):
                why.append(f"price {money(now['price'], now.get('cur'))} at or below the recorded research line {money(prev['research_line'], now.get('cur'))}")
        except ValueError: pass
    if r == 'average-not-cheap':   # v4.7 (user, 2026-10-23): reopens when the company now counts as a good business, whichever light made it average
        nb, nm = now['lights'].get('business'), now['lights'].get('management')
        if nb == 'green' and nm not in ('red', '', None):
            why.append(f"Management light now {nm}, Business light still green" if prev.get('business_light') == 'green' else f"Business light turned green, Management light {nm}")
        if now.get('median_pct') is not None and now['median_pct'] <= 33: why.append(f"median percentile {ordn(now['median_pct'])}, at or below the 33rd")
    if r == 'weak-business':
        if now['lights']['business'] not in ('red', ''): why.append(f"Business light now {now['lights']['business']}")
        p_sc = scores_parse(prev.get('measure_scores'))
        up = [k for k in SC_ORDER if k.startswith('B') and isinstance(p_sc.get(k), int) and p_sc[k] <= 2 and isinstance(now['scores'].get(k), int) and now['scores'][k] > p_sc[k]]
        if up: why.append('weak measure scored higher: ' + ', '.join(f"{k} {p_sc[k]} → {now['scores'][k]}" for k in up))
    if r == 'too-early' and now.get('kind') != 'early': why.append('no longer too early')
    if r == 'red-flag' and not now.get('redflags') and now.get('kind') != 'redflag': why.append('red flag no longer present')
    p_rel = set(relkey(x) for x in str(prev.get('relook') or '').split(';') if x.strip())   # v4.7.1: compare by meaning, not wording
    new_rel = [x for x in now.get('relook') or [] if relkey(x) not in p_rel]
    if new_rel: why.append('new re-look signal: ' + '; '.join(new_rel))
    ocd = d_(prev.get('our_check_date'))
    if ocd and ocd <= (d_(as_of) or datetime.date.today()): why.append(f"your check date {ocd.isoformat()} has passed: review your reopen condition")
    return (LOOK if why else NO_ACTION), why

def compare(run, baseline=None):
    snap = json.load(open(os.path.join(run, 'snapshot.json')))
    prior = json.load(open(os.path.join(run, 'prior_records.json'))) if os.path.exists(os.path.join(run, 'prior_records.json')) else {}
    base = json.load(open(baseline)) if baseline else {}
    items = []
    for t, now in snap.items():
        prev = prior.get(t)
        if not prev:
            items.append(dict(t=t, name=now['name'], first=True, before='', now=now['label'], status=NO_ACTION, why=[], changes=[])); continue
        rules_changed = (prev.get('rules_version') or '') != (now.get('rules_version') or '')
        changes = []
        if rules_changed and t in base:   # previous run rebuilt under the new rules: prior -> base is the rules effect
            b = dict(base[t]); b['reason'] = screen_reason(b['label'], b.get('kind'))
            changes += [(w, x, y, f"rules {prev.get('rules_version')} → {now.get('rules_version')}") for (w, x, y, _) in diff(prev, b)]
            pseudo = dict(prev); pseudo.update(screener_label=b['label'], measure_scores=scores_str(b['scores']), median_pct=b.get('median_pct'),
                                               direction=b.get('direction'), flags=' | '.join(b.get('flags') or []),
                                               **{f'{f}_light': b['lights'][f] for f in ('business', 'industry', 'management')})
            changes += diff(pseudo, now)
            changes.append(('rules version', prev.get('rules_version'), now.get('rules_version'), 'rules changed: effect separated with the rebuilt baseline'))
        else:
            changes += diff(prev, now)
            if rules_changed:
                changes.append(('rules version', prev.get('rules_version'), now.get('rules_version'),
                                'rules changed: rebuild the last archive under the new rules and pass it as --baseline to separate the rules effect'))
        status, why = reopen_test(prev, now, now.get('as_of'))
        # v4.7 guard: a reopen condition cannot be met when nothing moved since the record (McKesson, 23 Oct 2026). The user's own check date still counts.
        moved_px = False
        try:
            a_, b_ = prev.get('price_at_screen'), now.get('price')
            if a_ not in (None, '') and b_ is not None:
                a_, b_ = float(a_), float(b_); moved_px = abs(b_ - a_) > max(0.005, abs(a_) * 1e-5)   # the record stores 6 significant digits
        except ValueError: pass
        real = [c for c in changes if c[0] != 'rules version']   # a rules version alone is not a change in the company
        if status == LOOK and not real and not moved_px:
            own = [w for w in why if w.startswith('your check date')]
            cond = [w for w in why if not w.startswith('your check date')]
            if cond: why = own + ["screener condition (" + '; '.join(cond) + ") not counted: no change in label, lights, scores, percentile, price or flags since the record; check the record's reason"]
            status = LOOK if own else NO_ACTION
        items.append(dict(t=t, name=now['name'], first=False, before=prev.get('screener_label'), now=now['label'], status=status, why=why,
                          changes=[dict(what=a, before=b_, now=c, cause=d) for a, b_, c, d in changes],
                          our_decision=prev.get('our_decision') or '', our_reason=prev.get('our_reason') or '', our_reopen_if=prev.get('our_reopen_if') or ''))
    out = dict(as_of=next(iter(snap.values()))['as_of'] if snap else None, items=items)
    json.dump(out, open(os.path.join(run, 'reopen.json'), 'w'), ensure_ascii=False, indent=1)
    trig = [i for i in items if i['status'] == LOOK]
    print(f"compared {len(items)} companies: {sum(1 for i in items if i['first'])} first records, {len(trig)} Look again, "
          f"{sum(1 for i in items if i['changes'])} with changes")
    for i in trig: print(f"  LOOK AGAIN {i['t']}: {'; '.join(i['why'])}")
    return out

# ---------------------------------------------------------------- read existing notes
def scan_notes(notes_dir):
    by_t = {}
    for f in sorted(glob.glob(os.path.join(notes_dir, '*.md'))):
        fm, _ = split_note(open(f, encoding='utf-8').read())
        d = fm_parse(fm)
        if d.get('type') == '初筛记录' and d.get('ticker'): by_t[str(d['ticker'])] = dict(d, _file=os.path.basename(f))
    return by_t

def read(run, notes_dir):
    snap_p = os.path.join(run, 'snapshot.json')
    tick = set(json.load(open(snap_p))) if os.path.exists(snap_p) else set(json.load(open(os.path.join(run, 'config.json')))['companies'])
    allrec = scan_notes(notes_dir)
    pr = {t: v for t, v in allrec.items() if t in tick}
    json.dump(pr, open(os.path.join(run, 'prior_records.json'), 'w'), ensure_ascii=False, indent=1)
    print(f"{len(allrec)} screening records in the folder; {len(pr)} of the run's {len(tick)} companies have one")
    return pr

# ---------------------------------------------------------------- write notes
def safe_name(n): return re.sub(r'[\\/:*?"<>|#^\[\]]', '-', n).strip()

def latest_block(s):
    cur = s.get('cur')
    lines = [M_LATEST[0],
             f"**Latest: {s['label']}** ({s['as_of']}, rules {s.get('rules_version')}) — " + ' · '.join(s.get('lines') or []),
             '',
             f"- Lights: Business {SYMBOL.get(s['lights']['business'])} {s['lights']['business']} · Industry {SYMBOL.get(s['lights']['industry'])} {s['lights']['industry']} · "
             f"Management {SYMBOL.get(s['lights']['management'])} {s['lights']['management']}" + (f" ({s['ceo_tag']})" if s.get('ceo_tag') else ''),
             f"- Multiples: median {ordn(s['median_pct']) + ' percentile of their own history' if s.get('median_pct') is not None else 'not meaningful'}"
             + (f", {s['direction']}" if s.get('direction') else '') + f"; price {money(s.get('price'), cur)} on {s.get('price_date')}"
             + (f"; research line {money(s.get('research_line'), cur)}" if s.get('research_line') else ''),
             f"- Leading indicator (latest year against the window median): {leading_text(s)}",
             f"- Reopen if: {s['reopen_if']}",
             f"- Next check: {s['next_check']} ({s['next_check_why']})",
             f"- Status: **{s['reopen_status']}**" + (f" — {s['reopen_why']}" if s.get('reopen_why') else ''),
             M_LATEST[1]]
    return '\n'.join(lines)

def hist_row(s, change_txt, our_then):
    cur = s.get('cur'); L = s['lights']
    cells = [s['as_of'], s.get('rules_version') or '', s['label'] + (f": {s['lines'][0]}" if s.get('lines') and s['label'] == 'Not now' else ''),
             f"{SYMBOL.get(L['business'])} · {SYMBOL.get(L['industry'])} · {SYMBOL.get(L['management'])}",
             ordn(s['median_pct']) if s.get('median_pct') is not None else 'n/a', s.get('direction') or '–',
             f"{money(s.get('price'), cur)} / {money(s.get('research_line'), cur)}", leading_text(s), our_then or '–', change_txt or 'first record']
    return '| ' + ' | '.join(str(c).replace('|', '/').replace('\n', ' ') for c in cells) + ' |'

def new_note(s, fm_lines):
    title = f"# {s['name']} ({s['ticker']}) — 初筛记录"
    return ('---\n' + '\n'.join(fm_lines) + '\n---\n' + title + '\n\n'
            '> [!info] Screening record — AI 生成, 待核验. The company initial screener updates the frontmatter, the "Latest" block and adds one row to the history table on each run. '
            'It never changes your fields (`our_decision`, `our_reason`, `our_reopen_if`, `our_check_date`) or the "Your notes" section. '
            'A screener label is a research-priority call, not a buy or sell view (写入规则 20).\n\n'
            + latest_block(s) + '\n\n## Your notes\n\n\n## History\n\n' + M_HISTORY + '\n' + HIST_HEAD + '\n')

def write(run, notes_dir, run_file, industry, vault=None, snap_file=None, note_txt=''):
    snap = json.load(open(snap_file or os.path.join(run, 'snapshot.json')))
    rep_p = os.path.join(run, 'reopen.json')
    rep = {i['t']: i for i in json.load(open(rep_p))['items']} if os.path.exists(rep_p) else {}
    recs = scan_notes(notes_dir); today = datetime.date.today().isoformat(); written = []
    for t, s in snap.items():
        s = dict(s); s['reason'] = screen_reason(s['label'], s.get('kind'))
        s['reopen_if'] = reopen_text(s)
        s['next_check'], s['next_check_why'] = next_check(s)
        it = rep.get(t) or {}
        s['reopen_status'] = it.get('status') or NO_ACTION; s['reopen_why'] = '; '.join(it.get('why') or [])
        dp = ''
        if vault and os.path.exists(os.path.join(vault, '01 公司', s['name'], s['name'] + '.md')): dp = f"[[{s['name']}]]"
        src = (f"company-initial-screener rules {s.get('rules_version')}, scored by engine {s.get('engine') or 'not recorded'}, record written by vault_records {ENGINE}; run {run_file}; prices to {s.get('price_date')}"
               + ('; backfilled from the delivered HTML page: B1/B4 latest-year values are the page bar labels (whole % at 10% or more)' if s.get('precision') == 'html' else '')
               + (f"; fiscal year-end {s.get('fy_end')} from {s['fy_end_source']}" if s.get('fy_end_source') not in (None, '', 'page') else '')
               + (f"; {note_txt}" if note_txt else ''))
        vals = {'type': '初筛记录', '生成方式': 'AI 生成', '核验状态': '待核验', '来源说明': src, '行业': industry, '更新日期': today,
                'company': s['name'], 'ticker': t, 'group': s.get('group') or '', 'currency': s.get('cur') or '',
                'last_screened': s['as_of'], 'rules_version': s.get('rules_version') or '', 'run_file': run_file,
                'screener_label': s['label'], 'screen_reason': s['reason'], 'reason_line': '; '.join(s.get('lines') or []),
                'business_light': s['lights']['business'], 'industry_light': s['lights']['industry'], 'management_light': s['lights']['management'],
                'ceo_tag': s.get('ceo_tag') or '', 'flags': ' | '.join(s.get('flags') or []),
                'median_pct': s.get('median_pct'), 'direction': s.get('direction') or '', 'price_at_screen': s.get('price'), 'price_date': s.get('price_date'),
                'research_line': s.get('research_line'), 'latest_fy': s.get('latest_fy'), 'lead_fy': (s.get('lead') or {}).get('fy'),
                'b1_latest': (s.get('lead') or {}).get('b1_latest'), 'b1_median': (s.get('lead') or {}).get('b1_median'),
                'b4_latest': (s.get('lead') or {}).get('b4_latest'), 'b4_median': (s.get('lead') or {}).get('b4_median'),
                'measure_scores': scores_str(s.get('scores') or {}), 'relook': '; '.join(s.get('relook') or []),
                'reopen_if': s['reopen_if'], 'next_check': s['next_check'], 'next_check_why': s['next_check_why'],
                'reopen_status': s['reopen_status'], 'reopen_why': s['reopen_why'], 'decision_page': dp}
        ch = it.get('changes') or []
        cats = sorted({c['cause'].split(':')[0] for c in ch if c['what'] != 'label'})
        change_txt = ('; '.join(f"{c['what']} {c['before']} → {c['now']}" for c in ch) + (f" — cause: {', '.join(cats)} (detail in the run's reopen.json)" if cats else '')) if ch else ''
        if t in recs:
            path = os.path.join(notes_dir, recs[t]['_file']); text = open(path, encoding='utf-8').read()
            fm, body = split_note(text); prev = fm_parse(fm)
            if str(prev.get('last_screened')) == str(s['as_of']) and str(prev.get('run_file')) == run_file:
                print(f"skip {t}: this run is already recorded"); continue
            vals['first_screened'] = prev.get('first_screened') or s['as_of']
            if not vals['decision_page']: vals['decision_page'] = prev.get('decision_page') or ''
            vals['last_price_check'] = prev.get('last_price_check') or ''; vals['last_price'] = prev.get('last_price') or ''
            for k in SCREENER_KEYS:
                if k in vals: fm = fm_set(fm, k, vals[k], before='our_decision')
            for k in USER_KEYS:
                if not any(re.match(rf'^{k}:', ln) for ln in fm): fm = fm_set(fm, k, '')
            our_then = prev.get('our_decision') or ''
            if M_LATEST[0] in body and M_LATEST[1] in body:
                a = body.index(M_LATEST[0]); b = body.index(M_LATEST[1]) + len(M_LATEST[1])
                body = body[:a] + latest_block(s) + body[b:]
            row = hist_row(s, change_txt, our_then)
            if M_HISTORY in body:
                k = body.index(M_HISTORY) + len(M_HISTORY)
                hh = body.find(HIST_HEAD, k)
                ins = hh + len(HIST_HEAD) if hh >= 0 else k
                body = body[:ins] + '\n' + row + body[ins:]
            else:
                body = body.rstrip('\n') + '\n\n## History\n\n' + M_HISTORY + '\n' + HIST_HEAD + '\n' + row + '\n'
            open(path, 'w', encoding='utf-8').write('---\n' + '\n'.join(fm) + '\n---\n' + body)
            written.append(('updated', t, os.path.basename(path)))
        else:
            vals['first_screened'] = s['as_of']; vals['last_price_check'] = ''; vals['last_price'] = ''
            fm = []
            for k in SCREENER_KEYS: fm = fm_set(fm, k, vals.get(k, ''))
            for k in USER_KEYS: fm = fm_set(fm, k, '')
            fn = safe_name(s['name']) + NOTE_SUFFIX
            if os.path.exists(os.path.join(notes_dir, fn)): fn = safe_name(f"{s['name']} {t}") + NOTE_SUFFIX
            text = new_note(s, fm)
            text = text.rstrip('\n') + '\n' + hist_row(s, change_txt or 'first record', '') + '\n'
            open(os.path.join(notes_dir, fn), 'w', encoding='utf-8').write(text)
            written.append(('created', t, fn))
    json.dump(written, open(os.path.join(run, 'records_written.json'), 'w'), ensure_ascii=False, indent=1)
    for w in written: print(*w)
    return written

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('a'); ap.add_argument('b', nargs='?')
    ap.add_argument('--as-of'); ap.add_argument('--baseline'); ap.add_argument('--run-file', default='')
    ap.add_argument('--industry', default=''); ap.add_argument('--vault'); ap.add_argument('--snapshot'); ap.add_argument('--note', default='')
    ap.add_argument('--fy-end', default='', help='JSON file {ticker: {date, source}}: fiscal year-ends for companies whose page shows none')
    A = ap.parse_args()
    if A.cmd == 'snapshot':
        sn = snapshot_from_page_data(A.a); json.dump(sn, open(os.path.join(A.a, 'snapshot.json'), 'w'), ensure_ascii=False, indent=1); print(len(sn), 'companies in snapshot.json')
    elif A.cmd == 'snapshot-html':
        sn = snapshot_from_html(A.a, A.as_of, json.load(open(A.fy_end)) if A.fy_end else None); json.dump(sn, open(A.b, 'w'), ensure_ascii=False, indent=1); print(len(sn), 'companies in', A.b)
    elif A.cmd == 'read': read(A.a, A.b)
    elif A.cmd == 'compare': compare(A.a, A.baseline)
    elif A.cmd == 'write': write(A.a, A.b, A.run_file, A.industry, A.vault, A.snapshot, A.note)
    else: sys.exit('unknown command ' + A.cmd)
