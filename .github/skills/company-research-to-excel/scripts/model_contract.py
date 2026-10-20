"""Shared period, expression and evidence contract for initial historical exports.

This module does not calculate valuations or modify existing workbooks. Source
verification is deliberately implemented separately in source_audit.py.
"""
from __future__ import annotations

import ast
import json
import math
import re
from datetime import date
from pathlib import Path

DATA_START_COL = 3
DATA_START_ROW = 7
HDR_LABEL_ROW = 3
ALLOWED_FORMS = {"10-K", "10-Q", "10-K/A", "10-Q/A"}
MISSING = {"", "unavailable", "not disclosed", "not comparable", "not applicable",
           "not found", "n.a.", "n/a", "n.m.", "n/m", "未披露", "未找到", "不可比", "不适用"}
TOKEN_RE = re.compile(
    r"\{(?:(?P<sheet>[A-Za-z0-9_]+):)?(?P<row>[A-Za-z0-9_]+)"
    r"(?:(?P<offset>@-\d+)|\[(?P<period>[^{}\[\]]+)\])?\}"
)
PROFILE_PATH = Path(__file__).resolve().parent.parent / "assets" / "style-profile.json"


def load_style():
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def display_value(value):
    blank={'','unavailable','not disclosed','not applicable','not found','n.a.','n/a','未披露','未找到','不适用'}
    return None if isinstance(value,str) and value.strip().casefold() in blank else value


def sanitize_sheet_name(name):
    return re.sub(r"[\[\]:*?/\\]", "-", str(name))[:31]


def sheet_role(sheet):
    """Presentation grouping, overridable by the Agent for issuer-specific tabs."""
    explicit=sheet.get('role')
    roles={'contents','operating','income_statement','balance_sheet','cash_flow','metrics','notes'}
    if explicit in roles:return explicit
    short=str(sheet.get('short','')).upper()
    name=str(sheet.get('name','')).casefold()
    if name in {'contents','目录'}:return 'contents'
    if short in {'IS','BS','CF'}:return {'IS':'income_statement','BS':'balance_sheet','CF':'cash_flow'}[short]
    if short=='DM' or name in {'derived metrics','derivate metrics','financial metrics'}:return 'metrics'
    if short in {'SEG','GEO','OPS','KPI','OPM','REV','PRODUCTS'} or any(word in name for word in ('segment','operating metric','kpi','geography','revenue & operations')):return 'operating'
    return 'notes'


def ordered_sheets(sheets):
    priority={role:i for i,role in enumerate(load_style()['sheet_order'])}
    return sorted(sheets,key=lambda s:priority[sheet_role(s)])


def tab_color(sheet):
    role=sheet_role(sheet)
    group='statements' if role in {'income_statement','balance_sheet','cash_flow'} else role
    return sheet.get('tab_color') or load_style()['tab_colors'][group]


def contents_offset(sheet):
    return len(sheet.get("blocks", [])) + 2 if sheet.get("contents") else 0


def build_registry(model):
    registry, names, blocks = {}, {}, {}
    used_names = set()
    for sheet in model.get("sheets", []):
        name = sanitize_sheet_name(sheet["name"])
        if not name or name.casefold() in used_names:
            raise ValueError(f"Duplicate or empty Excel worksheet name: {name}")
        used_names.add(name.casefold())
        if sheet.get("short") and not re.fullmatch(r"[A-Za-z0-9_]+", sheet["short"]):
            raise ValueError(f"Invalid worksheet short code: {sheet['short']}")
        if sheet.get("kind") != "statement":
            continue
        short = sheet["short"]
        if short in registry:
            raise ValueError(f"Duplicate worksheet short code: {short}")
        registry[short], names[short], blocks[short] = {}, name, []
        r = DATA_START_ROW + contents_offset(sheet)
        for block in sheet.get("blocks", []):
            blocks[short].append(r)
            r += 1 + bool(block.get("note"))
            for row in block.get("rows", []):
                rid = row.get("id")
                if rid:
                    if not re.fullmatch(r"[A-Za-z0-9_]+", rid):
                        raise ValueError(f"Invalid metric ID: {short}:{rid}")
                    if rid in registry[short]:
                        raise ValueError(f"Duplicate metric ID: {short}:{rid}")
                    registry[short][rid] = r
                r += 1
            r += 1
    return registry, names, blocks


