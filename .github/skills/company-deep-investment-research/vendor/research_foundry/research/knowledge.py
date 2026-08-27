"""Company workspaces and conservative knowledge-base discovery."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Iterable

import yaml

from research_foundry.runtime.artifacts import hash_file

from .project import ProjectConfig
from .workspace import _safe_segment


class KnowledgeBaseError(ValueError):
    """Raised when a company identity or knowledge snapshot is invalid."""


@dataclass(frozen=True, slots=True)
class CompanyIdentity:
    company_id: str
    legal_name: str
    ticker: str | None
    domain: str
    aliases: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class KnowledgeEntry:
    path: str
    artifact_kind: str
    company_id: str
    research_id: str | None
    source_type: str
    as_of: str | None
    published: bool
    sha256: str
    byte_size: int
    can_inherit_conclusion: bool
    can_use_as_evidence: bool


@dataclass(frozen=True, slots=True)
class KnowledgeSnapshot:
    company: CompanyIdentity
    policy: str
    generated_at: str
    entries: tuple[KnowledgeEntry, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "research_knowledge_snapshot.v1",
            "company": asdict(self.company),
            "policy": self.policy,
            "generated_at": self.generated_at,
            "entries": [asdict(entry) for entry in self.entries],
        }


def initialize_company_workspace(
    config: ProjectConfig,
    *,
    company_id: str,
    legal_name: str,
    ticker: str | None = None,
    domain: str | None = None,
    aliases: Iterable[str] = (),
) -> tuple[Path, CompanyIdentity]:
    """Create one durable company directory and its typed subdirectories."""

    company_id = _identity_segment(company_id)
    legal_name = legal_name.strip()
    if not legal_name:
        raise KnowledgeBaseError("legal_name must be non-empty")
    normalized_aliases = tuple(
        dict.fromkeys(
            item.strip()
            for item in (company_id, legal_name, ticker or "", *(aliases or ()))
            if item and item.strip()
        )
    )
    identity = CompanyIdentity(
        company_id=company_id,
        legal_name=legal_name,
        ticker=ticker.strip() if ticker else None,
        domain=(domain or config.default_domain).strip(),
        aliases=normalized_aliases,
    )
    root = (config.company_root / _safe_segment(company_id, fallback_prefix="company")).resolve()
    if root.exists() and (root / "company.yaml").exists():
        existing = _load_company_identity(root / "company.yaml")
        if existing != identity:
            raise KnowledgeBaseError("company directory already contains a different identity")
    elif root.exists() and any(root.iterdir()):
        raise KnowledgeBaseError("company directory exists without company.yaml")
    root.mkdir(parents=True, exist_ok=True)
    for name in (
        "raw",
        "prepared",
        "research",
        "interactions/notes",
        "interactions/questions",
        "knowledge",
        "releases",
        "models",
    ):
        (root / name).mkdir(parents=True, exist_ok=True)
    (root / "company.yaml").write_text(
        yaml.safe_dump(
            {"schema_version": "research_company.v1", **asdict(identity)},
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return root, identity


def load_company_identity(company_root: str | Path) -> CompanyIdentity:
    return _load_company_identity(Path(company_root).expanduser().resolve() / "company.yaml")


def ingest_company_artifact(
    config: ProjectConfig,
    *,
    company_id: str,
    source: str | Path,
    kind: str,
    name: str | None = None,
) -> Path:
    """Copy one verified input into a company's raw or prepared archive."""

    if kind not in {"raw", "prepared"}:
        raise KnowledgeBaseError("company artifact kind must be raw or prepared")
    company_path = (
        config.company_root / _safe_segment(company_id, fallback_prefix="company")
    ).resolve()
    load_company_identity(company_path)
    source_path = Path(source).expanduser().resolve()
    if source_path.is_symlink() or not source_path.is_file():
        raise KnowledgeBaseError("company artifact source must be a regular file")
    destination = company_path / kind / (name.strip() if name else source_path.name)
    if destination.name in {"", ".", ".."} or "/" in destination.name or "\\" in destination.name:
        raise KnowledgeBaseError("company artifact name must be one filename")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.is_symlink() or not destination.is_file():
            raise KnowledgeBaseError("company artifact destination is unsafe")
        if hash_file(destination) != hash_file(source_path):
            raise KnowledgeBaseError("company artifact destination already contains different content")
        return destination
    temporary = destination.with_name(f".{destination.name}.tmp")
    shutil.copyfile(source_path, temporary)
    temporary.replace(destination)
    return destination


