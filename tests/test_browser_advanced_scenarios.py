"""Advanced Integration Tests for Browser Action Engine and Playwright Strategy.

Spins up a local HTTP Sandbox Server on a background thread and executes end-to-end
browser scenarios: logins, cookie persistence, SPA delays, infinite scroll rendering,
uploads/downloads, redirects, and server errors.
"""

import os
import tempfile
import unittest

from tools.browser.config import BrowserConfig
from tools.browser.constants import BrowserEngineType
from tools.browser.core.browser import Browser
from tests.sandbox_server import SandboxServer


class TestBrowserAdvancedScenarios(unittest.TestCase):
    """Integration tests running Playwright browser strategy against dynamic local server endpoints."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = SandboxServer()
        cls.server.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.stop()

    def setUp(self) -> None:
        self.config = BrowserConfig(engine_type=BrowserEngineType.PLAYWRIGHT, headless=True)
        self.browser = Browser(self.config)

    def tearDown(self) -> None:
        self.browser.close()

    def test_login_flow_and_cookie_session(self) -> None:
        """Verify dynamic login workflow, form submission, and cookie session authentication."""
        # 1. Open login page
        res = self.browser.open_url(f"{self.server.url}/login")
        self.assertTrue(res.success)
        self.assertEqual(res.title, "Login Page")

        # 2. Fill credentials and check remember me
        self.browser.fill_input("#username", "admin")
        self.browser.fill_input("#password", "secret")
        self.browser.check_checkbox("#remember", checked=True)

        # 3. Submit Form (triggers redirect to /admin)
        res_submit = self.browser.click("#submit-login")
        self.assertTrue(res_submit.success)

        # 4. Wait for redirection target to render
        self.browser.wait_for_selector("#admin-secret", state="visible", timeout=5.0)

        # 5. Check if we navigated to /admin
        url_res = self.browser.get_current_url()
        self.assertIn("/admin", url_res.data)

        # 6. Verify dashboard secret text is visible
        text_res = self.browser.get_clean_text()
        self.assertIn("Dashboard Loaded Successfully.", text_res.data)

    def test_spa_delayed_rendering(self) -> None:
        """Verify automated waiting for dynamic SPA asynchronous page loading elements."""
        res = self.browser.open_url(f"{self.server.url}/spa")
        self.assertTrue(res.success)

        # Wait for dynamically loaded element to render
        res_wait = self.browser.wait_for_selector("#async-loaded", state="visible", timeout=5.0)
        self.assertTrue(res_wait.success)

        text_res = self.browser.get_clean_text()
        self.assertIn("SPA Content Loaded Dynamically!", text_res.data)

    def test_infinite_scroll_element_loading(self) -> None:
        """Verify scroll actions and waiting for infinite scroll DOM additions."""
        res = self.browser.open_url(f"{self.server.url}/infinite-scroll")
        self.assertTrue(res.success)

        # Scroll to bottom
        self.browser.scroll_page(direction="bottom")

        # Wait for infinite-scrolled element to appear
        res_wait = self.browser.wait_for_selector("#scroll-target", state="visible", timeout=5.0)
        self.assertTrue(res_wait.success)

        text_res = self.browser.get_clean_text()
        self.assertIn("Target Scrolled Node Found!", text_res.data)

    def test_redirects_and_errors_handling(self) -> None:
        """Verify HTTP redirect routing and server 500 error page handling."""
        # Test redirect
        res_redir = self.browser.open_url(f"{self.server.url}/redirect")
        self.assertTrue(res_redir.success)
        self.assertIn("/login", self.browser.get_current_url().data)

        # Test error endpoint
        res_err = self.browser.open_url(f"{self.server.url}/error")
        # Under playwright, a 500 page loads successfully as a document
        self.assertTrue(res_err.success)
        self.assertIn("Internal Server Error", self.browser.get_clean_text().data)

    def test_file_upload_and_download(self) -> None:
        """Verify uploading local files and downloading binary attachments."""
        self.browser.open_url(f"{self.server.url}/login")
        self.browser.execute_javascript(
            "const a = document.createElement('a'); a.id = 'dl-link'; a.href = '/download'; a.download = 'download_file.txt'; a.innerText = 'Download'; document.body.appendChild(a);"
        )

        dl_res = self.browser.download_file("#dl-link")
        self.assertTrue(dl_res.success)
        dl_path = dl_res.data["path"] if isinstance(dl_res.data, dict) else dl_res.data
        self.assertTrue(os.path.exists(dl_path))
        
        with open(dl_path, "r") as f:
            content = f.read()
        self.assertEqual(content, "Production download contents verified.")
        os.remove(dl_path)

        # 2. Upload verification
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as tmp_file:
            tmp_file.write("Sandbox Upload Payload")
            tmp_file_path = tmp_file.name

        try:
            self.browser.open_url(f"{self.server.url}/login")
            
            # Write a custom HTML upload input dynamically on the login page to verify upload
            self.browser.execute_javascript(
                "const inp = document.createElement('input'); inp.type = 'file'; inp.id = 'up-file'; document.body.appendChild(inp);"
            )
            
            up_res = self.browser.upload_file("#up-file", tmp_file_path)
            self.assertTrue(up_res.success)
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)


if __name__ == "__main__":
    unittest.main()
