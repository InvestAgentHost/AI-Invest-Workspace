"""Faithful citation wrapping for provider-prepared meeting minutes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from .planning import TranscriptPlan


NUMBERED_HEADING = re.compile(r"^\s*\d{1,3}[.、]\s+\S")
SPEAKER_LABEL = re.compile(
    r"^\s*(?:operator|executive|management|analyst|ceo|cfo|ir|speaker|主持人|管理层|分析师|发言人|公司代表)"
    r"(?:\s+\d+)?[：:]\s*\S",
    re.IGNORECASE,
)


def is_provider_prepared_minutes(plan: TranscriptPlan, source: Path) -> bool:
    """Recognize structured provider minutes without inferring content semantics."""

    if plan.source_representation == "provider_prepared_minutes":
        return True
    return False


def prepare_provider_minutes(plan: TranscriptPlan, source: Path, output: Path) -> int | None:
    """Write a faithful, marker-addressable wrapper when the provider already prepared the minutes."""

    if not is_provider_prepared_minutes(plan, source):
        return None
    units = [line.strip() for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not units:
        return None
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    title = plan.source_title or f"{plan.target_name} {plan.event_date.isoformat()} {plan.event_type}"
    lines = [
        f"# {title}",
        "",
        f"- Source SHA-256: `{source_hash}`",
        "- Source coverage: unknown",
        "- Source representation: provider_prepared_minutes",
        "- Limitations: The supplied source is provider-prepared. Speaker attribution and completeness relative to the original event cannot be independently verified.",
        "",
    ]
    markers: list[dict[str, str]] = []
    for index, unit in enumerate(units, start=1):
        marker = f"T{index:04d}"
        lines.extend((f"### {marker} | provider-prepared minutes | unknown | unknown", "", unit, ""))
        markers.append({"id": marker, "source_kind": "provider_prepared_minutes"})
    (output / "cleaned_transcript.md").write_text("\n".join(lines), encoding="utf-8")
    (output / "transcript_metadata.json").write_text(
        json.dumps(
            {
                "schema_version": "analysis_ready_transcript.v2",
                "source_sha256": source_hash,
                "source_representation": "provider_prepared_minutes",
                "markers": markers,
                "issues": [
                    {
                        "code": "provider_prepared_minutes",
                        "severity": "warning",
                        "description": "Provider-prepared translated minutes; speaker-level attribution is unavailable.",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return len(markers)
