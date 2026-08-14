#!/usr/bin/env python3
"""Validate mechanical release contracts for a company research report."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


SOURCE_ID_RE = re.compile(r"\bS\d{2,4}\b")
ATTEMPT_ID_RE = re.compile(r"\b(?:AT|ATTEMPT)-?\d+\b", re.IGNORECASE)
TABLE_SEPARATOR_RE = re.compile(r"^\|(?:\s*:?-+:?\s*\|)+\s*$")
VALID_COVERAGE_STATES = {
    "covered",
    "unavailable",
    "unresolved",
    "n.a.",
    "na",
    "pass",
    "partial",
    "blocked",
}
REQUIRED_GATE_LABELS = (
    "A1",
    "A2",
    "B1",
    "B2",
    "C1",
    "C2",
    "D1",
    "D2",
    "E1",
    "E2",
    "R1",
    "R2",
    "R3",
)
GATE_STATUS_RE = r"PASS WITH LIMITATION|PASS|PARTIAL|BLOCKED|N\.A\."
RELEASE_STATUS_RE = r"PASS WITH LIMITATION|PASS|PARTIAL|BLOCKED"
STATUS_RANK = {
    "PASS": 0,
    "N.A.": 0,
    "PASS WITH LIMITATION": 1,
    "PARTIAL": 2,
    "BLOCKED": 3,
}


@dataclass
class Metrics:
    words: int
    h2: int
    h3: int
    tables: int
    source_ids: int


@dataclass
class Finding:
    severity: str
    code: str
    message: str


def read_text(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


def report_metrics(text: str) -> Metrics:
    lines = text.splitlines()
    latin_words = re.findall(r"[A-Za-z0-9]+(?:[._'-][A-Za-z0-9]+)*", text)
    cjk_characters = re.findall(r"[\u3400-\u4DBF\u4E00-\u9FFF]", text)
    return Metrics(
        words=len(latin_words) + (len(cjk_characters) + 1) // 2,
        h2=sum(line.startswith("## ") for line in lines),
        h3=sum(line.startswith("### ") for line in lines),
        tables=sum(bool(TABLE_SEPARATOR_RE.match(line)) for line in lines),
        source_ids=len(set(SOURCE_ID_RE.findall(text))),
    )


def coverage_states(text: str) -> set[str]:
    states: set[str] = set()
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip().lower() for cell in line.strip("|").split("|")]
        states.update(cell for cell in cells if cell in VALID_COVERAGE_STATES)
    return states


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--source-index", type=Path)
    parser.add_argument("--evidence-ledger", type=Path)
    parser.add_argument("--coverage", type=Path)
    parser.add_argument("--acquisition-log", type=Path)
    parser.add_argument("--validation-log", type=Path)
    parser.add_argument("--release-review", type=Path)
    parser.add_argument("--benchmark", type=Path)
    parser.add_argument("--depth-variance-justification", type=Path)
    parser.add_argument("--full-report", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args()


def validate(args: argparse.Namespace) -> tuple[Metrics, list[Finding], dict[str, float]]:
    findings: list[Finding] = []
    report_text = read_text(args.report)
    metrics = report_metrics(report_text)

    if report_text.count("```") % 2:
        findings.append(Finding("error", "unbalanced_fences", "Markdown code fences are unbalanced."))

    if args.full_report:
        artifact_args = {
            "source_index": args.source_index,
            "evidence_ledger": args.evidence_ledger,
            "coverage": args.coverage,
            "acquisition_log": args.acquisition_log,
            "validation_log": args.validation_log,
            "release_review": args.release_review,
        }
        for name, path in artifact_args.items():
            if path is None or not path.is_file():
                findings.append(Finding("error", f"missing_{name}", f"Full report requires {name.replace('_', '-')} artifact."))

        sanity_floors = {"words": 4000, "h2": 8, "h3": 24, "tables": 12, "source_ids": 10}
        for field, minimum in sanity_floors.items():
            actual = getattr(metrics, field)
            if actual < minimum:
                findings.append(Finding("error", f"low_{field}", f"{field}={actual} is below full-report sanity floor {minimum}; justify a narrower scope instead of declaring a full report."))

    report_ids = set(SOURCE_ID_RE.findall(report_text))
    if args.source_index and args.source_index.is_file():
        source_text = read_text(args.source_index)
        source_ids = set(SOURCE_ID_RE.findall(source_text))
        missing = sorted(report_ids - source_ids)
        if missing:
            findings.append(Finding("error", "unresolved_source_ids", f"Report source IDs absent from source index: {', '.join(missing)}"))
        if not re.search(r"https?://", source_text):
            findings.append(Finding("error", "source_index_without_urls", "Source index contains no original URLs."))

    if args.evidence_ledger and args.evidence_ledger.is_file():
        ledger_text = read_text(args.evidence_ledger)
        if not SOURCE_ID_RE.search(ledger_text):
            findings.append(Finding("error", "evidence_ledger_without_source_ids", "Evidence ledger contains no resolvable source IDs."))

    if args.acquisition_log and args.acquisition_log.is_file():
        acquisition_text = read_text(args.acquisition_log)
        acquisition_lower = acquisition_text.lower()
        field_groups = (
            ("attempt", "尝试", "获取记录"),
            ("question", "问题"),
            ("category", "source type", "类别", "类型"),
            ("result", "outcome", "结果", "结论"),
            ("next", "follow-up", "下一", "后续"),
        )
        visible_fields = sum(
            any(keyword in acquisition_lower for keyword in keywords if keyword.isascii())
            or any(keyword in acquisition_text for keyword in keywords if not keyword.isascii())
            for keywords in field_groups
        )
        if visible_fields < 4:
            findings.append(Finding("error", "acquisition_log_missing_fields", "Acquisition log does not expose enough of attempt, question, source category, result, and next-step fields."))

    if args.coverage and args.coverage.is_file():
        coverage_text = read_text(args.coverage)
        states = coverage_states(coverage_text)
        if "covered" not in states:
            findings.append(Finding("error", "coverage_without_covered", "Coverage matrix has no explicit covered rows."))
        if not ({"unavailable", "unresolved"} & states):
            findings.append(Finding("warning", "coverage_without_gaps", "Coverage matrix has no unavailable or unresolved rows; confirm this is evidence-based."))
        lower = coverage_text.lower()
        if (
            "attempt" not in lower
            and "尝试" not in coverage_text
            and "获取" not in coverage_text
            and not ATTEMPT_ID_RE.search(coverage_text)
        ):
            findings.append(Finding("error", "coverage_without_attempt_refs", "Coverage matrix does not expose acquisition-attempt references."))

    if args.release_review and args.release_review.is_file():
        review_raw = read_text(args.release_review)
        review_text = review_raw.lower()
        decision_match = re.search(
            rf"(?:release\s+(?:decision|status)|final\s+(?:decision|status)|发布(?:决定|状态|结论))[^\n]{{0,100}}(?<![A-Z])({RELEASE_STATUS_RE})(?![A-Z])",
            review_raw,
            re.IGNORECASE,
        )
        if not decision_match:
            findings.append(Finding("error", "review_without_decision", "Release review has no explicit release decision/status with PASS, PARTIAL, or BLOCKED."))
        if args.full_report:
            gate_statuses: dict[str, str] = {}
            for gate in REQUIRED_GATE_LABELS:
                match = re.search(
                    rf"(?<![A-Z0-9]){gate}(?![A-Z0-9])[^\n]{{0,160}}?(?<![A-Z])({GATE_STATUS_RE})(?![A-Z])",
                    review_raw,
                    re.IGNORECASE,
                )
                if match:
                    gate_statuses[gate] = match.group(1).upper()
            missing_gates = [gate for gate in REQUIRED_GATE_LABELS if gate not in gate_statuses]
            if missing_gates:
                findings.append(Finding("error", "review_missing_subgates", "Release review omits a status for mandatory sub-gates: " + ", ".join(missing_gates)))
            if "weakest" not in review_text and "最弱" not in review_raw and "最低" not in review_raw:
                findings.append(Finding("error", "review_without_weakest_gate", "Release review does not identify the weakest mandatory sub-gate."))
            if decision_match and not missing_gates:
                decision = decision_match.group(1).upper()
                weakest = max(STATUS_RANK[status] for status in gate_statuses.values())
                if STATUS_RANK[decision] < weakest:
                    findings.append(Finding("error", "decision_better_than_weakest_gate", f"Release decision {decision} is better than the weakest mandatory sub-gate."))
        if "benchmark" not in review_text and "基准" not in review_raw and args.benchmark:
            findings.append(Finding("error", "review_without_benchmark", "Release review does not discuss the selected benchmark."))

    ratios: dict[str, float] = {}
    if args.benchmark:
        benchmark_metrics = report_metrics(read_text(args.benchmark))
        dimensions = ("words", "h3", "tables", "source_ids")
        for field in dimensions:
            denominator = getattr(benchmark_metrics, field)
            ratios[field] = getattr(metrics, field) / denominator if denominator else 1.0
        low = [field for field, ratio in ratios.items() if ratio < 0.5]
        justification_ok = False
        if args.depth_variance_justification and args.depth_variance_justification.is_file():
            justification_text = read_text(args.depth_variance_justification).strip()
            justification_lower = justification_text.lower()
            has_section_language = (
                "section" in justification_lower
                and ("variance" in justification_lower or "benchmark" in justification_lower)
            ) or (
                ("章节" in justification_text or "逐章" in justification_text)
                and ("偏差" in justification_text or "基准" in justification_text)
            )
            justification_ok = len(justification_text) >= 200 and has_section_language
        if len(low) >= 3 and not justification_ok:
            findings.append(Finding("error", "material_benchmark_depth_variance", "Candidate is below 50% of benchmark in at least three depth diagnostics: " + ", ".join(low) + ". Add a section-by-section justification to the release review."))
        elif low:
            findings.append(Finding("warning", "benchmark_depth_variance", "Candidate is below 50% of benchmark in: " + ", ".join(low)))

    return metrics, findings, ratios


def main() -> int:
    args = parse_args()
    try:
        metrics, findings, ratios = validate(args)
    except (OSError, UnicodeError) as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        return 2

    payload = {
        "report": str(args.report),
        "metrics": asdict(metrics),
        "benchmark_ratios": ratios,
        "findings": [asdict(finding) for finding in findings],
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"report: {args.report}")
        print("metrics: " + ", ".join(f"{key}={value}" for key, value in asdict(metrics).items()))
        if ratios:
            print("benchmark ratios: " + ", ".join(f"{key}={value:.2f}" for key, value in ratios.items()))
        for finding in findings:
            print(f"{finding.severity.upper()} {finding.code}: {finding.message}")
        if not findings:
            print("PASS: no mechanical release findings")

    errors = any(finding.severity == "error" for finding in findings)
    return 1 if args.strict and errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
