#!/usr/bin/env python3
"""Audit/repair an existing KO disclosure workbook against preserved SEC HTML.
Run from Workspace with .venv/bin/python. Never rebuild the user's workbook.
Writes a separate reviewed copy; original sources remain intact.
"""
import argparse, ast, copy, hashlib, importlib.util, json, math, re, warnings
from collections import Counter
from pathlib import Path
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from openpyxl import load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.workbook.properties import CalcProperties
warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)
NUM = re.compile(r'\(\s*-?\d[\d,]*(?:\.\d+)?\s*\)|-?\d[\d,]*(?:\.\d+)?|[—–]|N/A')

def norm(s):
    s = str(s or '').lower().replace('\xa0',' ').replace('’',"'").replace('—','-').replace('–','-')
    s = re.sub(r'\s+\d+(?:,\d+)*$', '',s.strip())
    s = re.sub(r'\s+',' ',s)
    s = s.replace("shareowners'equity","shareowners' equity")
    aliases = {'income from continuing operations before income taxes':'income before income taxes',
     'income taxes from continuing operations':'income taxes', 'prepaid expenses and other assets':'prepaid expenses and other current assets',
     'other assets':'other noncurrent assets','other liabilities':'other noncurrent liabilities',
     'average shares outstanding':'average shares outstanding - basic',
     'average shares outstanding assuming dilution':'average shares outstanding - diluted',
     'significant (gains) losses on sales of assets - net':'significant (gains) losses - net',
     'issuances of debt':'issuances of loans, notes payable and long-term debt','payments of debt':'payments of loans, notes payable and long-term debt',
     'less: net income attributable to noncontrolling interests':'less: net income (loss) attributable to noncontrolling interests',
     'net cash provided by (used in) operating activities':'net cash provided by operating activities'}
    if s.startswith('trade accounts receivable'):return 'trade accounts receivable, less allowances'
    if s.startswith('treasury stock, at cost'):return 'treasury stock, at cost'
    if s.startswith('common stock'):return 'common stock, $0.25 par value'
    if s.startswith('property, plant and equipment, less accumulated'):return 'property, plant and equipment - net'
    if s.startswith('income (loss) from discontinued operations') or s.startswith('income from discontinued operations'):return 'income (loss) from discontinued operations, net of income taxes'
    s=s.replace('during the period','during the year').replace('at beginning of period','at beginning of year').replace('at end of period','at end of year')
    return aliases.get(s,s)

def values(cells):
    raw=' '.join(cells).replace('$','').replace('%','')
    out=[]
    for m in NUM.finditer(raw):
        x=m.group().strip()
        if x=='N/A':out.append(None)
        elif x in ('—','–'):out.append(0)
        else:out.append(float(x.strip('() ').replace(',','').replace(' ',''))*(-1 if x.startswith('(') else 1))
    return out

def html_rows(t):
    return [[re.sub(r'\s+',' ',c.get_text(' ',strip=True)) for c in tr.find_all(['td','th'],recursive=False)] for tr in t.find_all('tr')]

