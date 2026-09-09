#!/usr/bin/env python3
"""Produce review candidates for the documented 15-minute MA55 workflow.

This is a closed-bar research tool. It intentionally does not emit orders, prices,
position sizes, or claims that its manual trend gate is objective.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd


FIELD_ALIASES = {
    "security_code": ("security_code", "证券代码"),
    "timestamp": ("date", "日期", "tradeTime"),
    "open": ("open", "开盘价"),
    "high": ("high", "最高价"),
    "low": ("low", "最低价"),
    "close": ("close", "收盘价"),
    "volume": ("volume", "成交量"),
    "amount": ("amount", "成交额"),
}
TRUE_VALUES = {"1", "true", "yes", "y", "是"}
FALSE_VALUES = {"0", "false", "no", "n", "否", ""}
SESSIONS = (("09:30", "11:30"), ("13:00", "15:00"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--minute-csv", required=True, type=Path)
    parser.add_argument("--candidates-csv", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--touch-pct", type=float, default=0.003)
    parser.add_argument("--break-lookback-bars", type=int, default=8)
    parser.add_argument("--slope-bars", type=int, default=4)
    return parser.parse_args()


def choose_column(frame: pd.DataFrame, canonical: str, required: bool = True) -> str | None:
    for name in FIELD_ALIASES[canonical]:
        if name in frame.columns:
            return name
    if required:
        raise ValueError(f"missing {canonical}; accepted columns: {FIELD_ALIASES[canonical]}")
    return None


def normalize_minute_data(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    selected = {key: choose_column(raw, key, key not in {"volume", "amount"}) for key in FIELD_ALIASES}
    data = pd.DataFrame({key: raw[value] for key, value in selected.items() if value is not None})
    data["security_code"] = data["security_code"].astype(str).str.strip().str.upper()
    data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce")
    for name in ("open", "high", "low", "close", "volume", "amount"):
        if name in data:
            data[name] = pd.to_numeric(data[name], errors="coerce")
    required = ["security_code", "timestamp", "open", "high", "low", "close"]
    data = data.dropna(subset=required)
    data = data[data["security_code"].ne("")].sort_values(["security_code", "timestamp"])
    if data.empty:
        raise ValueError("no usable OHLC rows in minute CSV")
    if (data[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError("OHLC contains non-positive values; verify raw minute data")
    return data.reset_index(drop=True)


def normalize_candidates(path: Path) -> pd.DataFrame:
    candidates = pd.read_csv(path)
    required = {"security_code", "trend_eligible", "trend_note"}
    missing = sorted(required.difference(candidates.columns))
    if missing:
        raise ValueError(f"candidate CSV missing columns: {', '.join(missing)}")
    candidates = candidates[list(required)].copy()
    candidates["security_code"] = candidates["security_code"].astype(str).str.strip().str.upper()
    if candidates["security_code"].duplicated().any():
        dupes = candidates.loc[candidates["security_code"].duplicated(), "security_code"].tolist()
        raise ValueError(f"candidate CSV has duplicate security_code values: {', '.join(dupes[:10])}")

    def parse_flag(value: object) -> bool:
        token = str(value).strip().lower()
        if token in TRUE_VALUES:
            return True
        if token in FALSE_VALUES:
            return False
        raise ValueError(f"unsupported trend_eligible value: {value!r}")

    candidates["manual_trend_eligible"] = candidates["trend_eligible"].map(parse_flag)
    candidates["trend_note"] = candidates["trend_note"].fillna("").astype(str).str.strip()
    return candidates[["security_code", "manual_trend_eligible", "trend_note"]]


def session_bucket(timestamp: pd.Timestamp) -> pd.Timestamp | pd.NaT:
    day = timestamp.normalize()
    for start_text, end_text in SESSIONS:
        start = day + pd.Timedelta(start_text + ":00")
        end = day + pd.Timedelta(end_text + ":00")
        if start <= timestamp < end:
            return start + ((timestamp - start) // pd.Timedelta(minutes=15)) * pd.Timedelta(minutes=15)
    return pd.NaT


def build_15m_bars(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    data["bar_start"] = data["timestamp"].map(session_bucket)
    data = data.dropna(subset=["bar_start"])
    if data.empty:
        raise ValueError("no records fall in A-share continuous-auction sessions")
    aggregation: dict[str, str] = {"open": "first", "high": "max", "low": "min", "close": "last", "timestamp": "size"}
    if "volume" in data:
        aggregation["volume"] = "sum"
    if "amount" in data:
        aggregation["amount"] = "sum"
    bars = (
        data.sort_values(["security_code", "timestamp"])
        .groupby(["security_code", "bar_start"], as_index=False)
        .agg(aggregation)
        .rename(columns={"timestamp": "raw_rows"})
    )
    bars = bars.sort_values(["security_code", "bar_start"]).reset_index(drop=True)
    return bars


def sampling_audit(data: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for code, group in data.groupby("security_code", sort=True):
        diffs = group["timestamp"].sort_values().diff().dt.total_seconds().dropna()
        positive = diffs[diffs > 0]
        rows.append(
            {
                "security_code": code,
                "rows": len(group),
                "median_positive_gap_seconds": positive.median() if not positive.empty else None,
                "max_positive_gap_seconds": positive.max() if not positive.empty else None,
                "has_gap_over_15m": bool((positive > 15 * 60).any()),
            }
        )
    return pd.DataFrame(rows)


def mark_signals(bars: pd.DataFrame, touch_pct: float, break_lookback: int, slope_bars: int) -> pd.DataFrame:
    marked: list[pd.DataFrame] = []
    for _, group in bars.groupby("security_code", sort=False):
        group = group.copy().sort_values("bar_start").reset_index(drop=True)
        group["ma55"] = group["close"].rolling(55, min_periods=55).mean()
        group["ma233"] = group["close"].rolling(233, min_periods=233).mean()
        group["ma55_slope"] = group["ma55"] - group["ma55"].shift(slope_bars)
        group["bullish_red_k"] = group["close"] > group["open"]
        group["near_ma55"] = (
            group["ma55"].notna()
            & (group["low"] <= group["ma55"] * (1 + touch_pct))
            & (group["high"] >= group["ma55"] * (1 - touch_pct))
        )
        group["signal_type"] = ""
        last_breach: int | None = None
        prior_hold = False
        for position, row in group.iterrows():
            if pd.isna(row["ma55"]):
                continue
            if row["close"] < row["ma55"]:
                last_breach = position
                prior_hold = False
                continue
            is_reversal = bool(row["bullish_red_k"] and row["near_ma55"])
            if last_breach is not None and position - last_breach > break_lookback:
                last_breach = None
            if is_reversal and last_breach is not None:
                group.loc[position, "signal_type"] = "break_reclaim_ma55"
                last_breach = None
                prior_hold = True
            elif is_reversal and not prior_hold:
                group.loc[position, "signal_type"] = "hold_at_ma55"
                prior_hold = True
            elif not is_reversal:
                prior_hold = False
        marked.append(group)
    return pd.concat(marked, ignore_index=True)


def write_outputs(
    bars: pd.DataFrame,
    candidates: pd.DataFrame,
    audit: pd.DataFrame,
    output_dir: Path,
    args: argparse.Namespace,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    merged = bars.merge(candidates, how="left", on="security_code")
    merged["manual_trend_eligible"] = merged["manual_trend_eligible"].fillna(False).astype(bool)
    merged["trend_note"] = merged["trend_note"].fillna("")
    signals = merged[merged["signal_type"].ne("")].copy()
    signals["ma233_above_close"] = signals["ma233"].gt(signals["close"])
    signals["review_status"] = "REVIEW"
    signals.loc[signals["manual_trend_eligible"], "review_status"] = "QUALIFIED_FOR_REVIEW"
    signals["warning"] = ""
    signals.loc[signals["ma233"].isna(), "warning"] = "MA233 unavailable; no documented T reference"
    signals.loc[~signals["manual_trend_eligible"], "warning"] = signals.loc[
        ~signals["manual_trend_eligible"], "warning"
    ].map(lambda value: (value + "; " if value else "") + "manual trend gate is not confirmed")
    columns = [
        "security_code", "bar_start", "signal_type", "review_status", "manual_trend_eligible", "trend_note",
        "open", "high", "low", "close", "ma55", "ma55_slope", "ma233", "ma233_above_close", "raw_rows", "warning",
    ]
    signals[columns].to_csv(output_dir / "review_signals.csv", index=False)
    merged.to_csv(output_dir / "bars_15m_with_indicators.csv", index=False)
    audit.to_csv(output_dir / "raw_sampling_audit.csv", index=False)
    params = {
        "minute_csv": str(args.minute_csv),
        "candidates_csv": str(args.candidates_csv),
        "touch_pct": args.touch_pct,
        "break_lookback_bars": args.break_lookback_bars,
        "slope_bars": args.slope_bars,
        "implementation": "closed 15-minute bars only; no orders or position sizing",
    }
    (output_dir / "run_parameters.json").write_text(json.dumps(params, indent=2) + "\n", encoding="utf-8")
    print(f"15-minute bars: {output_dir / 'bars_15m_with_indicators.csv'}")
    print(f"review signals: {output_dir / 'review_signals.csv'}")
    print(f"raw sampling audit: {output_dir / 'raw_sampling_audit.csv'}")
    print(f"signals: {len(signals)}; qualified for review: {(signals['review_status'] == 'QUALIFIED_FOR_REVIEW').sum()}")


def main() -> None:
    args = parse_args()
    if not 0 <= args.touch_pct <= 0.05:
        raise ValueError("--touch-pct must be between 0 and 0.05")
    if args.break_lookback_bars < 1 or args.slope_bars < 1:
        raise ValueError("bar counts must be positive")
    minute = normalize_minute_data(args.minute_csv)
    candidates = normalize_candidates(args.candidates_csv)
    audit = sampling_audit(minute)
    bars = mark_signals(build_15m_bars(minute), args.touch_pct, args.break_lookback_bars, args.slope_bars)
    write_outputs(bars, candidates, audit, args.output_dir, args)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
