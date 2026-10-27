#!/usr/bin/env python3
"""Evidence-linked valuation inputs and delivery checks; no network calls or scoring-rule changes.

See references/valuation-reliability.md. Commands: build, promote, annotate, check.
Build stages candidates; promotion preserves existing inputs in an immutable revision backup.
"""
import argparse
import ast
import copy
import csv
import datetime as dt
import hashlib
from html.parser import HTMLParser
import json
import math
import os
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo

SCHEMA = 1
NAMES = {'pe': 'P/E', 'ebit': 'EV/EBIT', 'ebitda': 'EV/EBITDA'}
LABELS = {'eligible': '历史分位可用', 'nonpositive_denominator': '利润分母非正',
          'short_history': '比较历史不足', 'positive_days_short': '正值天数不足',
          'history_gap': '历史资料不足', 'positive_coverage_low': '正值覆盖不足',
          'current_gap': '当前输入缺项'}
ATTEMPTS = {'returned', 'reused', 'empty', 'missing_field', 'rate_limited',
            'permission_denied', 'unsupported_market', 'truncated', 'unavailable'}


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def write(p, value):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    os.replace(tmp, p)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def day(s):
    return dt.date.fromisoformat(s)


def trading_date(timestamp, exchange_timezone):
    """FX quotes near UTC midnight belong to the exchange's local calendar date."""
    return dt.datetime.fromtimestamp(timestamp, dt.timezone.utc).astimezone(ZoneInfo(exchange_timezone)).date().isoformat()


def finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def evidence(e, run):
    if not e.get('source') or not e.get('raw_path'):
        raise ValueError('source and saved raw_path are required')
    p = Path(e['raw_path'])
    if not any(q.is_file() for q in [p, run / p]):
        raise ValueError('raw evidence does not exist: ' + str(p))


def rules(run):
    for node in ast.parse((run / 'screener.py').read_text()).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'RULES' for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError('copied numerical engine has no literal RULES')


def clean_start(config, company, threshold):
    if company.get('pe_from'):
        start = day(company['pe_from'])
        months = threshold['deal_delay_months']
        y, m = divmod(start.year * 12 + start.month - 1 + months, 12)
        return dt.date(y, m + 1, start.day).isoformat()
    # The imported numerical engine ignores the legacy display-only pe_default_from setting.
    d = day(config['as_of'])
    return d.replace(year=d.year - 10).isoformat()


def ttm_bridge(fy, prior_ytd, current_ytd):
    """FY − prior YTD + current YTD; use matching definitions and actual publication dates."""
    es = [fy, prior_ytd, current_ytd]
    for k in ['currency', 'unit', 'basis', 'definition']:
        if len({e[k] for e in es}) != 1:
            raise ValueError('TTM bridge has incompatible ' + k)
    if fy['period_start'] != prior_ytd['period_start'] or not (
        prior_ytd['period_end'] < fy['period_end'] < current_ytd['period_start'] <= current_ytd['period_end']
    ):
        raise ValueError('TTM bridge periods do not form FY minus prior YTD plus current YTD')
    lengths = [(day(e['period_end']) - day(e['period_start'])).days for e in es]
    if not 350 <= lengths[0] <= 380 or abs(lengths[1] - lengths[2]) > 8:
        raise ValueError('TTM bridge durations are not comparable')
    out = {k: fy[k] for k in ['currency', 'unit', 'basis', 'definition']}
    out.update(value=fy['value'] - prior_ytd['value'] + current_ytd['value'], kind='ttm',
               period_start=(day(prior_ytd['period_end']) + dt.timedelta(days=1)).isoformat(),
               period_end=current_ytd['period_end'], available=max(e['available'] for e in es),
               published=max(e['published'] for e in es), source='Analysis: FY − prior YTD + current YTD',
               raw_path=current_ytd['raw_path'], inputs=copy.deepcopy(es))
    return out


