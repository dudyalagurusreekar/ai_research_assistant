"""Unit tests for Observability Tracer."""

import unittest
from infrastructure.observability import ObservabilityTracer


class TestObservabilityTracer(unittest.TestCase):
    """Test distributed tracing, timeline logging, and diagnostic report generation."""

    def test_tracer(self):
        tracer = ObservabilityTracer()
        span = tracer.start_span("test_span")
        span.finish()

        tracer.record_event("custom_event", {"detail": "info"})
        tracer.capture_snapshot("step_1", {"state": "active"})

        report = tracer.generate_diagnostic_report()
        self.assertEqual(report["total_spans"], 1)
        self.assertEqual(report["snapshot_count"], 1)
        self.assertIn("trace_id", report)


if __name__ == "__main__":
    unittest.main()
