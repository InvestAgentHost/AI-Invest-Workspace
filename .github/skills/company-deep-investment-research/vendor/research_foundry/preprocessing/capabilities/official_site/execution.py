"""Acquire official-site sources in Agent-reviewed batches."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import time
from typing import Any
from urllib.parse import urlsplit

from research_foundry.runtime.artifacts import hash_file
from research_foundry.runtime.run_records import (
    RunRecord,
    create_run,
    load_run_record,
    write_run_record,
)
from research_foundry.runtime.workspace import Workspace

from .discovery import (
    extract_approved_links,
    initial_urls,
    is_approved_url,
    normalize_url,
    sitemap_urls,
)
from .fetching import Fetcher, HttpOfficialSiteFetcher, OfficialSiteFetchError
from .indexing import build_official_site_index
from .models import (
    OfficialSiteCoverageReview,
    OfficialSitePlan,
    OfficialSiteSourceImport,
    SourceRecord,
)
from .planning import load_official_site_plan
from .preparation import analyze_prepared_markdown, html_to_markdown, pdf_to_markdown


class OfficialSiteExecutionError(RuntimeError):
    """Raised when an official-site run cannot continue safely."""


# These are infrastructure guardrails, not research targets or user-facing tuning.
_MAX_TOTAL_REQUESTS = 800
_MAX_URLS_PER_BATCH = 120
_REQUESTS_PER_SECOND = 1.0
_MAX_RESPONSE_BYTES = 25_000_000

_DATA_SUFFIXES = {".csv", ".json", ".xlsx", ".xls"}
_EXCLUDED_PATH_MARKERS = {
    "annual-report",
    "annual-reports",
    "quarterly-report",
    "quarterly-reports",
    "financial-report",
    "financial-reports",
    "financial-results",
    "sec-filing",
    "sec-filings",
    "regulatory-filing",
    "regulatory-filings",
    "10-k",
    "10q",
    "10-q",
}


def execute_official_site_plan(
    plan: OfficialSitePlan | str | Path,
    *,
    fetcher: Fetcher | None = None,
) -> RunRecord:
    """Start a run by acquiring only the Agent-selected entry URLs."""

    parsed = load_official_site_plan(plan) if isinstance(plan, (str, Path)) else plan
    if parsed.status != "ready" or parsed.agent_review.decision != "approved":
        raise OfficialSiteExecutionError("official-site plan is not Agent-approved")
    workspace = Workspace.from_path(parsed.workspace_root)
    workspace.ensure_layout()
    record = create_run(
        workspace.root,
        "official_site",
        {"schema_version": parsed.schema_version, "plan": parsed.model_dump(mode="json")},
    )
    run_directory = workspace.runs / record.run_id
    snapshot = run_directory / "snapshot"
    for relative in (
        "raw/pages",
        "raw/documents",
        "raw/data",
        "prepared/pages",
        "prepared/documents",
        "prepared/agent",
        "provenance/scripts",
        "deliverables",
        "data",
    ):
        (snapshot / relative).mkdir(parents=True, exist_ok=False)
    for relative in ("imports/raw", "imports/prepared", "scripts", "diagnostics"):
        (run_directory / "workbench" / relative).mkdir(parents=True, exist_ok=False)
    (run_directory / "plan.json").write_text(
        parsed.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )

    state = _new_crawl_state()
    sources: list[SourceRecord] = []
    failures: list[dict[str, str]] = []
    _acquire_batch(
        parsed,
        run_directory,
        snapshot,
        state,
        sources,
        failures,
        initial_urls(parsed.official_domains, parsed.seed_urls),
        fetcher=fetcher,
    )
    if not sources and not state["candidates"]:
        _persist_working_corpus(snapshot, state, sources)
        return _mark_failed(record, workspace, snapshot, state, failures)
    return _mark_awaiting_coverage_review(
        record, workspace, snapshot, state, sources, failures
    )


def review_official_site_coverage(
    workspace_root: str | Path,
    run_id: str,
    review: OfficialSiteCoverageReview | dict[str, Any] | str | Path,
    *,
    fetcher: Fetcher | None = None,
) -> RunRecord:
    """Apply one Agent coverage decision and keep the same unpublished snapshot."""

    workspace = Workspace.from_path(workspace_root)
    record = load_run_record(workspace.root, run_id)
    if record.capability != "official_site" or record.status not in {
        "awaiting_coverage_review",
        "needs_recovery",
    }:
        raise OfficialSiteExecutionError(
            "official-site coverage can only be reviewed before synthesis"
        )
    parsed_review = _load_coverage_review(review)
    plan = OfficialSitePlan.model_validate(record.input_manifest["plan"])
    snapshot = (workspace.runs / run_id / "snapshot").resolve()
    state = _load_crawl_state(snapshot)
    sources = _load_sources(snapshot)
    failures = list(record.items[0].get("failed_urls", []))

    normalized_urls: list[str] = []
    for value in parsed_review.selected_urls:
        url = normalize_url(value)
        if not is_approved_url(url, plan.official_domains):
            raise OfficialSiteExecutionError(
                f"coverage URL is outside approved official domains: {url}"
            )
        if _excluded_financial_url(url):
            raise OfficialSiteExecutionError(f"coverage URL is excluded by scope: {url}")
        if url in state["attempted_urls"]:
            raise OfficialSiteExecutionError(
                f"coverage URL was already attempted; use retry for a recorded failure: {url}"
            )
        if url not in normalized_urls:
            normalized_urls.append(url)

    review_payload = parsed_review.model_dump(mode="json")
    review_payload["selected_urls"] = normalized_urls
    review_payload["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    if parsed_review.decision == "complete" and not any(
        source.status == "prepared" for source in sources
    ):
        raise OfficialSiteExecutionError(
            "coverage cannot be completed without a prepared official source"
        )
    if parsed_review.decision == "complete":
        _validate_coverage_assessment(plan, parsed_review, sources)
    if len(normalized_urls) > _MAX_URLS_PER_BATCH:
        raise OfficialSiteExecutionError(
            f"Agent batch exceeds hard guardrail of {_MAX_URLS_PER_BATCH} URLs"
        )
    if int(state["requests_made"]) + len(normalized_urls) > _MAX_TOTAL_REQUESTS:
        raise OfficialSiteExecutionError(
            f"run exceeds hard guardrail of {_MAX_TOTAL_REQUESTS} requests"
        )
    state["coverage_reviews"].append(review_payload)
    _event(
        workspace.runs / run_id,
        "coverage_reviewed",
        {
            "decision": parsed_review.decision,
            "selected_url_count": len(normalized_urls),
            "material_gap_count": len(parsed_review.material_gaps),
        },
    )

    if parsed_review.decision == "complete":
        _write_crawl_state(snapshot, state)
        recovery_sources = _recovery_source_ids(
            sources, parsed_review.non_material_source_reasons
        )
        if recovery_sources:
            return _mark_needs_recovery(
                record,
                workspace,
                snapshot,
                state,
                sources,
                failures,
                recovery_sources,
            )
        return _finalize_coverage(record, workspace, snapshot, state, sources, failures)

    _acquire_batch(
        plan,
        workspace.runs / run_id,
        snapshot,
        state,
        sources,
        failures,
        normalized_urls,
        fetcher=fetcher,
    )
    return _mark_awaiting_coverage_review(
        record, workspace, snapshot, state, sources, failures
    )


def retry_official_site_failures(
    workspace_root: str | Path,
    run_id: str,
    *,
    fetcher: Fetcher | None = None,
) -> RunRecord:
    """Retry one bounded batch of recorded failures before synthesis begins."""

    workspace = Workspace.from_path(workspace_root)
    record = load_run_record(workspace.root, run_id)
    allowed = {"awaiting_coverage_review", "awaiting_synthesis", "needs_recovery", "failed"}
    if record.capability != "official_site" or record.status not in allowed:
        raise OfficialSiteExecutionError(
            "official-site failures can only be retried before publication"
        )
    snapshot = (workspace.runs / run_id / "snapshot").resolve()
    if record.status == "awaiting_synthesis" and _synthesis_started(snapshot):
        raise OfficialSiteExecutionError(
            "retry must run before Agent synthesis modifies deliverables"
        )
    failures = list(record.items[0].get("failed_urls", []))
    if not failures:
        return record
    plan = OfficialSitePlan.model_validate(record.input_manifest["plan"])
    state = _load_crawl_state(snapshot)
    sources = _load_sources(snapshot)
    capacity = min(
        _MAX_URLS_PER_BATCH,
        _MAX_TOTAL_REQUESTS - int(state["requests_made"]),
    )
    if capacity <= 0:
        raise OfficialSiteExecutionError("official-site hard request guardrail reached")
    selected_failures = failures[:capacity]
    remaining_failures = failures[capacity:]
    retried_failures: list[dict[str, str]] = []
    _acquire_batch(
        plan,
        workspace.runs / run_id,
        snapshot,
        state,
        sources,
        retried_failures,
        [str(item.get("url", "")) for item in selected_failures],
        fetcher=fetcher,
        allow_retry=True,
    )
    failures = remaining_failures + retried_failures
    if not sources and not state["candidates"]:
        _persist_working_corpus(snapshot, state, sources)
        return _mark_failed(record, workspace, snapshot, state, failures)
    # New evidence invalidates the previous coverage decision, so the Agent reviews again.
    return _mark_awaiting_coverage_review(
        record, workspace, snapshot, state, sources, failures
    )


def ingest_official_site_source(
    workspace_root: str | Path,
    run_id: str,
    source_import: OfficialSiteSourceImport | dict[str, Any] | str | Path,
) -> RunRecord:
    """Freeze one Agent-acquired workbench source into an unpublished snapshot."""

    workspace = Workspace.from_path(workspace_root)
    record = load_run_record(workspace.root, run_id)
    if record.capability != "official_site" or record.status not in {
        "awaiting_coverage_review",
        "needs_recovery",
    }:
        raise OfficialSiteExecutionError(
            "official-site source imports require an unpublished coverage or recovery run"
        )
    parsed = _load_source_import(source_import)
    plan = OfficialSitePlan.model_validate(record.input_manifest["plan"])
    source_url = normalize_url(parsed.source_url)
    final_url = normalize_url(parsed.final_url or parsed.source_url)
    for value in (source_url, final_url):
        if not is_approved_url(value, plan.official_domains):
            raise OfficialSiteExecutionError(
                f"import URL is outside approved official domains: {value}"
            )
        if _excluded_financial_url(value):
            raise OfficialSiteExecutionError(f"import URL is excluded by scope: {value}")

    run_directory = workspace.runs / run_id
    workbench = (run_directory / "workbench").resolve()
    raw_input = _workbench_file(workbench, parsed.raw_file)
    raw_content = raw_input.read_bytes()
    if not raw_content or len(raw_content) > _MAX_RESPONSE_BYTES:
        raise OfficialSiteExecutionError(
            f"import raw file must contain 1-{_MAX_RESPONSE_BYTES} bytes"
        )
    source_type, suffix = _classify(
        parsed.content_type.split(";", 1)[0].strip().lower(), final_url, raw_content
    )
    if source_type not in {"html", "pdf", "data"}:
        raise OfficialSiteExecutionError("import content type is unsupported")

    snapshot = (run_directory / "snapshot").resolve()
    state = _load_crawl_state(snapshot)
    sources = _load_sources(snapshot)
    digest = hashlib.sha256(raw_content).hexdigest()
    source = next((item for item in sources if item.raw_sha256 == digest), None)
    if source is None:
        source = _new_imported_source(
            snapshot,
            run_id,
            parsed,
            source_url,
            final_url,
            source_type,
            suffix,
            raw_content,
            len(sources) + 1,
        )
        sources.append(source)
    else:
        _apply_imported_preparation(
            snapshot, workbench, run_id, source, parsed, final_url
        )
        source.acquisition_method = parsed.acquisition_method
        source.origin_run_id = run_id
        if final_url != source.final_url and final_url not in source.url_aliases:
            source.url_aliases.append(final_url)

    if source_url not in state["attempted_urls"]:
        state["attempted_urls"].append(source_url)
    if final_url not in state["attempted_urls"]:
        state["attempted_urls"].append(final_url)
    state["candidates"] = [
        item for item in state["candidates"] if item["url"] not in {source_url, final_url}
    ]
    audit = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_id": source.source_id,
        "import": parsed.model_dump(mode="json"),
        "raw_sha256": source.raw_sha256,
        "prepared_sha256": source.prepared_sha256,
        "adapter_sha256": source.adapter_sha256,
    }
    with (snapshot / "source_imports.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(audit, ensure_ascii=False, sort_keys=True) + "\n")
    _event(run_directory, "agent_source_ingested", audit)
    failures = list(record.items[0].get("failed_urls", []))
    return _mark_awaiting_coverage_review(
        record, workspace, snapshot, state, sources, failures
    )


def reprepare_official_site_sources(
    workspace_root: str | Path,
    run_id: str,
    *,
    source_ids: list[str] | None = None,
    low_content_only: bool = False,
) -> RunRecord:
    """Re-run generic preparation from preserved raw sources before synthesis."""

    workspace = Workspace.from_path(workspace_root)
    record = load_run_record(workspace.root, run_id)
    if record.capability != "official_site" or record.status not in {
        "awaiting_coverage_review",
        "needs_recovery",
    }:
        raise OfficialSiteExecutionError(
            "official-site reprepare requires an unpublished coverage or recovery run"
        )
    if not source_ids and not low_content_only:
        raise OfficialSiteExecutionError("select source_ids or low_content_only")
    snapshot = (workspace.runs / run_id / "snapshot").resolve()
    state = _load_crawl_state(snapshot)
    sources = _load_sources(snapshot)
    selected = set(source_ids or [])
    unknown = selected - {source.source_id for source in sources}
    if unknown:
        raise OfficialSiteExecutionError(f"unknown official-site source: {sorted(unknown)[0]}")
    changed = 0
    for source in sources:
        should_prepare = source.source_id in selected or (
            low_content_only and _effective_health(source) != "healthy"
        )
        if not should_prepare or source.source_type not in {"html", "pdf"}:
            continue
        _generic_reprepare(snapshot, source)
        changed += 1
    if not changed:
        raise OfficialSiteExecutionError("no matching HTML or PDF source requires preparation")
    _event(
        workspace.runs / run_id,
        "sources_reprepared",
        {
            "source_ids": [
                source.source_id for source in sources if source.source_id in selected
            ],
            "low_content_only": low_content_only,
            "changed": changed,
        },
    )
    failures = list(record.items[0].get("failed_urls", []))
    return _mark_awaiting_coverage_review(
        record, workspace, snapshot, state, sources, failures
    )


def _acquire_batch(
    plan: OfficialSitePlan,
    run_directory: Path,
    snapshot: Path,
    state: dict[str, Any],
    sources: list[SourceRecord],
    failures: list[dict[str, str]],
    urls: list[str],
    *,
    fetcher: Fetcher | None,
    allow_retry: bool = False,
) -> None:
    normalized_urls: list[str] = []
    for value in urls:
        url = normalize_url(value)
        if not is_approved_url(url, plan.official_domains):
            raise OfficialSiteExecutionError(
                f"batch URL is outside approved official domains: {url}"
            )
        if _excluded_financial_url(url):
            raise OfficialSiteExecutionError(f"batch URL is excluded by scope: {url}")
        if url not in normalized_urls:
            normalized_urls.append(url)
    if len(normalized_urls) > _MAX_URLS_PER_BATCH:
        raise OfficialSiteExecutionError(
            f"Agent batch exceeds hard guardrail of {_MAX_URLS_PER_BATCH} URLs"
        )
    if int(state["requests_made"]) + len(normalized_urls) > _MAX_TOTAL_REQUESTS:
        raise OfficialSiteExecutionError(
            f"run exceeds hard guardrail of {_MAX_TOTAL_REQUESTS} requests"
        )

    attempted = set(state["attempted_urls"])
    if not allow_retry:
        repeated = next((url for url in normalized_urls if url in attempted), None)
        if repeated:
            raise OfficialSiteExecutionError(f"URL was already attempted: {repeated}")
    candidate_urls = {item["url"] for item in state["candidates"]}
    for url in normalized_urls:
        if url not in candidate_urls and url not in attempted:
            _event(run_directory, "agent_url_selected", {"url": url})

    client = fetcher or HttpOfficialSiteFetcher()
    raw_digests = {source.raw_sha256: index for index, source in enumerate(sources)}
    last_request_at = 0.0
    for url in normalized_urls:
        state["requests_made"] += 1
        if url not in state["attempted_urls"]:
            state["attempted_urls"].append(url)
        state["candidates"] = [
            item for item in state["candidates"] if item["url"] != url
        ]
        interval = 1.0 / _REQUESTS_PER_SECOND
        remaining = interval - (time.monotonic() - last_request_at)
        if remaining > 0 and isinstance(client, HttpOfficialSiteFetcher):
            time.sleep(remaining)
        try:
            response = client.fetch(
                url,
                max_bytes=_MAX_RESPONSE_BYTES,
                approved_domains=plan.official_domains,
            )
            last_request_at = time.monotonic()
            final_url = normalize_url(response.final_url)
            if not is_approved_url(final_url, plan.official_domains):
                raise OfficialSiteFetchError(
                    "final URL is outside approved official domains"
                )
            if final_url not in state["attempted_urls"]:
                state["attempted_urls"].append(final_url)
            state["candidates"] = [
                item for item in state["candidates"] if item["url"] != final_url
            ]
        except (OfficialSiteFetchError, ValueError, OSError) as error:
            failure = {"url": url, "error": str(error)}
            failures.append(failure)
            _event(run_directory, "fetch_failed", failure)
            continue

        content_type = (
            response.headers.get("content-type", "application/octet-stream")
            .split(";", 1)[0]
            .strip()
            .lower()
        )
        source_type, suffix = _classify(content_type, final_url, response.content)
        if source_type is None:
            failure = {
                "url": url,
                "error": f"unsupported content type: {content_type}",
            }
            failures.append(failure)
            _event(run_directory, "unsupported_content", failure)
            continue
        if source_type == "sitemap":
            xml = response.content.decode("utf-8", errors="replace")
            _add_candidates(
                state,
                sitemap_urls(xml, final_url, plan.official_domains),
                discovered_from=final_url,
                discovery_type="sitemap",
            )
            _event(run_directory, "sitemap_discovered", {"url": final_url})
            continue

        digest = hashlib.sha256(response.content).hexdigest()
        if digest in raw_digests:
            existing = sources[raw_digests[digest]]
            if final_url not in existing.url_aliases and final_url != existing.final_url:
                existing.url_aliases.append(final_url)
            _event(
                run_directory,
                "duplicate_content",
                {"url": final_url, "source_id": existing.source_id},
            )
        else:
            source = _save_source(
                snapshot,
                response,
                requested_url=url,
                final_url=final_url,
                content_type=content_type,
                source_type=source_type,
                suffix=suffix,
                ordinal=len(sources) + 1,
            )
            raw_digests[source.raw_sha256] = len(sources)
            sources.append(source)
            _event(
                run_directory,
                "source_saved",
                {"url": final_url, "source_id": source.source_id, "status": source.status},
            )

        if source_type == "html":
            html = response.content.decode("utf-8", errors="replace")
            _add_candidates(
                state,
                extract_approved_links(html, final_url, plan.official_domains),
                discovered_from=final_url,
                discovery_type="page_link",
            )


def _save_source(
    snapshot: Path,
    response: Any,
    *,
    requested_url: str,
    final_url: str,
    content_type: str,
    source_type: str,
    suffix: str,
    ordinal: int,
) -> SourceRecord:
    digest = hashlib.sha256(response.content).hexdigest()
    alias = f"O{ordinal:04d}"
    identity_material = f"{final_url}\n{digest}".encode("utf-8")
    source_id = f"src_{hashlib.sha256(identity_material).hexdigest()[:20]}"
    raw_ref = _raw_ref(source_type, source_id, suffix)
    raw_path = snapshot / raw_ref
    raw_path.write_bytes(response.content)
    raw_identity = hash_file(raw_path)
    prepared_ref: str | None = None
    prepared_sha256: str | None = None
    prepared_lines: int | None = None
    preparation_health = "unprepared"
    substantive_chars: int | None = None
    content_blocks: int | None = None
    heading_count: int | None = None
    title: str | None = None
    warnings: list[str] = []
    if source_type == "html":
        try:
            prepared, title, warnings = html_to_markdown(
                response.content,
                source_alias=alias,
                url=final_url,
                content_type=response.headers.get("content-type", ""),
            )
            prepared_ref = f"prepared/pages/{source_id}.md"
        except ValueError as error:
            prepared = None
            warnings = [str(error)]
    elif source_type == "pdf":
        prepared, title, warnings = pdf_to_markdown(
            response.content, source_alias=alias, url=final_url
        )
        if prepared is not None:
            prepared_ref = f"prepared/documents/{source_id}.md"
    else:
        prepared = None
        warnings = ["data_attachment_preserved_without_business_parsing"]
    if prepared is not None and prepared_ref:
        prepared_path = snapshot / prepared_ref
        prepared_path.write_bytes(prepared)
        identity = hash_file(prepared_path)
        prepared_sha256 = identity.sha256
        prepared_lines = len(prepared.decode("utf-8").splitlines())
        health = analyze_prepared_markdown(prepared)
        preparation_health = health.status
        substantive_chars = health.substantive_char_count
        content_blocks = health.content_block_count
        heading_count = health.heading_count
        if health.status == "low_content":
            warnings.append("prepared_low_substantive_content")
    return SourceRecord(
        source_id=source_id,
        alias=alias,
        requested_url=response.requested_url,
        canonical_url=normalize_url(requested_url),
        final_url=final_url,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        http_status=response.status_code,
        content_type=content_type,
        title=title,
        source_type=source_type,
        raw_ref=raw_ref,
        raw_sha256=raw_identity.sha256,
        raw_byte_size=raw_identity.byte_size,
        prepared_ref=prepared_ref,
        prepared_sha256=prepared_sha256,
        prepared_line_count=prepared_lines,
        status="prepared" if prepared_ref else "preserved_unprepared",
        warnings=warnings,
        acquisition_method="http",
        preparation_method=(
            "generic_html_v1"
            if source_type == "html" and prepared_ref
            else "text_layer_pdf_v1"
            if source_type == "pdf" and prepared_ref
            else None
        ),
        preparation_health=preparation_health,
        substantive_char_count=substantive_chars,
        content_block_count=content_blocks,
        heading_count=heading_count,
    )


def _load_source_import(
    source_import: OfficialSiteSourceImport | dict[str, Any] | str | Path,
) -> OfficialSiteSourceImport:
    if isinstance(source_import, OfficialSiteSourceImport):
        return source_import
    if isinstance(source_import, dict):
        return OfficialSiteSourceImport.model_validate(source_import)
    return OfficialSiteSourceImport.model_validate_json(
        Path(source_import).read_text(encoding="utf-8")
    )


def _workbench_file(workbench: Path, ref: str) -> Path:
    candidate = (workbench / ref).resolve()
    if workbench not in candidate.parents or not candidate.is_file():
        raise OfficialSiteExecutionError(
            f"workbench reference is unsafe or missing: {ref}"
        )
    return candidate


def _new_imported_source(
    snapshot: Path,
    run_id: str,
    parsed: OfficialSiteSourceImport,
    source_url: str,
    final_url: str,
    source_type: str,
    suffix: str,
    raw_content: bytes,
    ordinal: int,
) -> SourceRecord:
    digest = hashlib.sha256(raw_content).hexdigest()
    alias = f"O{ordinal:04d}"
    source_id = f"src_{hashlib.sha256(f'{final_url}\n{digest}'.encode()).hexdigest()[:20]}"
    raw_ref = _raw_ref(source_type, source_id, suffix)
    raw_path = snapshot / raw_ref
    raw_path.write_bytes(raw_content)
    source = SourceRecord(
        source_id=source_id,
        alias=alias,
        requested_url=source_url,
        canonical_url=source_url,
        final_url=final_url,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        http_status=parsed.http_status,
        content_type=parsed.content_type.split(";", 1)[0].strip().lower(),
        title=parsed.title,
        source_type=source_type,
        raw_ref=raw_ref,
        raw_sha256=digest,
        raw_byte_size=len(raw_content),
        status="preserved_unprepared",
        warnings=[],
        acquisition_method=parsed.acquisition_method,
        preparation_health="unprepared",
        origin_run_id=run_id,
    )
    workbench = (snapshot.parent / "workbench").resolve()
    _apply_imported_preparation(snapshot, workbench, run_id, source, parsed, final_url)
    return source


def _apply_imported_preparation(
    snapshot: Path,
    workbench: Path,
    run_id: str,
    source: SourceRecord,
    parsed: OfficialSiteSourceImport,
    final_url: str,
) -> None:
    if parsed.prepared_markdown_file:
        prepared_input = _workbench_file(workbench, parsed.prepared_markdown_file)
        prepared = _standardize_agent_markdown(
            prepared_input.read_bytes(),
            title=parsed.title or source.title,
            source_alias=source.alias,
            url=final_url,
        )
        _store_prepared(
            snapshot,
            source,
            prepared,
            preparation_method="agent_markdown_v1",
            title=parsed.title,
            warnings=[],
            directory="prepared/agent",
        )
    else:
        _generic_reprepare(snapshot, source)
    if parsed.script_file:
        script_input = _workbench_file(workbench, parsed.script_file)
        script_suffix = script_input.suffix if script_input.suffix else ".txt"
        adapter_ref = f"provenance/scripts/{source.source_id}{script_suffix}"
        adapter_path = snapshot / adapter_ref
        shutil.copyfile(script_input, adapter_path)
        source.adapter_ref = adapter_ref
        source.adapter_sha256 = hash_file(adapter_path).sha256
    source.origin_run_id = run_id


def _standardize_agent_markdown(
    content: bytes, *, title: str | None, source_alias: str, url: str
) -> bytes:
    try:
        body = content.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise OfficialSiteExecutionError("Agent Prepared Markdown must be UTF-8") from error
    if not body:
        raise OfficialSiteExecutionError("Agent Prepared Markdown cannot be empty")
    body = re.sub(
        r"\A(?:# .+?\n+)?Source:\s*\[[^]]+\]\([^)]+\)\s*",
        "",
        body,
        count=1,
        flags=re.DOTALL,
    ).strip()
    heading = (title or "Official website source").strip()
    return f"# {heading}\n\nSource: [{source_alias}]({url})\n\n{body}\n".encode("utf-8")


def _generic_reprepare(snapshot: Path, source: SourceRecord) -> None:
    raw_path = (snapshot / source.raw_ref).resolve()
    if snapshot not in raw_path.parents or not raw_path.is_file():
        raise OfficialSiteExecutionError(f"source raw file is unsafe or missing: {source.source_id}")
    content = raw_path.read_bytes()
    warnings: list[str]
    if source.source_type == "html":
        try:
            prepared, title, warnings = html_to_markdown(
                content,
                source_alias=source.alias,
                url=source.final_url,
                content_type=source.content_type,
            )
        except ValueError as error:
            prepared, title, warnings = None, source.title, [str(error)]
        method = "generic_html_v1"
        directory = "prepared/pages"
    elif source.source_type == "pdf":
        prepared, title, warnings = pdf_to_markdown(
            content, source_alias=source.alias, url=source.final_url
        )
        method = "text_layer_pdf_v1"
        directory = "prepared/documents"
    else:
        return
    if prepared is None:
        source.status = "preserved_unprepared"
        source.prepared_ref = None
        source.prepared_sha256 = None
        source.prepared_line_count = None
        source.preparation_method = None
        source.preparation_health = "unprepared"
        source.substantive_char_count = None
        source.content_block_count = None
        source.heading_count = None
        source.warnings = warnings
        return
    _store_prepared(
        snapshot,
        source,
        prepared,
        preparation_method=method,
        title=title,
        warnings=warnings,
        directory=directory,
    )


def _store_prepared(
    snapshot: Path,
    source: SourceRecord,
    prepared: bytes,
    *,
    preparation_method: str,
    title: str | None,
    warnings: list[str],
    directory: str,
) -> None:
    old_ref = source.prepared_ref
    prepared_ref = f"{directory}/{source.source_id}.md"
    prepared_path = snapshot / prepared_ref
    prepared_path.parent.mkdir(parents=True, exist_ok=True)
    prepared_path.write_bytes(prepared)
    health = analyze_prepared_markdown(prepared)
    source.prepared_ref = prepared_ref
    source.prepared_sha256 = hash_file(prepared_path).sha256
    source.prepared_line_count = len(prepared.decode("utf-8").splitlines())
    source.status = "prepared"
    source.title = title or source.title
    source.preparation_method = preparation_method
    source.preparation_health = health.status
    source.substantive_char_count = health.substantive_char_count
    source.content_block_count = health.content_block_count
    source.heading_count = health.heading_count
    source.warnings = list(warnings)
    if health.status == "low_content":
        source.warnings.append("prepared_low_substantive_content")
    if old_ref and old_ref != prepared_ref:
        old_path = (snapshot / old_ref).resolve()
        if snapshot in old_path.parents and old_path.is_file():
            old_path.unlink()


def _add_candidates(
    state: dict[str, Any],
    urls: list[str],
    *,
    discovered_from: str,
    discovery_type: str,
) -> None:
    attempted = set(state["attempted_urls"])
    known = {item["url"] for item in state["candidates"]}
    for url in urls:
        if url in attempted or url in known or _excluded_financial_url(url):
            continue
        state["candidates"].append(
            {
                "url": url,
                "discovered_from": discovered_from,
                "discovery_type": discovery_type,
            }
        )
        known.add(url)


def _new_crawl_state() -> dict[str, Any]:
    return {
        "schema_version": "research_foundry_official_site_crawl_state.v1",
        "requests_made": 0,
        "attempted_urls": [],
        "candidates": [],
        "coverage_reviews": [],
        "hard_guardrails": _hard_guardrails(),
    }


def _hard_guardrails() -> dict[str, int | float]:
    return {
        "max_total_requests": _MAX_TOTAL_REQUESTS,
        "max_urls_per_batch": _MAX_URLS_PER_BATCH,
        "requests_per_second": _REQUESTS_PER_SECOND,
        "max_response_bytes": _MAX_RESPONSE_BYTES,
    }


def _load_crawl_state(snapshot: Path) -> dict[str, Any]:
    path = snapshot / "crawl_state.json"
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise OfficialSiteExecutionError("official-site crawl state is missing or invalid") from error
    if state.get("schema_version") != "research_foundry_official_site_crawl_state.v1":
        raise OfficialSiteExecutionError("unsupported official-site crawl state")
    if state.get("hard_guardrails") != _hard_guardrails():
        raise OfficialSiteExecutionError("official-site hard guardrails were modified")
    requests_made = state.get("requests_made")
    if not isinstance(requests_made, int) or not 0 <= requests_made <= _MAX_TOTAL_REQUESTS:
        raise OfficialSiteExecutionError("official-site request counter is invalid")
    return state


def _write_crawl_state(snapshot: Path, state: dict[str, Any]) -> None:
    (snapshot / "crawl_state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _load_sources(snapshot: Path) -> list[SourceRecord]:
    path = snapshot / "sources.jsonl"
    if not path.exists():
        return []
    return [
        SourceRecord.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _persist_working_corpus(
    snapshot: Path, state: dict[str, Any], sources: list[SourceRecord]
) -> dict[str, int]:
    _write_crawl_state(snapshot, state)
    (snapshot / "sources.jsonl").write_text(
        "".join(source.model_dump_json() + "\n" for source in sources),
        encoding="utf-8",
    )
    _write_preparation_health(snapshot, sources)
    index_directory = snapshot / "index"
    if index_directory.exists():
        shutil.rmtree(index_directory)
    if not any(source.status == "prepared" for source in sources):
        return {"sources": 0, "sections": 0, "chunks": 0, "tables": 0}
    return build_official_site_index(snapshot, sources)["counts"]


def _effective_health(source: SourceRecord) -> str:
    if source.preparation_health:
        return source.preparation_health
    return "healthy" if source.status == "prepared" else "unprepared"


def _health_summary(sources: list[SourceRecord]) -> dict[str, int]:
    summary = {"healthy": 0, "low_content": 0, "unprepared": 0}
    for source in sources:
        summary[_effective_health(source)] += 1
    return summary


def _write_preparation_health(snapshot: Path, sources: list[SourceRecord]) -> None:
    summary = _health_summary(sources)
    payload = {
        "schema_version": "research_foundry_official_site_preparation_health.v1",
        "summary": {"sources": len(sources), **summary},
        "sources": [
            {
                "source_id": source.source_id,
                "alias": source.alias,
                "url": source.final_url,
                "source_type": source.source_type,
                "status": source.status,
                "preparation_health": _effective_health(source),
                "substantive_char_count": source.substantive_char_count,
                "content_block_count": source.content_block_count,
                "heading_count": source.heading_count,
                "preparation_method": source.preparation_method,
                "warnings": source.warnings,
            }
            for source in sources
        ],
    }
    (snapshot / "preparation_health.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _recovery_source_ids(
    sources: list[SourceRecord], non_material_source_reasons: dict[str, str]
) -> list[str]:
    waived = set(non_material_source_reasons)
    return [
        source.source_id
        for source in sources
        if source.source_type in {"html", "pdf"}
        and _effective_health(source) != "healthy"
        and source.source_id not in waived
    ]


def _validate_coverage_assessment(
    plan: OfficialSitePlan,
    review: OfficialSiteCoverageReview,
    sources: list[SourceRecord],
) -> None:
    by_id = {source.source_id: source for source in sources}
    expected = {value.strip().casefold(): value for value in plan.scope.include if value.strip()}
    assessed: dict[str, Any] = {}
    for item in review.coverage_assessment:
        key = item.area.casefold()
        if key in assessed:
            raise OfficialSiteExecutionError(f"coverage area is duplicated: {item.area}")
        assessed[key] = item
        for source_id in item.evidence_source_ids:
            if source_id not in by_id:
                raise OfficialSiteExecutionError(
                    f"coverage assessment references unknown source: {source_id}"
                )
    missing = [label for key, label in expected.items() if key not in assessed]
    if missing:
        raise OfficialSiteExecutionError(
            f"coverage assessment is missing planned area: {missing[0]}"
        )
    for source_id in review.non_material_source_reasons:
        source = by_id.get(source_id)
        if source is None:
            raise OfficialSiteExecutionError(
                f"non-material decision references unknown source: {source_id}"
            )
        if _effective_health(source) == "healthy":
            raise OfficialSiteExecutionError(
                f"healthy source cannot be waived as non-material: {source_id}"
            )
    for item in review.coverage_assessment:
        if item.status != "covered":
            continue
        unhealthy = [
            source_id
            for source_id in item.evidence_source_ids
            if _effective_health(by_id[source_id]) != "healthy"
        ]
        if unhealthy:
            raise OfficialSiteExecutionError(
                f"covered area relies on unhealthy source: {unhealthy[0]}"
            )


def _mark_awaiting_coverage_review(
    record: RunRecord,
    workspace: Workspace,
    snapshot: Path,
    state: dict[str, Any],
    sources: list[SourceRecord],
    failures: list[dict[str, str]],
) -> RunRecord:
    counts = _persist_working_corpus(snapshot, state, sources)
    prepared_count = sum(source.status == "prepared" for source in sources)
    health = _health_summary(sources)
    record.status = "awaiting_coverage_review"
    record.finished_at = None
    record.warnings = [f"{len(failures)}_urls_failed"] if failures else []
    record.items = [
        {
            "status": "awaiting_coverage_review",
            "snapshot_working_directory": str(snapshot),
            "workbench_directory": str(workspace.runs / record.run_id / "workbench"),
            "crawl_state": str(snapshot / "crawl_state.json"),
            "source_count": len(sources),
            "prepared_count": prepared_count,
            "healthy_prepared_count": health["healthy"],
            "low_content_count": health["low_content"],
            "unprepared_count": health["unprepared"],
            "preparation_health": str(snapshot / "preparation_health.json"),
            "candidate_count": len(state["candidates"]),
            "index_counts": counts,
            "failed_urls": failures,
            "hard_guardrails": _hard_guardrails(),
        }
    ]
    write_run_record(workspace.root, record)
    return record


def _mark_needs_recovery(
    record: RunRecord,
    workspace: Workspace,
    snapshot: Path,
    state: dict[str, Any],
    sources: list[SourceRecord],
    failures: list[dict[str, str]],
    recovery_source_ids: list[str],
) -> RunRecord:
    counts = _persist_working_corpus(snapshot, state, sources)
    health = _health_summary(sources)
    record.status = "needs_recovery"
    record.finished_at = None
    record.warnings = ["material_source_preparation_requires_recovery"]
    if failures:
        record.warnings.append(f"{len(failures)}_urls_failed")
    record.items = [
        {
            "status": "needs_recovery",
            "snapshot_working_directory": str(snapshot),
            "workbench_directory": str(workspace.runs / record.run_id / "workbench"),
            "crawl_state": str(snapshot / "crawl_state.json"),
            "preparation_health": str(snapshot / "preparation_health.json"),
            "source_count": len(sources),
            "healthy_prepared_count": health["healthy"],
            "low_content_count": health["low_content"],
            "unprepared_count": health["unprepared"],
            "candidate_count": len(state["candidates"]),
            "index_counts": counts,
            "failed_urls": failures,
            "recovery_source_ids": recovery_source_ids,
            "hard_guardrails": _hard_guardrails(),
        }
    ]
    write_run_record(workspace.root, record)
    return record


def _finalize_coverage(
    record: RunRecord,
    workspace: Workspace,
    snapshot: Path,
    state: dict[str, Any],
    sources: list[SourceRecord],
    failures: list[dict[str, str]],
) -> RunRecord:
    prepared_count = sum(source.status == "prepared" for source in sources)
    if not prepared_count:
        raise OfficialSiteExecutionError(
            "coverage cannot be completed without a prepared official source"
        )
    counts = _persist_working_corpus(snapshot, state, sources)
    health = _health_summary(sources)
    plan = OfficialSitePlan.model_validate(record.input_manifest["plan"])
    snapshot_id = _snapshot_id(plan, sources)
    _write_synthesis_templates(snapshot, plan, record.run_id, snapshot_id)
    final_review = state["coverage_reviews"][-1]
    record.status = "awaiting_synthesis"
    record.finished_at = None
    record.warnings = [f"{len(failures)}_urls_failed"] if failures else []
    record.items = [
        {
            "status": "awaiting_synthesis",
            "snapshot_id": snapshot_id,
            "snapshot_working_directory": str(snapshot),
            "deliverables_directory": str(snapshot / "deliverables"),
            "data_directory": str(snapshot / "data"),
            "quality_report": str(snapshot / "quality_report.json"),
            "crawl_state": str(snapshot / "crawl_state.json"),
            "source_count": len(sources),
            "prepared_count": prepared_count,
            "healthy_prepared_count": health["healthy"],
            "low_content_count": health["low_content"],
            "unprepared_count": health["unprepared"],
            "preparation_health": str(snapshot / "preparation_health.json"),
            "candidate_count": len(state["candidates"]),
            "index_counts": counts,
            "failed_urls": failures,
            "coverage_material_gaps": final_review["material_gaps"],
            "hard_guardrails": _hard_guardrails(),
        }
    ]
    write_run_record(workspace.root, record)
    return record


def _mark_failed(
    record: RunRecord,
    workspace: Workspace,
    snapshot: Path,
    state: dict[str, Any],
    failures: list[dict[str, str]],
) -> RunRecord:
    record.status = "failed"
    record.finished_at = datetime.now(timezone.utc)
    record.warnings = ["no_official_source_or_candidate"]
    record.items = [
        {
            "status": "failed",
            "snapshot_working_directory": str(snapshot),
            "crawl_state": str(snapshot / "crawl_state.json"),
            "failed_urls": failures,
            "hard_guardrails": _hard_guardrails(),
        }
    ]
    write_run_record(workspace.root, record)
    return record


def _load_coverage_review(
    review: OfficialSiteCoverageReview | dict[str, Any] | str | Path,
) -> OfficialSiteCoverageReview:
    if isinstance(review, OfficialSiteCoverageReview):
        return review
    if isinstance(review, dict):
        return OfficialSiteCoverageReview.model_validate(review)
    return OfficialSiteCoverageReview.model_validate_json(
        Path(review).read_text(encoding="utf-8")
    )


def _synthesis_started(snapshot: Path) -> bool:
    deliverables = list((snapshot / "deliverables").glob("*.md"))
    if any(
        "[Agent synthesis required]" not in path.read_text(encoding="utf-8")
        for path in deliverables
    ):
        return True
    if any(path.read_text(encoding="utf-8").strip() for path in (snapshot / "data").glob("*.jsonl")):
        return True
    try:
        return bool(
            json.loads((snapshot / "quality_report.json").read_text(encoding="utf-8")).get(
                "research_ready"
            )
        )
    except FileNotFoundError:
        return False
    except (OSError, ValueError):
        return True


def _write_synthesis_templates(
    snapshot: Path, plan: OfficialSitePlan, run_id: str, snapshot_id: str
) -> None:
    common = (
        "---\n"
        "schema_version: research_foundry_official_site_deliverable.v1\n"
        "document_type: {document_type}\n"
        f"target_name: {json.dumps(plan.target_name, ensure_ascii=False)}\n"
        f"as_of: {plan.as_of.isoformat()}\n"
        f"snapshot_id: {snapshot_id}\n"
        f"run_id: {run_id}\n"
        "quality_status: draft\n"
        "---\n\n"
    )
    documents = {
        "business_and_offering_handbook": "# Business and Offering Handbook\n\n[Agent synthesis required]\n",
        "strategy_and_developments": "# Strategy and Developments\n\n[Agent synthesis required]\n",
        "important_information": "# Important Information\n\n[Agent synthesis required]\n",
    }
    for document_type, body in documents.items():
        (snapshot / "deliverables" / f"{document_type}.md").write_text(
            common.format(document_type=document_type) + body, encoding="utf-8"
        )
    for filename in ("offering_catalog.jsonl", "development_events.jsonl"):
        (snapshot / "data" / filename).write_text("", encoding="utf-8")
    quality = {
        "schema_version": "research_foundry_official_site_quality.v1",
        "research_ready": False,
        "checks": {
            key: "fail"
            for key in (
                "provenance",
                "material_coverage",
                "evidence",
                "consistency",
                "limitations",
            )
        },
        "material_gaps": [
            "Agent synthesis and second-pass review have not been completed"
        ],
        "warnings": [],
    }
    (snapshot / "quality_report.json").write_text(
        json.dumps(quality, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _snapshot_id(plan: OfficialSitePlan, sources: list[SourceRecord]) -> str:
    identities = [
        "|".join(
            (
                source.raw_sha256,
                source.prepared_sha256 or "",
                source.preparation_method or "",
                source.adapter_sha256 or "",
            )
        )
        for source in sources
    ]
    material = "\n".join([plan.plan_id, *identities])
    return f"oss_{hashlib.sha256(material.encode('utf-8')).hexdigest()[:20]}"


def _classify(content_type: str, url: str, content: bytes) -> tuple[str | None, str]:
    suffix = Path(url.split("?", 1)[0]).suffix.lower()
    if "html" in content_type or content.lstrip()[:30].lower().startswith(
        (b"<!doctype html", b"<html")
    ):
        return "html", ".html"
    if content_type == "application/pdf" or suffix == ".pdf" or content.startswith(b"%PDF-"):
        return "pdf", ".pdf"
    if content_type in {"application/xml", "text/xml"} or suffix == ".xml":
        return "sitemap", ".xml"
    if suffix in _DATA_SUFFIXES or content_type in {
        "text/csv",
        "application/json",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }:
        return "data", suffix if suffix in _DATA_SUFFIXES else ".bin"
    return None, suffix or ".bin"


def _raw_ref(source_type: str, source_id: str, suffix: str) -> str:
    directory = {"html": "pages", "pdf": "documents", "data": "data"}[source_type]
    return f"raw/{directory}/{source_id}{suffix}"


def _excluded_financial_url(url: str) -> bool:
    path = urlsplit(normalize_url(url)).path.casefold()
    tokens = [value for value in re.split(r"[^a-z0-9]+", path) if value]
    normalized = "-".join(tokens)
    return any(
        re.search(rf"(?:^|-){re.escape(marker)}(?:-|$)", normalized)
        for marker in _EXCLUDED_PATH_MARKERS
    )


def _event(run_directory: Path, event: str, detail: dict[str, Any]) -> None:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **detail,
    }
    with (run_directory / "operation_events.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
