"""Rebuild a reviewed screen-v2 run from cached sources and curated judgments."""
import argparse
from collections import Counter
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import statistics
from datetime import date

try:
    from . import engine_v2 as engine
    from .prepare_v2 import prepare
except ImportError:
    import engine_v2 as engine
    from prepare_v2 import prepare


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def guidance_score(records):
    records = deepcopy(records)
    for r in records:
        r['target_midpoint'] = float((Decimal(str(r['target_low'])) + Decimal(str(r['target_high']))) / 2)
        r['hit'] = Decimal(str(r['actual'])) >= Decimal(str(r['target_midpoint']))
        if r['first_target_source']['published_on'] >= r['actual_source']['published_on']:
            raise ValueError('Guidance must precede actual results')
    n = len(records)
    if not n:
        return {'score': None, 'records': []}
    rate = sum(r['hit'] for r in records) / n
    score = engine.band(rate, [(.8, 5), (.6, 4), (.4, 3), (.2, 2)])
    score = min(score, 5 if n >= 5 else 4 if n >= 3 else 3)
    return {'score': score, 'count': n, 'hits': sum(r['hit'] for r in records), 'hit_rate': rate, 'records': records}


def cycle_score(members, annual):
    by_year = {}
    for t in members:
        rows = sorted(annual[t], key=lambda r: (r['year'], r['end']))
        # Last unique fiscal period; never compare a stub to a full year.
        years = {r['year']: r for r in rows}
        for y, b in years.items():
            a = years.get(y-1)
            if y < 2019 or not a or not a.get('revenue') or not b.get('revenue'):
                continue
            a, b = a['revenue'], b['revenue']
            if a['unit'] != b['unit'] or a['value'] <= 0:
                continue
            growth = b['value'] / a['value'] - 1
            by_year.setdefault(y, []).append({'ticker': t, 'growth': growth, 'currency': b['unit']})
    means = [{'year': y, 'median_growth': statistics.median(r['growth'] for r in vals), 'members': vals}
             for y, vals in sorted(by_year.items()) if len(vals) >= min(2, len(members))]
    if not means:
        raise ValueError('No cycle observations')
    worst = min(means, key=lambda r:r['median_growth'])
    subscore = engine.band(worst['median_growth'], [(-.1, 5), (-.2, 4), (-.3, 3), (-.45, 2)])
    ceiling = 2 if len(members) == 1 else 3
    return {'score': min(subscore, ceiling), 'cycle_subscore': subscore, 'ceiling': ceiling,
            'growth_forecast': None, 'proxy': 'own_company_cycle' if ceiling == 2 else 'peer_nominal_revenue_cycle',
            'worst': worst, 'annual': means}