def latest(events, date, max_age):
    known = [e for e in events if e['available'] <= date and e['period_end'] <= date]
    if not known:
        return None
    e = max(known, key=lambda v: (v['period_end'], v['available']))
    # Do not fall back to an older, conveniently complete report after a newer null observation.
    if e.get('approximate') or e['value'] is None or (day(date) - day(e['period_end'])).days > max_age:
        return None
    return e


def pack(rows):
    return {'d': ','.join(d[2:].replace('-', '') for d, v in rows),
            'r': ','.join('' if v is None else str(v) for d, v in rows)}


def classify(rows, denominator, missing, threshold):
    vals = [v for _, v in rows if v is not None]
    pos = sum(v > 0 for v in vals)
    n = len(rows)
    stats = dict(trading_days=n, observed_days=len(vals), positive_days=pos,
                 nonpositive_days=len(vals) - pos, missing_days=n - len(vals),
                 positive_share=100 * pos / n if n else 0)
    if denominator is not None and denominator <= 0:
        state = 'nonpositive_denominator'
    elif not rows or rows[-1][1] is None:
        state = 'current_gap'
    elif pos >= threshold['pe_min_pos_days'] and round(stats['positive_share']) >= threshold['pe_min_pos_share']:
        state = 'eligible'
    elif n < threshold['pe_min_pos_days']:
        state = 'short_history'
    elif stats['missing_days'] > stats['nonpositive_days']:
        state = 'history_gap'
    elif pos < threshold['pe_min_pos_days']:
        state = 'positive_days_short'
    else:
        state = 'positive_coverage_low'
    why = LABELS[state]
    if state == 'current_gap':
        why += '：' + ', '.join(missing)
    elif state != 'eligible':
        why += f'；正值{pos}日 / 比较窗{n}日，缺失{stats["missing_days"]}日'
    return dict(state=state, reason=why, **stats)


def validate_company(c, run, price_date):
    for k in ['key', 'listing', 'listing_currency', 'reporting_currency', 'quote_unit_id', 'accounting_standard']:
        if not c.get(k):
            raise ValueError('missing company identity: ' + k)
    if c['listing_currency'] == 'GBp':
        raise ValueError('normalize pence to GBP before valuation')
    if c.get('economic_history_from'):
        evidence(c['history_start_evidence'], run)
    if c.get('approximate_current'):
        approximate=c['approximate_current']
        evidence(approximate,run)
        if not approximate.get('reason') or not approximate.get('values'):
            raise ValueError('approximate current multiples require values and a reason')
        if any(k not in NAMES or not finite(v) for k,v in approximate['values'].items()):
            raise ValueError('invalid approximate current multiple')
    for field, events in c['metrics'].items():
        seen = set()
        for e in events:
            evidence(e, run)
            for k in ['published', 'available', 'period_end', 'unit', 'currency', 'basis']:
                if not e.get(k):
                    raise ValueError(field + ': missing ' + k)
            if day(e['available']) < day(e['published']) + dt.timedelta(days=1):
                raise ValueError(field + ': availability must be after public disclosure')
            if e['period_end'] > e['published']:
                raise ValueError(field + ': financial period ends after publication')
            if e['value'] is not None and not finite(e['value']):
                raise ValueError(field + ': non-finite value')
            if e['value'] is None and not e.get('reason'):
                raise ValueError(field + ': null requires a reason')
            for child in e.get('inputs',[]):
                if child.get('available') and child['available']>e['available']:
                    raise ValueError(field + ': derived value used an input before it was public')
            if (e['period_end'], e['available']) in seen:
                raise ValueError(field + ': unresolved duplicate event')
            seen.add((e['period_end'], e['available']))
            if field == 'shares':
                if e['unit'] != 'quote_units' or e['basis'] != c['quote_unit_id']:
                    raise ValueError('shares must be actual outstanding quote units on the price split/ADS basis')
            elif field == 'eps':
                if e['unit'] != e['currency'] + '/quote_unit' or e['basis'] != c['quote_unit_id'] or e.get('kind') != 'ttm':
                    raise ValueError('EPS must be TTM diluted EPS per matching quoted unit')
            elif e['unit'] != e['currency']:
                raise ValueError(field + ': amounts must be full reporting currency, not millions')
            if field != 'shares' and e['currency'] != c['reporting_currency']:
                raise ValueError(field + ': currency not normalized to reporting currency')
            if field in ['op', 'da'] and (e.get('kind') != 'ttm' or not e.get('period_start')):
                raise ValueError(field + ': require unadjusted TTM and its period start')
            definitions={'eps':'diluted_reported_eps','op':'reported_operating_profit','da':'pure_depreciation_amortization'}
            if field in definitions and e.get('definition')!=definitions[field]:
                raise ValueError(field + ': wrong or unverified reported-profit definition')
    for name in ['prices', 'fx', 'market_caps']:
        dates = []
        for q in c.get(name, []):
            evidence(q, run)
            day(q['date'])
            dates.append(q['date'])
            if q['value'] is not None and (not finite(q['value']) or q['value'] <= 0):
                raise ValueError(name + ': prices, FX and market caps must be positive')
            if name in ['prices', 'market_caps'] and (q['currency'] != c['listing_currency'] or q['basis'] != c['quote_unit_id']):
                raise ValueError(name + ': listing currency or split/ADS basis mismatch')
            if name == 'fx' and (q['from'], q['to']) != (c['reporting_currency'], c['listing_currency']):
                raise ValueError('FX must explicitly convert reporting currency to listing currency')
        if dates != sorted(set(dates)):
            raise ValueError(name + ': dates must be unique and sorted')
    if not any(q['date'] <= price_date for q in c['prices']):
        raise ValueError('no price observation on/before cutoff')
    claims = c.get('ev_claims', {})
    if claims.get('debt') != 1 or claims.get('cash') != -1 or any(v not in [-1, 1] for v in claims.values()):
        raise ValueError('ev_claims must include debt:+1, cash:-1 and explicit signs for other applicable claims')
    evidence(c['claims_review'], run)


