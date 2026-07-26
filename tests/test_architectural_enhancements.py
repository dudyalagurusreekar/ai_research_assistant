"""Unit tests for Architectural Enhancements:
1. ObjectiveTracker
2. ActionVerificationEngine
3. Capability-Based ToolRouter
4. Expanded Performance Metrics in BrowserMonitor
"""

import unittest
from tools.browser.planner import ObjectiveTracker, MilestoneStatus
from tools.browser.verification import ActionVerificationEngine, VerificationType
from tools.router import ToolRouter, ToolCapability
from tools.browser.monitor import BrowserMonitor


class TestObjectiveTracker(unittest.TestCase):
    """Tests for explicit milestone and outcome tracking."""

    def test_milestone_lifecycle(self):
        tracker = ObjectiveTracker(objective="Extract AI definition and download PDF")
        m1 = tracker.add_milestone("definition", "Extract AI definition")
        m2 = tracker.add_milestone("pdf_download", "Download PDF document")

        self.assertFalse(tracker.is_complete())
        self.assertEqual(len(tracker.get_pending_milestones()), 2)

        tracker.mark_achieved("definition", evidence="Artificial Intelligence is...")
        self.assertFalse(tracker.is_complete())
        self.assertEqual(m1.status, MilestoneStatus.ACHIEVED)

        tracker.mark_achieved("pdf_download", evidence="/path/to/ai.pdf")
        self.assertTrue(tracker.is_complete())
        self.assertEqual(len(tracker.get_pending_milestones()), 0)


class TestActionVerificationEngine(unittest.TestCase):
    """Tests for dedicated action verification checks."""

    def test_verify_url(self):
        engine = ActionVerificationEngine()
        res1 = engine.verify_url("wikipedia.org", "https://en.wikipedia.org/wiki/AI")
        self.assertTrue(res1.passed)
        self.assertEqual(res1.verification_type, VerificationType.URL)

        res2 = engine.verify_url("google.com", "https://en.wikipedia.org/wiki/AI")
        self.assertFalse(res2.passed)

    def test_verify_dom_change(self):
        engine = ActionVerificationEngine()
        self.assertTrue(engine.verify_dom_change("hash_1", "hash_2").passed)
        self.assertFalse(engine.verify_dom_change("hash_1", "hash_1").passed)

    def test_verify_element_and_text(self):
        engine = ActionVerificationEngine()
        html = '<div><h1>Artificial Intelligence</h1><button id="search">Search</button></div>'
        self.assertTrue(engine.verify_element_present("#search", html).passed)
        self.assertTrue(engine.verify_text_present("Artificial Intelligence", html).passed)
        self.assertFalse(engine.verify_text_present("Missing text", html).passed)


class TestToolRouter(unittest.TestCase):
    """Tests for capability-based tool routing."""

    def test_router_registration_and_intent(self):
        router = ToolRouter()
        router.register_tool(
            name="browser_tool",
            capability=ToolCapability.BROWSER,
            handler=lambda x: f"browser:{x}",
            description="Browser automation",
        )
        router.register_tool(
            name="file_reader",
            capability=ToolCapability.FILES,
            handler=lambda x: f"file:{x}",
            description="Read local file",
        )

        route_file = router.resolve_intent("read file /path/to/doc.pdf")
        self.assertIsNotNone(route_file)
        self.assertEqual(route_file.capability, ToolCapability.FILES)

        route_browser = router.resolve_intent("open wikipedia.org")
        self.assertIsNotNone(route_browser)
        self.assertEqual(route_browser.capability, ToolCapability.BROWSER)

        res = router.execute_route(route_file, x="doc.pdf")
        self.assertEqual(res, "file:doc.pdf")


class TestExpandedPerformanceMetrics(unittest.TestCase):
    """Tests for expanded telemetry in BrowserMonitor."""

    def test_expanded_metrics_recording(self):
        monitor = BrowserMonitor()
        monitor.record_prompt_tokens(1000, cached=False)
        monitor.record_prompt_tokens(500, cached=True)

        monitor.record_planning_latency(120.0)
        monitor.record_action_latency(45.0)
        monitor.record_verification_latency(10.0)
        monitor.record_failover()

        stats_dict = monitor.get_stats_dict()
        self.assertEqual(stats_dict["average_prompt_size"], 750.0)
        self.assertEqual(stats_dict["cache_hit_rate"], 50.0)
        self.assertEqual(stats_dict["average_planning_latency_ms"], 120.0)
        self.assertEqual(stats_dict["browser_action_latency_ms"], 45.0)
        self.assertEqual(stats_dict["verification_latency_ms"], 10.0)
        self.assertEqual(stats_dict["provider_failover_count"], 1)


if __name__ == "__main__":
    unittest.main()
