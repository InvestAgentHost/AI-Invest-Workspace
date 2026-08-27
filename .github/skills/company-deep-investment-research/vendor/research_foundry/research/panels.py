"""Deterministic preparation, materialization, and validation for research panels."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
from typing import Any, Iterable

from pydantic import TypeAdapter, ValidationError
import yaml

from research_foundry.runtime.artifacts import hash_file

from .contracts import PanelSourceRef, ResearchPanel, ResearchPanelRow, ResearchPanelValue
from .contracts.models import StableId
from .notebook import _inspect_source, _load_source_catalog, _replace_atomically, _resolve_notebook


_NUMBER = re.compile(r"^[\s$€£¥]*([+-]?)(?:\(?)([0-9][0-9,]*(?:\.[0-9]+)?)(?:\)?)[\s%]*$")
_STABLE_ID = TypeAdapter(StableId)


class ResearchPanelError(ValueError):
    """Raised when a panel cannot be built without guessing semantics."""


@dataclass(frozen=True, slots=True)
class PanelValidationReport:
    valid: bool
    panel_id: str | None
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    period_count: int
    row_count: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def prepare_panel_candidates(
    research_root: str | Path,
    *,
    panel_id: str,
    panel_type: str,
    title: str,
    periods: Iterable[str],
    source_indexes: dict[str, str | Path],
    workspace_root: str | Path,
    query_terms: Iterable[str] = (),
    default_unit: str | None = None,
) -> tuple[Path, Path]:
    """Freeze table-index candidates and create an Agent-editable semantic mapping."""

    root, workspace, _ = _resolve_notebook(research_root, workspace_root)
    try:
        panel_id = _STABLE_ID.validate_python(panel_id)
        panel_type = _STABLE_ID.validate_python(panel_type)
    except ValidationError as error:
        raise ResearchPanelError(f"invalid panel identity: {error}") from error
    if not title.strip():
        raise ResearchPanelError("panel title must be non-empty")
    if (root / "release_manifest.json").exists():
        raise ResearchPanelError("published notebook cannot prepare a panel")
    period_values = tuple(str(item).strip() for item in periods if str(item).strip())
    if not period_values or len(period_values) != len(set(period_values)):
        raise ResearchPanelError("panel periods must be non-empty and unique")
    terms = tuple(item.casefold().strip() for item in query_terms if item.strip())
    catalog = _load_source_catalog(root / "sources.md")
    candidates: list[dict[str, Any]] = []
    for source_id, index_input in sorted(source_indexes.items()):
        artifact_ref = catalog.get(source_id)
        if artifact_ref is None:
            raise ResearchPanelError(f"panel source is not registered: {source_id}")
        source = _inspect_source(source_id, artifact_ref, workspace)
        index_path = Path(index_input).expanduser()
        index_path = index_path if index_path.is_absolute() else workspace / index_path
        if index_path.is_symlink() or not index_path.is_file():
            raise ResearchPanelError(f"unsafe or missing table index: {source_id}")
        resolved_index = index_path.resolve()
        if workspace not in resolved_index.parents:
            raise ResearchPanelError(f"table index escapes workspace: {source_id}")
        for line_number, line in enumerate(
            resolved_index.read_text(encoding="utf-8").splitlines(), start=1
        ):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ResearchPanelError(
                    f"invalid table index JSON ({source_id}, line {line_number}): {error}"
                ) from error
            if not isinstance(record, dict):
                continue
            locator = record.get("locator") or {}
            if locator.get("artifact_sha256") != source.artifact_sha256:
                continue
            source_html = str(record.get("source_html", ""))
            if terms and not any(term in source_html.casefold() for term in terms):
                continue
            rows = _candidate_rows(record.get("rows"))
            if len(rows) < 2 or max((len(row) for row in rows), default=0) < 2:
                continue
            table_id = str(record.get("table_id", "")).strip()
            if not table_id:
                continue
            candidates.append(
                {
                    "candidate_id": f"{source_id}__{table_id}",
                    "source_id": source_id,
                    "table_id": table_id,
                    "start_line": int(locator.get("start_line") or record.get("start_line") or 0),
                    "end_line": int(locator.get("end_line") or record.get("end_line") or 0),
                    "section_path": record.get("section_path") or [],
                    "rows": rows,
                }
            )
    if source_indexes and not candidates:
        raise ResearchPanelError("no table candidates matched the registered sources and query")
    panel_directory = root / "panels"
    panel_directory.mkdir(exist_ok=True)
    candidate_path = panel_directory / f"{panel_id}.candidates.json"
    mapping_path = panel_directory / f"{panel_id}.mapping.yaml"
    if candidate_path.exists() or mapping_path.exists():
        raise ResearchPanelError(f"panel preparation already exists: {panel_id}")
    candidate_payload = {
        "schema_version": "research_panel_candidates.v1",
        "panel_id": panel_id,
        "source_count": len(source_indexes),
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    _replace_atomically(
        (json.dumps(candidate_payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        candidate_path,
    )
    mapping_payload = {
        "schema_version": "research_panel_mapping.v1",
        "panel_id": panel_id,
        "panel_type": panel_type,
        "title": title,
        "periods": list(period_values),
        "default_unit": default_unit,
        "owner_ref": "REPLACE_WITH_HARNESS_AGENT_REF",
        "adjudication_policy": (
            "Quality first: use candidates when reliable; reconstruct any row or full table "
            "with Agent-adjudicated values and exact source_ref when semantic alignment, "
            "restatement, scope, or parsing makes automatic extraction unsafe."
        ),
        "value_modes": {
            "row_fields": (
                "metric_id + label + section + scope + unit + values; financial_history "
                "uses income_statement/balance_sheet/cash_flow_statement sections"
            ),
            "candidate": (
                "period + status + candidate_id + zero-based row_index/column_index + "
                "source_scope; program reads and parses the cell"
            ),
            "agent_adjudicated": (
                "period + status + value + source_ref(source_id/start_line/end_line) + "
                "adjudication; use for restatements, scope changes, parser failures, or "
                "when the Agent reconstructs the full panel"
            ),
            "missing_or_incomparable": (
                "period + not_disclosed/not_comparable/not_applicable + note where required; "
                "not_comparable also requires exact source_ref"
            ),
        },
        "candidates_ref": candidate_path.relative_to(root).as_posix(),
        "comparability_notes": [],
        "missing_periods": [],
        "rows": [],
    }
    _replace_atomically(
        yaml.safe_dump(mapping_payload, allow_unicode=True, sort_keys=False).encode("utf-8"),
        mapping_path,
    )
    return candidate_path, mapping_path


def build_research_panel(
    research_root: str | Path,
    mapping_path: str | Path,
    *,
    workspace_root: str | Path,
) -> ResearchPanel:
    """Apply an Agent-adjudicated mapping without copying values by hand."""

    root, workspace, _ = _resolve_notebook(research_root, workspace_root)
    if (root / "release_manifest.json").exists():
        raise ResearchPanelError("published notebook cannot build a panel")
    mapping_source = Path(mapping_path).expanduser()
    mapping_source = mapping_source if mapping_source.is_absolute() else root / mapping_source
    if mapping_source.is_symlink() or not mapping_source.is_file():
        raise ResearchPanelError("panel mapping must be a regular file")
    mapping_source = mapping_source.resolve()
    if root not in mapping_source.parents:
        raise ResearchPanelError("panel mapping must stay below the research root")
    try:
        mapping = yaml.safe_load(mapping_source.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        raise ResearchPanelError(f"invalid panel mapping: {error}") from error
    if not isinstance(mapping, dict) or mapping.get("schema_version") != "research_panel_mapping.v1":
        raise ResearchPanelError("unsupported panel mapping")
    owner_ref = str(mapping.get("owner_ref", "")).strip()
    if not owner_ref or owner_ref == "REPLACE_WITH_HARNESS_AGENT_REF":
        raise ResearchPanelError("panel mapping requires a real owner_ref")
    candidate_ref = str(mapping.get("candidates_ref") or "").strip()
    candidate_path: Path | None = None
    candidates: dict[str, dict[str, Any]] = {}
    if candidate_ref:
        candidate_path = (root / candidate_ref).resolve()
        if root not in candidate_path.parents or candidate_path.is_symlink() or not candidate_path.is_file():
            raise ResearchPanelError("panel mapping references unsafe candidates")
        candidates_payload = json.loads(candidate_path.read_text(encoding="utf-8"))
        candidates = {
            item["candidate_id"]: item for item in candidates_payload.get("candidates", [])
        }
    errors: list[str] = []
    rows: list[ResearchPanelRow] = []
    for row_payload in mapping.get("rows") or []:
        try:
            rows.append(_build_panel_row(row_payload, candidates, errors))
        except (KeyError, TypeError, ValueError, ValidationError) as error:
            metric = row_payload.get("metric_id", "unknown") if isinstance(row_payload, dict) else "unknown"
            errors.append(f"invalid mapped row {metric}: {error}")
    panel_id = str(mapping.get("panel_id", ""))
    exception_path = root / "panels" / f"{panel_id}.exceptions.json"
    if errors:
        _replace_atomically(
            (json.dumps({"panel_id": panel_id, "errors": errors}, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
            exception_path,
        )
        raise ResearchPanelError(f"panel mapping has {len(errors)} unresolved exception(s): {errors[0]}")
    exception_path.unlink(missing_ok=True)
    try:
        panel = ResearchPanel(
            panel_id=panel_id,
            panel_type=mapping["panel_type"],
            title=mapping["title"],
            periods=tuple(str(item) for item in mapping.get("periods") or ()),
            default_unit=mapping.get("default_unit"),
            rows=tuple(rows),
            comparability_notes=tuple(mapping.get("comparability_notes") or ()),
            missing_periods=tuple(mapping.get("missing_periods") or ()),
        )
    except (KeyError, ValidationError) as error:
        raise ResearchPanelError(f"invalid materialized panel: {error}") from error
    panel_json = root / "panels" / f"{panel.panel_id}.json"
    panel_markdown = root / "panels" / f"{panel.panel_id}.md"
    _replace_atomically((panel.model_dump_json(indent=2) + "\n").encode("utf-8"), panel_json)
    _replace_atomically(render_research_panel(panel).encode("utf-8"), panel_markdown)
    record: dict[str, Any] = {
        "schema_version": "research_panel_build.v1",
        "panel_id": panel.panel_id,
        "owner_ref": owner_ref,
        "mapping_ref": mapping_source.relative_to(root).as_posix(),
        "mapping_sha256": hash_file(mapping_source).sha256,
        "panel_ref": panel_json.relative_to(root).as_posix(),
        "panel_sha256": hash_file(panel_json).sha256,
        "rendered_ref": panel_markdown.relative_to(root).as_posix(),
        "rendered_sha256": hash_file(panel_markdown).sha256,
    }
    if candidate_path is not None:
        record["candidates_ref"] = candidate_ref
        record["candidates_sha256"] = hash_file(candidate_path).sha256
    _replace_atomically(
        (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        root / "panels" / f"{panel.panel_id}.build.json",
    )
    report = validate_research_panel(root, panel.panel_id, workspace_root=workspace)
    if not report.valid:
        raise ResearchPanelError(f"materialized panel is invalid: {report.errors[0]}")
    return panel


def validate_research_panel(
    research_root: str | Path,
    panel_id: str,
    *,
    workspace_root: str | Path,
) -> PanelValidationReport:
    """Validate panel completeness, provenance, build identity, and standard checks."""

    errors: list[str] = []
    warnings: list[str] = []
    try:
        root, workspace, _ = _resolve_notebook(research_root, workspace_root)
        panel_path = root / "panels" / f"{panel_id}.json"
        panel = ResearchPanel.model_validate_json(panel_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, ValidationError) as error:
        return PanelValidationReport(False, None, (f"invalid panel: {error}",), (), 0, 0)
    if panel.panel_id != panel_id:
        errors.append("panel filename does not match panel_id")
    catalog = _load_source_catalog(root / "sources.md")
    source_records = {
        source_id: _inspect_source(source_id, artifact_ref, workspace)
        for source_id, artifact_ref in catalog.items()
    }
    expected_periods = set(panel.periods).difference(panel.missing_periods)
    for row in panel.rows:
        actual_periods = {value.period for value in row.values}
        missing = expected_periods.difference(actual_periods)
        if missing:
            errors.append(f"panel row silently omits period: {row.metric_id} -> {sorted(missing)[0]}")
        for value in row.values:
            for source_ref in value.source_refs:
                source = source_records.get(source_ref.source_id)
                if source is None:
                    errors.append(f"panel cites unknown source: {source_ref.source_id}")
                elif source_ref.end_line > source.line_count:
                    errors.append(
                        f"panel citation exceeds source lines: {source_ref.source_id}:L{source_ref.end_line}"
                    )
    _validate_balance_sheet(panel, errors)
    try:
        from .coverage import load_method_panel_specs

        spec = load_method_panel_specs(root).get(panel.panel_id)
        if spec is not None:
            metric_ids = {row.metric_id for row in panel.rows}
            for group in spec.required_metric_groups:
                if not metric_ids.intersection(group):
                    errors.append(
                        f"panel is missing required metric group: {panel.panel_id} -> "
                        f"{'/'.join(group)}; add a semantic row or explicit not_disclosed row"
                    )
    except (OSError, ValueError):
        pass
    build_path = root / "panels" / f"{panel_id}.build.json"
    rendered_path = root / "panels" / f"{panel_id}.md"
    try:
        build = json.loads(build_path.read_text(encoding="utf-8"))
        artifact_pairs = [
            ("mapping_ref", "mapping_sha256"),
            ("panel_ref", "panel_sha256"),
            ("rendered_ref", "rendered_sha256"),
        ]
        if "candidates_ref" in build:
            artifact_pairs.append(("candidates_ref", "candidates_sha256"))
        for ref_key, hash_key in artifact_pairs:
            path = (root / build[ref_key]).resolve()
            if root not in path.parents or path.is_symlink() or not path.is_file():
                errors.append(f"panel build references unsafe artifact: {ref_key}")
            elif hash_file(path).sha256 != build[hash_key]:
                errors.append(f"panel build artifact changed: {build[ref_key]}")
        if rendered_path.read_text(encoding="utf-8") != render_research_panel(panel):
            errors.append("rendered panel does not match panel JSON")
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as error:
        errors.append(f"invalid panel build record: {error}")
    return PanelValidationReport(
        not errors,
        panel.panel_id,
        tuple(errors),
        tuple(warnings),
        len(panel.periods),
        len(panel.rows),
    )


def load_research_panel(research_root: str | Path, panel_id: str) -> ResearchPanel:
    path = Path(research_root) / "panels" / f"{panel_id}.json"
    try:
        return ResearchPanel.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError) as error:
        raise ResearchPanelError(f"invalid panel {panel_id}: {error}") from error


def render_research_panel(panel: ResearchPanel) -> str:
    """Render a stable metric-by-period Markdown view for research and reporting."""

    lines = [f"<!-- rf:panel={panel.panel_id} -->", f"# {panel.title}", ""]
    if panel.default_unit:
        lines.extend((f"Default unit: {panel.default_unit}", ""))
    headers = ("Metric", "Section", "Scope", "Unit", *panel.periods)
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    values_by_row = {
        row.metric_id: {value.period: value for value in row.values} for row in panel.rows
    }
    for row in panel.rows:
        cells = [
            row.label,
            row.section or "-",
            row.scope,
            row.unit or panel.default_unit or "-",
        ]
        for period in panel.periods:
            value = values_by_row[row.metric_id].get(period)
            cells.append(_render_panel_value(value))
        lines.append("| " + " | ".join(_escape_cell(cell) for cell in cells) + " |")
    if panel.comparability_notes:
        lines.extend(("", "## Comparability notes", ""))
        lines.extend(f"- {note}" for note in panel.comparability_notes)
    if panel.missing_periods:
        lines.extend(("", f"Missing periods: {', '.join(panel.missing_periods)}"))
    return "\n".join(lines).rstrip() + "\n"


def _candidate_rows(payload: object) -> list[list[str]]:
    if not isinstance(payload, list):
        return []
    result: list[list[str]] = []
    for row in payload:
        if not isinstance(row, list):
            continue
        cells: list[str] = []
        for cell in row:
            cells.append(str(cell.get("text", "")) if isinstance(cell, dict) else str(cell))
        result.append(cells)
    return result


def _build_panel_row(
    payload: dict[str, Any], candidates: dict[str, dict[str, Any]], errors: list[str]
) -> ResearchPanelRow:
    row_scope = str(payload["scope"])
    values: list[ResearchPanelValue] = []
    for value_payload in payload.get("values") or []:
        status = str(value_payload["status"])
        if status not in {"reported", "derived"}:
            source_refs: tuple[PanelSourceRef, ...] = ()
            source_payload = value_payload.get("source_ref")
            if source_payload is not None:
                if not isinstance(source_payload, dict):
                    raise ValueError("source_ref must be an object")
                source_refs = (PanelSourceRef.model_validate(source_payload),)
            values.append(
                ResearchPanelValue(
                    period=value_payload["period"],
                    status=status,
                    source_refs=source_refs,
                    note=value_payload.get("note"),
                )
            )
            continue
        if "value" in value_payload:
            adjudication = str(value_payload.get("adjudication", "")).strip()
            if not adjudication:
                raise ValueError("Agent-adjudicated value requires adjudication rationale")
            source_payload = value_payload.get("source_ref")
            if not isinstance(source_payload, dict):
                raise ValueError("Agent-adjudicated value requires source_ref")
            source_ref = PanelSourceRef.model_validate(source_payload)
            try:
                number = Decimal(str(value_payload["value"]).replace(",", ""))
            except InvalidOperation as error:
                raise ValueError("Agent-adjudicated value is not numeric") from error
            values.append(
                ResearchPanelValue(
                    period=value_payload["period"],
                    value=number,
                    status=status,
                    source_refs=(source_ref,),
                    formula=value_payload.get("formula"),
                    note=adjudication,
                )
            )
            continue
        candidate = candidates.get(str(value_payload.get("candidate_id", "")))
        if candidate is None:
            raise ValueError(f"unknown candidate_id: {value_payload.get('candidate_id')}")
        source_scope = str(value_payload.get("source_scope", row_scope)).strip()
        if source_scope != row_scope:
            errors.append(
                f"scope mismatch {payload['metric_id']} {value_payload['period']}: "
                f"{source_scope} != {row_scope}; mark not_comparable or correct mapping"
            )
            continue
        row_index = int(value_payload["row_index"])
        column_index = int(value_payload["column_index"])
        try:
            raw = candidate["rows"][row_index][column_index]
        except (IndexError, TypeError) as error:
            raise ValueError("candidate row or column index is out of range") from error
        number = _parse_number(str(raw))
        source_ref = PanelSourceRef(
            source_id=candidate["source_id"],
            start_line=candidate["start_line"],
            end_line=candidate["end_line"],
        )
        values.append(
            ResearchPanelValue(
                period=value_payload["period"],
                value=number,
                status=status,
                source_refs=(source_ref,),
                formula=value_payload.get("formula"),
                note=value_payload.get("note"),
            )
        )
    return ResearchPanelRow(
        metric_id=payload["metric_id"],
        label=payload["label"],
        section=payload.get("section"),
        scope=row_scope,
        unit=payload.get("unit"),
        values=tuple(values),
    )


def _parse_number(value: str) -> Decimal:
    text = value.replace("\u00a0", " ").strip()
    if text in {"", "-", "—", "–", "N/A", "n/a"}:
        raise ValueError(f"cell is not numeric: {value!r}")
    negative = text.startswith("(") and text.rstrip(" %").endswith(")")
    match = _NUMBER.fullmatch(text)
    if match is None:
        raise ValueError(f"cell is not numeric: {value!r}")
    sign, digits = match.groups()
    try:
        number = Decimal(digits.replace(",", ""))
    except InvalidOperation as error:
        raise ValueError(f"cell is not numeric: {value!r}") from error
    if negative or sign == "-":
        number = -number
    return number


def _render_panel_value(value: ResearchPanelValue | None) -> str:
    if value is None:
        return "missing"
    if value.value is not None:
        return format(value.value, "f")
    labels = {
        "not_disclosed": "not disclosed",
        "not_comparable": "not comparable",
        "not_applicable": "n/a",
    }
    return labels.get(value.status, value.status)


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _validate_balance_sheet(panel: ResearchPanel, errors: list[str]) -> None:
    rows = {row.metric_id: row for row in panel.rows}
    assets_row = next((rows[item] for item in ("total_assets",) if item in rows), None)
    liabilities_row = next((rows[item] for item in ("total_liabilities",) if item in rows), None)
    equity_row = next(
        (
            rows[item]
            for item in ("total_equity", "stockholders_equity", "shareholders_equity")
            if item in rows
        ),
        None,
    )
    if assets_row is None or liabilities_row is None or equity_row is None:
        return
    values = {
        "assets": {item.period: item.value for item in assets_row.values if item.value is not None},
        "liabilities": {
            item.period: item.value for item in liabilities_row.values if item.value is not None
        },
        "equity": {item.period: item.value for item in equity_row.values if item.value is not None},
    }
    for period in panel.periods:
        assets = values["assets"].get(period)
        liabilities = values["liabilities"].get(period)
        equity = values["equity"].get(period)
        if None in {assets, liabilities, equity}:
            continue
        tolerance = max(Decimal("1"), abs(assets) * Decimal("0.001"))
        if abs(assets - liabilities - equity) > tolerance:
            errors.append(f"balance sheet does not reconcile for {period}")