def discover_company_knowledge(
    config: ProjectConfig,
    *,
    company_id: str,
    policy: str | None = None,
    write_snapshot: bool = True,
) -> KnowledgeSnapshot:
    """Build a compact provenance-aware index without loading old prose into context."""

    company_path = (config.company_root / _safe_segment(company_id, fallback_prefix="company")).resolve()
    identity = load_company_identity(company_path)
    selected_policy = policy or config.knowledge_policy
    if selected_policy not in {"reuse", "raw_only", "isolated"}:
        raise KnowledgeBaseError("policy must be reuse, raw_only, or isolated")
    selected: list[KnowledgeEntry] = []
    if selected_policy != "isolated":
        candidates = list(_iter_files(company_path))
        candidates.extend(_iter_external_company_files(config, identity))
        for path in candidates:
            entry = _entry_for(path, identity, config, selected_policy)
            if entry is not None:
                selected.append(entry)
    entries = tuple(
        sorted({entry.path: entry for entry in selected}.values(), key=lambda item: item.path)
    )
    snapshot = KnowledgeSnapshot(
        identity, selected_policy, datetime.now(timezone.utc).isoformat(), entries
    )
    if write_snapshot:
        knowledge = company_path / "knowledge"
        knowledge.mkdir(parents=True, exist_ok=True)
        _atomic_write(
            knowledge / "index.json",
            json.dumps(snapshot.as_dict(), ensure_ascii=False, indent=2) + "\n",
        )
        with (knowledge / "catalog.jsonl").open("w", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(asdict(entry), ensure_ascii=False, sort_keys=True) + "\n")
        _atomic_write(knowledge / "knowledge_context.md", _render_context(snapshot))
    return snapshot


def write_run_knowledge_snapshot(
    snapshot: KnowledgeSnapshot, destination: str | Path
) -> Path:
    path = Path(destination).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(path, json.dumps(snapshot.as_dict(), ensure_ascii=False, indent=2) + "\n")
    return path


def _iter_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return ()
    return (
        path
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink() and ".git" not in path.parts
    )


def _iter_external_company_files(
    config: ProjectConfig, identity: CompanyIdentity
) -> Iterable[Path]:
    artifacts = config.workspace_root / "artifacts"
    if not artifacts.exists():
        return ()
    tokens = tuple(_normalize(item) for item in identity.aliases if item)
    paths: list[Path] = []
    for path in artifacts.rglob("*"):
        if not path.is_file() or path.is_symlink() or ".git" in path.parts:
            continue
        haystack = _normalize(str(path))
        if any(token and token in haystack for token in tokens):
            paths.append(path)
    return paths


