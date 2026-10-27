#!/usr/bin/env python3
"""Parse a padded Fiscal.ai output file and save the JSON.
python3 save_raw.py <tool-results file> <RUN_DIR/raw/name.json>   (merges into the target if it exists)"""
import json, sys, os
src, dst = sys.argv[1], sys.argv[2]
raw = open(src).read()
i = raw.find('{'); j = raw.find('\n//')
txt = raw[i:j if j > 0 else None]
if txt.startswith('{"result"'): txt = json.loads(raw)['result']; txt = txt[:txt.find('\n//')] if '\n//' in txt else txt
d = json.loads(txt[:txt.rfind('}') + 1])
old = json.load(open(dst)) if os.path.exists(dst) else {}
old.update(d)
os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
json.dump(old, open(dst, 'w'))
for k, v in d.items():
    if not isinstance(v, dict): print(k, type(v)); continue
    if 'err' in v: print(k, 'ERROR', v['err'])
    elif 'rows' in v: print(k, 'FY' + str(v['L']), v.get('cur'), len(v['rows']), 'rows | am:', v.get('amSrc', '')[:50], '| imp:', v.get('impSrc', '')[:50])
    elif 'ebitda' in v: print(k, 'EV/EBIT days', len(v['ebit']['d'].split(',')) if v['ebit']['d'] else 0, 'to', v['ebit']['d'][-6:], '| EV/EBITDA days', len(v['ebitda']['d'].split(',')) if v['ebitda']['d'] else 0, 'to', v['ebitda']['d'][-6:], '| EV to', v['tev']['d'][-6:], '| price days', len(v['px']['d'].split(',')) if v['px']['d'] else 0, v.get('pxCur'), v.get('pxListing'))
    elif 'd' in v: print(k, 'P/E days', len(v['d'].split(',')) if v['d'] else 0, '| price', v.get('price'), '| fwd', v.get('fwd'))
    else: print(k, 'FY' + str(v.get('L')), 'n', v.get('n'), 'neg', v.get('neg'), 'opMed', v.get('opMed'))
