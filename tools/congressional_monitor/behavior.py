"""Behavioral analysis for congressional PTR disclosures.

This module describes disclosed member behavior.  It deliberately avoids
claiming current holdings, exact dollar values, intent, or investment returns.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
import re
from typing import Any, Iterable

from .company_context import company_context
from .member_priority import rank_member_priorities


_AMOUNT_BAND_RANK = {letter: rank for rank, letter in enumerate("ABCDEFGHIJ", start=1)}
_DIRECTION_LABELS = {"P": "buy", "S": "sell", "E": "exchange"}


def _day(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _member_key(row: dict[str, Any]) -> str:
    return str(row.get("member_id") or row.get("member_name") or "unknown-member")


def _ticker_key(row: dict[str, Any]) -> str:
    return str(row.get("ticker") or "").strip().upper()


def _amount_rank(value: Any) -> int | None:
    text = str(value or "").strip().upper()
    if text in _AMOUNT_BAND_RANK:
        return _AMOUNT_BAND_RANK[text]
    # Some normalized sources retain labels such as ``A ($1-$15,000)``.
    if text:
        rank = _AMOUNT_BAND_RANK.get(text[:1])
        if rank:
            return rank
        lower = re.search(r"\$?\s*([\d,]+)", text)
        if lower:
            value_number = int(lower.group(1).replace(",", ""))
            for threshold, band in ((1_000, 1), (15_001, 2), (50_001, 3), (100_001, 4), (250_001, 5), (500_001, 6), (1_000_001, 7), (5_000_001, 8), (25_000_001, 9), (50_000_001, 10)):
                if value_number >= threshold:
                    rank = band
            return rank
    return None


def _period_rows(rows: list[dict[str, Any]], start: date | None, end: date | None) -> list[dict[str, Any]]:
    return [row for row in rows if _ticker_key(row) and (day := _day(row.get("transaction_date"))) and (start is None or day >= start) and (end is None or day <= end)]


def _ticker_stats(rows: list[dict[str, Any]], *, all_rows: list[dict[str, Any]], active_member_count: int, min_members: int) -> list[dict[str, Any]]:
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_ticker_key(row)].append(row)
    first_seen: dict[tuple[str, str], date] = {}
    for row in all_rows:
        key = (_member_key(row), _ticker_key(row))
        day = _day(row.get("transaction_date"))
        if key[1] and day and (key not in first_seen or day < first_seen[key]):
            first_seen[key] = day
    output: list[dict[str, Any]] = []
    for ticker, ticker_rows in grouped.items():
        by_direction: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
        by_member_direction: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in ticker_rows:
            direction = str(row.get("transaction_code") or "").upper()
            by_direction[direction].append(row)
            by_member_direction[(_member_key(row), direction)].append(row)
        members = {_member_key(row) for row in ticker_rows}
        buy_members = {_member_key(row) for row in by_direction.get("P", [])}
        sell_members = {_member_key(row) for row in by_direction.get("S", [])}
        member_assets: defaultdict[str, set[str]] = defaultdict(set)
        for row in ticker_rows:
            if str(row.get("transaction_code") or "").upper() == "P":
                member_assets[_member_key(row)].add(str(row.get("asset_type") or "").upper())
        compound_long_members = {member for member, assets in member_assets.items() if "ST" in assets and "OP" in assets}
        repeat_buy_members = {member for (member, direction), member_rows in by_member_direction.items() if direction == "P" and len(member_rows) >= 2}
        first_time_members = {
            _member_key(row) for row in ticker_rows
            if str(row.get("transaction_code") or "").upper() == "P"
            and _day(row.get("transaction_date")) == first_seen.get((_member_key(row), ticker))
        }
        known_quantity_by_unit: defaultdict[str, float] = defaultdict(float)
        known_quantity_trade_count = 0
        for row in ticker_rows:
            quantity = row.get("quantity")
            if quantity is None:
                continue
            direction = str(row.get("transaction_code") or "").upper()
            if direction not in {"P", "S"}:
                continue
            unit = str(row.get("quantity_unit") or "unknown")
            known_quantity_by_unit[unit] += float(quantity) if direction == "P" else -float(quantity)
            known_quantity_trade_count += 1
        buy_ranks = [_amount_rank(row.get("amount_range")) for row in by_direction.get("P", [])]
        sell_ranks = [_amount_rank(row.get("amount_range")) for row in by_direction.get("S", [])]
        buy_ranks = [value for value in buy_ranks if value is not None]
        sell_ranks = [value for value in sell_ranks if value is not None]
        direction_balance = len(buy_members) - len(sell_members)
        member_share = len(members) / active_member_count if active_member_count else 0.0
        buy_participation = len(buy_members) / active_member_count if active_member_count else 0.0
        signal: list[str] = []
        score = 0
        if len(members) >= min_members and direction_balance != 0:
            signal.append("multi_member_attention")
            score += min(12, len(members) * 2)
        if len(buy_members) >= max(3, len(sell_members) + 2) and buy_participation >= 0.05:
            signal.append("broad_accumulation")
            score += 30
        elif active_member_count and len(sell_members) >= max(3, len(buy_members) + 2) and len(sell_members) / active_member_count >= 0.05:
            signal.append("broad_reduction")
            score += 30
        elif buy_members and sell_members:
            signal.append("mixed_direction_attention")
            score += 2
        if repeat_buy_members:
            signal.append("repeat_buying")
            score += min(16, len(repeat_buy_members) * 8)
        if compound_long_members:
            signal.append("compound_long_exposure")
            score += min(20, len(compound_long_members) * 10)
        if first_time_members and len(first_time_members) >= 2:
            signal.append("new_group_attention")
            score += 15
        if buy_ranks:
            score += min(15, round(sum(buy_ranks) / len(buy_ranks) * 2))
        chambers = sorted({str(row.get("chamber") or "Unknown") for row in ticker_rows})
        if len(chambers) >= 2:
            signal.append("cross_chamber_convergence")
            score += 15
        parties = sorted({str(row.get("party") or "").strip().upper() for row in ticker_rows if row.get("party")})
        if len(parties) >= 2:
            signal.append("cross_party_convergence")
            score += 15
        context = company_context(ticker, next((row.get("issuer") for row in ticker_rows if row.get("issuer")), None))
        output.append({
            "ticker": ticker,
            "issuer": next((row.get("issuer") for row in ticker_rows if row.get("issuer")), None),
            "company_context": context,
            "trade_count": len(ticker_rows),
            "member_count": len(members),
            "buy_trade_count": len(by_direction.get("P", [])),
            "sell_trade_count": len(by_direction.get("S", [])),
            "exchange_trade_count": len(by_direction.get("E", [])),
            "buy_member_count": len(buy_members),
            "sell_member_count": len(sell_members),
            "directional_member_balance": direction_balance,
            "buy_participation_rate": round(buy_participation, 4),
            "disclosed_member_share": round(member_share, 4),
            "repeat_buy_member_count": len(repeat_buy_members),
            "compound_long_member_count": len(compound_long_members),
            "first_time_buy_member_count": len(first_time_members),
            "known_net_quantity_by_unit": {unit: int(value) if value.is_integer() else value for unit, value in sorted(known_quantity_by_unit.items())} if known_quantity_by_unit else {},
            "known_quantity_trade_count": known_quantity_trade_count,
            "buy_amount_band_rank_mean": round(sum(buy_ranks) / len(buy_ranks), 2) if buy_ranks else None,
            "sell_amount_band_rank_mean": round(sum(sell_ranks) / len(sell_ranks), 2) if sell_ranks else None,
            "chambers": chambers,
            "parties": parties,
            "signals": signal,
            "behavior_score": min(score, 100),
            "members": sorted({str(row.get("member_name") or _member_key(row)) for row in ticker_rows}),
        })
    return sorted(output, key=lambda item: (-item["behavior_score"], -item["member_count"], -item["trade_count"], item["ticker"]))


def _member_stats(rows: list[dict[str, Any]], *, focus_members: set[str] | None = None, member_priorities: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_member_key(row)].append(row)
    output = []
    for member_id, member_rows in grouped.items():
        member_name = next((row.get("member_name") for row in member_rows if row.get("member_name")), member_id)
        if focus_members:
            searchable = f"{member_id} {member_name}".lower()
            if not any(value.lower() in searchable for value in focus_members):
                continue
        buys = [row for row in member_rows if str(row.get("transaction_code") or "").upper() == "P"]
        sells = [row for row in member_rows if str(row.get("transaction_code") or "").upper() == "S"]
        tickers = {_ticker_key(row) for row in member_rows if _ticker_key(row)}
        buy_tickers = {_ticker_key(row) for row in buys if _ticker_key(row)}
        sell_tickers = {_ticker_key(row) for row in sells if _ticker_key(row)}
        ticker_changes = Counter(_ticker_key(row) for row in member_rows if _ticker_key(row))
        output.append({
            "member_id": member_id,
            "member_name": member_name,
            "party": next((row.get("party") for row in member_rows if row.get("party")), None),
            "chambers": sorted({str(row.get("chamber") or "Unknown") for row in member_rows}),
            "trade_count": len(member_rows),
            "buy_trade_count": len(buys),
            "sell_trade_count": len(sells),
            "ticker_count": len(tickers),
            "buy_ticker_count": len(buy_tickers),
            "sell_ticker_count": len(sell_tickers),
            "net_directional_ticker_balance": len(buy_tickers - sell_tickers) - len(sell_tickers - buy_tickers),
            "change_mode_tickers": [{"ticker": ticker, "change_count": count} for ticker, count in ticker_changes.most_common(5)],
            "top_buy_tickers": sorted(Counter(_ticker_key(row) for row in buys if _ticker_key(row)).items(), key=lambda item: (-item[1], item[0]))[:5],
            "top_sell_tickers": sorted(Counter(_ticker_key(row) for row in sells if _ticker_key(row)).items(), key=lambda item: (-item[1], item[0]))[:5],
            "buy_trade_share": round(len(buys) / len(member_rows), 4) if member_rows else 0.0,
            "distinct_buy_dates": len({_day(row.get("transaction_date")) for row in buys if _day(row.get("transaction_date"))}),
            "member_priority": (member_priorities or {}).get(member_id),
        })
    return sorted(output, key=lambda item: (-((item.get("member_priority") or {}).get("priority_score") or 0), -item["buy_trade_count"], -item["trade_count"], item["member_name"]))


def _window(rows: list[dict[str, Any]], *, all_rows: list[dict[str, Any]], label: str, start: date | None, end: date | None, min_members: int, top_n: int, focus_members: set[str] | None = None, member_priorities: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    selected = _period_rows(rows, start, end)
    active_members = {_member_key(row) for row in selected}
    tickers = _ticker_stats(selected, all_rows=all_rows, active_member_count=len(active_members), min_members=min_members)
    buy_mode = {(_ticker_key(row), _member_key(row)) for row in selected if str(row.get("transaction_code") or "").upper() == "P"}
    sell_mode = {(_ticker_key(row), _member_key(row)) for row in selected if str(row.get("transaction_code") or "").upper() == "S"}
    def mode_rows(pairs: set[tuple[str, str]]) -> list[dict[str, Any]]:
        ticker_counts = Counter(ticker for ticker, _ in pairs)
        return [{"ticker": ticker, "member_change_count": count} for ticker, count in ticker_counts.most_common(10)]
    return {
        "label": label,
        "from_date": start.isoformat() if start else None,
        "to_date": end.isoformat() if end else None,
        "active_member_count": len(active_members),
        "trade_count": len(selected),
        "ticker_count": len({ _ticker_key(row) for row in selected}),
        "buy_trade_count": sum(str(row.get("transaction_code") or "").upper() == "P" for row in selected),
        "sell_trade_count": sum(str(row.get("transaction_code") or "").upper() == "S" for row in selected),
        "tickers": tickers[:top_n],
        "change_mode": {"buy": mode_rows(buy_mode), "sell": mode_rows(sell_mode)},
        "members": _member_stats(selected, focus_members=focus_members, member_priorities=member_priorities)[:top_n],
    }


def _trend(rows: list[dict[str, Any]], *, all_rows: list[dict[str, Any]], end: date, days: int, min_members: int, top_n: int) -> list[dict[str, Any]]:
    recent_start = end - timedelta(days=days - 1)
    prior_end = recent_start - timedelta(days=1)
    prior_start = prior_end - timedelta(days=days - 1)
    recent = {item["ticker"]: item for item in _ticker_stats(_period_rows(rows, recent_start, end), all_rows=all_rows, active_member_count=len({_member_key(row) for row in _period_rows(rows, recent_start, end)}), min_members=min_members)}
    prior = {item["ticker"]: item for item in _ticker_stats(_period_rows(rows, prior_start, prior_end), all_rows=all_rows, active_member_count=len({_member_key(row) for row in _period_rows(rows, prior_start, prior_end)}), min_members=min_members)}
    changes = []
    for ticker in set(recent) | set(prior):
        current, previous = recent.get(ticker, {}), prior.get(ticker, {})
        delta = (current.get("directional_member_balance", 0) - previous.get("directional_member_balance", 0))
        delta_buy = current.get("buy_member_count", 0) - previous.get("buy_member_count", 0)
        delta_sell = current.get("sell_member_count", 0) - previous.get("sell_member_count", 0)
        if not (delta or delta_buy or delta_sell):
            continue
        changes.append({"ticker": ticker, "issuer": current.get("issuer") or previous.get("issuer"), "company_context": current.get("company_context") or previous.get("company_context"), "recent_buy_member_count": current.get("buy_member_count", 0), "prior_buy_member_count": previous.get("buy_member_count", 0), "recent_sell_member_count": current.get("sell_member_count", 0), "prior_sell_member_count": previous.get("sell_member_count", 0), "delta_buy_member_count": delta_buy, "delta_sell_member_count": delta_sell, "delta_directional_member_balance": delta})
    return sorted(changes, key=lambda item: (-abs(item["delta_directional_member_balance"]), -abs(item["delta_buy_member_count"]), item["ticker"]))[:top_n]


def analyze_behavior(trades: Iterable[dict[str, Any]], *, windows: Iterable[int] = (30, 90), from_date: str | None = None, to_date: str | None = None, min_members: int = 2, top_n: int = 50, focus_members: Iterable[str] | None = None, include_full_period: bool = False, member_profiles: dict[str, dict[str, Any]] | None = None, important_members: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """Return multi-angle member and ticker behavior signals.

    ``windows`` are optional comparison lenses. The full selected period is
    available as an opt-in background view. Scores are heuristic ranking aids,
    not return forecasts.
    """

    all_rows = [dict(row) for row in trades if isinstance(row, dict) and _ticker_key(row) and _day(row.get("transaction_date"))]
    if not all_rows:
        return {"quality": {"trade_count": 0}, "period": {"from_date": None, "to_date": None}, "windows": [], "trends": []}
    lower = _day(from_date) if from_date else None
    upper = _day(to_date) if to_date else None
    selected = _period_rows(all_rows, lower, upper)
    dates = [_day(row.get("transaction_date")) for row in selected]
    start, end = (min(dates) if dates else lower), (max(dates) if dates else upper)
    if not selected:
        return {"quality": {"trade_count": 0}, "period": {"from_date": lower.isoformat() if lower else None, "to_date": upper.isoformat() if upper else None}, "windows": [], "trends": []}
    windows = sorted({int(days) for days in windows if int(days) > 0})
    focus = {str(value).strip().lower() for value in (focus_members or []) if str(value).strip()}
    priority_rows = rank_member_priorities(all_rows, profiles=member_profiles, recent_days=max(windows or [90]), as_of=end)
    priority_by_id = {item["member_id"]: item for item in priority_rows}
    window_results = [_window(selected, all_rows=all_rows, label=f"last_{days}_days", start=max(start, end - timedelta(days=days - 1)), end=end, min_members=min_members, top_n=top_n, focus_members=focus or None, member_priorities=priority_by_id) for days in windows]
    if include_full_period:
        window_results.append(_window(selected, all_rows=all_rows, label="full_selected_period", start=start, end=end, min_members=min_members, top_n=top_n, focus_members=focus or None, member_priorities=priority_by_id))
    return {
        "period": {"from_date": start.isoformat() if start else None, "to_date": end.isoformat() if end else None},
        "quality": {"trade_count": len(selected), "active_member_count": len({_member_key(row) for row in selected}), "ticker_count": len({_ticker_key(row) for row in selected}), "unknown_quantity_trade_count": sum(row.get("quantity") is None for row in selected), "party_fields_available": any(row.get("party") for row in selected), "chamber_counts": dict(Counter(str(row.get("chamber") or "Unknown") for row in selected)), "focus_members": sorted(focus)},
        "member_priorities": priority_rows,
        "important_members": important_members or {},
        "windows": window_results,
        "trends": [{"label": f"{days}_day_vs_prior_{days}_days", "from_date": max(start, end - timedelta(days=days - 1)).isoformat(), "to_date": end.isoformat(), "changes": _trend(selected, all_rows=all_rows, end=end, days=days, min_members=min_members, top_n=top_n)} for days in windows],
        "interpretation": [
            "行为分数用于排序和筛选，不是收益预测或投资建议。",
            "买入参与率和披露持仓覆盖率基于样本中的申报记录，不等于真实投资组合仓位。",
            "金额只按法定区间做等级比较；明确数量净变化仍可能因未披露数量而不完整。",
            "跨党派信号只有在源数据包含 party 字段时才会计算。",
        ],
    }


_SIGNAL_LABELS = {
    "multi_member_attention": "多人关注",
    "broad_accumulation": "群体增持",
    "broad_reduction": "群体减持",
    "repeat_buying": "重复买入",
    "new_group_attention": "新群体关注",
    "cross_chamber_convergence": "跨院收敛",
    "cross_party_convergence": "跨党派收敛",
    "compound_long_exposure": "股票+期权多头",
    "mixed_direction_attention": "买卖分歧",
}


def _signal_text(values: Iterable[str]) -> str:
    return "、".join(_SIGNAL_LABELS.get(value, value) for value in values) or "-"


def _pct(value: Any) -> str:
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return "-"


def render_behavior_markdown(result: dict[str, Any], *, title: str = "美国国会议员交易行为监测报告") -> str:
    """Render a readable analyst-facing Markdown report from ``analyze_behavior``."""

    period = result.get("period") or {}
    quality = result.get("quality") or {}
    visible_windows = [window for window in (result.get("windows") or []) if window.get("label") != "full_selected_period"]
    visible_labels = "、".join(window.get("label", "") for window in visible_windows) or "-"
    lines = [f"# {title}", "", f"- 数据覆盖范围：{period.get('from_date') or '-'} 至 {period.get('to_date') or '-'}", f"- 主分析窗口：{visible_labels}", f"- 数据记录：{quality.get('trade_count', 0)} 条", f"- 数据覆盖议员：{quality.get('active_member_count', 0)} 位", f"- 数据涉及证券：{quality.get('ticker_count', 0)} 只", f"- 生成时间：{date.today().isoformat()}", ""]
    lines.extend([
        "## 一、执行摘要", "",
        "本报告只分析 PTR（Periodic Transaction Report）披露的议员交易行为，目标是发现群体性增持、减持、重复关注和行为拐点等研究线索，不对公司基本面或未来收益作判断。",
        "",
    ])
    windows = result.get("windows") or []
    non_empty_windows = [window for window in windows if window.get("trade_count")]
    for window in non_empty_windows[:2]:
        top = [item for item in window.get("tickers", []) if item.get("signals")][:5]
        if not top:
            continue
        lines.append(f"**{window.get('label')}**：")
        for item in top:
            context = item.get("company_context") or {}
            lines.append(f"- **{item.get('ticker')}（{context.get('name') or item.get('issuer') or '未知发行人'}）**：买入议员 {item.get('buy_member_count', 0)} 位，卖出议员 {item.get('sell_member_count', 0)} 位，买入参与率 {_pct(item.get('buy_participation_rate'))}；{_signal_text(item.get('signals') or [])}。")
        lines.append("")
    lines.extend(["## 二、各时间窗口的群体行为", "", "以下榜单按启发式行为分数排序，分数只用于筛选研究对象。", ""])
    for window in windows:
        lines.extend([f"### {window.get('label')}", "", f"窗口：{window.get('from_date') or '-'} 至 {window.get('to_date') or '-'}；交易 {window.get('trade_count', 0)} 条；活跃议员 {window.get('active_member_count', 0)} 位。", "", "| 排名 | 股票 | 买入议员 | 卖出议员 | 买入参与率 | 方向净差 | 重复买入 | 首次关注 | 行为信号 |", "|---:|---|---:|---:|---:|---:|---:|---:|---|"])
        for rank, item in enumerate(window.get("tickers", [])[:20], start=1):
            context = item.get("company_context") or {}
            name = context.get("name") or item.get("issuer") or "未知发行人"
            lines.append(f"| {rank} | {item.get('ticker', '-')}（{name}） | {item.get('buy_member_count', 0)} | {item.get('sell_member_count', 0)} | {_pct(item.get('buy_participation_rate'))} | {item.get('directional_member_balance', 0)} | {item.get('repeat_buy_member_count', 0)} | {item.get('first_time_buy_member_count', 0)} | {_signal_text(item.get('signals') or [])} |")
        lines.append("")
        buy_mode = (window.get("change_mode") or {}).get("buy") or []
        sell_mode = (window.get("change_mode") or {}).get("sell") or []
        if buy_mode or sell_mode:
            buy_text = "、".join(f"{item['ticker']}（{item['member_change_count']} 次）" for item in buy_mode[:5]) or "-"
            sell_text = "、".join(f"{item['ticker']}（{item['member_change_count']} 次）" for item in sell_mode[:5]) or "-"
            lines.append(f"变动众数：买入 {buy_text}；卖出 {sell_text}。")
            lines.append("")
    lines.extend(["## 三、行为趋势变化", "", "趋势为当前窗口与前一个同长度窗口的披露行为差异，不代表价格趋势。", "", "| 比较窗口 | 股票 | 当前买入议员 | 前期买入议员 | 当前卖出议员 | 前期卖出议员 | 买入变化 | 方向净差变化 |", "|---|---|---:|---:|---:|---:|---:|---:|"])
    for trend in result.get("trends") or []:
        for item in (trend.get("changes") or [])[:20]:
            context = item.get("company_context") or {}
            name = context.get("name") or item.get("issuer") or "未知发行人"
            lines.append(f"| {trend.get('label', '-')} | {item.get('ticker', '-')}（{name}） | {item.get('recent_buy_member_count', 0)} | {item.get('prior_buy_member_count', 0)} | {item.get('recent_sell_member_count', 0)} | {item.get('prior_sell_member_count', 0)} | {item.get('delta_buy_member_count', 0):+d} | {item.get('delta_directional_member_balance', 0):+d} |")
    if not any(trend.get("changes") for trend in (result.get("trends") or [])):
        lines.append("| - | 暂无可比较变化 | - | - | - | - | - | - |")
    lines.append("")
    profile_window = next((window for window in windows if window.get("label") == "last_30_days"), None)
    profile_window = profile_window or next((window for window in reversed(windows) if window.get("label") != "full_selected_period"), None)
    if profile_window:
        focus = (quality.get("focus_members") or [])
        all_profile_members = profile_window.get("members") or []
        important_ids = {str(key).lower() for key in (result.get("important_members") or {})}
        important_members = [item for item in all_profile_members if str(item.get("member_id") or "").lower() in important_ids]
        priority_members = [item for item in all_profile_members if str((item.get("member_priority") or {}).get("priority_level") or "").startswith(("A ", "B "))]
        if focus:
            profile_members = all_profile_members[:10]
            heading = "指定议员近期行为画像"
            note = "以下为命令行指定的议员；重点级别仍按自动评分计算。"
        elif important_members:
            profile_members = important_members[:10]
            heading = "重点议员近期行为画像"
            note = "仅展示预先维护的重点议员名单中、且在近 30 天有交易的议员。"
        elif priority_members:
            profile_members = priority_members[:10]
            heading = "自动评级重点议员画像"
            note = "仅展示自动评级为 A 核心或 B 重点、且在近 30 天有交易的议员。"
        else:
            profile_members = all_profile_members[:8]
            heading = "近期高活跃议员画像"
            note = "当前缺少正式职务/委员会/媒体元数据，暂以近 90 日行为活跃度排序；不等于政治影响力排名。"
        lines.extend([f"## 四、{heading}", "", note, "", "| 议员 | 近 30 日交易 | 买入 | 卖出 | 买入证券 | 卖出证券 | 方向净差 | 变动众数 |", "|---|---:|---:|---:|---|---|---:|---|"])
        for item in profile_members:
            def ticker_text(entries: Any) -> str:
                labels = []
                for ticker, count in entries[:5]:
                    context = company_context(ticker)
                    name = context.get("name") or ticker
                    labels.append(f"{ticker}（{name}）×{count}")
                return "、".join(labels) or "-"
            mode = "、".join(f"{entry['ticker']}×{entry['change_count']}" for entry in (item.get("change_mode_tickers") or [])[:3]) or "-"
            lines.append(f"| {item.get('member_name', '-')} | {item.get('trade_count', 0)} | {item.get('buy_trade_count', 0)} | {item.get('sell_trade_count', 0)} | {ticker_text(item.get('top_buy_tickers') or [])} | {ticker_text(item.get('top_sell_tickers') or [])} | {item.get('net_directional_ticker_balance', 0):+d} | {mode} |")
        lines.append("")
    lines.extend([
        "## 五、重点公司简介", "",
        "公司简介仅用于帮助读者理解证券所属业务，不代表估值判断或投资建议。已收录公司使用固定业务概览；未收录证券仅做名称级粗略归类，并会明确标注需要进一步核验。", "",
        "| 股票 | 公司/发行人 | 所属领域 | 简要业务概览 |", "|---|---|---|---|",
    ])
    seen_context: set[str] = set()
    for window in windows:
        for item in window.get("tickers", []):
            ticker = str(item.get("ticker") or "")
            if not ticker or ticker in seen_context:
                continue
            seen_context.add(ticker)
            context = item.get("company_context") or {}
            sector = context.get("sector") or "未分类"
            if context.get("inferred"):
                sector = f"{sector}（名称推断）"
            lines.append(f"| {ticker} | {context.get('name') or item.get('issuer') or '-'} | {sector} | {context.get('summary') or '需补充公司公开资料。'} |")
    lines.extend([
        "",
        "## 六、信号解释框架", "",
        "- **群体增持**：同一窗口内买入议员明显多于卖出议员，且参与率达到筛选阈值。可作为群体关注线索，需观察后续是否持续。",
        "- **群体减持**：卖出议员明显多于买入议员。可作为风险偏好或暴露下降线索，不能直接解释为看空动机。",
        "- **重复买入**：同一议员在窗口内多次买入同一股票，区别于一次性交易。",
        "- **股票+期权多头**：同一议员在窗口内同时买入普通股和期权，表示披露层面的多工具上行敞口，应单独核验期权执行价和到期日。",
        "- **买卖分歧**：同一窗口内同时出现买入和卖出议员，表示行为方向不一致，不应当作群体增持。",
        "- **新群体关注**：多位议员在样本历史中首次出现该股票，可能是新出现的关注主题。",
        "- **跨院/跨党派收敛**：仅当输入数据包含相应字段且覆盖充分时才有解释力。",
        "",
        "## 七、数据边界与使用方式", "",
        f"- 当前样本包含 {quality.get('active_member_count', 0)} 位活跃议员和 {quality.get('ticker_count', 0)} 只证券，不等于全体国会议员或完整市场持仓。",
        f"- {quality.get('unknown_quantity_trade_count', 0)} 条交易没有明确数量，不能用于精确数量净变化。",
        "- PTR 是延迟交易披露，不是实时持仓；参与率和披露覆盖率不是实际组合仓位比例。",
        "- 金额只保留法定区间，报告不将区间转换为精确金额。",
        "- OCR、修订申报和未链接报告可能影响个别股票的统计，重大信号应回查原始报告。",
        "- 本报告输出的是行为线索，不是投资建议；后续研究应结合价格、行业和新闻信息独立验证。",
        "",
        "## 八、复核优先级建议", "",
        "优先复核同时满足以下条件的记录：多人同向交易、重复买入、首次群体关注、跨院/跨党派收敛，以及金额区间较高的交易。单一议员单次、低置信度且无重复行为的记录优先级较低。",
        "",
    ])
    return "\n".join(lines)
