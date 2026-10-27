"""Deterministic screen-v2 calculations. Inputs are separately reviewed evidence."""
from decimal import Decimal, ROUND_HALF_UP
import math
import statistics

VERSION = "screen-v2"
FACTOR_KEYS = {p: [f"{p}{i}" for i in range(1, 6)] for p in "BMI"}
SCORE_KEYS = {k for keys in FACTOR_KEYS.values() for k in keys} | {"B3a"}
LABELS = {"removed": "本轮淘汰", "provisional_review": "暂定评分／重组观察",
          "pending_work": "评分工作未完成", "complete_unscorable": "核验完成／不可比较",
          "fails_stage_1": "未通过初筛", "research_now": "优先研究",
          "watch_closely": "密切跟踪", "watchlist": "观察名单",
          "quality_pass_valuation_unavailable": "质量通过／估值待评",
          "cheap_fails_quality": "便宜但质量未达标", "ignore": "质量未达标／暂不优先",
          "quality_sensitive": "质量待确认／缺项敏感"}


def band(value, thresholds):
    if value is None or not math.isfinite(value):
        return None
    value = Decimal(str(value))
    for threshold, score in thresholds:
        if value >= Decimal(str(threshold)):
            return score
    return 1


def gross_score(delta):
    return band(delta, [(2, 5), (.5, 4), (-.5, 3), (-2, 2)])


def share_score(change):
    if change is None:
        return None
    change = Decimal(str(change))
    return 5 if change <= Decimal('-.15') else 4 if change <= Decimal('-.05') else 3 if change <= Decimal('.05') else 2 if change <= Decimal('.20') else 1


def tax_rate(rows):
    if any(r.get("tax") is None or r.get("pretax") is None for r in rows):
        return .25, "statutory_fallback_missing_tax_bridge"
    pretax = sum(r["pretax"] for r in rows)
    rate = sum(r["tax"] for r in rows) / pretax if pretax > 0 else None
    if rate is None or not 0 <= rate <= .5:
        return .25, "25% fallback for nonpositive pretax or tax outside 0–50%"
    return rate, "aggregate reported income tax / aggregate pretax"


def capital_return(rows, rate):
    required = ("equity", "debt_leases", "liquid_assets", "goodwill", "intangibles", "ebit")
    usable = [r for r in rows if all(r.get(k) is not None for k in required)]
    missing = [r["year"] for r in rows if r not in usable]
    calculations = []
    for r in usable:
        invested = Decimal(str(r["equity"])) + Decimal(str(r["debt_leases"])) - Decimal(str(r["liquid_assets"]))
        operating = invested - Decimal(str(r["goodwill"])) - Decimal(str(r["intangibles"]))
        calculations.append({"year": r["year"], "nopat": Decimal(str(r["ebit"])) * (1 - Decimal(str(rate))),
                             "capital_including_goodwill": invested, "operating_capital": operating})
    # Entire series switches definition, never just an anomalous year.
    fallback = any(r["operating_capital"] <= 0 for r in calculations)
    denominator = "capital_including_goodwill" if fallback else "operating_capital"
    invalid_capital = any(r[denominator] <= 0 for r in calculations)
    if invalid_capital or not calculations:
        return numeric_tree({"score": None, "median": None, "including_goodwill_median": None,
                "lowest_three_year_mean": None,
                "annual": calculations, "missing_years": missing, "invalid_capital": True})
    for r in calculations:
        r["scoring_roic"] = r["nopat"] / r[denominator]
        r["including_goodwill_roic"] = r["nopat"] / r["capital_including_goodwill"] if r["capital_including_goodwill"] > 0 else None
    med = statistics.median(r["scoring_roic"] for r in calculations)
    consecutive = [statistics.mean(r["scoring_roic"] for r in calculations[i:i+3])
                   for i in range(len(calculations)-2)
                   if calculations[i+2]["year"] - calculations[i]["year"] == 2]
    low = min(consecutive) if consecutive else None
    score = band(med, [(.25, 5), (.15, 4), (.10, 3), (.06, 2)])
    if low is not None:
        score = min(score, band(low, [(.15, 5), (.10, 4), (.06, 3), (-math.inf, 2)]))
    else:
        score = min(score, 3)
    if fallback:
        score = min(score, 4)
    incl = [r["including_goodwill_roic"] for r in calculations if r["including_goodwill_roic"] is not None]
    result = {"score": score, "median": med, "lowest_three_year_mean": low,
            "including_goodwill_median": statistics.median(incl) if incl else None,
            "denominator": denominator, "whole_window_fallback": fallback,
            "annual": calculations, "missing_years": missing, "invalid_capital": False}
    return numeric_tree(result)


def numeric_tree(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list):
        return [numeric_tree(v) for v in value]
    if isinstance(value, dict):
        return {k: numeric_tree(v) for k,v in value.items()}
    return value


