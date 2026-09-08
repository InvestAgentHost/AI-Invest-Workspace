#!/usr/bin/env python3
"""
Extract raw data from curated research artifacts into a draft model.json.

Mechanical extraction only — reads data files and organizes metrics by their
``statement`` field.  Does NOT make formatting decisions (bold, indent, growth,
margins, checks).  The AI agent reviews the draft, adds analytical wiring, and
customizes the workbook structure.

Usage:
    python3 assemble_model.py financial_input.json -o model.json
    python3 assemble_model.py financial_input.json -o model.json \\
        --metrics metrics.md --bundle tables.json
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path


# ---- statement-field routing (reads the curated field, not a judgment) ----

STATEMENT_SHEET_MAP = {
    "income": "IS",
    "balance_sheet": "BS",
    "cash_flow": "CF",
    "non_gaap": "IS",
    "operating_metric": "OP",
    "calculation": "OP",
}

DERIVED_CATEGORIES = {
    "profitability", "returns", "leverage", "solvency", "liquidity",
    "coverage", "cash_conversion", "earnings_quality", "growth",
    "working_capital", "common_size", "debt_bridge", "issuer_apm",
}

PERIOD_RE = re.compile(
    r"^(?:FY|CY)\d{2,4}(?:[/\-]\d{2,4})?$"
    r"|^(?:[1-4]Q|Q[1-4])(?:\s*FY)?\d{2,4}$"
    r"|^(?:19|20)\d{2}(?:[-/]\d{1,2})?$",
    re.I,
)


# --------------------------------------------------------- period helpers ----

def build_periods_block(obj):
    order = obj.get("period_order", [])
    annual, quarterly = [], []
    for label in order:
        pinfo = {"label": label}
        if "FY" in label or label.startswith("CY"):
            annual.append(pinfo)
        else:
            quarterly.append(pinfo)
    return {
        "annual": annual,
        "scrap_cols": 5 if quarterly else 0,
        "quarterly": quarterly,
    }


# -------------------------------------------------------- value extraction ----

def extract_values(obj, key, periods_order):
    vals = {}
    for period in periods_order:
        pdata = (obj.get("periods", {}).get(period, {})
                 .get("values", {}).get(key))
        if pdata is None:
            continue
        v = pdata.get("value") if isinstance(pdata, dict) else pdata
        if v is not None:
            vals[period] = v
    return vals


def get_field(obj, key, field):
    for period in obj.get("period_order", []):
        item = (obj.get("periods", {}).get(period, {})
                .get("values", {}).get(key))
        if isinstance(item, dict) and item.get(field):
            return item[field]
    return None


def classify_metrics(obj, periods_order):
    buckets = {"IS": [], "BS": [], "CF": [], "OP": []}
    nongaap = []
    seen = set()
    for period in periods_order:
        for key in obj.get("periods", {}).get(period, {}).get("values", {}) or {}:
            if key in seen:
                continue
            seen.add(key)
            stmt = get_field(obj, key, "statement")
            source_label = get_field(obj, key, "source_label")
            if stmt == "non_gaap":
                nongaap.append((key, source_label, stmt))
            else:
                target = STATEMENT_SHEET_MAP.get(stmt, "OP")
                buckets[target].append((key, source_label, stmt))
    return buckets, nongaap


def make_row(obj, key, source_label, periods_order):
    vals = extract_values(obj, key, periods_order)
    if not vals:
        return None
    label = source_label or key.replace("_", " ").title()
    return {"id": key, "label": label, "type": "input", "values": vals}


# ------------------------------------------------------- sheet builders ----

def build_statement_sheet(name, short, tab_color, metrics, obj,
                          periods_order, block_title, extra_blocks=None):
    rows = [r for k, sl, st in metrics
            if (r := make_row(obj, k, sl, periods_order))]
    if not rows and not extra_blocks:
        return None
    blocks = []
    if rows:
        blocks.append({"title": block_title, "rows": rows})
    if extra_blocks:
        blocks.extend(extra_blocks)
    return {
        "name": name, "short": short,
        "kind": "statement", "tab_color": tab_color,
        "blocks": blocks,
    }


# ------------------------------------------------------- metrics.md parser --

def parse_metric_value(text):
    text = text.strip()
    if not text or text.lower() in ("n/a", "n.a.", "n/m", "n.m.",
                                     "-", "--", "---", "—", "–"):
        return None, "num1"
    neg = False
    core = text
    if text.startswith("(") and ")" in text:
        neg, core = True, text[1:text.index(")")]

    m = re.match(r"^([+-]?[\d,]+\.?\d*)\s*%$", core)
    if m:
        v = float(m.group(1).replace(",", "")) / 100
        return (-v if neg else v), "pct"
    m = re.match(r"^([+-]?[\d,]+\.?\d*)\s*x$", core, re.I)
    if m:
        v = float(m.group(1).replace(",", ""))
        return (-v if neg else v), "x"
    m = re.match(r"^([+-]?[\d,]+\.?\d*)"
                 r"\s*(?:million|billion|thousand|days|pp|bps)?$",
                 core, re.I)
    if m:
        v = float(m.group(1).replace(",", ""))
        return (-v if neg else v), "num1"
    return None, "num1"


def parse_metrics_md(metrics_path):
    text = Path(metrics_path).read_text(encoding="utf-8")
    data = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 6:
            continue
        period, cat, metric, result = parts[1], parts[2], parts[3], parts[4]
        if cat not in DERIVED_CATEGORIES:
            continue
        if not period.startswith(("FY", "CY", "Q", "1Q", "2Q", "3Q", "4Q")):
            continue
        val, fmt = parse_metric_value(result)
        data.setdefault(cat, {})
        if metric not in data[cat]:
            data[cat][metric] = {"values": {}, "fmt": fmt}
        if val is not None:
            data[cat][metric]["values"][period] = val
            if fmt != "num1" and data[cat][metric]["fmt"] == "num1":
                data[cat][metric]["fmt"] = fmt
    return data


def build_derived_metrics_sheet(metrics_data):
    blocks = []
    for cat in sorted(metrics_data):
        rows = []
        for label, md in metrics_data[cat].items():
            if not md["values"]:
                continue
            slug = re.sub(r"_+", "_",
                          re.sub(r"[^a-z0-9_]", "_", label.lower())).strip("_")
            rows.append({
                "id": f"dm_{cat}_{slug}",
                "label": label,
                "type": "input",
                "values": md["values"],
                "fmt": md["fmt"],
            })
        if rows:
            blocks.append({
                "title": cat.upper().replace("_", " "),
                "rows": rows,
            })
    return {
        "name": "Derived Metrics", "short": "DM",
        "kind": "statement", "tab_color": "7030A0",
        "blocks": blocks,
    } if blocks else None


# ---------------------------------------------------------- bundle parser ----

_SEC_YEAR_RE = re.compile(r"^(19|20)\.(\d{2})$")


def normalize_period(raw, periods_set):
    """Map raw period text to a canonical label in *periods_set*, or None."""
    s = str(raw).strip()
    if not s:
        return None
    if s in periods_set:
        return s
    if PERIOD_RE.match(s):
        # Bare year "2024" → try "FY2024"
        if re.fullmatch(r"(?:19|20)\d{2}", s):
            for prefix in ("FY", "CY"):
                candidate = f"{prefix}{s}"
                if candidate in periods_set:
                    return candidate
        return s
    # SEC compact_row artifact: "20.24" → "2024" → "FY2024"
    m = _SEC_YEAR_RE.match(s)
    if m:
        year = m.group(1) + m.group(2)
        for prefix in ("FY", "CY"):
            candidate = f"{prefix}{year}"
            if candidate in periods_set:
                return candidate
        if PERIOD_RE.match(year):
            return year
    return None


def bundle_table_to_block(table, periods_set):
    headers = table.get("headers", [])
    rows = list(table.get("rows", []))
    tid = table.get("table_id", "T000")

    # 1. Try header-based period detection (standard markdown tables)
    period_map = {}
    for i, h in enumerate(headers):
        p = normalize_period(h, periods_set)
        if p:
            period_map[i] = p

    label_col = 0
    sec_promoted = False

    # 2. SEC HTML fallback: periods in an early data row, not headers
    if not period_map:
        for row_idx in range(min(5, len(rows))):
            candidate = rows[row_idx]
            ordered_periods = []
            for c in candidate:
                p = normalize_period(c, periods_set)
                if p:
                    ordered_periods.append(p)
            if len(ordered_periods) >= 2:
                period_map = {i + 1: p for i, p in enumerate(ordered_periods)}
                rows = rows[row_idx + 1:]
                sec_promoted = True
                break

    if not period_map:
        return None

    # 3. Find label column
    if not sec_promoted:
        for i, h in enumerate(headers):
            if i not in period_map and str(h).lower() in (
                    "metric", "label", "name", "description"):
                label_col = i
                break
        else:
            for i, h in enumerate(headers):
                if i not in period_map:
                    label_col = i
                    break

    block_rows, seen = [], set()
    for row in rows:
        if not row or len(row) <= label_col:
            continue
        lab = str(row[label_col] or "").strip()
        if not lab or lab in ("—", "-"):
            continue
        slug = re.sub(r"_+", "_",
                      re.sub(r"[^a-z0-9_]", "_", lab.lower())).strip("_")
        rid = f"{tid}_{slug}"
        base, n = rid, 1
        while rid in seen:
            rid, n = f"{base}_{n}", n + 1
        seen.add(rid)

        vals = {}
        for ci, p in period_map.items():
            if ci < len(row) and row[ci] is not None:
                v = row[ci]
                if isinstance(v, (int, float)):
                    vals[p] = v
                elif isinstance(v, str):
                    pv, _ = parse_metric_value(v)
                    if pv is not None:
                        vals[p] = pv
        if vals:
            block_rows.append({"id": rid, "label": lab,
                                "type": "input", "values": vals})
    if not block_rows:
        return None
    clean = re.sub(r"^\d+\.\s*", "", table.get("title", "Data")).strip()
    return {"title": (clean[:57] + "..." if len(clean) > 60
                      else clean).upper(),
            "rows": block_rows}


def build_bundle_sheets(bundle_path, periods_order, include_financials=False):
    bundle = json.loads(Path(bundle_path).read_text(encoding="utf-8"))
    ps = set(periods_order)
    groups = {}
    for t in bundle.get("tables", []):
        topic = t.get("topic_hint", "other_notes")
        if topic == "financials" and not include_financials:
            continue
        groups.setdefault(topic, []).append(t)

    sheets, used = [], set()
    for topic, tables in groups.items():
        name = topic.replace("_", " ").title()
        short = topic[:3].upper()
        if short in used:
            n = 2
            while f"{short}{n}" in used:
                n += 1
            short = f"{short}{n}"
        used.add(short)
        blocks = [b for t in tables if (b := bundle_table_to_block(t, ps))]
        if blocks:
            sheets.append({"name": name, "short": short,
                           "kind": "statement", "tab_color": "548235",
                           "blocks": blocks})
    return sheets


# -------------------------------------------------------- cover & sources ----

def build_cover(company):
    table = [[{"text": company.get("name", ""), "bold": True}], []]
    table.append([{"text": "Company information", "bold": True}])
    for key, label in [("ticker", "Ticker"), ("currency", "Reporting currency"),
                       ("units", "Units"),
                       ("reporting_framework", "Reporting framework"),
                       ("fiscal_year_end", "Fiscal year end"),
                       ("consolidation_scope", "Consolidation scope"),
                       ("as_of_date", "Research as-of date"),
                       ("model_date", "Model date")]:
        if company.get(key):
            table.append([label, str(company[key])])
    table += [[], [{"text": "Color legend", "bold": True}],
              [{"text": "Blue", "fill": "D6E4F0"}, "Hardcoded reported value"],
              [{"text": "Black"}, "Formula / calculation"],
              [{"text": "Green", "fill": "E2EFDA"}, "Cross-sheet link"],
              [{"text": "Grey italic"}, "Memo / commentary"],
              [], [{"text": "Sheet directory", "bold": True}]]
    return {"name": "Cover", "kind": "table",
            "col_widths": [28, 60], "tab_color": "1F4E79", "table": table}


def build_sources(company, obj, bundle_only=False):
    table = [[{"text": "Sources and data provenance", "bold": True}], [],
             [{"text": "Source", "bold": True},
              {"text": "Description", "bold": True},
              {"text": "Date", "bold": True}]]
    if not bundle_only:
        table.append(["financial_input.json", "Curated financial panel",
                       company.get("as_of_date", "")])
    else:
        table.append(["tables.json (bundle-only)", "Collector bundle from SEC filings",
                       company.get("model_date", "")])
    seen = set()
    for period in obj.get("period_order", []):
        for item in (obj.get("periods", {}).get(period, {})
                     .get("values", {}) or {}).values():
            if isinstance(item, dict) and item.get("source"):
                src = item["source"]
                if src not in seen:
                    seen.add(src)
                    table.append([src, item.get("source_label", "")[:60],
                                  period])
    return {"name": "Sources", "kind": "table",
            "col_widths": [32, 60, 20], "table": table}


# ------------------------------------------------------------- assembly ----

def assemble(financial_path, metrics_path=None, bundle_path=None):
    obj = json.loads(Path(financial_path).read_text(encoding="utf-8"))
    periods_order = obj.get("period_order",
                            list(obj.get("periods", {}).keys()))

    company = {
        "name": obj.get("entity", ""), "ticker": "",
        "currency": obj.get("currency", "USD"),
        "units": f'{obj.get("currency", "$")} in '
                 f'{obj.get("scale", "millions")} except per-share data',
        "reporting_framework": obj.get("reporting_framework", ""),
        "fiscal_year_end": obj.get("fiscal_year_end", ""),
        "consolidation_scope": obj.get("consolidation_scope", ""),
        "as_of_date": obj.get("as_of_date", ""),
        "model_date": datetime.now().strftime("%Y-%m-%d"),
    }

    periods_block = build_periods_block(obj)
    buckets, nongaap = classify_metrics(obj, periods_order)

    sheets = [build_cover(company)]

    ng_rows = [r for k, sl, st in nongaap
               if (r := make_row(obj, k, sl, periods_order))]
    ng_block = {"title": "NON-GAAP METRICS", "rows": ng_rows} if ng_rows else None

    is_sh = build_statement_sheet("Income Statement", "IS", "1F4E79",
                                  buckets["IS"], obj, periods_order,
                                  "INCOME STATEMENT",
                                  [ng_block] if ng_block else None)
    if is_sh:
        sheets.append(is_sh)

    for name, short, color, key, title in [
        ("Balance Sheet", "BS", "1F4E79", "BS", "BALANCE SHEET"),
        ("Cash Flow", "CF", "1F4E79", "CF", "CASH FLOW STATEMENT"),
        ("Operating Metrics", "OP", "548235", "OP", "OPERATING METRICS"),
    ]:
        sh = build_statement_sheet(name, short, color, buckets[key],
                                   obj, periods_order, title)
        if sh:
            sheets.append(sh)

    if metrics_path and Path(metrics_path).exists():
        dm = build_derived_metrics_sheet(parse_metrics_md(metrics_path))
        if dm:
            sheets.append(dm)

    if bundle_path and Path(bundle_path).exists():
        sheets.extend(build_bundle_sheets(bundle_path, periods_order))

    cover = sheets[0]
    for s in sheets[1:]:
        cover["table"].append([s["name"],
                               f'{s["short"]} tab' if s.get("kind") == "statement"
                               else ""])
    sheets.append(build_sources(company, obj))

    return {"company": company, "periods": periods_block, "sheets": sheets}, \
           buckets, nongaap


def assemble_bundle_only(bundle_path, periods_order, company_name="",
                         ticker="", metrics_path=None):
    company = {
        "name": company_name, "ticker": ticker,
        "currency": "USD",
        "units": "$ in millions except per-share data",
        "reporting_framework": "US GAAP",
        "fiscal_year_end": "",
        "consolidation_scope": "consolidated",
        "as_of_date": "",
        "model_date": datetime.now().strftime("%Y-%m-%d"),
    }

    annual = [{"label": p} for p in periods_order
              if "FY" in p or p.startswith("CY") or re.fullmatch(r"(?:19|20)\d{2}", p)]
    quarterly = [{"label": p} for p in periods_order if p not in
                 {a["label"] for a in annual}]
    periods_block = {
        "annual": annual,
        "scrap_cols": 5 if quarterly else 0,
        "quarterly": quarterly,
    }

    sheets = [build_cover(company)]
    all_bundle_sheets = build_bundle_sheets(
        bundle_path, periods_order, include_financials=True)
    if all_bundle_sheets:
        sheets.extend(all_bundle_sheets)

    if metrics_path and Path(metrics_path).exists():
        dm = build_derived_metrics_sheet(parse_metrics_md(metrics_path))
        if dm:
            sheets.append(dm)

    cover = sheets[0]
    for s in sheets[1:]:
        cover["table"].append([s["name"],
                               f'{s["short"]} tab' if s.get("kind") == "statement"
                               else ""])

    dummy_obj = {"period_order": periods_order, "periods": {}}
    sheets.append(build_sources(company, dummy_obj, bundle_only=True))

    model = {"company": company, "periods": periods_block, "sheets": sheets}

    total_rows = sum(
        sum(len(b.get("rows", [])) for b in s.get("blocks", []))
        for s in sheets if s.get("kind") == "statement")
    total_blocks = sum(
        len(s.get("blocks", []))
        for s in sheets if s.get("kind") == "statement")

    return model, total_blocks, total_rows


# -------------------------------------------------------- summary printer ----

def print_summary(model, buckets, nongaap, metrics_data):
    co = model["company"]
    p = model["periods"]
    na, nq = len(p.get("annual", [])), len(p.get("quarterly", []))

    print(f"\n{'='*60}")
    print("DATA EXTRACTION SUMMARY — draft model.json")
    print(f"{'='*60}")
    print(f"Company : {co.get('name','?')}")
    print(f"Currency: {co.get('currency','?')} | "
          f"Units: {co.get('units','?')}")
    print(f"Periods : {na} annual, {nq} quarterly")

    for label, key in [("Income Statement", "IS"), ("Balance Sheet", "BS"),
                        ("Cash Flow", "CF"), ("Operating Metrics", "OP")]:
        items = buckets.get(key, [])
        if items:
            print(f"\n{label} ({len(items)} metrics):")
            for k, sl, _ in items:
                print(f"  {k:35s}  {(sl or k)[:45]}")
    if nongaap:
        print(f"\nNon-GAAP ({len(nongaap)} metrics):")
        for k, sl, _ in nongaap:
            print(f"  {k:35s}  {(sl or k)[:45]}")
    if metrics_data:
        total = sum(len(v) for v in metrics_data.values())
        print(f"\nDerived Metrics ({len(metrics_data)} categories, "
              f"{total} metrics):")
        for cat in sorted(metrics_data):
            names = list(metrics_data[cat])[:3]
            extra = f" +{len(metrics_data[cat])-3}" if len(metrics_data[cat]) > 3 else ""
            print(f"  {cat:25s} ({len(metrics_data[cat]):2d}): "
                  f"{', '.join(names)}{extra}")

    print(f"\n{'='*60}")
    print("AGENT: customize model.json before building —")
    print('  "bold": true      on headline aggregates')
    print('  "indent": 1       on sub-line items')
    print("  growth_yoy/qoq    rows for key metrics")
    print("  calc              rows for margins, FCF")
    print("  check             rows for balance/income tie-outs")
    print(f"{'='*60}\n")


# ------------------------------------------------------------------ CLI ----

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("financial_input", nargs="?", default=None,
                    help="Path to financial_input.json (omit with --bundle-only)")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--metrics", help="Path to metrics.md")
    ap.add_argument("--bundle", help="Path to collector bundle JSON")
    ap.add_argument("--bundle-only", action="store_true",
                    help="Build model from tables.json alone (no financial_input)")
    ap.add_argument("--ticker", default="", help="Ticker symbol (bundle-only mode)")
    ap.add_argument("--name", default="", help="Company name (bundle-only mode)")
    ap.add_argument("--periods", default="",
                    help="Comma-separated period labels, e.g. FY2020,FY2021,...,FY2025")
    args = ap.parse_args()

    if args.bundle_only:
        if not args.bundle:
            ap.error("--bundle-only requires --bundle <tables.json>")
        if not args.periods:
            ap.error("--bundle-only requires --periods FY2020,FY2021,...,FY2025")
        periods_order = [p.strip() for p in args.periods.split(",") if p.strip()]

        metrics_data = None
        if args.metrics and Path(args.metrics).exists():
            metrics_data = parse_metrics_md(args.metrics)

        model, total_blocks, total_rows = assemble_bundle_only(
            args.bundle, periods_order,
            company_name=args.name, ticker=args.ticker,
            metrics_path=args.metrics)

        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(
            json.dumps(model, indent=2, ensure_ascii=False), encoding="utf-8")

        ns = len(model["sheets"])
        print(f"wrote {args.output} ({ns} sheets, bundle-only mode)")
        for s in model["sheets"]:
            if s.get("kind") == "statement":
                nr = sum(len(b.get("rows", [])) for b in s.get("blocks", []))
                print(f"  {s['name']} ({s['short']}): "
                      f"{len(s.get('blocks',[]))} blocks, {nr} rows")
            else:
                print(f"  {s['name']}: table")

        print(f"\n{'='*60}")
        print("BUNDLE-ONLY EXTRACTION — draft model.json")
        print(f"{'='*60}")
        print(f"Company : {args.name or '?'} ({args.ticker or '?'})")
        print(f"Periods : {len(periods_order)}")
        print(f"Sheets  : {ns}  |  Blocks: {total_blocks}  |  Rows: {total_rows}")
        if metrics_data:
            total_m = sum(len(v) for v in metrics_data.values())
            print(f"Derived : {len(metrics_data)} categories, {total_m} metrics")
        print(f"\n{'='*60}")
        print("NOTE: bundle-only draft is organized by collector topic_hint.")
        print("The agent MUST restructure into IS/BS/CF/SEG sheets during Phase 4.")
        print("Identify financial statement tables by row content, not topic.")
        print(f"{'='*60}\n")
        return

    if not args.financial_input:
        ap.error("financial_input is required (or use --bundle-only)")

    metrics_data = None
    if args.metrics and Path(args.metrics).exists():
        metrics_data = parse_metrics_md(args.metrics)

    model, buckets, nongaap = assemble(
        args.financial_input, args.metrics, args.bundle)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(
        json.dumps(model, indent=2, ensure_ascii=False), encoding="utf-8")

    ns = len(model["sheets"])
    print(f"wrote {args.output} ({ns} sheets)")
    for s in model["sheets"]:
        if s.get("kind") == "statement":
            nr = sum(len(b.get("rows", [])) for b in s.get("blocks", []))
            print(f"  {s['name']} ({s['short']}): "
                  f"{len(s.get('blocks',[]))} blocks, {nr} rows")
        else:
            print(f"  {s['name']}: table")

    print_summary(model, buckets, nongaap, metrics_data)


if __name__ == "__main__":
    main()
