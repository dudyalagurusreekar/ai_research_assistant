"""Built-in macros for the autonomous browser agent.

Implements reusable high-level skills: login, search, article extraction, form filling,
file upload, file download, page capture, structured scraping, and comparison.
"""

import json
from typing import Any, Dict

from tools.browser.macro.base import (
    BaseMacro,
    MacroExecutionError,
    MacroValidationError,
    register_macro,
)
from tools.browser.models.response import ActionResult


@register_macro("macro_search")
class SearchMacro(BaseMacro):
    """Orchestrates search queries across search engines or the current site contextually."""

    @property
    def name(self) -> str:
        return "macro_search"

    @property
    def description(self) -> str:
        return "Search for a query contextually on the current site or externally on Google."

    def validate(self, params: Dict[str, Any]) -> None:
        query = params.get("text_input") or params.get("text") or params.get("query")
        if not query:
            raise MacroValidationError("Search query ('text_input') is required.")
        scope = params.get("search_scope", "current_site")
        if scope not in ("current_site", "current_domain", "external"):
            raise MacroValidationError(f"Invalid search_scope: {scope}")

    def execute(self, params: Dict[str, Any]) -> ActionResult:
        query = params.get("text_input") or params.get("text") or params.get("query")
        scope = params.get("search_scope", "current_site")

        # Save checkpoint
        self.context.create_checkpoint()

        url = params.get("url")

        from tools.browser.macro.search_strategies import SearchStrategyCoordinator
        coordinator = SearchStrategyCoordinator(self.context.browser)
        
        # Determine strategy and get the execution dictionary
        strategy_dict = coordinator.execute_search(query, scope, url)

        # 1. Execute the primary strategy action (usually open_url or fill_input)
        if strategy_dict.get("action") == "open_url":
            self.run_sub_action({"action": "open_url", "url": strategy_dict.get("url")})
        elif strategy_dict.get("action") == "fill_input":
            sel = strategy_dict.get("selector")
            text = strategy_dict.get("text")
            self.run_sub_action({"action": "wait_for_selector", "selector": sel, "timeout": 2.0})
            self.run_sub_action({"action": "fill_input", "selector": sel, "text_input": text})

        # 2. Wait for page load
        try:
            self.run_sub_action({"action": "wait_for_network_idle", "timeout": 5.0})
        except MacroExecutionError:
            pass  # Non-fatal if page partially loaded but network not idle

        # 3. Extract result page text
        text_res = self.run_sub_action({"action": "get_clean_text"})

        current_url = self.context.browser.get_current_url().data or "about:blank"
        current_title = self.context.browser.get_page_title().data or "Search Results"

        return ActionResult(
            url=current_url,
            title=current_title,
            success=True,
            data=text_res.data,
        )


@register_macro("macro_login")
class LoginMacro(BaseMacro):
    """Executes a multi-input login credential submission."""

    @property
    def name(self) -> str:
        return "macro_login"

    @property
    def description(self) -> str:
        return "Log in to a website by filling credentials and submitting the form."

    def validate(self, params: Dict[str, Any]) -> None:
        url = params.get("url")
        credentials = params.get("credentials")
        if not url:
            raise MacroValidationError("Login URL ('url') is required.")
        if not credentials:
            raise MacroValidationError("Credentials dictionary ('credentials') is required.")

    def execute(self, params: Dict[str, Any]) -> ActionResult:
        url = params.get("url")
        credentials = params.get("credentials")

        if isinstance(credentials, str):
            try:
                credentials = json.loads(credentials)
            except Exception as e:
                raise MacroValidationError(f"Invalid credentials JSON: {e}")

        submit_selector = params.get("selector")

        self.context.create_checkpoint()

        # 1. Navigate to login URL
        self.run_sub_action({"action": "open_url", "url": url})

        # 2. Fill input credentials
        last_selector = None
        for sel, val in credentials.items():
            self.run_sub_action({"action": "wait_for_selector", "selector": sel, "timeout": 5.0})
            self.run_sub_action({"action": "fill_input", "selector": sel, "text_input": str(val)})
            last_selector = sel

        # 3. Submit
        if submit_selector:
            self.run_sub_action({"action": "wait_for_selector", "selector": submit_selector, "timeout": 5.0})
            self.run_sub_action({"action": "click", "selector": submit_selector})
        elif last_selector:
            self.run_sub_action({"action": "press_key", "selector": last_selector, "key": "Enter"})

        # 4. Wait for redirection / page change
        try:
            self.run_sub_action({"action": "wait_for_network_idle", "timeout": 5.0})
        except MacroExecutionError:
            pass

        current_url = self.context.browser.get_current_url().data or url
        current_title = self.context.browser.get_page_title().data or "Login Dashboard"

        return ActionResult(
            url=current_url,
            title=current_title,
            success=True,
        )


