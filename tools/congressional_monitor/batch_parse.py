"""Batch conversion of synced House reports into analyzable trade events."""

from __future__ import annotations

from datetime import datetime
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
from typing import Any

from .dedupe import deduplicate_trades
from .ptr_text import parse_text_layer_pdf


def _iso_filing_date(value: Any) -> str:
    text = str(value or "")
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return text


def _member_id(report: dict[str, Any]) -> str:
    index = report.get("index") or {}
    raw = f"{index.get('first_name', '')}-{index.get('last_name', '')}".lower()
    value = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    return value or str(report.get("document_id") or "unknown-member")


def _ticker(candidate: dict[str, Any]) -> str:
    options = candidate.get("ticker_candidates") or []
    if len(options) != 1:
        return ""
    item = options[0]
    return str(item.get("ticker") if isinstance(item, dict) else item).upper()


def _trade_from_candidate(candidate: dict[str, Any], report: dict[str, Any]) -> dict[str, Any] | None:
    ticker = _ticker(candidate)
    amounts = candidate.get("amount_range_candidates") or []
    codes = candidate.get("transaction_codes") or []
    assets = candidate.get("asset_type_candidates") or []
    if not (ticker and len(amounts) == 1 and len(codes) == 1 and len(assets) == 1 and candidate.get("transaction_date")):
        return None
    index = report.get("index") or {}
    report_id = str(report.get("document_id") or "")
    candidate_id = str(candidate.get("candidate_id") or "")
    return {
        "id": f"{report_id}-{candidate_id}" if report_id and candidate_id else candidate_id,
        "candidate_id": candidate_id,
        "report_id": report_id,
        "filing_date": _iso_filing_date(index.get("filing_date")),
        "transaction_date": candidate.get("transaction_date"),
        "ticker": ticker,
        "issuer": (candidate.get("ticker_candidates") or [{}])[0].get("issuer") if isinstance((candidate.get("ticker_candidates") or [{}])[0], dict) else candidate.get("asset_name"),
        "asset_type": assets[0],
        "transaction_code": codes[0],
        "amount_range": amounts[0],
        "owner_code": candidate.get("owner_code") or "",
        "description": candidate.get("description") or "",
        "quantity": candidate.get("quantity"),
        "quantity_unit": candidate.get("quantity_unit"),
        "member_id": _member_id(report),
        "member_name": f"{index.get('first_name', '')} {index.get('last_name', '')}".strip(),
        "district": index.get("district", ""),
        "chamber": "House",
        "source": "house-clerk",
        "source_file": report.get("path"),
        "report_kind": report.get("report_kind") or ("amendment" if str(index.get("filing_type", "")).upper() == "A" else "original"),
        "amends_report_id": report.get("amends_report_id") or index.get("amends_report_id") or None,
    }


