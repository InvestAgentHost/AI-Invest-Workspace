#!/usr/bin/env python3
"""Company initial screener - engine v4.7.2 (facts only, traffic lights, three separate factors). Rules version 2026-10-23c (2026-10-23c: Industry computed once per tag over every company with data, the run company included, with the company count shown and groups under 6 marked thin; settlement debt counts its current part too, for run companies and peers alike; the CEO-sale penalty cannot take M1 below 2; M3 uses the current CEO's years when there are at least 5 and counts losses on businesses sold or held for sale. 2026-10-23b: a deal that fails only the goodwill test keeps the window and B1/B4 take the lower of the full window and the years after the deal; litigation settlements payable on a fixed schedule count as debt; peer groups decided per tag; short history is tested before a weak Business light. 2026-10-23a: the AAER horizon counts from the end of the misconduct; v4.3 adds display-only items: the B1/B4 leading indicator and the screening-record fields).

  python3 screener.py RUN_DIR score   -> prints the data measures and the automatic perimeter flags (needs raw/main*.json)
  python3 screener.py RUN_DIR build   -> RUN_DIR/page_data.json (needs raw/main*.json, raw/pe.json, facts/<T>.json)

RUN_DIR/config.json holds the company list and run settings. Every threshold sits in RULES below;
change it there (and in the SKILL.md rules section) when a rule changes.
"""
import json, math, os, re, sys, glob, datetime, statistics as st
from decimal import Decimal, ROUND_HALF_UP

ENGINE_VERSION = 'v4.7.2'
RULES_VERSION = '2026-10-23c'   # change together with RULES; the page and the vault records take the label from here (run_meta.json), not from config.json

RULES = {
    'nopat_tax': 0.25,                        # fixed tax in NOPAT (B1, B3, B4)
    'window_years': 10,                       # data window = latest 10 fiscal years
    'short_min_years': 3,                     # fewer clean perimeter years -> short history, manual review
    'B1_median': [.25, .15, .10, .06],        # median ROIC on capital excl. goodwill -> 5, 4, 3, 2; below -> 1
    'B1_low': [.15, .10, .06],                # 25th-percentile year -> 5, 4, 3; below -> 2
    'B1_low_quantile': .25,                   # k-th lowest year, k = ceil(n x 0.25): 3rd lowest of 10
    'downturn_line': 0.50,                    # short history after a separation: low-3 segment margin < 50% of median -> B1 down one level
    'B2': [1.00, .90, .75, .50],              # FCF before interest / NOPAT -> 5, 4, 3, 2; below -> 1
    'tax_guard': (0.0, 0.50),                 # own tax rate outside this range -> 25%
    'B3': [.12, .08, .05, .02],               # 10-yr NOPAT per share growth -> 5, 4, 3, 2; below -> 1
    'growth_min_years': 6, 'growth_end_years': 3, 'share_jump': 0.50,
    'B4': [.15, .12, .09, .06],               # median ROIC incl. goodwill -> 5, 4, 3, 2; below -> 1
    'M1': [30, 15, 6, 2],                     # owned shares x price / base salary -> 5, 4, 3, 2; below -> 1
    'M2_sbc': [.03, .06, .10, .15],           # stock comp / operating income, 5-yr sums: <3% -> 5, <6% -> 4, <10% -> 3, <15% -> 2, else 1
    'M2_sbc_years': 5,
    'M2_vote': [.90, .80, .70, .50],          # say-on-pay For / (For + Against) -> 5, 4, 3, 2; below -> 1
    'M3_impair': [.05, .15, .30],             # 0 -> 5, <5% -> 4, <15% -> 3, <30% -> 2, else 1
    'M3_shares': [-.15, -.05, .05, .20],      # change <= -15% -> 5, <= -5% -> 4, <= +5% -> 3, <= +20% -> 2, else 1
    'redflag_402_years': 3, 'redflag_aaer_years': 5,
    'redflag_aaer_basis': 'conduct',          # user, 2026-10-23: the AAER horizon counts from the end of the misconduct the release describes (conduct_end), not the release date; an AAER whose conduct ended earlier is shown as information only. Falls back to the release date when conduct_end is missing.
    'flag_rev': .25, 'flag_gw_ic': .25,       # automatic perimeter flags
    'deal_after_ye': .25,                     # deal above 25% of revenue after the latest year-end -> "business changing"
    'quality_line': 3.5, 'quality_band_low': 3.0,   # quadrant: horizontal line and the shaded 'close' band
    'pe_lines': [33, 50, 67],                 # quadrant: vertical lines at these own-history P/E percentiles
    'lev_max': 5.0, 'cov_min': 2.0,           # financial-risk gate: net debt / EBITDA above 5x, or EBIT / interest below 2x
    'pe_min_pos_share': 60, 'pe_min_pos_days': 250, 'pe_short_years': 5,   # a multiple's range needs >= 250 positive days (about one year) and positive on >= 60% of days
    'pe_distorted': 1.5,                      # trailing / forward P/E above this -> "P/E distorted"
    'pe_stale_days': 20,                      # last daily P/E older than this before the as-of date -> 'P/E series stale' flag
    # ---- multiples: P/E, EV/EBIT and EV/EBITDA, each placed in its own history; the median of the three percentiles is the reading used by the Result
    'deal_delay_months': 12,                  # after a merger or separation (config pe_from) every multiple's window starts 12 months later: trailing earnings first cover only the current business then
    'mult_disagree_pts': 30,                  # highest minus lowest of the three percentiles at or above this -> 'multiples disagree' line
    'trend_years': [1, 3, 5, 10],             # EV/EBITDA change over these horizons (3, 5, 10 on the table; 1 in the hover text)
    'trend_min_years': 1,
    'level_years': [1, 3, 5, 10],             # today against the stock's own median multiple over these horizons (median of P/E, EV/EBIT, EV/EBITDA deviations)
    'level_min_days': 120,                    # a horizon needs this many positive days in the clean window
    'cheaper_move': .10,                      # 'Getting cheaper' = today 10% or more below its own 1-year median AND below the multiple exactly one year ago ('Getting dearer' the mirror); else 'Steady'
    'cheaper_counts': True,                   # option B (user, 2026-10-21): a good business that is getting cheaper is 'Research now' at any level                     # a 'since <clean date>' line needs at least this many years
    'pe_trend_move': .10,                     # multiple change beyond +/-10% -> rising / falling arrow
    # ---- lights: measure score 4-5 green, 3 yellow, 1-2 red; factor average >= 3.5 green, 3.0-3.5 yellow, < 3.0 red
    'light_green': 4, 'light_yellow': 3, 'factor_green': 3.5, 'factor_yellow': 3.0,
    # ---- Industry (peers from the tagged coverage universe; normalized inputs (see source_ledger.json) only, no repairs from filings)
    'I1': [.15, .12, .09, .06],               # peer median of 10-yr median ROIC incl. goodwill -> 5, 4, 3, 2; below -> 1 (B4 formula)
    'I2': [.10, .07, .04, .02],               # peer median 10-yr revenue growth -> 5, 4, 3, 2; below -> 1
    'I3': [-.05, -.10, -.20, -.30],           # worst year of the peers' median revenue change: better than -5% -> 5, -10% -> 4, -20% -> 3, -30% -> 2, else 1
    'peer_min': 3,                            # the 'returns vs peers' line needs at least 3 OTHER companies with a value over the company's own years
    'peer_tag_min': 4,                        # a tag keeps its own group when at least 4 of its companies have an I1 value; otherwise the whole tag widens to its parent group (v4.4)
    'group_min': 4,                           # v4.7 (user, 2026-10-23): I1 and I2 are medians over the whole group, the run company included, and need 4 companies with a value (= 3 peers + the company)
    'i3_min_cos': 4,                          # v4.7: an I3 year needs 4 companies in the group with a revenue change (was 3 peers)
    'near_cut': .01,                         # v4.7.1 (user, 2026-10-23): an Industry measure within 1 percentage point of a score cut-off is marked 'near the cut-off'
    'thin_group': 6,                          # v4.7: a group with fewer than 6 companies with an I1 value is shown as 'thin group'
    'm1_sale_floor': 2,                       # v4.7 (user, 2026-10-23): the CEO-sale penalty cannot take M1 below 2; a holding that already scores 1-2 shows the result of the selling
    'm3_ceo_min_years': 5,                    # v4.7 (user, 2026-10-23): M3 uses only the current CEO's fiscal years when the window holds at least 5 of them; else the full window
    'gw_only_keeps_window': True,             # v4.4: a deal flagged only by the goodwill test (no deal-caused revenue or share flag in that year or the next) keeps the window; B1 and B4 take the lower of the full window and the years after the deal
    'peer_min_years': 5, 'peer_growth_min_years': 6, 'i3_years': 10,
    # ---- Result (one of four categories, from the lights; see result())
    'research_now_pe': 50,                    # good company with the median multiple percentile at or below this -> Research now
    'new_ceo_months': 24,                     # CEO in office for less than this -> 'new CEO' signal
    'ceo_trace_years': 5,                     # CEO change within this many years -> tag under the Management light, with the years of M2/M3 under this CEO (user, 2026-10-21)
    'near_line_price': .05,                   # Research now: price less than 5% below the research line -> ' — close'
    'near_line_pts': 5,                       # Research at lower price: within this many percentile points above the line -> ' — close' (test)
    'low_in_range_pe': 33,                    # average business with the median multiple percentile at or below this -> Quick look (test)
    'peer_cut_gw_ic': .25, 'peer_cut_rev': .25, 'peer_cut_share': .50,   # a peer's window starts after a separation (revenue down > 25% AND goodwill + intangibles down > 25% of invested capital) or a diluted share jump > 50%; acquisitions stay in (ROIC incl. goodwill charges the price paid)
}

RUN = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
P = lambda *a: os.path.join(RUN, *a)
CFG = json.load(open(P('config.json')))
if CFG.get('rules_version') and CFG['rules_version'] != RULES_VERSION:
    sys.exit(f"config.json says rules_version {CFG['rules_version']}, but this engine ({ENGINE_VERSION}) scores under rules {RULES_VERSION}. "
             f"Set rules_version to {RULES_VERSION} (or leave it out), or run the engine that carries {CFG['rules_version']}.")
CO = CFG['companies']
KEY = {t: c['key'] for t, c in CO.items()}
AS_OF = CFG.get('as_of') or datetime.date.today().isoformat()

def _load(path, default):
    return json.load(open(path)) if os.path.exists(path) else default

RAW = {}
for f in sorted(glob.glob(P('raw', 'main*.json'))):
    RAW.update({k: v for k, v in json.load(open(f)).items() if isinstance(v, dict)})
PE = _load(P('raw', 'pe.json'), {})
EV = _load(P('raw', 'ev.json'), {})       # daily EV/EBIT, EV/EBITDA, enterprise value (millions) and share price from normalized inputs; actual sources in source_ledger.json

