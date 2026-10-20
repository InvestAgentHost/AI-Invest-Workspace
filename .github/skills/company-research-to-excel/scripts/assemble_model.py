#!/usr/bin/env python3
"""Assemble a historical draft; exact native column/row mappings require review."""
from __future__ import annotations

import argparse
import copy
import json
import re
from datetime import date
from pathlib import Path

from model_contract import PeriodIndex, fiscal_key
from provenance import source_period

ROUTING = {"income": "IS", "balance_sheet": "BS", "cash_flow": "CF",
           "operating_metric": "OP", "non_gaap": "NG"}
NAMES = {"IS": "Income Statement", "BS": "Balance Sheet", "CF": "Cash Flow",
         "OP": "Operating Metrics", "NG": "Disclosed Non-GAAP", "SEG": "Segments",
         "GEO": "Products & Geography", "NOTES": "Notes"}


def periods_block(obj, labels=None):
    declared = obj.get("period_metadata", {})
    if isinstance(declared, list):
        declared = {p["label"]: p for p in declared}
    annual, quarterly = [], []
    for label in labels or obj.get("period_order", []):
        entry = {"label": label, **declared.get(label, {})}
        pdata = obj.get("periods", {}).get(label, {})
        for field in ("start", "end", "fiscal_year", "fiscal_quarter", "grain", "comparatives"):
            if field in pdata and field not in entry:
                entry[field] = pdata[field]
        key = fiscal_key(entry)
        if key:
            entry.update(fiscal_year=key[0], fiscal_quarter=key[1])
        (quarterly if key and key[1] else annual).append(entry)
    return {"annual": annual, "quarterly": quarterly,
            "scrap_cols": 1 if annual and quarterly else 0}


def initial_model(obj, periods):
    company = copy.deepcopy(obj.get("company", {}))
    for key in ("name", "ticker", "entity", "currency", "scale", "reporting_framework",
                "fiscal_year_end", "consolidation_scope", "as_of_date"):
        if key in obj:
            company.setdefault(key, obj[key])
    company.setdefault("model_date", date.today().isoformat())
    model = {"schema": "historical-research-model.v4", "export_scope": "historical_10k_10q",
            "status": "draft", "company": company, "periods": periods,
            "required_statements": obj.get("required_statements", ["IS", "BS", "CF"]),
            "sources": copy.deepcopy(obj.get("sources", [])),
            "tables": copy.deepcopy(obj.get("tables", [])),
            "coverage": copy.deepcopy(obj.get("coverage", [])),
            "draft_gaps": [], "sheets": []}
    for key in ("required_topics", "coverage_scope_reason", "required_check_groups",
                "check_group_periods", "check_scope_reason"):
        if key in obj:
            model[key] = copy.deepcopy(obj[key])
    return model


def add_block(model, short, title, rows, metadata=None):
    if not rows:
        return
    sheet = next((s for s in model["sheets"] if s.get("short") == short), None)
    if sheet is None:
        sheet = {"name": NAMES.get(short, short), "short": short,
                 "kind": "statement", "blocks": []}
        model["sheets"].append(sheet)
    sheet["blocks"].append({**(metadata or {}), "title": title, "rows": rows})


def prepared_rows(model, obj):
    """Preserve per-period evidence; do not merge incompatible financial series."""
    labels = PeriodIndex(model["periods"]).labels
    buckets = {}
    for label in labels:
        for metric, item in obj.get("periods", {}).get(label, {}).get("values", {}).items():
            if not isinstance(item, dict):
                item = {"value": item}
            if item.get("status") in {"calculated", "estimate"} or item.get("statement") == "calculation":
                model["draft_gaps"].append(f"{metric}/{label}: derived result omitted; add a linked formula")
                continue
            short = ROUTING.get(item.get("statement"))
            if short is None:
                model["draft_gaps"].append(f"{metric}/{label}: statement ownership unresolved")
                continue
            identity = (short, metric, item.get("unit"), item.get("scope"),
                        item.get("measure_basis", "gaap"), item.get("series_id", "default"))
            if identity not in buckets:
                buckets[identity] = {"id": re.sub(r"[^A-Za-z0-9_]", "_", metric),
                                     "label": item.get("source_label") or metric,
                                     "type": "input", "values": {}, "evidence": {},
                                     "period_overrides": {}}
                for key in ("unit", "currency", "scope", "measure_basis", "metric_kind",
                            "additive", "fmt", "note", "time_basis"):
                    if key in item:
                        buckets[identity][key] = item[key]
            row = buckets[identity]
            row["values"][label] = item.get("value")
            row["evidence"][label] = copy.deepcopy(item.get("evidence", {}))
            if item.get("period"):
                row["period_overrides"][label] = copy.deepcopy(item["period"])
    used, by_short = {}, {}
    for identity, row in buckets.items():
        short, base_id = identity[0], row["id"]
        used[short, base_id] = used.get((short, base_id), 0) + 1
        if used[short, base_id] > 1:
            row["id"] += f"_basis_{used[short, base_id]}"
            model["draft_gaps"].append(f"{short}:{row['id']}: distinct scope/unit/basis kept separate; review sections")
        by_short.setdefault(short, []).append(row)
    for short, rows in by_short.items():
        add_block(model, short, "Reported historical actuals — review definitions and order", rows)


