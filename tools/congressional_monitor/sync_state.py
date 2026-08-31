"""Persistent state and deterministic diffs for congressional sync runs."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


STATE_SCHEMA_VERSION = 1
OPERATIONAL_STATUSES = {"discovered", "existing", "downloaded", "download_failed", "ocr_failed", "review_ready"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _candidate_summary(report: dict[str, Any]) -> dict[str, Any]:
    if isinstance(report.get("candidate_summary"), dict):
        summary = report["candidate_summary"]
        return {
            "candidate_ids": sorted(str(item) for item in summary.get("candidate_ids", []) if item),
            "review_candidate_ids": sorted(str(item) for item in summary.get("review_candidate_ids", []) if item),
            "validated_candidate_ids": sorted(str(item) for item in summary.get("validated_candidate_ids", []) if item),
            "candidate_count": int(summary.get("candidate_count", 0)),
            "review_count": int(summary.get("review_count", 0)),
            "validated_count": int(summary.get("validated_count", 0)),
        }
    parsed = report.get("parsed") or {}
    candidates = [item for page in parsed.get("pages", []) for item in page.get("candidates", [])] if isinstance(parsed, dict) else []
    candidate_ids = sorted(str(item.get("candidate_id")) for item in candidates if item.get("candidate_id"))
    review_ids = sorted(str(item.get("candidate_id")) for item in candidates if item.get("review_required") and item.get("candidate_id"))
    validated_ids = sorted(str(item.get("candidate_id")) for item in candidates if item.get("valid_for_curated") and item.get("candidate_id"))
    return {
        "candidate_ids": candidate_ids,
        "review_candidate_ids": review_ids,
        "validated_candidate_ids": validated_ids,
        "candidate_count": len(candidate_ids),
        "review_count": len(review_ids),
        "validated_count": len(validated_ids),
    }


def _report_key(report: dict[str, Any]) -> str:
    return str(report.get("document_id") or f"{report.get('year', '')}:{report.get('document_id', '')}")


def build_state(sync_result: dict[str, Any], *, generated_at: str | None = None) -> dict[str, Any]:
    """Reduce a sync result to stable, diffable report metadata."""

    reports: dict[str, dict[str, Any]] = {}
    for report in sync_result.get("reports", []):
        if not isinstance(report, dict):
            continue
        index = report.get("index") or {}
        candidate_summary = _candidate_summary(report)
        reports[_report_key(report)] = {
            "document_id": report.get("document_id"),
            "year": report.get("year"),
            "filing_date": index.get("filing_date"),
            "district": index.get("district"),
            "first_name": index.get("first_name"),
            "last_name": index.get("last_name"),
            "filing_type": index.get("filing_type"),
            "report_kind": report.get("report_kind") or ("amendment" if str(index.get("filing_type", "")).upper() == "A" else "original"),
            "amends_report_id": report.get("amends_report_id") or index.get("amends_report_id") or None,
            "lineage_status": report.get("lineage_status"),
            "status": report.get("status"),
            "path": report.get("path"),
            "sha256": report.get("sha256"),
            "bytes": report.get("bytes"),
            "text_layer": report.get("text_layer"),
            **candidate_summary,
            "error": report.get("error"),
        }
    scope = {
        "index_file": sync_result.get("index_file"),
        "member": sync_result.get("member"),
        "requested_count": sync_result.get("requested_count"),
        "limit": sync_result.get("limit"),
        "filing_types": sync_result.get("filing_types"),
    }
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "generated_at": generated_at or utc_now(),
        "scope": scope,
        "report_count": len(reports),
        "reports": reports,
    }


def load_state(path: Path | str) -> dict[str, Any] | None:
    source = Path(path)
    if not source.exists():
        return None
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid sync state JSON: {source}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != STATE_SCHEMA_VERSION or not isinstance(payload.get("reports"), dict):
        raise ValueError(f"unsupported sync state file: {source}")
    # Stage-one states used ``year:document_id``. Normalize them in memory so
    # upgrading does not re-report every already-seen document as new.
    normalized_reports: dict[str, Any] = {}
    for key, report in payload["reports"].items():
        document_id = str(report.get("document_id") or key.split(":", 1)[-1]) if isinstance(report, dict) else str(key)
        normalized_reports[document_id] = report
    payload["reports"] = normalized_reports
    return payload


def write_state(path: Path | str, state: dict[str, Any]) -> None:
    """Atomically write derived state, creating parent directories."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(destination)


