import unittest
from datetime import date

from tools.congressional_monitor.behavior import analyze_behavior, render_behavior_markdown
from tools.congressional_monitor.member_priority import rank_member_priorities


def trade(member, ticker, day, code="P", quantity=None, chamber="House"):
    return {
        "id": f"{member}-{ticker}-{day}-{code}",
        "member_id": member,
        "member_name": member.title(),
        "ticker": ticker,
        "issuer": ticker,
        "transaction_date": day,
        "transaction_code": code,
        "asset_type": "ST",
        "quantity": quantity,
        "quantity_unit": "shares" if quantity is not None else None,
        "chamber": chamber,
    }


class BehaviorTests(unittest.TestCase):
    def test_multi_angle_ticker_and_member_metrics(self):
        rows = [
            trade("a", "ABC", "2026-08-01", quantity=10),
            trade("a", "ABC", "2026-08-10", quantity=5),
            trade("b", "ABC", "2026-08-11", quantity=20),
            trade("c", "ABC", "2026-08-12", code="S", quantity=4),
            trade("e", "ABC", "2026-08-13", quantity=7),
            trade("d", "XYZ", "2026-01-01", quantity=2),
        ]
        result = analyze_behavior(rows, windows=(30, 90), top_n=10)
        self.assertEqual(result["quality"]["active_member_count"], 5)
        recent = next(item for item in result["windows"] if item["label"] == "last_30_days")
        abc = next(item for item in recent["tickers"] if item["ticker"] == "ABC")
        self.assertEqual(abc["buy_member_count"], 3)
        self.assertEqual(abc["sell_member_count"], 1)
        self.assertEqual(abc["repeat_buy_member_count"], 1)
        self.assertEqual(abc["known_net_quantity_by_unit"]["shares"], 38)
        self.assertIn("broad_accumulation", abc["signals"])

    def test_full_period_is_opt_in_and_trend_is_returned(self):
        rows = [trade("a", "ABC", "2026-06-20", code="S"), trade("b", "ABC", "2026-08-01")]
        result = analyze_behavior(rows, windows=(30,))
        self.assertEqual([item["label"] for item in result["windows"]], ["last_30_days"])
        self.assertEqual(result["trends"][0]["label"], "30_day_vs_prior_30_days")
        self.assertTrue(result["trends"][0]["changes"])
        with_full = analyze_behavior(rows, windows=(30,), include_full_period=True)
        self.assertEqual(with_full["windows"][-1]["label"], "full_selected_period")

    def test_markdown_renderer_contains_analyst_sections(self):
        result = analyze_behavior([trade("a", "AAPL", "2026-08-01"), trade("b", "AAPL", "2026-08-02")], windows=(30,))
        markdown = render_behavior_markdown(result)
        self.assertIn("# 美国国会议员交易行为监测报告", markdown)
        self.assertIn("## 一、执行摘要", markdown)
        self.assertIn("## 七、数据边界与使用方式", markdown)
        self.assertIn("AAPL", markdown)
        self.assertIn("Apple", markdown)
        self.assertIn("消费电子与软件服务", markdown)
        self.assertIn("近 30 日交易", markdown)
        self.assertNotIn("评分构成（领导/委员会/媒体/活跃/历史）", markdown)

    def test_member_priority_uses_metadata_and_observed_activity(self):
        rows = [
            trade("leader", "ABC", "2026-08-01"),
            trade("leader", "ABC", "2026-08-02"),
            trade("leader", "XYZ", "2026-08-03"),
            trade("quiet", "ABC", "2026-08-04"),
        ]
        profiles = {
            "leader": {
                "leadership_role": "Majority Leader",
                "committee_roles": ["Chair, Financial Services Committee"],
                "media_mentions_90d": 100,
            }
        }
        ranked = rank_member_priorities(rows, profiles=profiles, as_of=date(2026, 8, 4))
        self.assertEqual(ranked[0]["member_id"], "leader")
        self.assertEqual(ranked[0]["priority_level"], "B 重点")
        self.assertEqual(ranked[0]["missing_dimensions"], [])
        self.assertIn("领导职务", ranked[1]["missing_dimensions"])

    def test_behavior_report_includes_automatic_member_priority(self):
        result = analyze_behavior([trade("leader", "ABC", "2026-08-01"), trade("leader", "ABC", "2026-08-02")], windows=(30,), member_profiles={"leader": {"leadership_role": "Speaker"}})
        member = result["windows"][0]["members"][0]
        self.assertEqual(member["member_priority"]["priority_components"]["leadership"], 30.0)

    def test_direction_and_compound_exposure_drive_signal_order(self):
        rows = [
            {**trade("pelosi", "INTC", "2026-08-01", quantity=10000), "asset_type": "ST", "amount_range": "$500,001 - $1,000,000"},
            {**trade("pelosi", "INTC", "2026-08-01", quantity=50), "asset_type": "OP", "amount_range": "$250,001 - $500,000"},
            {**trade("x", "PANW", "2026-08-01", code="P"), "amount_range": "$1,001 - $15,000"},
            {**trade("y", "PANW", "2026-08-01", code="S"), "amount_range": "$1,001 - $15,000"},
            *[{**trade("lth", "LTH", f"2026-08-{day:02d}"), "amount_range": "$1,001 - $15,000"} for day in (1, 2, 3)],
        ]
        result = analyze_behavior(rows, windows=(30,), top_n=10)
        tickers = [item["ticker"] for item in result["windows"][0]["tickers"]]
        self.assertLess(tickers.index("INTC"), tickers.index("PANW"))
        self.assertLess(tickers.index("INTC"), tickers.index("LTH"))


if __name__ == "__main__":
    unittest.main()