def _entry_for(
    path: Path, identity: CompanyIdentity, config: ProjectConfig, policy: str
) -> KnowledgeEntry | None:
    text = _normalize(str(path))
    name = path.name.casefold()
    parts = {part.casefold() for part in path.parts}
    if name == "release_manifest.json" or name.endswith("_manifest.json"):
        kind, source_type, inherit, evidence = "manifest", "release", False, False
    elif "review" in name or "challenge" in name:
        kind, source_type, inherit, evidence = "review", "research", False, False
    elif "report" in name or "research_map" in name or "research_coverage" in name:
        kind, source_type, inherit, evidence = "report", "research", False, False
    elif "notes" in parts or "/notes/" in text or "interactions" in parts:
        kind, source_type, inherit, evidence = "note", "research", False, False
    elif "prepared" in parts or (
        name.endswith(".md") and any(token in text for token in ("prepared", "/source.md"))
    ):
        kind, source_type, inherit, evidence = "prepared", "prepared", False, True
    elif "raw" in parts or name.endswith((".html", ".pdf", ".json", ".txt")):
        kind, source_type, inherit, evidence = "raw", "raw", False, True
    else:
        return None
    if policy == "raw_only" and kind not in {"raw", "prepared"}:
        return None
    if not config.include_raw_sources and kind == "raw":
        return None
    if not config.include_prepared_sources and kind == "prepared":
        return None
    if not config.include_research_notes and kind == "note":
        return None
    if not config.include_reports and kind in {"report", "review"}:
        return None
    research_id, as_of = _research_identity(path)
    digest = hash_file(path)
    published = "release_manifest_json" in text
    if published and not config.include_published_runs:
        return None
    return KnowledgeEntry(
        path=str(path),
        artifact_kind=kind,
        company_id=identity.company_id,
        research_id=research_id,
        source_type=source_type,
        as_of=as_of,
        published=published,
        sha256=digest.sha256,
        byte_size=digest.byte_size,
        can_inherit_conclusion=inherit,
        can_use_as_evidence=evidence,
    )


def _research_identity(path: Path) -> tuple[str | None, str | None]:
    research_id = None
    as_of = None
    for parent in (path, *path.parents):
        if parent.name and re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{2,95}", parent.name):
            if parent.name not in {"artifacts", "research", "notes", "sources", "prepared", "raw"}:
                research_id = parent.name
        if re.fullmatch(r"20\d{2}-\d{2}-\d{2}", parent.name):
            as_of = parent.name
    return research_id, as_of


def _load_company_identity(path: Path) -> CompanyIdentity:
    if path.is_symlink() or not path.is_file():
        raise KnowledgeBaseError("company.yaml is missing")
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        raise KnowledgeBaseError(f"invalid company.yaml: {error}") from error
    if not isinstance(payload, dict) or payload.get("schema_version") != "research_company.v1":
        raise KnowledgeBaseError("unsupported company identity schema")
    try:
        return CompanyIdentity(
            company_id=_identity_segment(str(payload["company_id"])),
            legal_name=str(payload["legal_name"]).strip(),
            ticker=str(payload["ticker"]).strip() if payload.get("ticker") else None,
            domain=str(payload["domain"]).strip(),
            aliases=tuple(
                str(value).strip()
                for value in payload.get("aliases", ())
                if str(value).strip()
            ),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise KnowledgeBaseError(f"invalid company identity: {error}") from error


def _identity_segment(value: str) -> str:
    value = value.strip()
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{2,95}", value):
        raise KnowledgeBaseError("company_id must be a stable ASCII identifier")
    return value


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")


def _render_context(snapshot: KnowledgeSnapshot) -> str:
    lines = [
        "# Company Knowledge Context",
        "",
        f"- company_id: {snapshot.company.company_id}",
        f"- legal_name: {snapshot.company.legal_name}",
        f"- policy: {snapshot.policy}",
        "",
        "## Provenance rules",
        "",
        "- raw and prepared entries may be selected as evidence after the Agent reads them.",
        "- Prior note, report, and review entries are historical context or hypotheses, never inherited conclusions.",
        "- Strict blind runs should use isolated and create a new run.",
        "",
        "## Available artifacts",
        "",
    ]
    for entry in snapshot.entries:
        flags = []
        if entry.can_use_as_evidence:
            flags.append("evidence")
        if entry.can_inherit_conclusion:
            flags.append("conclusion")
        lines.append(f"- {entry.artifact_kind} [{', '.join(flags) or 'context'}] {entry.path}")
    return "\n".join(lines) + "\n"


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with open(fd, "w", encoding="utf-8", closefd=True) as handle:
            handle.write(text)
            handle.flush()
        Path(temporary).replace(path)
    except OSError:
        Path(temporary).unlink(missing_ok=True)
        raise
