"""Unit tests for Browser Metrics Tracker."""

import unittest
from tools.browser.metrics import BrowserMetricsTracker


class TestBrowserMetricsTracker(unittest.TestCase):
    """Test telemetry and action tracking."""

    def test_metrics_tracking(self):
        tracker = BrowserMetricsTracker()
        tracker.record_action("navigate", 150.0, True)
        tracker.record_action("click", 50.0, True)

        summary = tracker.get_metrics_summary()
        self.assertEqual(summary["total_actions"], 2)
        self.assertEqual(summary["average_latencies_ms"]["navigate"], 150.0)


if __name__ == "__main__":
    unittest.main()