def build_company(c, config, run, price_date, threshold):
    validate_company(c, run, price_date)
    age = {'quarterly': 190, 'semiannual': 290, 'annual': 410}[c.get('reporting_frequency', 'quarterly')]
    get = lambda k, d: latest(c['metrics'].get(k, []), d, c.get('max_age_days', {}).get(k, age))
    prices = [q for q in c['prices'] if c.get('economic_history_from', '0000-00-00') <= q['date'] <= price_date]
    if not prices:
        raise ValueError('no operating-company prices after economic history start')
    if (day(price_date)-day(prices[-1]['date'])).days>threshold['pe_stale_days']:
        raise ValueError('price is stale; obtain a current quote instead of reusing old multiples')
    pe, ebit, ebitda, tev, px = [], [], [], [], []
    trace = {}
    for quote in prices:
        d, price = quote['date'], quote['value']
        eps, op, da, shares = [get(k, d) for k in ['eps', 'op', 'da', 'shares']]
        fxrows = [q for q in c.get('fx', []) if q['date'] <= d]
        fxe = fxrows[-1] if fxrows else None
        xr = 1 if c['reporting_currency'] == c['listing_currency'] else (
            fxe['value'] if fxe and (day(d) - day(fxe['date'])).days <= c.get('fx_max_gap_days', 7) else None)
        missing = []
        mc = price * shares['value'] if price is not None and shares else None
        market = next((q for q in c.get('market_caps', []) if q['date'] == d), None)
        if market and market['value'] is not None:
            # Provider market caps can price only one Up-C class. Require a documented reconciliation.
            if mc and abs(market['value'] / mc - 1) > c.get('market_cap_tolerance', .02) and not c.get('market_cap_reconciliation'):
                raise ValueError('market cap disagrees with actual shares × price; reconcile classes/splits first')
            if c.get('market_cap_reconciliation'):
                evidence(c['market_cap_reconciliation'], run)
            mc = market['value']
        claims = {k: get(k, d) for k in c['ev_claims']}
        missing += [k for k, v in claims.items() if v is None]
        if not c['claims_review'].get('complete'):
            missing.append('EV claims review incomplete')
        if mc is None: missing.append('market_cap / actual shares')
        if xr is None: missing.append('FX')
        if price is None: missing.append('price')
        ev = mc + sum(v['value'] * c['ev_claims'][k] for k, v in claims.items()) * xr if not missing else None
        ep = eps['value'] * xr if eps and xr is not None else None
        operating = op['value'] * xr if op and xr is not None else None
        da_ok = op and da and all(op[k] == da[k] for k in ['period_start', 'period_end', 'basis'])
        earnings = (op['value'] + da['value']) * xr if da_ok and xr is not None else None
        ratios = [price / ep if price is not None and ep else None,
                  ev / operating if ev is not None and operating else None,
                  ev / earnings if ev is not None and earnings else None]
        ratios = [round(v, 6) if v is not None else None for v in ratios]
        for arr, v in zip([pe, ebit, ebitda], ratios): arr.append((d, v))
        tev.append((d, round(ev / 1e6, 6) if ev is not None else None)); px.append((d, price))
        trace = dict(date=d, price=price, quote=quote, FX=xr, FX_source=fxe, market_cap=mc,
                     market_cap_source=market, shares=shares, eps=eps, op=op, da=da, claims=claims,
                     EV=ev, PE=ratios[0], EV_EBIT=ratios[1], EV_EBITDA=ratios[2],
                     denominators={'pe': ep, 'ebit': operating, 'ebitda': earnings},
                     missing={'pe': ([] if ep is not None else ['TTM EPS / FX']) + ([] if price is not None else ['price']),
                              'ebit': missing + ([] if op else ['TTM operating profit']),
                              'ebitda': missing + ([] if da_ok else ['matching pure TTM D&A'])})
    window = clean_start(config, config['companies'][c['ticker']], threshold)
    stats = {k: classify([(d, v) for d, v in arr if d >= window], trace['denominators'][k], trace['missing'][k], threshold)
             for k, arr in [('pe', pe), ('ebit', ebit), ('ebitda', ebitda)]}
    audit = dict(key=c['key'], listing=c['listing'], quote_currency=c['listing_currency'], price_date=trace['date'],
                 economic_history_from=c.get('economic_history_from'), window=window, current=trace, metrics=stats,
                 approximate_current=c.get('approximate_current'), source_attempts=c.get('source_attempts', []),
                 limitations=c.get('limitations', []))
    # Keep missing current observations in the final row; never relabel a stale historical value as today's ratio.
    return ({**pack(pe), 'price':trace['price'], 'mcap':trace['market_cap'], 'ttm':pe[-1][1], 'fwd':None, 'cur':c['listing_currency']},
            {'ebit':pack(ebit), 'ebitda':pack(ebitda), 'tev':pack(tev), 'px':pack(px),
             'pxCur':c['listing_currency'], 'pxListing':c['listing']}, audit)