def build(root, config_path):
    cfg = load(config_path)
    if cfg['rule_version'] != engine.VERSION:
        raise ValueError('Use the reverse-v1 entry point for reproduction')
    if date.fromisoformat(cfg['price_date']) > date.fromisoformat(cfg['as_of']):
        raise ValueError('Price date is after research cutoff')
    out = root / cfg['output_dir']; old = root / cfg['baseline_dir']
    save(out/'run-config.json',cfg)
    curated = config_path.parent
    assessments = load(curated/'assessments.json')['companies']
    guidance = load(curated/'guidance-records.json')['companies']
    universe = load(old/'eligible.json')
    annual = load(old/'annual-facts.json')
    filing = {x['ticker']: x for x in load(old/'filing-index.json')}
    valuation = load(old/'valuation.json')
    old_inputs = {x['company_id'].split('/')[1]: x for x in load(old/'scoring-input.json')['companies']}
    snapshots = {r['ticker']: dict(r['tables'][0]) for r in load(old/'snapshots.json')}
    financials = prepare(cfg, root)
    save(out/'normalized-financials.json', financials)
    quant = {}
    for t, rows in financials.items():
        rate, basis = engine.tax_rate(rows)
        if t in cfg.get('tax_rate_overrides', {}):
            rate = cfg['tax_rate_overrides'][t]['rate']; basis = cfg['tax_rate_overrides'][t]['reason']
        returns = engine.capital_return(rows, rate)
        cash = engine.cash_conversion(rows)
        impairment = cfg.get('impairment_lower_bounds', {}).get(t)
        imp_ratio = None
        if impairment:
            average_assets = (rows[0]['goodwill']+rows[0]['intangibles']+rows[-1]['goodwill']+rows[-1]['intangibles'])/2
            lower = impairment['amount']/average_assets
            # A partial history can only determine a subscore at the worst bound.
            if lower > .30:
                imp_ratio = lower
            impairment = dict(impairment, ratio_lower_bound=lower, denominator=average_assets)
        alloc = engine.allocation(returns, rows, imp_ratio)
        quant[t] = {'window': [rows[0]['year'], rows[-1]['year']], 'count': len(rows),
                    'tax_rate': rate, 'tax_basis': basis, 'B1': returns, 'B2': cash, 'M3': alloc,
                    'impairment_evidence': impairment}
    ledger, inputs, cards = [], [], {}
    for issuer in universe:
        t = issuer['ticker']; a = assessments[t]; rows = financials[t]; q = quant[t]
        filings = filing[t]['filings']
        official = next({'url': f['url'], 'local_path': f['local_path']} for f in filings if f['type']=='annual')
        balance = {'url': f'https://stockanalysis.com/stocks/{t.lower()}/financials/balance-sheet/',
                   'local_path': cfg['source_dir']+f'/{t}-sa-balance-web.txt'}
        cfacts = {'url': f'https://data.sec.gov/api/xbrl/companyfacts/CIK{issuer["cik"]:010}.json',
                  'local_path': cfg['baseline_source_dir']+f'/{t}-companyfacts.json'}
        scores, reviews, reasons, entries = {}, {}, {}, []
        def add(k, score, claim, sources=None, review=None, value=None, limits='', kind='calculation', confidence='medium', locator=None):
            review = review or ('evidence_limited' if score is None else 'reviewed')
            scores[k] = score; reviews[k] = review
            if score is None:
                reasons[k] = claim
            rec = {'company_id': 'US/'+t, 'metric_id': k, 'score': score, 'review': review,
                   'claim_type': kind, 'claim': claim, 'sources': sources or [official], 'value': value,
                   'limitations': limits, 'confidence': confidence, 'as_of':cfg['as_of'],
                   'locator': locator or 'Consolidated statements / notes; calculation detail in calculations.json'}
            entries.append(rec); ledger.append(rec)
        def qualitative(k):
            r = a['metrics'][k]
            add(k, r['score'], r['claim'], r['sources'], r['review'], limits=r['limitations'],
                kind=r['claim_type'], confidence=r['confidence'], locator=r['locator'])
        short = t in cfg['provisional_issuers']
        years = cfg.get('perimeter_years', {}).get(t, len(rows))
        for k in ['B1','B2']:
            obj = q[k]; sc = obj['score']
            if short and sc is not None:
                sc = min(sc,3)
            if k=='B1':
                pct = lambda v:'N/A' if v is None else f'{v:.2%}'
                claim = (f"FY{rows[0]['year']}—{rows[-1]['year']}，NOPAT/期末资本；中位数{pct(obj['median'])}；"
                         f"最低连续三年均值{pct(obj['lowest_three_year_mean'])}；"
                         f"含商誉中位数{pct(obj['including_goodwill_median'])}。"
                         + ('经营资本曾非正，全窗口改用含商誉分母、上限4。' if obj.get('whole_window_fallback') else '')
                         + ('两种资本均无有效正分母，需人工适配，不自动给高分。' if obj.get('invalid_capital') else ''))
            else:
                ratio = obj.get('ratio'); upper = obj.get('ratio_upper_bound')
                claim = (f"累计扣SBC后股东FCF {obj.get('fcf_after_sbc', '未确定')} / 合并持续经营净利润{obj.get('profit')}（{rows[0]['currency']}百万）。"
                         + (f'转化率{ratio:.2%}。' if ratio is not None else f'扣SBC前上界{upper:.2%}；'+obj['reason'] if upper is not None else obj.get('reason','')))
            if short:
                claim += f' 当前边界仅{years}完整年，此为前身/混合历史，暂定上限3，禁止自动优先。'
            if k=='B2' and sc is None and a.get('b2_proxy'):
                proxy = a['b2_proxy']; sc = proxy['score']
                add(k, sc, proxy['claim'], proxy['sources'], 'provisional', dict(obj, proxy=proxy), proxy['limitations'], kind='inference',confidence='low')
            else:
                add(k, sc, claim, [official,cfacts,balance], 'provisional' if short and sc is not None else None, obj,
                    limits='期末资本而非平均资本；数据供应商余额含租赁，与官方权益交叉检查。' if k=='B1' else '减值/低利润可放大比率，不等于现金盈利质量优秀；未加回未经验证减值。')
        base_year = cfg.get('gross_base_year', {}).get(t, rows[0]['year'])
        base = next((r for r in annual[t] if r['year']==base_year and r.get('gross_margin') is not None), None)
        last = next(r for r in annual[t] if r['year']==rows[-1]['year'])
        if not base or last.get('gross_margin') is None:
            raise ValueError(f'{t}: gross margin unavailable')
        delta = float((Decimal(str(last['gross_margin']))-Decimal(str(base['gross_margin'])))*100)
        gross = engine.gross_score(delta); gross = min(gross,3) if short else gross
        q['B3a'] = {'base_year':base_year,'last_year':last['year'],'base_margin':base['gross_margin'],
                     'last_margin':last['gross_margin'],'change_pp':delta,'score':gross,'B3b':None}
        claim = f"FY{base_year}毛利率{base['gross_margin']:.2%}→FY{last['year']} {last['gross_margin']:.2%}，变化{delta:+.3f}pp；使用v2完整分档。"
        for k in ['B3a','B3']:
            add(k,gross,claim+('B3b纯价格/成本证据不足，B3按规则回退B3a。'if k=='B3'else''),[official,cfacts],
                'provisional' if short else 'reviewed',q['B3a'],limits='并购、品类组合、运输费用分类和通胀均可能影响毛利；不把price/mix当纯提价。')
        peers = [p for p in cfg['peer_groups'][t] if p not in cfg['provisional_issuers']
                 and quant[p]['B1'].get('including_goodwill_median') is not None]
        peer_median = statistics.median(quant[p]['B1']['including_goodwill_median'] for p in peers) if len(peers)>=3 else None
        own_return = q['B1'].get('including_goodwill_median')
        ratio = own_return/peer_median if peer_median and own_return is not None else None
        cap = 3 if ratio is None else 5 if ratio>=1.5 else 4 if ratio>1 else 3 if ratio>=.9 else 2
        r = a['metrics']['B4']; b4 = min(r['score'],cap)
        peer_sources = [next({'url':f['url'],'local_path':f['local_path']}for f in filing[p]['filings']if f['type']=='annual') for p in peers]
        q['peers'] = {'tickers':peers,'definition':'including_goodwill_roic','median':peer_median,'own_to_peer':ratio,'B4_cap':cap}
        add('B4',b4,r['claim']+f' 定性初分{r["score"]}；同行{peers}，同定义含商誉ROIC上限{cap}，最终{b4}。',
            [official,balance]+peer_sources,value=q['peers'],kind='judgment',limits='横向含商誉回报受品牌形成方式、制造/外包、税率与期末资本影响；同行替换敏感性单列。')
        qualitative('B5')
        for k in ['M1','M2']:
            qualitative(k)
        m3 = min(q['M3']['score'],3) if short and q['M3']['score'] is not None else q['M3']['score']
        add('M3',m3,'含商誉ROIC与复权申报日股数两子项（有可证明最差档减值下界时加入第三项），有效项均值向下取整。',
            [official,cfacts,balance],'provisional'if short else None,dict(q['M3'],impairment_evidence=q['impairment_evidence']),
            limits='不是稀释加权平均股数；股数时点、回购及并购对价均影响变化。不确定减值不填0；未计子项不表示无减值。')
        if t in guidance:
            g = guidance_score(guidance[t]); q['M4']=g
            ceiling=5 if g['count']>=5 else 4 if g['count']>=3 else 3
            add('M4',g['score'],f"首次全年指引中点达成{g['hits']}/{g['count']}（{g['hit_rate']:.0%}）；覆盖{g['count']}年，上限{ceiling}。",
                [r[k]for r in g['records']for k in ['first_target_source','actual_source']],review='provisional'if g['count']<3 else'reviewed',value=g,
                limits='披露的non-GAAP/CC定义逐年配对；文字指引区间是v2分析约定，按公司名称一致性而非选择易达标目标。')
        else:
            qualitative('M4')
        qualitative('M5')
        qualitative('I1')
        i2 = engine.band(peer_median,[(.20,5),(.14,4),(.10,3),(.06,2)])
        add('I2',i2,f'至少三家同经济模型的含商誉ROIC中位数；有效同行{peers}。'+('不足三家，N/A。'if i2 is None else f'中位数{peer_median:.2%}。'),
            [official]+peer_sources,value=q['peers'],limits='v2统一使用含商誉回报作为横向比较；非独立行业全样本统计，BUD/ABEV不重复计权。')
        qualitative('I3')
        cycle = cycle_score(cfg['cycle_groups'][t], annual); q['I4']=cycle
        add('I4',cycle['score'],f"匹配的未来五年需求CAGR未验证；周期最差FY{cycle['worst']['year']}，同行名义收入增长中位数{cycle['worst']['median_growth']:.2%}，周期子分{cycle['cycle_subscore']}。"
            + ('仅公司周期作弱代理，上限2。'if cycle['ceiling']==2 else '采用v2增长未验证分支，上限3。'),
            [official]+[next({'url':f['url'],'local_path':f['local_path']}for f in filing[p]['filings']if f['type']=='annual')for p in cfg['cycle_groups'][t]],value=cycle,
            kind='inference',confidence='low',limits='保留2020；名义合并收入包含汇率、通胀和收购，不能证明终端需求增长。烈酒仅两家；综合公司/代工单家代理更弱。')
        qualitative('I5')
        oldprice = old_inputs[t]['price']; v=valuation[t]
        price = dict(oldprice)
        price['forward_pe'] = None if snapshots[t].get('Forward PE','n/a')=='n/a' else float(snapshots[t]['Forward PE'])
        price['limitation'] = v.get('reason') or v['status']
        if price['percentile'] is not None:
            price['limitation'] = '有效日GAAP EPS经验分位；EPS舍入可影响极近边界值。'
        price['forward_peers'] = [{'ticker':p,'forward_pe':float(snapshots[p]['Forward PE'])}for p in cfg['peer_groups'][t]
                                  if snapshots[p].get('Forward PE','n/a')!='n/a']
        payload = {'company_id':'US/'+t,'name':issuer['name'],'perimeter_years':years,'provisional_history':short,
                   'scores':scores,'metric_review':reviews,'missing_reasons':reasons,'blocking_issues':[], 'price':price}
        inputs.append(payload)
        cards[t] = {'issuer':issuer,'profile':a,'financials':rows,'calculations':q,'evidence':entries,
                    'price':price,'valuation':v,'perimeter_years':years}
    payload = {'rule_version':engine.VERSION,'as_of':cfg['as_of'],'price_date':cfg['price_date'],'companies':inputs}
    results = engine.aggregate(payload)
    results['counts_by_status'] = dict(Counter(c['status']for c in results['companies']))
    results['coverage'] = {'companies':len(inputs),'metric_records':len(ledger),'numerically_scored':sum(r['score']is not None for r in ledger),
                           'reviewed_na':sum(r['score']is None for r in ledger),'pending_work':sum(r['review']=='pending_work'for r in ledger),
                           'factor_complete':sum(c['average']is not None for c in results['companies'])}
    # Score sensitivity is recomputed by the exact same gate engine.
    scenarios = {}
    for name in ['no_relative_moat_cap','akob_sbc_worst','growth_unverified_floor1','customer_bound_upper','B1_including_goodwill']:
        changed = deepcopy(payload)
        for c in changed['companies']:
            t = c['company_id'].split('/')[1]
            if name=='no_relative_moat_cap':c['scores']['B4']=assessments[t]['metrics']['B4']['score']
            if name=='akob_sbc_worst' and t=='AKO.B':c['scores']['B2']=1
            if name=='growth_unverified_floor1':c['scores']['I4']=1
            if name=='customer_bound_upper' and t in ['CCEP','KOF','BUD','CCU','SAM','WEST','MNST']:c['scores']['B5']=min(5,c['scores']['B5']+1)
            if name=='B1_including_goodwill':
                alt = deepcopy(financials[t])
                for row in alt:row['goodwill']=0;row['intangibles']=0
                sc=engine.capital_return(alt,quant[t]['tax_rate'])['score']
                c['scores']['B1']=min(sc,3)if sc is not None and t in cfg['provisional_issuers']else sc
        scenarios[name]=engine.aggregate(changed)
    save(out/'scoring-input.json',payload);save(out/'scoring-results.json',results)
    save(out/'calculations.json',quant);save(out/'cards.json',cards);save(out/'sensitivity.json',scenarios)
    (out/'evidence-ledger.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n'for r in ledger))
    paths={s['local_path']:s.get('url')for r in ledger for s in r['sources']}
    for t in financials:
        paths[cfg['baseline_source_dir']+f'/{t}-snapshot.html']=f'https://stockanalysis.com/stocks/{t.lower()}/'
        paths[cfg['baseline_source_dir']+f'/{t}-prices.json']=f'https://query1.finance.yahoo.com/v8/finance/chart/{t.replace(".","-")}'
    manifest=[]
    original_manifest_path=root/cfg['baseline_source_dir']/'manifest.json'
    original_urls={s['local_path']:s['url'] for s in load(original_manifest_path)['sources']
                   if s.get('local_path') and s.get('url')}
    for path,url in sorted(paths.items()):
        f=root/path
        if not f.is_file():raise ValueError(f'Missing evidence: {path}')
        manifest.append({'local_path':path,'original_url':original_urls.get(path,url),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'retrieved_on':cfg['as_of']})
    save(out/'source-manifest.json',manifest)
    if len(inputs)!=len(universe) or results['coverage']['factor_complete']!=len(universe) or results['coverage']['pending_work']:
        raise ValueError(f'Incomplete run: {results["coverage"]}')
    print(json.dumps(results['coverage'],ensure_ascii=False))
    for c in results['companies']:
        print(c['company_id'],*[c['factors'][p]['score']for p in 'BMI'],c['average'],c['label'])
    return cfg, results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config',type=Path)
    args=parser.parse_args()
    build(Path.cwd(),args.config)


if __name__=='__main__':main()
