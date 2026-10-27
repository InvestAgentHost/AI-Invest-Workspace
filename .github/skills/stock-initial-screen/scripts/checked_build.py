#!/usr/bin/env python3
"""Run the unchanged batch engine with explicit source-completeness eligibility checks."""
import importlib.util
import json
import copy
from pathlib import Path
import sys


def build(run):
    spec=importlib.util.spec_from_file_location('screen_engine_checked',run/'screener.py')
    engine=importlib.util.module_from_spec(spec)
    old_argv=sys.argv[:]
    try:
        sys.argv=[str(run/'screener.py'),str(run)]
        spec.loader.exec_module(engine)
    finally:sys.argv=old_argv
    gaps=[]
    base_facts=engine.facts;fact_cache={}
    def facts(t):
        if t in fact_cache:return copy.deepcopy(fact_cache[t])
        f=copy.deepcopy(base_facts(t));m=f.get('m1') or {};salary=m.get('base_salary')
        quote=(engine.PE.get(engine.KEY[t]) or {}).get('cur')
        cur=m.get('base_salary_currency') or m.get('salary_currency')
        if salary is not None and (not cur or not quote or cur!=quote):
            rate=m.get('salary_fx') or {}
            from valuation_pipeline import evidence,day,finite
            valid=False
            try:
                evidence(rate,run)
                price_date=(engine.PE.get(engine.KEY[t]) or {}).get('price_date') or engine.AS_OF
                valid=(rate['from']==cur and rate['to']==quote and finite(rate['value']) and rate['value']>0
                       and 0<=(day(price_date)-day(rate['date'])).days<=7)
            except (KeyError,ValueError,OSError):pass
            m['base_salary_original']=salary;m['base_salary_original_currency']=cur
            if valid:
                m['base_salary']=salary*rate['value'];m['base_salary_currency']=quote
            else:
                m['base_salary']=None
                gaps.append({'ticker':t,'field':'M1','reason':'salary currency/dated FX is unverified; cannot divide quote-currency holdings by raw foreign salary'})
            f['m1']=m
        fact_cache[t]=f
        out=run/'facts_model';out.mkdir(exist_ok=True)
        (out/(t+'.json')).write_text(json.dumps(f,ensure_ascii=False,indent=2))
        return copy.deepcopy(f)
    engine.facts=facts
    base_ic=engine.ic
    def ic(row):
        if row is None or any(row.get(k) is None for k in ['eq','debt','cash']):return None
        return base_ic(row)
    engine.ic=ic
    base_measures=engine.measures
    def measures(t,use_facts=True):
        base_rows=engine.rows
        def rows_for_math(*args,**kwargs):
            rows,L,cur=base_rows(*args,**kwargs)
            if rows[L].get('op') is None and rows[L].get('int'):
                rows=copy.deepcopy(rows);rows[L]['int']=None  # Undefined interest cover; never manufacture zero operating income.
            return rows,L,cur
        try:
            engine.rows=rows_for_math;m=base_measures(t,use_facts)
        finally:engine.rows=base_rows
        rows,L,_=engine.rows(t,use_facts)
        def missing(fields,years=None):
            return [(y,k) for y in (m['yrs'] if years is None else years) for k in fields if rows[y].get(k) is None]
        def block(code,why,updates):
            m.update(updates);m['repairs'].append(code+' not scored: '+why);gaps.append({'ticker':t,'field':code,'reason':why})
        profit_gaps=missing(['op','am','imp'])
        goodwill_gaps=missing(['gw'],sorted({y for v in m['yrs'] for y in [v-1,v]}))
        if profit_gaps or goodwill_gaps:
            block('B1',str(profit_gaps+goodwill_gaps),dict(B1=None,B1raw=None,b1Med=None,b1Low=None))
        if profit_gaps:
            block('B4',str(profit_gaps),dict(B4=None,b4Med=None))
            block('B3',str(profit_gaps),dict(B3=None,b3=None))
        cash_gaps=missing(['op','imp','capex','sbc','cfo'])
        if cash_gaps:block('B2',str(cash_gaps),dict(B2=None,b2=None))
        sbc_gaps=missing(['sbc','op'],m.get('sbcYrs',[]))
        if sbc_gaps:block('M2 SBC component',str(sbc_gaps),dict(M2sbc=None,sbcR=None))
        m3_gaps=missing(['imp','gw','ia'],m.get('m3Yrs',[]))
        if m3_gaps:block('M3',str(m3_gaps),dict(M3=None,M3parts=[None,None],impPct=None))
        return m
    engine.measures=measures
    engine.build_all()
    data=json.loads((run/'page_data.json').read_text())
    for t,c in data.items():
        rows,L,_=engine.rows(t);row=rows[L]
        absent=[k for k in ['debt','cash','op','da','int'] if row.get(k) is None]
        if absent:
            risk=next(x for x in c['measures'] if x['code']=='R1')
            risk['note']+=' 尚未核验输入：'+', '.join(absent)+'；缺项不是零。'
            if not c['risk']:
                c['risk']=None;risk['light']='na';risk['calc']='未完成全部财务风险检查：'+', '.join(absent)
            gaps.append({'ticker':t,'field':'R1','missing':absent})
            c['flags'].append('财务风险检查有未核验输入：'+', '.join(absent))
        fs=engine.facts(t);m1=fs.get('m1') or {}
        if m1.get('insiders_net_buyers_24m') is None or m1.get('ceo_sold_over_30pct_24m') is None:
            next(x for x in c['measures'] if x['code']=='M1')['note']+=' 近24个月市场交易调整未核验；当前为已核验持股与薪酬基分，未断言无买卖。'
            c['flags'].append('M1：24个月市场交易调整未核验，显示持股基分')
            gaps.append({'ticker':t,'field':'M1 trade adjustment','reason':'24-month review incomplete; check action sensitivity before delivery'})
        own_gaps=[g for g in gaps if g['ticker']==t]
        for measure in c['measures']:
            reason='；'.join(str(g.get('reason',g.get('missing',''))) for g in own_gaps if g['field']==measure['code'])
            if reason and measure.get('score') is None and measure['code']!='R1':
                measure['gap']='原始输入缺项：'+reason;measure['calc']='Not scored: '+measure['gap']
        # Incomplete capital observations describe data coverage, not the age of the issuer.
        if c['window']['n']==0 and any(rows[y].get(k) is None for y in rows for k in ['eq','debt','cash']):
            c['data_incomplete']=True
            if c['result'].get('kind')!='redflag':
                c['result']['lines']=['资料不足：资本回报输入未齐，不能据可计算年度数推断公司年龄']
                c['result']['why']=['资本回报资料缺项；不推算虚假的未来复核财年']
        for step in c['steps']:
            if step[0]=='Result':step[1]=c['result']['cat']+' — '+'; '.join(c['result']['lines'])
            if step[0]=='Financial risk gate' and absent:step[1]=next(x for x in c['measures'] if x['code']=='R1')['calc']
    (run/'page_data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    unique=list({json.dumps(g,sort_keys=True,ensure_ascii=False):g for g in gaps}.values())
    (run/'data_quality_gaps.json').write_text(json.dumps(unique,ensure_ascii=False,indent=2))
    meta=json.loads((run/'run_meta.json').read_text());meta['source_validation']='checked_build.py: missing capital, profit, cash-flow and stock-pay inputs cannot silently become zero; numerical RULES unchanged'
    (run/'run_meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    return data


if __name__=='__main__':
    if len(sys.argv)!=2:sys.exit('Usage: checked_build.py RUN_DIR')
    build(Path(sys.argv[1]).resolve())
