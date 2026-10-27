#!/usr/bin/env python3
"""Offline behavioral regression tests for evidence-linked batch valuation.

Run from Workspace with its canonical interpreter:
  .venv/bin/python .github/skills/stock-initial-screen/scripts/test_valuation_pipeline.py
Keep reproducible fixtures and command logs with:
  .../test_valuation_pipeline.py --artifacts-dir sources/skill-updates/stock-initial-screen/<unique-eval-dir>

All issuers, prices, financials, disclosures and source-attempt records below are
explicitly synthetic. No external API, network, installed package or real run is
used. HTML hash tests exercise the delivery checker directly, so they do not
depend on BeautifulSoup. Each test snapshots production scripts into its own run.
"""
import argparse
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parent
ARTIFACTS = None


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fixture(run):
    """Four independent economic cases; 2 ordinary shares per FXADS ADS."""
    run.mkdir(parents=True, exist_ok=False)
    for sub in ['raw', 'raw_sources', 'facts']:
        (run/sub).mkdir()
    names = ['valuation_pipeline.py', 'checked_build.py', 'screener.py',
             'make_html.py', 'redesign.py', 'vault_records.py']
    for name in names:
        shutil.copy2(SCRIPTS/name, run/name)
    write(run/'script_snapshot_hashes.json', {n:digest(run/n) for n in names})
    config = dict(title='SYNTHETIC offline reliability regression', as_of='2026-10-26',
                  rules_version='2026-10-23c', output='synthetic.html',
                  valuation_pipeline_required=True,
                  companies={t:dict(key='TEST_'+t, name='SYNTHETIC '+t, group='synthetic')
                             for t in ['FXADS', 'LOSS', 'IPO', 'DEBTGAP']})
    write(run/'config.json', config)
    dates = []
    date = dt.date(2025, 1, 2)
    while date <= dt.date(2026, 10, 23):
        if date.weekday() < 5:
            dates.append(date.isoformat())
        date += dt.timedelta(days=1)
    spec = dict(schema_version=1, price_date='2026-10-23', disclosure_cutoff='2026-10-26', companies={})
    main = {}
    cols = ['fy','rev','op','am','imp','da','eq','debt','cash','gw','ia','cfo','capex','sbc','int','intInc','pt','tax','dil','nicf']
    for t in config['companies']:
        foreign, loss = t == 'FXADS', t == 'LOSS'
        cur = 'EUR' if foreign else 'USD'
        basis = t + ('-ADS-2ordinary' if foreign else '-ordinary')
        source = dict(source='SYNTHETIC disclosure fixture; not a real issuer', raw_path='raw_sources/'+t+'.json')
        start = '2026-09-01' if t == 'IPO' else dates[0]
        c = dict(key='TEST_'+t, listing=t+'.SYNTHETIC', listing_currency='USD', reporting_currency=cur,
                 accounting_standard='IFRS' if foreign else 'US GAAP', quote_unit_id=basis,
                 reporting_frequency='semiannual', economic_history_from=start,
                 history_start_evidence=source.copy(), prices=[], market_caps=[], fx=[], metrics={},
                 ev_claims=dict(debt=1,cash=-1,settlement=1),
                 claims_review=dict(complete=True, **source),
                 limitations=['SYNTHETIC fixture; debt includes leases, settlement is additional; no preferred or NCI.'])
        for i, date in enumerate(dates):
            if date < start:
                continue
            c['prices'].append(dict(date=date,value=30+i*.01,currency='USD',basis=basis,**source))
            if foreign:
                c['fx'].append(dict(date=date,value=1.2,**{'from':'EUR','to':'USD'},**source))
        for field in ['eps','op','da','shares','debt','cash','settlement']:
            events = []
            for period, published in [('2024-12-31','2025-01-01'),('2025-06-30','2025-08-01'),
                                      ('2025-12-31','2026-02-01'),('2026-06-30','2026-08-01')]:
                value = dict(eps=(-2 if loss else 4 if foreign else 2),op=(-20e6 if loss else 20e6),
                             da=5e6,shares=5e6,debt=10e6,cash=2e6,settlement=3e6)[field]
                if t == 'DEBTGAP' and field == 'debt' and period == '2026-06-30':
                    value = None
                e = dict(published=published,available=(dt.date.fromisoformat(published)+dt.timedelta(days=1)).isoformat(),
                         period_end=period,value=value,currency=cur,unit=cur,basis=t+'-business',**source)
                if value is None:
                    e['reason']='SYNTHETIC unavailable financing note; latest null must not fall back to older debt'
                if field == 'shares':
                    e.update(unit='quote_units',currency='shares',basis=basis)
                elif field == 'eps':
                    e.update(unit=cur+'/quote_unit',basis=basis,kind='ttm',definition='diluted_reported_eps')
                elif field in ['op','da']:
                    e.update(kind='ttm',period_start=('2025-07-01' if period=='2026-06-30' else
                                                     '2024-07-01' if period=='2025-06-30' else period[:4]+'-01-01'),
                             definition={'op':'reported_operating_profit','da':'pure_depreciation_amortization'}[field])
                events.append(e)
            c['metrics'][field]=events
        providers=[('FocusAlpha','reused',['all'])]
        if t=='DEBTGAP':
            providers += [('Gangtise','missing_field',['claims']),('Original disclosure','missing_field',['claims'])]
        c['source_attempts']=[dict(provider=provider,tool='OFFLINE_SYNTHETIC',query=dict(ticker=t,synthetic=True,cutoff='2026-10-26'),
                                   retrieved_at='2026-10-26T00:00:00Z',scope=scope,status=status,**source)
                              for provider,status,scope in providers]
        spec['companies'][t]=c
        write(run/source['raw_path'],dict(synthetic=True,notice='No provider queried. No investment facts.',
                                          ordinary_shares=10e6 if foreign else 5e6,ordinary_per_ADS=2 if foreign else 1,
                                          metrics=c['metrics'],prices=c['prices'],fx=c['fx'],attempts=c['source_attempts']))
        rows=[]
        for year in range(2024 if t=='IPO' else 2014,2026):
            op=-20 if loss else 30*(1.08**(year-2014))
            row=dict(fy=year,rev=100*(1.08**(year-2014)),op=op,am=1,imp=0,da=5,eq=100,
                     debt=None if t=='DEBTGAP' else 20,cash=5,gw=10,ia=5,cfo=op*.85,capex=-5,
                     sbc=.3,int=1,intInc=.1,pt=op-.9,tax=max(0,(op-.9)*.25),dil=5,nicf=(op-.9)*.75)
            rows.append([row[k] for k in cols])
        main['TEST_'+t]=dict(t=t,L=2025,cur=cur,cols=cols,rows=rows,amSrc='SYNTHETIC acquired amortization',impSrc='SYNTHETIC impairment expense')
        facts=dict(ticker=t,company='SYNTHETIC '+t,as_of='2026-10-26',sec_registrant=True,fiscal_year_L=2025,
                   fiscal_year_end_latest='2025-12-31',currency=cur,
                   m1=dict(ceo='SYNTHETIC CEO '+t,ceo_since='2010-01-01',shares_owned_excl_options=1e6,
                           base_salary=100000,base_salary_currency=cur,salary_year='2025',
                           insiders_net_buyers_24m=False,ceo_sold_over_30pct_24m=False),
                   say_on_pay=dict(meeting_date='2026-05-01',**{'for':95,'against':5},status='found'),
                   red_flags=dict(item_402_recent=[],icfr=dict(fiscal_year_end='2025-12-31',management_conclusion='effective',
                                                             auditor_opinion='unqualified',material_weaknesses=[]),aaer_recent=[]),
                   data=dict(business_disposal_losses=dict(years={})))
        if foreign:
            facts['m1']['salary_fx']=dict(date='2026-10-23',value=1.2,**{'from':'EUR','to':'USD'},**source)
        write(run/'facts'/(t+'.json'),facts)
    write(run/'raw/main_synthetic.json',main)
    write(run/'valuation_inputs.json',spec)
    write(run/'source_ledger.json',dict(synthetic=True,notice='Offline synthetic regression only. No external source was queried.'))
    write(run/'page_text.json',dict(lead='SYNTHETIC fixtures only; not an investment report.',sources='SYNTHETIC local fixtures only.'))
    return run