n0 = lambda x: 0 if x is None else x
def r1(x): return float(Decimal(str(x)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
def pct(x, d=1): return '–' if x is None else f"{x * 100:.{d}f}%"
def fmt(x): return '–' if x is None else (f"{x:g}" if isinstance(x, (int, float)) else str(x))
def m0(x): return '–' if x is None else f"{x:,.0f}"
def ordn(n): return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"
def num(v):
    if isinstance(v, bool) or v is None: return None
    if isinstance(v, (int, float)): return v
    try: return float(str(v).replace(',', ''))
    except Exception: return None
def years_ago(n):
    y, m, d = AS_OF.split('-'); return f"{int(y) - n}-{m}-{d}"

def ge(x, cuts, scores, floor):
    for c, s in zip(cuts, scores):
        if x >= c: return s
    return floor
def lt(x, cuts, scores, floor):
    for c, s in zip(cuts, scores):
        if x < c: return s
    return floor
s_b1med = lambda x: ge(x, RULES['B1_median'], (5, 4, 3, 2), 1)
s_b1low = lambda x: ge(x, RULES['B1_low'], (5, 4, 3), 2)
s_b2 = lambda x: ge(x, RULES['B2'], (5, 4, 3, 2), 1)
s_b3 = lambda x: ge(x, RULES['B3'], (5, 4, 3, 2), 1)
s_b4 = lambda x: ge(x, RULES['B4'], (5, 4, 3, 2), 1)
s_m1 = lambda x: ge(x, RULES['M1'], (5, 4, 3, 2), 1)
s_sbc = lambda x: lt(x, RULES['M2_sbc'], (5, 4, 3, 2), 1)
s_vote = lambda x: ge(x, RULES['M2_vote'], (5, 4, 3, 2), 1)
s_i1 = lambda x: ge(x, RULES['I1'], (5, 4, 3, 2), 1)
s_i2 = lambda x: ge(x, RULES['I2'], (5, 4, 3, 2), 1)
def s_i3(x):
    for c, s in zip(RULES['I3'], (5, 4, 3, 2)):
        if x > c: return s
    return 1
def near_cut(x, cuts):
    """v4.7.1: the score cut-off closest to x when it lies within RULES['near_cut'] (display only; the score is unchanged)."""
    if x is None or x == float('inf'): return None
    c = min(cuts, key=lambda c: abs(x - c))
    return c if abs(x - c) <= RULES['near_cut'] + 1e-12 else None
def near_txt(x, c):
    return f"near the cut-off: {x * 100:.1f}% is {abs(x - c) * 100:.1f} points {'above' if x >= c else 'below'} the {c * 100:.0f}% line, so one company more or less in the group can move this score"
def light(s):
    if not isinstance(s, (int, float)): return 'na'
    return 'g' if s >= RULES['light_green'] else 'y' if s >= RULES['light_yellow'] else 'r'
def flight(v):
    if v is None: return 'na'
    return 'g' if v >= RULES['factor_green'] else 'y' if v >= RULES['factor_yellow'] else 'r'
LNAME = {'g': 'green', 'y': 'yellow', 'r': 'red', 'na': 'no light'}
def s_imp(x):
    a, b, c = RULES['M3_impair']
    return 5 if x == 0 else 4 if x < a else 3 if x < b else 2 if x < c else 1
def s_dil(x):
    a, b, c, d = RULES['M3_shares']
    return 5 if x <= a else 4 if x <= b else 3 if x <= c else 2 if x <= d else 1

# ---------------- data
def facts(t):
    return _load(P('facts', f'{t}.json'), {})

def rows(t, use_facts=True):
    """Fiscal-year rows, with config data_fixes and the fact collector's repairs (amortization, impairments, continuing CFO)."""
    k = KEY[t]; d = RAW[k]; fx = CO[t].get('data_fixes') or {}; R = {}; rep = []
    for r in d['rows']:
        x = dict(zip(d['cols'], r))
        if fx.get('zero_am'): x['am'] = 0
        if fx.get('zero_imp'): x['imp'] = 0
        R[x['fy']] = x
    cc = []
    for y, x in R.items():          # automatic check: operating cash flow from continuing operations where the filing shows it
        if x.get('cfoCont') is not None and (x.get('cfo') is None or abs(x['cfo'] - x['cfoCont']) > 0.05):
            cc.append(f"FY{y} {m0(x.get('cfo'))}→{x['cfoCont']:,.1f}"); x['cfo'] = x['cfoCont']
    if cc: rep.append('Operating cash flow switched to the filed "continuing operations" line: ' + ', '.join(sorted(cc)))
    if use_facts:
        F = (facts(t).get('data') or {})
        for col, fk, lab in (('am', 'amortization_acquired_intangibles', 'amortization of acquired intangibles'),
                             ('imp', 'impairments_gw_intangibles', 'goodwill and intangible impairments'),
                             ('cfo', 'cfo_continuing', 'operating cash flow from continuing operations')):
            ch = []
            for y, v in (F.get(fk) or {}).items():
                y = int(str(y)[:4]); v = num(v)
                if v is None or y not in R: continue
                if col in ('am', 'imp'): v = abs(v)
                old = R[y].get(col)
                if old is None or abs(n0(old) - v) > 0.05:
                    ch.append(f"FY{y} {m0(old) if old is not None else 'blank'}→{v:,.1f}")
                R[y][col] = v
            if ch: rep.append(f"{lab.capitalize()} from filings (fact collector): " + ', '.join(sorted(ch)))
        dl = F.get('debt_like') or {}          # v4.4: litigation settlements payable on a fixed schedule count as debt; v4.7: current + non-current part
        ch, nocur = [], []
        # v4.7.1: a flat {year: value}, one {label, years} item, or several named {label, years} items
        if isinstance(dl, dict) and 'years' not in dl and any(isinstance(v, dict) and 'years' in v for v in dl.values()):
            yrs_ = {}
            for it in dl.values():
                if not (isinstance(it, dict) and 'years' in it): continue
                for y_, v_ in (it.get('years') or {}).items():
                    nc_, cu_ = settle_parts(v_); p_ = yrs_.setdefault(str(y_), {'noncurrent': 0, 'current': 0, '_cu': True})
                    p_['noncurrent'] += abs(n0(nc_)); p_['current'] += abs(n0(cu_)); p_['_cu'] = p_['_cu'] and cu_ is not None
            dl = {'label': '; '.join(str(it.get('label')) for it in dl.values() if isinstance(it, dict) and it.get('label')),
                  'years': {y_: {'noncurrent': p_['noncurrent'], 'current': (p_['current'] if p_['_cu'] else None)} for y_, p_ in yrs_.items()}}
        for y, v in ((dl.get('years') if isinstance(dl, dict) and 'years' in dl else dl) or {}).items():
            try: y = int(str(y)[:4])
            except ValueError: continue
            if y not in R: continue
            nc, cu = settle_parts(v)
            if nc is None and cu is None: continue
            add = abs(n0(nc)) + abs(n0(cu))
            if cu is None: nocur.append(y)              # a missing current part is flagged, never read as zero
            if add == 0: continue
            R[y]['debt'] = n0(R[y].get('debt')) + add
            ch.append(f"FY{y} +{add:,.0f}" + (f" ({abs(n0(nc)):,.0f} long-term + {abs(cu):,.0f} current)" if cu is not None else ' (long-term only)'))
        if ch: rep.append("Debt-like liabilities added to debt" + (f" ({dl.get('label')})" if isinstance(dl, dict) and dl.get('label') else '') + ' (fact collector): ' + ', '.join(sorted(ch)))
        if nocur: rep.append(f"Settlement debt: current part not disclosed or not collected for {fyspan(sorted(nocur))}, so debt is understated in those years")
        for col, ys in (CO[t].get('data_overrides') or {}).items():
            for y, v in ys.items():
                if int(y) in R: R[int(y)][col] = v; rep.append(f"{col} FY{y} set to {v} (config)")
    return R, d['L'], rep

def settle_parts(v):
    """One year of a fixed-schedule settlement liability: a number (non-current part only, fact files before v4.7) or
    {noncurrent, current}. Returns (noncurrent, current); current is None when it was not disclosed or not collected."""
    if isinstance(v, dict):
        return num(v.get('noncurrent')), num(v.get('current'))
    return num(v), None

def ic(x):
    if x is None or x.get('eq') is None: return None
    return n0(x['debt']) + x['eq'] - n0(x['cash'])

def nopat(x):
    return (x['op'] + n0(x['am']) + n0(x['imp'])) * (1 - RULES['nopat_tax'])

def fyspan(ys):
    return (f"FY{ys[0]}" if ys[0] == ys[-1] else f"FY{ys[0]}–FY{ys[-1]}") if ys else ''

def flags(t, R, L):
    """Automatic perimeter flags (rule 2) for FY(L-10)..FY(L)."""
    out = []
    for y in range(L - RULES['window_years'], L + 1):
        if y not in R or y - 1 not in R: continue
        a, p = R[y], R[y - 1]
        if a.get('rev') and p.get('rev') and abs(a['rev'] / p['rev'] - 1) > RULES['flag_rev']:
            out.append(dict(fy=y, test='revenue', text=f"revenue {m0(p['rev'])} → {m0(a['rev'])} ({a['rev'] / p['rev'] - 1:+.0%})"))
        icp = ic(p)
        if icp and icp > 0 and ic(a) is not None:
            dg = (n0(a['gw']) + n0(a['ia'])) - (n0(p['gw']) + n0(p['ia']))
            if abs(dg) / icp > RULES['flag_gw_ic']:
                out.append(dict(fy=y, test='goodwill', text=f"goodwill + intangibles {dg:+,.0f} = {dg / icp:+.0%} of prior invested capital {m0(icp)}"))
        if a.get('dil') and p.get('dil') and a['dil'] / p['dil'] - 1 > RULES['share_jump']:
            out.append(dict(fy=y, test='shares', text=f"diluted shares {p['dil']:.1f} → {a['dil']:.1f} ({a['dil'] / p['dil'] - 1:+.0%})"))
    fy = ((facts(t).get('perimeter') or {}).get('flagged_years') or {})
    for f in out:
        e = fy.get(str(f['fy'])) or {}
        f['cause'] = e.get('cause'); f['why'] = e.get('explanation', ''); f['src'] = e.get('source', ''); f['url'] = e.get('url', '')
    return out

# ---------------- Industry: peers from the tagged coverage universe
UDIR = CFG.get('universe_dir')
UNI, RAWU = {}, {}
if UDIR:
    UDIR = UDIR if os.path.isabs(UDIR) else os.path.join(RUN, UDIR)
    UNI = json.load(open(os.path.join(UDIR, 'universe.json')))
    for f in sorted(glob.glob(os.path.join(UDIR, 'raw', '*.json'))):
        RAWU.update({k: v for k, v in json.load(open(f)).items() if isinstance(v, dict) and 'rows' in v})
AMFA = (_load(os.path.join(UDIR, 'raw_extra', 'am_focusalpha.json'), {}) or {}).get('companies', {}) if UDIR else {}
# v4.7 (user, 2026-10-23): one settlement-debt definition for run companies and peers. Fixed-schedule settlement liabilities
# (current + non-current) for universe companies, from filings; the one exception to 'peers use normalized inputs (see source_ledger.json) only'.
DLU = (_load(os.path.join(UDIR, 'raw_extra', 'debt_like.json'), {}) or {}).get('companies', {}) if UDIR else {}

def fa_amortization(k, R):
    """FocusAlpha amortization by normalized fiscal year: match each FocusAlpha row to the year whose net income agrees within 2%, else by period-end year."""
    out = {}
    for r in (AMFA.get(k) or {}).get('rows') or []:
        am = r.get('amortization')
        if am is None: continue
        y = None
        if r.get('net_income') is not None:
            for fy, x in R.items():
                ni = x.get('nicf')
                if ni not in (None, 0) and abs(ni - r['net_income']) <= max(abs(ni) * .02, 0.6): y = fy; break
        if y is None:
            d = str(r.get('report_period') or ''); y = int(d[:4]) - (1 if d[5:7] == '01' and int(d[8:10] or 0) <= 7 else 0) if d else None
        if y is not None and y not in out: out[y] = am
    return out
_PM = {}

def peer_measures(k):
    """Data-only measures for one universe company (no repairs from filings, no perimeter judgment).
    Window: latest 10 fiscal years, starting after the latest separation (revenue down > 25% and goodwill + intangibles down > 25% of invested capital)
    or diluted share jump > 50%, or at window_from in universe.json. Acquisitions stay in: ROIC including goodwill charges the price paid."""
    if k in _PM: return _PM[k]
    d = RAWU.get(k) or RAW.get(k); u = (UNI.get('companies') or {}).get(k, {})
    if not d or 'rows' not in d: _PM[k] = dict(ok=False, why='no normalized statement data (see source_ledger.json)'); return _PM[k]
    R = {}; notes = []
    bad = lambda src: bool(__import__('re').search(r'profit|before|excluding', src or '', __import__('re').I))
    zam, zimp = bad(d.get('amSrc')), bad(d.get('impSrc'))
    for r in d['rows']:
        x = dict(zip(d['cols'], r))
        if zam: x['am'] = 0
        if zimp: x['imp'] = 0
        R[x['fy']] = x
    if zam or zimp: notes.append('a matched amortization/impairment line was a profit subtotal, so it was set to 0')
    dlu = DLU.get(k) or {}; added, nocur = [], []
    for y, v in (dlu.get('years') or {}).items():
        y = int(str(y)[:4]); nc, cu = settle_parts(v)
        if y not in R or (nc is None and cu is None): continue
        add = abs(n0(nc)) + abs(n0(cu))
        if add: R[y]['debt'] = n0(R[y].get('debt')) + add; added.append(y)
        if cu is None: nocur.append(y)
    if nocur and not added: notes.append(f"settlement liabilities: current part not disclosed for {fyspan(sorted(nocur))}")
    if added: notes.append(f"settlement liabilities added to debt for {fyspan(sorted(added))} (from filings: {dlu.get('label', 'fixed-schedule settlements')})" + (f"; current part not disclosed for {fyspan(sorted(nocur))}" if nocur else ''))
    fa = fa_amortization(k, R); filled = 0
    for y, v in fa.items():
        if y in R and not R[y].get('am'): R[y]['am'] = v; filled += 1
    if filled: notes.append(f'amortization of intangibles from FocusAlpha (cash flow statement) for {filled} years')
    elif (d.get('amSrc') or 'none') == 'none' or zam: notes.append('no amortization of acquired intangibles in the data (ROIC understated if the company has acquisitions)')
    L = d['L']; W = RULES['window_years']; start = L - W + 1; cut = None
    for y in range(L - W + 1, L + 1):
        if y not in R or y - 1 not in R: continue
        a, p_ = R[y], R[y - 1]; icp = ic(p_)
        if icp and icp > 0 and ic(a) is not None and a.get('rev') and p_.get('rev'):
            dg = (n0(a['gw']) + n0(a['ia'])) - (n0(p_['gw']) + n0(p_['ia'])); dr = a['rev'] / p_['rev'] - 1
            if dg / icp < -RULES['peer_cut_gw_ic'] and dr < -RULES['peer_cut_rev']:
                cut = (y, f"separation: revenue {dr:+.0%} and goodwill + intangibles {dg / icp:+.0%} of invested capital in FY{y}")
        if a.get('dil') and p_.get('dil') and a['dil'] / p_['dil'] - 1 > RULES['peer_cut_share']: cut = (y, f"diluted shares {a['dil'] / p_['dil'] - 1:+.0%} in FY{y}")
    if cut and cut[0] + 1 > start: start = cut[0] + 1; notes.append('window starts FY%d: %s' % (start, cut[1]))
    if u.get('window_from') and int(u['window_from']) > start: start = int(u['window_from']); notes.append(f"window starts FY{start}: {u.get('window_why', 'set in universe.json')}")
    rt = next((t for t, kk in KEY.items() if kk == k), None)          # a run company used as a peer keeps the perimeter set in this run's config
    if rt and (CO[rt].get('perimeter_start') or 0) > start: start = CO[rt]['perimeter_start']; notes.append(f"window starts FY{start}: perimeter set for this company in the run")
    yrs = [y for y in range(start, L + 1) if y in R and y - 1 in R and R[y].get('op') is not None and ic(R[y]) is not None and ic(R[y - 1]) is not None]
    roic, neg = {}, 0
    for y in yrs:
        ci = (ic(R[y]) + ic(R[y - 1])) / 2
        if ci > 0: roic[y] = nopat(R[y]) / ci
        else: neg += 1
    o = dict(ok=True, key=k, t=u.get('t', k), name=u.get('name', k), tag=u.get('tag'), L=L, start=start, cur=d.get('cur'), notes=notes, roic=roic, neg=neg)
    if neg >= 3 and sum(nopat(R[y]) for y in yrs) > 0: o.update(roicMed=float('inf'), roicWhy=f'invested capital ≤ 0 in {neg} years: counted as top of the range')
    elif len(roic) >= RULES['peer_min_years']: o.update(roicMed=st.median(roic.values()), roicWhy='')
    else: o.update(roicMed=None, roicWhy=f'{len(roic)} usable years (needs {RULES["peer_min_years"]})')
    gy = [y for y in range(start, L + 1) if y in R and R[y].get('rev')]
    e = RULES['growth_end_years']
    if len(gy) >= RULES['peer_growth_min_years']:
        a = st.median(R[y]['rev'] for y in gy[:e]); b = st.median(R[y]['rev'] for y in gy[-e:])
        o.update(revG=(b / a) ** (1 / (len(gy) - e)) - 1 if a > 0 and b > 0 else None, revYrs=(gy[0], gy[-1]))
    else: o.update(revG=None, revYrs=None)
    o['revChg'] = {y: R[y]['rev'] / R[y - 1]['rev'] - 1 for y in range(start + 1, L + 1) if y in R and y - 1 in R and R[y].get('rev') and R[y - 1].get('rev') and R[y - 1]['rev'] > 0}
    _PM[k] = o
    return o

def peer_group(t):
    """Group for the Industry light (v4.7, user 2026-10-23): every company in the run company's tag, the run company included, so every
    company in a tag gets the same Industry light. The tag keeps its own group when peer_tag_min of its companies have an I1 value;
    otherwise the whole tag widens to the parent group (all tags under it). `others` = the group without the run company (for the
    'returns vs peers' line, which compares the company with everyone else)."""
    k = KEY[t]; U = UNI.get('companies') or {}; u = U.get(k)
    if not u: return None
    tag = u['tag']; T = UNI['tags'][tag]; par = T['parent']
    mem_all = [x for x, v in U.items() if v['tag'] == tag]
    mem = [x for x in mem_all if peer_measures(x).get('roicMed') is not None]
    if len(mem) >= RULES['peer_tag_min']:
        return dict(tag=tag, label=T['label'], level='tag', members=mem_all, others=[x for x in mem_all if x != k],
                    why=f"{len(mem)} companies with data in '{T['label']}'" + (f", {u.get('t', t)} included" if k in mem else f"; {u.get('t', t)} has no I1 value of its own"))
    wide = [x for x, v in U.items() if UNI['tags'][v['tag']]['parent'] == par]
    return dict(tag=tag, label=T['label'], level='parent', parent=par, plabel=UNI['parents'][par], members=wide, others=[x for x in wide if x != k],
                why=f"only {len(mem)} companies with data in '{T['label']}' (needs {RULES['peer_tag_min']}), so the tag widens to '{UNI['parents'][par]}'")

def industry(t, L):
    g = peer_group(t)
    if g is None: return None, []
    k = KEY[t]
    pm = [peer_measures(x) for x in g['members']]; pm = [p for p in pm if p.get('ok')]
    out = []
    grp = g['label'] if g['level'] == 'tag' else f"{g['plabel']} (widened from {g['label']})"
    rv = [p['roicMed'] for p in pm if p.get('roicMed') is not None]
    thin = len(rv) < RULES['thin_group']
    cnt = f"{len(rv)} companies" + (' · thin group' if thin else '')
    me = (UNI.get('companies') or {}).get(k, {}).get('t', t)
    selfp = next((p for p in pm if p['key'] == k), {})
    inc = lambda fld: f"{me} included" if selfp.get(fld) is not None else f"{me} has no value of its own"
    med1 = st.median(rv) if len(rv) >= RULES['group_min'] else None
    i1 = s_i1(med1) if med1 is not None else None
    fmtr = lambda v: '>100% (capital ≤ 0)' if v == float('inf') else pct(v)
    rule_grp = f"Group = every company in the tag with data, {me} included, so every company in the tag gets the same Industry light; needs {RULES['group_min']} companies with a value; under {RULES['thin_group']} it is marked thin."
    n1 = near_cut(med1, RULES['I1'])
    out.append(dict(code='I1', name='Industry return on all capital', factor='Industry', kind='Data (group)', score=i1, near=(near_txt(med1, n1) if n1 is not None else ''),
                    inputs=[['Group', grp], ['Companies with a value', f"{len(rv)} of {len(pm)}, {inc('roicMed')}" + (' · thin group' if thin else '')]],
                    calc=(f"Median of the group's 10-year median ROIC including goodwill = {fmtr(med1)} → {i1}" if med1 is not None else f"Not scored: {len(rv)} companies with a value (needs {RULES['group_min']})"),
                    note='', rule='Each company in the group: NOPAT ÷ average (debt + leases + settlement liabilities + equity − cash), median over its latest 10 fiscal years (B4 formula, normalized inputs (see source_ledger.json) plus filed settlement liabilities). Group value = median across the group. ≥15% → 5, ≥12% → 4, ≥9% → 3, ≥6% → 2, <6% → 1. ' + rule_grp))
    gv = [p['revG'] for p in pm if p.get('revG') is not None]
    med2 = st.median(gv) if len(gv) >= RULES['group_min'] else None
    i2 = s_i2(med2) if med2 is not None else None
    n2 = near_cut(med2, RULES['I2'])
    out.append(dict(code='I2', name='Industry revenue growth', factor='Industry', kind='Data (group)', score=i2, near=(near_txt(med2, n2) if n2 is not None else ''),
                    inputs=[['Group', grp], ['Companies with a value', f"{len(gv)} of {len(pm)}, {inc('revG')}"]],
                    calc=(f"Median of the group's 10-year revenue growth = {pct(med2)} → {i2}" if med2 is not None else f"Not scored: {len(gv)} companies with a value (needs {RULES['group_min']})"),
                    note='Revenue growth includes acquisitions. A separation, a share-count jump above 50% or a known spin-off starts that company\'s window after it. Each company\'s growth is in its own reporting currency, so it includes exchange-rate effects.',
                    rule='Each company in the group: median revenue of its first 3 years to median of its last 3 years, as a yearly rate (B3 method), needs 6 years. Group value = median across the group. ≥10% → 5, ≥7% → 4, ≥4% → 3, ≥2% → 2, <2% → 1. ' + rule_grp))
    GL = max([p['L'] for p in pm] or [L])   # v4.7 review: the I3 years come from the group (its latest fiscal year), not from the scored company, so every company in the tag gets the same I3
    yrs = list(range(GL - RULES['i3_years'] + 1, GL + 1)); byy = {}
    for y in yrs:
        v = [p['revChg'][y] for p in pm if y in p['revChg']]
        if len(v) >= RULES['i3_min_cos']: byy[y] = (st.median(v), len(v))
    if byy:
        srt = sorted(byy.items(), key=lambda kv: kv[1][0]); wy, (wv, wn) = srt[0]
        i3 = s_i3(wv); second = srt[1] if len(srt) > 1 else None
        calc = f"Worst year FY{wy}: median revenue change {wv * 100:+.1f}% across {wn} companies → {i3}" + (f". Second-worst FY{second[0]}: {second[1][0] * 100:+.1f}%" if second else '')
    else: i3, calc = None, f"Not scored: no year with at least {RULES['i3_min_cos']} companies"
    n3 = near_cut(wv, RULES['I3']) if byy else None
    out.append(dict(code='I3', name='Depth of the worst industry year', factor='Industry', kind='Data (group)', score=i3, near=(near_txt(wv, n3) if n3 is not None else ''),
                    inputs=[['Group', grp], ['Median revenue change by year', ', '.join(f"FY{y % 100:02d} {v[0] * 100:+.0f}%" for y, v in sorted(byy.items()))]],
                    calc=calc, note='',
                    rule=f"For each of the last 10 fiscal years, the median revenue change across the group (a year needs {RULES['i3_min_cos']} companies); the worst of those years: better than −5% → 5, −5% to −10% → 4, −10% to −20% → 3, −20% to −30% → 2, worse than −30% → 1. " + rule_grp))
    tbl = sorted([dict(t=p['t'], name=p['name'], tag=UNI['tags'][p['tag']]['label'], window=f"FY{p['start']}–FY{p['L']}", roic=(None if p.get('roicMed') is None else ('inf' if p['roicMed'] == float('inf') else round(p['roicMed'], 4))),
                        roicWhy=p.get('roicWhy', ''), revG=None if p.get('revG') is None else round(p['revG'], 4), cur=p['cur'], notes='; '.join(p['notes']), self=p['key'] == k) for p in pm],
                 key=lambda r: -(1e9 if r['roic'] == 'inf' else (r['roic'] if r['roic'] is not None else -1e9)))
    nom = sum(1 for p in pm if any('no amortization' in n for n in p['notes']))
    # the 'returns vs peers' line compares the company with everyone else: the group without the run company, over the company's own scoring years
    po = [p for p in pm if p['key'] != k]
    cy = set(measures(t)['yrs']) if t in KEY else set()
    need = min(3, max(2, len(cy) - 1))
    same = [st.median([v for y, v in p['roic'].items() if y in cy]) for p in po if len([y for y in p['roic'] if y in cy]) >= need]
    i1_same = st.median(same) if len(same) >= RULES['peer_min'] else None
    return dict(group=g, label=grp, table=tbl, noAm=nom, n=len(pm), nVal=len(rv), thin=thin, count=cnt, i1=med1, i1_same=i1_same, i1_same_n=len(same), byYear={y: round(v[0], 4) for y, v in byy.items()}), out

def factor(ms, name):
    """Average of the factor's measures; a missing measure becomes a range (missing = 1 to missing = 5), never an average of what is left."""
    vals = [x['score'] for x in ms if isinstance(x['score'], (int, float))]; miss = [x['code'] for x in ms if not isinstance(x['score'], (int, float))]
    if not ms or not vals: return dict(lo=None, hi=None, point=None, light='na', calc=f'Not scored: no {name} measure available')
    S, n = sum(vals), len(ms); lo, hi = (S + len(miss)) / n, (S + 5 * len(miss)) / n; pt = r1((lo + hi) / 2)
    if miss:
        calc = f"({' + '.join(f'{v:g}' for v in vals)} + {len(miss)} missing) ÷ {n}: lowest {lo:.2f} (missing = 1) to highest {hi:.2f} (missing = 5); middle {pt}. Missing: {', '.join(miss)}"
        ll, lh = flight(lo), flight(hi); lt_ = ll if ll == lh else 'range'
    else:
        calc = '(' + ' + '.join(f'{v:g}' for v in vals) + f") ÷ {n} = {S / n:.3f} → {pt}"; lt_ = flight(pt)
    if lt_ != 'range': calc += f" → {LNAME[lt_]}"
    else: calc += f" → between {LNAME[flight(lo)]} and {LNAME[flight(hi)]}; shown as a grey ? because no filed fact fills the gap"
    gaps = [f"{x['code']} {x['name']}: {x.get('gap') or (x['calc'][12:].rstrip('.') if x['calc'].startswith('Not scored: ') else 'no value')}" for x in ms if not isinstance(x['score'], (int, float))]
    return dict(lo=round(lo, 2), hi=round(hi, 2), point=pt, light=lt_, lightLo=flight(lo), lightHi=flight(hi), calc=calc, gaps=gaps)

# ---------------- data measures
def _ymd0(d):
    m_ = re.search(r'(\d{4})-(\d{2})(?:-(\d{2}))?', str(d or ''))
    if m_: return (int(m_.group(1)), int(m_.group(2)), int(m_.group(3) or 1))
    m_ = re.match(r'\s*(\d{4})\b', str(d or ''))           # a year alone ("1972"): the year counts from January
    return (int(m_.group(1)), 1, 1) if m_ else None

def fy_end_month(Fc):
    ic_ = (Fc.get('red_flags') or {}).get('icfr')
    fe = _ymd0(Fc.get('fiscal_year_end_latest')) or (_ymd0(ic_.get('fiscal_year_end')) if isinstance(ic_, dict) else None)
    return fe[1] if fe else 12

def ceo_years(Fc, ys):
    """Fiscal years in ys under the current CEO: a year counts when the CEO held the job for at least 6 of its 12 months (same test as the CEO tag)."""
    m1 = Fc.get('m1') or {}; since = _ymd0(m1.get('ceo_since'))
    if since is None: return None
    fem = fy_end_month(Fc); sy, sm, sd = since; s_idx = sy * 12 + sm + (1 if sd > 15 else 0)
    under = [y for y in ys if (y * 12 + fem) - s_idx + 1 >= 6]
    nm = re.sub(r'\s*\([^)]*\)', '', str(m1.get('ceo') or '')).split(';')[0].strip() or 'the CEO'
    return dict(yrs=under, since=f"{MON[sm - 1]} {sy}", name=nm)

def measures(t, use_facts=True):
    c = CO[t]; R, L, rep = rows(t, use_facts); W = RULES['window_years']
    start = max(c.get('perimeter_start') or (L - W + 1), L - W + 1)
    yrs = [y for y in range(start, L + 1) if y in R and (y - 1) in R and R[y].get('op') is not None and ic(R[y]) is not None and ic(R[y - 1]) is not None]
    o = dict(L=L, start=start, yrs=yrs, n=len(yrs), perim=start > L - W + 1, repairs=rep, cur=RAW[KEY[t]].get('cur'))
    # ---- B1: ROIC on capital excluding goodwill only (acquired intangibles stay in capital)
    ex, inc, nops, fb = [], [], [], []
    for y in yrs:
        a, p = R[y], R[y - 1]; nop = nopat(a); nops.append(nop)
        ci = (ic(a) + ic(p)) / 2; ce = ((ic(a) - n0(a['gw'])) + (ic(p) - n0(p['gw']))) / 2
        inc.append(nop / ci if ci > 0 else None)
        if ce > 0: ex.append(nop / ce)
        else: ex.append(inc[-1]); fb.append(y)
    o.update(nopat={y: round(v, 1) for y, v in zip(yrs, nops)}, roicEx=ex, roicIn=inc, fallbackYrs=fb)
    v = [x for x in ex if x is not None]
    if v:
        srt = sorted(v); k = max(1, math.ceil(len(srt) * RULES['B1_low_quantile']))
        o.update(b1Med=st.median(v), b1Low=srt[k - 1], b1K=k, b1N=len(v))
        sm, sl = s_b1med(o['b1Med']), s_b1low(o['b1Low'])
        o.update(b1SM=sm, b1SL=sl, B1raw=1 if sm == 1 else min(sm, sl))
    else:
        o.update(b1Med=None, b1Low=None, b1K=None, b1N=0, b1SM=None, b1SL=None, B1raw=1 if nops and sum(nops) <= 0 else None)
    o['short'] = len(yrs) < RULES['short_min_years']
    o['B1'] = o['B1raw']; o['downturnNote'] = ''
    if o['B1'] is not None and o['perim'] and not o['short']:
        o['B1'], o['downturnNote'] = downturn(t, o['B1'])
    # ---- B4: ROIC including goodwill, median over the same window
    vi = [x for x in inc if x is not None]
    if vi: o.update(b4Med=st.median(vi), B4=s_b4(st.median(vi)))
    elif nops: o.update(b4Med=None, B4=5 if sum(nops) > 0 else 1)
    else: o.update(b4Med=None, B4=None)
    # ---- B2: FCF before interest / NOPAT at own tax rate
    Fs = INT = EBIT = PT = TX = 0; ok = 0; sbc_missing = 0
    for y in yrs:
        x = R[y]
        if x.get('cfo') is None: continue
        if x.get('sbc') is None: sbc_missing += 1
        Fs += x['cfo'] + n0(x['capex']) - n0(x['sbc'])
        INT += n0(x['int']) - n0(x['intInc']); EBIT += x['op'] + n0(x['imp']); PT += n0(x['pt']); TX += n0(x['tax']); ok += 1
    t_raw = TX / PT if PT > 0 else None
    lo, hi = RULES['tax_guard']
    tr = t_raw if (t_raw is not None and lo <= t_raw <= hi) else RULES['nopat_tax']
    nm, den = Fs + INT * (1 - tr), EBIT * (1 - tr)
    o.update(b2tRaw=t_raw, b2F=Fs, b2Int=INT, b2t=tr, b2Num=nm, b2Den=den, b2Years=ok, sbcMissingYears=sbc_missing)
    if ok == 0: o.update(B2=None, b2=None)
    elif Fs <= 0 or den <= 0: o.update(B2=1, b2=None)
    else: o.update(b2=nm / den, B2=s_b2(nm / den))
    # ---- B3: NOPAT per share growth over 10 years; acquisitions stay in, a spin-off or a share jump > 50% starts the window later
    gs = max(L - W + 1, c.get('growth_start') or 0); why = c.get('growth_start_why', '')
    for y in range(L - W + 2, L + 1):
        if y in R and y - 1 in R and R[y].get('dil') and R[y - 1].get('dil') and R[y]['dil'] / R[y - 1]['dil'] - 1 > RULES['share_jump'] and y + 1 > gs:
            gs = y + 1; why = f"diluted shares rose {R[y]['dil'] / R[y - 1]['dil'] - 1:+.0%} in FY{y}"
    gy = [y for y in range(gs, L + 1) if y in R and R[y].get('op') is not None and R[y].get('dil') and R[y].get('rev')]
    o.update(gStart=gs, gWhy=why, gYrs=gy)
    nps = {y: nopat(R[y]) / R[y]['dil'] for y in gy}; rev = {y: R[y]['rev'] for y in gy}
    o['nps'] = {y: round(v, 3) for y, v in nps.items()}
    def growth(ser):
        if len(gy) < RULES['growth_min_years']: return None, None, None, f"{len(gy)} years (needs {RULES['growth_min_years']})"
        e = RULES['growth_end_years']; a = st.median(ser[y] for y in gy[:e]); b = st.median(ser[y] for y in gy[-e:])   # median end points
        if a <= 0 or b <= 0: return a, b, None, 'end point at or below zero'
        return a, b, (b / a) ** (1 / (len(gy) - e)) - 1, ''
    a, b, g, gn = growth(nps); o.update(b3A=a, b3B=b, b3=g, b3Note=gn, B3=s_b3(g) if g is not None else None, b3Exp=len(gy) - RULES['growth_end_years'])
    a, b, g, _ = growth(rev); o.update(revA=a, revB=b, revG=g)
    # ---- M2 (data part): stock comp / operating income, latest 5 fiscal years
    sy = [y for y in range(L - RULES['M2_sbc_years'] + 1, L + 1) if y in R and R[y].get('op') is not None]
    sb = [y for y in sy if R[y].get('sbc') is not None]
    S = sum(R[y]['sbc'] for y in sb); OP = sum(R[y]['op'] for y in sb)
    o.update(sbcYrs=sb, sbcSum=S, sbcOp=OP, sbcR=(S / OP if OP > 0 else None) if len(sb) >= 3 else None)
    o['M2sbc'] = None if len(sb) < 3 else (s_sbc(S / OP) if OP > 0 else 1)
    # ---- M3: impairments and share count (ROIC incl. goodwill moved to B4)
    #      v4.7 (user, 2026-10-23): the window is the current CEO's fiscal years when the B1 window holds at least 5 of them, else the
    #      full B1 window; losses on businesses sold or held for sale (net of any filed release of past currency-translation losses) count with impairments.
    Fc_ = facts(t) if use_facts else {}
    cy_ = ceo_years(Fc_, yrs)
    m3y = cy_['yrs'] if cy_ and len(cy_['yrs']) >= RULES['m3_ceo_min_years'] else list(yrs)
    m3why = (f"current CEO's years ({cy_['name']} since {cy_['since']})" if cy_ and m3y == cy_['yrs'] and m3y != list(yrs) else
             (f"full window: {cy_['name']} has {len(cy_['yrs'])} of its years (needs {RULES['m3_ceo_min_years']} for a CEO-only window)" + ("; mostly the previous CEO's record" if len(cy_['yrs']) * 2 < len(yrs) else '') if cy_ and m3y != cy_['yrs'] else
              ('full window, all under the current CEO' if cy_ else 'full window: CEO start date not in the fact file')))
    dsp = ((Fc_.get('data') or {}).get('business_disposal_losses') or {}) if use_facts else {}
    dsp_raw = (Fc_.get('data') or {}).get('business_disposal_losses') if use_facts else None
    if isinstance(dsp, dict) and ('years' in dsp or 'gains' in dsp): dsp_y = dsp.get('years') or {}
    elif isinstance(dsp, dict): dsp_y = {y: v for y, v in dsp.items() if str(y)[:4].isdigit()}
    else: dsp_y = {}
    dloss, dnote = {}, []
    for y, v in (dsp_y or {}).items():
        y = int(str(y)[:4]); v = v if isinstance(v, dict) else {'loss': v}
        lo_, cta = num(v.get('loss')), num(v.get('cta_release_included'))
        if lo_ is None or lo_ <= 0: continue
        cnt_ = lo_ - (abs(cta) if cta is not None else 0)
        dloss[y] = max(cnt_, 0)
        if y not in m3y: continue                      # outside the M3 window: not counted, not listed
        dnote.append(f"FY{y} {lo_:,.0f}" + (f" less {abs(cta):,.0f} currency-translation release = {dloss[y]:,.0f}" if cta is not None else ' (currency-translation part not disclosed: whole loss counted)'))
    impSum = sum(n0(R[y]['imp']) for y in m3y); dSum = sum(dloss.get(y, 0) for y in m3y)
    gwia = [n0(R[y]['gw']) + n0(R[y]['ia']) for y in m3y]
    tot = impSum + dSum
    impPct = tot / (sum(gwia) / len(gwia)) if gwia and sum(gwia) > 0 else (0 if tot == 0 and m3y else None)
    d0y = L - W
    if yrs and o['perim']: d0y = yrs[0]
    if m3y and m3y != list(yrs): d0y = m3y[0] - 1
    if c.get('dil_base'): d0y = c['dil_base']
    d0 = (R.get(d0y) or {}).get('dil'); dL = R[L].get('dil')
    dil = (dL / d0 - 1) if d0 and dL else None
    parts = [s_imp(impPct) if impPct is not None else None, s_dil(dil) if dil is not None else None]
    pv = [p for p in parts if p is not None]
    o.update(impSum=impSum, dispSum=dSum, dispNote=dnote, dispCollected=isinstance(dsp_raw, dict),
             impPct=impPct, dilChg=dil, dilFrom=d0y if d0 else None, M3parts=parts, m3Yrs=m3y, m3Why=m3why, ceoYrs=cy_,
             M3=math.floor(sum(pv) / len(pv)) if len(pv) == 2 else None)
    # ---- financial-risk gate (latest fiscal year): net debt / EBITDA and EBIT / gross interest
    x = R[L]; nd = n0(x['debt']) - n0(x['cash']); ebitda = x['op'] + x['da'] if x.get('da') is not None and x.get('op') is not None else None
    lev = None if ebitda is None else (nd / ebitda if ebitda > 0 else (float('inf') if nd > 0 else -1))
    cov = (x['op'] / x['int']) if x.get('int') else None
    o.update(levND=nd, levEBITDA=ebitda, lev=lev, cov=cov,
             risk=(lev is not None and lev > RULES['lev_max']) or (cov is not None and cov < RULES['cov_min']))
    o['flags'] = flags(t, R, L)
    # ---- v4.4 (user, 2026-10-23): a deal flagged only by the goodwill test keeps the window; B1 and B4 take the lower of the
    #      full-window score and the score on the average of the years after the deal (first year with both balance sheets after it).
    ok_y = {int(k) for k in (c.get('deal_flags_ok') or {})}
    isdeal = lambda f: str(f.get('cause') or '').lower().startswith('deal')
    big = {f['fy'] for f in o['flags'] if isdeal(f) and f['test'] in ('revenue', 'shares') and f['fy'] not in ok_y}   # v4.7.1: a year in deal_flags_ok (e.g. the full-year effect of a goodwill-only deal) does not make the deal 'big'
    gwonly = sorted({f['fy'] for f in o['flags'] if isdeal(f) and f['test'] == 'goodwill' and f['fy'] >= start and f['fy'] not in ok_y
                     and f['fy'] not in big and (f['fy'] + 1) not in big} if RULES['gw_only_keeps_window'] else set())
    pf = c.get('post_deal_from') or ((gwonly[-1] + 1) if gwonly else None)
    o.update(gwOnly=gwonly, postFrom=pf, postYrs=[], b1Post=None, b4Post=None, B1full=o['B1'], B4full=o['B4'], B1post=None, B4post=None)
    if pf and not o['short']:
        py = [(y, e, i) for y, e, i in zip(yrs, ex, inc) if y >= pf]
        o['postYrs'] = [y for y, _, _ in py]
        pe_ = [e for _, e, _ in py if e is not None]; pi_ = [i for _, _, i in py if i is not None]
        if pe_ and o['B1'] is not None:
            o['b1Post'] = sum(pe_) / len(pe_); o['B1post'] = s_b1med(o['b1Post']); o['B1'] = min(o['B1'], o['B1post'])
        if pi_ and o['B4'] is not None:
            o['b4Post'] = sum(pi_) / len(pi_); o['B4post'] = s_b4(o['b4Post']); o['B4'] = min(o['B4'], o['B4post'])
    # ---- data checks: gaps the fact collector must repair from filings
    W10 = [y for y in range(L - W + 1, L + 1) if y in R]
    chk = []
    noam = [y for y in W10 if not R[y].get('am') and n0(R[y].get('ia')) > 0]
    if noam: chk.append(f"amortization of acquired intangibles missing for FY{noam[0]}–FY{noam[-1]} ({len(noam)} yrs) while intangibles are on the balance sheet")
    disc = [y for y in W10 if R[y].get('cfoDisc')]
    if disc: chk.append(f"cash flow shows discontinued operations in FY{disc[0]}–FY{disc[-1]}: operating cash flow must be from continuing operations")
    nosbc = [y for y in W10 if R[y].get('sbc') is None]
    if nosbc: chk.append(f"stock compensation missing for {len(nosbc)} of {len(W10)} years")
    o['dataChecks'] = chk
    return o

def downturn(t, b1):
    d = (CO.get(t) or {}).get('downturn') or {}
    if d.get('type') == 'merger':
        return b1, 'Short window after an acquisition or merger: no single predecessor series, so no downturn check.'
    m = {int(y): v for y, v in (d.get('margins') or {}).items() if num(v) is not None}
    if d.get('type') != 'separation' or len(m) < 3:
        return b1, 'Downturn check not run: no predecessor segment margins supplied.' if d.get('type') == 'separation' else ''
    ys = sorted(m)[-RULES['window_years']:]
    lows = [(sum(m[y] for y in ys[i:i + 3]) / 3, ys[i]) for i in range(len(ys) - 2) if ys[i + 2] - ys[i] == 2]
    med = st.median(m[y] for y in ys); low, ly = min(lows); ratio = low / med if med > 0 else 0
    drop = ratio < RULES['downturn_line']; nb = max(1, b1 - 1) if drop else b1
    return nb, (f"Downturn check on {d.get('segment', 'the predecessor segment')}, FY{ys[0]}–FY{ys[-1]}: lowest 3-year average margin {pct(low)} (FY{ly}–FY{ly + 2}) ÷ median {pct(med)} = {ratio * 100:.0f}%"
                + (f", below the {RULES['downturn_line'] * 100:.0f}% line, so B1 drops one level ({b1} → {nb})." if drop else f", at or above the {RULES['downturn_line'] * 100:.0f}% line, so no drop."))

def score():
    print('tick  window       n | ROIC ex-gw med / 25th pct  B1 | B2 (b2)      | B3 NOPAT/sh (rev)        | B4 incl-gw  | SBC/op  M2s | M3 | flags')
    for t in KEY:
        if KEY[t] not in RAW: print(t, 'no data'); continue
        m = measures(t, use_facts=os.path.isdir(P('facts')))
        fl = '; '.join(f"FY{f['fy']} {f['text']}" for f in m['flags'])
        print(f"{t:5} FY{m['start']}-{m['L']} {m['n']:2} | {pct(m['b1Med']):>6} / {pct(m['b1Low']):>6} (k={m['b1K']}) {fmt(m['B1']):2} | {fmt(m['B2']):2} ({pct(m['b2'])}) | {fmt(m['B3']):2} {pct(m['b3'])} ({pct(m['revG'])}, {len(m['gYrs'])}y) | {fmt(m['B4']):2} {pct(m['b4Med'])} | {pct(m['sbcR'])} {fmt(m['M2sbc'])} | {fmt(m['M3'])}")
        if fl: print('      perimeter flags:', fl)
        for x in m['dataChecks']: print('      data check:', x)

# ---------------- Result category
SHORT = {'B1': 'return on capital', 'B2': 'cash conversion', 'B3': 'growth', 'B4': 'return on all capital incl. acquisitions',
         'M1': 'CEO ownership', 'M2': 'stock pay and pay vote', 'M3': 'write-downs and share count',
         'I1': 'industry returns', 'I2': 'industry growth', 'I3': 'industry downturns'}
def months_since(d):
    import re
    m = re.search(r'(\d{4})-(\d{2})(?:-(\d{2}))?', str(d or ''))
    if not m: return None
    y, mo = int(m.group(1)), int(m.group(2)); ay, am = int(AS_OF[:4]), int(AS_OF[5:7])
    return (ay - y) * 12 + (am - mo)

def _ymd(d):
    m = re.search(r'(\d{4})-(\d{2})(?:-(\d{2}))?', str(d or ''))
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 1)) if m else None

