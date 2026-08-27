"""Mechanical validation and immutable publication for research workspaces."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

import yaml

from research_foundry.runtime.artifacts import hash_file, publish_bytes

from .contracts import (
    EvidenceRef,
    PublishedArtifact,
    QuantitativeModelInput,
    ResearchBrief,
    ResearchClaim,
    ResearchQualityReport,
    ResearchReleaseManifest,
    WorkPackageBrief,
    WorkPackageResult,
)
from .modeling import QuantitativeModelError, verify_quantitative_model
from .sources import ResearchSourceError, verify_research_source_manifest


_PLACEHOLDER = re.compile(r"(?:\bTODO\b|\bTBD\b|\[Agent synthesis required\])", re.IGNORECASE)


class ResearchValidationError(ValueError):
    """Raised when a research workspace cannot be published or verified."""


@dataclass(frozen=True, slots=True)
class ResearchValidationReport:
    """Agent-readable result of deterministic research checks."""

    valid: bool
    publishable: bool
    research_id: str | None
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    package_count: int
    claim_count: int
    key_claim_count: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_research(
    research_root: str | Path,
    *,
    workspace_root: str | Path,
) -> ResearchValidationReport:
    """Validate structure, evidence, handoffs, challenge, and release readiness."""

    root = Path(research_root).expanduser().resolve()
    workspace = Path(workspace_root).expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    if not _is_below(root, workspace):
        return _report(errors=("research root must stay below workspace root",))

    brief = _load_model(
        root / "research_brief.yaml",
        ResearchBrief,
        "research brief",
        errors,
        yaml_input=True,
    )
    if brief is None:
        return _report(errors=tuple(errors))
    if root.name != brief.research_id:
        errors.append("research root name does not match research_id")

    package_briefs: dict[str, WorkPackageBrief] = {}
    package_results: dict[str, WorkPackageResult] = {}
    all_claims: dict[str, ResearchClaim] = {}
    consumed_evidence_refs: set[str] = set()
    packages_root = root / "packages"
    package_dirs = sorted(
        path for path in packages_root.iterdir() if path.is_dir()
    ) if packages_root.is_dir() else []
    if not package_dirs:
        errors.append("research contains no work packages")

    hash_cache: dict[Path, tuple[str, int]] = {}
    for package_dir in package_dirs:
        package_label = package_dir.name
        package_brief = _load_model(
            package_dir / "brief.json",
            WorkPackageBrief,
            f"package {package_label} brief",
            errors,
        )
        result = _load_model(
            package_dir / "result.json",
            WorkPackageResult,
            f"package {package_label} result",
            errors,
        )
        workpaper = _read_text(package_dir / "workpaper.md", f"package {package_label} workpaper", errors)
        if workpaper is not None:
            if len(re.sub(r"\s+", "", workpaper)) < 40:
                errors.append(f"package {package_label} workpaper is not substantive")
            if _PLACEHOLDER.search(workpaper):
                errors.append(f"package {package_label} workpaper contains a placeholder")
        claims = _load_jsonl_models(
            package_dir / "claims.jsonl",
            ResearchClaim,
            f"package {package_label} claims",
            errors,
        )
        local_claims: dict[str, ResearchClaim] = {}
        for claim in claims:
            if claim.claim_id in local_claims:
                errors.append(f"package {package_label} contains duplicate claim_id: {claim.claim_id}")
            elif claim.claim_id in all_claims:
                errors.append(f"claim_id is duplicated across packages: {claim.claim_id}")
            else:
                local_claims[claim.claim_id] = claim
                all_claims[claim.claim_id] = claim
            for evidence in (*claim.evidence, *claim.counterevidence):
                _validate_evidence(evidence, workspace, hash_cache, errors, claim.claim_id)
                consumed_evidence_refs.add(evidence.artifact_ref)
        if package_brief is not None:
            if package_brief.package_id != package_label:
                errors.append(f"package directory does not match brief package_id: {package_label}")
            if package_brief.package_id in package_briefs:
                errors.append(f"duplicate package_id: {package_brief.package_id}")
            package_briefs[package_brief.package_id] = package_brief
        if result is not None:
            if result.package_id != package_label:
                errors.append(f"package directory does not match result package_id: {package_label}")
            missing_claims = sorted(set(result.material_claim_ids).difference(local_claims))
            if missing_claims:
                errors.append(
                    f"package {package_label} result references missing local claim: {missing_claims[0]}"
                )
            orphan_claims = sorted(set(local_claims).difference(result.material_claim_ids))
            if orphan_claims:
                errors.append(
                    f"package {package_label} contains claim not handed off by result: {orphan_claims[0]}"
                )
            package_results[result.package_id] = result

    _validate_dependencies(package_briefs, errors)
    missing_results = sorted(set(package_briefs).difference(package_results))
    if missing_results:
        errors.append(f"work package is missing a valid result: {missing_results[0]}")

    prepared_source_refs: dict[str, str] = {}
    sources_root = root / "sources"
    source_dirs = sorted(
        path for path in sources_root.iterdir() if path.is_dir()
    ) if sources_root.is_dir() else []
    for source_dir in source_dirs:
        try:
            source_manifest = verify_research_source_manifest(
                source_dir / "source_manifest.json", workspace_root=workspace
            )
            if source_manifest.source_id != source_dir.name:
                errors.append(f"source directory does not match source_id: {source_dir.name}")
            if source_manifest.prepared_artifact is not None:
                prepared_source_refs[
                    source_manifest.prepared_artifact.artifact_ref
                ] = source_manifest.source_id
        except ResearchSourceError as error:
            errors.append(f"invalid research source {source_dir.name}: {error}")

    models_root = root / "models"
    model_dirs = sorted(
        path for path in models_root.iterdir() if path.is_dir()
    ) if models_root.is_dir() else []
    for model_dir in model_dirs:
        try:
            verify_quantitative_model(model_dir, workspace_root=workspace)
        except QuantitativeModelError as error:
            errors.append(f"invalid quantitative model {model_dir.name}: {error}")
            continue
        model_inputs = _load_jsonl_models(
            model_dir / "model_inputs.jsonl",
            QuantitativeModelInput,
            f"quantitative model {model_dir.name} inputs",
            errors,
        )
        for model_input in model_inputs:
            for evidence in model_input.evidence:
                _validate_evidence(
                    evidence,
                    workspace,
                    hash_cache,
                    errors,
                    model_input.input_id,
                )
                consumed_evidence_refs.add(evidence.artifact_ref)

    for artifact_ref, source_id in sorted(prepared_source_refs.items()):
        if artifact_ref not in consumed_evidence_refs:
            warnings.append(f"evidence-ready source is not consumed by a claim or model: {source_id}")

    deliverables = root / "deliverables"
    report_text = _read_text(deliverables / "research_report.md", "research report", errors)
    if report_text is not None:
        if len(re.sub(r"\s+", "", report_text)) < 200:
            errors.append("research report is not substantive")
        if _PLACEHOLDER.search(report_text):
            errors.append("research report contains a placeholder")

    key_claims = _load_jsonl_models(
        deliverables / "key_claims.jsonl",
        ResearchClaim,
        "key claims",
        errors,
    )
    key_claim_by_id: dict[str, ResearchClaim] = {}
    for claim in key_claims:
        if claim.claim_id in key_claim_by_id:
            errors.append(f"key claims contain duplicate claim_id: {claim.claim_id}")
            continue
        key_claim_by_id[claim.claim_id] = claim
        source_claim = all_claims.get(claim.claim_id)
        if source_claim is None:
            errors.append(f"key claim is not present in a package: {claim.claim_id}")
        elif source_claim != claim:
            errors.append(f"key claim is not an exact package claim copy: {claim.claim_id}")
        if report_text is not None and f"[{claim.claim_id}]" not in report_text:
            errors.append(f"research report does not reference key claim: {claim.claim_id}")
    if not key_claims:
        errors.append("research release contains no key claims")

    quality = _load_model(
        deliverables / "quality_report.json",
        ResearchQualityReport,
        "quality report",
        errors,
    )
    quality_ready = False
    if quality is not None:
        if quality.research_id != brief.research_id:
            errors.append("quality report research_id does not match brief")
        quality_ready = quality.research_ready
        challenged = set(quality.independently_challenged_claim_ids)
        missing_challenged = sorted(challenged.difference(key_claim_by_id))
        if missing_challenged:
            errors.append(
                f"quality report challenges a non-key claim: {missing_challenged[0]}"
            )
        if challenged:
            challenge_text = _read_text(root / "reviews" / "challenge.md", "challenge review", errors)
            if challenge_text is not None:
                if len(re.sub(r"\s+", "", challenge_text)) < 100:
                    errors.append("challenge review is not substantive")
                for claim_id in sorted(challenged):
                    if claim_id not in challenge_text:
                        errors.append(f"challenge review does not name challenged claim: {claim_id}")
        if quality.research_ready:
            unfinished = sorted(
                package_id
                for package_id, result in package_results.items()
                if result.status != "completed"
            )
            if unfinished:
                errors.append(f"research_ready contains unfinished package: {unfinished[0]}")

    if (root / "release_manifest.json").exists():
        try:
            verify_published_research(root, workspace_root=workspace)
        except ResearchValidationError as error:
            errors.append(f"published release verification failed: {error}")

    return ResearchValidationReport(
        valid=not errors,
        publishable=not errors and quality_ready,
        research_id=brief.research_id,
        errors=tuple(errors),
        warnings=tuple(warnings),
        package_count=len(package_briefs),
        claim_count=len(all_claims),
        key_claim_count=len(key_claim_by_id),
    )


def publish_research(
    research_root: str | Path,
    *,
    workspace_root: str | Path,
) -> ResearchReleaseManifest:
    """Validate and freeze the complete research file inventory."""

    root = Path(research_root).expanduser().resolve()
    workspace = Path(workspace_root).expanduser().resolve()
    manifest_path = root / "release_manifest.json"
    if manifest_path.exists():
        return verify_published_research(root, workspace_root=workspace)

    validation = validate_research(root, workspace_root=workspace)
    if not validation.publishable:
        detail = validation.errors[0] if validation.errors else "quality report is not research_ready"
        raise ResearchValidationError(f"research is not publishable: {detail}")
    brief = _require_model(root / "research_brief.yaml", ResearchBrief, yaml_input=True)
    key_claims = _require_jsonl_models(
        root / "deliverables" / "key_claims.jsonl", ResearchClaim
    )
    package_ids = tuple(sorted(path.name for path in (root / "packages").iterdir() if path.is_dir()))
    artifacts: list[PublishedArtifact] = []
    for path in _release_files(root):
        identity = hash_file(path)
        artifacts.append(
            PublishedArtifact(
                artifact_ref=path.relative_to(root).as_posix(),
                sha256=identity.sha256,
                byte_size=identity.byte_size,
            )
        )
    manifest = ResearchReleaseManifest(
        research_id=brief.research_id,
        domain=brief.domain,
        as_of=brief.as_of,
        published_at=datetime.now(timezone.utc),
        package_ids=package_ids,
        key_claim_ids=tuple(claim.claim_id for claim in key_claims),
        artifacts=tuple(artifacts),
    )
    rendered = manifest.model_dump_json(indent=2) + "\n"
    publish_bytes(rendered.encode("utf-8"), manifest_path)
    return verify_published_research(root, workspace_root=workspace)


def verify_published_research(
    research_root: str | Path,
    *,
    workspace_root: str | Path,
) -> ResearchReleaseManifest:
    """Verify the manifest and every frozen file in one published release."""

    root = Path(research_root).expanduser().resolve()
    workspace = Path(workspace_root).expanduser().resolve()
    if not _is_below(root, workspace):
        raise ResearchValidationError("research root must stay below workspace root")
    try:
        manifest = ResearchReleaseManifest.model_validate_json(
            (root / "release_manifest.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError) as error:
        raise ResearchValidationError(f"invalid release manifest: {error}") from error
    brief = _require_model(root / "research_brief.yaml", ResearchBrief, yaml_input=True)
    if manifest.research_id != brief.research_id or manifest.domain != brief.domain:
        raise ResearchValidationError("release manifest identity does not match research brief")

    expected_refs = {path.relative_to(root).as_posix() for path in _release_files(root)}
    manifest_refs = {artifact.artifact_ref for artifact in manifest.artifacts}
    if manifest_refs != expected_refs:
        raise ResearchValidationError("release file inventory does not match manifest")
    for artifact in manifest.artifacts:
        path = (root / artifact.artifact_ref).resolve()
        if not _is_below(path, root) or not path.is_file() or path.is_symlink():
            raise ResearchValidationError(f"unsafe or missing release artifact: {artifact.artifact_ref}")
        identity = hash_file(path)
        if identity.sha256 != artifact.sha256 or identity.byte_size != artifact.byte_size:
            raise ResearchValidationError(f"release artifact identity mismatch: {artifact.artifact_ref}")
    return manifest


def _validate_evidence(
    evidence: EvidenceRef,
    workspace: Path,
    hash_cache: dict[Path, tuple[str, int]],
    errors: list[str],
    claim_id: str,
) -> None:
    path = (workspace / evidence.artifact_ref).resolve()
    if not _is_below(path, workspace) or not path.is_file() or path.is_symlink():
        errors.append(f"claim {claim_id} has unsafe or missing evidence: {evidence.artifact_ref}")
        return
    if path not in hash_cache:
        identity = hash_file(path)
        try:
            line_count = len(path.read_text(encoding="utf-8").splitlines())
        except UnicodeDecodeError:
            errors.append(f"claim {claim_id} evidence is not UTF-8 text: {evidence.artifact_ref}")
            return
        hash_cache[path] = (identity.sha256, line_count)
    actual_hash, line_count = hash_cache[path]
    if actual_hash != evidence.artifact_sha256:
        errors.append(f"claim {claim_id} evidence hash mismatch: {evidence.artifact_ref}")
    if evidence.end_line > line_count:
        errors.append(f"claim {claim_id} evidence line range exceeds file: {evidence.artifact_ref}")


def _validate_dependencies(
    briefs: dict[str, WorkPackageBrief],
    errors: list[str],
) -> None:
    for package_id, brief in briefs.items():
        missing = sorted(set(brief.dependencies).difference(briefs))
        if missing:
            errors.append(f"package {package_id} depends on missing package: {missing[0]}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(package_id: str) -> None:
        if package_id in visited or package_id not in briefs:
            return
        if package_id in visiting:
            errors.append(f"work package dependency cycle includes: {package_id}")
            return
        visiting.add(package_id)
        for dependency in briefs[package_id].dependencies:
            visit(dependency)
        visiting.remove(package_id)
        visited.add(package_id)

    for package_id in briefs:
        visit(package_id)


def _load_model(
    path: Path,
    model: type[Any],
    label: str,
    errors: list[str],
    *,
    yaml_input: bool = False,
) -> Any | None:
    try:
        if yaml_input:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
            return model.model_validate(payload)
        return model.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, yaml.YAMLError) as error:
        errors.append(f"invalid or missing {label}: {error}")
        return None


def _require_model(path: Path, model: type[Any], *, yaml_input: bool = False) -> Any:
    errors: list[str] = []
    value = _load_model(path, model, path.name, errors, yaml_input=yaml_input)
    if value is None:
        raise ResearchValidationError(errors[0])
    return value


def _load_jsonl_models(
    path: Path,
    model: type[Any],
    label: str,
    errors: list[str],
) -> list[Any]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        errors.append(f"invalid or missing {label}: {error}")
        return []
    values: list[Any] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            values.append(model.model_validate_json(line))
        except ValueError as error:
            errors.append(f"invalid {label} line {line_number}: {error}")
    return values


def _require_jsonl_models(path: Path, model: type[Any]) -> list[Any]:
    errors: list[str] = []
    values = _load_jsonl_models(path, model, path.name, errors)
    if errors:
        raise ResearchValidationError(errors[0])
    return values


def _read_text(path: Path, label: str, errors: list[str]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        errors.append(f"invalid or missing {label}: {error}")
        return None


def _release_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ResearchValidationError(f"release cannot contain symlink: {path.relative_to(root)}")
        if not path.is_file() or path.name == "release_manifest.json":
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def _is_below(path: Path, root: Path) -> bool:
    return path != root and root in path.parents


def _report(*, errors: tuple[str, ...]) -> ResearchValidationReport:
    return ResearchValidationReport(
        valid=False,
        publishable=False,
        research_id=None,
        errors=errors,
        warnings=(),
        package_count=0,
        claim_count=0,
        key_claim_count=0,
    )