def build(run, input_file, tickers=None):
    config, spec = read(run/'config.json'), read(input_file)
    if spec.get('schema_version') != SCHEMA:
        raise ValueError('unsupported valuation input schema')
    if day(spec['price_date']) > day(spec['disclosure_cutoff']) or spec['disclosure_cutoff'] != config['as_of']:
        raise ValueError('price/disclosure cutoff mismatch with run config')
    threshold = rules(run)
    selected = tickers or list(config['companies'])
    if not selected or len(selected) != len(set(selected)):
        raise ValueError('target scope empty or duplicated')
    seed = {name: read(run/'raw'/f'{name}.json') if (run/'raw'/f'{name}.json').exists() else {} for name in ['pe','ev']}
    data = copy.deepcopy(seed); audits = {}; errors = [];preserved_hashes={};evidence_hashes={}
    prior_path=run/'valuation_audit.json'
    if set(selected)!=set(config['companies']) and prior_path.exists():
        prior=read(prior_path)
        if prior.get('schema_version')==SCHEMA:
            if (prior['price_date'],prior['disclosure_cutoff'])!=(spec['price_date'],spec['disclosure_cutoff']):
                raise ValueError('partial repair must preserve the prior price/disclosure cutoff')
            for name,h in prior['input_hashes'].items():
                if sha(run/name)!=h:
                    raise ValueError('preserved input changed; use a new revision input filename for partial repairs: '+name)
            audits=copy.deepcopy(prior['companies']);preserved_hashes=copy.deepcopy(prior['input_hashes'])
            evidence_hashes=copy.deepcopy(prior.get('evidence_hashes',{}))
    for t in selected:
        if t not in config['companies'] or t not in spec['companies']:
            raise ValueError('target missing from config or inputs: ' + t)
        c = copy.deepcopy(spec['companies'][t]);c['ticker'] = t
        if c['key'] != config['companies'][t]['key']:
            raise ValueError(t + ': engine key mismatch')
        pe, ev, audit = build_company(c, config, run, spec['price_date'], threshold)
        data['pe'][c['key']] = pe;data['ev'][c['key']] = ev;audits[t] = audit
    for t,c in config['companies'].items():
        if t not in selected and any(c['key'] not in data[n] for n in ['pe','ev']):
            errors.append(t + ': targeted rebuild has no preserved baseline series')
    if errors: raise ValueError('; '.join(errors))
    input_hashes = {**preserved_hashes,str(input_file.resolve().relative_to(run)):sha(input_file), 'config.json':sha(run/'config.json')}
    a = dict(schema_version=SCHEMA, price_date=spec['price_date'], disclosure_cutoff=spec['disclosure_cutoff'],
             scope=selected, companies=audits, input_hashes=input_hashes)
    def bind_evidence(value):
        if isinstance(value,dict):
            if value.get('raw_path'):
                p=Path(value['raw_path']);p=p if p.is_file() else run/p
                if not p.is_file():raise ValueError('referenced raw evidence is missing: '+str(p))
                relative_path=os.path.relpath(p.resolve(),run)
                if relative_path not in evidence_hashes:evidence_hashes[relative_path]=sha(p)
            for child in value.values():bind_evidence(child)
        elif isinstance(value,list):
            for child in value:bind_evidence(child)
    for t in selected:bind_evidence(spec['companies'][t])
    a['evidence_hashes']=evidence_hashes
    stage = run/'valuation_stage'
    for n in ['pe','ev']: write(stage/'raw'/f'{n}.json', data[n])
    a['generated_input_hashes']={f'raw/{n}.json':sha(stage/'raw'/f'{n}.json') for n in ['pe','ev']}
    write(stage/'valuation_audit.json', a)
    write(stage/'stage_manifest.json', {'source_hashes':input_hashes,'baseline_hashes':{
        n: sha(run/'raw'/f'{n}.json') if (run/'raw'/f'{n}.json').exists() else None for n in ['pe','ev']},
        'candidate_hashes':{n:sha(stage/'raw'/f'{n}.json') for n in ['pe','ev']},'audit_hash':sha(stage/'valuation_audit.json')})
    return a