def cash_conversion(rows):
    required = ("cfo", "capex", "net_income")
    if any(any(r.get(k) is None for k in required) for r in rows):
        return {"score": None, "reason": "missing reconciled CFO/capex/continuing profit"}
    dec = lambda value: Decimal(str(value))
    before_sbc = sum(dec(r["cfo"]) - dec(r["capex"]) - dec(r.get("financing_interest_paid", 0))
                     + dec(r.get("investing_interest_received", 0)) for r in rows)
    profit = sum(dec(r["net_income"]) for r in rows)
    totals={'cfo_sum':sum(dec(r['cfo'])for r in rows),'capex_sum':sum(dec(r['capex'])for r in rows),
            'financing_interest_paid':sum(dec(r.get('financing_interest_paid',0))for r in rows),
            'investing_interest_received':sum(dec(r.get('investing_interest_received',0))for r in rows)}
    if profit == 0:
        return numeric_tree({'score':None,'reason':'zero cumulative continuing profit; ratio undefined',
                             'profit':profit,'before_sbc_fcf':before_sbc,**totals})
    missing_sbc = [r["year"] for r in rows if r.get("sbc") is None]
    if missing_sbc:
        upper = before_sbc / profit if profit > 0 else None
        definite_low = before_sbc < 0 or profit < 0 or (upper is not None and upper < .5)
        return numeric_tree({"score": 1 if definite_low else None, "before_sbc_fcf": before_sbc,
                "profit": profit, "ratio_upper_bound": upper, "missing_sbc_years": missing_sbc,
                "reason": "pre-SBC upper bound already implies score1" if definite_low else "SBC amount not disclosed; upper bound cannot determine score",**totals})
    # Only positive noncash addbacks are deducted. An accounting reversal is
    # retained in raw_sbc but cannot raise the conservative owner-cash measure.
    sbc_deduction = sum(max(Decimal(0),dec(r['sbc'])) for r in rows)
    fcf = before_sbc - sbc_deduction
    ratio = fcf / profit if profit > 0 else None
    score = 1 if fcf < 0 or profit < 0 else band(ratio, [(1, 5), (.9, 4), (.75, 3), (.5, 2)])
    return numeric_tree({"score": score, "fcf_after_sbc": fcf, "before_sbc_fcf": before_sbc,
            "sbc": sbc_deduction, "raw_sbc": sum(dec(r['sbc'])for r in rows), "profit": profit, "ratio": ratio,
            **totals})


def allocation(returns, rows, impairment=None):
    roic = returns.get("including_goodwill_median")
    rs = band(roic, [(.15, 5), (.12, 4), (.09, 3), (.06, 2)])
    shares = [r for r in rows if r.get("filing_shares") is not None]
    change = Decimal(str(shares[-1]["filing_shares"])) / Decimal(str(shares[0]["filing_shares"])) - 1 if len(shares) >= 2 and shares[0]["filing_shares"] > 0 else None
    ss = share_score(change)
    imp_score = None
    if impairment is not None:
        imp_score = 5 if impairment == 0 else 4 if impairment < .05 else 3 if impairment < .15 else 2 if impairment <= .30 else 1
    subs = [x for x in (rs, ss, imp_score) if x is not None]
    score = math.floor(statistics.mean(subs)) if len(subs) >= 2 else None
    return {"score": score, "roic_including_goodwill": roic, "roic_subscore": rs,
            "share_change": float(change) if change is not None else None, "share_subscore": ss,
            "share_basis": "source standardized filing-date shares, split adjusted; timing differs from weighted-average diluted shares",
            "impairment_ratio": impairment, "impairment_subscore": imp_score}


def factor(scores, keys):
    values = [Decimal(str(scores[k])) for k in keys if scores[k] is not None]
    if len(values) < 4:
        return {"score": None, "mean_unrounded": None, "missing": [k for k in keys if scores[k] is None]}
    mean = sum(values) / len(values)
    return {"score": float(mean.quantize(Decimal('.1'), rounding=ROUND_HALF_UP)),
            "mean_unrounded": str(mean), "missing": [k for k in keys if scores[k] is None]}


