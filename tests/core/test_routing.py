"""Unit tests for Capability Router."""

import unittest
from core.registry import CapabilityRegistry
from core.routing import CapabilityRouter
from core.models import Request
from tests.core.test_registry import DummyTool


class TestCapabilityRouter(unittest.TestCase):
    """Test router decisions without tool execution."""

    def test_routing_by_explicit_name(self):
        registry = CapabilityRegistry()
        tool1 = DummyTool("search_tool", ["search"])
        registry.register_tool(tool1)

        router = CapabilityRouter(registry)
        req = Request(intent="do something", session_id="s1", parameters={"tool_name": "search_tool"})

        decision = router.route(req)
        self.assertIsNotNone(decision)
        self.assertEqual(decision.tool_name, "search_tool")
        self.assertEqual(decision.confidence, 1.0)

    def test_routing_by_intent(self):
        registry = CapabilityRegistry()
        tool1 = DummyTool("pdf_reader", ["pdf", "documents"])
        registry.register_tool(tool1)

        router = CapabilityRouter(registry)
        req = Request(intent="Extract text from pdf document", session_id="s1")

        decision = router.route(req)
        self.assertIsNotNone(decision)
        self.assertEqual(decision.tool_name, "pdf_reader")
        self.assertGreaterEqual(decision.confidence, 0.85)

    def test_routing_no_match(self):
        registry = CapabilityRegistry()
        router = CapabilityRouter(registry)
        req = Request(intent="unsupported request", session_id="s1")

        decision = router.route(req)
        self.assertIsNone(decision)


if __name__ == "__main__":
    unittest.main()