def _validated_candidates(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    values = parsed.get("validated_candidates")
    if isinstance(values, list):
        return [item for item in values if isinstance(item, dict)]
    return [item for page in parsed.get("pages", []) for item in (page.get("validated_candidates") or []) if isinstance(item, dict)]


def build_effective_view(reports: list[dict[str, Any]], trades: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply only explicit amendment links, then exact cross-file de-duplication."""

    superseded: dict[str, str] = {}
    unlinked: list[str] = []
    for report in reports:
        if report.get("report_kind") == "amendment":
            target = report.get("amends_report_id") or (report.get("index") or {}).get("amends_report_id")
            if target:
                superseded[str(target)] = str(report.get("document_id"))
            else:
                unlinked.append(str(report.get("document_id")))
    effective = [trade for trade in trades if str(trade.get("report_id")) not in superseded]
    deduped = deduplicate_trades(effective)
    return {
        "trades": deduped["trades"],
        "superseded_reports": [{"report_id": old, "replaced_by": new} for old, new in sorted(superseded.items())],
        "unlinked_amendments": sorted(unlinked),
        "duplicates": deduped["duplicates"],
        "duplicate_count": deduped["duplicate_count"],
    }


def parse_sync_manifest(manifest_path: Path | str, *, minimum_probability: float = 0.90) -> dict[str, Any]:
    source = Path(manifest_path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"sync manifest not found: {source}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid sync manifest JSON: {source}: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("reports"), list):
        raise ValueError("sync manifest must contain a reports list")
    report_results: list[dict[str, Any]] = []
    all_trades: list[dict[str, Any]] = []
    counts = {"parsed": 0, "ocr_queue": 0, "failed": 0, "candidate_count": 0, "review_count": 0, "analysis_ready_count": 0}
    for report in payload["reports"]:
        if not isinstance(report, dict):
            continue
        item = {key: report.get(key) for key in ("document_id", "year", "status", "path", "report_kind", "amends_report_id", "lineage_status", "index")}
        path = Path(str(report.get("path"))) if report.get("path") else None
        parsed = report.get("parsed") if isinstance(report.get("parsed"), dict) else None
        if parsed:
            parsed_result = parsed
            item["parse_source"] = "sync_ocr"
        elif report.get("text_layer", {}).get("ocr_required"):
            item["parse_status"] = "ocr_queue"
            item["ocr_reason"] = "text_layer_missing_or_insufficient"
            counts["ocr_queue"] += 1
            report_results.append(item)
            continue
        elif path and path.is_file():
            try:
                parsed_result = parse_text_layer_pdf(path, source_sha256=report.get("sha256"), report=report, minimum_probability=minimum_probability)
                item["parse_source"] = "text_layer"
            except Exception as exc:
                item["parse_status"] = "failed"
                item["error"] = str(exc)
                counts["failed"] += 1
                report_results.append(item)
                continue
        else:
            item["parse_status"] = "failed"
            item["error"] = "report PDF is not available"
            counts["failed"] += 1
            report_results.append(item)
            continue
        candidates = _validated_candidates(parsed_result)
        review_queue = parsed_result.get("review_queue") or []
        trades = [trade for candidate in candidates if (trade := _trade_from_candidate(candidate, report))]
        item.update({"parse_status": "parsed", "candidate_count": len(candidates) + len(review_queue), "review_count": len(review_queue), "analysis_ready_count": len(trades), "parsed": parsed_result})
        report_results.append(item)
        all_trades.extend(trades)
        counts["parsed"] += 1
        counts["candidate_count"] += item["candidate_count"]
        counts["review_count"] += item["review_count"]
        counts["analysis_ready_count"] += len(trades)
    effective = build_effective_view(report_results, all_trades)
    quality = {
        "report_count": len(report_results),
        "parsed_reports": counts["parsed"],
        "ocr_queue_reports": counts["ocr_queue"],
        "failed_reports": counts["failed"],
        "amendment_reports": sum(item.get("report_kind") == "amendment" for item in report_results),
        "unlinked_amendment_reports": len(effective["unlinked_amendments"]),
        "candidate_count": counts["candidate_count"],
        "review_count": counts["review_count"],
        "analysis_ready_count": counts["analysis_ready_count"],
        "review_rate": round(counts["review_count"] / counts["candidate_count"], 4) if counts["candidate_count"] else 0.0,
        "analysis_ready_rate": round(counts["analysis_ready_count"] / counts["candidate_count"], 4) if counts["candidate_count"] else 0.0,
    }
    counts.update({"report_count": len(report_results), "effective_trade_count": len(effective["trades"])})
    return {"source_manifest": str(source), "changes": payload.get("changes") or {}, "counts": counts, "quality": quality, "reports": report_results, "analysis_ready_trades": all_trades, "effective": effective}


def summarize_effective_trades(trades: list[dict[str, Any]]) -> dict[str, Any]:
    dates = [str(item.get("transaction_date")) for item in trades if item.get("transaction_date")]
    return {
        "trade_count": len(trades),
        "member_count": len({item.get("member_id") for item in trades if item.get("member_id")}),
        "ticker_count": len({item.get("ticker") for item in trades if item.get("ticker")}),
        "date_range": {"from": min(dates) if dates else None, "to": max(dates) if dates else None},
        "members": dict(Counter(item.get("member_name") or item.get("member_id") for item in trades).most_common()),
        "tickers": dict(Counter(item.get("ticker") for item in trades).most_common()),
        "directions": dict(Counter(item.get("transaction_code") for item in trades).most_common()),
        "asset_types": dict(Counter(item.get("asset_type") for item in trades).most_common()),
        "quantity": {
            "explicit_trade_count": sum(item.get("quantity") is not None for item in trades),
            "unknown_trade_count": sum(item.get("quantity") is None for item in trades),
        },
    }


def detect_event_alerts(parse_result: dict[str, Any], *, window_days: int = 30) -> list[dict[str, Any]]:
    """Generate descriptive event alerts without inferring intent."""

    window_days = max(1, int(window_days))
    trades = list((parse_result.get("effective") or {}).get("trades") or [])
    alerts: list[dict[str, Any]] = []
    manifest_changes = parse_result.get("changes") or {}
    for report in manifest_changes.get("new_reports") or []:
        alerts.append({"type": "new_report", "document_id": report.get("document_id"), "report_kind": report.get("report_kind") or "original"})
    for report in manifest_changes.get("changed_reports") or []:
        alerts.append({"type": "changed_report", "document_id": report.get("document_id")})
    for report_id in (parse_result.get("effective") or {}).get("unlinked_amendments") or []:
        alerts.append({"type": "unlinked_amendment", "document_id": report_id})

    by_member_ticker: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    by_ticker: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        by_member_ticker[(str(trade.get("member_id")), str(trade.get("ticker")))].append(trade)
        by_ticker[str(trade.get("ticker"))].append(trade)
    for (member_id, ticker), rows in by_member_ticker.items():
        first = min(rows, key=lambda item: str(item.get("transaction_date") or ""))
        alerts.append({"type": "member_first_ticker", "member_id": member_id, "member_name": first.get("member_name"), "ticker": ticker, "transaction_date": first.get("transaction_date"), "transaction_code": first.get("transaction_code")})
    for ticker, rows in by_ticker.items():
        dated: list[tuple[Any, dict[str, Any]]] = []
        for item in rows:
            if not item.get("transaction_date"):
                continue
            try:
                dated.append((datetime.fromisoformat(str(item["transaction_date"])).date(), item))
            except ValueError:
                continue
        dated.sort(key=lambda pair: pair[0])
        window_rows: list[dict[str, Any]] = []
        for index, (start_day, _) in enumerate(dated):
            cohort = [item for day, item in dated[index:] if (day - start_day).days <= window_days]
            if len({str(item.get("member_id")) for item in cohort}) >= 2:
                window_rows = cohort
                break
        if not window_rows:
            continue
        members = sorted({str(item.get("member_id")) for item in window_rows})
        dates = sorted(str(item.get("transaction_date")) for item in window_rows if item.get("transaction_date"))
        alerts.append({"type": "multi_member_ticker", "ticker": ticker, "member_ids": members, "member_count": len(members), "date_range": {"from": dates[0] if dates else None, "to": dates[-1] if dates else None}, "window_days": window_days})
    return alerts
