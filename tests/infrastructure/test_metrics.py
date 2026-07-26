"""Unit tests for Metrics Engine."""

import unittest
from infrastructure.metrics import MetricsEngine


class TestMetricsEngine(unittest.TestCase):
    """Test cost calculation and metrics report generation."""

    def test_metrics_cost_and_report(self):
        engine = MetricsEngine()
        cost = engine.calculate_cost(1000, 1000)
        self.assertAlmostEqual(cost, 0.002, places=4)

        engine.monitor.record_tokens(2000, 1000)
        report = engine.get_metrics_report()
        self.assertEqual(report["total_tokens"], 3000)
        self.assertIn("estimated_llm_cost_usd", report)


if __name__ == "__main__":
    unittest.main()
