#!/usr/bin/env python3
"""Independent arithmetic/IF/IFERROR evaluator for disclosure workbooks.
Uses lazy Excel branch semantics, validates quoted cross-sheet references, and
compares formula-linked source inputs with source-cell-audit.json when supplied.
"""
import argparse,ast,json,operator,re
from collections import Counter
from pathlib import Path
from openpyxl import load_workbook
REF=re.compile(r"(?:(?:'([^']+)'|([A-Za-z_][A-Za-z_0-9]*))!)?\$?([A-Z]{1,3})\$?(\d+)")
OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Pow:operator.pow}
class Evaluator:
 def __init__(self,w):self.w=w;self.cache={};self.active=set()
 def cell(self,s,c):
  key=(s,c)
  if key in self.cache:return self.cache[key]
  if key in self.active:raise ValueError('circular reference')
  self.active.add(key)
  try:
   v=self.w[s][c].value
   if isinstance(v,str) and v.startswith('='):v=self.expr(s,v[1:])
   self.cache[key]=v;return v
  finally:self.active.remove(key)
 def expr(self,s,f):
  f=f.strip()
  # Replace innermost function groups, with lazy outer IFERROR/IF branches.
  m=re.fullmatch(r'(IFERROR|IF|N)\((.*)\)',f)
  if m:
   body=m[2];args=[];depth=0;quoted=False;start=0
   for i,c in enumerate(body):
    if c=='"':quoted=not quoted
    if not quoted:
     if c=='(':depth+=1
     if c==')':depth-=1
     if c==',' and depth==0:args.append(body[start:i]);start=i+1
   args.append(body[start:])
   if m[1]=='IFERROR':
    try:return self.expr(s,args[0])
    except (ZeroDivisionError,ValueError,KeyError,TypeError):return self.expr(s,args[1])
   if m[1]=='IF':return self.expr(s,args[1] if self.expr(s,args[0]) else args[2])
   x=self.expr(s,args[0]);return x if isinstance(x,(int,float)) else 0
  if f=='""':return ''
  # N(ref) in a condition; no other nested calls exist in this workbook.
  f=re.sub(r'N\(([^()]+)\)',lambda m:repr(self.expr(s,'N('+m[1]+')')),f)
  def sub(m):
   x=self.cell(m[1] or m[2] or s,m[3]+m[4])
   if x is None or x=='':return '0'
   if not isinstance(x,(int,float)):raise ValueError('text in numeric expression '+str(x))
   return repr(x)
  f=REF.sub(sub,f).replace('^','**')
  f=re.sub(r'(?<![<>=!])=(?!=)','==',f)
  tree=ast.parse(f,mode='eval')
  def ev(n):
   if isinstance(n,ast.Expression):return ev(n.body)
   if isinstance(n,ast.Constant) and isinstance(n.value,(int,float,str)):return n.value
   if isinstance(n,ast.BinOp) and type(n.op) in OPS:return OPS[type(n.op)](ev(n.left),ev(n.right))
   if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.USub,ast.UAdd)):return -ev(n.operand) if isinstance(n.op,ast.USub) else ev(n.operand)
   if isinstance(n,ast.Compare) and len(n.ops)==1 and isinstance(n.ops[0],ast.Eq):return ev(n.left)==ev(n.comparators[0])
   raise ValueError('unsupported formula '+f)
  return ev(tree)

def audit(path,source=None):
 w=load_workbook(path);ev=Evaluator(w);res={'formulas':0,'errors':[],'checks':[],'source_formula_mismatches':[],'cached_values':{}}
 for ws in w:
  for row in ws:
   for c in row:
    if c.data_type!='f' or c.value.startswith('=HYPERLINK'):continue
    res['formulas']+=1
    try:
     v=ev.cell(ws.title,c.coordinate);res['cached_values'][ws.title+'!'+c.coordinate]=v
     lab=ws.cell(c.row,1).value or ''
     if ('Check' in lab or 'check:' in lab) and not lab.startswith('Info'):
      tol=.015 if 'factors' in lab or 'rounding' in lab else .5
      if isinstance(v,(int,float)) and abs(v)>tol:res['checks'].append({'sheet':ws.title,'cell':c.coordinate,'label':lab,'value':v,'tolerance':tol})
    except Exception as e:res['errors'].append({'sheet':ws.title,'cell':c.coordinate,'formula':c.value,'error':str(e)})
 if source:
  for x in json.loads(Path(source).read_text())['provenance']:
   c=w[x['sheet']][x['cell']]
   if c.data_type!='f':continue
   try:v=ev.cell(x['sheet'],x['cell'])
   except Exception:continue
   if isinstance(x['expected'],(int,float)) and abs(v-x['expected'])>1e-8:res['source_formula_mismatches'].append({**x,'formula_value':v})
 return res
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('workbook');p.add_argument('--source');p.add_argument('--output');a=p.parse_args();r=audit(a.workbook,a.source)
 if a.output:Path(a.output).write_text(json.dumps(r,ensure_ascii=False,indent=2))
 print({k:v for k,v in r.items() if k!='cached_values'})