def ceo_trace(Fc, m):
    """CEO change within RULES['ceo_trace_years']: who, since when, and how many of the years behind M2 and M3 fall under this CEO.
    A fiscal year counts when the CEO was in office for at least 6 of its 12 months. The tag is a display item: it changes no measure or light."""
    m1 = Fc.get('m1') or {}; since = _ymd(m1.get('ceo_since')); ms = months_since(m1.get('ceo_since'))
    if since is None or ms is None or ms >= 12 * RULES['ceo_trace_years']: return None
    fem = fy_end_month(Fc)   # v4.7: the same year-end month as the M3 window test
    sy, sm, sd = since; s_idx = sy * 12 + sm + (1 if sd > 15 else 0)
    under = lambda y: (y * 12 + fem) - s_idx + 1 >= 6
    cnt = lambda ys: (sum(1 for y in ys if under(y)), len(ys))
    m2 = cnt(m.get('sbcYrs') or [])
    imp = cnt(m.get('m3Yrs') or m.get('yrs') or [])
    sh = cnt(list(range(m['dilFrom'] + 1, m['L'] + 1))) if m.get('dilFrom') else None
    vote = (Fc.get('say_on_pay') or {}).get('meeting_date'); vd = _ymd(vote)
    vy = None if vd is None else max(y for y in range(vd[0] - 2, vd[0] + 1) if (y, fem, 31) < vd)   # the vote covers pay for the last fiscal year ended before the meeting
    vote_before = None if vy is None else not under(vy)
    ch = [x for x in (m1.get('ceo_changes_5y') or []) if isinstance(x, dict)]
    name = str(ch[-1].get('to') or '').strip() if ch else re.sub(r'\s*\([^)]*\)', '', str(m1.get('ceo') or '')).split(';')[0].strip()
    tier = 'new' if ms < RULES['new_ceo_months'] else 'recent'
    mon_ = lambda d: (MON[d[1] - 1] + ' ' + str(d[0])) if d else '?'
    parts = [f"M1 is {name or 'the CEO'}'s own holding"]
    if m2[1]: parts.append(f"M2 stock pay: {m2[0]} of {m2[1]} fiscal years under this CEO")
    if vote_before is not None: parts.append(f"M2 pay vote ({str(vote)[:10]}) covered FY{vy} pay, " + ('before this CEO' if vote_before else 'under this CEO'))
    if imp[1]: parts.append(f"M3 write-downs: {imp[0]} of {imp[1]} years")
    if sh: parts.append(f"M3 share count: {sh[0]} of {sh[1]} years")
    hist = '; '.join(f"{mon_(_ymd(x.get('date')))} {x.get('from', '?')} → {str(x.get('to', '?')).rstrip('.')}" for x in ch)
    yrs_ = ms / 12
    text = (f"{'New CEO' if tier == 'new' else 'CEO change'}: {name} since {mon_(since)} ({ms} months)." if ms < 24 else f"CEO change: {name} since {mon_(since)} ({yrs_:.1f} years).")
    text += (f" CEO changes in the last {RULES['ceo_trace_years']} years: {hist}." if hist else '')
    K = m2[0] + imp[0] + (sh[0] if sh else 0); N = m2[1] + imp[1] + (sh[1] if sh else 0)
    text = text.replace('..', '.') + ' ' + '; '.join(parts) + '.' + ((' Most of the years behind M2 and M3 are ' + ('under this CEO.' if K * 2 >= N else 'under earlier CEOs.')) if N else '')
    return dict(name=name, since=f"{sy:04d}-{sm:02d}-{sd:02d}", months=ms, tier=tier, label=('New CEO · ' if tier == 'new' else 'CEO since ') + mon_(since),
                count=len(ch), changes=ch, m2=list(m2), imp=list(imp), sh=list(sh) if sh else None, voteBefore=vote_before, voteFY=vy, underShare=(K / N if N else None), text=text)

