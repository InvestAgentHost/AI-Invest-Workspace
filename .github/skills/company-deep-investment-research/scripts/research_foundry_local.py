#!/usr/bin/env python3
"""Portable bridge for the bundled ResearchFoundry data and research primitives.

The bridge is intended for the terminal harness, not as a second research
runtime. It keeps command output JSON-serializable and leaves semantic planning
and user confirmation to the calling skill.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
from datetime import date
import importlib
import json
import os
from pathlib import Path
import sys
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
VENDOR_ROOT = SKILL_ROOT / "vendor"
if str(VENDOR_ROOT) not in sys.path:
    sys.path.insert(0, str(VENDOR_ROOT))


def _json_default(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=_json_default))


def _load_json(path: Path) -> Any:
    return json.loads(path.expanduser().resolve().read_text(encoding="utf-8"))


def _load_document(path: Path) -> Any:
    """Load JSON by default and YAML for human-edited request documents."""

    text = path.expanduser().resolve().read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import yaml

        value = yaml.safe_load(text)
        if value is None:
            raise ValueError(f"request document is empty: {path}")
        return value


def _write_json(path: Path, value: Any) -> None:
    destination = path.expanduser().resolve()
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite existing file: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=_json_default) + "\n",
        encoding="utf-8",
    )


def _record_output(record: Any) -> dict[str, Any]:
    payload = record.model_dump(mode="json") if hasattr(record, "model_dump") else _json_default(record)
    return payload


def _transcript_parser(sub: argparse._SubParsersAction) -> None:
    transcript = sub.add_parser("transcript", help="prepare manually supplied transcript files")
    commands = transcript.add_subparsers(dest="transcript_command", required=True)

    plan = commands.add_parser("plan")
    plan.add_argument("source", type=Path)
    plan.add_argument("--target", required=True)
    plan.add_argument("--event-date", required=True)
    plan.add_argument(
        "--event-type",
        required=True,
        choices=("earnings_call", "fireside_chat", "investor_meeting", "roadshow", "conference", "other"),
    )
    plan.add_argument("--fiscal-period")
    plan.add_argument("--workspace", required=True, type=Path)
    plan.add_argument("--provider", default="local")
    plan.add_argument("--provider-record-id")
    plan.add_argument("--provenance", type=Path)
    plan.add_argument("--source-title")
    plan.add_argument("--source-representation", choices=("raw_transcript", "provider_prepared_minutes"), default="raw_transcript")
    plan.add_argument("--confirm", action="store_true")
    plan.add_argument("--output", required=True, type=Path)

    template = commands.add_parser("metadata-template")
    template.add_argument("--output", required=True, type=Path)
    template.add_argument("--source", default="")
    template.add_argument("--target", default="")
    template.add_argument("--event-date", default="")
    template.add_argument("--event-type", default="")
    template.add_argument("--fiscal-period", default="")
    template.add_argument("--workspace", default="")

    metadata = commands.add_parser("plan-metadata")
    metadata.add_argument("metadata", type=Path)
    metadata.add_argument("--confirm", action="store_true")
    metadata.add_argument("--output", required=True, type=Path)

    run = commands.add_parser("run")
    run.add_argument("plan", type=Path)

    publish = commands.add_parser("publish")
    publish.add_argument("run_id")
    publish.add_argument("--workspace", required=True, type=Path)

    inspect = commands.add_parser("inspect")
    inspect.add_argument("run_id")
    inspect.add_argument("--workspace", required=True, type=Path)

    check = commands.add_parser("check")
    check.add_argument("--output", required=True, type=Path)
    check.add_argument("--source", type=Path)


def _sec_parser(sub: argparse._SubParsersAction) -> None:
    ten_k = sub.add_parser("ten-k", help="acquire and index SEC native HTML filings")
    commands = ten_k.add_subparsers(dest="ten_k_command", required=True)
    sec = commands.add_parser("sec-html")
    sec_commands = sec.add_subparsers(dest="sec_html_command", required=True)

    plan = sec_commands.add_parser("plan")
    plan.add_argument("reference")
    plan.add_argument("--accession")
    plan.add_argument("--target", required=True)
    plan.add_argument("--workspace", required=True, type=Path)
    plan.add_argument("--fiscal-year", type=int)
    plan.add_argument("--user-agent", required=True)
    plan.add_argument("--no-assets", action="store_true")
    plan.add_argument("--confirm", action="store_true")
    plan.add_argument("--output", required=True, type=Path)

    run = sec_commands.add_parser("run")
    run.add_argument("plan", type=Path)

    index = sec_commands.add_parser("index")
    index.add_argument("package", type=Path)
    index.add_argument("--output", type=Path)
    index.add_argument("--max-chunk-chars", type=int, default=8000)

    search = sec_commands.add_parser("search")
    search.add_argument("index", type=Path)
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=20)
    search.add_argument("--kind", choices=("all", "chunks", "tables", "sections"), default="all")

    read = sec_commands.add_parser("read")
    read.add_argument("package", type=Path)
    read.add_argument("--start-line", required=True, type=int)
    read.add_argument("--end-line", required=True, type=int)


def _official_parser(sub: argparse._SubParsersAction) -> None:
    official = sub.add_parser("official-site", help="acquire and validate official website evidence")
    commands = official.add_subparsers(dest="official_site_command", required=True)

    plan = commands.add_parser("plan")
    plan.add_argument("request", type=Path)
    plan.add_argument("--output", required=True, type=Path)

    run = commands.add_parser("run")
    run.add_argument("plan", type=Path)

    review = commands.add_parser("review-coverage")
    review.add_argument("run_id")
    review.add_argument("--workspace", required=True, type=Path)
    review.add_argument("--input", required=True, type=Path)

    publish = commands.add_parser("publish")
    publish.add_argument("run_id")
    publish.add_argument("--workspace", required=True, type=Path)

    inspect = commands.add_parser("inspect")
    inspect.add_argument("run_id")
    inspect.add_argument("--workspace", required=True, type=Path)

    retry = commands.add_parser("retry")
    retry.add_argument("run_id")
    retry.add_argument("--workspace", required=True, type=Path)

    ingest = commands.add_parser("ingest")
    ingest.add_argument("run_id")
    ingest.add_argument("--workspace", required=True, type=Path)
    ingest.add_argument("--input", required=True, type=Path)

    reprepare = commands.add_parser("reprepare")
    reprepare.add_argument("run_id")
    reprepare.add_argument("--workspace", required=True, type=Path)
    reprepare.add_argument("--source-id", action="append", default=[])
    reprepare.add_argument("--low-content-only", action="store_true")

    search = commands.add_parser("search")
    search.add_argument("snapshot", type=Path)
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=20)
    search.add_argument("--kind", choices=("all", "chunks", "tables", "sections"), default="all")

    read = commands.add_parser("read")
    read.add_argument("snapshot", type=Path)
    read.add_argument("source")
    read.add_argument("--start-line", required=True, type=int)
    read.add_argument("--end-line", required=True, type=int)


def _research_parser(sub: argparse._SubParsersAction) -> None:
    research = sub.add_parser("research", help="initialize, validate, and publish research contracts")
    commands = research.add_subparsers(dest="research_command", required=True)

    init = commands.add_parser("init")
    init.add_argument("brief", type=Path)
    init.add_argument("--workspace", required=True, type=Path)

    validate = commands.add_parser("validate")
    validate.add_argument("research_root", type=Path)
    validate.add_argument("--workspace", required=True, type=Path)

    publish = commands.add_parser("publish")
    publish.add_argument("research_root", type=Path)
    publish.add_argument("--workspace", required=True, type=Path)

    capture = commands.add_parser("capture-source")
    capture.add_argument("research_root", type=Path)
    capture.add_argument("metadata", type=Path)
    capture.add_argument("--source", required=True, type=Path)
    capture.add_argument("--workspace", required=True, type=Path)
    capture.add_argument("--prepared", type=Path)


def _doctor(args: argparse.Namespace) -> int:
    checks: dict[str, Any] = {
        "python": {"version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", "required": "3.12+", "ok": sys.version_info >= (3, 12)},
        "vendor_root": {"path": str(VENDOR_ROOT), "ok": VENDOR_ROOT.is_dir()},
        "network": {"configured": os.environ.get("WEB_SEARCH", "live"), "note": "network is supplied by terminal configuration"},
        "excluded_capabilities": {"status": "not bundled", "items": ["model-specific OCR executors", "third-party data-provider adapters"]},
    }
    dependencies = {
        "pydantic": "pydantic",
        "yaml": "yaml",
        "httpx": "httpx",
        "PyMuPDF": "fitz",
        "xlsxwriter": "xlsxwriter",
    }
    checks["dependencies"] = {}
    for name, module in dependencies.items():
        try:
            importlib.import_module(module)
            checks["dependencies"][name] = {"ok": True}
        except Exception as error:  # noqa: BLE001
            checks["dependencies"][name] = {"ok": False, "error": f"{type(error).__name__}: {error}"}
    imports = (
        "research_foundry.preprocessing.capabilities.ten_k.sources.sec_html",
        "research_foundry.preprocessing.capabilities.official_site",
        "research_foundry.preprocessing.capabilities.transcripts",
        "research_foundry.research",
    )
    checks["bundled_imports"] = {}
    for name in imports:
        try:
            importlib.import_module(name)
            checks["bundled_imports"][name] = {"ok": True}
        except Exception as error:  # noqa: BLE001
            checks["bundled_imports"][name] = {"ok": False, "error": f"{type(error).__name__}: {error}"}
    if args.workspace:
        from research_foundry.runtime.workspace import Workspace

        workspace = Workspace.from_path(args.workspace)
        try:
            workspace.ensure_layout()
            checks["workspace"] = {"path": str(workspace.root), "ok": True}
        except OSError as error:
            checks["workspace"] = {"path": str(workspace.root), "ok": False, "error": str(error)}
    checks["ok"] = all(
        item.get("ok", True)
        for group in checks.values()
        if isinstance(group, dict)
        for item in (group.values() if group is checks.get("dependencies") or group is checks.get("bundled_imports") else (group,))
        if isinstance(item, dict) and "ok" in item
    )
    _print(checks)
    return 0 if checks["ok"] else 1


def _transcript(args: argparse.Namespace) -> int:
    from research_foundry.preprocessing.capabilities.transcripts import (
        build_transcript_plan,
        build_transcript_plan_from_metadata,
        inspect_transcript_run,
        publish_transcript_run,
        start_transcript_run,
        validate_cleaned_transcript,
        write_transcript_metadata_template,
    )
    from research_foundry.preprocessing.capabilities.transcripts.planning import TranscriptPlan

    if args.transcript_command == "plan":
        plan = build_transcript_plan(
            args.source,
            target_name=args.target,
            event_date=date.fromisoformat(args.event_date),
            event_type=args.event_type,
            workspace_root=args.workspace,
            fiscal_period=args.fiscal_period,
            provider=args.provider,
            provider_record_id=args.provider_record_id,
            provenance_path=args.provenance,
            source_representation=args.source_representation,
            source_title=args.source_title,
            confirmed=args.confirm,
        )
        _write_json(args.output, plan)
        _print(plan)
        return 0
    if args.transcript_command == "metadata-template":
        path = write_transcript_metadata_template(
            args.output,
            source_path=args.source,
            target_name=args.target,
            event_date_value=args.event_date,
            event_type=args.event_type,
            fiscal_period=args.fiscal_period,
            workspace_root=args.workspace,
        )
        _print({"path": path})
        return 0
    if args.transcript_command == "plan-metadata":
        plan = build_transcript_plan_from_metadata(args.metadata, confirmed=args.confirm)
        _write_json(args.output, plan)
        _print(plan)
        return 0
    if args.transcript_command == "run":
        plan = TranscriptPlan.model_validate_json(args.plan.read_text(encoding="utf-8"))
        _print(start_transcript_run(plan))
        return 0
    if args.transcript_command == "publish":
        record, destination = publish_transcript_run(args.workspace, args.run_id)
        _print({"record": record, "artifact_directory": destination})
        return 0
    if args.transcript_command == "inspect":
        _print(inspect_transcript_run(args.workspace, args.run_id))
        return 0
    source = args.source.resolve() if args.source else None
    result = validate_cleaned_transcript(source, args.output.resolve())
    _print(result)
    return 0 if result.usable else 1


def _sec(args: argparse.Namespace) -> int:
    from research_foundry.preprocessing.capabilities.ten_k.indexing import (
        materialize_index,
        read_markdown_lines,
        search_index,
    )
    from research_foundry.preprocessing.capabilities.ten_k.sources.sec_html.execution import (
        build_sec_html_plan,
        execute_sec_html_plan,
    )

    if args.sec_html_command == "plan":
        plan = build_sec_html_plan(
            reference=args.reference,
            accession=args.accession,
            target_name=args.target,
            workspace_root=args.workspace,
            fiscal_year=args.fiscal_year,
            user_agent=args.user_agent,
            confirmed=args.confirm,
            download_assets=not args.no_assets,
        )
        _write_json(args.output, plan)
        _print(plan)
        return 0
    if args.sec_html_command == "run":
        _print(execute_sec_html_plan(_load_json(args.plan)))
        return 0
    if args.sec_html_command == "index":
        _print(materialize_index(args.package, output_root=args.output, max_chunk_chars=args.max_chunk_chars))
        return 0
    if args.sec_html_command == "search":
        _print(search_index(args.index, args.query, limit=args.limit, kind=args.kind))
        return 0
    _print(read_markdown_lines(args.package, args.start_line, args.end_line))
    return 0


def _official(args: argparse.Namespace) -> int:
    from research_foundry.preprocessing.capabilities.official_site import (
        OfficialSiteCoverageReview,
        OfficialSiteRequest,
        OfficialSiteSourceImport,
        build_official_site_plan,
        execute_official_site_plan,
        ingest_official_site_source,
        inspect_official_site_run,
        publish_official_site_run,
        read_official_site_lines,
        reprepare_official_site_sources,
        retry_official_site_failures,
        review_official_site_coverage,
        search_official_site_index,
    )

    command = args.official_site_command
    if command == "plan":
        plan = build_official_site_plan(OfficialSiteRequest.model_validate(_load_document(args.request)))
        _write_json(args.output, plan)
        _print(plan)
    elif command == "run":
        _print(execute_official_site_plan(_load_document(args.plan)))
    elif command == "review-coverage":
        _print(review_official_site_coverage(args.workspace, args.run_id, OfficialSiteCoverageReview.model_validate(_load_document(args.input))))
    elif command == "publish":
        record, destination = publish_official_site_run(args.workspace, args.run_id)
        _print({"record": record, "artifact_directory": destination})
    elif command == "inspect":
        _print(inspect_official_site_run(args.workspace, args.run_id))
    elif command == "retry":
        _print(retry_official_site_failures(args.workspace, args.run_id))
    elif command == "ingest":
        _print(ingest_official_site_source(args.workspace, args.run_id, OfficialSiteSourceImport.model_validate(_load_document(args.input))))
    elif command == "reprepare":
        _print(reprepare_official_site_sources(args.workspace, args.run_id, source_ids=args.source_id, low_content_only=args.low_content_only))
    elif command == "search":
        _print(search_official_site_index(args.snapshot / "index", args.query, limit=args.limit, kind=args.kind))
    else:
        _print(read_official_site_lines(args.snapshot, args.source, args.start_line, args.end_line))
    return 0


def _research(args: argparse.Namespace) -> int:
    from research_foundry.research import (
        capture_research_source,
        load_source_metadata,
        initialize_research_workspace,
        publish_research,
        validate_research,
    )
    from research_foundry.research.contracts import ResearchBrief

    if args.research_command == "init":
        brief_payload = _load_document(args.brief)
        brief = ResearchBrief.model_validate(brief_payload)
        _print(initialize_research_workspace(args.workspace, brief))
        return 0
    if args.research_command == "validate":
        result = validate_research(args.research_root, workspace_root=args.workspace)
        _print(result)
        return 0 if result.valid else 1
    if args.research_command == "publish":
        _print(publish_research(args.research_root, workspace_root=args.workspace))
        return 0
    metadata = load_source_metadata(args.metadata)
    _print(capture_research_source(args.research_root, metadata, source_path=args.source, prepared_path=args.prepared, workspace_root=args.workspace))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="research_foundry_local")
    sub = parser.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor", help="check bundled runtime and terminal prerequisites")
    doctor.add_argument("--workspace", type=Path)
    _transcript_parser(sub)
    _sec_parser(sub)
    _official_parser(sub)
    _research_parser(sub)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        return _doctor(args)
    if args.command == "transcript":
        return _transcript(args)
    if args.command == "ten-k":
        return _sec(args)
    if args.command == "official-site":
        return _official(args)
    if args.command == "research":
        return _research(args)
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
