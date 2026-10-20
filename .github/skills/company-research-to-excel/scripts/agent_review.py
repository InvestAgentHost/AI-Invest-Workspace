"""Validate an independent-Agent review record; metadata cannot prove review occurred."""
from __future__ import annotations

import hashlib
from pathlib import Path

from provenance import data_fingerprint

REVIEW_CHECKS = {
    "coverage", "periods_units_scope", "versions_and_labels",
    "derivations", "anomalies", "workbook_consistency",
}


def review_binding(model, workbook):
    return {"data_fingerprint": data_fingerprint(model),
            "workbook_sha256": hashlib.sha256(Path(workbook).read_bytes()).hexdigest()}


def verify_agent_review(model, workbook, review=None):
    binding = review_binding(model, workbook)
    findings = []
    def issue(message, status="UNVERIFIABLE"):
        findings.append({"status": status, "location": "agent_data_review", "message": message})
    if not review:
        issue("Independent-Agent review is pending; automated checks do not constitute release approval")
        return {"status": "UNVERIFIABLE", "binding": binding, "findings": findings}
    reviewer = review.get("reviewer", {})
    if not isinstance(reviewer, dict):
        reviewer = {}
    reviewer_id, producer_id = reviewer.get("agent_id"), reviewer.get("producer_agent_id")
    if any(not isinstance(value, str) or not value.strip() for value in (reviewer_id, producer_id)):
        issue("Independent review needs actual reviewer and producer Agent IDs")
    elif reviewer_id.strip() == producer_id.strip():
        issue("The producer cannot serve as its own independent reviewer")
    for key, expected in binding.items():
        if review.get(key) != expected:
            issue(f"Agent review is stale or applies to a different {key}")
    if review.get("status") != "pass" or not review.get("summary"):
        issue("The independent reviewer must inspect originals/final Excel and record a concise conclusion")
    if not REVIEW_CHECKS.issubset(set(review.get("checks", []))):
        issue("Agent review does not cover all required semantic/data checks")
    for key, expected in (
        ("reviewed_sources", {s["source_id"] for s in model.get("sources", [])}),
        ("reviewed_tables", {t["table_id"] for t in model.get("tables", [])}),
    ):
        actual = set(review.get(key, []))
        if actual != expected:
            issue(f"{key} differs from actual scope; missing={sorted(expected - actual)}, unknown={sorted(actual - expected)}")
    for finding in review.get("findings", []):
        if finding.get("status") != "resolved":
            issue(f"Unresolved Agent finding: {finding.get('location', '?')} {finding.get('issue', '')}", "FAIL")
        elif not finding.get("resolution"):
            issue("A resolved Agent finding needs the actual correction/explanation")
    return {"status": "FAIL" if any(f["status"] == "FAIL" for f in findings)
            else "UNVERIFIABLE" if findings else "PASS",
            "binding": binding, "findings": findings}