def _business_signature(report: dict[str, Any]) -> tuple[Any, ...]:
    """Fields that represent a report/data change, excluding transient status/path."""

    filing_type = str(report.get("filing_type") or "").upper()
    report_kind = report.get("report_kind") or ("amendment" if filing_type == "A" else "original")
    lineage_status = report.get("lineage_status") or ("unlinked_amendment" if report_kind == "amendment" else "original")
    return (
        report.get("filing_date"), report.get("district"), report.get("first_name"), report.get("last_name"),
        report.get("filing_type"), report.get("sha256"), report.get("bytes"),
        report_kind, report.get("amends_report_id"), lineage_status,
        tuple(report.get("candidate_ids") or ()), tuple(report.get("review_candidate_ids") or ()),
        tuple(report.get("validated_candidate_ids") or ()), report.get("error"),
    )


def diff_states(previous: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, Any]:
    """Return report and candidate changes between two sync states."""

    old_reports = (previous or {}).get("reports", {})
    new_reports = current.get("reports", {})
    old_keys, new_keys = set(old_reports), set(new_reports)
    new_report_keys = sorted(new_keys - old_keys)
    removed_report_keys = sorted(old_keys - new_keys)
    changed_report_keys = sorted(key for key in old_keys & new_keys if _business_signature(old_reports[key]) != _business_signature(new_reports[key]))
    status_changes = sorted(
        ({"key": key, "from": old_reports[key].get("status"), "to": new_reports[key].get("status")}
         for key in old_keys & new_keys
         if old_reports[key].get("status") != new_reports[key].get("status")),
        key=lambda item: item["key"],
    )

    old_candidates = {candidate_id for report in old_reports.values() for candidate_id in report.get("candidate_ids", [])}
    new_candidates = {candidate_id for report in new_reports.values() for candidate_id in report.get("candidate_ids", [])}
    new_candidate_ids = sorted(new_candidates - old_candidates)
    removed_candidate_ids = sorted(old_candidates - new_candidates)
    first_run = previous is None
    # A bounded/member-filtered sync cannot safely infer removals from the index.
    scope = current.get("scope", {})
    def _scope_value(value: Any) -> tuple[str, ...]:
        if isinstance(value, (list, tuple)):
            return tuple(sorted(str(item) for item in value))
        return (str(value),) if value not in (None, "") else ()

    comparable_scope = bool(
        previous
        and _scope_value(previous.get("scope", {}).get("index_file")) == _scope_value(scope.get("index_file"))
        and previous.get("scope", {}).get("member") == scope.get("member")
        and previous.get("scope", {}).get("limit") == scope.get("limit")
        and _scope_value(previous.get("scope", {}).get("filing_types")) == _scope_value(scope.get("filing_types"))
    )
    return {
        "first_run": first_run,
        "previous_generated_at": (previous or {}).get("generated_at"),
        "current_generated_at": current.get("generated_at"),
        "new_reports": [new_reports[key] for key in new_report_keys],
        "changed_reports": [new_reports[key] for key in changed_report_keys],
        "removed_reports": [old_reports[key] for key in removed_report_keys] if comparable_scope else [],
        "status_changes": status_changes,
        "new_candidate_ids": new_candidate_ids,
        "removed_candidate_ids": removed_candidate_ids if comparable_scope else [],
        "counts": {
            "new_reports": len(new_report_keys),
            "changed_reports": len(changed_report_keys),
            "removed_reports": len(removed_report_keys) if comparable_scope else 0,
            "status_changes": len(status_changes),
            "new_candidates": len(new_candidate_ids),
            "removed_candidates": len(removed_candidate_ids) if comparable_scope else 0,
        },
    }
