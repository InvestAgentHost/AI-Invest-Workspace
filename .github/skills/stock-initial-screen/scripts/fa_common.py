"""Shared helpers for the FocusAlpha converters (FocusAlpha-only version, v4.11.4)."""
import datetime as dt, json, re

def load(path):
    """A saved FocusAlpha tool output (the JSON text, possibly with text around it)."""
    t = open(path).read(); i = t.find('{'); j = t.rfind('}')
    return json.loads(t[i:j + 1])

def rows_of(paths, *names):
    """All rows under the given list names (e.g. 'income_statements', 'data') across saved outputs."""
    out = []
    for p in paths:
        d = load(p); f = d.get('financials', d)
        for n in names:
            out += f.get(n) or []
    return out

D = lambda s: dt.date.fromisoformat(str(s)[:10])

def fy_name(fy_end):
    """The engine's (and Fiscal.ai's) name for a fiscal year ending on fy_end: a year ending January-May is named for the year before."""
    return fy_end.year if fy_end.month >= 6 else fy_end.year - 1

def fy_of_quarter(q_end, fye_month):
    """Fiscal year (engine naming) of a quarter that ends on q_end, given the month the fiscal year ends."""
    y = q_end.year if q_end.month <= fye_month else q_end.year + 1
    return fy_name(dt.date(y, fye_month, 28))

def imp_fields(r):
    return [k for k in (r or {}) if re.search(r'impairment', k) and re.search(r'goodwill|intangible', k) and r[k] is not None]

M = lambda v: None if v is None else round(v / 1e6, 1)
A = lambda v: None if v is None else round(abs(v) / 1e6, 1)
