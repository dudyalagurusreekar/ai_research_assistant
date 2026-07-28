"""Unit and Integration Tests for Browser Automation Engine and Playwright Strategy.

Covers Strategy Pattern instantiation, Command Pattern actions, Facade operations,
network interception, session persistence, dialog alerts, screenshots, downloads,
and full lifecycle resource management.
"""

import os
import unittest
import asyncio
import tempfile
import json
from pathlib import Path

from tools.browser.config import BrowserConfig
from tools.browser.constants import BrowserEngineType, BrowserAction
from tools.browser.exceptions import UnsupportedEngineError
from tools.browser.automation.factory import AutomationStrategyFactory, MockAutomationStrategy
from tools.browser.automation.engine import BrowserAutomationEngine
from tools.browser.automation.commands import ClickCommand, CommandRunner
from tools.browser.automation.models import SessionState, NetworkRequestLog, NetworkResponseLog, DialogLog
from tools.browser.automation.observer import NetworkObserver
from tools.browser.core.browser import Browser
from tools.browser.models.request import ActionParams


class TestBrowserAutomationFoundation(unittest.TestCase):
    """Unit tests covering Strategy registry, commands, observers, and mock strategies."""

    def setUp(self) -> None:
        self.config = BrowserConfig(engine_type=BrowserEngineType.MOCK)

    def test_strategy_factory_mock(self):
        """Verify Strategy factory resolves MOCK engine correctly."""
        strategy = AutomationStrategyFactory.create_strategy(BrowserEngineType.MOCK, self.config)
        self.assertIsInstance(strategy, MockAutomationStrategy)

    def test_strategy_factory_selenium_stub(self):
        """Verify Strategy factory throws expected exception for unimplemented Selenium stub."""
        with self.assertRaises(UnsupportedEngineError):
            AutomationStrategyFactory.create_strategy(BrowserEngineType.SELENIUM, self.config)

    def test_command_instantiation_and_execution(self):
        """Verify browser commands encapsulate action details and run via CommandRunner."""
        strategy = MockAutomationStrategy(self.config)
        runner = CommandRunner()

        click_cmd = ClickCommand(selector="#btn", timeout=1.0)
        self.assertEqual(click_cmd.selector, "#btn")
        self.assertEqual(click_cmd.timeout, 1.0)

        # Run against mock strategy
        loop = asyncio.new_event_loop()
        try:
            res = loop.run_until_complete(runner.run(click_cmd, strategy))
            self.assertTrue(res)
        finally:
            loop.close()

    def test_network_observer_logging(self):
        """Verify NetworkObserver records requests, responses, console logs, and errors."""
        observer = NetworkObserver()
        observer.record_request(NetworkRequestLog(url="https://api.org/v1", method="POST"))
        observer.record_response(NetworkResponseLog(url="https://api.org/v1", status=201))
        observer.record_dialog(DialogLog(type="alert", message="Welcome User", action_taken="accepted"))
        observer.record_console(type_="log", text="Hello from JS console")
        observer.record_page_error("Uncaught ReferenceError: x is not defined")

        summary = observer.get_summary()
        self.assertEqual(summary["request_count"], 1)
        self.assertEqual(summary["response_count"], 1)
        self.assertEqual(summary["dialog_count"], 1)
        self.assertEqual(summary["console_count"], 1)
        self.assertEqual(summary["error_count"], 1)

        observer.clear()
        self.assertEqual(observer.get_summary()["request_count"], 0)


class TestBrowserAutomationEngineFacade(unittest.TestCase):
    """Tests covering the high-level BrowserAutomationEngine facade using the Mock Strategy."""

    def setUp(self) -> None:
        self.config = BrowserConfig(engine_type=BrowserEngineType.MOCK)
        self.engine = BrowserAutomationEngine(self.config)

    def tearDown(self) -> None:
        self.engine.close()

    def test_facade_navigation(self):
        """Verify open_page and navigate operations."""
        res = self.engine.open_page("https://example-spa.com")
        self.assertTrue(res["success"])
        self.assertEqual(res["url"], "https://example-spa.com")

    def test_facade_element_interactions(self):
        """Verify click, fill_form, scroll, and JavaScript execution."""
        self.assertTrue(self.engine.click("#button"))
        self.assertTrue(self.engine.fill_form({"#user": "admin", "#pass": "secret"}, submit_selector="#submit"))
        self.assertTrue(self.engine.scroll_to("down", amount=300))
        self.assertEqual(self.engine.execute_script("return 1 + 1;"), "mock_js_result")

    def test_facade_session_persistence(self):
        """Verify exporting and importing authentication sessions."""
        self.engine._run_sync(self.engine.strategy.set_cookies([{"name": "session_id", "value": "xyz123"}]))
        state = self.engine.export_session()
        self.assertEqual(len(state.cookies), 1)
        self.assertEqual(state.cookies[0]["value"], "xyz123")


