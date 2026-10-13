#!/usr/bin/env python3
"""Create or apply a user-confirmed archive plan for company research uploads.

Default mode is read-only: it inventories files under the research data inbox
and writes a JSON plan. Applying a plan requires --apply and --mapping. Files
are never overwritten; equal hashes are reported as already archived.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


SKIP_DIRS = {"sec-plans", "official-site", "valuation", "context", "evidence", "monitoring"}
METADATA_NAMES = {
    "research-context.md", "source-index.md", "evidence-ledger.md",
    "acquisition-attempt-log.md", "coverage-matrix.md", "validation-log.md",
    "release-review.md", "official-site-request.json", "archive-plan.json",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def suggestion(path: Path) -> tuple[str, str]:
    parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    suffix = path.suffix.lower()
    if "transcript" in parts or "earningscall" in name or "investorday" in name:
        return "transcripts", "filename/path indicates a transcript or conference record"
    if suffix in {".docx", ".pdf"}:
        return "user-provided", "uploaded document; confirm whether it is a report or third-party source"
    if suffix in {".xlsx", ".xls", ".csv"}:
        return "user-provided", "structured upload; confirm whether it is source data or a working model"
    if "sec" in parts or "10-k" in name or "10-q" in name or "8-k" in name:
        return "sec", "path/name indicates a filing or SEC material"
    if "ir" in parts or "investor" in name or "presentation" in name:
        return "ir", "path/name indicates company IR material"
    return "user-provided", "classification needs user confirmation"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, default=Path("."))
    parser.add_argument("--market", required=True)
    parser.add_argument("--company-id", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--mapping", type=Path, help="Confirmed JSON mapping generated/edited by the user")
    parser.add_argument("--apply", action="store_true", help="Apply mapping; requires --mapping")
    return parser.parse_args()


def inventory(root: Path, sources_root: Path, workspace: Path) -> list[dict]:
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name in METADATA_NAMES:
            continue
        relative_parts = path.relative_to(root).parts
        if relative_parts and relative_parts[0] in SKIP_DIRS:
            continue
        category, reason = suggestion(path)
        relative = path.relative_to(root).as_posix()
        destination = sources_root / category / path.name
        rows.append({
            "source": relative,
            "relative_path": relative,
            "sha256": sha256(path),
            "size_bytes": path.stat().st_size,
            "suggested_category": category,
            "suggestion_reason": reason,
            "destination": destination.relative_to(workspace).as_posix(),
            "destination_relative_path": (sources_root / category / path.name).as_posix(),
            "status": "pending_confirmation",
        })
    return rows


def apply_mapping(mapping_path: Path, workspace: Path, data_root: Path, sources_root: Path) -> list[dict]:
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    if not isinstance(mapping, list):
        raise ValueError("mapping must be a JSON list")
    results = []
    for item in mapping:
        if item.get("status") != "approved":
            results.append({"source": item.get("source"), "status": "skipped"})
            continue
        source = (data_root / item["source"]).resolve()
        destination = (workspace / item["destination"]).resolve()
        if not source.is_file() or data_root.resolve() not in source.parents:
            raise ValueError(f"unsafe or missing source: {item.get('source')}")
        if sources_root.resolve() not in destination.parents:
            raise ValueError(f"destination must be under sources root: {item.get('destination')}")
        source_hash = sha256(source)
        if item.get("sha256") and item["sha256"] != source_hash:
            raise ValueError(f"source changed since plan: {item['source']}")
        if destination.exists():
            if destination.is_file() and sha256(destination) == source_hash:
                results.append({"source": item["source"], "destination": item["destination"], "status": "already_archived"})
                continue
            raise FileExistsError(f"refusing to overwrite existing destination: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        results.append({"source": item["source"], "destination": item["destination"], "status": "moved", "sha256": source_hash})
    return results


def main() -> int:
    args = parse_args()
    workspace = args.workspace_root.resolve()
    data_root = workspace / "research" / "companies" / args.market / args.company_id / "data"
    sources_root = workspace / "sources" / "companies" / args.market / args.company_id
    if not data_root.is_dir():
        raise SystemExit(f"research data root missing: {data_root}")
    if args.apply and not args.mapping:
        raise SystemExit("--apply requires --mapping after user confirmation")
    if args.apply:
        result = apply_mapping(args.mapping.resolve(), workspace, data_root, sources_root)
        print(json.dumps({"status": "APPLIED", "results": result}, ensure_ascii=False, indent=2))
        return 0
    rows = inventory(data_root, sources_root, workspace)
    output = (args.output or (data_root / "archive-plan.json")).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "company-archive-plan.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "company_id": args.company_id,
        "data_root": data_root.relative_to(workspace).as_posix(),
        "sources_root": sources_root.relative_to(workspace).as_posix(),
        "user_confirmation_required": True,
        "items": rows,
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    plan_display = output.relative_to(workspace).as_posix() if workspace in output.parents else str(output)
    print(json.dumps({"status": "PLAN_ONLY", "plan": plan_display, "items": len(rows)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
