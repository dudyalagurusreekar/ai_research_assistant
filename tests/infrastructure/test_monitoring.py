"""Unit tests for Infrastructure Monitor."""

import unittest
from infrastructure.monitoring import InfrastructureMonitor


class TestInfrastructureMonitor(unittest.TestCase):
    """Test telemetry, token tracking, and tool statistics."""

    def test_monitor_recording(self):
        mon = InfrastructureMonitor()
        mon.record_tokens(100, 50)
        self.assertEqual(mon.total_tokens, 150)

        mon.record_tool_execution("browser_tool", 120.0, success=True)
        mon.record_tool_execution("browser_tool", 80.0, success=False)

        summary = mon.get_summary()
        self.assertEqual(summary["tool_calls"]["browser_tool"], 2)
        self.assertEqual(summary["avg_tool_latencies_ms"]["browser_tool"], 100.0)
        self.assertEqual(summary["counters"]["tool_error.browser_tool"], 1)


if __name__ == "__main__":
    unittest.main()
