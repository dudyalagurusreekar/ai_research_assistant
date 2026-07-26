"""Comprehensive Unit and Integration Tests for Browser Action Engine.

Validates fill, clear, press_key, select_dropdown, check_checkbox, file_upload, file_download,
full-page and element screenshots, network & console capture, intelligent waiting strategies,
form submission, selector validation, retries, and ActionResult telemetry.
"""

import os
import time
import json
import unittest
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from pathlib import Path

from tools.browser.config import BrowserConfig
from tools.browser.constants import BrowserEngineType
from tools.browser.core.browser import Browser
from tools.browser.tool import BrowserTool
from tools.browser.models.response import ActionResult
from tools.browser.exceptions import ValidationError, UploadError


class LocalHTTPTestServer:
    """Local HTTP Server serving dynamic HTML fixtures for browser automation testing."""

    def __init__(self):
        self.server = None
        self.thread = None
        self.port = 0

    def start(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/download":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/octet-stream")
                    self.send_header("Content-Disposition", 'attachment; filename="sample.txt"')
                    self.end_headers()
                    self.wfile.write(b"Downloaded content sample payload")
                    return

                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()

                html = """<!DOCTYPE html>
<html>
<head>
    <title>Browser Action Engine Test Page</title>
</head>
<body>
    <h1>Browser Action Test Suite</h1>

    <!-- Form & Inputs -->
    <form id="test-form" action="/submitted" method="GET">
        <input type="text" id="username" name="username" value="" />
        <input type="checkbox" id="agree" name="agree" />
        <select id="country" name="country">
            <option value="us">United States</option>
            <option value="ca">Canada</option>
            <option value="uk">United Kingdom</option>
        </select>
        <input type="file" id="file-upload" name="file-upload" />
        <button type="submit" id="submit-btn">Submit Form</button>
    </form>

    <!-- Key & Dynamic Waiting Elements -->
    <input type="text" id="key-target" placeholder="Type here" />
    <div id="key-result"></div>
    <div id="dynamic-target" style="display:none;">Dynamic Element Loaded</div>

    <!-- Download link -->
    <a id="download-link" href="/download">Download File</a>

    <script>
        // Console log emitter
        console.log("TEST_CONSOLE_MESSAGE: Page Loaded Successfully");
        console.error("TEST_CONSOLE_ERROR: Synthetic Console Warning");

        // Keydown listener
        document.getElementById("key-target").addEventListener("keydown", function(e) {
            document.getElementById("key-result").innerText = "Key pressed: " + e.key;
        });

        // Dynamic timer
        setTimeout(function() {
            document.getElementById("dynamic-target").style.display = "block";
            window.dynamicReady = true;
        }, 300);

        // Fetch trigger
        fetch('/download').catch(function(e){});
    </script>
</body>
</html>"""
                self.wfile.write(html.encode("utf-8"))

            def log_message(self, format, *args):
                pass  # Suppress HTTP server output in test logs

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_port
        self.thread = Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()