def promote(run):
    import shutil
    stage = run/'valuation_stage';m=read(stage/'stage_manifest.json')
    for p,h in m['source_hashes'].items():
        if sha(run/p) != h: raise ValueError('source changed since staging: ' + p)
    for n in ['pe','ev']:
        p=run/'raw'/f'{n}.json';now=sha(p) if p.exists() else None
        if now != m['baseline_hashes'][n]: raise ValueError('baseline changed since staging: ' + n)
        if sha(stage/'raw'/f'{n}.json') != m['candidate_hashes'][n]: raise ValueError('candidate changed: ' + n)
    if sha(stage/'valuation_audit.json') != m['audit_hash']: raise ValueError('staged audit changed')
    for p,h in read(stage/'valuation_audit.json').get('evidence_hashes',{}).items():
        if not (run/p).is_file() or sha(run/p)!=h:raise ValueError('raw evidence changed since staging: '+p)
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    backup=run/'valuation_revisions'/stamp;backup.mkdir(parents=True,exist_ok=False)
    for f in ['raw/pe.json','raw/ev.json','valuation_audit.json','page_data.json','page_text.json','snapshot.json','reopen.json','source_ledger.json','config.json','run_meta.json','valuation_coverage.csv','final_manifest.json',read(run/'config.json').get('output','screener_scores.html')]:
        p=run/f
        if p.exists():
            q=backup/f;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    for n in ['pe','ev']: write(run/'raw'/f'{n}.json',read(stage/'raw'/f'{n}.json'))
    write(run/'valuation_audit.json',read(stage/'valuation_audit.json'))
    write(backup/'promotion.json',m)
    return backup


