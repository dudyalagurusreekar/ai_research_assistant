"""Unit tests for Core Foundation Exception Framework."""

import unittest
from core.exceptions import (
    ErrorCode,
    CoreError,
    ValidationError,
    SessionError,
    CapabilityError,
    RoutingError,
    EventError,
    ConfigError,
    DependencyError,
)


class TestExceptions(unittest.TestCase):
    """Test exception hierarchy and serialization."""

    def test_core_error_properties(self):
        cause = ValueError("Invalid value")
        err = CoreError("Test error", code=ErrorCode.UNKNOWN_ERROR, context={"key": "val"}, cause=cause)

        self.assertEqual(err.message, "Test error")
        self.assertEqual(err.code, ErrorCode.UNKNOWN_ERROR)
        self.assertEqual(err.context, {"key": "val"})
        self.assertEqual(err.cause, cause)
        self.assertIn("ERR_UNKNOWN", str(err))

        d = err.to_dict()
        self.assertEqual(d["error_code"], "ERR_UNKNOWN")
        self.assertEqual(d["message"], "Test error")
        self.assertEqual(d["context"], {"key": "val"})
        self.assertIn("Invalid value", d["cause"])

    def test_derived_exceptions(self):
        v_err = ValidationError("Bad input")
        self.assertEqual(v_err.code, ErrorCode.VALIDATION_ERROR)

        s_err = SessionError("Session failed")
        self.assertEqual(s_err.code, ErrorCode.SESSION_EXECUTION_FAILED)

        c_err = CapabilityError("Capability missing")
        self.assertEqual(c_err.code, ErrorCode.CAPABILITY_INVALID)

        r_err = RoutingError("Route failed")
        self.assertEqual(r_err.code, ErrorCode.ROUTING_FAILED)

        e_err = EventError("Event failed")
        self.assertEqual(e_err.code, ErrorCode.EVENT_DISPATCH_FAILED)

        cfg_err = ConfigError("Config missing")
        self.assertEqual(cfg_err.code, ErrorCode.CONFIG_INVALID)

        dep_err = DependencyError("Dep missing")
        self.assertEqual(dep_err.code, ErrorCode.DEPENDENCY_RESOLUTION_FAILED)


if __name__ == "__main__":
    unittest.main()
