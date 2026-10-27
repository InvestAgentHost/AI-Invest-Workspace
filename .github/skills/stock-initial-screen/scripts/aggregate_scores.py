#!/usr/bin/env python3
"""Aggregate evidence-reviewed scores. No retrieval or single-metric scoring."""

import argparse
from collections import Counter
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import sys


VERSION = "reverse-v1"
FACTOR_KEYS = {p: [f"{p}{n}" for n in range(1, 6)] for p in ("B", "M", "I")}
SCORE_KEYS = {key for keys in FACTOR_KEYS.values() for key in keys} | {"B3a"}
LABELS = {
    "removed": "本轮淘汰",
    "manual_review": "人工复核",
    "fails_stage_1": "未通过初筛",
    "research_now": "优先研究",
    "watch_closely": "密切跟踪",
    "watchlist": "观察名单",
    "quality_pass_valuation_unavailable": "质量通过，估值待评",
    "cheap_fails_quality": "便宜但质量不达标",
    "ignore": "暂不优先",
}
GROUPS = {
    "research_now": 0, "watch_closely": 0, "watchlist": 0,
    "fails_stage_1": 1, "cheap_fails_quality": 1, "ignore": 1,
    "manual_review": 2, "quality_pass_valuation_unavailable": 2,
    "removed": 3,
}


def number(value, field, low=None, high=None):
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f"{field}: expected finite JSON number")
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError(f"{field}: expected finite number")
    if (low is not None and result < low) or (high is not None and result > high):
        raise ValueError(f"{field}: outside allowed range")
    return result


def strings(value, field):
    if not isinstance(value, list) or any(
        not isinstance(v, str) or not v.strip() for v in value
    ):
        raise ValueError(f"{field}: expected list of nonempty strings")
    return list(value)


def require_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field}: expected nonempty string")
    return value


def rounded(value, places="0.1"):
    return value.quantize(Decimal(places), rounding=ROUND_HALF_UP)


def factor(scores, keys):
    missing = [k for k in keys if scores[k] is None]
    if len(missing) > 1:
        return None, {"score": None, "mean_unrounded": None, "missing": missing}
    values = [scores[k] for k in keys if scores[k] is not None]
    mean = sum(values) / Decimal(len(values))
    value = rounded(mean)
    return value, {
        "score": float(value), "mean_unrounded": str(mean), "missing": missing
    }


