"""Unit Tests for Event-Driven Browser State and Event Dispatcher.

Validates that BrowserState acts as the single source of truth and correctly
dispatches granular events when URL, title, DOM, tabs, cookies, storage,
and scroll position change.
"""

import unittest
from tools.browser.browser.events import (
    BrowserEvent,
    BrowserEventType,
    EventDispatcher,
)
from tools.browser.browser.state import BrowserState, BrowserStateSnapshot


class TestEventDispatcher(unittest.TestCase):
    """Tests for EventDispatcher subscription, unsubscription, and dispatching."""

    def test_specific_event_subscription(self):
        dispatcher = EventDispatcher()
        received = []

        def on_url_change(event: BrowserEvent):
            received.append(event)

        dispatcher.subscribe(on_url_change, BrowserEventType.URL_CHANGED)
        dispatcher.dispatch(
            BrowserEvent(
                event_type=BrowserEventType.URL_CHANGED,
                old_value="about:blank",
                new_value="https://example.com",
            )
        )
        dispatcher.dispatch(
            BrowserEvent(
                event_type=BrowserEventType.TITLE_CHANGED,
                old_value="",
                new_value="Example",
            )
        )

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].event_type, BrowserEventType.URL_CHANGED)
        self.assertEqual(received[0].new_value, "https://example.com")

    def test_global_event_subscription(self):
        dispatcher = EventDispatcher()
        received = []

        def on_any_event(event: BrowserEvent):
            received.append(event)

        dispatcher.subscribe(on_any_event, None)
        dispatcher.dispatch(
            BrowserEvent(event_type=BrowserEventType.URL_CHANGED, new_value="u1")
        )
        dispatcher.dispatch(
            BrowserEvent(event_type=BrowserEventType.DOM_CHANGED, new_value="dom1")
        )

        self.assertEqual(len(received), 2)

    def test_unsubscribe(self):
        dispatcher = EventDispatcher()
        received = []

        def listener(event: BrowserEvent):
            received.append(event)

        dispatcher.subscribe(listener, BrowserEventType.URL_CHANGED)
        dispatcher.unsubscribe(listener, BrowserEventType.URL_CHANGED)

        dispatcher.dispatch(
            BrowserEvent(event_type=BrowserEventType.URL_CHANGED, new_value="u1")
        )
        self.assertEqual(len(received), 0)


class TestBrowserState(unittest.TestCase):
    """Tests for Event-Driven BrowserState updates and event emissions."""

    def test_state_mutation_emits_events(self):
        state = BrowserState()
        events = []

        state.subscribe(lambda evt: events.append(evt))

        snap1 = BrowserStateSnapshot(
            version=1,
            timestamp=100.0,
            url="https://test.com",
            title="Test Page",
            dom_snapshot="<html><body>Hello</body></html>",
            tabs=["https://test.com"],
            active_tab_index=0,
            cookies=[{"name": "c1", "value": "v1"}],
            local_storage={"theme": "dark"},
            session_storage={},
            scroll_position={"x": 0, "y": 100},
        )

        state.update_state(snap1)

        event_types = [e.event_type for e in events]
        self.assertIn(BrowserEventType.URL_CHANGED, event_types)
        self.assertIn(BrowserEventType.TITLE_CHANGED, event_types)
        self.assertIn(BrowserEventType.DOM_CHANGED, event_types)
        self.assertIn(BrowserEventType.TABS_CHANGED, event_types)
        self.assertIn(BrowserEventType.COOKIES_CHANGED, event_types)
        self.assertIn(BrowserEventType.STORAGE_CHANGED, event_types)
        self.assertIn(BrowserEventType.SCROLL_CHANGED, event_types)
        self.assertIn(BrowserEventType.STATE_UPDATED, event_types)

        self.assertEqual(state.url, "https://test.com")
        self.assertEqual(state.title, "Test Page")
        self.assertEqual(state.scroll_position, {"x": 0, "y": 100})
        self.assertEqual(state.navigation_history, ["https://test.com"])

    def test_no_event_emitted_when_property_unchanged(self):
        state = BrowserState()
        snap1 = BrowserStateSnapshot(
            version=1,
            timestamp=100.0,
            url="https://test.com",
            title="Test Page",
            dom_snapshot="<html>hello</html>",
        )
        state.update_state(snap1)

        events = []
        state.subscribe(lambda evt: events.append(evt))

        # Update with identical properties (only timestamp changed)
        snap2 = BrowserStateSnapshot(
            version=2,
            timestamp=105.0,
            url="https://test.com",
            title="Test Page",
            dom_snapshot="<html>hello</html>",
        )
        state.update_state(snap2)

        event_types = [e.event_type for e in events]
        self.assertNotIn(BrowserEventType.URL_CHANGED, event_types)
        self.assertNotIn(BrowserEventType.TITLE_CHANGED, event_types)
        self.assertNotIn(BrowserEventType.DOM_CHANGED, event_types)
        self.assertIn(BrowserEventType.STATE_UPDATED, event_types)

    def test_rollback_emits_event(self):
        state = BrowserState()
        snap1 = BrowserStateSnapshot(
            version=1,
            timestamp=100.0,
            url="https://old.com",
            title="Old",
            dom_snapshot="old",
        )
        snap2 = BrowserStateSnapshot(
            version=2,
            timestamp=200.0,
            url="https://new.com",
            title="New",
            dom_snapshot="new",
        )
        state.update_state(snap1)
        state.update_state(snap2)

        events = []
        state.subscribe(lambda evt: events.append(evt))

        state.rollback_state(snap1)

        self.assertEqual(state.url, "https://old.com")
        self.assertEqual(state.version, 1)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, BrowserEventType.STATE_ROLLED_BACK)
        self.assertEqual(events[0].old_value, 2)
        self.assertEqual(events[0].new_value, 1)


class TestBrowserToolFacade(unittest.TestCase):
    """Tests for deterministic BrowserToolFacade execution and automatic event emission."""

    def test_execute_action_triggers_state_sync_and_events(self):
        from unittest.mock import MagicMock
        from tools.browser.models import ActionResult
        from tools.browser.browser.tool import BrowserToolFacade

        mock_browser = MagicMock()
        mock_browser.open_url.return_value = ActionResult(success=True, url="https://mockurl.com", title="Mock Title", data="https://mockurl.com")
        mock_browser.get_current_url.return_value = ActionResult(success=True, url="https://mockurl.com", title="Mock Title", data="https://mockurl.com")
        mock_browser.get_page_title.return_value = ActionResult(success=True, url="https://mockurl.com", title="Mock Title", data="Mock Title")
        mock_browser.get_page_html.return_value = ActionResult(success=True, url="https://mockurl.com", title="Mock Title", data="<html>mock</html>")

        facade = BrowserToolFacade(browser=mock_browser)
        events = []
        facade.state.subscribe(lambda evt: events.append(evt))

        result = facade.execute_action("open_url", url="https://mockurl.com")
        self.assertTrue(result["success"])
        self.assertEqual(result["data"], "https://mockurl.com")
        self.assertEqual(facade.state.url, "https://mockurl.com")
        self.assertEqual(facade.state.title, "Mock Title")

        event_types = [e.event_type for e in events]
        self.assertIn(BrowserEventType.URL_CHANGED, event_types)
        self.assertIn(BrowserEventType.TITLE_CHANGED, event_types)
        self.assertIn(BrowserEventType.DOM_CHANGED, event_types)
        self.assertIn(BrowserEventType.STATE_UPDATED, event_types)


if __name__ == "__main__":
    unittest.main()
