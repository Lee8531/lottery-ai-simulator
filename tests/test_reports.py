import unittest

from lottery_sim.analysis.stability import SegmentMetric, SeedSensitivity
from lottery_sim.models import BacktestResult
from lottery_sim.reports.compare_report import render_compare_report
from lottery_sim.reports.stability_report import render_stability_report
from lottery_sim.reports.text_report import render_backtest_report


class ReportRenderingTests(unittest.TestCase):
    def test_backtest_report_contains_dashboard_metrics(self):
        result = BacktestResult(
            game_name="测试彩种",
            total_draws=12,
            total_bets=10,
            total_cost=20,
            total_payout=5,
            hit_distribution={"未中奖": 9, "三等奖": 1},
            bet_results=(),
        )

        report = render_backtest_report(result, strategy_name="测试策略")

        self.assertIn("策略：测试策略", report)
        self.assertIn("回测期数：12", report)
        self.assertIn("投注注数：10", report)
        self.assertIn("中奖金额：5", report)
        self.assertIn("返奖率：25.00%", report)

    def test_compare_report_renders_strategy_rows(self):
        result = BacktestResult(
            game_name="测试彩种",
            total_draws=1,
            total_bets=1,
            total_cost=2,
            total_payout=4,
            hit_distribution={"命中": 1},
            bet_results=(),
        )

        report = render_compare_report([("策略A", result)])

        self.assertIn("策略 | 回测期数 | 投注注数 | 投入金额 | 中奖金额 | 返奖率 | 中奖注数", report)
        self.assertIn("策略A | 1 | 1 | 2 | 4 | 200.00% | 1", report)

    def test_stability_report_renders_seed_and_segment_sections(self):
        report = render_stability_report(
            SeedSensitivity(
                seed_count=2,
                average_roi=0.5,
                min_roi=0.25,
                max_roi=0.75,
                average_direct_hits=1.5,
            ),
            [
                (
                    "热号策略",
                    SegmentMetric("总体", 10, 20, 5, 1),
                    [SegmentMetric("2026", 3, 6, 2, 1)],
                )
            ],
            game_label="测试彩种",
        )

        self.assertIn("测试彩种策略稳定性报告", report)
        self.assertIn("随机种子数量：2", report)
        self.assertIn("热号策略", report)
        self.assertIn("2026 | 3 | 6 | 2 | 33.33% | 1", report)


if __name__ == "__main__":
    unittest.main()