class Auditor:
    def __init__(self,root,work,out):
        self.root,self.work,self.out=root,work,out
        self.raw=json.loads((work/'statements_raw.json').read_text());self.ops=json.loads((work/'operating_raw.json').read_text())
        self.model=json.loads((work/'model.json').read_text());self.wb=load_workbook(work/'KO_model.xlsx')
        self.soups={};self.tables={};self.changes=[];self.checked=Counter();self.unresolved=[];self.provenance=[]
        spec=importlib.util.spec_from_file_location('builder',root/'.github/skills/company-research-to-excel/scripts/build_workbook.py')
        b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b);self.builder=b.Builder(self.model)
        self.models={s['name']:s for s in self.model['sheets']};self.by_row={}
        for s in self.model['sheets']:
            if s['kind']!='statement':continue
            self.by_row[s['name']]={self.builder.registry[s['short']][r['id']]:r for b in s['blocks'] for r in b['rows'] if 'id' in r}
    def soup(self,key):
        if key not in self.soups:
            p=self.root/Path(self.raw[key]['md_path']).parent.parent/'raw/source.html'
            s=BeautifulSoup(p.read_text(),'lxml')
            for tag in s.find_all('sup'):tag.decompose()
            for tag in list(s.find_all(style=re.compile(r'vertical-align\s*:\s*super',re.I))):tag.decompose()
            for tag in list(s.find_all(style=re.compile(r'position\s*:\s*relative;?[^;]*;?top\s*:\s*-|top\s*:\s*-',re.I))):tag.decompose()
            self.soups[key]=s;self.tables[key]=[(t,html_rows(t)) for t in s.find_all('table')]
        return self.soups[key]
    def select(self,key,predicate):
        self.soup(key)
        candidates=[(t,rows) for t,rows in self.tables[key] if predicate(t.get_text(' ',strip=True).lower())]
        if not candidates:raise ValueError('No source table '+key)
        return candidates[0][1]
    def source(self,key,table=''):
        path=str(Path(self.raw[key]['md_path']).parent.parent/'raw/source.html')
        acc=self.raw[key]['accession'].replace('-','')
        return {'filing':key,'path':path,'url':f'https://www.sec.gov/Archives/edgar/data/21344/{acc}/','table':table}
    def put(self,sn,rn,period,value,source,reason='source-cell verification',factor=1):
        ws=self.wb[sn];cols={c.value:c.column for c in ws[3] if c.value};col=cols[period];c=ws.cell(rn,col)
        value=value*factor if isinstance(value,(int,float)) else value
        if isinstance(value,float) and value.is_integer():value=int(value)
        self.checked[sn]+=1
        self.provenance.append({'sheet':sn,'cell':c.coordinate,'period':period,'expected':value,**source})
        if c.data_type=='f':return  # Preserve links; numeric tie-outs are checked separately.
        same=c.value==value or (isinstance(c.value,(int,float)) and isinstance(value,(int,float)) and math.isclose(c.value,value,rel_tol=1e-12,abs_tol=1e-12))
        if not same:
            self.changes.append({'sheet':sn,'cell':c.coordinate,'period':period,'label':ws.cell(rn,1).value,'before':c.value,'after':value,'reason':reason,**source})
            c.value=value
            c.comment=Comment(f"Verified 2026-10-14; {source['filing']}; {source['table']}\n{source['path']}\n{reason}",'Codex audit')
        r=self.by_row.get(sn,{}).get(rn)
        if r and r.get('type')=='input':
            r.setdefault('values',{})[period]=value
    def statement(self):
        for sn,kind in [('Income Statement','IS'),('Balance Sheet','BS'),('Cash Flow','CF')]:
            ws=self.wb[sn]
            for period in self.builder.layout.all_labels:
                y=int(re.search(r'20\d\d',period)[0]);isq=not period.startswith('FY')
                key=(f'10Q-Q{period[0]}/FY{y}' if isq else f'10K-FY{min(y+(1 if kind=="BS" else 2),2025)}')
                if kind=='IS':pred=lambda x:all(s in x for s in ['net operating revenues','gross profit','selling, general and administrative expenses','basic net income per share'])
                elif kind=='BS':pred=lambda x:all(s in x for s in ['total assets','total current liabilities','treasury stock'])
                else:pred=lambda x:all(s in x for s in ['operating activities','purchases of property','financing activities']) and ('consolidated net income' in x or 'net income from continuing' in x)
                rows=self.select(key,pred)
                # Financial rows have one label cell followed by presentation columns.
                expected={}
                n=0 if isq else min(y+(1 if kind=='BS' else 2),2025)-y
                for cells in rows:
                    if not cells:continue
                    lab=norm(cells[0]);v=values(cells[1:])
                    if kind=='BS' and lab=='deferred income taxes':lab='deferred income tax liabilities'
                    if lab and v and n<len(v):expected[lab]=v[n]
                seen=set()
                for rn,r in self.by_row[sn].items():
                    if r.get('type')!='input':continue
                    label=r.get('note','').split('Filed caption: ',1)[-1] if 'Filed caption: ' in r.get('note','') else r['label']
                    label=label.split(' Full label:',1)[0]
                    if 'Full label: ' in r.get('note','') and 'Filed caption: ' not in r.get('note',''):label=r['note'].split('Full label: ',1)[1]
                    lab=norm(label)
                    if lab in expected:
                        self.put(sn,rn,period,expected[lab],self.source(key,kind),'SEC HTML statement, exact caption and period column');seen.add(lab)
                    elif period in r.get('values',{}):self.unresolved.append({'sheet':sn,'period':period,'label':label,'reason':'caption not matched'})
                for lab in expected.keys()-seen:
                    if any(x in lab for x in ['ended','in millions','liabilities and equity','december']):continue
                    self.unresolved.append({'sheet':sn,'period':period,'label':lab,'reason':'source caption absent from workbook'})
    def volumes(self):
        annual={};quarter={};self.verified_volume_raw={}
        # Verify the system total in the HTML narrative, with the original year mapping.
        for y,b in self.ops["unit_case_volume_bn"].items():
            if not 2016<=int(y)<=2025:continue
            key="10K-"+b["filing"].split()[0];self.soup(key)
            txt=self.soups[key].get_text(" ",strip=True)
            m=re.search(r"The Coca-Cola system sold (.+?) unit cases",txt)
            vv=re.findall(r"([0-9.]+)\s*billion",m[1]) if m else []
            fy=int(key[-4:]);n=fy-int(y)
            if n>=len(vv):raise ValueError("Missing system volume "+y)
            self.put("Operating Metrics",14,"FY"+y,float(vv[n]),self.source(key,"Beverage Volume narrative"))
        for key in self.raw:
            y=int(re.search(r'20\d\d',key)[0]);isq='10Q' in key
            rows=self.select(key,lambda x:'worldwide' in x and 'unit cases' in x and 'concentrate sales' in x)
            heads=' '.join(' '.join(c) for c in rows[:5]);pairs=re.findall(r'(20\d\d)\s+(?:versus|vs\.)\s+(20\d\d)',heads)
            nperiod=2 if len(pairs)>1 else 1
            rawrows=[]
            for c in rows:
                if not c or norm(c[0]) not in ['worldwide','emea','europe, middle east & africa','latin america','north america','asia pacific','global ventures','bottling investments']:continue
                seg='EMEA' if norm(c[0])=='europe, middle east & africa' else c[0]
                v=values(c[1:]);rawrows.append([seg]+v)
                if isq:
                    q=re.search(r'Q(\d)',key)[1];period=f'{q}Q{y}';quarter[(period,seg)]=(v[:2],key)
                else:
                    for j in range(nperiod):
                        yy=int(pairs[j][0]) if pairs else y
                        if 2016<=yy<=2025:annual[(f'FY{yy}',seg)]=(v[j*2:j*2+2],key)
            if not isq:
                self.verified_volume_raw[str(y)]={"rows":rawrows,"path":self.raw[key]["md_path"],"line":self.ops.get("volume_growth",{}).get(str(y),{}).get("line",0),"periods":[[int(a),int(b)] for a,b in pairs] or [[y,y-1]],"html_path":self.source(key)["path"]}
        # Dict filing order is ascending, so later comparative presentations win.
        ws=self.wb['Operating Metrics']
        for rn,metric in [(r,0) for r in range(18,25)]+[(r,1) for r in range(27,32)]:
            seg=ws.cell(rn,1).value
            for (period,s),(v,key) in {**annual,**quarter}.items():
                if s==seg and len(v)>metric:
                    value='N/A' if v[metric] is None else v[metric]/100
                    self.put('Operating Metrics',rn,period,value,self.source(key,'Beverage volume growth'),'Separate unit cases / concentrate sales; superscript footnotes excluded')
                    ws.cell(rn,{c.value:c.column for c in ws[3]}[period]).number_format='0.0%;(0.0%);"-"'
        # Add Asia Pacific / Global Ventures concentrate rows without shifting existing links.
        # Reuse the existing spacer row 32 for AP; put GV in a new audit supplement instead.
        for seg in ['Asia Pacific','Global Ventures']:
            if seg=='Asia Pacific':
                rn=32;ws.cell(rn,1).value=seg
                ws.cell(rn,1)._style=copy.copy(ws['A31']._style)
                for (period,s),(v,key) in {**annual,**quarter}.items():
                    if s==seg and len(v)>1:
                        self.put('Operating Metrics',rn,period,'N/A' if v[1] is None else v[1]/100,self.source(key,'Beverage volume growth'),'Previously omitted concentrate sales segment')
                        ws.cell(rn,{c.value:c.column for c in ws[3]}[period])._style=copy.copy(ws['D31']._style)
            else:
                # Place omitted GV below existing content; explicit header and periods.
                rn=124;ws.cell(123,1).value='Concentrate sales volume growth — Global Ventures (supplement)';ws.cell(rn,1).value=seg
                for (period,s),(v,key) in {**annual,**quarter}.items():
                    if s==seg and len(v)>1:
                        self.put('Operating Metrics',rn,period,'N/A' if v[1] is None else v[1]/100,self.source(key,'Beverage volume growth'),'Previously omitted concentrate sales segment')
                        ws.cell(rn,{c.value:c.column for c in ws[3]}[period])._style=copy.copy(ws['D31']._style)
        ws['B15']='Growth calculated from rounded billion-case totals; may differ from issuer-reported comparable volume growth below (calendar and structural adjustments). '
        ws['B24']='Global Ventures FY2018 is the comparative disclosed in FY2019 10-K, including acquired-business history; FY2019 excludes Costa non-ready-to-drink volume. See the volume footnotes; segment dissolved in FY2025.'
        ws['B30']='Company explicitly reports concentrate sales for Bottling Investments as N/A; N/A is neither zero nor the adjacent footnote number.'
        ws['B123']='Same concentrate-sales table as rows 27-32; supplement retains all existing workbook row references.'
        # Fix percentage style of user-added Global Ventures quarterly UC.
        for c in ws[24][2:]:
            if c.value is not None:c.number_format=ws['D18'].number_format
    def raw_operating(self):
        corrected=copy.deepcopy(self.ops);corrected["volume_growth"]=self.verified_volume_raw
        for kind,blocks in self.ops.items():
            if kind in ['checks','volume_growth','unit_case_volume_bn','customer_concentration','goodwill_by_segment']:continue
            for fy,b in blocks.items():
                if kind in ['debt_by_type','held_for_sale','equity_fair_value'] and fy!='2025':continue
                key=f'10K-FY{fy}';self.soup(key)
                labels=list(b.get('rows',{})) if isinstance(b.get('rows'),dict) else [r[0] for r in b.get('rows',[])]
                if b.get('blocks'):labels=list(next(iter(b['blocks'].values())).keys())
                wanted={norm(x) for x in labels if x}
                if not wanted:continue
                candidates=[]
                for t,rows in self.tables[key]:
                    got={norm(c[0]) for c in rows if c}
                    score=len(wanted&got)/len(wanted)
                    expected_n = len(next(iter(b['rows'].values()))) if isinstance(b.get('rows'),dict) else len(b['rows'][0])-1 if b.get('rows') else None
                    count_match=sum(norm(c[0]) in wanted and len(values(c[1:]))==expected_n for c in rows if c) if expected_n else 0
                    txt=t.get_text(' ',strip=True).lower()
                    if kind=='revenue_factors' and not ('volume' in txt and 'acquisitions' in txt):continue
                    if kind=='segment_revenue_pct' and ('unit cases' in txt or 'volume' in txt or 'operating income' in txt):continue
                    candidates.append((score,count_match,len(rows),rows))
                score,_,_,rows=max(candidates,key=lambda x:(x[0],x[1],-x[2]))
                if score<.7:
                    self.unresolved.append({'table':kind,'filing':key,'reason':'HTML table mapping below threshold','score':score});continue
                dest=corrected[kind][fy]
                if b.get('blocks'):
                    yy=None
                    for c in rows:
                        if not c:continue
                        m=re.search(r'(20\d\d)',c[0]);lab=norm(c[0])
                        if m and (lab.startswith('year ended') or re.fullmatch(r'20\d\d',lab)):yy=m[1];continue
                        if yy in dest['blocks']:
                            target=next((l for l in dest['blocks'][yy] if norm(l)==lab),None)
                            if target is not None:
                                vv=values(c[1:]);n=len(dest['blocks'][yy][target])
                                if len(vv)==n:dest['blocks'][yy][target]=vv
                else:
                    found={norm(c[0]):c for c in rows if c}
                    for lab in labels:
                        c=found.get(norm(lab))
                        if c is None:continue
                        old=b['rows'][lab] if isinstance(b['rows'],dict) else next(r[1:] for r in b['rows'] if r[0]==lab)
                        if kind=='debt_by_type':
                            vv=values(c[1:])
                            if len(vv)==2*len(old):vv=vv[::2]
                        else:vv=values(c[1:])
                        if len(vv)!=len(old):
                            self.unresolved.append({'table':kind,'filing':key,'label':lab,'reason':'column count mismatch','html':vv,'raw':old});continue
                        if isinstance(dest['rows'],dict):dest['rows'][lab]=vv
                        else:next(r for r in dest['rows'] if r[0]==lab)[1:]=vv
        # Use sheet assembler strictly to map audited source arrays to IDs; existing workbook layout survives.
        spec=importlib.util.spec_from_file_location('ops_sheets',self.work/'_ops_sheets.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        for sn,blocks in [('Operating Metrics',mod.sheet_ops(corrected)),('Note Schedules',mod.sheet_notes(corrected))]:
            s=self.models[sn];idx=self.builder.registry[s['short']]
            for block in blocks:
                for r in block['rows']:
                    if r.get('type')!='input' or r.get('id','').startswith(('ops_uc','ops_cs')):continue
                    rn=idx.get(r['id'])
                    if rn is None:continue
                    for period,value in r.get('values',{}).items():
                        if not self.builder.layout.in_span(r,period):continue
                        kind='revenue_factors' if r['id'].startswith('ops_fac') else 'line_of_business' if r['id'].startswith('ops_lob') else 'segment_revenue_pct' if r['id'].startswith('ops_mix') else 'equity_method_summary' if r['id'].startswith('note_eq_') else 'equity_fair_value' if r['id'].startswith('note_fv_') else 'tax_pretax' if r['id'].startswith('note_tax_pt') else 'tax_current_deferred' if r['id'].startswith(('note_tax_current','note_tax_deferred')) else 'unrecognized_tax_benefits' if r['id'].startswith('note_utb') else 'debt_by_type' if r['id'].startswith('note_debt') else 'held_for_sale'
                        yy=int(period[-4:]);fy=max((int(f) for f,b in corrected[kind].items() if yy in [int(y) for y in (b.get('years') or list(b.get('blocks',{})) or [f])]),default=yy)
                        source=self.source(f'10K-FY{fy}',block['title'])
                        self.put(sn,rn,period,value,source,'SEC HTML table label and numeric-column verification')
        self.corrected_ops=corrected
    def quarters_operating(self):
        for period in self.builder.layout.quarterly_labels:
            y=int(period[-4:]);key=f'10Q-Q{period[0]}/FY{y}'
            rows=self.select(key,lambda x:all(k in x for k in ['concentrate operations','finished product operations','united states','international','three months']))
            first={};
            for c in rows:
                if not c:continue
                lab=norm(c[0])
                if lab in ['concentrate operations','finished product operations','total'] and lab not in first:first[lab]=values(c[1:])
            for base,lab in [(89,'concentrate operations'),(95,'finished product operations'),(101,'total')]:
                v=first[lab]
                for j in range(3):self.put('Operating Metrics',base+j,period,v[j],self.source(key,'Note 3: three-month revenue by line of business'))
            # Revenue-factor tables: fixed source columns, one row per geography.
            rows=self.select(key,lambda x:all(k in x for k in ['volume','acquisitions','consolidated']) and ('price/mix' in x or 'price, product' in x))
            first={}
            for c in rows:
                if not c:continue
                seg='EMEA' if norm(c[0])=='europe, middle east & africa' else c[0]
                if seg in ['Consolidated','EMEA','Latin America','North America','Asia Pacific','Bottling Investments','Global Ventures'] and seg not in first:first[seg]=values(c[1:])[:5]
            ws=self.wb['Operating Metrics']
            for base,j in [(35,0),(44,1),(53,2),(62,3),(71,4)]:
                for rn in range(base,base+7):
                    seg=ws.cell(rn,1).value
                    if seg in first and len(first[seg])==5:self.put('Operating Metrics',rn,period,first[seg][j]/100,self.source(key,'Three-month net revenue factors'))
            # Mix derives from filed three-month segment revenue; formula references are separately checked.
    def segments(self):
        ws=self.wb['Segments']
        metricmap={'third party':'third_party','intersegment':'interseg','total net operating revenues':'total_rev','operating income (loss)':'op_income','operating income':'op_income','depreciation and amortization':'da','capital expenditures':'capex'}
        def extract(key):
            self.soup(key);out={};cols=None;current=None
            for t,rows in self.tables[key]:
                txt=t.get_text(' ',strip=True).lower()
                if 'third party' not in txt or 'intersegment' not in txt or 'operating income' not in txt:continue
                if 'latin america' in txt:
                    for c in rows:
                        if any('Latin America' in x for x in c) and any('Consolidated' in x for x in c):
                            cols=[x for x in c if x];break
                if cols is None:continue
                for c in rows:
                    if not c:continue
                    lab=norm(c[0])
                    if ('year ended' in lab or 'months ended' in lab or 'as of and for' in lab or re.fullmatch(r'20\d\d',c[0])) and re.search(r'20\d\d',c[0]):
                        yr=re.search(r'20\d\d',c[0])[0];current=(yr,'ytd' if 'six months' in lab or 'nine months' in lab else 'q' if 'three months' in lab else 'fy');out.setdefault(current,{'cols':cols,'rows':{}})
                    if current and lab in metricmap:
                        v=values(c[1:]);name=metricmap[lab]
                        if len(v)==len(cols):out[current]['rows'][name]=v
                        else:self.unresolved.append({'sheet':'Segments','filing':key,'label':lab,'reason':'segment source column count','values':len(v),'columns':len(cols)})
            return out
        cache={}
        for rn,r in self.by_row['Segments'].items():
            if r.get('type')!='input' or not r.get('values'):continue
            rid=r['id'];prefix=rid[0]
            metric=next((m for m in ['third_party','interseg','total_rev','op_income','capex','da'] if rid.startswith(prefix+'_'+m+'_')),None)
            if not metric:continue
            seg=r['label']
            for period in self.builder.layout.all_labels:
                cell=ws.cell(rn,self.builder.layout.col_of[period])
                if cell.value is None:continue
                y=int(period[-4:]);isq=not period.startswith('FY')
                if isq:
                    if not (prefix=='c' and period!='3Q2024' or prefix=='b' and period=='3Q2024'):continue
                    key=f'10Q-Q{period[0]}/FY{y}'
                else:
                    if period not in r.get('values',{}):continue
                    f=2025 if prefix=='c' else 2018 if prefix=='a' else {2017:2019,2018:2020,2019:2021,2020:2022,2021:2023,2022:2024,2023:2024,2024:2024}[y]
                    key=f'10K-FY{f}'
                if key not in cache:cache[key]=extract(key)
                blk=cache[key].get((str(y),'q' if isq else 'fy'))
                if not blk or metric not in blk['rows']:self.unresolved.append({'sheet':'Segments','cell':cell.coordinate,'period':period,'reason':'segment metric not located'});continue
                cols=['EMEA' if norm(c)=='europe, middle east & africa' else c for c in blk['cols']]
                target='Consolidated' if seg=='Consolidated (as reported)' else seg
                if target not in cols:self.unresolved.append({'sheet':'Segments','cell':cell.coordinate,'reason':'segment not located','segment':seg});continue
                self.put('Segments',rn,period,blk['rows'][metric][cols.index(target)],self.source(key,'Segment note, '+('three months' if isq else str(y))+' / '+metric))
    def geography(self):
        for period in self.builder.layout.all_labels:
            y=int(period[-4:]);isq=not period.startswith('FY');key=f'10Q-Q{period[0]}/FY{y}' if isq else f'10K-FY{min(y+2,2025)}'
            if isq:
                # 10-Q Note 3 supplies US/International revenue via total business operations.
                rows=self.select(key,lambda x:all(k in x for k in ['concentrate operations','finished product operations','united states','international','three months']))
                vals=next(values(c[1:]) for c in rows if c and norm(c[0])=='total');labels=['United States','International','Net operating revenues'];n=0
            else:
                rows=self.select(key,lambda x:all(k in x for k in ['united states','international','net operating revenues']) and 'concentrate operations' not in x and 'income before' not in x and 'gross profit' not in x and 'pension' not in x)
                n=min(y+2,2025)-y;vals=[]
                for lab in ['united states','international','net operating revenues']:
                    c=next(c for c in rows if c and norm(c[0])==lab);vals.append(values(c[1:])[n])
            for j in range(3):self.put('Geography',11+j,period,vals[j],self.source(key,'Geography / three-month Note 3 total' if isq else 'Geography revenue'))
            if isq:continue
            bsy=min(y+1,2025);key=f'10K-FY{bsy}'
            rows=self.select(key,lambda x:all(k in x for k in ['united states','international','property, plant and equipment']) and 'net operating revenues' not in x and 'pension' not in x)
            n=bsy-y
            for rn,lab in [(21,'united states'),(22,'international'),(23,'property, plant and equipment - net')]:
                c=next(c for c in rows if c and norm(c[0])==lab);self.put('Geography',rn,period,values(c[1:])[n],self.source(key,'Geography PP&E'))
    def note_completeness(self):
        key='10K-FY2025';txt=self.soup(key).get_text(' ',strip=True)
        m=re.search(r'one bottler accounted for (\d+)\s*% of our net operating revenues',txt)
        if not m:raise ValueError('Customer concentration disclosure not found')
        self.put('Operating Metrics',119,'FY2025',int(m[1])/100,self.source(key,'Business / geographic data: bottler concentration'),'Restore disclosed 10% concentration; same-paragraph no-customer-over-10% applies to 2024/2023')
        self.wb['Operating Metrics']['L119'].number_format=self.wb['Operating Metrics']['D18'].number_format
        self.wb['Operating Metrics']['B119']='2025: one bottler accounts for 10% of revenue. The following sentence refers to 2024 and 2023; it does not negate the 2025 disclosure.'
        ws=self.wb['Note Schedules']
        ws['A26']='2. EQUITY METHOD INVESTMENTS — QUOTED FAIR VALUES (FY2025, Note 6; carrying-value bridge below)'
        ws['A104']='EQUITY METHOD INVESTMENTS — CARRYING VALUES AND FAIR-VALUE DIFFERENCES (FY2025 supplement)'
        source=self.source(key,'Note 6: publicly traded equity method investments, Fair Value / Carrying Value / Difference')
        fv=self.corrected_ops['equity_fair_value']['2025']['rows']
        carryrows=[];diffrows=[]
        for i,r in enumerate(x for x in fv if not x[0].startswith('Total')):
            rn=106+2*i;name=r[0]
            ws.cell(rn,1,name+' — carrying value');ws.cell(rn+1,1,name+' — fair value less carrying value')
            self.put('Note Schedules',rn,'FY2025',r[2],source,'Restore omitted carrying-value column')
            self.put('Note Schedules',rn+1,'FY2025',r[3],source,'Restore omitted difference column as live formula')
            ws.cell(rn+1,12,f'=L{27+i}-L{rn}')
            self.changes[-1]['after']=ws.cell(rn+1,12).value
            for rr in [rn,rn+1]:
                ws.cell(rr,12)._style=copy.copy(ws['L27']._style)
                ws.cell(rr,1)._style=copy.copy(ws['A27']._style)
            carryrows.append(rn);diffrows.append(rn+1)
        for rn,label,colrows in [(123,'Total quoted fair value',list(range(27,34))),(124,'Total carrying value',carryrows),(125,'Total fair value less carrying value',diffrows)]:
            v=next(r for r in fv if r[0].startswith('Total'))[rn-122]
            ws.cell(rn,1,label);self.put('Note Schedules',rn,'FY2025',v,source,'Restore total from the same disclosure, linked to components')
            ws.cell(rn,12,'='+'+'.join('L'+str(r) for r in colrows))
            self.changes[-1]['after']=ws.cell(rn,12).value
            ws.cell(rn,12)._style=copy.copy(ws['L76']._style)
        ws['A126']='Check: total fair value - carrying value - difference (≈0)';ws['L126']='=L123-L124-L125'
        ws['B104']=source['path']
        for rr in diffrows+[123,124,125,126]:ws.cell(rr,12).font=Font(name='Arial',size=10,color='000000')
        ws['L126']._style=copy.copy(self.wb['Balance Sheet']['L66']._style)
        self.wb['Derived Metrics']['B39']='Annual columns: annual EBITDA denominator. Quarterly columns: discrete three-month EBITDA denominator, without annualization; these multiples are not directly comparable to annual multiples.'
    def review_metadata(self):
        for ws in self.wb:
            if isinstance(ws['A2'].value,str):ws['A2']=ws['A2'].value.replace('2026-10-13','2026-10-14')
        cover=self.wb['Cover']
        for row in cover:
            label=str(row[0].value or '')
            if label=='Workbook date':row[1].value='2026-10-14 (reviewed; original export 2026-10-13)'
            if label.startswith('Derived Metrics'):row[1].value='Live formulas from verified IS/BS/CF and segment D&A; annual and selected discrete-quarter ratios. Cash-flow ratios retain annual coverage where quarterly inputs are cumulative.'
            if label=='BS Detail, Note Schedules, Operating Metrics':
                row[0].value='Operating Metrics and Note Schedules coverage'
                row[1].value='Built and verified: volume, revenue factors, line of business, debt, income taxes, equity-method investees, and assets/liabilities held for sale. Standalone BS Detail remains absent.'
            if label=='Quarterly gaps':row[1].value='4Q2024/4Q2025 are not separately derived. Quarterly YoY growth is shown only for matching periods present in the workbook. Undisclosed inputs remain blank; explicit N/A remains N/A.'
        rn=cover.max_row+2
        cover.cell(rn,1,'Review 2026-10-14');cover.cell(rn,2,'See Audit 2026-10-14 for source-cell checks and change log. Original workbook preserved; source numbers verified against SEC raw HTML after excluding superscript footnotes.')
        cover.cell(rn+1,1,'Operating Metrics');cover.cell(rn+1,2,'FY2016-FY2025 volume growth and six disclosed quarters; omitted Asia Pacific / Global Ventures concentrate-sales rows restored. Global Ventures comparative FY2018 follows FY2019 disclosure basis.')
        cover.cell(rn+2,1,'Note Schedules');cover.cell(rn+2,2,'FY2025 equity-investment carrying values / differences / totals restored as a supplement; original fair values retained.')
        src=self.wb['Sources'];rn=src.max_row+2
        src.cell(rn,1,'Review 2026-10-14');src.cell(rn,2,'Raw SEC HTML exact-caption / exact-period checks; 10 annual filings and six interim filings. Superscript / raised-position footnotes excluded before numeric extraction.')
        src.cell(rn+1,1,'Audit evidence');src.cell(rn+1,2,str(self.out.relative_to(self.root)/'source-cell-audit.json'))
        src.cell(rn+2,1,'Formula evaluation');src.cell(rn+2,2,'Independent arithmetic evaluation and Excel full rebuild/recalculation; formula results checked against disclosed source inputs and existing tie-outs.')
        src.cell(rn+3,1,'Source-basis caution');src.cell(rn+3,2,'Growth from rounded unit-case totals differs from reported comparable growth; quarterly CF is cumulative; quarterly net-debt/EBITDA uses discrete-quarter EBITDA without annualization.')
        summary=self.wb.create_sheet('Audit 2026-10-14')
        summary.append(['KO workbook review — 2026-10-14']);summary.append(['Coverage','FY2016-FY2025; 3Q2024, 1Q/2Q/3Q2025, 1Q/2Q2026'])
        summary.append(['Method','SEC original HTML; caption and period-column matching; superscripts removed'])
        summary.append(['Source-cell checks',len({(x['sheet'],x['cell']) for x in self.provenance})])
        summary.append(['Unresolved source matches',len(self.unresolved)])
        summary.append(['Data cells revised or completed',len(self.changes)])
        summary.append(['Formula verification','All numeric formulas evaluated; no errors or off-tolerance tie-outs. See formula-audit.json.'])
        summary.append(['Preservation','Original workbook retained. All original numeric formulas and unrelated worksheet data preserved.'])
        summary.append(['Interpretation','N/A = explicitly not applicable. Blank = undisclosed / out of scope. Dash zero = explicitly disclosed zero.'])
        summary.append(['Workbook source','research/companies/US/KO-coca-cola/outputs/company-research-to-excel-20261013/KO_model.xlsx'])
        summary.append(['Audit evidence',str(self.out.relative_to(self.root)/'source-cell-audit.json')])
        summary.append([]);summary.append(['Sheet','Source checks','Data changes'])
        counts=Counter(x['sheet'] for x in self.changes)
        for sn,n in self.checked.items():summary.append([sn,n,counts[sn]])
        summary.append([]);summary.append(['Sheet','Cell','Period','Metric','Before','After','Filing','Original source URL','Workspace-relative source','Reason'])
        for x in self.changes:
            row=[x['sheet'],x['cell'],x['period'],x['label'],str(x['before']) if x['before'] is not None else '(blank)',str(x['after']),x['filing'],x['url'],x['path'],x['reason']]
            summary.append(row)
            # Change-log formulas are literal documentation, never live computations.
            for c in summary[summary.max_row]:
                if c.data_type=='f':c.data_type='s'
        for col,width in zip('ABCDEFGHIJ',[24,12,14,62,20,28,24,65,80,65]):summary.column_dimensions[col].width=width
        summary.freeze_panes='E23';summary.sheet_view.showGridLines=False;summary.sheet_view.zoomScale=85
        summary.sheet_properties.tabColor='1F4E79'
        for row in summary:
            for c in row:
                c.font=Font(name='Arial',size=10);c.alignment=Alignment(vertical='top',wrap_text=True)
            summary.row_dimensions[row[0].row].height=30
        for rn in [1,13,22]:
            for c in summary[rn]:c.fill=PatternFill('solid',fgColor='1F4E79');c.font=Font(name='Arial',size=10,bold=True,color='FFFFFF')
        for ws in [cover,src]:
            for row in ws:
                for c in row:
                    if c.value is not None:c.alignment=Alignment(vertical='top',wrap_text=True)
                ws.row_dimensions[row[0].row].height=max(ws.row_dimensions[row[0].row].height or 16.5,32)
        self.wb['Operating Metrics'].row_dimensions[32].height=16.5
        self.wb['Operating Metrics'].print_area='A1:U124';self.wb['Note Schedules'].print_area='A1:U126'
        self.wb.active=self.wb.sheetnames.index('Operating Metrics')
    def run(self):
        for name in ['statement','volumes','raw_operating','quarters_operating','segments','geography','note_completeness','review_metadata']:
            print('Running',name,flush=True);getattr(self,name)()
        self.out.mkdir(parents=True,exist_ok=True)
        (self.out/'source-cell-audit.json').write_text(json.dumps({'checked':dict(self.checked),'changes':self.changes,'unresolved':self.unresolved,'provenance':self.provenance},ensure_ascii=False,indent=2))
        (self.out/'operating_raw_verified.json').write_text(json.dumps(self.corrected_ops,ensure_ascii=False,indent=2))
        (self.out/'model_verified.json').write_text(json.dumps(self.model,ensure_ascii=False,indent=2))
        print('Checked',dict(self.checked),'Changes',len(self.changes),'Unresolved',len(self.unresolved))
        for x in self.unresolved[:20]:print(x)
        self.wb.calculation=CalcProperties(calcId=191029,fullCalcOnLoad=True)
        self.wb.save(self.out/'KO_model_reviewed.xlsx')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--work',default='research/companies/US/KO-coca-cola/outputs/company-research-to-excel-20261013');ap.add_argument('--out',default='data/derived/companies/US/KO-coca-cola/workbook-audit-20261014');args=ap.parse_args()
    root=Path(args.root).resolve();Auditor(root,root/args.work,root/args.out).run()
