"""Unit and Integration Tests for BrowserStateMemoryManager.

Validates immutable snapshots capturing, Local/Session Storage extraction,
scroll position mapping, focused element tracking, state diffing,
history serialization, and rollback restoration.
"""

import unittest
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

from tools.browser.config import BrowserConfig
from tools.browser.constants import BrowserEngineType
from tools.browser.core.browser import Browser
from tools.browser.state_manager import BrowserStateMemoryManager, BrowserStateSnapshot


class LocalStateTestServer:
    """Local HTTP Server serving dynamic HTML fixtures for state manager testing."""

    def __init__(self):
        self.server = None
        self.thread = None
        self.port = 0

    def start(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()

                html = """<!DOCTYPE html>
<html>
<head>
    <title>State Manager Test Page</title>
</head>
<body>
    <h1>State Manager Test</h1>
    <input type="text" id="focus-target" value="focused text" />
    <form id="state-form">
        <input type="text" id="username" name="username" value="user_value" />
    </form>
    <script>
        // Set local storage and session storage
        window.localStorage.setItem("theme", "dark");
        window.localStorage.setItem("user_id", "12345");
        window.sessionStorage.setItem("session_token", "abc-xyz");
    </script>
</body>
</html>"""
                self.wfile.write(html.encode("utf-8"))

            def log_message(self, format, *args):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_port
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()


class TestBrowserStateMemoryManager(unittest.TestCase):
    """Integration and Unit tests for BrowserStateMemoryManager."""

    @classmethod
    def setUpClass(cls):
        cls.server = LocalStateTestServer()
        cls.server.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def setUp(self):
        self.config = BrowserConfig(
            engine_type=BrowserEngineType.PLAYWRIGHT,
            headless=True,
            timeout_seconds=5.0,
            max_retries=0,
        )
        self.browser = Browser(config=self.config)
        self.manager = BrowserStateMemoryManager(self.browser)

    def tearDown(self):
        self.browser.close()

    def test_snapshot_to_and_from_dict(self):
        """Verify snapshot dictionary serialization/deserialization."""
        snap = BrowserStateSnapshot(
            version=3,
            timestamp=1234567.89,
            url="http://example.com",
            title="Example Title",
            dom_snapshot="<html></html>",
            tabs=["http://example.com"],
            active_tab_index=0,
            cookies=[{"name": "test_cookie", "value": "val"}],
            local_storage={"theme": "light"},
            session_storage={"token": "secret"},
            scroll_position={"x": 10, "y": 100},
            focused_element_selector="#input",
            detected_forms=[{"id": "login-form", "action": "/login", "inputs": []}],
            previous_action={"action": "click", "selector": "#btn"}
        )

        d = snap.to_dict()
        self.assertEqual(d["version"], 3)
        self.assertEqual(d["url"], "http://example.com")
        self.assertEqual(d["local_storage"]["theme"], "light")

        snap_re = BrowserStateSnapshot.from_dict(d)
        self.assertEqual(snap_re.version, 3)
        self.assertEqual(snap_re.url, "http://example.com")
        self.assertEqual(snap_re.session_storage["token"], "secret")

    def test_state_capture(self):
        """Verify state manager captures state from live page correctly."""
        self.browser.open_url(self.base_url)

        # Focus element to check focus tracking
        self.browser.click("#focus-target")

        # Capture State
        snap = self.manager.capture_state(previous_action={"action": "open_url"})
        
        self.assertEqual(snap.version, 0)
        self.assertEqual(snap.url.rstrip("/"), self.base_url.rstrip("/"))
        self.assertEqual(snap.title, "State Manager Test Page")
        self.assertIn("State Manager Test", snap.dom_snapshot)
        
        # Verify LocalStorage & SessionStorage
        self.assertEqual(snap.local_storage.get("theme"), "dark")
        self.assertEqual(snap.local_storage.get("user_id"), "12345")
        self.assertEqual(snap.session_storage.get("session_token"), "abc-xyz")
        
        # Verify Focused element
        self.assertEqual(snap.focused_element_selector, "#focus-target")

        # Verify Form detection
        self.assertTrue(len(snap.detected_forms) >= 1)
        self.assertEqual(snap.detected_forms[0]["id"], "state-form")

    def test_diff_snapshots(self):
        """Verify snapshot diffing logic reports accurate structural changes."""
        self.browser.open_url(self.base_url)
        
        snap0 = self.manager.capture_state()

        # Modify LocalStorage
        self.browser.execute_javascript("window.localStorage.setItem('theme', 'light'); window.localStorage.removeItem('user_id');")
        
        snap1 = self.manager.capture_state()

        diff = self.manager.diff_snapshots(snap0, snap1)
        
        self.assertFalse(diff["url_changed"])
        self.assertIn("theme", diff["local_storage"]["changed"])
        self.assertIn("user_id", diff["local_storage"]["removed"])

    def test_rollback_to(self):
        """Verify state rollback restores cookies, storage, and navigation."""
        self.browser.open_url(self.base_url)

        # Phase 1: Set theme=dark, capture version 0
        self.manager.capture_state()

        # Phase 2: Set theme=blue, capture version 1
        self.browser.execute_javascript("window.localStorage.setItem('theme', 'blue');")
        snap1 = self.manager.capture_state()
        self.assertEqual(snap1.local_storage.get("theme"), "blue")

        # Phase 3: Rollback to 0
        restored = self.manager.rollback_to(0)
        self.assertEqual(restored.version, 0)

        # Capture live state to confirm local storage was restored
        snap2 = self.manager.capture_state()
        self.assertEqual(snap2.local_storage.get("theme"), "dark")

    def test_serialization(self):
        """Verify history serialization and deserialization."""
        self.browser.open_url(self.base_url)
        self.manager.capture_state()
        
        serialized = self.manager.serialize_history()
        
        new_manager = BrowserStateMemoryManager(self.browser)
        new_manager.deserialize_history(serialized)
        
        self.assertEqual(new_manager.current_version, self.manager.current_version)
        self.assertEqual(len(new_manager.history), 1)
        self.assertEqual(new_manager.history[0].url.rstrip("/"), self.base_url.rstrip("/"))


if __name__ == "__main__":
    unittest.main()
