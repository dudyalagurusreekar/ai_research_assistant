"""Unit tests for Structured Logging."""

import unittest
from infrastructure.logging import StructuredLogger


class TestStructuredLogger(unittest.TestCase):
    """Test structured logger binding and formatting."""

    def test_logger_context(self):
        logger = StructuredLogger("test_logger")
        logger.set_context(session_id="sess_1", trace_id="trace_1", correlation_id="corr_1")

        self.assertEqual(logger._session_id, "sess_1")
        self.assertEqual(logger._trace_id, "trace_1")
        self.assertEqual(logger._correlation_id, "corr_1")

        # Ensure logging calls execute cleanly
        logger.info("Test info message", extra_fields={"foo": "bar"})
        logger.error("Test error message")


if __name__ == "__main__":
    unittest.main()
