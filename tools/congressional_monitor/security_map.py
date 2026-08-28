"""Conservative ticker and statutory amount-range mappings for PTR OCR."""

from __future__ import annotations

import re
from typing import Any


AMOUNT_RANGE_BY_COLUMN = {
    "A": "$1,001 - $15,000",
    "B": "$15,001 - $50,000",
    "C": "$50,001 - $100,000",
    "D": "$100,001 - $250,000",
    "E": "$250,001 - $500,000",
    "F": "$500,001 - $1,000,000",
    "G": "$1,000,001 - $5,000,000",
    "H": "$5,000,001 - $25,000,000",
    "I": "$25,000,001 - $50,000,000",
    "J": "Over $50,000,000",
}

_ALIASES = {
    "KIMBERLY CLARK CORPORATION": ("KMB", "known_alias"),
    "BERKSHIRE HATHAWAY INC CLASS B": ("BRK.B", "known_alias"),
    "BERKSHIRE HATHAWAY INC CLASS A": ("BRK.A", "known_alias"),
    "CARRIER GLOBAL CORPORATION": ("CARR", "known_alias"),
    "STARBUCKS CORP": ("SBUX", "known_alias"),
    "ROCKWELL AUTOMATION INC": ("ROK", "known_alias"),
    "BANK OF AMERICA CORP": ("BAC", "known_alias"),
    "ZOETIS INC": ("ZTS", "known_alias"),
}


def _clean_name(value: str) -> str:
    text = value.upper().replace("&", " AND ")
    text = re.sub(r"\b(?:CMN|COMMON STOCK|ORDINARY SHARES?|CLASS\s+[ABC])\b", lambda match: " CLASS " + match.group(0)[-1] if match.group(0).startswith("CLASS") else " ", text)
    text = re.sub(r"[^A-Z0-9. ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def ticker_candidates(asset_name: str | None, overrides: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """Return only conservative exact/override candidates; never guess from words."""

    cleaned = _clean_name(str(asset_name or ""))
    override_map = { _clean_name(key): value.upper() for key, value in (overrides or {}).items() }
    if cleaned in override_map:
        return [{"ticker": override_map[cleaned], "confidence": "override", "normalized_name": cleaned}]
    for alias, (ticker, confidence) in _ALIASES.items():
        alias_clean = _clean_name(alias)
        if cleaned == alias_clean or cleaned.startswith(alias_clean + " "):
            return [{"ticker": ticker, "confidence": confidence, "normalized_name": cleaned}]
    return []


def amount_range_candidates(columns: list[str] | None) -> list[str]:
    return [AMOUNT_RANGE_BY_COLUMN[column] for column in (columns or []) if column in AMOUNT_RANGE_BY_COLUMN]
