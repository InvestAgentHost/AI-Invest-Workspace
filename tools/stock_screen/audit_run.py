#!/usr/bin/env python3
"""Audit score coverage separately from data availability and aggregation validity.

This checks necessary structural conditions for a finished screen. It does not
verify source claims or approve analyst judgments. No data retrieval is performed.
"""
import argparse
from collections import Counter
import importlib.util
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / ".github/skills/stock-initial-screen/scripts/aggregate_scores.py"


def load_engine():
    spec = importlib.util.spec_from_file_location("screen_aggregate", ENGINE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit(payload, results, ledger, engine):
    companies = payload["companies"]
    recomputed = engine.aggregate(payload)
    issues = []
    if recomputed != results:
        issues.append("scoring-results.json differs from aggregation of current inputs")
    evidence = {}
    for record in ledger:
        key = (record["company_id"], record["metric_id"])
        if key in evidence:
            issues.append(f"duplicate evidence record: {key}")
        evidence[key] = record
    expected_keys = {(c["company_id"], k) for c in companies for k in c["scores"]}
    if set(evidence) != expected_keys:
        issues.append("evidence ledger keys differ from input score keys")
    for c in companies:
        for k, score in c["scores"].items():
            record = evidence.get((c["company_id"], k))
            if record is not None and record["score"] != score:
                issues.append(f"evidence/input score mismatch: {c['company_id']}/{k}")
    coverage = {}
    for k in [*engine.FACTOR_KEYS["B"], *engine.FACTOR_KEYS["M"],
              *engine.FACTOR_KEYS["I"], "B3a"]:
        filled = [c["company_id"] for c in companies if c["scores"][k] is not None]
        reasons = Counter(c["missing_reasons"][k].split(":", 1)[0]
                          for c in companies if c["scores"][k] is None)
        coverage[k] = {"filled": len(filled), "total": len(companies),
                       "issuers": filled, "missing_categories": dict(reasons)}
    evaluated = recomputed["companies"]
    factor_counts = {k: sum(c["factors"][k]["score"] is not None for c in evaluated)
                     for k in engine.FACTOR_KEYS}
    unresolved = [c["company_id"] for c in evaluated if c["status"] == "manual_review"]
    completion_errors = list(issues)
    if unresolved:
        completion_errors.append(f"{len(unresolved)} issuer classifications remain manual_review")
    score_count = sum(x["filled"] for x in coverage.values())
    return {
        "as_of": payload["as_of"], "rule_version": payload["rule_version"],
        "check_scope": "Structural coverage and consistency only; evidence quality needs review",
        "delivery_status": "incomplete" if completion_errors else "structure_ready",
        "consistency_pass": not issues, "consistency_errors": issues,
        "completion_errors": completion_errors, "issuer_count": len(companies),
        "scores_filled": score_count, "scores_total": len(companies) * len(coverage),
        "scores_missing": len(companies) * len(coverage) - score_count,
        "factor_counts": factor_counts,
        "average_count": sum(c["average"] is not None for c in evaluated),
        "stage_1_determined": sum(c["stage_1"] is not None for c in evaluated),
        "unresolved_issuers": unresolved,
        "status_counts": recomputed["counts_by_status"], "metric_coverage": coverage,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--require-complete", action="store_true",
                        help="Exit 2 when any issuer classification remains unresolved")
    args = parser.parse_args()
    p = args.run_dir
    payload = json.loads((p / "scoring-input.json").read_text())
    if payload['rule_version']=='screen-v2':
        from audit_v2 import audit_files
        report=audit_files(ROOT,p)
        print(json.dumps(report,ensure_ascii=False))
        return 2 if report['errors'] else 0
    results = json.loads((p / "scoring-results.json").read_text())
    ledger = [json.loads(line) for line in (p / "evidence-ledger.jsonl").read_text().splitlines()]
    report = audit(payload, results, ledger, load_engine())
    report["input_sha256"] = {name: hashlib.sha256((p / name).read_bytes()).hexdigest()
                              for name in ("scoring-input.json", "scoring-results.json", "evidence-ledger.jsonl")}
    facts_path = p / "annual-facts.json"
    if facts_path.exists():
        facts = json.loads(facts_path.read_text())
        report["financial_data"] = {
            "issuers": len(facts),
            "annual_observations": sum(len(rows) for rows in facts.values()),
            "numeric_fields": sum(isinstance(v, dict) and v.get("value") is not None
                                  for rows in facts.values() for row in rows for v in row.values()),
        }
    (p / "completion-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("delivery_status", "consistency_pass", "scores_filled",
                     "scores_total", "factor_counts", "stage_1_determined", "completion_errors")}, ensure_ascii=False))
    return 2 if not report["consistency_pass"] or (args.require_complete and report["completion_errors"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
