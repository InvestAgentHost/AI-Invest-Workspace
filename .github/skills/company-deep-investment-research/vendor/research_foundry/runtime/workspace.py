"""User-selected workspace layout for inputs, state, logs, cache, and artifacts."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Workspace:
    root: Path

    @classmethod
    def from_path(cls, root: str | Path) -> "Workspace":
        path = Path(root).expanduser().resolve()
        return cls(path)

    @property
    def targets(self) -> Path:
        return self.root / "targets"

    @property
    def runs(self) -> Path:
        return self.root / "runs"

    @property
    def artifacts(self) -> Path:
        return self.root / "artifacts"

    @property
    def state(self) -> Path:
        return self.root / "state"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def cache(self) -> Path:
        return self.root / "cache"

    def ensure_layout(self) -> None:
        for path in (self.targets, self.runs, self.artifacts, self.state, self.logs, self.cache):
            path.mkdir(parents=True, exist_ok=True)