def fiscal_key(info):
    label = str(info.get("label", ""))
    y, q = info.get("fiscal_year"), info.get("fiscal_quarter")
    annual = re.fullmatch(r"(?:FY|CY)?((?:19|20)\d{2})", label, re.I)
    quarter = re.fullmatch(r"(?:(?:([1-4])Q|Q([1-4]))(?:FY)?((?:19|20)\d{2})|((?:19|20)\d{2})Q([1-4]))", label, re.I)
    if y is None:
        if annual: y = int(annual[1])
        elif quarter: y = int(quarter[3] or quarter[4])
    if q is None and quarter:
        q = int(quarter[1] or quarter[2] or quarter[5])
    if y is None:
        return None
    if q is not None and int(q) not in (1, 2, 3, 4):
        raise ValueError(f"Invalid fiscal quarter for {label}")
    return int(y), int(q) if q is not None else None


class PeriodIndex:
    def __init__(self, periods):
        self.annual = list(periods.get("annual", []))
        self.quarterly = list(periods.get("quarterly", []))
        self.entries = self.annual + self.quarterly
        self.info = {p["label"]: p for p in self.entries}
        self.labels = [p["label"] for p in self.entries]
        if len(self.info) != len(self.entries):
            raise ValueError("Period labels must be unique")
        self.annual_labels = [p["label"] for p in self.annual]
        self.quarterly_labels = [p["label"] for p in self.quarterly]
        self.keys = {}
        for p in self.entries:
            key = fiscal_key(p)
            if key is not None:
                if key in self.keys:
                    raise ValueError(f"Duplicate fiscal period: {key}; use row period_overrides for YTD")
                self.keys[key] = p["label"]

    def prior(self, label, relation="yoy", offset=1):
        info = self.info[label]
        explicit = info.get("comparatives", {}).get(relation) if offset == 1 else None
        if explicit:
            return explicit if explicit in self.info else None
        key = fiscal_key(info)
        if key is None:
            return None
        y, q = key
        if q is None:
            return self.keys.get((y - offset, None)) if relation != "qoq" else None
        if relation == "yoy":
            return self.keys.get((y - offset, q))
        ordinal = y * 4 + q - 1 - offset
        return self.keys.get((ordinal // 4, ordinal % 4 + 1))

    def offset(self, label, count):
        return self.prior(label, "offset", count)

    def in_span(self, row, label):
        if row.get("applicable_periods") is not None:
            return label in row["applicable_periods"]
        key = fiscal_key(self.info[label])
        if key is None:
            return not (row.get("min_label") or row.get("max_label"))
        current = key[0], key[1] or 4
        for field, is_min in [("min_label", True), ("max_label", False)]:
            bound = row.get(field)
            if bound:
                if bound not in self.info:
                    raise ValueError(f"Unknown {field}: {bound}")
                b = fiscal_key(self.info[bound])
                if b is None:
                    raise ValueError(f"No fiscal identity for {field}: {bound}")
                boundary = b[0], b[1] or (1 if is_min else 4)
                if (is_min and current < boundary) or (not is_min and current > boundary):
                    return False
        return True


def period_for(model, row, label):
    info = dict(PeriodIndex(model["periods"]).info[label])
    info.update(row.get("period_overrides", {}).get(label, {}))
    if row.get("time_basis"):
        info["grain"] = row["time_basis"]
    info.setdefault("grain", "annual" if label in [p["label"] for p in model["periods"].get("annual", [])] else "discrete")
    if info["grain"] == "instant":
        info["start"] = None
    return info


def cell_meta(row, label):
    return row.get("cell_meta", {}).get(label, {})


def cell_expr(row, label, index):
    if label in row.get("cell_expr", {}):
        return row["cell_expr"][label]
    if label in row.get("expr_by_period", {}):
        return row["expr_by_period"][label]
    if label in index.quarterly_labels and row.get("expr_q"):
        return row["expr_q"]
    return row.get("expr")


def resolve_token(match, current_short, label, index):
    short = match["sheet"] or current_short
    period = match["period"] or label
    if match["offset"]:
        period = index.offset(label, int(match["offset"][2:]))
    if period not in index.info:
        period = None
    return short, match["row"], period


def expression_tree(expr):
    """Parse arithmetic only; source text can never become executable Python."""
    tokens = list(TOKEN_RE.finditer(expr))
    names = {f"v{i}" for i in range(len(tokens))}
    counter = iter(range(len(tokens)))
    plain = TOKEN_RE.sub(lambda _: f"v{next(counter)}", expr)
    tree = ast.parse(plain, mode="eval")
    allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult,
               ast.Div, ast.Pow, ast.USub, ast.UAdd, ast.Constant, ast.Name, ast.Load)
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise ValueError(f"Unsupported expression syntax: {expr}")
        if isinstance(node, ast.Constant) and not is_number(node.value):
            raise ValueError(f"Only numeric constants are allowed: {expr}")
        if isinstance(node, ast.Name) and node.id not in names:
            raise ValueError(f"Unknown expression name: {node.id}")
    return tree, tokens


def evaluate_tree(node, values):
    if isinstance(node, ast.Expression):
        return evaluate_tree(node.body, values)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return values[node.id]
    if isinstance(node, ast.UnaryOp):
        v = evaluate_tree(node.operand, values)
        return -v if isinstance(node.op, ast.USub) else v
    a, b = evaluate_tree(node.left, values), evaluate_tree(node.right, values)
    if isinstance(node.op, ast.Add): return a + b
    if isinstance(node.op, ast.Sub): return a - b
    if isinstance(node.op, ast.Mult): return a * b
    if isinstance(node.op, ast.Div): return a / b
    if isinstance(node.op, ast.Pow): return a ** b
    raise ValueError("Unsupported arithmetic operator")


def model_issues(model):
    """Structural/data declarations only; final release also requires Agent review."""
    from provenance import provenance_issues
    issues = []
    fail = issues.append
    if model.get("schema") != "historical-research-model.v4":
        fail("Use compact historical-research-model.v4; convert old drafts explicitly")
    if model.get("export_scope") != "historical_10k_10q":
        fail("Only initial historical 10-K/10-Q exports belong to this workflow")
    if model.get("status") not in {"mapped", "reviewed"} or model.get("draft_gaps"):
        fail("Resolve draft_gaps and source mappings before normal build")
    index = PeriodIndex(model.get("periods", {}))
    if not index.labels: fail("No historical periods")
    as_of = model.get("company", {}).get("as_of_date")
    try:
        as_of_date = date.fromisoformat(as_of)
    except (ValueError, TypeError):
        fail("Company as_of_date must be an ISO date")
        as_of_date = None
    for info in index.entries:
        identity = fiscal_key(info)
        if identity is None or (info["label"] in index.quarterly_labels) != (identity[1] is not None):
            fail(f"Invalid fiscal identity: {info['label']}")
        try:
            start, end = date.fromisoformat(info["start"]), date.fromisoformat(info["end"])
            if start > end or as_of_date and end > as_of_date:
                fail(f"Reversed/future historical interval: {info['label']}")
        except (ValueError, TypeError, KeyError):
            fail(f"Exact flow start/end required: {info['label']}")
    for entries in (index.annual, index.quarterly):
        keys = [fiscal_key(p) for p in entries]
        if all(k is not None for k in keys) and keys != sorted(keys, key=lambda k: (k[0], k[1] or 0)):
            fail("Annual/quarter blocks must each run in chronological fiscal order")
    registry, _, _ = build_registry(model)
    for short in model.get("required_statements", ["IS", "BS", "CF"]):
        if short not in registry: fail(f"Required statement missing: {short}")
    issues.extend(provenance_issues(model))
    check_rows = []
    for sheet in model.get("sheets", []):
        if sheet.get("kind") == "table": continue
        if sheet.get("kind") != "statement":
            fail(f"Unsupported sheet kind: {sheet.get('kind')}")
            continue
        short = sheet["short"]
        for block in sheet.get("blocks", []):
            for row in block.get("rows", []):
                rid, kind = row.get("id"), row.get("type", "input")
                if kind in {"spacer", "note"}: continue
                where = f"{short}:{rid}"
                if not rid: fail(f"{short}: metric ID missing")
                if kind not in {"input", "subtotal", "calc", "link", "growth_yoy", "growth_qoq", "check"}:
                    fail(f"{where}: unsupported row type {kind}")
                if kind != "input" and row.get("values"):
                    fail(f"{where}: formula rows cannot contain hardcoded results")
                if any(period_for(model, row, p)["grain"] == "ytd" for p in index.quarterly_labels) and not block.get("note"):
                    fail(f"{where}: YTD data needs a clear section note")
                if kind == "subtotal":
                    if not row.get("children"): fail(f"{where}: subtotal components missing")
                    for child in row.get("children", []):
                        if child not in registry.get(short, {}): fail(f"{where}: unknown subtotal child {child}")
                target = row.get("ref") if kind == "link" else row.get("of") if kind.startswith("growth_") else None
                if kind == "link" or kind.startswith("growth_"):
                    ts, tr = target.split(":", 1) if target and ":" in target else (short, target)
                    if tr not in registry.get(ts, {}): fail(f"{where}: unknown linked/growth metric {target}")
                for label, value in row.get("values", {}).items():
                    if label not in index.info:
                        fail(f"{where}: unknown period {label}")
                        continue
                    if not is_number(value) and value is not None and str(value).lower() not in MISSING:
                        fail(f"{where}/{label}: unresolved value {value!r}")
                    if label in row.get("cell_expr", {}) or label in row.get("expr_by_period", {}):
                        fail(f"{where}/{label}: input and formula cannot own the same cell")
                    if not index.in_span(row, label): fail(f"{where}/{label}: outside declared applicability")
                expressions = {**row.get("cell_expr", {}), **row.get("expr_by_period", {})}
                all_expr = [row.get("expr"), row.get("expr_q"), *expressions.values()]
                if kind in {"calc", "check"} and not any(all_expr): fail(f"{where}: formula missing")
                for label, expr in expressions.items():
                    if label not in index.info:
                        fail(f"{where}: unknown expression period {label}")
                        continue
                    meta = cell_meta(row, label)
                    if meta.get("status") != "calculated":
                        fail(f"{where}/{label}: derived override must be calculated, never a reported estimate")
                    try:
                        _, tokens = expression_tree(expr)
                        refs = [resolve_token(t, short, label, index) for t in tokens]
                        d = meta.get("derivation", {})
                        if any(p is not None and p != label for _, _, p in refs):
                            if not d.get("inputs") or not d.get("reason"):
                                fail(f"{where}/{label}: cross-period formula needs input references/reason")
                        if d.get("kind") == "quarter_difference" and (
                            not row.get("additive") or not d.get("additive") or
                            row.get("metric_kind") in {"eps", "weighted_average_shares", "balance", "ratio"}):
                            fail(f"{where}/{label}: invalid nonadditive quarter subtraction")
                    except (ValueError, SyntaxError) as exc:
                        fail(f"{where}/{label}: {exc}")
                for expr in all_expr:
                    if not expr: continue
                    try:
                        _, tokens = expression_tree(expr)
                        for token in tokens:
                            ts = token["sheet"] or short
                            if token["row"] not in registry.get(ts, {}):
                                fail(f"{where}: unknown reference {ts}:{token['row']}")
                            if token["period"] and token["period"] not in index.info:
                                fail(f"{where}: unknown explicit period {token['period']}")
                        if kind == "check" and len({(t["sheet"] or short, t["row"], t["period"], t["offset"]) for t in tokens}) < 2:
                            fail(f"{where}: check needs distinct source/component references")
                    except (ValueError, SyntaxError) as exc:
                        fail(f"{where}: {exc}")
                if kind == "check":
                    check_rows.append(row)
                    tolerance = row.get("tolerance", 1e-9)
                    if not is_number(tolerance) or tolerance < 0:
                        fail(f"{where}: invalid check tolerance")
                    elif tolerance > 1e-9 and not row.get("tolerance_reason"):
                        fail(f"{where}: rounding tolerance needs a unit/source explanation")
                    if row.get("expect_nonzero"): fail(f"{where}: expect_nonzero cannot bypass a failed bridge")
    default_groups = {"income_bridge", "balance_equation", "cash_bridge"}
    required_groups = model.get("required_check_groups", sorted(default_groups))
    if not isinstance(required_groups, list) or any(not isinstance(g, str) or not g.strip() for g in required_groups):
        fail("required_check_groups must be a list of non-empty group names")
        required_groups = sorted(default_groups)
    if set(required_groups) != default_groups and not model.get("check_scope_reason"):
        fail("Adapted reconciliation groups need a brief check_scope_reason")
    for group in required_groups:
        expected = model.get("check_group_periods", {}).get(group, index.labels)
        matching = [r for r in check_rows if r.get("check_group") == group]
        if not matching: fail(f"Required reconciliation group missing: {group}")
        for label in expected:
            if label not in index.info or not any(index.in_span(r, label) for r in matching):
                fail(f"Required reconciliation {group} does not cover {label}")
        if set(expected) != set(index.labels) and not model.get("check_scope_reason"):
            fail(f"{group}: narrowed reconciliation coverage needs check_scope_reason")
    return issues
