#!/usr/bin/env python3
"""Fill a Fiscal.ai .js template.  usage: fill_template.py <template.js> <out.js> --keys '["NYSE_PH","NYSE_CR"]' [--tickers '["PH"]'] [--from 2016-10-13]"""
import argparse, json
ap = argparse.ArgumentParser(); ap.add_argument('template'); ap.add_argument('out')
ap.add_argument('--keys'); ap.add_argument('--tickers'); ap.add_argument('--from', dest='frm')
a = ap.parse_args(); s = open(a.template).read()
if a.keys: s = s.replace('__KEYS__', json.dumps(json.loads(a.keys)))
if a.tickers: s = s.replace('__TICKERS__', json.dumps(json.loads(a.tickers)))
if a.frm: s = s.replace('__FROM__', a.frm)
left = [p for p in ('__KEYS__', '__TICKERS__', '__FROM__') if p in s]
if left: raise SystemExit('placeholders left unfilled: ' + ', '.join(left))
open(a.out, 'w').write(s); print(a.out)
