#!/usr/bin/env python3
"""Generate an auditable proxy-based rotation/T plan from normalized daily CSVs."""
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd


def read_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"date", "close", "amount"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path}: missing columns {sorted(missing)}")
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    return df.sort_values("date")


def market_state(df: pd.DataFrame) -> tuple[str, dict]:
    x = df.copy()
    x["ma20"] = x.close.rolling(20).mean()
    x["ma60"] = x.close.rolling(60).mean()
    x["amount_ratio"] = x.amount / x.amount.rolling(20).mean()
    x["prior_high60"] = x.close.shift(1).rolling(60).max()
    r = x.iloc[-1]
    if pd.isna(r.ma60) or pd.isna(r.prior_high60):
        return "REVIEW", {"reason": "need at least 60 daily bars"}
    trend = bool(r.close > r.ma20 > r.ma60)
    risk_off = (not trend and r.amount_ratio < 0.8) or (r.close < r.ma60 and r.amount_ratio >= 1.2)
    breakout = bool(r.close > r.prior_high60 and r.amount_ratio >= 1.3)
    distribution = bool(r.close >= 0.97 * r.prior_high60 and r.amount_ratio < 0.8)
    if risk_off:
        state = "RISK_OFF"
    elif breakout:
        state = "BREAKOUT"
    elif distribution:
        state = "DISTRIBUTION"
    else:
        state = "REBOUND"
    return state, {"close": float(r.close), "ma20": float(r.ma20), "ma60": float(r.ma60),
                   "amount_ratio": float(r.amount_ratio)}


def sector_table(df: pd.DataFrame, benchmark: pd.DataFrame) -> pd.DataFrame:
    if "sector" not in df.columns:
        raise ValueError("sectors CSV needs sector column")
    bidx = benchmark.set_index("date")
    b = bidx.close.pct_change(5).rename("bench5")
    b20 = bidx.close.pct_change(20).rename("bench20")
    rows = []
    for sector, g in df.groupby("sector"):
        g = g.sort_values("date").copy()
        g["ret5"] = g.close.pct_change(5)
        g["ret20"] = g.close.pct_change(20)
        g["amount_ratio"] = g.amount / g.amount.rolling(20).mean()
        r = g.iloc[-1]
        bench5 = b.reindex([r.date]).iloc[0] if r.date in b.index else float("nan")
        bench20 = b20.reindex([r.date]).iloc[0] if r.date in b20.index else float("nan")
        rows.append({"sector": sector, "rs5": r.ret5 - bench5, "rs20": r.ret20 - bench20,
                     "breadth": r.get("breadth", float("nan")), "amount_ratio": r.amount_ratio})
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    for c in ["rs5", "rs20", "breadth", "amount_ratio"]:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out["score"] = out[["rs5", "rs20", "breadth", "amount_ratio"]].rank(pct=True).mean(axis=1)
    out["state"] = "WEAKENING"
    out.loc[(out.score >= 0.7) & (out.rs5 > 0) & (out.rs20 > 0) & (out.breadth >= 0.6), "state"] = "LEADER"
    out.loc[(out.score >= 0.7) & (out.rs5 > 0), "state"] = "REBOUND"
    return out.sort_values("score", ascending=False)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", required=True)
    ap.add_argument("--sectors", required=True)
    ap.add_argument("--stocks", required=True)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()
    bench, sectors, stocks = map(read_csv, [args.benchmark, args.sectors, args.stocks])
    state, meta = market_state(bench)
    ranked = sector_table(sectors, bench)
    top = set(ranked.query("state in ['LEADER','REBOUND']").head(4).sector) if not ranked.empty else set()
    if "sector" not in stocks.columns or "symbol" not in stocks.columns:
        raise ValueError("stocks CSV needs symbol and sector columns")
    latest = stocks.sort_values("date").groupby("symbol", as_index=False).tail(1).copy()
    latest["action"] = "HOLD"
    latest.loc[latest.sector.isin(top) & (state == "BREAKOUT"), "action"] = "BUY_BASE"
    latest.loc[latest.sector.isin(top) & (state == "REBOUND"), "action"] = "BUY_T"
    latest.loc[~latest.sector.isin(top), "action"] = "REDUCE_T"
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{"market_state": state, **meta}]).to_csv(outdir / "market_state.csv", index=False)
    ranked.to_csv(outdir / "sector_rank.csv", index=False)
    latest[["symbol", "sector", "action"]].to_csv(outdir / "action_plan.csv", index=False)


if __name__ == "__main__":
    main()
