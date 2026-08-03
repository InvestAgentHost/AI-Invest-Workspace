from __future__ import annotations

from datetime import timedelta

from main import parse_start_date


def test_parse_start_date_uses_hong_kong_midnight() -> None:
    value = parse_start_date("2024-01-01", "Asia/Hong_Kong")
    assert value is not None
    assert value.isoformat() == "2024-01-01T00:00:00+08:00"
    assert value.utcoffset() == timedelta(hours=8)


def test_parse_start_date_preserves_explicit_offset() -> None:
    value = parse_start_date("2024-01-01T00:00:00+00:00", "Asia/Hong_Kong")
    assert value is not None
    assert value.isoformat() == "2024-01-01T00:00:00+00:00"