def bundle_rows(model, bundle):
    """Assemble selected source views; all shared metadata is stored once."""
    labels = set(PeriodIndex(model["periods"]).labels)
    known = {s["source_id"]: s for s in model["sources"]}
    for source in bundle.get("sources", []):
        existing = known.get(source["source_id"], {})
        for key in ("path", "sha256", "filing_type", "filing_date", "url"):
            if existing.get(key) and source.get(key) and existing[key] != source[key]:
                raise ValueError(f"Conflicting original metadata: {source['source_id']}/{key}")
        known[source["source_id"]] = {**existing, **copy.deepcopy(source)}
    model["sources"] = list(known.values())
    canonical = {(s["short"], r["id"]): r for s in model["sheets"]
                 for b in s.get("blocks", []) for r in b.get("rows", []) if r.get("id")}
    for native in bundle.get("tables", []):
        meta = native.get("metadata", {})
        # No disposition ledger for all website layout/header tables.
        # Agent review owns completeness of SELECTED financial source views.
        for view in meta.get("views", []):
            short, tid = view["sheet_short"], view["table_id"]
            definition = {k: copy.deepcopy(view[k]) for k in
                          ("table_id", "topic", "defaults", "periods", "data_rows", "context", "exclude_rows")
                          if k in view}
            definition.update(source_id=meta["source_id"],
                              html_table_index=meta["html_table_index"], rows={})
            if any(t["table_id"] == tid for t in model["tables"]):
                raise ValueError(f"Duplicate selected source view: {tid}")
            # Map expanded source geometry back to physical original cells.
            positions = {}
            for e in native.get("cell_evidence", []):
                for dr in range(e.get("rowspan", 1)):
                    for dc in range(e.get("colspan", 1)):
                        positions[e["row"] + dr, e["column"] + dc] = e
            new_rows = []
            for item in view["metrics"]:
                ri, lc, rid = item["source_row"], item.get("source_column", 0), item["id"]
                source_label = positions.get((ri, lc))
                if not source_label: raise ValueError(f"{tid}:{rid}: source label cannot be located")
                mapping = {"r": source_label["html_row_index"], "c": source_label["html_cell_index"],
                           "label": source_label["raw_text"]}
                # Unit etc. are exceptions to the table default, not repetitions.
                for field in ("unit", "currency", "scope", "basis", "normalization", "period_rule", "period_overrides"):
                    if field in item and item[field] != definition["defaults"].get(field):
                        mapping[field] = copy.deepcopy(item[field])
                definition["rows"][rid] = mapping
                effective = {**definition["defaults"], **mapping}
                row_meta = {"unit": effective.get("unit"), "currency": effective.get("currency"),
                            "scope": effective.get("scope"), "measure_basis": effective.get("basis")}
                key = short, rid
                row = canonical.get(key)
                if row is None:
                    row = {"id": rid, "label": item.get("label", mapping["label"]), "type": "input",
                           **row_meta, "values": {}, "evidence": {}, "period_overrides": {}}
                    for field in ("metric_kind", "additive", "fmt", "bold", "indent", "note"):
                        if field in item: row[field] = item[field]
                    canonical[key] = row
                    new_rows.append(row)
                elif any(row.get(k) != v for k, v in row_meta.items()):
                    raise ValueError(f"{short}:{rid}: incompatible source series; use distinct metric IDs")
                for label, column in definition["periods"].items():
                    if label not in labels:
                        raise ValueError(f"{tid}: fiscal period not in model: {label}")
                    if label in row["values"]:
                        raise ValueError(f"{short}:{rid}/{label}: duplicate actual; explicitly choose original/recast precedence")
                    ci = column["column"]
                    e = positions.get((ri, ci))
                    if not e: raise ValueError(f"{tid}:{rid}/{label}: original value cannot be located")
                    overrides = copy.deepcopy(view.get("exceptions", {}).get(f"{rid}/{label}", {}))
                    binding = {"table": tid, "r": e["html_row_index"], "c": e["html_cell_index"]}
                    if overrides: binding["overrides"] = overrides
                    normalization = {**definition["defaults"].get("normalization", {}),
                                     **mapping.get("normalization", {}), **overrides.get("normalization", {})}
                    value = native["rows"][ri][ci]
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        value *= normalization.get("multiplier", 1) * normalization.get("sign", 1)
                    elif value in {"—", "–", "-"} and normalization.get("dash_means_zero") and normalization.get("reason"):
                        value = 0
                    row["values"][label], row["evidence"][label] = value, binding
                    # A table-level YTD/instant mapping drives the row override;
                    # no separate per-value period declaration is required.
                    period_index = PeriodIndex(model["periods"])
                    base = period_index.info[label]
                    actual = {k: v for k, v in source_period(period_index, definition, mapping, label, overrides).items()
                              if k in {"start", "end", "grain"}}
                    if any(base.get(k) != v for k, v in actual.items()):
                        row["period_overrides"][label] = actual
            model["tables"].append(definition)
            add_block(model, short, view.get("title", native["title"]), new_rows,
                      {"note": view.get("note", "Reported intervals and units follow shared source mappings."),
                       "table_ids": [tid]})
    # Coverage is a single topic matrix. Do not generate 'not disclosed' claims.
    existing_topics = {c["topic"]: c for c in model["coverage"]}
    for table in model["tables"]:
        topic = table["topic"]
        if topic not in existing_topics:
            entry = {"topic": topic, "tables": []}
            model["coverage"].append(entry)
            existing_topics[topic] = entry
        if table["table_id"] not in existing_topics[topic].setdefault("tables", []):
            existing_topics[topic]["tables"].append(table["table_id"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("financial_input", nargs="?")
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--bundle-only", action="store_true")
    parser.add_argument("--periods", default="", help="Comma-separated fiscal labels; dates still require review")
    parser.add_argument("--period-metadata", type=Path, help="JSON mapping fiscal labels to dates and grain")
    parser.add_argument("--ticker", default="")
    parser.add_argument("--name", default="")
    parser.add_argument("--metrics", help="Deprecated: calculated Markdown is not a source of actuals")
    args = parser.parse_args()
    if args.metrics:
        parser.error("--metrics is disabled: create derived formulas linked to source-bound actuals")
    if args.bundle_only and not args.bundle:
        parser.error("--bundle-only requires --bundle")
    if not args.financial_input and not args.bundle_only:
        parser.error("Provide financial_input or --bundle-only")
    obj = json.loads(Path(args.financial_input).read_text(encoding="utf-8")) if args.financial_input else {}
    if args.period_metadata:
        obj["period_metadata"] = json.loads(args.period_metadata.read_text(encoding="utf-8"))
    labels = [s.strip() for s in args.periods.split(",") if s.strip()] or None
    model = initial_model(obj, periods_block(obj, labels))
    if args.name: model["company"]["name"] = args.name
    if args.ticker: model["company"]["ticker"] = args.ticker
    if args.financial_input:
        prepared_rows(model, obj)
    if args.bundle:
        bundle_rows(model, json.loads(args.bundle.read_text(encoding="utf-8")))
    if not model["sources"]:
        model["draft_gaps"].append("Original 10-K/10-Q catalog missing; prepared JSON alone is not authoritative")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise FileExistsError(f"Draft exists; explicitly edit it or choose a new path: {args.output}")
    args.output.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "DRAFT", "output": str(args.output),
                      "sheets": len(model["sheets"]), "review_gaps": len(model["draft_gaps"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