def result(c, out, bus, mgt, pe, rem, short, flags_out, Fc, b4=None, i1=None, n_clean=None, L_fy=None):
    """Action label (Research now / Quick look / Research at lower price / Not now) with the reason as the first line, plus re-look signals.
    `pe` here is the combined multiples reading from mult_band() (median percentile of P/E, EV/EBIT, EV/EBITDA)."""
    L = {x['code']: x for x in out}
    weak = lambda f, lts: [SHORT.get(x['code'], x['code']) for x in out if x['factor'] == f and x.get('light') in lts]
    m1 = Fc.get('m1') or {}; ms = months_since(m1.get('ceo_since'))
    new_ceo = ms is not None and 0 <= ms < RULES['new_ceo_months']
    signals = []
    if new_ceo: signals.append(f"new CEO since {str(m1.get('ceo_since'))[:7]}")
    signals += [f.split(' after the latest')[0].replace('Business changing: ', 'business changing: ') for f in flags_out if f.startswith('Business changing')]
    pct = pe.get('pct') if pe.get('band') else None
    if rem:
        cat = 'Pass for now'; why = ['accounting red flag: ' + '; '.join(rem)]
        if bus['light'] == 'r': why.append('weak business: weak on ' + ', '.join(weak('Business', ('r',))))
    elif short:   # v4.4 (user, 2026-10-23): short history is tested before a weak Business light; the scores are for information only
        cat = 'Too early to judge'; why = ['short history: too few clean years on the current business to judge it']
        if pct is not None: why.append(f"multiples at the {ordn(pct)} percentile")
    elif bus['light'] == 'r':
        cat = 'Pass for now'; why = ['weak business: weak on ' + ', '.join(weak('Business', ('r',)))]
    elif bus['light'] == 'g' and mgt['light'] != 'r' and not short:
        if pct is not None and pct <= RULES['research_now_pe']:
            cat = 'Research now'; why = [f"good business; multiples at the {ordn(pct)} percentile of their own history (median of P/E, EV/EBIT, EV/EBITDA), below their usual level (not a valuation: the price still has to be checked against the 15% hurdle)"]
        else:
            cat = 'Watchlist'; why = [f"good business; multiples at the {ordn(pct)} percentile of their own history" if pct is not None else 'good business; multiples not meaningful today']
    elif short or bus['light'] == 'range':
        cat = 'Too early to judge'; why = []
        if short: why.append('short history: too few clean years on the current business to judge it')
        if bus['light'] == 'range': why.append('a business measure is missing and the Business light depends on it')
        if pct is not None: why.append(f"multiples at the {ordn(pct)} percentile")
    else:
        cat = 'Average business'; why = []
        if bus['light'] == 'y':
            wy, wr = weak('Business', ('y',)), weak('Business', ('r',))
            why.append('business average: average on ' + ', '.join(wy) + ('; weak on ' + ', '.join(wr) if wr else '') if wy or wr else 'business average')
        if mgt['light'] == 'r': why.append('good business but weak management record, weak on ' + ', '.join(weak('Management', ('r',))))
        if pct is not None: why.append(f"multiples at the {ordn(pct)} percentile")
    # ---- action label: answers "should I spend research time on this now?"; the reason becomes the first line
    kind = {'Research now': 'good', 'Watchlist': 'good', 'Average business': 'average', 'Too early to judge': 'early'}.get(cat) or ('redflag' if rem else 'weak')
    cheaper = pe.get('direction') == 'cheaper'
    if kind == 'good': action = 'Research now' if ((pct is not None and pct <= RULES['research_now_pe']) or (cheaper and RULES['cheaper_counts'])) else 'Research at lower price'
    elif kind == 'average' and pct is not None and pct <= RULES['low_in_range_pe']: action = 'Quick look'
    else: action = 'Not now'
    TINY = {'B1': 'returns', 'B2': 'cash conversion', 'B3': 'growth', 'B4': 'returns incl. deals', 'M1': 'CEO ownership', 'M2': 'stock pay', 'M3': 'write-downs/dilution'}
    tw = lambda f, lt: [TINY.get(x['code'], x['code']) for x in out if x['factor'] == f and x.get('light') == lt]
    mon = lambda d: (lambda m: f"{['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][int(m.group(2)) - 1]} {m.group(1)}" if m else str(d))(__import__('re').search(r'(\d{4})-(\d{2})', str(d)))
    RFS = {'Material weakness': 'material weakness', 'SEC AAER': 'SEC enforcement (AAER)', '8-K Item 4.02': 'restatement (8-K 4.02)', 'Restatement': 'error restatement', 'Modified audit': 'modified audit opinion', 'Accounting regulator': 'regulator finding'}
    avg_txt = lambda: '; '.join(x for x in (('average on ' + ', '.join(tw('Business', 'y'))) if tw('Business', 'y') else '', ('weak on ' + ', '.join(tw('Business', 'r'))) if tw('Business', 'r') else '') if x)
    sym = {'USD': '$', 'EUR': '€', 'GBP': '£'}.get(pe.get('cur') or '', (pe.get('cur') or '') + ' ')
    lines = []
    d1 = ((pe.get('level') or {}).get('1') or {}).get('dev')
    if action == 'Research now' and not (pct is not None and pct <= RULES['research_now_pe']):
        lines.append(f"Good business, getting cheaper: multiples {abs(d1) * 100:.0f}% below their 1-year level and {abs(pe['level']['1']['agoChg']) * 100:.0f}% below a year ago")
        lines.append(f"Still above their usual level ({ordn(pct)})" if pct is not None else 'Long-run level not meaningful')
    elif action == 'Research now':
        lines.append(f"Good business, multiples below their usual level ({ordn(pct)})")
        if pe.get('trigger') and pe.get('price'):
            gap = pe['price'] / pe['trigger'] - 1
            lines.append(f"Research line {sym}{pe['trigger']:,.2f}; price {abs(gap) * 100:.0f}% below it" + (' — close' if gap > -RULES['near_line_price'] else ''))
    elif action == 'Research at lower price':
        if pct is not None:
            lines.append(f"Good business, multiples above their usual level ({ordn(pct)})")
            if pe.get('trigger') and pe.get('price'):
                lines.append(f"Research below {sym}{pe['trigger']:,.2f} ({(pe['trigger'] / pe['price'] - 1) * 100:+.0f}% from today)" + (' — close' if pct - RULES['research_now_pe'] <= RULES['near_line_pts'] else ''))
        else: lines.append('Good business; multiples not meaningful today')
    elif action == 'Quick look':
        lines.append(f"Average business, but multiples low in their own history ({ordn(pct)})")
        if avg_txt(): lines.append('Check why it is ' + avg_txt())
    else:
        if kind == 'redflag': lines.append('Accounting red flag: ' + ', '.join(next((v for k2, v in RFS.items() if r.startswith(k2)), r) for r in rem) + '; revisit when resolved')
        elif kind == 'weak': lines.append('Weak business: weak on ' + ', '.join(tw('Business', 'r')))
        elif kind == 'early':
            if short and n_clean is not None and L_fy:
                lines.append(f"Too early: only {n_clean} clean years on the current business")
                lines.append(f"Revisit after FY{L_fy + RULES['short_min_years'] - n_clean} results")
            else: lines.append('Too early: a missing measure decides the Business light')
        else:
            lines.append('Average business, ' + (f"multiples not low in their own history ({ordn(pct)})" if pct is not None else 'multiples not meaningful'))
            if bus['light'] == 'g' and mgt['light'] == 'r':   # run fix 2026-10-23: green Business with a red Management light is 'average' for the label; say why
                lines.append('Business light green, but weak management record: weak on ' + ', '.join(tw('Management', 'r')))
            else:
                lines.append((avg_txt() or 'Business light yellow').capitalize() + ('' if mgt['light'] != 'r' else '; weak management record'))
    if action != 'Not now' and b4 is not None and i1 is not None and i1 != float('inf'):
        d = b4 - i1
        lines.append(f"Returns {b4 * 100:.1f}% vs peers {i1 * 100:.1f}%: " + ('above' if d > .01 else 'below' if d < -.01 else 'in line'))
        why.append(f"return on all capital {b4 * 100:.1f}% (B4, with amortization added back) against the peer median {i1 * 100:.1f}% over the same years (amortization on the normalized source basis, with the established US-peer FocusAlpha fill; see source_ledger.json)")
    if pe.get('disagree') and action != 'Not now':
        dz = pe['disagree']; lines.append(f"Multiples disagree: {dz['hi']} {ordn(dz['hiPct'])}, {dz['lo']} {ordn(dz['loPct'])}; check why")
    sig = []
    if new_ceo: sig.append(f"new CEO since {mon(m1.get('ceo_since'))}")
    for f in flags_out:
        if f.startswith('Business changing'):
            import re as _re
            mm = _re.match(r'Business changing: (.+?) \(.*?about (\d+)% of revenue\)', f)
            sig.append(f"{mm.group(1).split(' (')[0]} deal, ~{mm.group(2)}% of revenue" if mm else 'large deal')
    for f in flags_out:
        if f.startswith('Past SEC enforcement'):
            mm = __import__('re').match(r'Past SEC enforcement: (.+?) \((\d{4})[^)]*\), misconduct ([^;]+);', f)
            sig.append(f"past SEC enforcement, {mm.group(1)} ({mm.group(2)}) for {mm.group(3)} accounting" if mm else 'past SEC enforcement')
    if sig: lines.append(('Re-look signal: ' if action in ('Not now', 'Quick look') else 'Note: ') + '; '.join(sig))
    relook = signals if action in ('Not now', 'Quick look') else []
    caution = signals if action in ('Research now', 'Research at lower price') else []
    return dict(cat=action, kind=kind, why=why, relook=relook, caution=caution, newCeo=new_ceo, lines=lines, pct=pct)

