"""Compact provenance: shared table context, physical value coordinates, exceptions.

Resolved evidence exists only in memory. Production model.json never expands
shared file/unit/period/label data into an audit object for every value.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

from model_contract import ALLOWED_FORMS, PeriodIndex, is_number, period_for

DEFAULT_SUPPORTING_TOPICS = {"segments", "products_geography", "operating_metrics", "material_notes"}


def valid_topic(topic):
    return isinstance(topic, str) and bool(topic.strip())


def source_locator(table, locator):
    if not locator or locator.get("kind") == "text": return locator
    return {"kind": "html_cell", "table_index": locator.get("table_index", table.get("html_table_index")),
            "row_index": locator.get("row_index", locator.get("r")),
            "cell_index": locator.get("cell_index", locator.get("c")), "text": locator.get("text")}


def source_period(index, table, mapping, label, overrides=None):
    period = dict(index.info.get(label, {}))
    period.update({k: v for k, v in table["periods"][label].items() if k not in {"column", "headers"}})
    rule = mapping.get("period_rule")
    if rule in {"opening_balance", "closing_balance"}:
        end = ((date.fromisoformat(period["start"]) - timedelta(days=1)).isoformat()
               if rule == "opening_balance" else period["end"])
        period.update(start=None, end=end, grain="instant")
    elif rule:
        raise ValueError(f"Unknown source period rule: {rule}")
    period.update(mapping.get("period_overrides", {}).get(label, {}))
    period.update((overrides or {}).get("period", {}))
    period.setdefault("grain", "annual" if label in index.annual_labels else "discrete")
    if period["grain"] == "instant": period["start"] = None
    return period


class EvidenceIndex:
    def __init__(self, model):
        self.model = model
        self.periods = PeriodIndex(model["periods"])
        self.tables = {t["table_id"]: t for t in model.get("tables", [])}

    def resolve(self, row, label, binding):
        table = self.tables[binding["table"]]
        metric = binding.get("metric", row["id"])
        mapping = table["rows"][metric]
        overrides = binding.get("overrides", {})
        if overrides and not overrides.get("reason"):
            raise ValueError("A value exception needs a reason")
        allowed = {"reason", "period", "unit", "currency", "scope", "basis", "version",
                   "normalization", "context_ref", "sign_locator"}
        if set(overrides) - allowed:
            raise ValueError("Unsupported value override; map a separate shared source view for another file/label/locator")
        shared = copy.deepcopy(table["defaults"])
        shared.update({k: v for k, v in mapping.items() if k not in {"r", "c", "label"}})
        column = table["periods"].get(label)
        if column is None:
            raise ValueError(f"Source table has no mapped period {label}")
        period = source_period(self.periods, table, mapping, label, overrides)
        context = table.get("context", {})
        shared.update({
            "source_id": table["source_id"], "table_id": table["table_id"],
            "locator_kind": table.get("locator_kind", "html_cell"),
            "html_table_index": table.get("html_table_index"),
            "html_row_index": binding.get("r", mapping.get("r")),
            "html_cell_index": binding.get("c"),
            "label_row_index": mapping.get("r"), "label_cell_index": mapping.get("c"),
            "source_label": mapping["label"], "period": period,
            "period_header_cells": [source_locator(table, h) for h in column.get("headers", [])],
            "unit_locator": source_locator(table, context.get("unit")),
            "scope_locator": source_locator(table, context.get("scope")),
            "normalization": {**table["defaults"].get("normalization", {}),
                              **mapping.get("normalization", {}),
                              **overrides.get("normalization", {})},
        })
        if shared["locator_kind"] == "text":
            shared["text_locator"] = binding.get("text")
            shared["label_locator"] = mapping.get("locator")
        shared.update({k: v for k, v in overrides.items() if k not in {"reason", "period", "normalization"}})
        if shared.get("sign_locator"):
            shared["sign_locator"] = source_locator(table, shared["sign_locator"])
        return shared

    def facts(self, include_missing=False):
        """Every numeric owner, including native non-period schedules."""
        for sheet in self.model.get("sheets", []):
            short = sheet.get("short", sheet["name"])
            if sheet.get("kind") == "statement":
                for block in sheet.get("blocks", []):
                    for row in block.get("rows", []):
                        for label, value in row.get("values", {}).items():
                            if is_number(value) or include_missing and label in row.get("evidence", {}):
                                yield short, row, label, value, row.get("evidence", {}).get(label, {})
            elif sheet.get("kind") == "table":
                bindings = {(e["row"], e["column"]): e for e in sheet.get("cell_evidence", [])}
                for ri, record in enumerate(sheet.get("table", [])):
                    for ci, value in enumerate(record):
                        if not is_number(value) and not (include_missing and (ri, ci) in bindings): continue
                        binding = bindings.get((ri, ci), {})
                        row = {"id": binding.get("id", f"cell_{ri}_{ci}"), "native_schedule": True}
                        yield short, row, binding.get("period_label"), value, binding


def provenance_issues(model):
    issues = []
    sources = {s.get("source_id"): s for s in model.get("sources", [])}
    if not sources or None in sources or len(sources) != len(model.get("sources", [])):
        issues.append("Original source IDs must be present and unique")
    for sid, source in sources.items():
        path = Path(source.get("path", ""))
        if not source.get("path") or path.is_absolute() or ".." in path.parts:
            issues.append(f"{sid}: original path must be Workspace-relative")
        if source.get("filing_type") not in ALLOWED_FORMS:
            issues.append(f"{sid}: original is not an identified 10-K/10-Q")
        digest = source.get("sha256", "")
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdefABCDEF" for c in digest):
            issues.append(f"{sid}: original hash missing/invalid")
        if not source.get("url") or not source.get("filing_date"):
            issues.append(f"{sid}: original URL/filing date missing")
    index = EvidenceIndex(model)
    if not index.tables or len(index.tables) != len(model.get("tables", [])):
        issues.append("Shared source table IDs must be present and unique")
    for tid, table in index.tables.items():
        if table.get("source_id") not in sources:
            issues.append(f"{tid}: unknown original")
        if not valid_topic(table.get("topic")):
            issues.append(f"{tid}: disclosure topic missing")
        defaults = table.get("defaults", {})
        for field in ("unit", "scope", "basis", "version"):
            if not defaults.get(field): issues.append(f"{tid}: shared {field} missing")
        if not table.get("periods") or not table.get("rows"):
            issues.append(f"{tid}: period/metric mapping missing")
        if table.get("locator_kind", "html_cell") == "html_cell":
            if not isinstance(table.get("html_table_index"), int) or table["html_table_index"] < 0:
                issues.append(f"{tid}: native table index missing")
            bounds = table.get("data_rows", [])
            if len(bounds) != 2 or any(not isinstance(v, int) or v < 0 for v in bounds) or bounds[0] > bounds[-1]:
                issues.append(f"{tid}: set financial body data_rows=[first,last] once per table")
            for label, period in table.get("periods", {}).items():
                if not isinstance(period.get("column"), int) or period["column"] < 0:
                    issues.append(f"{tid}/{label}: source grid column missing")
        for key, reason in table.get("exclude_rows", {}).items():
            if not str(key).isdigit() or not reason:
                issues.append(f"{tid}: financial row exclusion requires row and reason")
    canonical_measures = {}
    for short, row, label, value, binding in index.facts():
        where = f"{short}:{row['id']}/{label}"
        try:
            ref = index.resolve(row, label, binding)
            if ref["locator_kind"] == "html_cell":
                if any(not isinstance(ref.get(k), int) or ref[k] < 0 for k in
                       ("html_row_index", "html_cell_index", "label_row_index", "label_cell_index")):
                    raise ValueError("Physical value/label locator missing")
            elif ref["locator_kind"] != "text":
                raise ValueError("Unknown original locator kind")
            if not row.get("native_schedule"):
                expected = period_for(model, row, label)
                if any(ref["period"].get(k) != expected.get(k) for k in ("start", "end", "grain")):
                    raise ValueError("Source interval differs from the exported interval")
                for field in ("unit", "scope", "currency"):
                    if row.get(field) and row[field] != ref.get(field):
                        raise ValueError(f"Source {field} differs from canonical metric")
                if row.get("measure_basis") and row["measure_basis"] != ref.get("basis"):
                    raise ValueError("Accounting/disclosure basis differs from canonical metric")
                signature = tuple(ref.get(k) for k in ("unit", "currency", "scope", "basis"))
                prior = canonical_measures.setdefault((short, row["id"]), signature)
                if prior != signature:
                    raise ValueError("Different units/scopes/accounting bases are merged into one canonical series")
            if not ref["period"].get("end") or ref["period"].get("grain") not in {"annual", "discrete", "ytd", "instant"}:
                raise ValueError("Exact source reporting interval missing")
            end = date.fromisoformat(ref["period"]["end"])
            if ref["period"]["grain"] != "instant" and date.fromisoformat(ref["period"]["start"]) > end:
                raise ValueError("Reversed source reporting interval")
            if end > date.fromisoformat(model["company"]["as_of_date"]):
                raise ValueError("A source actual cannot be after the research as-of date")
        except Exception as exc:
            issues.append(f"{where}: {exc}")
    coverage = model.get("coverage", [])
    covered_topics, covered_tables = set(), set()
    for item in coverage:
        topic = item.get("topic")
        if not valid_topic(topic):
            issues.append("Coverage topic must be a non-empty string")
            continue
        if topic in covered_topics:
            issues.append(f"Duplicate coverage topic: {topic}; use one shared entry")
        covered_topics.add(topic)
        if item.get("status", "covered") == "covered":
            if not item.get("tables"):
                issues.append(f"{topic}: covered topic needs shared table IDs")
            for tid in item.get("tables", []):
                if tid not in index.tables or index.tables[tid].get("topic") != topic:
                    issues.append(f"{topic}: invalid shared table target {tid}")
                else:
                    covered_tables.add(tid)
        elif item.get("status") not in {"not_disclosed", "not_applicable"} or not item.get("reason"):
            issues.append(f"{topic}: unexplained disclosure coverage status")
        for gap in item.get("gaps", []):
            if not gap.get("reason"): issues.append(f"{topic}: unexplained coverage gap")
    defaults = set(model.get("required_statements", ["IS", "BS", "CF"])) | DEFAULT_SUPPORTING_TOPICS
    required = model.get("required_topics", sorted(defaults))
    if not isinstance(required, list) or any(not valid_topic(t) for t in required):
        issues.append("required_topics must be a list of non-empty topic names")
        required = sorted(defaults)
    if defaults - set(required) and not model.get("coverage_scope_reason"):
        issues.append("Regrouped disclosure coverage needs a brief coverage_scope_reason")
    for topic in set(required):
        if topic not in covered_topics:
            issues.append(f"Disclosure coverage not reviewed: {topic}")
    for tid in sorted(set(index.tables) - covered_tables):
        issues.append(f"Selected source view absent from coverage matrix: {tid}")
    return issues


def data_fingerprint(model):
    """Bind the Agent review to actual data, mappings, formulas and source versions."""
    core = {k: v for k, v in model.items() if k not in {"status", "draft_gaps", "generated_at"}}
    return hashlib.sha256(json.dumps(core, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()