class TestBrowserActionEngine(unittest.TestCase):
    """Test suite covering all browser actions using Playwright and local HTTP server."""

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
            timeout_seconds=10.0,
            max_retries=1,
        )
        self.browser = Browser(config=self.config)
        self.browser.open_url(self.base_url)

    def tearDown(self):
        self.browser.close()

    def test_fill_and_clear_input(self):
        """Verify fill_input and clear_input with post-action verification."""
        res_fill = self.browser.fill_input("#username", "alice_smith")
        self.assertTrue(res_fill.success)
        self.assertEqual(res_fill.action, "fill_input")
        self.assertIsNotNone(res_fill.verification)
        self.assertTrue(res_fill.verification.get("verified"))
        self.assertEqual(res_fill.verification.get("field_value"), "alice_smith")

        res_clear = self.browser.clear_input("#username")
        self.assertTrue(res_clear.success)
        self.assertEqual(res_clear.action, "clear_input")
        self.assertTrue(res_clear.verification.get("verified"))
        self.assertEqual(res_clear.verification.get("field_value"), "")

    def test_press_key(self):
        """Verify press_key triggers keyboard listener on element."""
        res = self.browser.press_key("#key-target", "Enter")
        self.assertTrue(res.success)
        self.assertEqual(res.action, "press_key")

        text = self.browser.execute_javascript("document.getElementById('key-result').innerText").data
        self.assertEqual(text, "Key pressed: Enter")

    def test_select_dropdown(self):
        """Verify select_dropdown selects option by value or label."""
        res_ca = self.browser.select_dropdown("#country", "ca")
        self.assertTrue(res_ca.success)
        self.assertEqual(res_ca.action, "select_dropdown")
        self.assertEqual(res_ca.verification.get("selected_value"), "ca")

        res_lbl = self.browser.select_dropdown("#country", "label:United Kingdom")
        self.assertTrue(res_lbl.success)
        self.assertEqual(res_lbl.verification.get("selected_value"), "uk")

    def test_check_checkbox(self):
        """Verify check_checkbox sets checked state true/false."""
        res_chk = self.browser.check_checkbox("#agree", checked=True)
        self.assertTrue(res_chk.success)
        self.assertEqual(res_chk.action, "check_checkbox")
        self.assertTrue(res_chk.verification.get("checked"))

        res_unchk = self.browser.check_checkbox("#agree", checked=False)
        self.assertTrue(res_unchk.success)
        self.assertFalse(res_unchk.verification.get("checked"))

    def test_file_upload(self):
        """Verify upload_file attaches local file to input."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"Hello World File Upload Test")
            tmp_path = tmp.name

        try:
            res = self.browser.upload_file("#file-upload", tmp_path)
            self.assertTrue(res.success)
            self.assertEqual(res.action, "upload_file")

            file_name = self.browser.execute_javascript("document.getElementById('file-upload').files[0].name").data
            self.assertEqual(file_name, os.path.basename(tmp_path))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_file_upload_missing_file_error(self):
        """Verify upload_file fails gracefully when target file path does not exist."""
        res = self.browser.upload_file("#file-upload", "non_existent_file_path_12345.txt")
        self.assertFalse(res.success)
        self.assertTrue(any("does not exist" in err for err in res.errors))

    def test_file_download(self):
        """Verify download_file downloads file from trigger link."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            res = self.browser.download_file("#download-link", download_dir=tmp_dir)
            self.assertTrue(res.success)
            self.assertEqual(res.action, "download_file")
            downloaded_path = res.data.get("path")
            self.assertTrue(os.path.exists(downloaded_path))
            self.assertTrue(os.path.getsize(downloaded_path) > 0)

    def test_capture_screenshots(self):
        """Verify full page and target element screenshot capture."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            full_path = os.path.join(tmp_dir, "full.png")
            elem_path = os.path.join(tmp_dir, "elem.png")

            res_full = self.browser.capture_screenshot(path=full_path, full_page=True)
            self.assertTrue(res_full.success)
            self.assertTrue(os.path.exists(full_path))

            res_elem = self.browser.capture_screenshot(path=elem_path, selector="#test-form")
            self.assertTrue(res_elem.success)
            self.assertTrue(os.path.exists(elem_path))

    def test_network_and_console_log_capture(self):
        """Verify interception of console statements and network traffic."""
        res_console = self.browser.capture_console_logs()
        self.assertTrue(res_console.success)
        logs = res_console.data
        self.assertTrue(any("TEST_CONSOLE_MESSAGE" in log.get("text", "") for log in logs))

        res_net = self.browser.capture_network_requests()
        self.assertTrue(res_net.success)
        reqs = res_net.data
        self.assertTrue(isinstance(reqs, list))

    def test_intelligent_waiting_strategies(self):
        """Verify wait_for_selector, wait_for_function, wait_for_url, and wait_for_network_idle."""
        res_sel = self.browser.wait_for_selector("#dynamic-target", state="visible")
        self.assertTrue(res_sel.success)

        res_fn = self.browser.wait_for_function("window.dynamicReady === true")
        self.assertTrue(res_fn.success)

        res_url = self.browser.wait_for_url("127.0.0.1")
        self.assertTrue(res_url.success)

        res_net_idle = self.browser.wait_for_network_idle()
        self.assertTrue(res_net_idle.success)

    def test_submit_form(self):
        """Verify submit_form submits form element."""
        self.browser.fill_input("#username", "submit_tester")
        res = self.browser.submit_form("#test-form")
        self.assertTrue(res.success)
        self.assertEqual(res.action, "submit_form")

    def test_selector_validation(self):
        """Verify empty selector raises ValidationError."""
        res = self.browser.click("")
        self.assertFalse(res.success)
        self.assertTrue(any("Selector cannot be empty" in err for err in res.errors))

    def test_browser_tool_wrapper(self):
        """Verify BrowserTool wrapper handles structured actions and returns JSON strings."""
        tool = BrowserTool(browser=self.browser)
        
        # Test fill_input via forward
        raw_json = tool.forward(action="fill_input", selector="#username", text_input="agent_user")
        data = json.loads(raw_json)
        self.assertTrue(data["success"])
        self.assertEqual(data["action"], "fill_input")
        self.assertEqual(data["verification"]["field_value"], "agent_user")

        # Test submit_form via forward
        raw_json_sub = tool.forward(action="submit_form", selector="#test-form")
        data_sub = json.loads(raw_json_sub)
        self.assertTrue(data_sub["success"])
        self.assertEqual(data_sub["action"], "submit_form")

    def test_browser_tool_auto_navigation(self):
        """Verify BrowserTool auto-navigates on content extraction actions if url is provided."""
        tool = BrowserTool(browser=self.browser)
        
        # Test get_clean_text with url
        target_url = f"http://127.0.0.1:{self.server.port}/"
        raw_json = tool.forward(action="get_clean_text", url=target_url)
        data = json.loads(raw_json)
        self.assertTrue(data["success"])
        self.assertEqual(data["action"], "get_clean_text")
        self.assertIn("Browser Action Test Suite", data["data"])

        # Test get_page_title with url
        raw_json_title = tool.forward(action="get_page_title", url=target_url)
        data_title = json.loads(raw_json_title)
        self.assertTrue(data_title["success"])
        self.assertEqual(data_title["action"], "get_page_title")
        self.assertEqual(data_title["data"], "Browser Action Engine Test Page")


if __name__ == "__main__":
    unittest.main()