class TestPlaywrightStrategyIntegration(unittest.TestCase):
    """Integration tests running a real headless Playwright Chromium instance against a local HTML page."""

    def setUp(self) -> None:
        self.config = BrowserConfig(engine_type=BrowserEngineType.PLAYWRIGHT, headless=True)
        self.engine = BrowserAutomationEngine(self.config)

        # Create a local test HTML file with various inputs, interactive buttons, scripts, and scrollable container
        self.temp_html = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
        self.html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Playwright Automation Test Page</title>
            <style>
                #scrollable {
                    height: 100px;
                    overflow-y: scroll;
                    border: 1px solid black;
                }
                .spacer { height: 1000px; }
            </style>
        </head>
        <body>
            <h1>Dynamic DOM Automation Demo</h1>
            
            <button id="btn-click" onclick="document.getElementById('status').innerText = 'Clicked Successfully!'">Click Me</button>
            <p id="status">Idle</p>

            <form id="test-form" onsubmit="event.preventDefault(); document.getElementById('form-status').innerText = 'Submitted: ' + document.getElementById('username').value;">
                <input type="text" id="username" name="username" placeholder="Username" />
                <select id="role">
                    <option value="user">User</option>
                    <option value="admin">Administrator</option>
                </select>
                <button type="submit" id="btn-submit">Submit Form</button>
            </form>
            <p id="form-status">Unsubmitted</p>

            <div id="scrollable">
                <p>Line 1</p><p>Line 2</p><p>Line 3</p><p>Line 4</p><p>Line 5</p>
                <p>Line 6</p><p>Line 7</p><p>Line 8</p><p>Line 9</p><p>Line 10</p>
            </div>

            <button id="btn-alert" onclick="alert('JS Dialog Alert!')">Alert</button>

            <div class="spacer"></div>
            <p id="bottom-marker">At the bottom</p>

            <script>
                console.log('Page loaded completely');
            </script>
        </body>
        </html>
        """
        self.temp_html.write(self.html_content)
        self.temp_html.close()
        self.test_url = f"file:///{Path(self.temp_html.name).as_posix()}"

    def tearDown(self) -> None:
        self.engine.close()
        if os.path.exists(self.temp_html.name):
            os.remove(self.temp_html.name)

    def test_playwright_full_interaction_flow(self):
        """Execute navigation, clicks, form fills, selects, scrolls, JS execution, dialog alerts, and screenshots."""
        # 1. Navigation
        res = self.engine.open_page(self.test_url)
        self.assertTrue(res["success"])
        self.assertEqual(res["title"], "Playwright Automation Test Page")

        # 2. Click Button & Verify DOM State Change
        click_success = self.engine.click("#btn-click")
        self.assertTrue(click_success)
        
        # Verify text change via evaluate_script
        status_text = self.engine.execute_script("document.getElementById('status').innerText")
        self.assertEqual(status_text, "Clicked Successfully!")

        # 3. Form Fill & Select Dropdown & Submit Form
        self.engine.fill_form(
            {"#username": "Alice"},
            submit_selector="#btn-submit"
        )
        form_status = self.engine.execute_script("document.getElementById('form-status').innerText")
        self.assertEqual(form_status, "Submitted: Alice")

        # Select option from dropdown
        self.engine.select_option("#role", "admin")
        selected_role = self.engine.execute_script("document.getElementById('role').value")
        self.assertEqual(selected_role, "admin")

        # 4. Scroll page
        scroll_success = self.engine.scroll_to(direction="bottom")
        self.assertTrue(scroll_success)

        # 5. JS Alerts Handling (observer verification)
        self.engine.click("#btn-alert")
        logs = self.engine.capture_network()
        self.assertTrue(any(d.type == "alert" and "JS Dialog Alert!" in d.message for d in logs["dialogs"]))

        # 6. Capture Screenshots
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = os.path.join(tmpdir, "screenshot.png")
            img_bytes = self.engine.take_screenshot(path=img_path, full_page=True)
            self.assertTrue(os.path.exists(img_path))
            self.assertGreater(len(img_bytes), 0)

        # 7. Session cookies verification
        cookies = self.engine.export_session()
        self.assertIsInstance(cookies, SessionState)


class TestBrowserIntegrationWithAutomation(unittest.TestCase):
    """Tests checking integration of Browser automation actions into the core Browser orchestrator class."""

    def setUp(self) -> None:
        self.config = BrowserConfig(engine_type=BrowserEngineType.MOCK)
        self.browser = Browser(self.config)

    def tearDown(self) -> None:
        self.browser.close()

    def test_browser_facade_action_delegation(self):
        """Verify Browser.execute_action delegates dynamically to automation engine."""
        action_params = ActionParams(
            action=BrowserAction.CLICK,
            selector="#btn-submit"
        )
        resp = self.browser.execute_action(action_params)
        # Note: since it is a mock strategy, get_url() returns current_url which defaults to about:blank
        self.assertEqual(resp.url, "about:blank")
        self.assertEqual(resp.status_code, 200)

        # Confirm convenience facades exist
        self.assertTrue(hasattr(self.browser, "click"))
        self.assertTrue(hasattr(self.browser, "fill_form"))
        self.assertTrue(hasattr(self.browser, "take_screenshot"))

    def test_browser_first_class_sdk_apis(self):
        """Verify the 22 first-class Action Engine SDK APIs return structured ActionResult objects."""
        # 1. open_url
        res = self.browser.open_url("https://test.local")
        self.assertTrue(res.success)
        self.assertEqual(res.url, "https://test.local")
        self.assertEqual(res.title, "Mock Title")
        self.assertIsNotNone(res.metrics)
        self.assertGreaterEqual(res.metrics.execution_time_ms, 0)

        # 2. click
        self.assertTrue(self.browser.click("#selector").success)
        # 3. double_click
        self.assertTrue(self.browser.double_click("#selector").success)
        # 4. hover
        self.assertTrue(self.browser.hover("#selector").success)
        # 5. fill_input
        self.assertTrue(self.browser.fill_input("#selector", "text").success)
        # 6. clear_input
        self.assertTrue(self.browser.clear_input("#selector").success)
        # 7. press_key
        self.assertTrue(self.browser.press_key("#selector", "Enter").success)
        # 8. select_dropdown
        self.assertTrue(self.browser.select_dropdown("#selector", "option_val").success)
        # 9. check_checkbox
        self.assertTrue(self.browser.check_checkbox("#selector", checked=True).success)
        # 10. upload_file
        self.assertTrue(self.browser.upload_file("#selector", "file.txt").success)
        # 11. download_file
        res_dl = self.browser.download_file("#selector")
        self.assertTrue(res_dl.success)
        dl_path = res_dl.data["path"] if isinstance(res_dl.data, dict) else res_dl.data
        self.assertEqual(dl_path, "/tmp/mock_download.txt")
        # 12. wait_for_selector
        self.assertTrue(self.browser.wait_for_selector("#selector").success)
        # 13. wait_for_navigation
        self.assertTrue(self.browser.wait_for_navigation().success)
        # 14. scroll_page
        self.assertTrue(self.browser.scroll_page(direction="down").success)
        # 15. execute_javascript
        res_js = self.browser.execute_javascript("console.log('test')")
        self.assertTrue(res_js.success)
        self.assertEqual(res_js.data, "mock_js_result")
        # 16. capture_screenshot
        res_ss = self.browser.capture_screenshot()
        self.assertTrue(res_ss.success)
        self.assertEqual(res_ss.data, b"mock_png_bytes")
        # 17. capture_network_requests
        self.assertTrue(self.browser.capture_network_requests().success)
        # 18. capture_console_logs
        self.assertTrue(self.browser.capture_console_logs().success)
        # 19. get_current_url
        res_url = self.browser.get_current_url()
        self.assertTrue(res_url.success)
        self.assertEqual(res_url.data, "https://test.local")
        # 20. get_page_title
        res_title = self.browser.get_page_title()
        self.assertTrue(res_title.success)
        self.assertEqual(res_title.data, "Mock Title")
        # 21. get_page_html
        res_html = self.browser.get_page_html()
        self.assertTrue(res_html.success)
        self.assertIn("<html>", res_html.data)
        # 22. get_clean_text
        res_text = self.browser.get_clean_text()
        self.assertTrue(res_text.success)
        self.assertEqual(res_text.data, "Mock Content")

    def test_browser_tool_action_dispatch(self):
        """Verify BrowserTool executes action commands and returns serialized ActionResults."""
        from tools.browser import BrowserTool
        tool = BrowserTool(browser=self.browser)

        # Test tool navigation
        res_str = tool.forward(action="open_url", url="https://tool-test.local")
        res_dict = json.loads(res_str)
        self.assertTrue(res_dict["success"])
        self.assertEqual(res_dict["url"], "https://tool-test.local")
        self.assertEqual(res_dict["title"], "Mock Title")

        # Test tool click
        click_str = tool.forward(action="click", selector="#btn")
        click_dict = json.loads(click_str)
        self.assertTrue(click_dict["success"])

        # Test validation error behavior
        err_str = tool.forward(action="fill_input", selector="")
        err_dict = json.loads(err_str)
        self.assertFalse(err_dict["success"])
        self.assertTrue(any("required" in err for err in err_dict["errors"]))


if __name__ == "__main__":
    unittest.main()