def evaluate(company):
    if not isinstance(company, dict):
        raise ValueError("company: expected object")
    identity = require_text(company.get("company_id"), "company_id")
    name = require_text(company.get("name"), f"{identity}.name")
    years = company.get("perimeter_years")
    if isinstance(years, bool) or not isinstance(years, int) or years < 0:
        raise ValueError(f"{identity}.perimeter_years: expected nonnegative integer")
    supplied = company.get("scores")
    if not isinstance(supplied, dict) or set(supplied) != SCORE_KEYS:
        raise ValueError(f"{identity}.scores: require exactly 15 measures plus B3a")
    missing_reasons = company.get("missing_reasons", {})
    if not isinstance(missing_reasons, dict):
        raise ValueError(f"{identity}.missing_reasons: expected object")
    scores = {}
    for key, value in supplied.items():
        if value is None:
            require_text(missing_reasons.get(key), f"{identity}.{key}.missing_reason")
            scores[key] = None
        else:
            score = number(value, f"{identity}.{key}", 1, 5)
            if not key.startswith("I") and score != score.to_integral_value():
                raise ValueError(f"{identity}.{key}: expected integer score")
            scores[key] = score
    if years < 3 and any(scores[k] is not None for k in ("B1", "B2", "M3")):
        raise ValueError(f"{identity}: B1/B2/M3 must be null for history below 3 years")
    blocks = strings(company.get("blocking_issues", []), "blocking_issues")
    flags = strings(company.get("review_flags", []), "review_flags")
    price = company.get("price")
    if not isinstance(price, dict):
        raise ValueError(f"{identity}.price: expected object")
    prices = {}
    for key in ("trailing_pe", "percentile", "history_years"):
        if key not in price:
            raise ValueError(f"{identity}.price: missing {key}")
        value = price[key]
        low = 0 if key in ("percentile", "history_years") else None
        high = 100 if key == "percentile" else None
        prices[key] = None if value is None else number(value, key, low, high)
    pe, pct, history = (prices[k] for k in ("trailing_pe", "percentile", "history_years"))
    if pct is not None and (pe is None or pe <= 0 or history is None or history <= 0):
        raise ValueError(f"{identity}: percentile requires positive P/E and history")
    band = None
    if pct is not None:
        band = "bottom" if pct * 3 <= 100 else "middle" if pct * 3 <= 200 else "top"
    if history is not None and 0 < history < 5:
        flags.append("P/E history below five years; add two comparable forward P/Es")

    factor_values, factors = {}, {}
    for prefix, keys in FACTOR_KEYS.items():
        factor_values[prefix], factors[prefix] = factor(scores, keys)
    average = None
    if all(v is not None for v in factor_values.values()):
        average = sum(factor_values.values()) / Decimal(3)
    quality = None if average is None else (
        factor_values["B"] >= Decimal("3.5")
        and factor_values["M"] >= 3
        and factor_values["I"] >= 3
    )
    stage, stage_mean = None, None
    if all(scores[k] is not None for k in ("B1", "B2", "B3a")):
        stage_mean = sum(scores[k] for k in ("B1", "B2", "B3a")) / Decimal(3)
        stage = scores["B1"] >= 3 and stage_mean >= 3
    elif scores["B1"] is not None and scores["B1"] < 3:
        stage = False
    removals = [f"{k} = 1" for k in ("B1", "M5") if scores[k] == 1]
    required_missing = [k for k in ("B1", "M5") if scores[k] is None]
    if removals:
        status, reasons = "removed", removals
    elif blocks or years < 3 or required_missing:
        status, reasons = "manual_review", list(blocks)
        if years < 3:
            reasons.append("Fewer than three complete fiscal years in current perimeter")
        if required_missing:
            reasons.append("Missing hard-gate scores: " + ", ".join(required_missing))
    elif stage is False:
        status, reasons = "fails_stage_1", ["B1 < 3 or Stage 1 mean < 3"]
    elif stage is None or quality is None:
        status, reasons = "manual_review", []
        if stage is None:
            reasons.append("Stage 1 requires B1, B2 and B3a")
        if quality is None:
            reasons.append("At least one factor has more than one missing measure")
    elif quality:
        status = {
            "bottom": "research_now", "middle": "watch_closely", "top": "watchlist",
            None: "quality_pass_valuation_unavailable",
        }[band]
        reasons = ["Stage 1 and all quality thresholds pass"]
        reasons.append("Valuation unavailable" if band is None else f"P/E band: {band}")
    else:
        status = "cheap_fails_quality" if band == "bottom" else "ignore"
        reasons = ["One or more quality thresholds fail"]
    return {
        "company_id": identity, "name": name, "factors": factors,
        "average": None if average is None else float(rounded(average, "0.01")),
        "average_unrounded": None if average is None else str(average),
        "stage_1": stage,
        "stage_1_mean": None if stage_mean is None else str(stage_mean),
        "quality_pass": quality, "price_band": band,
        "status": status, "label": LABELS[status], "reasons": reasons,
        "missing_reasons": missing_reasons, "review_flags": flags,
        "blocking_issues": blocks,
    }


def aggregate(payload):
    if not isinstance(payload, dict) or payload.get("rule_version") != VERSION:
        raise ValueError(f"rule_version must be {VERSION}; changed rules need a new engine")
    dates = {}
    for key in ("as_of", "price_date"):
        value = require_text(payload.get(key), key)
        parsed = date.fromisoformat(value)
        if value != parsed.isoformat():
            raise ValueError(f"{key}: use YYYY-MM-DD")
        dates[key] = parsed
    if dates["price_date"] > dates["as_of"]:
        raise ValueError("price_date cannot be later than as_of")
    companies = payload.get("companies")
    if not isinstance(companies, list) or not companies:
        raise ValueError("companies: expected nonempty list")
    results = [evaluate(c) for c in companies]
    identities = [c["company_id"] for c in results]
    if len(set(identities)) != len(identities):
        raise ValueError("Duplicate company_id")
    results.sort(key=lambda c: (
        GROUPS[c["status"]],
        c["average_unrounded"] is None,
        -Decimal(c["average_unrounded"]) if c["average_unrounded"] is not None else 0,
        c["company_id"],
    ))
    for rank, result in enumerate(results, 1):
        result["rank"] = rank
    return {
        "rule_version": VERSION, "as_of": payload["as_of"],
        "price_date": payload["price_date"], "count": len(results),
        "counts_by_status": dict(sorted(Counter(c["status"] for c in results).items())),
        "companies": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, help="New JSON path; never overwrites")
    args = parser.parse_args()
    try:
        with args.input.open(encoding="utf-8") as stream:
            payload = json.load(stream, parse_float=Decimal)
        output = json.dumps(aggregate(payload), ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(output)
            print(f"Wrote {args.output}")
        else:
            sys.stdout.write(output)
    except (ValueError, OSError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()
