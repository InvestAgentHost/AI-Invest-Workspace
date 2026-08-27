"""Finalize clean human reports while preserving deterministic evidence traceability."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Any

from pydantic import ValidationError

from research_foundry.runtime.artifacts import hash_file

from .contracts import (
    ReportEvidenceBlock,
    ReportEvidenceMap,
    ReportEvidenceSourceRef,
    ReportPanelRef,
)
from .notebook import (
    _inspect_source,
    _load_source_catalog,
    _parse_citations,
    _replace_atomically,
    _resolve_notebook,
)
from .panels import load_research_panel, validate_research_panel


_TOPIC = re.compile(r"<!--\s*rf:topic=([A-Za-z][A-Za-z0-9_-]{2,95})\s*-->")
_TABLE = re.compile(r"<!--\s*rf:table=([A-Za-z][A-Za-z0-9_-]{2,95})\s*-->")
_BLOCK = re.compile(r"<!--\s*rf:block=([A-Za-z][A-Za-z0-9_-]{2,95})\s*-->")
_PANEL = re.compile(
    r"\[\[panel:([A-Za-z][A-Za-z0-9_-]{2,95})#"
    r"([A-Za-z][A-Za-z0-9_,-]{2,})@([^\]]+)\]\]"
)
_VISIBLE_INTERNAL = re.compile(
    r"\[\[(?:panel:)?[A-Za-z][A-Za-z0-9_-]{2,95}(?::L|#)|"
    r"\bsha256\b|(?:^|\s)(?:/home/|artifacts/)",
    re.IGNORECASE | re.MULTILINE,
)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_MATERIAL_NUMBER = re.compile(r"(?<![A-Za-z])(?:[$€£¥]\s*)?\d[\d,.]*(?:%|\s*(?:million|billion|bps))?", re.IGNORECASE)


class ReportFinalizationError(ValueError):
    """Raised when a Writer draft cannot be finalized safely."""


@dataclass(frozen=True, slots=True)
class ReportFinalizationValidation:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    block_count: int
    source_ref_count: int
    panel_ref_count: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def finalize_research_report(
    research_root: str | Path,
    *,
    workspace_root: str | Path,
    writer_ref: str,
    draft_ref: str = "notes/report_draft.md",
) -> ReportEvidenceMap:
    """Validate Writer markers, strip visible traceability, and materialize final outputs."""

    root, workspace, identity = _resolve_notebook(research_root, workspace_root)
    if (root / "release_manifest.json").exists():
        raise ReportFinalizationError("published notebook cannot finalize a report")
    if not writer_ref.strip():
        raise ReportFinalizationError("report finalization requires writer_ref")
    draft_path = (root / draft_ref).resolve()
    if root not in draft_path.parents or draft_path.is_symlink() or not draft_path.is_file():
        raise ReportFinalizationError("Writer draft must be a regular file below the research root")
    try:
        draft = draft_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ReportFinalizationError(f"unable to read Writer draft: {error}") from error
    if _BLOCK.search(draft):
        raise ReportFinalizationError("Writer draft cannot assign rf:block IDs")
    catalog = _load_source_catalog(root / "sources.md")
    source_records = {
        source_id: _inspect_source(source_id, artifact_ref, workspace)
        for source_id, artifact_ref in catalog.items()
    }
    clean_chunks: list[str] = []
    blocks: list[ReportEvidenceBlock] = []
    topic_id = "front_matter"
    topic_counts: dict[str, int] = {}
    for raw_chunk in re.split(r"\n[ \t]*\n", draft.strip()):
        topic_match = _TOPIC.search(raw_chunk)
        if topic_match:
            topic_id = topic_match.group(1)
        citations, malformed = _parse_citations(_PANEL.sub("", raw_chunk), "report.md")
        if malformed:
            raise ReportFinalizationError("Writer draft contains a malformed source citation")
        source_refs: list[ReportEvidenceSourceRef] = []
        for citation in citations:
            source = source_records.get(citation.source_id)
            if source is None:
                raise ReportFinalizationError(f"Writer draft cites unknown source: {citation.source_id}")
            if citation.end_line > source.line_count:
                raise ReportFinalizationError(
                    f"Writer draft citation exceeds source lines: {citation.source_id}:L{citation.end_line}"
                )
            source_refs.append(
                ReportEvidenceSourceRef(
                    source_id=citation.source_id,
                    start_line=citation.start_line,
                    end_line=citation.end_line,
                )
            )
        panel_refs = tuple(_parse_panel_ref(match, root, workspace) for match in _PANEL.finditer(raw_chunk))
        clean = re.sub(
            r"\[\[[A-Za-z][A-Za-z0-9_-]{2,95}:L[1-9][0-9]*(?:-L?[1-9][0-9]*)?\]\]",
            "",
            raw_chunk,
        )
        clean = _PANEL.sub("", clean)
        clean = re.sub(r"[ \t]+\n", "\n", clean)
        clean = re.sub(r" {2,}", " ", clean).strip()
        substantive = _HTML_COMMENT.sub("", clean).strip()
        if not substantive:
            clean_chunks.append(clean)
            continue
        kind = _block_kind(substantive)
        if kind not in {"heading"} and _MATERIAL_NUMBER.search(substantive) and not (
            source_refs or panel_refs
        ):
            raise ReportFinalizationError(
                f"material numeric report block lacks a source or panel binding: {substantive[:100]}"
            )
        topic_counts[topic_id] = topic_counts.get(topic_id, 0) + 1
        block_id = f"{topic_id}_{topic_counts[topic_id]:03d}"
        clean_chunks.append(f"<!-- rf:block={block_id} -->\n{clean}")
        blocks.append(
            ReportEvidenceBlock(
                block_id=block_id,
                topic_id=topic_id,
                block_kind=kind,
                source_refs=tuple(_unique_source_refs(source_refs)),
                panel_refs=panel_refs,
            )
        )
    report_text = "\n\n".join(chunk for chunk in clean_chunks if chunk).rstrip() + "\n"
    if _VISIBLE_INTERNAL.search(report_text):
        raise ReportFinalizationError("final report would expose an internal citation, path, or hash")
    report_path = root / "report.md"
    _replace_atomically(report_text.encode("utf-8"), report_path)
    evidence_map = ReportEvidenceMap(
        research_id=identity.research_id,
        report_ref="report.md",
        report_sha256=hash_file(report_path).sha256,
        draft_ref=draft_path.relative_to(root).as_posix(),
        draft_sha256=hash_file(draft_path).sha256,
        writer_ref=writer_ref,
        blocks=tuple(blocks),
    )
    map_path = root / "report_evidence_map.json"
    _replace_atomically((evidence_map.model_dump_json(indent=2) + "\n").encode("utf-8"), map_path)
    validation = validate_finalized_report(root, workspace_root=workspace)
    if not validation.valid:
        raise ReportFinalizationError(f"finalized report is invalid: {validation.errors[0]}")
    return evidence_map


def validate_finalized_report(
    research_root: str | Path,
    *,
    workspace_root: str | Path,
) -> ReportFinalizationValidation:
    """Validate report/map identity and every source and panel reference."""

    errors: list[str] = []
    warnings: list[str] = []
    try:
        root, workspace, identity = _resolve_notebook(research_root, workspace_root)
        report_path = root / "report.md"
        map_path = root / "report_evidence_map.json"
        report_text = report_path.read_text(encoding="utf-8")
        evidence_map = ReportEvidenceMap.model_validate_json(map_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, ValidationError) as error:
        return ReportFinalizationValidation(False, (f"invalid finalized report: {error}",), (), 0, 0, 0)
    if evidence_map.research_id != identity.research_id:
        errors.append("report evidence map research_id does not match task.md")
    if hash_file(report_path).sha256 != evidence_map.report_sha256:
        errors.append("report.md changed after deterministic finalization")
    draft_path = (root / evidence_map.draft_ref).resolve()
    if root not in draft_path.parents or draft_path.is_symlink() or not draft_path.is_file():
        errors.append("report evidence map references an unsafe Writer draft")
    elif hash_file(draft_path).sha256 != evidence_map.draft_sha256:
        errors.append("Writer draft changed after deterministic finalization")
    if _VISIBLE_INTERNAL.search(report_text):
        errors.append("report.md exposes an internal citation, path, or hash")
    marker_ids = tuple(_BLOCK.findall(report_text))
    mapped_ids = tuple(block.block_id for block in evidence_map.blocks)
    if len(marker_ids) != len(set(marker_ids)):
        errors.append("report.md repeats an rf:block marker")
    if set(marker_ids) != set(mapped_ids):
        errors.append("report block markers do not match report evidence map")
    catalog = _load_source_catalog(root / "sources.md")
    source_records = {
        source_id: _inspect_source(source_id, artifact_ref, workspace)
        for source_id, artifact_ref in catalog.items()
    }
    source_ref_count = 0
    panel_ref_count = 0
    validated_panels: set[str] = set()
    for block in evidence_map.blocks:
        source_ref_count += len(block.source_refs)
        panel_ref_count += len(block.panel_refs)
        for source_ref in block.source_refs:
            source = source_records.get(source_ref.source_id)
            if source is None:
                errors.append(f"report evidence map cites unknown source: {source_ref.source_id}")
            elif source_ref.end_line > source.line_count:
                errors.append(
                    f"report evidence map citation exceeds source lines: {source_ref.source_id}:L{source_ref.end_line}"
                )
        for panel_ref in block.panel_refs:
            try:
                panel = load_research_panel(root, panel_ref.panel_id)
            except ValueError as error:
                errors.append(str(error))
                continue
            unknown_metrics = set(panel_ref.metric_ids).difference(row.metric_id for row in panel.rows)
            unknown_periods = set(panel_ref.periods).difference(panel.periods)
            if unknown_metrics:
                errors.append(
                    f"report references unknown panel metric: {panel_ref.panel_id} -> {sorted(unknown_metrics)[0]}"
                )
            if unknown_periods:
                errors.append(
                    f"report references unknown panel period: {panel_ref.panel_id} -> {sorted(unknown_periods)[0]}"
                )
            if panel.panel_id not in validated_panels:
                panel_validation = validate_research_panel(root, panel.panel_id, workspace_root=workspace)
                errors.extend(f"panel {panel.panel_id}: {item}" for item in panel_validation.errors)
                validated_panels.add(panel.panel_id)
    if identity.research_shape == "comprehensive":
        from .coverage import validate_comprehensive_report

        report_errors, report_warnings = validate_comprehensive_report(
            root, report_text=report_text
        )
        errors.extend(f"report contract: {item}" for item in report_errors)
        warnings.extend(report_warnings)
    return ReportFinalizationValidation(
        not errors,
        tuple(errors),
        tuple(warnings),
        len(evidence_map.blocks),
        source_ref_count,
        panel_ref_count,
    )


def load_report_evidence_map(research_root: str | Path) -> ReportEvidenceMap:
    try:
        return ReportEvidenceMap.model_validate_json(
            (Path(research_root) / "report_evidence_map.json").read_text(encoding="utf-8")
        )
    except (OSError, ValidationError) as error:
        raise ReportFinalizationError(f"invalid report evidence map: {error}") from error


def _parse_panel_ref(match: re.Match[str], root: Path, workspace: Path) -> ReportPanelRef:
    panel_id, metric_text, period_text = match.groups()
    metric_ids = tuple(item.strip() for item in metric_text.split(",") if item.strip())
    periods = tuple(item.strip() for item in period_text.split(",") if item.strip())
    panel = load_research_panel(root, panel_id)
    validation = validate_research_panel(root, panel_id, workspace_root=workspace)
    if not validation.valid:
        raise ReportFinalizationError(f"Writer draft references invalid panel {panel_id}: {validation.errors[0]}")
    unknown_metrics = set(metric_ids).difference(row.metric_id for row in panel.rows)
    unknown_periods = set(periods).difference(panel.periods)
    if unknown_metrics:
        raise ReportFinalizationError(
            f"Writer draft references unknown panel metric: {panel_id} -> {sorted(unknown_metrics)[0]}"
        )
    if unknown_periods:
        raise ReportFinalizationError(
            f"Writer draft references unknown panel period: {panel_id} -> {sorted(unknown_periods)[0]}"
        )
    return ReportPanelRef(panel_id=panel_id, metric_ids=metric_ids, periods=periods)


def _block_kind(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].lstrip().startswith("#"):
        return "heading"
    if any(line.strip().startswith("|") for line in lines):
        return "table"
    if lines and all(line.lstrip().startswith(("- ", "* ", "+ ")) for line in lines if line.strip()):
        return "list"
    return "prose"


def _unique_source_refs(
    values: list[ReportEvidenceSourceRef],
) -> list[ReportEvidenceSourceRef]:
    result: list[ReportEvidenceSourceRef] = []
    seen: set[tuple[str, int, int, str]] = set()
    for value in values:
        key = (value.source_id, value.start_line, value.end_line, value.evidence_role)
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result
