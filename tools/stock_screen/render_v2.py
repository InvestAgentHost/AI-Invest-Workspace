"""Render Markdown and a standalone HTML report from the same v2 results."""
import csv
from html import escape as esc
import json
import os
from pathlib import Path
from urllib.parse import quote

NAMES={'B1':'资本回报','B2':'股东现金转化','B3a':'毛利率变化','B3':'定价权代理','B4':'竞争优势','B5':'收入耐久性',
       'M1':'利益绑定','M2':'激励设计','M3':'资本配置','M4':'目标兑现','M5':'治理与坦诚',
       'I1':'竞争结构','I2':'同行资本回报','I3':'上下游议价','I4':'需求与周期','I5':'替代与监管'}
ORDER=['B1','B2','B3a','B3','B4','B5','M1','M2','M3','M4','M5','I1','I2','I3','I4','I5']


def number(x,n=1):return 'N/A' if x is None else f'{x:,.{n}f}'
def percent(x,n=1):return 'N/A' if x is None else f'{x:.{n}%}'
def score(x):return 'N/A' if x is None else str(x) if isinstance(x,int) else f'{x:.1f}'
def stage(c):return '通过'if c['stage_1']is True else'未通过'if c['stage_1']is False else'未定'


def render(root,cfg):
    folder=root/cfg['output_dir'];read=lambda name:json.loads((folder/name).read_text())
    result=read('scoring-results.json');cards=read('cards.json');inputs={c['company_id']:c for c in read('scoring-input.json')['companies']}
    audit=read('completion-audit.json');scenarios=read('sensitivity.json')
    htmlpath=root/cfg['html_path'];mdpath=root/cfg['report_path'];htmlpath.parent.mkdir(parents=True,exist_ok=True)
    mdpath.parent.mkdir(parents=True,exist_ok=True)
    def href(path):return quote(os.path.relpath(root/path,htmlpath.parent),safe='/')
    def source_links(record):
        seen=set();links=[]
        for s in record['sources']:
            key=s['local_path']
            if key in seen:continue
            seen.add(key)
            if len(links)<4:
                links.append(f'<a href="{esc(s["url"],quote=True)}" target="_blank" rel="noopener">原文{len(links)+1}</a> <a class="muted" href="{href(key)}" target="_blank">缓存</a>')
        extra=f'；另{len(seen)-4}份见证据台账'if len(seen)>4 else''
        return ' · '.join(links)+extra
    top=[c['company_id'].split('/')[1]for c in result['companies']if c['status']=='research_now']
    cover=result['coverage']
    common_intro=(f"截至{cfg['as_of']}，价格日{cfg['price_date']}。美股上市饮料发行人按总市值≥5亿美元筛选，共{result['count']}家；"
                  '含酒类、装瓶商、咖啡/茶制造及相关综合集团，ADR按发行人去重。')
    limits=(f"23/23家公司已有B、M、I及综合均分。368个评分位置中{cover['numerically_scored']}个有数值、{cover['reviewed_na']}个保留N/A，"
            f"其中包括指引序列覆盖、非现金SBC及同行数量限制；不能把它们称为全部事实已完整。"
            'KDP、CELH、PRMB采用前身/混合历史暂定；AKO.B采用现金转化上界情景，B及均分均为暂定上界。')
    priority=(f"本版框架的优先研究对象为{'、'.join(top)}。两者历史P/E有效窗口均不足5年，已列供应商forward同业对照；"
              '低分位不证明绝对便宜，也不构成交易建议。')
    revisions=[
        ('补全中间档位','B3a、M3股数/减值、M4达成率、I4增长/周期均有明确端点，标为本次方法补全。'),
        ('资本与现金口径','B1按期末经营资本，全窗口非正分母改含商誉并封顶；B2明确改成扣SBC的股东FCF/持续经营净利润。'),
        ('同业与缺项','B4/I2统一含商誉回报；不足三家不凑数。缺项仍N/A，自动优先另须通过缺项均取1分的压力检查。'),
        ('指引与现任CEO',f"配对{audit['guidance_pairs']}个年度的首次目标/实际值，另DEO正式撤回中期指引为M4=1。BRBR现任CEO实际归属持股0，M1=1，三年相对TSR激励按修订M2=3。"),
        ('重要性与短历史','KDP非财务SEC事项由旧版机械M5=1修订为3；CELH财务报告执法、KOF/FMX持续控制缺陷仍为1。重组短历史不冒充十年记录。'),
        ('上下界而非填空','COKE B2保持N/A，但B1=5、B3a=5时任何B2∈[1,5]都通过Stage1；AKO.B B2=3仅为可证明评分上界，1—3敏感性与暂定资格同时保留。')]
    methods=("B/M/I各五项等权，至少四项，half-up一位小数；综合均分为三维已显示分数的平均。"
             "Stage1用B1、B2、B3a；质量要求B≥3.5、M≥3、I≥3。B1/M5经核验为1先淘汰；重组与上界情景不得自动优先。"
             "B3b纯价格/成本证据未闭合，B3按毛利率变化B3a回退。I4没有匹配的未来五年需求预测，使用有数据的周期代理、同行上限3/单家上限2；不能据此声称行业未来高增长。"
             "实际财务窗口为3—5个完整财年（CCEP4年，PRMB混合4年），并非十年财务质量验证。")
    data_links=[('规则说明','.github/skills/stock-initial-screen/references/screen-v2.md'),('计算明细',cfg['output_dir']+'/calculations.json'),
                ('输入与逐项状态',cfg['output_dir']+'/scoring-input.json'),('唯一评分结果',cfg['output_dir']+'/scoring-results.json'),
                ('证据台账',cfg['output_dir']+'/evidence-ledger.jsonl'),('来源哈希清单',cfg['output_dir']+'/source-manifest.json'),
                ('验收记录',cfg['output_dir']+'/completion-audit.json'),('完整修订前诊断','research/screens/2026-10-20-us-beverages-ge500m-diagnosis.md')]
    # Markdown is a durable full report, not an empty pointer to the HTML.
    md=['# 美股饮料公司初筛｜screen-v2', '', common_intro,'',priority,'',limits,'',
        '## 总表','', '|证券|市值 $bn|B|M|I|均分|Stage1|TTM P/E|自身分位|Forward P/E|分类|',
        '|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---|']
    rows=[]
    for c in result['companies']:
        t=c['company_id'].split('/')[1];card=cards[t];p=card['price'];initial=inputs[c['company_id']]
        star='*'if c['comparability']=='provisional'else''
        values=[t,number(card['issuer']['market_cap_usd']/1e9,2),*[number(c['factors'][x]['score'])+star for x in'BMI'],number(c['average'],2)+star,
                stage(c),number(p['trailing_pe'],2),'N/A'if p['percentile']is None else number(p['percentile'])+'%',number(p['forward_pe'],2),c['label']]
        md.append('|'+ '|'.join(values)+'|')
        cls='priority'if c['status']=='research_now'else'provisional'if c['comparability']=='provisional'else''
        row=f'<tr class="{cls}" data-ticker="{t}" data-status="{c["status"]}"><td><a class="ticker" href="#{t}">{t}</a><small>{esc(card["profile"]["group"])}</small></td>'
        for v in values[1:]:row+=f'<td>{esc(v)}</td>'
        row+='</tr>';rows.append(row)
    md += ['', '*带星号为暂定/混合历史；AKO.B商业分与均分为上界情景。N/A未填默认分。总表分类按门槛排序，非按平均分简单排序。',
           '', '## 修订及方法边界','',methods,'']
    md += [f'- **{a}**：{b}'for a,b in revisions]
    md += ['','## 方法敏感性','',
           '若取消相对ROIC的B4上限，PEP将由“便宜但质量未达标”升为“优先研究”，KO将质量通过。品牌外包与制造、收购与自建品牌仍影响横向资本比较，因此这两家须带方法敏感性阅读。',
           '把所有增长未验证的I4置1，COCO、BRBR的I均为3.0，仍达质量门槛。B1统一改含商誉资本的独立情景也一并保存；TAP的高扣商誉回报不宜直接当作高经济回报。',
           'AKO.B若B2由上界3降至1，商业维度由3.5降至3.0、均分约3.17，Stage1也不再通过，始终保持暂定。',
           '', '## 公司评分与计算','']
    sections=[]
    for c in result['companies']:
        t=c['company_id'].split('/')[1];card=cards[t];p=card['price'];q=card['calculations'];e={r['metric_id']:r for r in card['evidence']}
        md += [f"### {t}｜{card['issuer']['name']}",'',f"{c['label']}；B/M/I={c['factors']['B']['score']}/{c['factors']['M']['score']}/{c['factors']['I']['score']}；均分{number(c['average'],2)}。财务FY{q['window'][0]}—{q['window'][1]}，当前边界完整年{card['perimeter_years']}。",'',
               '**主要反证：**'+card['profile']['risk'],'', '|指标|分数|依据与限制|来源|','|---|---:|---|---|']
        evidence_html=[]
        for k in ORDER:
            rec=e[k];mark='†'if rec['review']=='provisional'else''
            links=[]
            for s in rec['sources'][:2]:links.append(f"[原文]({s['url']})；`{s['local_path']}`")
            md.append('|'+ '|'.join([k+' '+NAMES[k],score(rec['score'])+mark,rec['claim']+' '+rec['limitations'],'；'.join(links)])+'|')
            state={'evidence_limited':'有限覆盖 N/A','not_applicable':'不适用','provisional':'暂定情景','reviewed':'已评分'}.get(rec['review'],rec['review'])
            evidence_html.append(f'<tr><td><strong>{k}</strong><small>{NAMES[k]}</small></td><td class="metric-score">{score(rec["score"])}{mark}</td><td>{esc(rec["claim"])}<small>{esc(rec["limitations"])}</small><small>{state} · {esc(rec["claim_type"])} · 置信度 {rec["confidence"]}</small></td><td class="sources">{source_links(rec)}<small>{esc(rec["locator"])}</small></td></tr>')
        md += ['', '**逐年财务输入**（本币百万，股数百万；财务分子为官方披露/明确构造，余额含供应商标准化值）','',
               '|FY|币种|EBIT|CFO|Capex|SBC|净利润|总权益含暂时性权益|债务/租赁|现金/短投|商誉|其他无形|申报日股数|',
               '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        finrows=[]
        for r in card['financials']:
            vals=[str(r['year']),r['currency']]+[number(r.get(k),2)for k in ['ebit','cfo','capex','sbc','net_income','equity','debt_leases','liquid_assets','goodwill','intangibles','filing_shares']]
            md.append('|'+ '|'.join(vals)+'|');finrows.append('<tr>'+''.join(f'<td>{esc(v)}</td>'for v in vals)+'</tr>')
        ret=q['B1'];cash=q['B2'];alloc=q['M3'];peer=q['peers']
        bridge=[
            'B1：NOPAT=EBIT×(1−税率)；含商誉资本=权益含暂时性权益+债务/租赁−现金/短投；经营资本再扣商誉与其他无形。'
            +f"本轮分母 {ret.get('denominator','不可用')}；经营/替代回报中位数{percent(ret.get('median'))}，最低连续三年平均{percent(ret.get('lowest_three_year_mean'))}，含商誉中位数{percent(ret.get('including_goodwill_median'))}。",
            'B2：Σ(CFO−Capex−非现金SBC加回−融资类现金利息+投资类现金利息收入)/Σ合并持续经营净利润。'
            +f"已知累计CFO {number(cash.get('cfo_sum'),2)}，Capex {number(cash.get('capex_sum'),2)}，扣SBC前FCF {number(cash.get('before_sbc_fcf'),2)}。"
            +f"分子{number(cash.get('fcf_after_sbc'),2)}，利润分母{number(cash.get('profit'),2)}，比率{percent(cash.get('ratio'))}；"
            +f"SBC合计{number(cash.get('sbc'),2)}，融资类利息{number(cash.get('financing_interest_paid'),2)}，投资类利息收入{number(cash.get('investing_interest_received'),2)}。"
            +(f"未知SBC时的比率上界{percent(cash.get('ratio_upper_bound'))}。"if cash.get('missing_sbc_years')else''),
            f"M3：含商誉ROIC{percent(alloc.get('roic_including_goodwill'))}→{score(alloc.get('roic_subscore'))}分；"
            +f"复权申报日股数变化{percent(alloc.get('share_change'))}→{score(alloc.get('share_subscore'))}分；"
            +f"减值子分{score(alloc.get('impairment_subscore'))}；有效子项平均向下取整={score(alloc.get('score'))}（短历史另封顶）。",
            f"B4/I2：同行{', '.join(peer['tickers'])or'无足够同模型同行'}；含商誉回报中位数{percent(peer['median'])}；"
            +f"本公司/同行={number(peer['own_to_peer'],2)}；B4上限{peer['B4_cap']}。"]
        if q.get('impairment_evidence'):
            imp=q['impairment_evidence'];bridge.append(f"已核验部分减值下界{number(imp['amount'],2)}/期初期末商誉无形平均{number(imp['denominator'],2)}={percent(imp['ratio_lower_bound'],2)}，已超过30%，故减值子项可确定为1；不是完整累计额。")
        notes=list(dict.fromkeys(note for r in card['financials']for note in r['source_notes']))
        bridge.extend(notes)
        md+=['','**计算桥接及特殊口径**','']+['- '+x for x in bridge]+['']
        bridge_html='<h4>计算桥接及特殊口径</h4><div class="method">'+''.join('<p>'+esc(s)+'</p>'for s in bridge)+'</div>'
        g=q.get('M4');gtable=''
        if g:
            md += ['','**首次全年指引配对**','', '|FY|同口径指标|首次范围|中点|实际|达成|首次/实际来源|','|---|---|---:|---:|---:|---|---|']
            grows=[]
            for r in g['records']:
                vals=[str(r['fiscal_year']),r['metric'],f"{r['target_low']}—{r['target_high']}",number(r['target_midpoint'],2),number(r['actual'],2),'是'if r['hit']else'否']
                md.append('|'+ '|'.join(vals+[f"[首次]({r['first_target_source']['url']}) / [实际]({r['actual_source']['url']})；{r['interpretation']}"])+'|')
                grows.append('<tr>'+''.join(f'<td>{esc(v)}</td>'for v in vals)+f'<td><a href="{r["first_target_source"]["url"]}">首次 {r["first_target_source"]["published_on"]}</a> / <a href="{r["actual_source"]["url"]}">实际 {r["actual_source"]["published_on"]}</a><small>{esc(r["interpretation"])}</small></td></tr>')
            gtable='<h4>首次全年指引与实际</h4><div class="scroll"><table class="compact"><thead><tr>'+''.join('<th>'+x+'</th>'for x in['FY','同口径指标','首次范围','中点','实际','达成','来源与解释'])+'</tr></thead><tbody>'+''.join(grows)+'</tbody></table></div>'
        v=card['valuation'];chart=''
        if p['percentile']is not None:
            maximum=max(v['p90'],p['trailing_pe'])*1.15
            def x(val):return 55+650*val/maximum
            points=''.join(f'<line x1="{x(v[k]):.1f}" x2="{x(v[k]):.1f}" y1="40" y2="65" stroke="#527c6a"/><text x="{x(v[k]):.1f}" y="88" text-anchor="middle">{label} {v[k]:.1f}×</text>'for k,label in [('p10','P10'),('p50','P50'),('p90','P90')])
            chart=f'<svg class="pechart" viewBox="0 0 760 100" role="img" aria-label="{t}自身P/E分布参考点"><line x1="55" x2="705" y1="52" y2="52" stroke="#cbd8ce" stroke-width="6"/>{points}<circle cx="{x(p["trailing_pe"]):.1f}" cy="52" r="7" fill="#bc652a"/><text x="{x(p["trailing_pe"]):.1f}" y="24" text-anchor="middle" fill="#9a4d1f">当前 {p["trailing_pe"]:.2f}×</text></svg>'
            valtext=f"有效历史 {v['start']}—{v['end']}，{v['effective_days']}个交易日、{p['history_years']:.2f}年；当前经验分位 {p['percentile']:.1f}%。每股GAAP收益取当时已披露值，正P/E完整有效日统计，图只展示P10/P50/P90参考点。"
        else:
            valtext='自身历史分位未建立/停用：'+p['limitation']+'。TTM与forward仅为当前供应商快照，不能在历史轴上伪造分位。'
        if p['history_years']is not None and p['history_years']<5:
            peertext='；'.join(f"{r['ticker']} {r['forward_pe']:.2f}×"for r in p['forward_peers'])
            valtext+=' 短历史：此为可重建EPS窗口，不一定覆盖上市全期。Forward同经济模型对照：'+peertext+'。口径为供应商预测，品类/增长差异仍大，不能直接等同合理倍数。'
        md += ['', '**估值：**'+valtext,'','**后续核实：**','']+[f'{i+1}. {s}'for i,s in enumerate(card['profile']['questions'])]+['']
        bound=''
        if t=='AKO.B':bound='<p class="warning"><strong>上界情景，非已证实现金转化：</strong>B2=3是扣SBC前的最高可支持评分，范围1—3；B=3.5及均分3.33为暂定上界。原始SBC未知，未录为0。B2=1时B=3.0、Stage1失败。</p>'
        if t=='COKE':bound='<p class="note">B2仍为N/A。Stage1最差均值=(5+1+5)/3=3.67，最佳5.00；所有合法B2都通过，因此有数学依据判“通过”。</p>'
        gate=(f"Stage1 {stage(c)}；质量均分{'通过'if c['quality_pass']else'未达标'}；未评分项均取1分的压力结果 B/M/I="+
              '/'.join(number(c['quality_floor'][p])for p in'BMI')+f"，{'仍通过'if c['quality_robust_to_unscored']else'不稳健/已未通过'}。")
        details=f'<details class="company" id="{t}"><summary><span><b>{t}</b> {esc(card["issuer"]["name"])}</span><span class="badge">{esc(c["label"])}</span><span>B {c["factors"]["B"]["score"]:.1f} · M {c["factors"]["M"]["score"]:.1f} · I {c["factors"]["I"]["score"]:.1f}</span></summary><div class="body"><p>{esc(gate)}</p><p>财务窗口 FY{q["window"][0]}—{q["window"][1]}，当前边界 {card["perimeter_years"]}个完整年度。税率 {q["tax_rate"]:.2%}；{esc(q["tax_basis"])}</p>{bound}<p class="risk"><b>主要反证：</b>{esc(card["profile"]["risk"])}</p><div class="scroll"><table class="evidence"><thead><tr><th>指标</th><th>分数</th><th>依据、口径及局限</th><th>证据</th></tr></thead><tbody>'+''.join(evidence_html)+'</tbody></table></div><h4>逐年财务输入</h4><p class="muted">本币百万，股数百万。权益含暂时性/可赎回权益，债务已含租赁。SBC的N/A不代表0。</p><div class="scroll"><table class="compact"><thead><tr>'+''.join('<th>'+x+'</th>'for x in['FY','币种','EBIT','CFO','Capex','SBC','净利润','权益','债务/租赁','现金/短投','商誉','其他无形','申报日股数'])+'</tr></thead><tbody>'+''.join(finrows)+'</tbody></table></div>'+gtable+'<h4>估值及历史覆盖</h4>'+chart+f'<p>{esc(valtext)}</p><p>TTM {number(p["trailing_pe"],2)}×；Forward {number(p["forward_pe"],2)}×。<a href="{href(cfg["baseline_source_dir"]+"/"+t+"-snapshot.html")}">价格/估值快照</a></p><h4>继续研究时优先核实</h4><ol>'+''.join('<li>'+esc(s)+'</li>'for s in card['profile']['questions'])+'</ol><p><a href="#ranking">返回总表</a> · <a href="'+href(cfg['output_dir']+'/calculations.json')+'">完整数值桥接</a></p></div></details>'
        details=details.replace('<h4>逐年财务输入</h4>',bridge_html+'<h4>逐年财务输入</h4>')
        sections.append(details)
    md += ['## 来源、复算与验收','',f"验收：{audit['delivery_status']}；三维/均分23家；Stage1均可判定；历史PE {audit['pe_histories']}家；{audit['guidance_pairs']}组年度配对；{audit['source_files']}个证据/价格文件有哈希。验收检查结构和数值链，不替代对全部原文的独立财务审计。",'']
    for label,path in data_links:md.append(f'- {label}：`{path}`')
    md += ['', '复算命令：','', '```bash', '.venv/bin/python tools/stock_screen/run_v2.py '+str(Path(cfg['output_dir']).relative_to('data/derived')).replace('screens/','data/curated/screens/',1)+'/run.json','```','']
    # The configuration location is a stable path, independent of the derived folder.
    md[-3]='.venv/bin/python tools/stock_screen/run_v2.py data/curated/screens/'+folder.name+'/run.json'
    mdpath.write_text('\n'.join(md))
    sensitivity_rows=[]
    mainmap={c['company_id']:c for c in result['companies']}
    for key,title in [('no_relative_moat_cap','取消相对ROIC上限'),('growth_unverified_floor1','I4未验证增长按1'),('B1_including_goodwill','B1统一含商誉资本'),('akob_sbc_worst','AKO.B现金转化最差'),('customer_bound_upper','客户浓度区间上端')]:
        changed=[f"{c['company_id'].split('/')[1]}：{mainmap[c['company_id']]['label']} → {c['label']}"for c in scenarios[key]['companies']if c['status']!=mainmap[c['company_id']]['status']]
        sensitivity_rows.append(f'<tr><td>{title}</td><td>{esc("；".join(changed)or"未改变正式分类；分数详见情景文件。")}</td></tr>')
    html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>美股饮料初筛 · screen-v2</title><style>
    :root{--ink:#183b32;--muted:#5c7167;--line:#d7e2d9;--green:#17664e;--bg:#f4f7f2}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.7 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}main{max-width:1460px;margin:auto;padding:34px 28px 80px}a{color:var(--green);text-underline-offset:3px}h1{font-size:32px;line-height:1.3;margin:12px 0}h2{font-size:22px;margin:30px 0 13px}h4{font-size:17px;margin:24px 0 10px}p{margin:10px 0}.eyebrow{font-size:12px;letter-spacing:2px;color:var(--muted)}.lead{max-width:1120px}.hero{border-bottom:1px solid var(--line);padding-bottom:20px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:23px 0}.stat{background:white;border:1px solid var(--line);border-radius:10px;padding:14px 20px}.stat b{font-size:28px;display:block;line-height:1.3}.stat small{color:var(--muted)}.note,.warning{padding:14px 18px;border-radius:8px;background:#e5eee5;border-left:4px solid #6a947d}.warning{background:#fff3df;border-color:#bc8c40}.muted,small{color:var(--muted)}small{display:block;font-size:12px;line-height:1.6;margin-top:4px}.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:white}table{width:100%;border-collapse:collapse;font-size:13px;line-height:1.55}th{background:#e8efe7;text-align:left;font-weight:650;white-space:nowrap}th,td{padding:12px 11px;border-bottom:1px solid #e1e8e1;vertical-align:top}tbody tr:last-child td{border-bottom:0}#ranking td{white-space:nowrap}#ranking td:first-child{min-width:164px}#ranking .ticker{font-weight:700}#ranking tr.priority{background:#edf6e9}#ranking tr.provisional{background:#fff8ec}button{background:white;border:1px solid var(--line);border-radius:6px;color:var(--ink);padding:8px 13px;cursor:pointer;font:inherit}th button{border:0;background:transparent;padding:0;font-size:13px;font-weight:700}input{padding:9px 12px;border:1px solid var(--line);border-radius:6px;font:inherit;width:280px}.toolbar{display:flex;flex-wrap:wrap;gap:10px;margin:13px 0}.badge{display:inline-block;border-radius:20px;background:#e8efe5;padding:3px 10px;font-size:12px}.company{background:white;border:1px solid var(--line);border-radius:10px;margin:13px 0;scroll-margin-top:20px}.company>summary{cursor:pointer;display:flex;gap:18px;align-items:center;justify-content:space-between;padding:17px 20px;font-size:13px}.company>summary b{font-size:18px;margin-right:8px}.company>summary span:first-child{flex:1}.body{padding:0 20px 22px}.evidence td:nth-child(1){width:120px}.evidence td:nth-child(2){width:65px}.evidence td:nth-child(3){min-width:460px}.evidence td:nth-child(4){width:240px}.metric-score{font-size:18px;font-weight:700}.sources{font-size:12px}.compact{font-size:12px}.compact td{white-space:nowrap}.compact td:last-child{white-space:normal;min-width:120px}.risk{border-left:3px solid #bb8e6f;padding:7px 14px;background:#faf5ef}.pechart{max-width:760px;width:100%;font:12px sans-serif}.links{display:flex;gap:16px;flex-wrap:wrap;font-size:13px}.method{background:white;border:1px solid var(--line);border-radius:10px;padding:18px 22px}footer{border-top:1px solid var(--line);margin-top:30px;padding-top:18px;font-size:12px}@media(max-width:800px){main{padding:24px 15px}.stats{grid-template-columns:repeat(2,1fr)}h1{font-size:27px}.company>summary{align-items:flex-start;flex-direction:column;gap:6px}.body{padding:0 12px 18px}}@media print{details{display:block}details>.body{display:block}.toolbar,button{display:none}main{max-width:none;padding:0}.scroll{overflow:visible}.company{break-inside:avoid}table{font-size:9px}}
    </style></head><body><main>'''
    html+=f'<header class="hero"><div class="eyebrow">AI INVEST · FUNDAMENTAL SCREEN · {cfg["as_of"]}</div><h1>美股饮料公司初筛</h1><p class="lead">{esc(common_intro)}</p><p><strong>{esc(priority)}</strong></p><div class="stats"><div class="stat"><b>23 / 23</b><small>三维评分与均分已完成</small></div><div class="stat"><b>{cover["numerically_scored"]} / 368</b><small>单项有数值；另{cover["reviewed_na"]}项N/A</small></div><div class="stat"><b>{audit["guidance_pairs"]}</b><small>首次全年目标/实际配对</small></div><div class="stat"><b>{audit["pe_histories"]}</b><small>可使用的自身P/E历史</small></div></div><p class="note">{esc(limits)}</p><div class="links">'+''.join(f'<a href="{href(path)}">{label}</a>'for label,path in data_links[:7])+f'<a href="{href(cfg["report_path"])}">完整Markdown报告</a></div></header>'
    html+='<h2>评分总表</h2><p class="muted">规则 screen-v2；价格为10月19日收盘。点击证券展开完整评分与证据。*为暂定，AKO.B为上界情景；N/A不以中性分填充。</p><div class="toolbar"><input id="search" placeholder="搜索代码、业务或分类" aria-label="搜索公司"><button id="onlyPriority">只看优先研究</button><button id="showAll">全部23家</button><button id="expand">展开全部公司卡</button></div><div class="scroll"><table id="ranking"><thead><tr>'+''.join(f'<th><button data-sort="{i}">{x}</button></th>'for i,x in enumerate(['证券 / 业务','市值 $bn','B','M','I','均分','Stage1','TTM P/E','自身分位','Forward P/E','正式分类']))+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div><p class="muted">分类先看硬门槛/暂定，再看Stage1、质量和估值；均分高不保证通过。质量待确认表示缺项的最差情景会改变质量结论。Forward为供应商预测，独立于GAAP历史分位。</p>'
    html+='<h2>修订、敏感性与剩余边界</h2><div class="method"><p>'+esc(methods)+'</p><ul>'+''.join(f'<li><b>{a}：</b>{esc(b)}</li>'for a,b in revisions)+'</ul><p>三维评分使用的同行是本次23家中的经济模型分组；品牌制造与外包、地区和税率的差异仍然存在。PEP与KO尤其受相对资本上限影响，须同时看下面的独立情景。</p><div class="scroll"><table><thead><tr><th>独立方法情景</th><th>分类变化</th></tr></thead><tbody>'+''.join(sensitivity_rows)+'</tbody></table></div><p><a href="'+href(cfg['output_dir']+'/sensitivity.json')+'">查看全部情景分数</a>。情景不覆盖主规则。COCO/BRBR在I4=1压力下行业分均3.0，仍通过；它们在所有未评分项取1分时也仍满足质量门槛。</p><p>金融数据原始材料已保存。原报告空白的原因是只完成了局部取数/定性打分，旧引擎只汇总、不计算缺失项目；本次新增规范化、完整定量计算和交付验收。原始文件及旧版结果均保留。</p></div>'
    html+='<h2>23家公司评分、计算与原文证据</h2>'+''.join(sections)
    html+=f'<footer>验收：{esc(audit["delivery_status"])}；源文件{audit["source_files"]}份有哈希，三维结果23家、Stage1判定23家。源文件完整性和数值一致性检查不等于全部事实的独立审计。规则、定性判断、推断和N/A均按单项标注。<p>复算：<code>.venv/bin/python tools/stock_screen/run_v2.py data/curated/screens/{folder.name}/run.json</code></p></footer>'
    html+='''</main><script>
    const rows=[...document.querySelectorAll('#ranking tbody tr')];let priorityOnly=false;
    function filter(){const q=document.getElementById('search').value.trim().toLowerCase();rows.forEach(r=>r.hidden=(priorityOnly&&r.dataset.status!=='research_now')||!r.textContent.toLowerCase().includes(q))}
    document.getElementById('search').addEventListener('input',filter);document.getElementById('onlyPriority').onclick=()=>{priorityOnly=true;filter()};document.getElementById('showAll').onclick=()=>{priorityOnly=false;document.getElementById('search').value='';filter()};
    document.getElementById('expand').onclick=()=>{let all=[...document.querySelectorAll('.company')];let open=all.some(d=>!d.open);all.forEach(d=>d.open=open);document.getElementById('expand').textContent=open?'收起全部公司卡':'展开全部公司卡'};
    let direction={};document.querySelectorAll('[data-sort]').forEach(b=>b.onclick=()=>{const i=Number(b.dataset.sort);direction[i]=-(direction[i]||1);let ordered=[...rows].sort((a,b)=>{let av=a.cells[i].textContent.trim(),bv=b.cells[i].textContent.trim();let an=parseFloat(av.replace('*','')),bn=parseFloat(bv.replace('*',''));return direction[i]*(Number.isFinite(an)&&Number.isFinite(bn)?an-bn:av.localeCompare(bv,'zh'))});ordered.forEach(r=>r.parentNode.appendChild(r))});
    function reveal(){const id=decodeURIComponent(location.hash.slice(1));const el=document.getElementById(id);if(el&&el.classList.contains('company')){el.open=true;el.scrollIntoView({block:'start'})}}window.addEventListener('hashchange',reveal);reveal();
    </script></body></html>'''
    htmlpath.write_text(html)
    # The visible table is the canonical sorted results, not a second computation.
    return {'html_path':str(htmlpath.relative_to(root)),'markdown_path':str(mdpath.relative_to(root)),
            'table_rows':len(rows),'company_cards':len(sections),'metric_rows':len(cards)*len(ORDER),
            'results_sha256':__import__('hashlib').sha256((folder/'scoring-results.json').read_bytes()).hexdigest()}
