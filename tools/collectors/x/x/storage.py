from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def compact_utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path, fallback: Any = None) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(
                json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
            )
            count += 1
    return count


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSONL at {path}:{number}") from exc
    return rows


@dataclass(frozen=True)
class SourcePaths:
    root: Path
    raw_batches: Path
    normalized: Path
    images: Path
    state: Path
    manifest: Path
    posts_jsonl: Path
    media_jsonl: Path
    conversations_jsonl: Path

    @classmethod
    def from_root(cls, root: Path) -> "SourcePaths":
        return cls(
            root=root,
            raw_batches=root / "raw" / "batches",
            normalized=root / "normalized",
            images=root / "assets" / "images",
            state=root / "state",
            manifest=root / "state" / "manifest.json",
            posts_jsonl=root / "normalized" / "posts.jsonl",
            media_jsonl=root / "normalized" / "media.jsonl",
            conversations_jsonl=root / "normalized" / "conversations.jsonl",
        )

    def ensure(self) -> None:
        for path in (self.raw_batches, self.normalized, self.images, self.state):
            path.mkdir(parents=True, exist_ok=True)


class BatchArchive:
    def __init__(self, paths: SourcePaths, profile: str, command: str) -> None:
        paths.ensure()
        self.paths = paths
        self.batch_id = compact_utc_now()
        self.root = paths.raw_batches / self.batch_id
        self.responses = self.root / "responses"
        self.snapshots = self.root / "snapshots"
        self.responses.mkdir(parents=True)
        self.snapshots.mkdir(parents=True)
        self.manifest: dict[str, Any] = {
            "batch_id": self.batch_id,
            "profile": profile,
            "command": command,
            "started_at": utc_now(),
            "completed_at": None,
            "status": "running",
            "response_files": [],
            "snapshot_files": [],
            "observed_post_ids": [],
            "earliest_post_at": None,
            "latest_post_at": None,
            "stop_reason": None,
            "errors": [],
        }
        self._response_hashes: set[str] = set()
        self.save_manifest()

    def save_manifest(self) -> None:
        write_json(self.root / "manifest.json", self.manifest)

    def save_response(self, operation: str, url: str, payload: Any) -> Path | None:
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode(
            "utf-8"
        )
        digest = hashlib.sha256(encoded).hexdigest()
        if digest in self._response_hashes:
            return None
        self._response_hashes.add(digest)
        safe_operation = "".join(c if c.isalnum() else "-" for c in operation).strip(
            "-"
        )
        path = (
            self.responses
            / f"{len(self.manifest['response_files']) + 1:05d}-{safe_operation or 'graphql'}-{digest[:12]}.json"
        )
        write_json(
            path,
            {
                "captured_at": utc_now(),
                "operation": operation,
                "url": url,
                "data": payload,
            },
        )
        self.manifest["response_files"].append(str(path.relative_to(self.root)))
        return path

    def save_snapshot(
        self, route: str, iteration: int, posts: list[dict[str, Any]]
    ) -> Path:
        path = self.snapshots / f"{len(self.manifest['snapshot_files']) + 1:05d}.json"
        write_json(
            path,
            {
                "captured_at": utc_now(),
                "route": route,
                "iteration": iteration,
                "posts": posts,
            },
        )
        self.manifest["snapshot_files"].append(str(path.relative_to(self.root)))
        return path

    def finish(
        self, status: str, stop_reason: str, errors: list[str] | None = None
    ) -> None:
        self.manifest["completed_at"] = utc_now()
        self.manifest["status"] = status
        self.manifest["stop_reason"] = stop_reason
        self.manifest["errors"] = errors or []
        self.save_manifest()


def update_source_manifest(paths: SourcePaths, batch_manifest: dict[str, Any]) -> None:
    manifest = read_json(
        paths.manifest,
        {"schema_version": 1, "updated_at": None, "known_post_ids": [], "batches": []},
    )
    batches = manifest.setdefault("batches", [])
    batches.append(
        {
            key: batch_manifest.get(key)
            for key in (
                "batch_id",
                "started_at",
                "completed_at",
                "status",
                "stop_reason",
                "earliest_post_at",
                "latest_post_at",
                "requested_start_at",
                "earliest_target_post_at",
                "start_date_reached",
                "search_windows_processed",
            )
        }
    )
    manifest["batches"] = batches[-100:]
    known = set(manifest.get("known_post_ids", []))
    known.update(batch_manifest.get("observed_post_ids", []))
    manifest["known_post_ids"] = sorted(known)
    manifest["updated_at"] = utc_now()
    write_json(paths.manifest, manifest)
