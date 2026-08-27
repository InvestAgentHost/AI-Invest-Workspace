"""Initialize one research workspace below a user-selected artifact root."""

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
import unicodedata

import yaml

from .contracts import ResearchBrief


_WINDOWS_RESERVED = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{number}" for number in range(1, 10)),
    *(f"lpt{number}" for number in range(1, 10)),
}


@dataclass(frozen=True, slots=True)
class ResearchWorkspace:
    """Paths owned by one research run."""

    workspace_root: Path
    research_root: Path
    brief: ResearchBrief

    @property
    def packages(self) -> Path:
        return self.research_root / "packages"

    @property
    def deliverables(self) -> Path:
        return self.research_root / "deliverables"

    @property
    def reviews(self) -> Path:
        return self.research_root / "reviews"

    @property
    def models(self) -> Path:
        return self.research_root / "models"


def initialize_research_workspace(
    workspace_root: str | Path,
    brief: ResearchBrief,
) -> ResearchWorkspace:
    """Create or idempotently reopen the deterministic research directory."""

    root = Path(workspace_root).expanduser().resolve()
    subject = _safe_segment(brief.scope.subjects[0], fallback_prefix="subject")
    domain = _safe_segment(brief.domain, fallback_prefix="domain")
    research_root = (
        root
        / "artifacts"
        / "research"
        / domain
        / subject
        / brief.as_of.isoformat()
        / brief.research_id
    )
    research_root.mkdir(parents=True, exist_ok=True)
    brief_path = research_root / "research_brief.yaml"
    canonical = yaml.safe_dump(
        brief.model_dump(mode="json"),
        allow_unicode=True,
        sort_keys=False,
    )
    if brief_path.exists():
        existing = ResearchBrief.model_validate(
            yaml.safe_load(brief_path.read_text(encoding="utf-8"))
        )
        if existing != brief:
            raise ValueError("research workspace already contains a different brief")
    else:
        brief_path.write_text(canonical, encoding="utf-8")
    (research_root / "packages").mkdir(exist_ok=True)
    (research_root / "deliverables").mkdir(exist_ok=True)
    return ResearchWorkspace(root, research_root, brief)


def load_research_brief(path: str | Path) -> ResearchBrief:
    """Load one human- and Agent-editable YAML research brief."""

    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("research brief must be a YAML object")
    return ResearchBrief.model_validate(payload)


def _safe_segment(value: str, *, fallback_prefix: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().lower()
    segment = re.sub(r"[^\w.-]+", "_", normalized, flags=re.UNICODE).strip("._-")
    segment = segment[:80].rstrip("._-")
    if not segment or segment in _WINDOWS_RESERVED:
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
        segment = f"{fallback_prefix}_{digest}"
    return segment
