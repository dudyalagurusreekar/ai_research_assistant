"""Unit and Integration Tests for BrowserActionExecutor Middleware.

Validates action normalization, validation, executing commands, state tracking,
and JSON serialization.
"""

import json
import unittest
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

from tools.browser.config import BrowserConfig
from tools.browser.constants import BrowserEngineType
from tools.browser.core.browser import Browser
from tools.browser.executor import BrowserActionExecutor


class LocalHTTPTestServer:
    """Local HTTP Server serving dynamic HTML fixtures for browser executor testing."""

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
    <title>Browser Executor Test Page</title>
</head>
<body>
    <h1>Browser Executor Test</h1>
    <form id="test-form" action="/submitted" method="GET">
        <input type="text" id="username" name="username" value="" />
        <input type="checkbox" id="agree" name="agree" />
        <select id="country" name="country">
            <option value="us">United States</option>
            <option value="ca">Canada</option>
        </select>
        <button type="submit" id="submit-btn">Submit Form</button>
    </form>
    <div id="dynamic-el" style="display:none;">Dynamic content loaded</div>
    <script>
        setTimeout(() => {
            const el = document.getElementById("dynamic-el");
            if (el) el.style.display = "block";
        }, 100);
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


class TestBrowserActionExecutor(unittest.TestCase):
    """Integration tests validating BrowserActionExecutor middleware execution."""

    @classmethod
    def setUpClass(cls):
        cls.server = LocalHTTPTestServer()
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
        self.executor = BrowserActionExecutor(self.browser)

    def tearDown(self):
        self.browser.close()

    def test_invalid_action(self):
        """Verify empty or invalid actions fail gracefully."""
        res_no_action = self.executor.execute({})
        self.assertFalse(res_no_action.success)
        self.assertTrue(any("Action name is required" in err for err in res_no_action.errors))

        res_unknown = self.executor.execute({"action": "unknown_action_99"})
        self.assertFalse(res_unknown.success)
        self.assertTrue(any("Unknown browser action" in err for err in res_unknown.errors))

    def test_selector_validation(self):
        """Verify selector actions validate syntax first."""
        res = self.executor.execute({"action": "click", "selector": ""})
        self.assertFalse(res.success)
        self.assertTrue(any("selector is required" in err for err in res.errors))

        res_malformed = self.executor.execute({"action": "click", "selector": "#username[invalid"})
        self.assertFalse(res_malformed.success)
        self.assertTrue(any("Selector validation failed" in err for err in res_malformed.errors))

    def test_open_url_and_fill_input(self):
        """Verify open_url and fill_input flow."""
        # 1. Open URL
        res_open = self.executor.execute({"action": "open_url", "url": self.base_url})
        self.assertTrue(res_open.success)
        self.assertEqual(res_open.url.rstrip("/"), self.base_url.rstrip("/"))

        # 2. Fill Input
        res_fill = self.executor.execute({
            "action": "fill_input",
            "selector": "#username",
            "text": "test_user_exec"
        })
        self.assertTrue(res_fill.success)
        self.assertEqual(res_fill.verification.get("field_value"), "test_user_exec")
        self.assertTrue(res_fill.metrics.execution_time_ms > 0)

    def test_checkbox_and_dropdown(self):
        """Verify check_checkbox and select_dropdown verifications."""
        self.executor.execute({"action": "open_url", "url": self.base_url})

        # Check Checkbox
        res_chk = self.executor.execute({
            "action": "check_checkbox",
            "selector": "#agree",
            "checked": True
        })
        self.assertTrue(res_chk.success)
        self.assertTrue(res_chk.verification.get("checked"))

        # Select Dropdown
        res_sel = self.executor.execute({
            "action": "select_dropdown",
            "selector": "#country",
            "text": "ca"
        })
        self.assertTrue(res_sel.success)
        self.assertEqual(res_sel.verification.get("selected_value"), "ca")

    def test_wait_for_selector(self):
        """Verify waiting for selector actions works via executor."""
        self.executor.execute({"action": "open_url", "url": self.base_url})

        res_wait = self.executor.execute({
            "action": "wait_for_selector",
            "selector": "#dynamic-el",
            "text": "visible"
        })
        self.assertTrue(res_wait.success)

    def test_execute_to_json(self):
        """Verify action output serialization to JSON."""
        res_json = self.executor.execute_to_json({"action": "open_url", "url": self.base_url})
        data = json.loads(res_json)
        self.assertTrue(data["success"])
        self.assertEqual(data["url"].rstrip("/"), self.base_url.rstrip("/"))
        self.assertIsNotNone(data["metrics"])


if __name__ == "__main__":
    unittest.main()
