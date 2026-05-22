import unittest

from lottery_sim.dashboard import _dashboard_js


class DashboardTextTests(unittest.TestCase):
    def test_realtime_job_completion_text_is_not_mojibake(self):
        script = _dashboard_js()

        self.assertIn("setActionState(job.status === 'completed' ? '完成' : '失败'", script)
        self.assertIn("`${button.textContent}完成`", script)
        self.assertIn("`${button.textContent}失败`", script)
        self.assertNotIn("瀹屾垚", script)
        self.assertNotIn("澶辫触", script)


if __name__ == "__main__":
    unittest.main()