class ReliabilityBehavior(unittest.TestCase):
    def setUp(self):
        self.temp = None
        if ARTIFACTS:
            self.root = ARTIFACTS/self._testMethodName
            self.root.mkdir(parents=True,exist_ok=False)
        else:
            self.temp = tempfile.TemporaryDirectory(prefix='valuation-reliability-')
            self.root = Path(self.temp.name)
        self.run = fixture(self.root/'run')
        self.log=[]

    def tearDown(self):
        write(self.root/'command_log.json',self.log)
        if self.temp:
            self.temp.cleanup()

    def cli(self,script,*args,expected=0):
        command=[sys.executable,str(self.run/script),*[str(a) for a in args]]
        result=subprocess.run(command,capture_output=True,text=True)
        self.log.append(dict(command=command,exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr))
        if expected is not None:
            self.assertEqual(result.returncode,expected,result.stdout+'\n'+result.stderr)
        return result

    def stage(self,input_name='valuation_inputs.json',tickers=None):
        args=['build',self.run,'--input',self.run/input_name]
        if tickers:
            args += ['--tickers',tickers]
        self.cli('valuation_pipeline.py',*args)
        return read(self.run/'valuation_stage/valuation_audit.json')

    def build_all(self):
        self.stage()
        self.cli('valuation_pipeline.py','promote',self.run)
        self.cli('checked_build.py',self.run)
        self.cli('valuation_pipeline.py','annotate',self.run)

    def check(self,html=None,expected=0):
        args=['check',self.run]
        if html:
            args += ['--html',html]
        self.cli('valuation_pipeline.py',*args,expected=expected)
        return read(self.run/'delivery_check.json')

    def write_hash_html(self):
        p=self.run/'synthetic.html'
        p.write_text('<meta name="screen-data-sha256" content="'+digest(self.run/'page_data.json')+'">'
                     '<meta name="screen-config-sha256" content="'+digest(self.run/'config.json')+'">历史估值分位不可用',encoding='utf-8')
        return p

    def test_cross_currency_and_ads_basis(self):
        a=self.stage()['companies']['FXADS']['current']
        self.assertAlmostEqual(a['market_cap'],a['price']*5e6)
        self.assertAlmostEqual(a['PE'],a['price']/(4*1.2),places=5)
        self.assertAlmostEqual(a['EV'],a['price']*5e6+(10e6-2e6+3e6)*1.2)
        self.assertAlmostEqual(a['EV_EBIT'],a['EV']/(20e6*1.2),places=5)
        spec=read(self.run/'valuation_inputs.json')
        spec['companies']['FXADS']['metrics']['shares'][-1]['basis']='ordinary-shares-unconverted'
        write(self.run/'bad_basis.json',spec)
        r=self.cli('valuation_pipeline.py','build',self.run,'--input',self.run/'bad_basis.json',expected=1)
        self.assertIn('quote units',r.stderr)

    def test_future_disclosures_cannot_backfill_history(self):
        spec=read(self.run/'valuation_inputs.json')
        future=copy.deepcopy(spec['companies']['FXADS']['metrics']['eps'][-1])
        future.update(published='2026-10-23',available='2026-10-24',period_end='2026-09-30',value=400)
        spec['companies']['FXADS']['metrics']['eps'].append(future)
        write(self.run/'valuation_inputs.json',spec)
        a=self.stage()['companies']['FXADS']['current']
        self.assertEqual(a['eps']['value'],4)
        self.assertAlmostEqual(a['PE'],a['price']/4.8,places=5)
        future['available']='2026-10-23'
        write(self.run/'bad_publication.json',spec)
        r=self.cli('valuation_pipeline.py','build',self.run,'--input',self.run/'bad_publication.json',expected=1)
        self.assertIn('after public disclosure',r.stderr)

    def test_losses_missing_financing_and_short_ipo_are_distinct(self):
        self.build_all()
        a=read(self.run/'valuation_audit.json')['companies']
        self.assertEqual(a['LOSS']['metrics']['pe']['state'],'nonpositive_denominator')
        self.assertEqual(a['LOSS']['metrics']['ebitda']['state'],'nonpositive_denominator')
        self.assertEqual(a['DEBTGAP']['metrics']['pe']['state'],'eligible')
        self.assertEqual(a['DEBTGAP']['metrics']['ebit']['state'],'current_gap')
        self.assertIsNone(a['DEBTGAP']['current']['EV'])
        self.assertIsNone(a['DEBTGAP']['current']['claims']['debt'])
        self.assertEqual(a['IPO']['metrics']['pe']['state'],'short_history')
        self.assertGreater(a['IPO']['current']['PE'],0)
        data=read(self.run/'page_data.json')
        self.assertIsNone(data['DEBTGAP']['risk'])
        self.assertTrue(data['DEBTGAP']['data_incomplete'])
        self.assertIn('资本回报输入未齐',data['DEBTGAP']['result']['lines'][0])
        self.assertIn('当前输入缺项',data['DEBTGAP']['mult']['metrics']['ebit']['why'])
        self.assertTrue(self.check()['passed'])
        self.assertTrue(self.check()['warnings'])

    def test_stale_html_is_rejected(self):
        self.build_all()
        html=self.write_hash_html()
        self.assertTrue(self.check(html)['passed'])
        data=read(self.run/'page_data.json');data['FXADS']['notes']='Changed after HTML generation'
        write(self.run/'page_data.json',data)
        result=self.check(html,expected=1)
        self.assertTrue(any('screen-data-sha256' in e for e in result['errors']))

    def test_partial_repair_preserves_non_targets_and_quality(self):
        self.build_all()
        before=read(self.run/'page_data.json')
        before_raw={name:read(self.run/'raw'/(name+'.json')) for name in ['pe','ev']}
        spec=read(self.run/'valuation_inputs.json')
        spec['companies']['FXADS']['metrics']['eps'][-1]['value']=5
        write(self.run/'valuation_inputs_revision.json',spec)
        a=self.stage('valuation_inputs_revision.json','FXADS')
        self.assertEqual(set(a['companies']),set(before))
        for name in ['pe','ev']:
            candidate=read(self.run/'valuation_stage/raw'/(name+'.json'))
            for ticker in ['LOSS','IPO','DEBTGAP']:
                self.assertEqual(candidate['TEST_'+ticker],before_raw[name]['TEST_'+ticker])
        self.cli('valuation_pipeline.py','promote',self.run)
        self.cli('valuation_pipeline.py','refresh',self.run)
        after=read(self.run/'page_data.json')
        for ticker in ['LOSS','IPO','DEBTGAP']:
            self.assertEqual(after[ticker],before[ticker])
        for field in ['measures','business','industry','management','scores','window','risk']:
            self.assertEqual(after['FXADS'][field],before['FXADS'][field])
        self.assertNotEqual(after['FXADS']['mult']['metrics']['pe']['now'],before['FXADS']['mult']['metrics']['pe']['now'])
        self.assertTrue(self.check()['passed'])

    def test_promote_rejects_changed_input_and_preserves_baseline(self):
        self.stage()
        spec=read(self.run/'valuation_inputs.json')
        spec['companies']['FXADS']['metrics']['eps'][-1]['value']=100
        write(self.run/'valuation_inputs.json',spec)
        result=self.cli('valuation_pipeline.py','promote',self.run,expected=1)
        self.assertIn('source changed since staging',result.stderr)
        self.assertFalse((self.run/'raw/pe.json').exists())

    def test_delivery_rejects_changed_promoted_valuation_series(self):
        self.build_all()
        pe=read(self.run/'raw/pe.json')
        pe['TEST_FXADS']['r']=pe['TEST_FXADS']['r'].rsplit(',',1)[0]+',9999'
        write(self.run/'raw/pe.json',pe)
        result=self.check(expected=None)
        self.assertFalse(result['passed'],'Delivery accepted a changed promoted valuation series without rebuilding page_data/audit')

    def test_delivery_rejects_changed_original_evidence(self):
        self.build_all()
        source=read(self.run/'raw_sources/FXADS.json')
        source['metrics']['eps'][-1]['value']=400
        write(self.run/'raw_sources/FXADS.json',source)
        result=self.check(expected=None)
        self.assertFalse(result['passed'],'Delivery accepted changed raw evidence behind unchanged normalized inputs and audit')

    def test_configured_window_matches_engine_eligibility(self):
        config=read(self.run/'config.json');config['pe_default_from']='2026-09-01'
        write(self.run/'config.json',config)
        self.stage()
        self.cli('valuation_pipeline.py','promote',self.run)
        self.cli('checked_build.py',self.run)
        self.cli('valuation_pipeline.py','annotate',self.run)

    def test_missing_latest_annual_operating_profit_is_not_a_crash(self):
        self.stage()
        self.cli('valuation_pipeline.py','promote',self.run)
        main=read(self.run/'raw/main_synthetic.json')
        cols=main['TEST_FXADS']['cols']
        main['TEST_FXADS']['rows'][-1][cols.index('op')]=None
        write(self.run/'raw/main_synthetic.json',main)
        self.cli('checked_build.py',self.run)
        data=read(self.run/'page_data.json')['FXADS']
        risk=next(m for m in data['measures'] if m['code']=='R1')
        self.assertIn('op',risk['note'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--artifacts-dir',type=Path)
    options,remaining=parser.parse_known_args()
    if options.artifacts_dir:
        ARTIFACTS=options.artifacts_dir.resolve()
        ARTIFACTS.mkdir(parents=True,exist_ok=False)
    unittest.main(argv=[sys.argv[0],*remaining],verbosity=2)
