"""Prepare and apply an auditable Agent review workflow for PTR candidates."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .review import apply_review_decisions


def _context_record(candidate: dict[str, Any]) -> dict[str, Any]:
    context = candidate.get("report_context") or {}
    member_name = str(context.get("member_name") or "")
    member_id = "-".join(member_name.lower().split()) or str(context.get("document_id") or "")
    filing_date = str(context.get("filing_date") or "")
    for fmt in ("%m/%d/%Y", "%m/%d/%y"):
        try:
            filing_date = datetime.strptime(filing_date, fmt).date().isoformat()
            break
        except ValueError:
            pass
    return {
        "member_id": member_id,
        "member_name": member_name,
        "district": context.get("district") or "",
        "report_id": str(context.get("document_id") or ""),
        "filing_date": filing_date,
    }


def _review_candidates(parse_payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for report in parse_payload.get("reports", []):
        if not isinstance(report, dict):
            continue
        index = report.get("index") or {}
        for candidate in (report.get("parsed") or {}).get("review_queue", []):
            if not isinstance(candidate, dict):
                continue
            item = dict(candidate)
            item["report_context"] = {
                "document_id": report.get("document_id"),
                "year": report.get("year"),
                "path": report.get("path"),
                "report_kind": report.get("report_kind"),
                "amends_report_id": report.get("amends_report_id"),
                "member_name": f"{index.get('first_name', '')} {index.get('last_name', '')}".strip(),
                "district": index.get("district"),
                "filing_date": index.get("filing_date"),
                "filing_type": index.get("filing_type"),
            }
            item["agent_triage"] = "agent_review"
            item["agent_evidence"] = {
                "raw_text": candidate.get("raw_text"),
                "raw_blocks": candidate.get("raw_blocks"),
                "issues": candidate.get("issues", []),
                "ticker_candidates": candidate.get("ticker_candidates", []),
                "amount_range_candidates": candidate.get("amount_range_candidates", []),
            }
            item.update({key: value for key, value in _context_record(item).items() if value})
            candidates.append(item)
    return candidates


def prepare_agent_review(parse_payload: dict[str, Any], *, batch_size: int = 50) -> dict[str, Any]:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    candidates = _review_candidates(parse_payload)
    batches = [{"batch_id": f"batch-{index // batch_size + 1:03d}", "candidates": candidates[index:index + batch_size]} for index in range(0, len(candidates), batch_size)]
    return {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_parse": parse_payload.get("source_manifest"),
        "candidate_count": len(candidates),
        "batch_size": batch_size,
        "batch_count": len(batches),
        "decision_schema": {
            "candidate_id": "string",
            "status": "approved | rejected | needs_more_evidence",
            "ticker": "required for approved",
            "issuer": "required for approved",
            "asset_type": "ST | OP | AB | OT",
            "transaction_code": "P | S | E",
            "amount_range": "required for approved",
            "notes": "evidence-based explanation",
        },
        "instructions": [
            "只依据 candidate 的 raw_text/raw_blocks 和候选字段作判断。",
            "不能凭常识猜测 ticker、金额区间或数量。",
            "证据不足时使用 needs_more_evidence，不要强行 approved。",
            "approved 必须补齐 ticker、issuer、asset_type、transaction_code、amount_range 及报告上下文。",
        ],
        "batches": batches,
    }


def apply_agent_review(packet: dict[str, Any], decisions_payload: dict[str, Any], *, output_path: Path | str | None = None) -> dict[str, Any]:
    candidates = [candidate for batch in packet.get("batches", []) for candidate in batch.get("candidates", []) if isinstance(candidate, dict)]
    review_payload = {"source_file": packet.get("source_parse"), "review_queue": candidates}
    result = apply_review_decisions(review_payload, decisions_payload)
    decision_ids = {str(item.get("candidate_id")) for item in decisions_payload.get("decisions", []) if isinstance(item, dict)}
    candidate_ids = {str(item.get("candidate_id")) for item in candidates if item.get("candidate_id")}
    result["agent_review"] = {
        "packet_schema_version": packet.get("schema_version"),
        "candidate_count": len(candidates),
        "decision_count": len(decision_ids),
        "unreviewed_count": len(candidate_ids - decision_ids),
        "decision_source": decisions_payload.get("source") or "agent",
    }
    if output_path:
        destination = Path(output_path)
        if destination.exists():
            raise FileExistsError(f"refusing to overwrite existing output: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def load_agent_packet(path: Path | str) -> dict[str, Any]:
    """Load an inline packet or a batch manifest with relative file paths."""

    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    batch_entries = payload.get("batches") if isinstance(payload, dict) else None
    if not isinstance(batch_entries, list):
        raise ValueError("agent review packet must contain batches")
    if batch_entries and all(isinstance(item, str) for item in batch_entries):
        batches = []
        for item in batch_entries:
            batch_path = Path(item)
            if not batch_path.is_absolute():
                batch_path = source.parent / batch_path
            batch = json.loads(batch_path.read_text(encoding="utf-8"))
            if not isinstance(batch, dict):
                raise ValueError(f"invalid agent review batch: {batch_path}")
            batches.append(batch)
        payload["batches"] = batches
    return payload


def write_review_batches(packet: dict[str, Any], output_dir: Path | str) -> dict[str, Any]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    batch_paths = []
    for batch in packet.get("batches", []):
        path = destination / f"{batch['batch_id']}.json"
        path.write_text(json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8")
        batch_paths.append(str(path))
    manifest = {key: packet.get(key) for key in ("schema_version", "created_at", "source_parse", "candidate_count", "batch_size", "batch_count", "decision_schema", "instructions")}
    manifest["batches"] = batch_paths
    (destination / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"output_dir": str(destination), "manifest": str(destination / "manifest.json"), "batch_paths": batch_paths, "candidate_count": packet.get("candidate_count", 0), "batch_count": packet.get("batch_count", 0)}
