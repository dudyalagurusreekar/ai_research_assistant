"""Unit Tests for LLM and Monitor layers.

Validates stateless LLM JSON cleaning/parsing and BrowserMonitor telemetry/loop detection.
"""

import unittest
from unittest.mock import patch, MagicMock
from tools.browser.llm import LLMClient
from tools.browser.monitor import BrowserMonitor
from tools.browser.browser.events import EventDispatcher, BrowserEvent, BrowserEventType


class TestLLMClient(unittest.TestCase):
    """Tests for LLM client JSON cleaning and generation interface."""

    def test_clean_json_markdown(self):
        client = LLMClient()
        raw_1 = "```json\n{\"action\": \"click\", \"selector\": \"#btn\"}\n```"
        cleaned_1 = client._clean_json_markdown(raw_1)
        self.assertEqual(cleaned_1, "{\"action\": \"click\", \"selector\": \"#btn\"}")

        raw_2 = "```\n{\"action\": \"open_url\"}\n```"
        cleaned_2 = client._clean_json_markdown(raw_2)
        self.assertEqual(cleaned_2, "{\"action\": \"open_url\"}")

    @patch("tools.browser.llm.client.resilient_completion")
    def test_generate_json_success(self, mock_comp):
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = "```json\n{\"action\": \"click\", \"selector\": \"#btn\"}\n```"
        mock_resp.usage.prompt_tokens = 50
        mock_resp.usage.completion_tokens = 15
        mock_resp.usage.total_tokens = 65
        mock_comp.return_value = mock_resp

        client = LLMClient(model="test-model")
        res = client.generate_json(messages=[{"role": "user", "content": "test"}])
        self.assertTrue(res.success)
        self.assertEqual(res.parsed_json, {"action": "click", "selector": "#btn"})
        self.assertEqual(res.total_tokens, 65)
        self.assertEqual(res.model, "test-model")


class TestBrowserMonitor(unittest.TestCase):
    """Tests for Event-driven BrowserMonitor and loop detection."""

    def test_monitor_records_events(self):
        dispatcher = EventDispatcher()
        monitor = BrowserMonitor(dispatcher=dispatcher)

        dispatcher.dispatch(BrowserEvent(BrowserEventType.URL_CHANGED, new_value="https://test.com"))
        dispatcher.dispatch(BrowserEvent(BrowserEventType.DOM_CHANGED, new_value="<html></html>"))
        dispatcher.dispatch(BrowserEvent(BrowserEventType.STATE_ROLLED_BACK, old_value=2, new_value=1))

        self.assertEqual(monitor.stats.events_received, 3)
        self.assertEqual(monitor.stats.url_changes, 1)
        self.assertEqual(monitor.stats.dom_changes, 1)
        self.assertEqual(monitor.stats.rollbacks, 1)

    def test_url_loop_detection(self):
        dispatcher = EventDispatcher()
        monitor = BrowserMonitor(dispatcher=dispatcher, max_loop_threshold=3)

        dispatcher.dispatch(BrowserEvent(BrowserEventType.URL_CHANGED, new_value="https://loop.com"))
        dispatcher.dispatch(BrowserEvent(BrowserEventType.URL_CHANGED, new_value="https://loop.com"))
        self.assertEqual(monitor.stats.loops_detected, 0)

        dispatcher.dispatch(BrowserEvent(BrowserEventType.URL_CHANGED, new_value="https://loop.com"))
        self.assertEqual(monitor.stats.loops_detected, 1)

    def test_action_loop_detection(self):
        monitor = BrowserMonitor(max_loop_threshold=2)
        self.assertFalse(monitor.check_action_loop("click(#btn)"))
        self.assertTrue(monitor.check_action_loop("click(#btn)"))
        self.assertEqual(monitor.stats.loops_detected, 1)


if __name__ == "__main__":
    unittest.main()