@register_macro("macro_fill_form")
class FormFillingMacro(BaseMacro):
    """Handles multi-field form fills with optional submission."""

    @property
    def name(self) -> str:
        return "macro_fill_form"

    @property
    def description(self) -> str:
        return "Fill a multi-field form and optionally click the submit selector."

    def validate(self, params: Dict[str, Any]) -> None:
        form_data = params.get("form_data")
        if not form_data:
            raise MacroValidationError("Form data mapping ('form_data') is required.")

    def execute(self, params: Dict[str, Any]) -> ActionResult:
        form_data = params.get("form_data")
        if isinstance(form_data, str):
            try:
                form_data = json.loads(form_data)
            except Exception as e:
                raise MacroValidationError(f"Invalid form_data JSON: {e}")

        submit_selector = params.get("selector")

        self.context.create_checkpoint()

        # 1. Fill fields
        for sel, val in form_data.items():
            self.run_sub_action({"action": "wait_for_selector", "selector": sel, "timeout": 5.0})
            self.run_sub_action({"action": "fill_input", "selector": sel, "text_input": str(val)})

        # 2. Click Submit
        if submit_selector:
            self.run_sub_action({"action": "wait_for_selector", "selector": submit_selector, "timeout": 5.0})
            self.run_sub_action({"action": "click", "selector": submit_selector})
            try:
                self.run_sub_action({"action": "wait_for_network_idle", "timeout": 5.0})
            except MacroExecutionError:
                pass

        current_url = self.context.browser.get_current_url().data or "about:blank"
        current_title = self.context.browser.get_page_title().data or "Form Completed"

        return ActionResult(
            url=current_url,
            title=current_title,
            success=True,
        )


@register_macro("macro_extract_article")
class ArticleExtractionMacro(BaseMacro):
    """Directly navigates and extracts readable article text."""

    @property
    def name(self) -> str:
        return "macro_extract_article"

    @property
    def description(self) -> str:
        return "Navigate to a page and extract its main readable text content."

    def validate(self, params: Dict[str, Any]) -> None:
        url = params.get("url")
        if not url:
            raise MacroValidationError("Target URL ('url') is required.")

    def execute(self, params: Dict[str, Any]) -> ActionResult:
        url = params.get("url")

        # 1. Open URL
        self.run_sub_action({"action": "open_url", "url": url})

        # 2. Extract clean text
        text_res = self.run_sub_action({"action": "get_clean_text"})

        current_title = self.context.browser.get_page_title().data or ""

        return ActionResult(
            url=url,
            title=current_title,
            success=True,
            data=text_res.data,
        )


@register_macro("macro_capture_page")
class PageCaptureMacro(BaseMacro):
    """Multi-observation capture of a page."""

    @property
    def name(self) -> str:
        return "macro_capture_page"

    @property
    def description(self) -> str:
        return "Capture screenshot, HTML, console logs, and network traffic from a page."

    def validate(self, params: Dict[str, Any]) -> None:
        pass

    def execute(self, params: Dict[str, Any]) -> ActionResult:
        url = params.get("url")

        # Navigate if URL provided
        if url:
            self.run_sub_action({"action": "open_url", "url": url})

        # Capture multiple sources
        screenshot_res = self.run_sub_action({"action": "capture_screenshot", "checked": True})
        network_res = self.run_sub_action({"action": "capture_network_requests"})
        console_res = self.run_sub_action({"action": "capture_console_logs"})
        text_res = self.run_sub_action({"action": "get_clean_text"})

        data_summary = {
            "screenshot_path": screenshot_res.data if screenshot_res.success else None,
            "network_requests_count": len(network_res.data) if network_res.success and isinstance(network_res.data, list) else 0,
            "console_logs_count": len(console_res.data) if console_res.success and isinstance(console_res.data, list) else 0,
            "extracted_text_snippet": text_res.data[:500] if text_res.success and text_res.data else ""
        }

        current_url = self.context.browser.get_current_url().data or url or "about:blank"
        current_title = self.context.browser.get_page_title().data or "Page Capture"

        return ActionResult(
            url=current_url,
            title=current_title,
            success=True,
            data=data_summary,
        )


@register_macro("macro_navigate_and_read")
class NavigationAndReadMacro(BaseMacro):
    """Equivalent to navigation followed by clean text reading."""

    @property
    def name(self) -> str:
        return "macro_navigate_and_read"

    @property
    def description(self) -> str:
        return "Open a URL, wait for network idle, and return clean text."

    def validate(self, params: Dict[str, Any]) -> None:
        url = params.get("url")
        if not url:
            raise MacroValidationError("URL ('url') is required.")

    def execute(self, params: Dict[str, Any]) -> ActionResult:
        url = params.get("url")
        
        self.run_sub_action({"action": "open_url", "url": url})
        try:
            self.run_sub_action({"action": "wait_for_network_idle", "timeout": 5.0})
        except MacroExecutionError:
            pass
            
        text_res = self.run_sub_action({"action": "get_clean_text"})
        current_title = self.context.browser.get_page_title().data or ""

        return ActionResult(
            url=url,
            title=current_title,
            success=True,
            data=text_res.data,
        )