def annotate(run):
    data,audit=read(run/'page_data.json'),read(run/'valuation_audit.json')
    if audit.get('schema_version') != SCHEMA: raise ValueError('rebuild the valuation audit using this pipeline')
    for p,h in audit.get('generated_input_hashes',{}).items():
        if sha(run/p)!=h:raise ValueError('promoted valuation inputs changed; rebuild first: '+p)
    for t,a in audit['companies'].items():
        c=data[t];c['valuation_quality']=copy.deepcopy(a)
        c['pe']['price_date']=a['price_date']
        for k,q in a['metrics'].items():
            m=c['mult']['metrics'][k]
            if (m['pct'] is not None) != (q['state']=='eligible'):
                raise ValueError(t+' '+k+': audit and engine disagree about history eligibility')
            if q['state']!='eligible':m['why']=q['reason']
        c['pe']['why']=a['metrics']['pe']['reason'] if a['metrics']['pe']['state']!='eligible' else ''
        if not c['mult']['band']:
            c['mult']['why']='；'.join(q['reason'] for q in a['metrics'].values())
            if c['result']['cat']=='Research at lower price':
                c['result']['lines'][0]='估值分位不可用；不能据此判断价格偏贵（保留原引擎行动标签）'
        for row in c['mult'].get('trends',[])+([c['mult']['one']] if c['mult'].get('one') else []):
            if row.get('na')=='EBITDA negative today' and a['metrics']['ebitda']['state']!='nonpositive_denominator':
                row.update(na=a['metrics']['ebitda']['reason'],short='当前同口径倍数缺项')
        for step in c['steps']:
            if step[0]=='Result':step[1]=c['result']['cat']+' — '+'; '.join(c['result']['lines'])
            if step[0]=='Multiples in their own history':
                step[1]='；'.join(NAMES[k]+': '+(str(c['mult']['metrics'][k]['pct'])+'分位' if q['state']=='eligible' else q['reason']) for k,q in a['metrics'].items())
    write(run/'page_data.json',data)
    with (run/'valuation_coverage.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['ticker','price_date','currency','multiple','current','state','reason','positive_days','nonpositive_days','missing_days','window_days','percentile','approximate_current'])
        for t,a in audit['companies'].items():
            for k,q in a['metrics'].items():
                m=data[t]['mult']['metrics'][k]
                w.writerow([t,a['price_date'],a['quote_currency'],NAMES[k],m['now'],q['state'],q['reason'],q['positive_days'],q['nonpositive_days'],q['missing_days'],q['trading_days'],m['pct'],json.dumps(a.get('approximate_current'),ensure_ascii=False)])
    ledger=read(run/'source_ledger.json') if (run/'source_ledger.json').exists() else {}
    ledger['valuation_pipeline']={'schema_version':SCHEMA,'audit':'valuation_audit.json','coverage':'valuation_coverage.csv',
                                  'price_date':audit['price_date'],'disclosure_cutoff':audit['disclosure_cutoff'],
                                  'scope':audit['scope'],'actual_sources':'Per-company current inputs and source_attempts in valuation_audit.json'}
    write(run/'source_ledger.json',ledger)
    bindings=[run/'page_data.json',run/'valuation_coverage.csv',run/'source_ledger.json',run/'run_meta.json']
    for base in ['raw','facts','facts_model','universe']:
        if (run/base).exists():bindings+=list((run/base).rglob('*.json'))
    write(run/'delivery_bindings.json',{str(p.relative_to(run)):sha(p) for p in bindings if p.is_file()})
    return audit


def refresh(run):
    """Recalculate only selected companies' valuations/actions using preserved quality measures."""
    import importlib.util
    audit=read(run/'valuation_audit.json');data=read(run/'page_data.json');before=copy.deepcopy(data)
    spec=importlib.util.spec_from_file_location('screen_engine_valuation_refresh',run/'screener.py')
    engine=importlib.util.module_from_spec(spec);argv=sys.argv[:]
    try:
        sys.argv=[str(run/'screener.py'),str(run)];spec.loader.exec_module(engine)
    finally:sys.argv=argv
    for t in audit['scope']:
        c=data[t];pe=engine.pe_band(t);mx=engine.mult_band(t,pe)
        result=engine.result(engine.CO[t],c['measures'],c['business'],c['management'],mx,c['removed'],c['short'],c['flags'],engine.facts(t),
                             b4=(c.get('lead') or {}).get('b4Med'),i1=(c.get('peers') or {}).get('i1_same'),
                             n_clean=c['window']['n'],L_fy=c['window']['L'])
        c['pe']=pe;c['mult']=mx
        if not c.get('data_incomplete'):c['result']=result
        c['zone']['price']='历史估值第'+str(mx['pct'])+'分位' if mx.get('band') else '历史估值分位不可用'
        for st in c['steps']:
            if st[0]=='Result':st[1]=c['result']['cat']+' — '+'; '.join(c['result']['lines'])
            if st[0]=='Multiples in their own history':st[1]=str(mx.get('pct')) if mx.get('band') else mx['why']
    for t,c in before.items():
        if t not in audit['scope'] and data[t]!=c:raise ValueError('non-target company changed: '+t)
        for k in ['measures','business','industry','management','scores','removed','redflags','risk','window']:
            if data[t][k]!=c[k]:raise ValueError('valuation refresh changed quality data: '+t+' '+k)
    write(run/'page_data.json',data)
    return annotate(run)


def check_run(run, html_file=None):
    errors=[];warnings=[];config=read(run/'config.json');data=read(run/'page_data.json');audit=read(run/'valuation_audit.json')
    if set(data)!=set(config['companies']):errors.append('company count/identity mismatch')
    if audit.get('schema_version')!=SCHEMA:return {'passed':False,'errors':['missing current valuation pipeline audit'],'warnings':[]}
    for p,h in audit['input_hashes'].items():
        if not (run/p).is_file() or sha(run/p)!=h:errors.append('valuation source/config changed after build: '+p)
    for group in ['evidence_hashes','generated_input_hashes']:
        for p,h in audit.get(group,{}).items():
            if not (run/p).is_file() or sha(run/p)!=h:errors.append(group+': changed/missing '+p)
    if not (run/'delivery_bindings.json').exists():errors.append('missing delivery bindings; run annotate after build')
    else:
        for p,h in read(run/'delivery_bindings.json').items():
            if not (run/p).is_file() or sha(run/p)!=h:errors.append('built report/source changed after annotate: '+p)
    for t,a in audit['companies'].items():
        if data[t].get('valuation_quality')!=a:errors.append(t+': annotations missing/stale; run annotate after build')
        attempts=a['source_attempts']
        for x in attempts:
            try:
                if x['status'] not in ATTEMPTS or not all(k in x for k in ['provider','tool','query','retrieved_at','scope']):
                    raise ValueError('incomplete attempt')
                evidence(x,run)
            except (KeyError,ValueError) as exc:errors.append(t+': invalid source attempt: '+str(exc))
        fa=[x for x in attempts if x.get('provider')=='FocusAlpha']
        if not fa:errors.append(t+': FocusAlpha was not checked or same-cutoff cache was not documented')
        scopes={k for x in fa for k in x.get('scope',[])}
        for k in ['prices','eps','op','da','shares','claims']:
            if not ({k,'all','valuation'} & scopes or (k!='prices' and 'financials' in scopes) or (k=='prices' and 'market_data' in scopes)):
                errors.append(t+': no FocusAlpha attempt documented for '+k)
        gaps=[k for k,q in a['metrics'].items() if q['state'] in ['current_gap','history_gap']]
        if gaps:
            fallback=[x for x in attempts if x.get('provider') in ['Gangtise','Original disclosure']]
            providers={x.get('provider') for x in fallback}
            if not {'Gangtise','Original disclosure'}<=providers:
                errors.append(t+': unresolved gaps require Gangtise capability/lookup and original-disclosure attempts')
            warnings.append(t+': '+', '.join(a['metrics'][k]['reason'] for k in gaps))
        if a.get('approximate_current'):
            try:
                evidence(a['approximate_current'],run)
                if not a['approximate_current'].get('reason'):raise ValueError('missing reason')
            except ValueError as exc:errors.append(t+': invalid approximate current multiple: '+str(exc))
        for k,q in a['metrics'].items():
            if (data[t]['mult']['metrics'][k]['pct'] is not None)!=(q['state']=='eligible'):
                errors.append(t+' '+k+': percentile inconsistent with source coverage')
    if config.get('valuation_pipeline_required') and set(audit['companies'])!=set(data):
        errors.append('new batch requires a valuation audit for every company; merge preserved baseline audit for partial repair')
    if html_file:
        text=Path(html_file).read_text(encoding='utf-8')
        class MetaReader(HTMLParser):
            def __init__(self):super().__init__();self.values={};self.language=None
            def handle_starttag(self,tag,attrs):
                if tag.lower()=='html':self.language=dict(attrs).get('lang')
                if tag.lower()=='meta':
                    a=dict(attrs)
                    if a.get('name'):self.values[a['name']]=a.get('content')
        meta=MetaReader();meta.feed(text)
        for name,p in [('screen-data-sha256',run/'page_data.json'),('screen-config-sha256',run/'config.json')]:
            if meta.values.get(name)!=sha(p):
                errors.append('HTML is stale or lacks '+name)
        if config.get('report_language')=='zh-CN' and meta.language not in ['zh-CN','zh-Hans']:
            errors.append('final HTML must be localized into Chinese before delivery; see chinese-report-style.md')
        if '历史估值分位' not in text:errors.append('HTML does not explain unavailable historical percentiles')
    return {'passed':not errors,'errors':errors,'warnings':warnings,'scope':audit.get('scope',[])}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['build','promote','refresh','annotate','check']);p.add_argument('run',type=Path);p.add_argument('--input',type=Path);p.add_argument('--tickers');p.add_argument('--html',type=Path);a=p.parse_args();run=a.run.resolve()
    try:
        if a.command=='build':
            if not a.input:p.error('build requires --input')
            out=build(run,a.input, a.tickers.split(',') if a.tickers else None);print('Staged valuations for',len(out['scope']),'companies; inspect valuation_stage/valuation_audit.json before promote')
        elif a.command=='promote':print('Promoted; preserved baseline at',promote(run))
        elif a.command=='refresh':print('Refreshed only the selected valuations/actions; preserved quality scores and other issuers:',refresh(run)['scope'])
        elif a.command=='annotate':print('Annotated',len(annotate(run)['companies']),'companies without changing numerical scores')
        else:
            result=check_run(run,a.html);write(run/'delivery_check.json',result);print(json.dumps(result,ensure_ascii=False));return 0 if result['passed'] else 1
    except (ValueError,KeyError,OSError) as exc:
        print('Valuation pipeline error:',exc,file=sys.stderr);return 1
    return 0


if __name__=='__main__':sys.exit(main())