def evaluate(c):
    scores = c["scores"]
    if set(scores) != SCORE_KEYS:
        raise ValueError(f"{c['company_id']}: expected 16 score keys")
    for k, value in scores.items():
        if value is None:
            if not c.get("missing_reasons", {}).get(k):
                raise ValueError(f"{c['company_id']}/{k}: missing reason required")
        elif isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 1 <= value <= 5:
            raise ValueError(f"{c['company_id']}/{k}: invalid score")
        elif not k.startswith('I') and Decimal(str(value)) != Decimal(str(value)).to_integral_value():
            raise ValueError(f'{k}: business, management and B3a scores must be integers')
    reviews = c.get('metric_review', {})
    if set(reviews) != SCORE_KEYS:
        raise ValueError(f"{c['company_id']}: all metrics need review status")
    pending = [k for k,v in reviews.items() if v == 'pending_work']
    invalid = [k for k,v in reviews.items() if v not in ['reviewed', 'not_applicable', 'evidence_limited', 'provisional', 'pending_work']]
    if invalid:
        raise ValueError(f"{c['company_id']}: invalid review statuses {invalid}")
    years = c.get('perimeter_years')
    if isinstance(years, bool) or not isinstance(years, int) or years < 0:
        raise ValueError('perimeter_years must be a nonnegative integer')
    short = years < 3
    for k, review in reviews.items():
        if review in ['not_applicable','evidence_limited'] and scores[k] is not None:
            raise ValueError(f'{k}: N/A status must have null score')
        if review in ['reviewed','provisional'] and scores[k] is None:
            raise ValueError(f'{k}: reviewed/provisional needs a numerical score')
    if short:
        for k in ('B1','B2','M3'):
            if scores[k] is not None and (scores[k] > 3 or reviews[k] != 'provisional'):
                raise ValueError(f'{k}: history below three years requires provisional score at most3')
    provisional_gate = short or c.get('provisional_history') or any(v=='provisional' for v in reviews.values())
    factors = {p: factor(scores, keys) for p, keys in FACTOR_KEYS.items()}
    avg = statistics.mean(f['score'] for f in factors.values()) if all(f['score'] is not None for f in factors.values()) else None
    gate_values = [scores[k] for k in ('B1','B2','B3a')]
    stage_mean = statistics.mean(gate_values) if all(v is not None for v in gate_values) else None
    # A missing score stays null. Bounds prove the gate only if EVERY possible
    # legal completion (1..5) gives the same answer; this is not imputation.
    lower = sum(1 if v is None else v for v in gate_values) / 3
    upper = sum(5 if v is None else v for v in gate_values) / 3
    stage = (False if scores['B1'] is not None and scores['B1'] < 3 else
             True if scores['B1'] is not None and scores['B1'] >= 3 and lower >= 3 else
             False if upper < 3 else None)
    quality = factors['B']['score'] >= 3.5 and factors['M']['score'] >= 3 and factors['I']['score'] >= 3 if avg is not None else None
    # Conservative check of every unscored metric. These values are a sensitivity
    # calculation only and never become the recorded company scores.
    floor_scores = {k:1 if v is None else v for k,v in scores.items()}
    quality_floor = {p:factor(floor_scores,keys)['score'] for p,keys in FACTOR_KEYS.items()}
    robust = quality_floor['B'] >= 3.5 and quality_floor['M'] >= 3 and quality_floor['I'] >= 3
    price = c['price']; pct = price.get('percentile')
    if pct is not None and (not 0 <= pct <= 100 or not price.get('trailing_pe') or price['trailing_pe'] <= 0):
        raise ValueError('Invalid historical P/E percentile')
    if pct is not None and (not isinstance(price.get('history_years'), (int,float)) or not math.isfinite(price['history_years']) or price['history_years']<=0):
        raise ValueError('Percentile requires positive historical coverage')
    valuation_band = None if pct is None else 'bottom' if pct <= 100/3 else 'middle' if pct <= 200/3 else 'top'
    hard_b1 = scores['B1'] == 1 and reviews['B1'] == 'reviewed'
    hard_m5 = scores['M5'] == 1 and reviews['M5'] == 'reviewed'
    if hard_b1 or hard_m5:
        status = 'removed'
    elif pending:
        status = 'pending_work'
    elif c.get('blocking_issues') or provisional_gate:
        status = 'provisional_review'
    elif avg is None or stage is None or scores['M5'] is None:
        status = 'complete_unscorable'
    elif not stage:
        status = 'fails_stage_1'
    elif quality and not robust:
        status = 'quality_sensitive'
    elif quality:
        status = {None:'quality_pass_valuation_unavailable','bottom':'research_now','middle':'watch_closely','top':'watchlist'}[valuation_band]
    else:
        status = 'cheap_fails_quality' if valuation_band == 'bottom' else 'ignore'
    return {'company_id': c['company_id'], 'name': c['name'], 'scores': scores,
            'factors': factors, 'average': round(avg, 2) if avg is not None else None,
            'stage_1': stage, 'stage_1_mean': stage_mean, 'stage_1_bounds': [lower,upper], 'quality_pass': quality,
            'status': status, 'label': LABELS[status], 'price_band': valuation_band,
            'quality_floor': quality_floor, 'quality_robust_to_unscored': robust,
            'completion_status': 'pending_work' if pending else 'complete_limited' if any(v=='evidence_limited' for v in reviews.values()) else 'complete',
            'comparability': 'provisional' if provisional_gate else 'complete_unscorable' if status=='complete_unscorable' else 'eligible' if avg is not None else 'complete_unscorable',
            'pending_metrics': pending, 'blocking_issues': c.get('blocking_issues', [])}


def aggregate(payload):
    if payload['rule_version'] != VERSION:
        raise ValueError('Expected screen-v2')
    results = [evaluate(c) for c in payload['companies']]
    if len({c['company_id'] for c in results}) != len(results):
        raise ValueError('Duplicate issuer')
    order = {s: i for i,s in enumerate(['research_now','watch_closely','watchlist','quality_pass_valuation_unavailable','quality_sensitive','cheap_fails_quality','fails_stage_1','ignore','provisional_review','complete_unscorable','removed','pending_work'])}
    results.sort(key=lambda c:(order[c['status']], -(c['average'] or 0), c['company_id']))
    return {'rule_version':VERSION,'as_of':payload['as_of'],'price_date':payload['price_date'],
            'count':len(results),'companies':results}