@register_macro("macro_scrape")
class ScrapingMacro(BaseMacro):
    """Extracts structured items from a page based on CSS selectors."""

    @property
    def name(self) -> str:
        return "macro_scrape"

    @property
    def description(self) -> str:
        return "Scrape list items or structured records matching a CSS selector."

    def validate(self, params: Dict[str, Any]) -> None:
        selector = params.get("selector")
        if not selector:
            raise MacroValidationError("CSS selector ('selector') is required.")

    def execute(self, params: Dict[str, Any]) -> ActionResult:
        selector = params.get("selector")
        url = params.get("url")

        if url:
            self.run_sub_action({"action": "open_url", "url": url})

        self.run_sub_action({"action": "wait_for_selector", "selector": selector, "timeout": 5.0})

        # Run JS to pull text list for matching items
        js = (
            f"Array.from(document.querySelectorAll('{selector}'))"
            f".map(el => (el.innerText || el.textContent || '').trim())"
            f".filter(txt => txt.length > 0)"
        )
        js_res = self.run_sub_action({"action": "execute_javascript", "extra_args": js})

        current_url = self.context.browser.get_current_url().data or "about:blank"
        current_title = self.context.browser.get_page_title().data or "Scraped Page"

        return ActionResult(
            url=current_url,
            title=current_title,
            success=True,
            data=js_res.data,
        )


@register_macro("macro_compare")
class ComparisonMacro(BaseMacro):
    """Compares the visual or textual content of two URLs."""

    @property
    def name(self) -> str:
        return "macro_compare"

    @property
    def description(self) -> str:
        return "Compare page content or layouts between two URLs."

    def validate(self, params: Dict[str, Any]) -> None:
        url = params.get("url")
        other_url = params.get("extra_args") or params.get("other_url")
        if not url or not other_url:
            raise MacroValidationError("Two URLs ('url' and 'other_url') are required.")

    def execute(self, params: Dict[str, Any]) -> ActionResult:
        url1 = params.get("url")
        url2 = params.get("extra_args") or params.get("other_url")

        # 1. Capture Page 1
        self.run_sub_action({"action": "open_url", "url": url1})
        text1_res = self.run_sub_action({"action": "get_clean_text"})
        text1 = text1_res.data or ""

        # 2. Capture Page 2
        self.run_sub_action({"action": "open_url", "url": url2})
        text2_res = self.run_sub_action({"action": "get_clean_text"})
        text2 = text2_res.data or ""

        # Check for textual similarities / diff length
        diff_len = abs(len(text1) - len(text2))
        similarity = 0.0
        if len(text1) > 0 or len(text2) > 0:
            longer = max(len(text1), len(text2))
            similarity = (1.0 - (diff_len / longer)) * 100.0

        comparison_data = {
            "url1_length": len(text1),
            "url2_length": len(text2),
            "length_difference": diff_len,
            "text_length_similarity_pct": round(similarity, 2),
        }

        current_url = self.context.browser.get_current_url().data or url2

        return ActionResult(
            url=current_url,
            title="Comparison Result",
            success=True,
            data=comparison_data,
        )


@register_macro("macro_upload_file")
class FileUploadMacro(BaseMacro):
    """Executes a file upload."""

    @property
    def name(self) -> str:
        return "macro_upload_file"

    @property
    def description(self) -> str:
        return "Upload a file to a specific input selector element."

    def validate(self, params: Dict[str, Any]) -> None:
        selector = params.get("selector")
        file_path = params.get("text_input") or params.get("file_path")
        if not selector or not file_path:
            raise MacroValidationError("CSS Selector ('selector') and file path ('text_input') are required.")

    def execute(self, params: Dict[str, Any]) -> ActionResult:
        selector = params.get("selector")
        file_path = params.get("text_input") or params.get("file_path")

        self.run_sub_action({"action": "wait_for_selector", "selector": selector, "timeout": 5.0})
        upload_res = self.run_sub_action({"action": "upload_file", "selector": selector, "text_input": file_path})

        current_url = self.context.browser.get_current_url().data or "about:blank"
        current_title = self.context.browser.get_page_title().data or ""

        return ActionResult(
            url=current_url,
            title=current_title,
            success=True,
            data=upload_res.data,
        )


@register_macro("macro_download_file")
class FileDownloadMacro(BaseMacro):
    """Executes a download click."""

    @property
    def name(self) -> str:
        return "macro_download_file"

    @property
    def description(self) -> str:
        return "Trigger a file download by clicking on a selector."

    def validate(self, params: Dict[str, Any]) -> None:
        selector = params.get("selector")
        if not selector:
            raise MacroValidationError("Click selector ('selector') is required.")

    def execute(self, params: Dict[str, Any]) -> ActionResult:
        selector = params.get("selector")
        download_dir = params.get("text_input") or params.get("download_dir")

        self.run_sub_action({"action": "wait_for_selector", "selector": selector, "timeout": 5.0})
        download_res = self.run_sub_action({
            "action": "download_file",
            "selector": selector,
            "text_input": download_dir,
        })

        current_url = self.context.browser.get_current_url().data or "about:blank"
        current_title = self.context.browser.get_page_title().data or ""

        return ActionResult(
            url=current_url,
            title=current_title,
            success=True,
            data=download_res.data,
        )
