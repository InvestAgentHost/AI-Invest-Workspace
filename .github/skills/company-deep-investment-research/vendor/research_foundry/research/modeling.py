"""Evidence-bound quantitative research models and deterministic outputs."""

from __future__ import annotations

from datetime import UTC, datetime, time
from decimal import Decimal
from html import escape
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import zipfile
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError, field_validator
import xlsxwriter

from research_foundry.runtime.artifacts import hash_file, publish_bytes

from .contracts import (
    PublishedArtifact,
    QuantitativeChartSpec,
    QuantitativeCheckResult,
    QuantitativeModelChecks,
    QuantitativeModelInput,
    QuantitativeModelManifest,
    QuantitativeModelSpec,
    ResearchBrief,
)
from .evidence import (
    EvidenceLocatorDraft,
    ResearchEvidenceBindingError,
    bind_evidence_locator,
)


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
_PLACEHOLDER = re.compile(r"(?:\bTODO\b|\bTBD\b|\[Agent synthesis required\])", re.IGNORECASE)
_PALETTE = ("#24557A", "#D46A2E", "#2D7D61", "#8B5FA8", "#B78B1E", "#B44C55")


class QuantitativeModelError(ValueError):
    """Raised when a quantitative research model cannot be built safely."""


class QuantitativeModelInputDraft(BaseModel):
    """Small semantic model input before evidence identities are attached."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    input_id: Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[A-Za-z][A-Za-z0-9_-]{2,95}$")]
    metric: NonEmptyStr
    value: Decimal
    period: NonEmptyStr
    unit: NonEmptyStr
    entity: NonEmptyStr
    perimeter: NonEmptyStr
    data_state: Literal["reported", "adjusted", "derived", "guidance", "model", "scenario"]
    definition: NonEmptyStr
    formula: NonEmptyStr | None = None
    scenario: NonEmptyStr | None = None
    evidence: Annotated[tuple[EvidenceLocatorDraft, ...], Field(min_length=1)]

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: Decimal) -> Decimal:
        if not value.is_finite():
            raise ValueError("model input value must be finite")
        return value


def build_quantitative_model(
    model_directory: str | Path,
    *,
    workspace_root: str | Path,
) -> QuantitativeModelManifest:
    """Bind model inputs, recompute checks, and generate workbook and charts."""

    model_dir = Path(model_directory).expanduser().resolve()
    workspace = Path(workspace_root).expanduser().resolve()
    if not _is_below(model_dir, workspace) or model_dir.parent.name != "models":
        raise QuantitativeModelError("model directory must be below a research models directory")
    research_root = model_dir.parent.parent
    if not (research_root / "research_brief.yaml").is_file():
        raise QuantitativeModelError("model directory is not below an initialized research run")
    if (research_root / "release_manifest.json").exists():
        raise QuantitativeModelError("published research cannot rebuild a model")
    if model_dir.is_symlink() or not model_dir.is_dir():
        raise QuantitativeModelError("model directory must be a regular directory")

    brief = _load_json_or_yaml_brief(research_root / "research_brief.yaml")
    spec = _load_model(model_dir / "model_spec.json", QuantitativeModelSpec, "model spec")
    if spec.model_id != model_dir.name:
        raise QuantitativeModelError("model directory name does not match model_id")
    if spec.research_id != brief.research_id:
        raise QuantitativeModelError("model research_id does not match research brief")

    notes_path = model_dir / "model_notes.md"
    notes = _read_substantive_notes(notes_path)
    inputs_path = model_dir / "model_inputs.jsonl"
    inputs = bind_model_inputs(inputs_path, workspace_root=workspace)
    input_by_id = {item.input_id: item for item in inputs}

    checks = _run_checks(spec, input_by_id)
    checks_path = model_dir / "model_checks.json"
    _replace_atomically(
        (checks.model_dump_json(indent=2) + "\n").encode("utf-8"),
        checks_path,
    )
    if not checks.all_passed:
        failed = next(result.check_id for result in checks.results if result.status == "failed")
        raise QuantitativeModelError(f"model check failed: {failed}")

    _validate_charts(spec.charts, input_by_id)
    figures_dir = model_dir / "figures"
    if figures_dir.exists():
        if figures_dir.is_symlink() or not figures_dir.is_dir():
            raise QuantitativeModelError("model figures path must be a regular directory")
        shutil.rmtree(figures_dir)
    figures_dir.mkdir()
    for chart in spec.charts:
        _write_svg(chart, input_by_id, figures_dir / f"{chart.chart_id}.svg")

    workbook_path = model_dir / "model_workbook.xlsx"
    _write_workbook(
        workbook_path,
        brief=brief,
        spec=spec,
        inputs=inputs,
        checks=checks,
        notes=notes,
    )

    manifest_path = model_dir / "model_manifest.json"
    artifacts = tuple(
        _published_artifact(path, workspace)
        for path in _model_files(model_dir, exclude_manifest=True)
    )
    manifest = QuantitativeModelManifest(
        model_id=spec.model_id,
        research_id=spec.research_id,
        purpose=spec.purpose,
        input_count=len(inputs),
        check_count=len(checks.results),
        chart_count=len(spec.charts),
        artifacts=artifacts,
    )
    _replace_atomically(
        (manifest.model_dump_json(indent=2) + "\n").encode("utf-8"),
        manifest_path,
    )
    return verify_quantitative_model(model_dir, workspace_root=workspace)


def bind_model_inputs(
    input_path: str | Path,
    *,
    workspace_root: str | Path,
) -> tuple[QuantitativeModelInput, ...]:
    """Bind semantic model input evidence and atomically canonicalize JSONL."""

    path_input = Path(input_path).expanduser()
    if path_input.is_symlink() or not path_input.is_file():
        raise QuantitativeModelError("model inputs must be a regular JSONL file")
    path = path_input.resolve()
    workspace = Path(workspace_root).expanduser().resolve()
    if not _is_below(path, workspace):
        raise QuantitativeModelError("model inputs must stay below workspace root")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise QuantitativeModelError(f"unable to read model inputs: {error}") from error

    identity_cache: dict[Path, tuple[str, int]] = {}
    values: list[QuantitativeModelInput] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            canonical = QuantitativeModelInput.model_validate_json(line)
        except ValidationError:
            canonical = None
        if canonical is not None:
            _verify_canonical_input(canonical, workspace, identity_cache)
            values.append(canonical)
            continue
        try:
            draft = QuantitativeModelInputDraft.model_validate_json(line)
            values.append(
                QuantitativeModelInput(
                    input_id=draft.input_id,
                    metric=draft.metric,
                    value=draft.value,
                    period=draft.period,
                    unit=draft.unit,
                    entity=draft.entity,
                    perimeter=draft.perimeter,
                    data_state=draft.data_state,
                    definition=draft.definition,
                    formula=draft.formula,
                    scenario=draft.scenario,
                    evidence=tuple(
                        bind_evidence_locator(locator, workspace, identity_cache)
                        for locator in draft.evidence
                    ),
                )
            )
        except (ValidationError, ResearchEvidenceBindingError) as error:
            raise QuantitativeModelError(
                f"invalid model input line {line_number}: {error}"
            ) from error
    if not values:
        raise QuantitativeModelError("model inputs contain no values")
    ids = [item.input_id for item in values]
    if len(ids) != len(set(ids)):
        raise QuantitativeModelError("model inputs contain duplicate input_id")
    ordered = tuple(sorted(values, key=lambda item: item.input_id))
    rendered = "".join(
        json.dumps(item.model_dump(mode="json", exclude_none=True), ensure_ascii=False, sort_keys=True)
        + "\n"
        for item in ordered
    ).encode("utf-8")
    _replace_atomically(rendered, path)
    return ordered


def verify_quantitative_model(
    model_directory: str | Path,
    *,
    workspace_root: str | Path,
) -> QuantitativeModelManifest:
    """Verify a generated model manifest, artifacts, inputs, checks, and workbook."""

    model_dir = Path(model_directory).expanduser().resolve()
    workspace = Path(workspace_root).expanduser().resolve()
    if not _is_below(model_dir, workspace) or model_dir.is_symlink() or not model_dir.is_dir():
        raise QuantitativeModelError("model directory must be a regular directory below workspace root")
    manifest = _load_model(
        model_dir / "model_manifest.json", QuantitativeModelManifest, "model manifest"
    )
    if manifest.model_id != model_dir.name:
        raise QuantitativeModelError("model manifest ID does not match directory")
    expected_refs = {
        path.relative_to(workspace).as_posix()
        for path in _model_files(model_dir, exclude_manifest=True)
    }
    manifest_refs = {artifact.artifact_ref for artifact in manifest.artifacts}
    if expected_refs != manifest_refs:
        raise QuantitativeModelError("model artifact inventory does not match manifest")
    for artifact in manifest.artifacts:
        path = (workspace / artifact.artifact_ref).resolve()
        if not _is_below(path, workspace) or path.is_symlink() or not path.is_file():
            raise QuantitativeModelError(f"unsafe or missing model artifact: {artifact.artifact_ref}")
        identity = hash_file(path)
        if identity.sha256 != artifact.sha256 or identity.byte_size != artifact.byte_size:
            raise QuantitativeModelError(f"model artifact identity mismatch: {artifact.artifact_ref}")

    inputs = _load_jsonl(model_dir / "model_inputs.jsonl", QuantitativeModelInput, "model inputs")
    checks = _load_model(model_dir / "model_checks.json", QuantitativeModelChecks, "model checks")
    spec = _load_model(model_dir / "model_spec.json", QuantitativeModelSpec, "model spec")
    if not checks.all_passed:
        raise QuantitativeModelError("model contains failed checks")
    if manifest.input_count != len(inputs) or manifest.check_count != len(checks.results):
        raise QuantitativeModelError("model manifest counts do not match artifacts")
    if manifest.chart_count != len(spec.charts):
        raise QuantitativeModelError("model manifest chart count does not match spec")
    workbook = model_dir / "model_workbook.xlsx"
    if not zipfile.is_zipfile(workbook):
        raise QuantitativeModelError("model workbook is not a valid XLSX package")
    with zipfile.ZipFile(workbook) as archive:
        if "xl/workbook.xml" not in archive.namelist():
            raise QuantitativeModelError("model workbook is missing workbook.xml")
    _read_substantive_notes(model_dir / "model_notes.md")
    return manifest


def _verify_canonical_input(
    item: QuantitativeModelInput,
    workspace: Path,
    identity_cache: dict[Path, tuple[str, int]],
) -> None:
    for evidence in item.evidence:
        locator = EvidenceLocatorDraft(
            artifact_ref=evidence.artifact_ref,
            start_line=evidence.start_line,
            end_line=evidence.end_line,
        )
        bound = bind_evidence_locator(locator, workspace, identity_cache)
        if bound != evidence:
            raise QuantitativeModelError(
                f"model input evidence identity changed: {item.input_id}"
            )


def _run_checks(
    spec: QuantitativeModelSpec,
    inputs: dict[str, QuantitativeModelInput],
) -> QuantitativeModelChecks:
    results: list[QuantitativeCheckResult] = []
    for check in spec.checks:
        selected: list[QuantitativeModelInput] = []
        observed = Decimal("0")
        for term in check.terms:
            item = inputs.get(term.input_id)
            if item is None:
                raise QuantitativeModelError(
                    f"model check {check.check_id} references missing input: {term.input_id}"
                )
            selected.append(item)
            observed += term.coefficient * item.value
        _require_check_scope(check.check_id, "period", check.period, selected)
        _require_check_scope(check.check_id, "unit", check.unit, selected)
        _require_check_scope(check.check_id, "perimeter", check.perimeter, selected)
        difference = observed - check.expected_value
        results.append(
            QuantitativeCheckResult(
                check_id=check.check_id,
                category=check.category,
                description=check.description,
                status="passed" if abs(difference) <= check.tolerance else "failed",
                observed_value=observed,
                expected_value=check.expected_value,
                difference=difference,
                tolerance=check.tolerance,
                input_ids=tuple(term.input_id for term in check.terms),
            )
        )
    return QuantitativeModelChecks(
        model_id=spec.model_id,
        all_passed=all(result.status == "passed" for result in results),
        results=tuple(results),
    )


def _require_check_scope(
    check_id: str,
    field_name: str,
    expected: str | None,
    inputs: list[QuantitativeModelInput],
) -> None:
    if expected is None:
        return
    mismatched = [item.input_id for item in inputs if getattr(item, field_name) != expected]
    if mismatched:
        raise QuantitativeModelError(
            f"model check {check_id} has incompatible {field_name}: {mismatched[0]}"
        )


def _validate_charts(
    charts: tuple[QuantitativeChartSpec, ...],
    inputs: dict[str, QuantitativeModelInput],
) -> None:
    for chart in charts:
        expected_periods: tuple[str, ...] | None = None
        for series in chart.series:
            selected = []
            for input_id in series.input_ids:
                item = inputs.get(input_id)
                if item is None:
                    raise QuantitativeModelError(
                        f"chart {chart.chart_id} references missing input: {input_id}"
                    )
                if item.unit != chart.unit:
                    raise QuantitativeModelError(
                        f"chart {chart.chart_id} has incompatible unit: {input_id}"
                    )
                selected.append(item)
            periods = tuple(item.period for item in selected)
            if len(periods) != len(set(periods)):
                raise QuantitativeModelError(
                    f"chart {chart.chart_id} series {series.name} repeats a period"
                )
            if expected_periods is None:
                expected_periods = periods
            elif periods != expected_periods:
                raise QuantitativeModelError(
                    f"chart {chart.chart_id} series use different period sequences"
                )


def _write_workbook(
    destination: Path,
    *,
    brief: ResearchBrief,
    spec: QuantitativeModelSpec,
    inputs: tuple[QuantitativeModelInput, ...],
    checks: QuantitativeModelChecks,
    notes: str,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        suffix=".xlsx", dir=destination.parent, prefix=f".{destination.name}.", delete=False
    )
    temporary = Path(handle.name)
    handle.close()
    try:
        workbook = xlsxwriter.Workbook(temporary)
        workbook.set_properties(
            {
                "title": spec.purpose,
                "subject": brief.decision_question,
                "author": "ResearchFoundry",
                "comments": "Generated from evidence-bound quantitative model inputs.",
                "created": datetime.combine(brief.as_of, time.min, tzinfo=UTC),
            }
        )
        header = workbook.add_format({"bold": True, "bg_color": "#D9E3EA", "border": 1})
        text_wrap = workbook.add_format({"text_wrap": True, "valign": "top"})
        number = workbook.add_format({"num_format": "0.00########"})

        control = workbook.add_worksheet("Control")
        control.write_row(0, 0, ["Field", "Value"], header)
        control.write_row(1, 0, ["Research ID", brief.research_id])
        control.write_row(2, 0, ["Model ID", spec.model_id])
        control.write_row(3, 0, ["As of", brief.as_of.isoformat()])
        control.write_row(4, 0, ["Decision question", brief.decision_question])
        control.write_row(5, 0, ["Purpose", spec.purpose])
        control.write_row(7, 0, ["Model notes", notes], text_wrap)
        control.set_column(0, 0, 22)
        control.set_column(1, 1, 100)
        control.set_row(7, 90)

        input_sheet = workbook.add_worksheet("Model Inputs")
        input_headers = [
            "Input ID", "Metric", "Value", "Period", "Unit", "Entity", "Perimeter",
            "Data state", "Definition", "Formula", "Scenario", "Evidence",
        ]
        input_sheet.write_row(0, 0, input_headers, header)
        for row, item in enumerate(inputs, start=1):
            input_sheet.write(row, 0, item.input_id)
            input_sheet.write(row, 1, item.metric)
            input_sheet.write_number(row, 2, float(item.value), number)
            input_sheet.write(row, 3, item.period)
            input_sheet.write(row, 4, item.unit)
            input_sheet.write(row, 5, item.entity)
            input_sheet.write(row, 6, item.perimeter)
            input_sheet.write(row, 7, item.data_state)
            input_sheet.write(row, 8, item.definition, text_wrap)
            input_sheet.write(row, 9, item.formula or "", text_wrap)
            input_sheet.write(row, 10, item.scenario or "")
            evidence = "; ".join(
                f"{ref.artifact_ref}:{ref.start_line}-{ref.end_line} [{ref.artifact_sha256}]"
                for ref in item.evidence
            )
            input_sheet.write(row, 11, evidence, text_wrap)
        input_sheet.freeze_panes(1, 0)
        input_sheet.autofilter(0, 0, len(inputs), len(input_headers) - 1)
        input_sheet.set_column(0, 1, 28)
        input_sheet.set_column(2, 2, 16)
        input_sheet.set_column(3, 7, 20)
        input_sheet.set_column(8, 11, 55)

        check_sheet = workbook.add_worksheet("Checks")
        check_headers = [
            "Check ID", "Category", "Description", "Status", "Observed", "Expected",
            "Difference", "Tolerance", "Input IDs",
        ]
        check_sheet.write_row(0, 0, check_headers, header)
        for row, result in enumerate(checks.results, start=1):
            check_sheet.write(row, 0, result.check_id)
            check_sheet.write(row, 1, result.category)
            check_sheet.write(row, 2, result.description, text_wrap)
            check_sheet.write(row, 3, result.status)
            for column, value in enumerate(
                (result.observed_value, result.expected_value, result.difference, result.tolerance),
                start=4,
            ):
                check_sheet.write_number(row, column, float(value), number)
            check_sheet.write(row, 8, ", ".join(result.input_ids), text_wrap)
        check_sheet.set_column(0, 1, 24)
        check_sheet.set_column(2, 2, 55)
        check_sheet.set_column(3, 7, 16)
        check_sheet.set_column(8, 8, 55)

        data_sheet = workbook.add_worksheet("Charts Data")
        chart_sheet = workbook.add_worksheet("Charts")
        data_column = 0
        chart_row = 0
        input_by_id = {item.input_id: item for item in inputs}
        for chart_index, chart_spec in enumerate(spec.charts):
            chart = workbook.add_chart({"type": "line" if chart_spec.chart_type == "line" else "column"})
            period_count = len(chart_spec.series[0].input_ids)
            data_sheet.write(0, data_column, "Period", header)
            periods = [input_by_id[input_id].period for input_id in chart_spec.series[0].input_ids]
            for row, period in enumerate(periods, start=1):
                data_sheet.write(row, data_column, period)
            for series_index, series in enumerate(chart_spec.series, start=1):
                column = data_column + series_index
                data_sheet.write(0, column, series.name, header)
                for row, input_id in enumerate(series.input_ids, start=1):
                    data_sheet.write_number(row, column, float(input_by_id[input_id].value), number)
                chart.add_series(
                    {
                        "name": ["Charts Data", 0, column],
                        "categories": ["Charts Data", 1, data_column, period_count, data_column],
                        "values": ["Charts Data", 1, column, period_count, column],
                        "line": {"color": _PALETTE[(series_index - 1) % len(_PALETTE)]},
                        "fill": {"color": _PALETTE[(series_index - 1) % len(_PALETTE)]},
                    }
                )
            chart.set_title({"name": chart_spec.title})
            chart.set_y_axis({"name": chart_spec.unit, "major_gridlines": {"visible": True}})
            chart.set_legend({"position": "bottom"})
            chart.set_style(10)
            chart_sheet.insert_chart(chart_row, 0, chart, {"x_scale": 1.35, "y_scale": 1.2})
            chart_row += 24
            data_column += len(chart_spec.series) + 2
        data_sheet.hide()
        chart_sheet.set_column(0, 12, 12)
        workbook.close()
        os.replace(temporary, destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _write_svg(
    chart: QuantitativeChartSpec,
    inputs: dict[str, QuantitativeModelInput],
    destination: Path,
) -> None:
    width, height = 960, 480
    left, right, top, bottom = 90, 30, 65, 85
    plot_width = width - left - right
    plot_height = height - top - bottom
    periods = [inputs[input_id].period for input_id in chart.series[0].input_ids]
    values = [
        float(inputs[input_id].value)
        for series in chart.series
        for input_id in series.input_ids
    ]
    low = min(0.0, min(values))
    high = max(0.0, max(values))
    if high == low:
        high = low + 1.0

    def x_at(index: int) -> float:
        if len(periods) == 1:
            return left + plot_width / 2
        return left + plot_width * index / (len(periods) - 1)

    def y_at(value: float) -> float:
        return top + plot_height * (high - value) / (high - low)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width / 2}" y="32" text-anchor="middle" font-family="Arial, sans-serif" font-size="22" font-weight="700" fill="#20252b">{escape(chart.title)}</text>',
    ]
    for tick in range(6):
        value = low + (high - low) * tick / 5
        y = y_at(value)
        parts.append(f'<line x1="{left}" y1="{y:.2f}" x2="{width-right}" y2="{y:.2f}" stroke="#d8dde2" stroke-width="1"/>')
        parts.append(f'<text x="{left-10}" y="{y+4:.2f}" text-anchor="end" font-family="Arial, sans-serif" font-size="12" fill="#4b5560">{value:,.2f}</text>')
    for index, period in enumerate(periods):
        x = x_at(index)
        parts.append(f'<text x="{x:.2f}" y="{height-bottom+25}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#4b5560">{escape(period)}</text>')
    parts.append(f'<text x="20" y="{top + plot_height/2}" text-anchor="middle" transform="rotate(-90 20 {top + plot_height/2})" font-family="Arial, sans-serif" font-size="13" fill="#4b5560">{escape(chart.unit)}</text>')

    for series_index, series in enumerate(chart.series):
        color = _PALETTE[series_index % len(_PALETTE)]
        series_values = [float(inputs[input_id].value) for input_id in series.input_ids]
        if chart.chart_type == "line":
            points = " ".join(
                f"{x_at(index):.2f},{y_at(value):.2f}"
                for index, value in enumerate(series_values)
            )
            parts.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="3"/>')
            for index, value in enumerate(series_values):
                parts.append(f'<circle cx="{x_at(index):.2f}" cy="{y_at(value):.2f}" r="4" fill="{color}"/>')
        else:
            group_width = plot_width / max(len(periods), 1) * 0.7
            bar_width = group_width / len(chart.series)
            zero_y = y_at(0)
            for index, value in enumerate(series_values):
                center = left + plot_width * (index + 0.5) / len(periods)
                x = center - group_width / 2 + series_index * bar_width
                value_y = y_at(value)
                y = min(zero_y, value_y)
                bar_height = max(abs(zero_y - value_y), 1)
                parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width*0.86:.2f}" height="{bar_height:.2f}" fill="{color}"/>')
        legend_x = left + series_index * 180
        parts.append(f'<rect x="{legend_x}" y="{height-28}" width="14" height="14" fill="{color}"/>')
        parts.append(f'<text x="{legend_x+20}" y="{height-16}" font-family="Arial, sans-serif" font-size="12" fill="#30363d">{escape(series.name)}</text>')
    parts.append("</svg>\n")
    publish_bytes("".join(parts).encode("utf-8"), destination)


def _published_artifact(path: Path, workspace: Path) -> PublishedArtifact:
    identity = hash_file(path)
    return PublishedArtifact(
        artifact_ref=path.relative_to(workspace).as_posix(),
        sha256=identity.sha256,
        byte_size=identity.byte_size,
    )


def _model_files(model_dir: Path, *, exclude_manifest: bool) -> list[Path]:
    files: list[Path] = []
    for path in model_dir.rglob("*"):
        if path.is_symlink():
            raise QuantitativeModelError(
                f"model cannot contain symlink: {path.relative_to(model_dir)}"
            )
        if not path.is_file():
            continue
        if exclude_manifest and path.name == "model_manifest.json":
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(model_dir).as_posix())


def _load_model(path: Path, model: type[BaseModel], label: str):
    if path.is_symlink():
        raise QuantitativeModelError(f"{label} cannot be a symlink")
    try:
        return model.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise QuantitativeModelError(f"invalid or missing {label}: {error}") from error


def _load_jsonl(path: Path, model: type[BaseModel], label: str) -> tuple[BaseModel, ...]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise QuantitativeModelError(f"invalid or missing {label}: {error}") from error
    values = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            values.append(model.model_validate_json(line))
        except ValueError as error:
            raise QuantitativeModelError(f"invalid {label} line {line_number}: {error}") from error
    if not values:
        raise QuantitativeModelError(f"{label} contain no values")
    return tuple(values)


def _load_json_or_yaml_brief(path: Path) -> ResearchBrief:
    import yaml

    try:
        return ResearchBrief.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, yaml.YAMLError) as error:
        raise QuantitativeModelError(f"invalid research brief: {error}") from error


def _read_substantive_notes(path: Path) -> str:
    if path.is_symlink():
        raise QuantitativeModelError("model notes cannot be a symlink")
    try:
        notes = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise QuantitativeModelError(f"invalid or missing model notes: {error}") from error
    if len(re.sub(r"\s+", "", notes)) < 100:
        raise QuantitativeModelError("model notes are not substantive")
    if _PLACEHOLDER.search(notes):
        raise QuantitativeModelError("model notes contain a placeholder")
    return notes


def _replace_atomically(data: bytes, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb", dir=destination.parent, prefix=f".{destination.name}.", delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temporary, destination)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise


def _is_below(path: Path, root: Path) -> bool:
    return path != root and root in path.parents
