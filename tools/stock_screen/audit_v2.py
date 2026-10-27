"""Check v2 coverage, evidence integrity, valuation and deterministic results."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
try:
    from . import engine_v2
except ImportError:
    import engine_v2


def audit_files(root, folder):
    read=lambda name:json.loads((folder/name).read_text())
    cfg=read('run-config.json');payload=read('scoring-input.json');results=read('scoring-results.json')
    ledger=[json.loads(line)for line in(folder/'evidence-ledger.jsonl').read_text().splitlines()]
    computed=engine_v2.aggregate(payload);errors=[]
    if computed['companies']!=results['companies']:errors.append('Stored results differ from recomputation')
    keys={(c['company_id'],k)for c in payload['companies']for k in c['scores']}
    records={(r['company_id'],r['metric_id']):r for r in ledger}
    if set(records)!=keys or len(records)!=len(ledger):errors.append('Evidence keys differ or duplicate')
    for c in payload['companies']:
        for k,s in c['scores'].items():
            r=records.get((c['company_id'],k),{})
            if r.get('score')!=s or r.get('review')!=c['metric_review'][k]:errors.append(f'Ledger mismatch {c["company_id"]}/{k}')
            if not r.get('claim') or not r.get('sources'):errors.append(f'Missing claim/source {c["company_id"]}/{k}')
        if c['price']['percentile']is not None:
            t=c['company_id'].split('/')[1];f=root/cfg['baseline_dir']/(t+'-daily-pe.csv')
            daily=list(csv.DictReader(f.open()));values=[float(r['pe'])for r in daily if r['pe']]
            last=values[-1];p=100*(sum(v<last for v in values)+.5*sum(v==last for v in values))/len(values)
            if abs(p-c['price']['percentile'])>1e-8:errors.append(f'PE percentile differs {t}: {p}')
            if any(r['eps_available_on']>r['date']for r in daily):errors.append(f'Lookahead EPS {t}')
            if daily[-1]['date']!=cfg['price_date']:errors.append(f'Stale price {t}')
            if c['price']['history_years']<5 and len(c['price'].get('forward_peers',[]))<2:errors.append(f'Missing short-history forward peers {t}')
    for s in read('source-manifest.json'):
        f=root/s['local_path']
        if not f.exists()or hashlib.sha256(f.read_bytes()).hexdigest()!=s['sha256']:errors.append(f'Source hash mismatch {f.name}')
    for t,q in read('calculations.json').items():
        for pair in q.get('M4',{}).get('records',[]):
            for key in ['first_target_source','actual_source']:
                dt=pair[key].get('published_on')
                if dt and dt>cfg['as_of']:errors.append(f'Future source {t}')
    for c in computed['companies']:
        if c['average']is None or any(c['factors'][p]['score']is None for p in 'BMI'):errors.append(f'Incomplete factors {c["company_id"]}')
        if c['completion_status']=='pending_work':errors.append(f'Pending work {c["company_id"]}')
        if c['status']=='research_now'and not c['quality_robust_to_unscored']:errors.append(f'Unrobust priority {c["company_id"]}')
    # The issuer information is nested in cards; do not infer cap from share class price.
    caps=[c['issuer']['market_cap_usd']for c in read('cards.json').values()]
    if any(v<500e6 for v in caps):errors.append('Issuer below market-cap floor')
    metric_coverage={k:dict(Counter('scored'if r['score']is not None else r['review']for r in ledger if r['metric_id']==k))for k in engine_v2.SCORE_KEYS}
    result={'rule_version':engine_v2.VERSION,'as_of':cfg['as_of'],'delivery_status':'failed'if errors else'complete_with_declared_limits',
            'scope':'Deterministic calculations, coverage, source integrity and original-price PE timing; qualitative claims require analyst review',
            'errors':errors,'coverage':results['coverage'],'metric_coverage':metric_coverage,
            'all_three_factors':sum(c['average']is not None for c in results['companies']),
            'stage_determined':sum(c['stage_1']is not None for c in results['companies']),
            'pe_histories':sum(c['price']['percentile']is not None for c in payload['companies']),
            'guidance_pairs':sum(q.get('M4',{}).get('count',0)for q in read('calculations.json').values()),
            'source_files':len(read('source-manifest.json')),
            'input_sha256':{name:hashlib.sha256((folder/name).read_bytes()).hexdigest()for name in ['scoring-input.json','scoring-results.json','evidence-ledger.jsonl']}}
    (folder/'completion-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result
