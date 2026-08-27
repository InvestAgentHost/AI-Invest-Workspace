"""Build a stable Agent-reviewed official-site plan."""

import hashlib
import json
from pathlib import Path

from .models import OfficialSitePlan, OfficialSiteRequest


def build_official_site_plan(request: OfficialSiteRequest | dict) -> OfficialSitePlan:
    parsed = request if isinstance(request, OfficialSiteRequest) else OfficialSiteRequest.model_validate(request)
    payload = parsed.model_dump(mode="json")
    identity_payload = {key: value for key, value in payload.items() if key != "schema_version"}
    digest = hashlib.sha256(
        json.dumps(identity_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:20]
    payload["schema_version"] = "research_foundry_official_site_plan.v1"
    return OfficialSitePlan(plan_id=f"osp_{digest}", status="ready", **payload)


def load_official_site_plan(path: str | Path) -> OfficialSitePlan:
    return OfficialSitePlan.model_validate_json(Path(path).read_text(encoding="utf-8"))
