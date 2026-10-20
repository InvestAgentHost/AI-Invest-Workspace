"""Safe historical formula wiring and independent arithmetic recomputation.

This layer checks model logic only. It never substitutes for source_audit or an
Excel-compatible engine recalculating the delivered workbook.
"""
from __future__ import annotations

import ast
import math

from openpyxl.utils import get_column_letter

from model_contract import (DATA_START_COL, PeriodIndex, build_registry, cell_expr,
                            evaluate_tree, expression_tree, is_number, resolve_token, display_value)


class Layout(PeriodIndex):
    def __init__(self, periods):
        super().__init__(periods)
        self.col_of = {}
        c = DATA_START_COL
        for p in self.annual:
            self.col_of[p["label"]] = c
            c += 1
        # One unfilled separator, only when both blocks exist.
        n = int(periods.get("scrap_cols", 1)) if self.annual and self.quarterly else 0
        if n not in (0, 1):
            raise ValueError("Historical style permits at most one annual/quarter separator")
        self.scrap_cols = list(range(c, c + n))
        c += n
        for p in self.quarterly:
            self.col_of[p["label"]] = c
            c += 1
        self.last_col = max(DATA_START_COL, c - 1)
        self.all_labels = self.labels


class FormulaPlan:
    def __init__(self, model):
        self.model, self.layout = model, Layout(model["periods"])
        self.registry, self.sheet_names, self.block_rows = build_registry(model)
        self.rows = {}
        for sheet in model["sheets"]:
            if sheet.get("kind") == "statement":
                for block in sheet.get("blocks", []):
                    for row in block.get("rows", []):
                        if row.get("id"): self.rows[sheet["short"], row["id"]] = row

    def reference(self, short, rid, label, current):
        if label is None: return None
        if (short, rid) not in self.rows:
            raise ValueError(f"Unknown metric {short}:{rid}")
        addr = f"{get_column_letter(self.layout.col_of[label])}{self.registry[short][rid]}"
        name = self.sheet_names[short].replace("'", "''")
        return addr if short == current else f"'{name}'!{addr}"

    def target(self, token, current, label):
        short, rid = token.split(":", 1) if ":" in token else (current, token)
        return short, rid, label

    def expression(self, expr, current, label):
        tree, tokens = expression_tree(expr)
        refs = [self.reference(*resolve_token(t, current, label, self.layout), current) for t in tokens]
        if any(ref is None for ref in refs):
            return None
        divisors = []
        def render(node):
            if isinstance(node, ast.Expression): return render(node.body)
            if isinstance(node, ast.Constant): return str(node.value)
            if isinstance(node, ast.Name): return refs[int(node.id[1:])]
            if isinstance(node, ast.UnaryOp):
                return f"({'-' if isinstance(node.op, ast.USub) else '+'}{render(node.operand)})"
            left, right = render(node.left), render(node.right)
            ops = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.Pow: "^"}
            if isinstance(node.op, ast.Div): divisors.append(right)
            return f"({left}{ops[type(node.op)]}{right})"
        body = render(tree)
        # Guard inner denominators before expressions which depend on them.
        for denominator in reversed(divisors):
            body = f'IF({denominator}=0,"",{body})'
        if refs:
            body = f'IF(COUNT({",".join(refs)})={len(refs)},{body},"")'
        return "=" + body

    def cell_value(self, short, row, label):
        if not self.layout.in_span(row, label): return None
        kind = row.get("type", "input")
        expr = cell_expr(row, label, self.layout)
        if expr:
            return self.expression(expr, short, label)
        if kind == "input":
            value = row.get("values", {}).get(label)
            return display_value(value)
        if kind in {"note", "spacer"}: return None
        if kind == "subtotal":
            refs = [self.reference(short, rid, label, short) for rid in row["children"]]
            return f'=IF(COUNT({",".join(refs)})={len(refs)},SUM({",".join(refs)}),"")'
        if kind == "link":
            ref = self.reference(*self.target(row["ref"], short, label), short)
            return f'=IF(COUNT({ref})=1,{ref},"")'
        if kind.startswith("growth_"):
            prior = self.layout.prior(label, "yoy" if kind == "growth_yoy" else "qoq")
            if prior is None: return None
            cur = self.reference(*self.target(row["of"], short, label), short)
            prev = self.reference(*self.target(row["of"], short, prior), short)
            # Growth on a zero/negative comparison base is not an ordinary rate.
            return f'=IF(COUNT({cur},{prev})=2,IF({prev}>0,{cur}/{prev}-1,"n.m."),"")'
        raise ValueError(f"Missing formula for {short}:{row.get('id')}/{label}")


class Evaluator:
    def __init__(self, model):
        self.plan = FormulaPlan(model)
        self.index, self.rows = self.plan.layout, self.plan.rows
        self.cache, self.issues = {}, []

    def value(self, short, rid, label, stack=()):
        key = short, rid, label
        if key in self.cache: return self.cache[key]
        if key in stack: raise ValueError(f"Circular model reference: {key}")
        row = self.rows[short, rid]
        if label is None or not self.index.in_span(row, label): return None
        stack = stack + (key,)
        kind, result = row.get("type", "input"), None
        expr = cell_expr(row, label, self.index)
        if expr:
            tree, tokens = expression_tree(expr)
            vals = [self.value(*resolve_token(t, short, label, self.index), stack) for t in tokens]
            if all(is_number(v) for v in vals):
                try:
                    result = evaluate_tree(tree, {f"v{i}": v for i, v in enumerate(vals)})
                except (ArithmeticError, ValueError) as exc:
                    self.issues.append(f"{key}: {exc}")
        elif kind == "input":
            result = row.get("values", {}).get(label)
        elif kind == "subtotal":
            vals = [self.value(short, child, label, stack) for child in row["children"]]
            result = sum(vals) if vals and all(is_number(v) for v in vals) else None
        elif kind == "link":
            result = self.value(*self.plan.target(row["ref"], short, label), stack)
        elif kind.startswith("growth_"):
            prior = self.index.prior(label, "yoy" if kind == "growth_yoy" else "qoq")
            if prior is not None:
                a = self.value(*self.plan.target(row["of"], short, label), stack)
                b = self.value(*self.plan.target(row["of"], short, prior), stack)
                if is_number(a) and is_number(b) and b > 0:
                    result = a / b - 1
        if result is not None and not is_number(result): result = None
        if isinstance(result, complex) or result is not None and not math.isfinite(result):
            raise ValueError(f"Nonfinite formula result: {key}")
        self.cache[key] = result
        return result