# ---------------- facts -> management measures and red flags
def ev_list(items, n=3):
    out = []
    for e in (items or [])[:n]:
        if not isinstance(e, dict): continue
        fact = e.get('fact', '') or ''
        if e.get('quote'): fact += (' ' if fact else '') + f"“{str(e['quote']).strip()[:300]}”"
        out.append(dict(fact=fact, source=e.get('source', ''), url=e.get('url') or '', tag='Fact'))
    return out

def red_flags(t, Fc):
    rf = Fc.get('red_flags') or {}; out = []
    since402, sinceA = years_ago(RULES['redflag_402_years']), years_ago(RULES['redflag_aaer_years'])
    def dated(lst, since):
        keep = []
        for x in lst or []:
            dt = (x.get('date') if isinstance(x, dict) else None) or ''
            if not dt or str(dt)[:10] >= since: keep.append(x)
        return keep
    if Fc.get('sec_registrant', True):
        for x in dated(rf.get('item_402_recent') or rf.get('item_402_since_2023_10_20'), since402):
            out.append(('8-K Item 4.02 non-reliance', x))
        ic_ = rf.get('icfr') or {}
        mc, ao = str(ic_.get('management_conclusion', '')).lower(), str(ic_.get('auditor_opinion', '')).lower()
        if 'not effective' in mc or 'ineffective' in mc or 'adverse' in ao or (ic_.get('material_weaknesses') or []):
            out.append((f"Material weakness at FY-end {ic_.get('fiscal_year_end', '')}", dict(detail='; '.join(map(str, ic_.get('material_weaknesses') or []))[:300], management=ic_.get('management_conclusion'), auditor=ic_.get('auditor_opinion'))))
        for x in rf.get('aaer_recent') or rf.get('aaer_since_2021_10_20') or []:
            d = x.get('date') if isinstance(x, dict) else None
            if RULES['redflag_aaer_basis'] == 'conduct' and isinstance(x, dict) and x.get('conduct_end'): d = x['conduct_end']
            if not d or str(d)[:10] >= sinceA: out.append(('SEC AAER', x))
    else:
        ns = rf.get('non_sec') or {}
        for x in ns.get('error_restatement') or []:
            if isinstance(x, dict) and (x.get('is_error_per_company') is False or x.get('is_error') is False): continue   # re-presentation, not an error
            out.append(('Restatement to correct an error', x))
        mo = ns.get('modified_audit_opinion')
        if mo not in (None, False, '', 'none', 'no', 'unmodified') and not str(mo).lower().startswith(('no', 'unmodified', 'unqualified', 'false')):
            out.append(('Modified audit opinion', mo))
        for x in ns.get('regulator_findings') or []: out.append(('Accounting regulator finding', x))
    for lab, why in (CO[t].get('red_flag_overrides') or {}).items():
        out = [o for o in out if o[0] != lab] if why == 'clear' else out + [(lab, why)]
    return out

def short_desc(x):
    if isinstance(x, dict):
        return ' · '.join(str(x.get(k)) for k in ('date', 'number', 'subject', 'description', 'detail', 'management', 'auditor', 'name') if x.get(k))[:260]
    return str(x)[:260]

# ---------------- P/E band
def pe_from_default(): return years_ago(RULES['window_years'])

def clean_start(c):
    """First date of every multiple's window: config pe_from (merger, separation, listing break) plus deal_delay_months, else 10 years."""
    pf = c.get('pe_from')
    if not pf: return pe_from_default()
    y, m = int(pf[:4]), int(pf[5:7]) + RULES['deal_delay_months']
    y += (m - 1) // 12; m = (m - 1) % 12 + 1
    return f"{y}-{m:02d}-{pf[8:10]}"

def qtile(a, x):
    s2 = sorted(a); i = (len(s2) - 1) * x; lo, hi = math.floor(i), math.ceil(i); return round(s2[lo] + (s2[hi] - s2[lo]) * (i - lo), 1)
MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
_d6 = lambda iso: iso[2:10].replace('-', '')
_iso = lambda d6: '20' + d6[:2] + '-' + d6[2:4] + '-' + d6[4:]
r0 = lambda x: int(Decimal(str(x)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def pe_band(t):
    k = KEY[t]; c = CO[t]; p = PE.get(k) or {'d': '', 'r': ''}
    ds = p['d'].split(',') if p.get('d') else []; rs = p['r'].split(',') if p.get('r') else []
    frm = clean_start(c); f6 = frm[2:].replace('-', '')
    ser = [(a, float(b) if b not in ('', None) else None) for a, b in zip(ds, rs) if a >= f6]
    pos = [v for _, v in ser if v is not None and v > 0]
    now = ser[-1][1] if ser else None; yrs = (len(ser) / 252) if ser else 0
    stale = None; ov = c.get('pe_now_override')
    if ser:
        last = datetime.date(2000 + int(ser[-1][0][:2]), int(ser[-1][0][2:4]), int(ser[-1][0][4:]))
        if (datetime.date.fromisoformat(AS_OF) - last).days > RULES['pe_stale_days']: stale = last.isoformat()
    if ov: now = num(ov.get('value'))
    d6 = lambda s: '20' + s[:2] + '-' + s[2:4] + '-' + s[4:]
    pe = dict(fwd=p.get('fwd'), price=p.get('price'), cur=p.get('cur'), now=now, n=len(ser), from_=d6(ser[0][0]) if ser else None, to=d6(ser[-1][0]) if ser else None,
              years=round(yrs, 1), posShare=round(len(pos) / len(ser) * 100) if ser else 0, from_why=c.get('pe_from_why', ''),
              stale=stale, override=(ov or {}).get('why'))
    if ov: pe['to'] = ov.get('date', pe['to'])
    def q(a, x):
        s = sorted(a); i = (len(s) - 1) * x; lo, hi = math.floor(i), math.ceil(i); return round(s[lo] + (s[hi] - s[lo]) * (i - lo), 1)
    band = None
    if now is not None and now > 0 and len(pos) >= RULES['pe_min_pos_days'] and pe['posShare'] >= RULES['pe_min_pos_share']:
        pe.update(pct=round(sum(1 for v in pos if v <= now) / len(pos) * 100), p10=q(pos, .1), p33=q(pos, 1 / 3), p50=q(pos, .5), p67=q(pos, 2 / 3), p90=q(pos, .9))
        band = 'meaningful'
        pe['why'] = ''
    else:
        pe['why'] = 'no P/E history' if not ser else 'loss-making today (negative trailing P/E)' if (now is None or now <= 0) else f"positive P/E on only {pe['posShare']}% of days" if pe['posShare'] < RULES['pe_min_pos_share'] else 'too little history'
    pe['band'] = band; pe['short'] = yrs < RULES['pe_short_years']
    pe['ratio'] = round(now / pe['fwd'], 2) if (now and now > 0 and pe['fwd'] and pe['fwd'] > 0) else None
    pe['distorted'] = pe['ratio'] is not None and pe['ratio'] > RULES['pe_distorted']
    wk = [f"{d6(ser[i][0])[:7]}|{'' if ser[i][1] is None or ser[i][1] <= 0 else ser[i][1]}" for i in range(0, len(ser), 5)]
    if ser and (len(ser) - 1) % 5: wk.append(f"{d6(ser[-1][0])[:7]}|{'' if ser[-1][1] is None or ser[-1][1] <= 0 else ser[-1][1]}")
    pe['wk'] = ','.join(wk)
    return pe

MNAME = {'pe': 'P/E', 'ebit': 'EV/EBIT', 'ebitda': 'EV/EBITDA'}
def _ser(block, f6=None):
    if not block or not block.get('d'): return []
    out = [(a, float(b) if b not in ('', None) else None) for a, b in zip(block['d'].split(','), block['r'].split(','))]
    return [x for x in out if f6 is None or x[0] >= f6]
def _at(ser, d6, max_gap=10):
    """Last value on or before d6, if it is no more than max_gap days earlier."""
    prior = [x for x in ser if x[0] <= d6]
    if not prior: return None
    gap = (datetime.date.fromisoformat(_iso(d6)) - datetime.date.fromisoformat(_iso(prior[-1][0]))).days
    return prior[-1] if gap <= max_gap else None

def mult_band(t, pe):
    """P/E, EV/EBIT and EV/EBITDA each placed in its own history (same window); the median percentile is the reading.
    Trigger = median of the three share prices at which each multiple would sit at its own median.
    Trend = EV/EBITDA change over 3, 5 and 10 years, split into enterprise value and EBITDA; P/E split (price, EPS) in the hover text."""
    k = KEY[t]; c = CO[t]; e = EV.get(k) or {}; asof = datetime.date.fromisoformat(AS_OF)
    frm = clean_start(c); f6 = _d6(frm)
    tev = _ser(e.get('tev')); px = _ser(e.get('px')); pes = _ser(PE.get(k))
    tev_now = tev[-1][1] if tev else None
    ms = {'pe': dict(name='P/E', now=pe['now'], pct=pe.get('pct') if pe['band'] else None, p50=pe.get('p50') if pe['band'] else None,
                     why=pe.get('why', ''), note=pe.get('override') or (f"daily P/E ends {pe['stale']}" if pe.get('stale') else ''))}
    for m in ('ebit', 'ebitda'):
        sr = _ser(e.get(m), f6); pos = [v for _, v in sr if v is not None and v > 0]
        d = dict(name=MNAME[m], now=None, pct=None, p50=None, why='', note='')
        if not sr: d['why'] = 'no data in the window'; ms[m] = d; continue
        now = sr[-1][1]; last = sr[-1][0]
        if (asof - datetime.date.fromisoformat(_iso(last))).days > RULES['pe_stale_days'] and tev_now and now:
            tl = _at(tev, last)
            if tl and tl[1]:
                d['note'] = (f"the normalized source data (see source_ledger.json) series ends {_iso(last)}; today's value = {now}× × enterprise value today {tev_now:,.0f} ÷ enterprise value on {_iso(last)} {tl[1]:,.0f} "
                             f"(operating profit as of that date)")
                now = round(now * tev_now / tl[1], 1)
        d['now'] = now; share = round(len(pos) / len(sr) * 100)
        if now is None or now <= 0: d['why'] = 'operating profit negative today'
        elif len(pos) < RULES['pe_min_pos_days']: d['why'] = 'under one year in the window'
        elif share < RULES['pe_min_pos_share']: d['why'] = f'positive on only {share}% of days'
        else: d['pct'] = round(sum(1 for v in pos if v <= now) / len(pos) * 100); d['p50'] = qtile(pos, .5)
        ms[m] = d
    ok = [m for m in ('pe', 'ebit', 'ebitda') if ms[m]['pct'] is not None]
    pct = r0(st.median([ms[m]['pct'] for m in ok])) if ok else None
    dis = None
    if len(ok) >= 2:
        hi = max(ok, key=lambda m: ms[m]['pct']); lo = min(ok, key=lambda m: ms[m]['pct'])
        if ms[hi]['pct'] - ms[lo]['pct'] >= RULES['mult_disagree_pts']: dis = dict(hi=MNAME[hi], hiPct=ms[hi]['pct'], lo=MNAME[lo], loPct=ms[lo]['pct'])
    # ---- trigger: share price at which each multiple sits at its own median (enterprise value moves one for one with market value; net debt held)
    price = pe.get('price'); mc = num((PE.get(k) or {}).get('mcap')); mc = mc / 1e6 if mc else None
    # net debt = enterprise value − market value ON THE SAME DAY: the market value is re-priced to the enterprise-value date with the
    # daily price series (shares = market value ÷ price from the same pull; the price series may be in pence, so only its unit is matched)
    nd = None
    if tev_now and mc and price and px:
        u = 10 ** round(math.log10(price / px[-1][1])) if px[-1][1] else 1
        pt = _at(px, tev[-1][0])
        if pt: nd = tev_now - (mc / price) * pt[1] * u
    imp = {}
    for m in ok:
        d = ms[m]
        if m == 'pe': imp[m] = price * d['p50'] / d['now'] if price else None
        elif tev_now and mc and price and nd is not None: imp[m] = (tev_now * d['p50'] / d['now'] - nd) / (mc / price)
        if imp.get(m) is not None: d['implied'] = round(imp[m], 2)
    iv = [v for v in imp.values() if v is not None]
    trig = round(st.median(iv), 2) if iv else None
    # ---- trend: EV/EBITDA over 3, 5, 10 years; 'since <clean date>' when a horizon starts before the clean window
    eb = _ser(e.get('ebitda')); eb_now = ms['ebitda']['now']
    first = eb[0][0] if eb else None
    clean6 = f6 if c.get('pe_from') else first
    px_now = px[-1][1] if px else None
    def entry(start6, label, years):
        a = _at(eb, start6); v = _at(tev, start6)
        if not (eb_now and eb_now > 0 and tev_now): return dict(label=label, na='EBITDA negative today', short='EBITDA negative today')
        if not a or not v: return dict(label=label, na=f"no data on {_iso(start6)}", short='no data then')
        if a[1] is None or a[1] <= 0: return dict(label=label, na=f"EBITDA was negative on {_iso(a[0])}", short='EBITDA negative then')
        mch = eb_now / a[1] - 1; evch = tev_now / v[1] - 1; ebch = (1 + evch) / (1 + mch) - 1
        o = dict(label=label, years=years, date=_iso(a[0]), multY=a[1], mult=eb_now, chg=round(mch, 4), evChg=round(evch, 4), ebitdaChg=round(ebch, 4),
                 dir='falling' if mch < -RULES['pe_trend_move'] else 'rising' if mch > RULES['pe_trend_move'] else 'steady')
        pa = _at(pes, start6); pp = _at(px, start6)
        if pe['now'] and pe['now'] > 0 and pa and pp and px_now:
            if pa[1] is not None and pa[1] > 0:
                pch = px_now / pp[1] - 1; pech = pe['now'] / pa[1] - 1
                o.update(peY=pa[1], peChg=round(pech, 4), priceChg=round(pch, 4), epsChg=round((1 + pch) / (1 + pech) - 1, 4))
            else: o['peNa'] = 'P/E negative then'
        return o
    rows, one, unclean = [], None, []
    for n in RULES['trend_years']:
        st6 = _d6(years_ago(n))
        if clean6 and st6 < clean6:
            if n > 1: unclean.append(n)
            continue
        en = entry(st6, f"{n} yr", n)
        if n == 1: one = en
        else: rows.append(en)
    if unclean and clean6:
        yrs = round((asof - datetime.date.fromisoformat(_iso(clean6))).days / 365.25, 1)
        why = (f"{c.get('pe_from_why') or 'business change'} ({c['pe_from'][:7]}) plus {RULES['deal_delay_months']} months" if c.get('pe_from') else f"first trading day {_iso(clean6)}")
        lab = f"since {MON[int(clean6[2:4]) - 1]} {2000 + int(clean6[:2])} ({yrs:g} yr)"
        if yrs >= RULES['trend_min_years']:
            en = entry(clean6, lab, yrs); en['why'] = f"{', '.join(str(n) for n in unclean)}-year start is before the clean window ({why})"; rows.append(en)
        else:
            rows.append(dict(label=f"{unclean[0]}–{unclean[-1]} yr" if len(unclean) > 1 else f"{unclean[0]} yr", na=f"clean window starts {_iso(clean6)} ({why}); under {RULES['trend_min_years']} year since",
                             short=(f"business changed {MON[int(c['pe_from'][5:7]) - 1]} {c['pe_from'][:4]}" if c.get('pe_from') else f"listed {MON[int(clean6[2:4]) - 1]} {2000 + int(clean6[:2])}")))
    # ---- today against the stock's own median over 1, 3, 5, 10 years (clean window only); median across the three multiples
    lvl = {}
    sers = {'pe': pes, 'ebit': _ser(e.get('ebit')), 'ebitda': eb}
    lo6 = max(clean6 or '000000', min((x[0][0] for x in sers.values() if x), default='000000'))
    for n in RULES['level_years']:
        eff = max(_d6(years_ago(n)), lo6); yrs = round((asof - datetime.date.fromisoformat(_iso(eff))).days / 365.25, 1)
        per = {}
        for mk, sr in sers.items():
            nw = ms[mk]['now']
            vals = [v for d, v in sr if d >= eff and v is not None and v > 0]
            if nw and nw > 0 and len(vals) >= RULES['level_min_days']: per[mk] = dict(med=round(st.median(vals), 1), dev=round(nw / st.median(vals) - 1, 4))
        if per: lvl[str(n)] = dict(dev=round(st.median([x['dev'] for x in per.values()]), 4), years=yrs, short=yrs < n - 0.05, per=per)
    one_y = lvl.get('1')
    direction = None
    if one_y and one_y['years'] >= .9:   # needs close to a full year of clean history
        ago6 = _d6(years_ago(1)); ag = {}
        for mk, sr in sers.items():
            a = _at(sr, ago6, 31); nw = ms[mk]['now']   # up to a month earlier when the data has a gap (MTU: none from 29 Sep 2025 to 2 Jan 2026)
            if a and a[1] and a[1] > 0 and nw and nw > 0: ag[mk] = dict(then=a[1], date=_iso(a[0]), chg=round(nw / a[1] - 1, 4))
        one_y['ago'] = ag
        one_y['agoChg'] = round(st.median([x['chg'] for x in ag.values()]), 4) if ag else None
        ac = one_y['agoChg']
        if one_y['dev'] <= -RULES['cheaper_move'] and ac is not None and ac < 0: direction = 'cheaper'
        elif one_y['dev'] >= RULES['cheaper_move'] and ac is not None and ac > 0: direction = 'dearer'
        elif ac is None: direction = None
        else: direction = 'steady'
    notes = [f"{d['name']}: {d['note']}" for d in ms.values() if d.get('note')]
    return dict(level=lvl, direction=direction, netDebt=None if nd is None else round(nd, 1), band='meaningful' if ok else None, pct=pct, n=len(ok), metrics=ms, disagree=dis, trigger=trig, cur=pe.get('cur'), price=price,
                window=frm, windowWhy=(f"{c.get('pe_from_why')} ({c['pe_from']}) plus {RULES['deal_delay_months']} months" if c.get('pe_from') else '10 years'),
                why='; '.join(f"{d['name']}: {d['why']}" for d in ms.values() if d['why']) if not ok else '',
                trends=rows, one=one, notes=notes)

# ---------------- assembly
def build(t, RANK):
    c = CO[t]; MN = c.get('measure_notes') or {}; m = measures(t); Fc = facts(t); cur = m['cur'] or ''
    out = []; flags_out = []
    win = f"FY{m['yrs'][0]}–FY{m['yrs'][-1]} ({m['n']} yrs)" if m['yrs'] else 'none'
    short_lbl = f"short history ({m['n']} years)" if m['short'] else ''
    # ---- B1
    yrsx = m['yrs']
    ins = [['Window', win + (' — current perimeter' if m['perim'] else '')],
           ['ROIC by year (capital excl. goodwill)', ', '.join(f"FY{y % 100:02d} {pct(v, 0)}" + ('*' if y in m['fallbackYrs'] else '') for y, v in zip(yrsx, m['roicEx']))]]
    if m['b1Med'] is None: calc = 'No year with positive capital.' if m['B1'] is None else 'NOPAT ≤ 0 → 1.'
    else:
        calc = f"Median {pct(m['b1Med'])} → {m['b1SM']}; {ordn(m['b1K'])} lowest of {m['b1N']} years {pct(m['b1Low'])} → {m['b1SL']}; B1 = lower = {m['B1raw']}"
        if m['B1full'] != m['B1raw']: calc += f"; downturn check → {m['B1full']}"
        if m['B1post'] is not None:
            post_txt = f"after the FY{m['postFrom'] - 1} deal: average {fyspan(m['postYrs'])} {pct(m['b1Post'])} → {m['B1post']}"
            calc = (post_txt[0].upper() + post_txt[1:] + '; full window: ' + calc + f"; B1 = lower of full window and after the deal = {m['B1']}") if m['B1post'] < m['B1full'] else (calc + '; ' + post_txt + f"; B1 = lower of full window and after the deal = {m['B1']}")
        elif m['postFrom']: calc += f"; deal in FY{m['postFrom'] - 1}: no full year after it yet, so the full window is used"
    if m['short']: calc = f"{short_lbl.capitalize()}: shown for information. " + calc
    note = ' '.join(x for x in (MN.get('B1', ''), m['downturnNote'], ('* capital excluding goodwill was ≤ 0, so ROIC including goodwill is used for that year.' if m['fallbackYrs'] else ''),
                                (f"Rank in this run: {RANK['B1'][t]} of {len(RANK['B1'])} on median." if t in RANK['B1'] else '')) if x)
    out.append(dict(code='B1', name='Return on capital, excluding goodwill', factor='Business', kind='Data', score=m['B1'], inputs=ins, calc=calc, note=note,
                    rule='NOPAT = (operating income + amortization of acquired intangibles + goodwill/intangible impairments) × 0.75. Capital = debt + leases + equity − cash − goodwill (acquired intangibles stay in), average of opening and closing. Median: ≥25% → 5, ≥15% → 4, ≥10% → 3, ≥6% → 2, <6% → 1. 25th-percentile year (3rd lowest of 10): ≥15% → 5, ≥10% → 4, ≥6% → 3, else 2. B1 = lower. Fewer than 3 clean years → short history, manual review. A deal flagged only by the goodwill test keeps the window; B1 is then the lower of this and the score on the average of the years after the deal (median thresholds).'))
    # ---- B2
    b2t_note = f" (raw {pct(m['b2tRaw'])} outside 0–50%, so 25% used)" if m['b2tRaw'] is not None and abs(m['b2tRaw'] - m['b2t']) > 1e-6 else ''
    ins = [['Years', str(m['b2Years'])], ['Cumulative FCF (CFO + capex − SBC), m', m0(m['b2F'])], ['Own tax rate t', pct(m['b2t']) + b2t_note],
           ['Net interest × (1 − t), m', m0(m['b2Int'] * (1 - m['b2t']))], ['FCF before interest, m', m0(m['b2Num'])], ['(Operating income + impairments) × (1 − t), m', m0(m['b2Den'])]]
    calc = 'No cash flow years.' if m['B2'] is None else (f"FCF {m0(m['b2F'])} or NOPAT {m0(m['b2Den'])} ≤ 0 → 1" if m['b2'] is None else f"{m0(m['b2Num'])} ÷ {m0(m['b2Den'])} = {pct(m['b2'])} → {m['B2']}")
    note = ' '.join(x for x in (MN.get('B2', ''), 'Stock compensation missing in the data for some years and not subtracted.' if m['sbcMissingYears'] else '') if x)
    out.append(dict(code='B2', name='Cash conversion', factor='Business', kind='Data', score=m['B2'], inputs=ins, calc=calc, note=note,
                    rule='(FCF + net interest × (1 − t)) ÷ ((operating income + impairments) × (1 − t)) over the B1 window; operating cash flow from continuing operations. ≥100% → 5, ≥90% → 4, ≥75% → 3, ≥50% → 2, else 1.'))
    # ---- B3
    gy = m['gYrs']; e = RULES['growth_end_years']
    ins = [['Window', (f"FY{gy[0]}–FY{gy[-1]} ({len(gy)} yrs)" if gy else 'none') + (f" — starts FY{m['gStart']}: {m['gWhy']}" if m['gWhy'] else '')],
           ['NOPAT per diluted share by year', ', '.join(f"FY{y % 100:02d} {v:.2f}" for y, v in m['nps'].items())]]
    if m['B3'] is not None:
        calc = f"Start = median FY{gy[0]}–FY{gy[e - 1]} = {m['b3A']:.2f}; end = median FY{gy[-e]}–FY{gy[-1]} = {m['b3B']:.2f}; ({m['b3B']:.2f} ÷ {m['b3A']:.2f})^(1/{m['b3Exp']}) − 1 = {pct(m['b3'])} → {m['B3']}"
    else: calc = f"Not scored: {m['b3Note']}."
    b3, b3kind, b3name, b3gap, b3rule_extra, b3ev = m['B3'], 'Data', 'Growth in NOPAT per share', None, '', []
    sub = _load(P('facts', f'{t}_b3sub.json'), None)
    if b3 is None and sub and sub.get('accepted') is False:
        calc += f" A filed substitute was collected but not used: {sub.get('reject_reason', '')}"
        ins.append([f"Filed substitute (not used): {sub.get('measure', '')}", ', '.join(f"FY{int(y) % 100:02d} {r.get('op')} ({r.get('op_basis', '')})" for y, r in sorted((sub.get('years') or {}).items()) if isinstance(r, dict) and int(y) > m['L'] - RULES['window_years'])])
    elif b3 is None and sub:
        bases = {r.get('op_basis') for y, r in (sub.get('years') or {}).items() if isinstance(r, dict) and r.get('comparable') is not False and int(y) > m['L'] - RULES['window_years'] and r.get('op_basis')}
        if len(bases) > 1: sub = dict(sub, accepted=False, reject_reason=f"the filed years use {len(bases)} different profit definitions ({', '.join(sorted(bases))}); one definition is needed across the window.")
    if b3 is None and sub and sub.get('accepted') is not False:
        ys = {}
        for y, r in (sub.get('years') or {}).items():
            y = int(y)
            if y < m['L'] - RULES['window_years'] + 1 or y > m['L'] or not isinstance(r, dict) or r.get('comparable') is False: continue
            v = num(r.get('op')) if r.get('op') is not None else (sum(num(r[k]) for k in r if k.endswith('_op') and num(r[k]) is not None) if any(k.endswith('_op') and num(r[k]) is not None for k in r) else None)
            if v is not None: ys[y] = v
        yy = sorted(ys)
        ins.append([f"Substitute: {sub.get('measure', 'segment operating profit')} ({sub.get('currency', '')}m, filed)", ', '.join(f"FY{y % 100:02d} {ys[y]:,.0f}" for y in yy)])
        if len(yy) >= RULES['growth_min_years']:
            a = st.median(ys[y] for y in yy[:e]); b = st.median(ys[y] for y in yy[-e:]); span = yy[-2] - yy[1]
            if a > 0 and b > 0:
                g = (b / a) ** (1 / span) - 1; b3 = s_b3(g)
                calc = (f"NOPAT per share has only {m['b3Note']}, so B3 uses the filed substitute. Start = median FY{yy[0]}–FY{yy[e - 1]} = {a:,.0f}; end = median FY{yy[-e]}–FY{yy[-1]} = {b:,.0f}; "
                        f"({b:,.0f} ÷ {a:,.0f})^(1/{span}) − 1 = {pct(g)} → {b3}")
                b3kind, b3name = 'Fact (substitute)', 'Growth: filed substitute'
                b3rule_extra = ' Substitute when the company\'s own history is too short after a separation: growth of the same businesses\' segment operating profit from the predecessor\'s filings (not per share), same median end-point method, needs 6 comparable years.'
                b3ev = [dict(fact=f"FY{y}: " + ', '.join(f"{k} {v}" for k, v in r.items() if k not in ('filing', 'url', 'quote', 'comparable')), source=r.get('filing', ''), url=r.get('url', ''), tag='Fact')
                        for y, r in sorted((sub.get('years') or {}).items()) if isinstance(r, dict)][-12:]
            else: calc += ' The filed substitute has an end point at or below zero, so it cannot score either.'
        else: calc += f" The filed substitute has {len(yy)} comparable years in the window (needs {RULES['growth_min_years']})."
    if b3 is None: b3gap = (f"only {len(m['gYrs'])} years of history (needs {RULES['growth_min_years']})" if 'needs' in m['b3Note'] else m['b3Note']) + (f" (window starts FY{m['gStart']}: {m['gWhy']})" if m['gWhy'] else '') + (('; filed substitute not used: ' + sub['reject_reason']) if sub and sub.get('reject_reason') else ('; no comparable filed substitute' if sub else '; no filed history before that'))
    rg = (f"Revenue grew {pct(m['revG'])} a year on the same method ({m0(m['revA'])} → {m0(m['revB'])} {cur}m). Information only." if m['revG'] is not None else '')
    out.append(dict(code='B3', name=b3name, factor='Business', kind=b3kind, score=b3, gap=b3gap, evidence=b3ev, inputs=ins, calc=calc, note=' '.join(x for x in (MN.get('B3', ''), rg, (('Source: ' + str((sub or {}).get('source_tool') or 'filings') + '. ' + str((sub or {}).get('notes') or '')) if b3kind != 'Data' else '')) if x),
                    rule='Median of the first 3 years to the median of the last 3 years of the 10-year window; acquisitions stay in; a spin-off/separation or a one-year jump of more than 50% in diluted shares starts the window after it; needs 6 years. ≥12% → 5, ≥8% → 4, ≥5% → 3, ≥2% → 2, else 1.' + b3rule_extra))
    # ---- B4
    ins = [['Window', win], ['ROIC by year (capital incl. goodwill)', ', '.join(f"FY{y % 100:02d} {pct(v, 0)}" for y, v in zip(yrsx, m['roicIn']))]]
    b4full_txt = f"Median {pct(m['b4Med'])} → {m['B4full']}" if m['b4Med'] is not None else ''
    b4post_txt = f"after the FY{m['postFrom'] - 1} deal: average {fyspan(m['postYrs'])} {pct(m['b4Post'])} → {m['B4post']}" if m['B4post'] is not None else ''
    if b4post_txt and m['B4post'] < m['B4full']: b4full_txt = b4post_txt[0].upper() + b4post_txt[1:] + '; full window: m' + b4full_txt[1:] + f"; B4 = lower of full window and after the deal = {m['B4']}"
    elif b4post_txt: b4full_txt += '; ' + b4post_txt + f"; B4 = lower of full window and after the deal = {m['B4']}"
    elif m['postFrom'] and b4full_txt: b4full_txt += f"; deal in FY{m['postFrom'] - 1}: no full year after it yet, so the full window is used"
    calc = (b4full_txt if m['b4Med'] is not None else ('Capital ≤ 0 every year' + (f" → {m['B4']}" if m['B4'] else ''))) + (' (short history: shown, not used)' if m['short'] else '')
    note = ' '.join(x for x in (MN.get('B4', ''), (f"Rank in this run: {RANK['B4'][t]} of {len(RANK['B4'])}." if t in RANK['B4'] else '')) if x)
    out.append(dict(code='B4', name='Return on all capital, including goodwill', factor='Business', kind='Data', score=m['B4'], inputs=ins, calc=calc, note=note,
                    rule='NOPAT ÷ average (debt + leases + equity − cash), median over the B1 window. Charges for the price paid for acquisitions. ≥15% → 5, ≥12% → 4, ≥9% → 3, ≥6% → 2, <6% → 1. A deal flagged only by the goodwill test keeps the window; B4 is then the lower of this and the score on the average of the years after the deal.'))
    # ---- M1
    f1 = Fc.get('m1') or {}; pe = pe_band(t); mx = mult_band(t, pe)
    sh, sal, price = num(f1.get('shares_owned_excl_options')), num(f1.get('base_salary')), pe['price']
    m1 = None; adj = []
    if f1.get('founder_family_5pct_active') is True: m1 = 5; calc = 'Founder or family holder of 5% or more with an active role → 5'; mult = None
    elif sh is not None and sal and price:
        mult = sh * price / sal; m1 = s_m1(mult); calc = f"{sh:,.0f} shares × {price:,.2f} ÷ {sal:,.0f} = {mult:.1f}× → {m1}"
    else: mult = None; calc = 'Not scored: shares or salary not found.'
    if m1 is not None:
        if f1.get('insiders_net_buyers_24m') is True and m1 < 5: m1 += 1; adj.append('+1 officers and directors net open-market buyers (24 months)')
        if f1.get('ceo_sold_over_30pct_24m') is True:   # v4.7 (user, 2026-10-23): the penalty cannot take M1 below 2
            fl = RULES['m1_sale_floor']
            if m1 > fl: m1 -= 1; adj.append('−1 CEO sold more than 30% of held shares (24 months)')
            else: adj.append(f"CEO sold more than 30% of held shares (24 months): no −1, because the penalty cannot take M1 below {fl} and the holding already scores {m1}")
        if adj: calc += '; ' + '; '.join(adj) + f" → {m1}"
    cut = lambda s, n=200: (s[:n].rsplit(' ', 1)[0] + ' …') if len(s) > n else s
    ins = [['CEO', f"{f1.get('ceo', '–')}" + (f" (since {f1.get('ceo_since')})" if f1.get('ceo_since') else '')], ['Shares owned, excl. options and unvested', m0(sh)],
           ['Shares calculation', cut(str(f1.get('shares_calc') or '–'))], [f"Price ({pe['cur']}; see source ledger)", fmt(price)], [f"Base salary ({f1.get('salary_year', '')})", m0(sal)],
           ['Insider trades, 24 months', cut(str(f1.get('trades_note') or '–'))]]
    evm1 = ev_list(f1.get('evidence'), 4) + ([dict(fact='Shares calculation: ' + str(f1['shares_calc']), source='', url='', tag='Fact')] if len(str(f1.get('shares_calc') or '')) > 200 else []) \
        + ([dict(fact='Insider trades: ' + str(f1['trades_note']), source='', url='', tag='Fact')] if len(str(f1.get('trades_note') or '')) > 200 else [])
    out.append(dict(code='M1', name='CEO ownership', factor='Management', kind='Fact', score=m1, gap=None if m1 is not None else ('not disclosed: ' + ('shares owned' if sh is None else '') + (' and ' if sh is None and not sal else '') + ('base salary' if not sal else '') + ' not published'), inputs=ins, calc=calc, note=MN.get('M1', ''), evidence=evm1,
                    rule="Owned shares (excl. options and unvested awards) × today's price ÷ base salary: ≥30× → 5 (or founder/family ≥5% with an active role), ≥15× → 4, ≥6× → 3, ≥2× → 2, <2× → 1. +1 if officers and directors were net open-market buyers over 24 months; −1 if the CEO sold more than 30% of held shares, but never below 2 (a holding that already scores 1 or 2 shows the result of the selling)."))
    # ---- M2
    sp = Fc.get('say_on_pay') or {}
    vf, va = num(sp.get('for')), num(sp.get('against'))
    vote = (vf / (vf + va)) if (vf is not None and va is not None and vf + va > 0) else num(sp.get('pct_for'))
    if vote is not None and vote > 1: vote /= 100
    sv = s_vote(vote) if vote is not None else None
    parts = [x for x in (m['M2sbc'], sv) if x is not None]
    m2 = min(parts) if parts else None
    c_sbc = (f"Stock comp {m0(m['sbcSum'])} ÷ operating income {m0(m['sbcOp'])} (FY{m['sbcYrs'][0]}–FY{m['sbcYrs'][-1]}) = {pct(m['sbcR'])} → {m['M2sbc']}" if m['M2sbc'] is not None and m['sbcR'] is not None
             else ('Operating income ≤ 0 → 1' if m['M2sbc'] == 1 else 'Stock comp not available'))
    c_vote = (f"say-on-pay {m0(vf)} ÷ ({m0(vf)} + {m0(va)}) = {pct(vote)} → {sv}" if (sv is not None and vf is not None and va is not None) else (f"say-on-pay {pct(vote)} → {sv}" if sv is not None else f"say-on-pay: {sp.get('status') or 'not found'}"))
    calc = f"{c_sbc}; {c_vote}; M2 = lower = {fmt(m2)}"
    ins = [['Stock comp, 5 years, m', m0(m['sbcSum']) if m['sbcYrs'] else 'not in the data'], ['Operating income, same years, m', m0(m['sbcOp']) if m['sbcYrs'] else '–'], ['Latest pay vote', f"{sp.get('meeting_date', '')} · For {m0(vf)} · Against {m0(va)} · Abstain {m0(num(sp.get('abstain')))}" if vf is not None else str(sp.get('status') or '–')]]
    out.append(dict(code='M2', name='Cost of stock pay and the pay vote', factor='Management', kind='Data + Fact', score=m2, gap=None if m2 is not None else 'no stock comp data and no pay vote found', inputs=ins, calc=calc, note=MN.get('M2', ''), evidence=ev_list(sp.get('evidence')),
                    rule='(a) Stock compensation ÷ operating income, sums over the latest 5 fiscal years: <3% → 5, 3–6% → 4, 6–10% → 3, 10–15% → 2, >15% → 1. (b) Latest say-on-pay For ÷ (For + Against): ≥90% → 5, 80–90% → 4, 70–80% → 3, 50–70% → 2, <50% → 1. M2 = lower of the two; one alone if the other is missing.'))
    # ---- M3
    m3y = m['m3Yrs']
    ins = [['Window', (fyspan(m3y) + f" ({len(m3y)} yrs)" if m3y else 'none') + ' — ' + m['m3Why']],
           ['Goodwill and intangible impairments, m', m0(m['impSum'])],
           ['Losses on businesses sold or held for sale, m', (m0(m['dispSum']) + ((' (' + '; '.join(m['dispNote']) + ')') if m['dispNote'] else '')) if m['dispCollected'] else 'not collected in this fact file'],
           ['(Impairments + losses) ÷ average goodwill + intangibles', pct(m['impPct'], 0) if m['impPct'] is not None else '–'],
           [f"Diluted share change (FY{m['dilFrom']} → FY{m['L']})" if m['dilFrom'] else f"Diluted share change from FY{m['L'] - RULES['window_years']}", f"{m['dilChg'] * 100:+.1f}%" if m['dilChg'] is not None else 'no share count that far back']]
    calc = 'Column scores ' + ', '.join(fmt(x) for x in m['M3parts']) + (f"; average rounded down → {m['M3']}" if m['M3'] is not None else '; not scored (needs both columns)')
    m3note = ' '.join(x for x in (MN.get('M3', ''), ('' if m['dispCollected'] else 'Losses on businesses sold or held for sale were not collected for this company (fact file before v4.7), so only impairments count.')) if x)
    out.append(dict(code='M3', name='Capital allocation record', factor='Management', kind='Data', score=m['M3'], gap=None if m['M3'] is not None else ('no share count from 10 years ago (the company was not listed then)' if m['dilChg'] is None else 'no goodwill or impairment data'), inputs=ins, calc=calc, note=m3note,
                    rule=f"Window: the current CEO's fiscal years when the B1 window holds at least {RULES['m3_ceo_min_years']} of them (a year counts when the CEO held the job for 6 of its 12 months), else the full B1 window. (Goodwill and intangible impairments + losses on businesses sold or held for sale, less any filed release of past currency-translation losses) ÷ average goodwill + intangibles over the window: 0 → 5, <5% → 4, <15% → 3, <30% → 2, else 1. Diluted shares from the year before the window (FY(L−10) for the full window, or the first perimeter year): down ≥15% → 5, down 5–15% → 4, ±5% → 3, up 5–20% → 2, up >20% → 1. Average, rounded down; needs both."))
    # ---- financial-risk gate (a flag on the page)
    lv = m['lev']; levtxt = '–' if lv is None else ('EBITDA ≤ 0 with net debt' if lv == float('inf') else ('net cash' if lv < 0 else f"{lv:.1f}×"))
    covtxt = '–' if m['cov'] is None else f"{m['cov']:.1f}×"
    out.append(dict(code='R1', name='Financial risk gate', factor='Risk', kind='Data', score=None, inputs=[
        [f"Net debt FY{m['L']} (debt + leases − cash), m", m0(m['levND'])], [f"EBITDA FY{m['L']} (operating income + D&A), m", m0(m['levEBITDA'])],
        ['Net debt ÷ EBITDA', levtxt], ['Operating income ÷ gross interest expense', covtxt]],
        calc=('Gate triggered' if m['risk'] else 'Gate not triggered') + (' (interest expense not in the data)' if m['cov'] is None else ''), note=MN.get('R1', ''),
        rule=f"Triggered if net debt ÷ EBITDA is above {RULES['lev_max']:g}× (or EBITDA ≤ 0 with net debt), or operating income ÷ gross interest is below {RULES['cov_min']:g}×. Latest fiscal year."))
    # ---- Industry: peer measures from the tagged coverage universe
    ind, ims = industry(t, m['L'])
    out[-1:-1] = ims                                    # Industry rows sit before the risk gate
    for x in out: x['light'] = light(x['score']) if x['factor'] != 'Risk' else ('r' if m['risk'] else 'g')
    # ---- three factors, never combined; a missing measure becomes a range (1 to 5), never an average of what is left
    for x in out:
        if x['score'] is None and (c.get('measure_gaps') or {}).get(x['code']): x['gap'] = c['measure_gaps'][x['code']]
    bus = factor([x for x in out if x['factor'] == 'Business'], 'Business')
    if m['short'] and bus['point'] is not None: bus['calc'] += f"; short history ({m['n']} clean years): shown for information"
    indf = factor(ims, 'Industry') if ims else dict(lo=None, hi=None, point=None, light='na', calc='Not scored: company not in the coverage universe')
    if ind: indf.update(count=ind['count'], nVal=ind['nVal'], thin=ind['thin'])   # v4.7: the company count sits next to the Industry light
    # v4.7.1 (user, 2026-10-23): an Industry measure near its cut-off is marked; when one score step on that measure would change the light, a flag says so
    nearm = []
    for x in ims or []:
        if x.get('near') and isinstance(x.get('score'), (int, float)):
            x['calc'] += ' (near the cut-off)'
            x['note'] = x['near'][0].upper() + x['near'][1:] + '.' + (' ' + x['note'] if x.get('note') else '')
            vals = [y['score'] for y in ims if isinstance(y.get('score'), (int, float))]
            if len(vals) == len(ims):
                S = sum(vals); flips = {flight(r1((S + d) / len(ims))) for d in (-1, 1) if 1 <= x['score'] + d <= 5} - {indf.get('light')}
                if flips: nearm.append(f"{x['code']} ({x['near'].split(': ', 1)[1].split(',')[0]})")
    indf['near'] = nearm
    mgt = factor([x for x in out if x['factor'] == 'Management'], 'Management')
    # ---- red flags
    rf = red_flags(t, Fc); rem = list(dict.fromkeys(lab for lab, _ in rf))
    # ---- placement on the quadrant
    QL, QB = RULES['quality_line'], RULES['quality_band_low']
    if bus['point'] is None: qz = 'Business not scored'
    elif bus['lo'] < QL <= bus['hi'] and bus['lo'] != bus['hi']: qz = f"Business range crosses {QL:g}"
    elif bus['point'] >= QL: qz = f"Business ≥ {QL:g}"
    elif bus['point'] >= QB: qz = f"Business {QB:g}–{QL:g}"
    else: qz = f"Business < {QB:g}"
    if pe['band'] is None: pz = 'P/E not meaningful'
    else:
        a, b2, c3 = RULES['pe_lines']; pc = pe['pct']
        pz = f"P/E ≤ {ordn(a)} pct" if pc <= a else f"P/E {ordn(a)}–{ordn(b2)} pct" if pc <= b2 else f"P/E {ordn(b2)}–{ordn(c3)} pct" if pc <= c3 else f"P/E > {ordn(c3)} pct"
    steps = [['Accounting red flags', 'Found: ' + '; '.join(rem) if rem else 'None found'],
             ['Business', bus['calc']],
             ['Industry', indf['calc'] + (f" · peers: {ind['label']}" if ind else '')],
             ['Management', mgt['calc']],
             ['Multiples in their own history', (f"median {ordn(mx['pct'])} percentile of " + ', '.join(f"{d['name']} {d['now']}× ({ordn(d['pct'])})" for d in mx['metrics'].values() if d['pct'] is not None)
                                                  + f"; window from {mx['window']} ({mx['windowWhy']})") if mx['band'] else f"Not meaningful: {mx['why']}"],
             ['Financial risk gate', ('Triggered' if m['risk'] else 'Not triggered') + f": net debt ÷ EBITDA {levtxt}, interest cover {covtxt}"]]
    # ---- flags
    if m['short']: flags_out.append(f"Short history: {m['n']} clean years")
    flags_out += [r for r in m['repairs'] if r.startswith('Settlement debt: current part')]
    if m['risk']: flags_out.append(f"Financial risk: net debt ÷ EBITDA {levtxt}, interest cover {covtxt}")
    if pe.get('override'): flags_out.append('P/E rebuilt: ' + pe['override'])
    elif pe.get('stale'): flags_out.append(f"P/E series stale: the daily P/E ends {pe['stale']}")
    for nt in mx['notes']:
        if not nt.startswith('P/E'): flags_out.append('EV multiple rebuilt: ' + nt)
    if pe['distorted']: flags_out.append(f"P/E distorted: trailing {pe['now']}× ÷ forward {pe['fwd']:.1f}× = {pe['ratio']:.1f} (above {RULES['pe_distorted']})")
    per = Fc.get('perimeter') or {}
    for d in per.get('after_year_end') or []:
        eff = num(d.get('revenue_effect_pct')) if isinstance(d, dict) else None
        if eff is not None and eff > RULES['deal_after_ye'] * 100:
            stt = str(d.get('status', '')).split(' - ')[0].split(';')[0][:30]
            flags_out.append(f"Business changing: {d.get('name', 'deal')} ({stt + ', ' if stt else ''}about {eff:.0f}% of revenue) after the latest year-end")
    unexpl = [f for f in m['flags'] if f['fy'] >= m['start'] and not f.get('cause')]
    if unexpl: flags_out.append('Perimeter flag not explained: ' + '; '.join(f"FY{f['fy']} {f['text']}" for f in unexpl))
    ok = {int(k): v for k, v in (c.get('deal_flags_ok') or {}).items()}
    for f in m['flags']:
        if f['fy'] >= m['start'] and str(f.get('cause') or '').lower().startswith('deal'):
            if f['fy'] in ok: f['why'] = (f.get('why') or '') + f" [Kept in the window: {ok[f['fy']]}]"
            elif f['fy'] in (m.get('gwOnly') or []):
                f['why'] = (f.get('why') or '') + ' [Goodwill test only: window kept; B1 and B4 also measured on the years after the deal (v4.4)]'
            else: flags_out.append(f"Deal inside the scoring window: FY{f['fy']} — check the perimeter start")
    if m.get('gwOnly'):
        gy_ = m['gwOnly'][-1]
        flags_out.append(f"Deal in FY{gy_} (goodwill test only): window kept; " + (f"B1/B4 also on {fyspan(m['postYrs'])}, lower score used" if m.get('postYrs') else 'no full year after it yet'))
    if c.get('held_for_sale'):
        h = c['held_for_sale']; flags_out.append(f"Held-for-sale assets in capital {h.get('years', '') if isinstance(h, dict) else h}: returns understated")
    if c.get('b3_mix'): flags_out.append(f"B3 mixes: {c['b3_mix']}")
    for x in (Fc.get('red_flags') or {}).get('aaer_recent') or []:   # user, 2026-10-23: an AAER whose misconduct ended before the horizon is not a red flag, but stays highlighted
        if isinstance(x, dict) and not any(lab == 'SEC AAER' for lab, _ in rf):
            cs, ce = str(x.get('conduct_start') or '')[:4], str(x.get('conduct_end') or '')[:4]
            flags_out.append(f"Past SEC enforcement: {x.get('number', 'AAER')} ({x.get('date', '')}), misconduct {cs + '–' if cs and cs != ce else ''}{ce}; outside the {RULES['redflag_aaer_years']}-year horizon, not a red flag")
    if indf.get('near'): flags_out.append('Industry light near a cut-off: ' + '; '.join(indf['near']) + ' — one step on that measure would change the light')
    flags_out += c.get('extra_flags') or []
    # ---- leading indicator (display only, v4.3; user 2026-10-22): the latest year against the window median for B1 and B4.
    #      The lights use 10-year windows and 3-year medians, so a real turn shows late; this line shows it first. No score uses it.
    fye = Fc.get('fiscal_year_end_latest') or (((Fc.get('red_flags') or {}).get('icfr') or {}).get('fiscal_year_end')) or None
    lead = dict(fy=m['L'], fyEnd=fye, b1Latest=None, b1Med=m.get('b1Med'), b4Latest=None, b4Med=m.get('b4Med'))
    if m['yrs'] and m['yrs'][-1] == m['L']: lead.update(b1Latest=m['roicEx'][-1], b4Latest=m['roicIn'][-1])
    for x in out:
        if x['code'] in ('B1', 'B4'):
            a_, md_ = (lead['b1Latest'], lead['b1Med']) if x['code'] == 'B1' else (lead['b4Latest'], lead['b4Med'])
            if a_ is not None and md_ is not None:
                x['note'] = (x['note'] + ' ' if x['note'] else '') + (f"Latest year FY{m['L']}: {pct(a_)} against the window median {pct(md_)} "
                            f"({'above' if a_ > md_ + .005 else 'below' if a_ < md_ - .005 else 'in line'}; shown only, the score uses the median).")
    res = result(c, out, bus, mgt, mx, rem, m['short'], flags_out, Fc, n_clean=m['n'], L_fy=m['L'], b4=m.get('b4Med'), i1=(ind or {}).get('i1_same'))
    steps.insert(0, ['Result', res['cat'] + ' — ' + '; '.join(res['lines']) + '. Detail: ' + '; '.join(res['why']) + ('. Re-look signal: ' + '; '.join(res['relook']) if res['relook'] else '') + ('. Note: ' + '; '.join(res['caution']) if res['caution'] else '')])
    sc = {x['code']: x['score'] for x in out}
    return dict(ticker=t, name=c.get('name', t), group=c.get('group', ''), cur=cur, measures=out, business=bus, industry=indf, management=mgt, ceo=ceo_trace(Fc, m), peers=ind, result=res, zone=dict(quality=qz, price=pz),
                growth=m['b3'], scores=sc, steps=steps, pe=pe, mult=mx, removed=rem, risk=m['risk'], short=m['short'], flags=flags_out,
                redflags=[dict(label=a, detail=short_desc(b)) for a, b in rf], redflag_check=Fc.get('red_flags') or {}, sec=Fc.get('sec_registrant', True),
                info=Fc.get('info') or {}, perimeter=per, autoflags=m['flags'],
                window=dict(start=m['start'], first=m['yrs'][0] if m['yrs'] else None, L=m['L'], n=m['n'], perim=m['perim'], short=m['short'], growth=[gy[0], gy[-1]] if gy else None),
                repairs=m['repairs'], perimeter_note=c.get('perimeter_note', ''), notes=Fc.get('notes', ''), lead=lead)

def build_all():
    M = {t: measures(t) for t in KEY if KEY[t] in RAW}
    RANK = {}
    for code, fld in (('B1', 'b1Med'), ('B4', 'b4Med')):
        vals = sorted([(M[t][fld], t) for t in M if M[t][fld] is not None and not M[t]['short']], reverse=True)
        RANK[code] = {t: i for i, (_, t) in enumerate(vals, 1)}
    res = {t: build(t, RANK) for t in M}
    json.dump(res, open(P('page_data.json'), 'w'), default=str)
    json.dump(dict(engine=ENGINE_VERSION, rules_version=RULES_VERSION, built=datetime.datetime.now().isoformat(timespec='seconds'), as_of=AS_OF,
                   companies=len(res)), open(P('run_meta.json'), 'w'), indent=1)   # v4.7.2: the label the page and the records print
    if UNI:   # coverage-universe summary for the page: every company, its tag, the reason, and the tag medians
        U = UNI['companies']; tags = []
        for tg, T in UNI['tags'].items():
            mem = [k for k, v in U.items() if v['tag'] == tg]; pm = [peer_measures(k) for k in mem]
            rv = [x['roicMed'] for x in pm if x.get('roicMed') is not None]; gv = [x['revG'] for x in pm if x.get('revG') is not None]
            tags.append(dict(tag=tg, label=T['label'], parent=UNI['parents'][T['parent']], definition=T['def'], n=len(mem), nRoic=len(rv),
                             roic=None if not rv else ('inf' if st.median(rv) == float('inf') else round(st.median(rv), 4)), revG=round(st.median(gv), 4) if gv else None))
        comp = [dict(key=k, t=v['t'], name=v['name'], tag=UNI['tags'][v['tag']]['label'], tagCode=v['tag'], why=v['why'], gics=v.get('gics', ''), window=v.get('window_why', ''), run=k in KEY.values(),
                     data=peer_measures(k).get('roicMed') is not None) for k, v in U.items()]
        for x in tags: x['parentCode'] = UNI['tags'][x['tag']]['parent']
        json.dump(dict(name=UNI.get('name'), status=UNI.get('status'), min_peers=RULES['peer_min'], tag_min=RULES['peer_tag_min'], thin=RULES['thin_group'], tags=tags, companies=comp, excluded=UNI.get('excluded') or {}), open(P('universe_page.json'), 'w'))
    for t in sorted(res, key=lambda t: (bool(res[t]['removed']), -(res[t]['business']['point'] or 0))):
        v = res[t]; p = v['pe']; b = v['business']; ms = v['scores']
        I, Mg = v['industry'], v['management']
        print(f"{t:5} B {fmt(b['point']):4} {b['light']:5} ({' '.join(fmt(ms[c]) for c in ('B1', 'B2', 'B3', 'B4'))}) I {fmt(I['point']):4} {I['light']:5} ({' '.join(fmt(ms.get(c)) for c in ('I1', 'I2', 'I3'))}) M {fmt(Mg['point']):4} {Mg['light']:5} ({' '.join(fmt(ms[c]) for c in ('M1', 'M2', 'M3'))}) | PE {fmt(p['now']):6} pct {fmt(p.get('pct')):4} | {v['zone']['quality']} · {v['zone']['price']} | {'REMOVED ' + '; '.join(v['removed']) if v['removed'] else ''} | {' | '.join(v['flags'])}")

if __name__ == '__main__':
    cmd = sys.argv[2] if len(sys.argv) > 2 else 'score'
    {'score': score, 'build': build_all}[cmd]()
