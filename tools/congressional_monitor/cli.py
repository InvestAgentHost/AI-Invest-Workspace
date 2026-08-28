"""Command-line analysis of congressional PTR transaction disclosures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .core import coverage, cross_chamber_report, filter_trades, infer_positions, load_dataset, summarize, validate_dataset
from .ocr import OCRError, assess_ocr_document, ocr_pdf
from .ptr_ocr import parse_and_validate_document
from .house_index import read_house_index, summarize_house_index
from .review import apply_review_decisions, review_template
from .house_download import download_ptr
from .sync import sync_house_ptrs
from .senate_efd import read_senate_efd, summarize_senate_efd


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, help="Curated data directory; defaults to data/curated.")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON.")
    parser.add_argument("--data-file", action="append", default=[], help="Additional curated JSON file; repeatable for historical years.")
    parser.add_argument("--senate-file", action="append", default=[], help="Senate eFD JSON/CSV; repeatable (place before the subcommand).")
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("summary", "统计交易申报总览、议员分布和证券频次。"),
        ("trades", "列出符合筛选条件的交易申报。"),
        ("member", "查看某位议员的交易统计。"),
        ("ticker", "查看某只证券涉及的议员和交易。"),
        ("positions", "根据明确披露数量估算已披露净持仓变动。"),
        ("report", "一次输出某议员或期间的交易、净变动、来源和质量摘要。"),
        ("coverage", "查看当前快照的议员、报告和日期覆盖。"),
        ("check", "校验规范化数据的必填字段、重复 ID 和引用完整性。"),
        ("ocr", "对扫描型 PTR PDF 的指定页面调用 GLM OCR。"),
        ("ocr-check", "检查 OCR 输出的字段信号、置信度和人工复核风险。"),
        ("ocr-parse", "按坐标重建 PTR 候选交易并生成待复核队列。"),
        ("house-index", "读取 House Clerk 年度索引并发现 PTR 增量报告。"),
        ("ocr-review", "生成 OCR 复核模板，或应用批准决定生成 curated 数据。"),
        ("house-download", "下载一份 House Clerk 官方 PTR PDF，不覆盖已有文件。"),
        ("sync", "串联 House Clerk 索引、下载、文本层判断和 OCR 准备。"),
        ("senate-efd", "读取官方 Senate eFD JSON/CSV 导出并统一交易字段。"),
        ("cross-report", "生成 House/Senate 两院统一交易行为报告。"),
    ):
        command = commands.add_parser(name, help=help_text)
        if name not in {"ocr", "ocr-check", "ocr-parse", "house-index", "ocr-review", "house-download", "sync", "senate-efd", "cross-report"}:
            command.add_argument("value", nargs="?", help="member_id/姓名/地区，或证券 ticker。")
        if name not in {"ocr", "ocr-check", "ocr-parse", "house-index", "ocr-review", "house-download", "sync", "senate-efd", "cross-report"}:
            command.add_argument("--data-dir", type=Path, default=argparse.SUPPRESS, help="Curated data directory; defaults to data/curated.")
            command.add_argument("--data-file", action="append", default=argparse.SUPPRESS, help="Additional curated JSON file; repeatable for historical years.")
            command.add_argument("--member", help="member_id、姓名或地区，例如 pelosi-nancy、CA11。")
            command.add_argument("--ticker", help="股票代码，例如 BE、AAPL。")
            command.add_argument("--from-date", dest="from_date", help="交易日下限 YYYY-MM-DD。")
            command.add_argument("--to-date", dest="to_date", help="交易日上限 YYYY-MM-DD。")
            command.add_argument("--direction", choices=("P", "S", "E"), help="原始方向代码。")
            command.add_argument("--asset-type", help="原始资产类型代码，例如 ST、OP、AB、OT。")
        command.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="Output machine-readable JSON.")
        if name == "ocr":
            command.add_argument("pdf", type=Path, help="待识别的 PDF 路径。")
            command.add_argument("--pages", help="页码列表，例如 1,3；默认全部页面。")
            command.add_argument("--dpi", type=int, default=220, help="PDF 渲染分辨率，默认 220。")
        elif name == "ocr-check":
            command.add_argument("ocr_json", type=Path, help="ocr 命令输出或单页缓存 JSON 路径。")
            command.add_argument("--low-probability", type=float, default=0.80, help="低置信度块阈值，默认 0.80。")
            command.add_argument("--review-probability", type=float, default=0.90, help="页面复核阈值，默认 0.90。")
        elif name == "ocr-parse":
            command.add_argument("ocr_json", type=Path, help="ocr 命令输出或单页缓存 JSON 路径。")
            command.add_argument("--minimum-probability", type=float, default=0.90, help="候选交易最低平均置信度，默认 0.90。")
            command.add_argument("--review-output", type=Path, help="将待复核队列写入 JSON 文件。")
        elif name == "house-index":
            command.add_argument("index_file", type=Path, help="House Clerk YYYYFD.txt 或 ZIP 文件。")
            command.add_argument("--member", help="按姓名、选区或文档 ID 筛选。")
            command.add_argument("--filing-type", default="P", help="申报类型，默认 P（PTR）。")
        elif name == "ocr-review":
            command.add_argument("review_json", type=Path, help="ocr-parse 生成的待复核 JSON。")
            command.add_argument("--decisions", type=Path, help="复核决定 JSON；省略时只生成模板。")
            command.add_argument("--template-output", type=Path, help="写出可编辑的复核模板。")
            command.add_argument("--output", type=Path, help="批准记录的全新 curated JSON 输出路径。")
            command.add_argument("--member-id", help="为批准记录提供默认 member_id。")
            command.add_argument("--member-name", help="为批准记录提供默认议员姓名。")
            command.add_argument("--district", help="为批准记录提供默认选区。")
            command.add_argument("--report-id", help="为批准记录提供默认报告 ID。")
            command.add_argument("--filing-date", help="为批准记录提供默认申报日期 YYYY-MM-DD。")
        elif name == "house-download":
            command.add_argument("document_id", help="House Clerk 文档 ID。")
            command.add_argument("--year", required=True, help="申报年度，例如 2026。")
            command.add_argument("--output-dir", type=Path, default=Path("sources/providers/house-clerk"), help="保存根目录。")
            command.add_argument("--url-template", default=None, help="可选 URL 模板，必须包含 {year} 和 {document_id}。")
        elif name == "sync":
            command.add_argument("--year", required=True, help="申报年度，例如 2025。")
            command.add_argument("--index-file", type=Path, help="年度索引 ZIP/TXT；默认 sources/providers/house-clerk/<year>/<year>FD.zip。")
            command.add_argument("--member", help="按姓名、选区或文档 ID 筛选。")
            command.add_argument("--limit", type=int, help="最多处理多少条索引记录。")
            command.add_argument("--download", action="store_true", help="下载尚不存在的 PTR PDF。")
            command.add_argument("--ocr", action="store_true", help="对无文本层 PDF 调用 GLM OCR。")
            command.add_argument("--pages", help="OCR 页码列表，例如 1,2；默认全部页面。")
            command.add_argument("--dpi", type=int, default=220, help="OCR 渲染分辨率，默认 220。")
            command.add_argument("--output-root", type=Path, default=Path("sources/providers/house-clerk"), help="原始 PDF 保存根目录。")
            command.add_argument("--manifest", type=Path, help="同步清单输出路径；默认 data/derived/congressional-monitor/sync/<year>.json。")
        elif name == "senate-efd":
            command.add_argument("efd_file", type=Path, help="官方 Senate eFD JSON/CSV 导出文件。")
            command.add_argument("--member", help="按 senator/member ID 或姓名筛选。")
        elif name == "cross-report":
            command.add_argument("--senate-file", action="append", default=argparse.SUPPRESS, help="Senate eFD JSON/CSV；可重复。")
            command.add_argument("--from-date", dest="from_date", help="交易日下限 YYYY-MM-DD。")
            command.add_argument("--to-date", dest="to_date", help="交易日上限 YYYY-MM-DD。")
            command.add_argument("--limit", type=int, default=50, help="最多输出多少条近期交易。")
    return parser


def _text_report(command: str, rows: list[dict], dataset: dict, value: str | None) -> str:
    if command == "summary":
        stats = summarize(rows)
        lines = ["国会议员交易申报统计", f"记录数: {stats['trade_count']} | 议员数: {stats['member_count']}", f"交易日: {stats['date_range']['from'] or '-'} 至 {stats['date_range']['to'] or '-'}", "", "方向: " + " · ".join(f"{key} {count}" for key, count in stats["directions"].items()), "资产类型: " + " · ".join(f"{key} {count}" for key, count in stats["asset_types"].items()), "", "议员:"]
        lines.extend(f"  {name}: {count} 条" for name, count in stats["members"].items())
        lines.append("证券:")
        lines.extend(f"  {ticker}: {count} 条" for ticker, count in list(stats["tickers"].items())[:20])
        return "\n".join(lines)
    title = "交易申报"
    if command == "member":
        title = f"议员交易申报 · {value or '筛选结果'}"
    elif command == "ticker":
        title = f"证券交易申报 · {value or '筛选结果'}"
    lines = [title, f"共 {len(rows)} 条", ""]
    for item in rows:
        lines.append(f"{item.get('transaction_date', '-')} | {item.get('member_name', item.get('member_id', '-'))} | {item.get('ticker', '-')} | {item.get('transaction_code', '-')} | {item.get('asset_type', '-')} | {item.get('amount_range', '-')} | 报告 {item.get('report_id', '-')}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "ocr":
            pages = [int(item) for item in args.pages.split(",")] if args.pages else None
            result = ocr_pdf(args.pdf, page_numbers=pages, dpi=args.dpi)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            else:
                print(f"OCR 完成: {result['source_file']} | 页面 {len(result['pages'])}/{result['page_count']}")
                for page in result["pages"]:
                    print(f"  第 {page.get('page')} 页 | 置信度 {page.get('average_probability') or '未知'} | {'缓存' if page.get('cached') else '新识别'}")
            return 0
        if args.command == "ocr-check":
            try:
                payload = json.loads(args.ocr_json.read_text(encoding="utf-8"))
            except FileNotFoundError as exc:
                raise OCRError(f"OCR JSON not found: {args.ocr_json}") from exc
            except json.JSONDecodeError as exc:
                raise OCRError(f"invalid OCR JSON: {args.ocr_json}: {exc}") from exc
            if not isinstance(payload, dict):
                raise OCRError("OCR JSON must be an object")
            result = assess_ocr_document(payload, low_probability=args.low_probability, review_probability=args.review_probability)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            else:
                state = "需要复核" if result["review_required"] else "通过"
                print(f"OCR 质检: {state} | 页面 {len(result['pages'])}/{result['page_count']}")
                for page in result["pages"]:
                    issues = ", ".join(page["issues"]) or "-"
                    print(f"  第 {page.get('page') or '-'} 页 | 置信度 {page.get('average_probability') or '未知'} | 文本块 {page['word_block_count']} | 问题 {issues}")
            return 0
        if args.command == "ocr-parse":
            try:
                payload = json.loads(args.ocr_json.read_text(encoding="utf-8"))
            except FileNotFoundError as exc:
                raise OCRError(f"OCR JSON not found: {args.ocr_json}") from exc
            except json.JSONDecodeError as exc:
                raise OCRError(f"invalid OCR JSON: {args.ocr_json}: {exc}") from exc
            if not isinstance(payload, dict):
                raise OCRError("OCR JSON must be an object")
            result = parse_and_validate_document(payload, minimum_probability=args.minimum_probability)
            if args.review_output:
                args.review_output.parent.mkdir(parents=True, exist_ok=True)
                review_payload = {
                    "source_file": result.get("source_file") or str(args.ocr_json),
                    "source_sha256": result.get("source_sha256"),
                    "candidates": [item for page in result.get("pages", []) for item in page.get("candidates", [])],
                    "review_queue": result["review_queue"],
                }
                args.review_output.write_text(json.dumps(review_payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            else:
                print(f"OCR 候选解析: 候选 {len(result['review_queue']) + len(result['validated_candidates'])} 条 | 待复核 {len(result['review_queue'])} 条 | 可入 curated {len(result['validated_candidates'])} 条")
                for item in result["review_queue"]:
                    print(f"  第 {item.get('page') or '-'} 页 y={item.get('row_y')} | {item.get('asset_name') or '未知资产'} | 问题: {', '.join(item['issues'])}")
            return 0
        if args.command == "house-index":
            rows = read_house_index(args.index_file, filing_type=args.filing_type, member=args.member)
            result = summarize_house_index(rows)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            else:
                print(f"House Clerk PTR 索引: {result['ptr_count']} 条 | 申报日 {result['date_range']['from'] or '-'} 至 {result['date_range']['to'] or '-'}")
                for row in rows[:30]:
                    print(f"{row['filing_date']} | {row['first_name']} {row['last_name']} | {row['district']} | 文档 {row['document_id']}")
                if len(rows) > 30:
                    print(f"... 其余 {len(rows) - 30} 条请使用 --json")
            return 0
        if args.command == "ocr-review":
            try:
                review_payload = json.loads(args.review_json.read_text(encoding="utf-8"))
            except FileNotFoundError as exc:
                raise OCRError(f"review JSON not found: {args.review_json}") from exc
            except json.JSONDecodeError as exc:
                raise OCRError(f"invalid review JSON: {args.review_json}: {exc}") from exc
            if not isinstance(review_payload, dict):
                raise OCRError("review JSON must be an object")
            if not args.decisions:
                template = review_template(review_payload)
                if args.template_output:
                    args.template_output.parent.mkdir(parents=True, exist_ok=True)
                    args.template_output.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
                print(json.dumps(template, ensure_ascii=False, indent=2))
                return 0
            try:
                decisions_payload = json.loads(args.decisions.read_text(encoding="utf-8"))
            except FileNotFoundError as exc:
                raise OCRError(f"decisions JSON not found: {args.decisions}") from exc
            except json.JSONDecodeError as exc:
                raise OCRError(f"invalid decisions JSON: {args.decisions}: {exc}") from exc
            defaults = {key: value for key, value in {
                "member_id": args.member_id, "member_name": args.member_name,
                "district": args.district, "report_id": args.report_id,
                "filing_date": args.filing_date,
            }.items() if value}
            result = apply_review_decisions(review_payload, decisions_payload, defaults=defaults)
            if args.output:
                if args.output.exists():
                    raise OCRError(f"refusing to overwrite existing output: {args.output}")
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({key: result[key] for key in ("promoted_count", "errors", "source")}, ensure_ascii=False, indent=2))
            return 0
        if args.command == "house-download":
            result = download_ptr(args.document_id, args.year, output_dir=args.output_dir, url_template=args.url_template or "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{document_id}.pdf")
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"已下载 PTR {result['document_id']} | {result['bytes']} bytes | SHA-256 {result['sha256']} | {result['path']}")
            return 0
        if args.command == "sync":
            index_file = args.index_file or Path("sources/providers/house-clerk") / args.year / f"{args.year}FD.zip"
            pages = [int(item) for item in args.pages.split(",")] if args.pages else None
            result = sync_house_ptrs(index_file, output_root=args.output_root, member=args.member, limit=args.limit, download=args.download, ocr=args.ocr, pages=pages, dpi=args.dpi)
            manifest = args.manifest or Path("data/derived/congressional-monitor/sync") / f"{args.year}.json"
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            else:
                print(f"同步完成: {result['requested_count']} 条 | " + " · ".join(f"{key} {value}" for key, value in sorted(result["counts"].items())))
                print(f"清单: {manifest}")
            return 0
        if args.command == "senate-efd":
            rows = read_senate_efd(args.efd_file, member=args.member)
            result = summarize_senate_efd(rows)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            else:
                print(f"Senate eFD: {result['trade_count']} 条 | 议员 {result['member_count']} | 交易日 {result['date_range']['from'] or '-'} 至 {result['date_range']['to'] or '-'}")
                for row in rows[:30]:
                    print(f"{row['transaction_date'] or '-'} | {row['member_name'] or row['member_id'] or '-'} | {row['ticker'] or row['asset_name'] or '-'} | {row['transaction_code'] or '-'} | {row['amount_range'] or '-'}")
            return 0
        dataset = load_dataset(args.data_dir, args.data_file, getattr(args, "senate_file", []))
        if args.command == "cross-report":
            result = cross_chamber_report(dataset["trades"], from_date=args.from_date, to_date=args.to_date, limit=args.limit)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            else:
                print(f"两院交易报告: {result['trade_count']} 条 | 交易日 {result['date_range']['from'] or '-'} 至 {result['date_range']['to'] or '-'}")
                for chamber, item in result["chambers"].items():
                    print(f"{chamber}: {item['trade_count']} 条 / {item['member_count']} 名议员")
                print("共同涉及证券: " + (", ".join(item["ticker"] for item in result["joint_tickers"]) or "-") )
                for item in result["recent_trades"][:10]:
                    print(f"{item['transaction_date'] or '-'} | {item['chamber']} | {item['member_name'] or item['member_id']} | {item['ticker'] or '-'} | {item['transaction_code'] or '-'}")
            return 0
        member = args.member
        ticker = args.ticker
        if args.command == "member":
            member = args.value or member
        elif args.command == "ticker":
            ticker = args.value or ticker
        rows = filter_trades(dataset["trades"], member=member, ticker=ticker, from_date=args.from_date, to_date=args.to_date, direction=args.direction, asset_type=args.asset_type)
        positions = infer_positions(rows) if args.command in {"positions", "report"} else []
        if args.json:
            if args.command == "coverage":
                output = {"query": vars(args), "coverage": coverage(dataset)}
            elif args.command == "check":
                output = {"query": vars(args), "quality": validate_dataset(dataset)}
            else:
                output = {"query": vars(args), "summary": summarize(rows), "trades": rows}
            if args.command in {"positions", "report"}:
                output["positions"] = positions
            if args.command == "report":
                output["quality"] = validate_dataset(dataset)
                output["coverage"] = coverage(dataset)
            print(json.dumps(output, ensure_ascii=False, indent=2, default=str))
        else:
            if args.command == "coverage":
                cov = coverage(dataset)
                print(f"数据覆盖\n议员: {cov['member_count']} | 交易申报: {cov['trade_count']} | 交易日: {cov['date_range']['from'] or '-'} 至 {cov['date_range']['to'] or '-'}\n报告: " + ", ".join(item["report_id"] for item in cov["reports"]))
            elif args.command == "check":
                quality = validate_dataset(dataset)
                print(json.dumps(quality, ensure_ascii=False, indent=2))
            elif args.command in {"positions", "report"}:
                if args.command == "report":
                    print(f"议员交易分析报告 · {args.value or args.member or '筛选范围'}\n交易申报: {len(rows)} 条 | 净变动组合: {len(positions)} 个\n")
                lines = ["已披露持仓净变动估计", f"共 {len(positions)} 个议员-证券-资产组合", ""]
                lines.extend(f"{item['member_name']} | {item['ticker']} | {item['asset_type']} | 净变动 {item['known_net_quantity_change'] if item['known_net_quantity_change'] is not None else '未知'} {item.get('quantity_unit') or '单位'} | 已知买入 {item['known_purchase_quantity']} | 已知卖出 {item['known_sale_quantity']} | 未知数量 {item['unknown_quantity_trade_count']} | {item['confidence']}" for item in positions)
                print("\n".join(lines))
            else:
                print(_text_report(args.command, rows, dataset, args.value))
        return 0
    except (FileNotFoundError, ValueError, OCRError) as exc:
        print(f"congressional-monitor: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
