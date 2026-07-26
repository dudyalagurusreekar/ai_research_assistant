"""Central Browser Orchestrator Engine and Facade for the Browser Tool Subsystem.

This module contains the central `Browser` class. Acting as a unified Facade, it coordinates
configuration, network fetchers (Step 2), content cleaners & parsers (Step 3), content routing,
language detection, automatic memory & resource management, high-level AI agent operations,
and multi-page web research crawling (Step 4).
"""

import json
import time
from typing import Optional, Dict, Any, List, Union
from urllib.parse import urlparse

from tools.browser.config import BrowserConfig
from tools.browser.constants import PageStatus, BrowserAction
from tools.browser.exceptions import BrowserError, ValidationError
from tools.browser.models.request import BrowserRequest, NavigationParams, ActionParams
from tools.browser.models.response import (
    BrowserResponse,
    PageMetadata,
    PerformanceMetrics,
    FetchResult,
    ActionResult,
    ActionMetrics,
)
from tools.browser.models.page import PageState, LinkInfo
from tools.browser.core.base_fetcher import BaseFetcher
from tools.browser.core.base_parser import BaseParser
from tools.browser.fetchers.factory import FetcherFactory
from tools.browser.parsers.factory import ParserFactory
from tools.browser.services.content_router import ContentRouter
from tools.browser.services.language import LanguageDetector
from tools.browser.crawler import CrawlerEngine
from tools.browser.utils.helpers import generate_request_id, sanitize_url, validate_url, clean_text
from tools.browser.utils.logging import get_browser_logger


class Browser:
    """Unified Facade and Core Orchestrator Engine for the Browser Tool Subsystem.

    Provides a clean, resource-efficient API for AI research agents, managing
    connection pools, memory disposal, content routing, language detection, and crawling.

    Attributes:
        config (BrowserConfig): Active configuration settings.
        fetcher (BaseFetcher): Concrete network fetcher strategy instance.
        parser (BaseParser): Default document parser strategy instance.
        router (ContentRouter): Strategy router selecting parsers by MIME type/extension.
        language_detector (LanguageDetector): Document language detection utility.
        crawler (CrawlerEngine): Multi-page recursive crawler engine.
        current_state (Optional[PageState]): In-memory representation of currently loaded page.
        history (List[str]): Navigation URL history log.
    """

    def __init__(
        self,
        config: Optional[BrowserConfig] = None,
        fetcher: Optional[BaseFetcher] = None,
        parser: Optional[BaseParser] = None,
        router: Optional[ContentRouter] = None,
    ) -> None:
        """Initialize the Browser Facade and orchestrator components.

        Args:
            config (Optional[BrowserConfig]): Browser configuration parameters.
            fetcher (Optional[BaseFetcher]): Injected network fetcher strategy.
            parser (Optional[BaseParser]): Injected default document parser strategy.
            router (Optional[ContentRouter]): Injected content strategy router.
        """
        self.config = config or BrowserConfig()
        self.config.validate()

        self.fetcher = fetcher or FetcherFactory.create_fetcher(self.config.engine_type, self.config)
        self.parser = parser or ParserFactory.create_parser("BS4")
        self.router = router or ContentRouter(default_parser=self.parser)
        self.language_detector = LanguageDetector()
        self.crawler = CrawlerEngine(self)

        self._automation_engine: Optional[Any] = None
        if hasattr(self.fetcher, "automation_engine"):
            self._automation_engine = getattr(self.fetcher, "automation_engine")

        self.current_state: Optional[PageState] = None
        self.history: List[str] = []
        self._logger = get_browser_logger("Browser")

        self._logger.info(
            f"Initialized Browser Facade (Engine: {self.config.engine_type.value}, "
            f"Fetcher: {self.fetcher.__class__.__name__}, Default Parser: {self.parser.__class__.__name__})"
        )

    @property
    def automation(self) -> Any:
        """Access underlying BrowserAutomationEngine facade."""
        if not self._automation_engine:
            from tools.browser.automation.engine import BrowserAutomationEngine
            self._automation_engine = BrowserAutomationEngine(config=self.config)
        return self._automation_engine

    # -------------------------------------------------------------------------
    # Core Navigation & Resource Management Pipeline
    # -------------------------------------------------------------------------

    def read_page(self, url: str, **kwargs: Any) -> BrowserResponse:
        """Primary AI-friendly page reading operation.

        Executes the full pipeline: Fetcher -> ContentRouter -> Parser -> Memory Cleanup -> DTO.

        Args:
            url (str): Target webpage or resource URL.
            **kwargs: Overrides (keep_raw_html=True to disable automatic memory release).

        Returns:
            BrowserResponse: Unified browser response with clean extracted content.
        """
        start_time = time.time()
        req_id = generate_request_id("read")

        sanitized_url = sanitize_url(url)
        validate_url(sanitized_url)

        self._logger.info(f"[{req_id}] Executing read_page for '{sanitized_url}'")

        nav_params = NavigationParams(
            url=sanitized_url,
            method=kwargs.get("method", self.config.default_headers.get("method", "GET")),
            headers=kwargs.get("headers", self.config.default_headers),
            timeout=kwargs.get("timeout", self.config.timeout_seconds),
        )

        # 1. Network Fetching
        fetch_start = time.time()
        fetch_result = self.fetcher.fetch(nav_params)
        fetch_duration = (time.time() - fetch_start) * 1000.0

        # 2. Content Type Strategy Routing & Document Parsing
        parse_start = time.time()
        active_parser = self.router.route(fetch_result)

        if fetch_result.success:
            page_state = active_parser.parse(fetch_result)
            # Detect language automatically
            detected_lang = self.language_detector.detect(page_state.metadata, page_state.main_text)
            page_state.metadata.language = detected_lang
            self.current_state = page_state
            extracted_text = page_state.main_text
            metadata = page_state.metadata
        else:
            extracted_text = fetch_result.text
            metadata = PageMetadata(
                title=fetch_result.url,
                description=f"Network fetch error ({fetch_result.status_code})",
            )

        parse_duration = (time.time() - parse_start) * 1000.0
        total_duration = (time.time() - start_time) * 1000.0

        self.history.append(fetch_result.url)

        status = (
            PageStatus.PARSED
            if fetch_result.success
            else PageStatus.FAILED
        )

        keep_raw = kwargs.get("keep_raw_html", self.config.enable_cache)
        raw_html_content = fetch_result.text if keep_raw else None

        # 3. Automatic Memory Management (Disposing raw byte payload buffers)
        if not keep_raw:
            fetch_result.content = b""

        return BrowserResponse(
            request_id=req_id,
            url=fetch_result.url,
            status=status,
            status_code=fetch_result.status_code,
            metadata=metadata,
            extracted_text=extracted_text,
            raw_html=raw_html_content,
            metrics=PerformanceMetrics(
                fetch_duration_ms=fetch_duration,
                parse_duration_ms=parse_duration,
                total_duration_ms=total_duration,
                content_length_bytes=len(extracted_text.encode("utf-8")),
                redirect_count=fetch_result.redirect_count,
            ),
            errors=[fetch_result.error_message] if fetch_result.error_message else [],
        )

    def navigate(self, url: str, **kwargs: Any) -> BrowserResponse:
        """Navigate to URL (compatibility wrapper delegating to read_page)."""
        return self.read_page(url, **kwargs)

    # -------------------------------------------------------------------------
    # High-Level Task-Oriented AI Operations
    # -------------------------------------------------------------------------

    def extract_information(self, url: str, query: str, **kwargs: Any) -> Dict[str, Any]:
        """Fetch webpage and extract targeted sections matching a user query.

        Args:
            url (str): Target webpage URL.
            query (str): Keyword query to match against page content.

        Returns:
            Dict[str, Any]: Extracted relevant headings, paragraphs, and tables.
        """
        response = self.read_page(url, **kwargs)
        if not self.current_state:
            return {"url": url, "matched_sections": [], "matched_tables": []}

        query_terms = [q.lower() for q in query.split() if len(q) > 2]

        matched_headings = [
            h for h in self.current_state.headings
            if any(term in h["text"].lower() for term in query_terms)
        ]

        matched_paragraphs = [
            p for p in self.current_state.paragraphs
            if any(term in p.lower() for term in query_terms)
        ]

        matched_tables = [
            t for t in self.current_state.tables
            if any(term in json.dumps(t).lower() for term in query_terms)
        ]

        return {
            "url": response.url,
            "title": response.metadata.title,
            "query": query,
            "matched_headings": matched_headings,
            "matched_paragraphs": matched_paragraphs,
            "matched_tables": matched_tables,
        }

    def search_page(self, query: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """Search inside currently loaded page for matching text snippets.

        Args:
            query (str): Search query string.

        Returns:
            List[Dict[str, Any]]: List of matching sentence snippets with context.
        """
        if not self.current_state or not self.current_state.main_text:
            return []

        text = self.current_state.main_text
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 10]
        query_lower = query.lower()

        results = []
        for idx, sentence in enumerate(sentences):
            if query_lower in sentence.lower():
                results.append({
                    "snippet_index": idx,
                    "snippet": sentence + ".",
                    "context": " ".join(sentences[max(0, idx - 1): min(len(sentences), idx + 2)]),
                })

        return results

    def find_links(self, filters: Optional[Dict[str, Any]] = None, **kwargs: Any) -> List[LinkInfo]:
        """Filter extracted links on currently loaded page.

        Args:
            filters (Optional[Dict[str, Any]]): Filter options (is_external, keyword, extension).

        Returns:
            List[LinkInfo]: Matching filtered LinkInfo DTOs.
        """
        if not self.current_state:
            return []

        links = self.current_state.links
        if not filters:
            return links

        filtered = []
        is_external = filters.get("is_external")
        keyword = filters.get("keyword", "").lower()
        extension = filters.get("extension", "").lower()

        for link in links:
            if is_external is not None and link.is_external != is_external:
                continue
            if keyword and (keyword not in link.text.lower() and keyword not in link.href.lower()):
                continue
            if extension and not urlparse(link.href).path.lower().endswith(extension):
                continue
            filtered.append(link)

        return filtered

    def collect_documents(self, url: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """Scan target page and collect all downloadable research document links.

        Args:
            url (str): Target webpage URL.

        Returns:
            List[Dict[str, Any]]: List of research document links (.pdf, .docx, .xlsx, .csv).
        """
        self.read_page(url, **kwargs)
        if not self.current_state:
            return []

        doc_extensions = (".pdf", ".docx", ".doc", ".xlsx", ".csv", ".json", ".zip")
        documents = []

        for link in self.current_state.links:
            path = urlparse(link.href).path.lower()
            if any(path.endswith(ext) for ext in doc_extensions):
                documents.append({
                    "url": link.href,
                    "text": link.text,
                    "extension": path.split(".")[-1] if "." in path else "",
                    "is_external": link.is_external,
                })

        return documents

    def discover_links(self, url: str, **kwargs: Any) -> List[LinkInfo]:
        """Fetch target page and return all discovered links.

        Args:
            url (str): Target webpage URL.

        Returns:
            List[LinkInfo]: List of extracted LinkInfo DTOs.
        """
        self.read_page(url, **kwargs)
        return self.current_state.links if self.current_state else []

    def crawl(
        self,
        start_url: str,
        max_depth: int = 2,
        max_pages: int = 10,
        allowed_domains: Optional[List[str]] = None,
        respect_robots_txt: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Multi-page recursive crawling operation returning a CrawlResult.

        Args:
            start_url (str): Seed URL.
            max_depth (int): Maximum depth level.
            max_pages (int): Maximum total pages.
            allowed_domains (Optional[List[str]]): Domain restriction whitelist.
            respect_robots_txt (bool): Respect robots.txt.

        Returns:
            CrawlResult: Aggregated crawl output model.
        """
        return self.crawler.crawl(
            start_url=start_url,
            max_depth=max_depth,
            max_pages=max_pages,
            allowed_domains=allowed_domains,
            respect_robots_txt=respect_robots_txt,
            strategy=kwargs.get("strategy"),
            rate_limit_delay=kwargs.get("rate_limit_delay", 0.5),
            keep_raw_html=kwargs.get("keep_raw_html", False),
        )

    def crawl_domain(self, domain: str, max_depth: int = 2, max_pages: int = 15, **kwargs: Any) -> Any:
        """Crawl an entire target domain.

        Args:
            domain (str): Target domain hostname.
            max_depth (int): Maximum depth.
            max_pages (int): Maximum page limit.

        Returns:
            CrawlResult: Aggregated crawl result.
        """
        return self.crawler.crawl_domain(domain=domain, max_depth=max_depth, max_pages=max_pages, **kwargs)

    def crawl_site_map(self, sitemap_url: str, max_pages: int = 15, **kwargs: Any) -> Any:
        """Discover and crawl pages from a sitemap.xml.

        Args:
            sitemap_url (str): Target sitemap URL.
            max_pages (int): Page limit.

        Returns:
            CrawlResult: Aggregated crawl result.
        """
        return self.crawler.crawl_site_map(sitemap_url=sitemap_url, max_pages=max_pages, **kwargs)

    def crawl_until(self, start_url: str, condition_fn: Any, max_pages: int = 10, **kwargs: Any) -> Any:
        """Crawl until a custom condition evaluates to True.

        Args:
            start_url (str): Seed URL.
            condition_fn (Callable[[PageState], bool]): Predicate condition.
            max_pages (int): Safety page limit.

        Returns:
            Optional[CrawlNode]: Matching node or None.
        """
        return self.crawler.crawl_until(start_url=start_url, condition_fn=condition_fn, max_pages=max_pages, **kwargs)

    def execute_action(self, action_params: ActionParams) -> BrowserResponse:
        """Execute interactive browser actions (click, scroll, type, extract)."""
        req_id = generate_request_id("act")
        action_params.validate()

        self._logger.info(f"[{req_id}] Executing dynamic action '{action_params.action.value}' on selector '{action_params.selector}'")

        # 1. Execute action via automation engine
        val = action_params.text_input or action_params.scroll_offset or action_params.extra_args
        result = self.automation.interact(
            action_type=action_params.action,
            selector=action_params.selector,
            value=val,
        )

        # 2. Extract post-action HTML source and metadata to update PageState
        html_source = self.automation.get_page_source()
        current_url = self.automation._run_sync(self.automation.strategy.get_url())
        current_title = self.automation._run_sync(self.automation.strategy.get_title())

        # Construct a dummy FetchResult for parsing
        fetch_result = FetchResult(
            url=current_url,
            status_code=200,
            headers={"content-type": "text/html"},
            content=html_source.encode("utf-8"),
            encoding="utf-8",
            mime_type="text/html",
            success=True,
        )

        # 3. Route and parse post-action state
        active_parser = self.router.route(fetch_result)
        page_state = active_parser.parse(fetch_result)
        page_state.metadata.title = current_title
        self.current_state = page_state

        return BrowserResponse(
            request_id=req_id,
            url=current_url,
            status=PageStatus.LOADED,
            status_code=200,
            metadata=page_state.metadata,
            extracted_text=page_state.main_text,
            raw_html=html_source,
        )

    # -------------------------------------------------------------------------
    # First-Class Browser Action Engine SDK APIs (Step 6 Redesign)
    # -------------------------------------------------------------------------

    def _execute_action_api(
        self,
        action_name: str,
        func: Any,
        *args: Any,
        verification_fn: Optional[Any] = None,
        **kwargs: Any,
    ) -> ActionResult:
        """Execute a strategy action, monitor performance metrics, verify results, and wrap in ActionResult."""
        start_time = time.time()
        errors = []
        success = False
        data = None
        verification_info = None
        console_logs = []
        network_requests = []

        if hasattr(self, "_automation_engine") and self._automation_engine:
            self._automation_engine.last_action_result = None

        try:
            data = func(*args, **kwargs)
            success = True
        except Exception as e:
            errors.append(str(e))
            self._logger.error(f"Browser SDK Action '{action_name}' failed: {e}")

        # Capture the pipeline result IMMEDIATELY after executing the core function,
        # before any post-action verification or cleanup runs more commands.
        pipeline_res = None
        if hasattr(self, "_automation_engine") and self._automation_engine:
            pipeline_res = self._automation_engine.last_action_result

        # Post-action verification strategy execution (fallback)
        if success and verification_fn:
            try:
                verification_info = verification_fn(data)
            except Exception as ve:
                self._logger.warning(f"Action verification for '{action_name}' warning: {ve}")
                verification_info = {"verified": False, "message": str(ve)}

        execution_time = (time.time() - start_time) * 1000.0
        retries_attempted = 0
        validation_time = 0.0
        exec_only_time = execution_time
        wait_time = 0.0
        ver_time = 0.0

        # Retrieve pipeline metrics & logs from saved pipeline result if available
        if pipeline_res:
            if pipeline_res.get("errors"):
                for err in pipeline_res["errors"]:
                    if err not in errors:
                        errors.append(err)
            
            if pipeline_res.get("verification") is not None:
                # Prefer pipeline verification if it was defined and verified is True
                pipeline_ver = pipeline_res["verification"]
                if pipeline_ver.get("verified"):
                    verification_info = pipeline_ver
                
            console_logs = pipeline_res.get("console_logs", [])
            network_requests = pipeline_res.get("network_requests", [])
            
            pm = pipeline_res.get("metrics", {})
            retries_attempted = pm.get("retries_attempted", 0)
            validation_time = pm.get("validation_time_ms", 0.0)
            exec_only_time = pm.get("execution_only_time_ms", execution_time)
            wait_time = pm.get("wait_time_ms", 0.0)
            ver_time = pm.get("verification_time_ms", 0.0)
            execution_time = pm.get("execution_time_ms", execution_time)

        # Retrieve current page info
        url = "about:blank"
        title = ""
        try:
            if self._automation_engine:
                url = self.automation._run_sync(self.automation.strategy.get_url())
                title = self.automation._run_sync(self.automation.strategy.get_title())
        except Exception:
            pass

        metrics = ActionMetrics(
            execution_time_ms=execution_time,
            retries_attempted=retries_attempted,
            validation_time_ms=validation_time,
            execution_only_time_ms=exec_only_time,
            wait_time_ms=wait_time,
            verification_time_ms=ver_time,
        )
        return ActionResult(
            action=action_name,
            success=success,
            url=url,
            title=title,
            data=data,
            verification=verification_info,
            metrics=metrics,
            errors=errors,
            console_logs=console_logs,
            network_requests=network_requests,
        )

    def open_url(self, url: str, wait_until: Optional[str] = None, timeout: Optional[float] = None) -> ActionResult:
        """Open target webpage URL and wait for DOM load."""
        def _action():
            sanitized = sanitize_url(url)
            validate_url(sanitized)
            res = self.automation.open_page(sanitized, wait_until=wait_until, timeout=timeout)
            
            # Post-navigation DOM extraction & state routing
            html = self.automation.get_page_source()
            fetch_res = FetchResult(
                url=res.get("url", sanitized),
                status_code=res.get("status_code", 200),
                headers={"content-type": "text/html"},
                content=html.encode("utf-8"),
                encoding="utf-8",
                mime_type="text/html",
                success=res.get("success", True),
            )
            active_parser = self.router.route(fetch_res)
            self.current_state = active_parser.parse(fetch_res)
            return res

        def _verify(res):
            return {"verified": True, "url": self.current_state.url if self.current_state else url}

        return self._execute_action_api("open_url", _action, verification_fn=_verify)

    def click(self, selector: str, timeout: Optional[float] = None, force: bool = False) -> ActionResult:
        """Click on element matching selector."""
        return self._execute_action_api("click", self.automation.click, selector, timeout=timeout, force=force)

    def double_click(self, selector: str, timeout: Optional[float] = None, force: bool = False) -> ActionResult:
        """Double click on element matching selector."""
        return self._execute_action_api("double_click", self.automation.double_click, selector, timeout=timeout, force=force)

    def hover(self, selector: str, timeout: Optional[float] = None) -> ActionResult:
        """Hover mouse pointer over element matching selector."""
        return self._execute_action_api("hover", self.automation.hover, selector, timeout=timeout)

    def fill_input(self, selector: str, text: str, timeout: Optional[float] = None) -> ActionResult:
        """Fill text string into target text input matching selector."""
        return self._execute_action_api("fill_input", self.automation.fill_input, selector, text, timeout=timeout)

    def type_text(self, selector: str, text: str, clear_first: bool = True, timeout: Optional[float] = None) -> ActionResult:
        """Type text character-by-character into input field simulating keyboard typing."""
        return self._execute_action_api("type_text", self.automation.type_text, selector, text, clear_first=clear_first, timeout=timeout)

    def clear_input(self, selector: str, timeout: Optional[float] = None) -> ActionResult:
        """Clear text input field matching selector."""
        def _verify(res):
            try:
                val = self.automation.execute_script(f"document.querySelector('{selector}').value")
                return {"verified": val == "", "field_value": val}
            except Exception:
                return {"verified": True}

        return self._execute_action_api("clear_input", self.automation.clear_input, selector, timeout=timeout, verification_fn=_verify)

    def press_key(self, selector: str, key: str, timeout: Optional[float] = None) -> ActionResult:
        """Press keyboard key on element matching selector."""
        return self._execute_action_api("press_key", self.automation.press_key, selector, key, timeout=timeout)

    def select_dropdown(self, selector: str, value: str, timeout: Optional[float] = None) -> ActionResult:
        """Select option by value in dropdown matching selector."""
        def _verify(res):
            try:
                val = self.automation.execute_script(f"document.querySelector('{selector}').value")
                return {"verified": True, "selected_value": val}
            except Exception:
                return {"verified": True}

        return self._execute_action_api("select_dropdown", self.automation.select_option, selector, value, timeout=timeout, verification_fn=_verify)

    def check_checkbox(self, selector: str, checked: bool = True, timeout: Optional[float] = None) -> ActionResult:
        """Set checkbox or radio element state to checked/unchecked."""
        def _verify(res):
            try:
                is_chk = self.automation.execute_script(f"document.querySelector('{selector}').checked")
                return {"verified": is_chk == checked, "checked": is_chk}
            except Exception:
                return {"verified": True}

        return self._execute_action_api("check_checkbox", self.automation.check_checkbox, selector, checked, timeout=timeout, verification_fn=_verify)

    def upload_file(self, selector: str, files: Union[str, List[str]], timeout: Optional[float] = None) -> ActionResult:
        """Upload file(s) into file input element matching selector."""
        return self._execute_action_api("upload_file", self.automation.upload_file, selector, files, timeout=timeout)

    def download_file(self, trigger_selector: str, download_dir: Optional[str] = None, timeout: Optional[float] = None) -> ActionResult:
        """Click element triggering download and save file locally."""
        return self._execute_action_api("download_file", self.automation.download_file, trigger_selector, download_dir, timeout=timeout)

    def submit_form(self, selector: str, timeout: Optional[float] = None) -> ActionResult:
        """Submit form or click submit button matching selector."""
        return self._execute_action_api("submit_form", self.automation.submit_form, selector, timeout=timeout)

    def wait_for_selector(self, selector: str, state: str = "visible", timeout: Optional[float] = None) -> ActionResult:
        """Wait for selector to reach a specific state."""
        return self._execute_action_api("wait_for_selector", self.automation.wait_for_element, selector, state, timeout=timeout)

    def wait_for_navigation(self, wait_until: Optional[str] = None, timeout: Optional[float] = None) -> ActionResult:
        """Wait for page transition or navigation to complete."""
        return self._execute_action_api("wait_for_navigation", self.automation.wait_for_navigation, wait_until, timeout=timeout)

    def wait_for_function(self, script: str, arg: Any = None, timeout: Optional[float] = None) -> ActionResult:
        """Wait for custom JS function expression to evaluate to truthy."""
        return self._execute_action_api("wait_for_function", self.automation.wait_for_function, script, arg, timeout=timeout)

    def wait_for_url(self, url_pattern: str, timeout: Optional[float] = None) -> ActionResult:
        """Wait until active page URL matches target pattern."""
        return self._execute_action_api("wait_for_url", self.automation.wait_for_url, url_pattern, timeout=timeout)

    def wait_for_network_idle(self, timeout: Optional[float] = None) -> ActionResult:
        """Wait until network activity settles to idle state."""
        return self._execute_action_api("wait_for_network_idle", self.automation.wait_for_network_idle, timeout=timeout)

    def scroll_page(self, direction: str = "down", selector: Optional[str] = None, amount: int = 500) -> ActionResult:
        """Scroll page window or scrollable container element."""
        return self._execute_action_api("scroll_page", self.automation.scroll_to, direction, selector, amount)

    def execute_javascript(self, script: str, arg: Any = None) -> ActionResult:
        """Execute custom JavaScript script in current page context."""
        return self._execute_action_api("execute_javascript", self.automation.execute_script, script, arg)

    def capture_screenshot(self, path: Optional[str] = None, full_page: bool = False, selector: Optional[str] = None) -> ActionResult:
        """Capture screenshot of active viewport, full page document, or target element."""
        return self._execute_action_api("capture_screenshot", self.automation.take_screenshot, path, full_page, selector)

    def capture_network_requests(self) -> ActionResult:
        """Retrieve logs of all intercepted outbound HTTP requests."""
        def _action():
            logs = self.automation.capture_network()
            return logs.get("requests", [])
        return self._execute_action_api("capture_network_requests", _action)

    def capture_console_logs(self) -> ActionResult:
        """Retrieve logs of all captured browser console statements."""
        def _action():
            return self.automation.capture_console_logs()
        return self._execute_action_api("capture_console_logs", _action)

    def get_current_url(self) -> ActionResult:
        """Retrieve active page URL."""
        def _action():
            return self.automation._run_sync(self.automation.strategy.get_url())
        return self._execute_action_api("get_current_url", _action)

    def get_page_title(self) -> ActionResult:
        """Retrieve active page title."""
        def _action():
            return self.automation._run_sync(self.automation.strategy.get_title())
        return self._execute_action_api("get_page_title", _action)

    def get_page_html(self) -> ActionResult:
        """Retrieve rendered page inner HTML source."""
        def _action():
            return self.automation.get_page_source()
        return self._execute_action_api("get_page_html", _action)

    def get_clean_text(self) -> ActionResult:
        """Retrieve stripped clean text content of the page."""
        def _action():
            html = self.automation.get_page_source()
            current_url = self.automation._run_sync(self.automation.strategy.get_url())
            
            fetch_res = FetchResult(
                url=current_url,
                status_code=200,
                headers={"content-type": "text/html"},
                content=html.encode("utf-8"),
                encoding="utf-8",
                mime_type="text/html",
                success=True,
            )
            active_parser = self.router.route(fetch_res)
            self.current_state = active_parser.parse(fetch_res)
            return self.current_state.main_text
        return self._execute_action_api("get_clean_text", _action)

    def get_current_state(self) -> Optional[PageState]:
        """Retrieve current in-memory page state model."""
        return self.current_state

    # Legacy dynamic helper methods for backward compatibility
    def fill_form(self, field_values: Dict[str, str], submit_selector: Optional[str] = None, timeout: Optional[float] = None) -> bool:
        """Fill form values (legacy)."""
        return self.automation.fill_form(field_values, submit_selector=submit_selector, timeout=timeout)

    def scroll_to(self, direction: str = "down", selector: Optional[str] = None, amount: int = 500) -> bool:
        """Scroll page or scrollable element (legacy)."""
        return self.automation.scroll_to(direction=direction, selector=selector, amount=amount)

    def wait_for_element(self, selector: str, state: str = "visible", timeout: Optional[float] = None) -> Any:
        """Wait for element selector (legacy)."""
        return self.automation.wait_for_element(selector, state=state, timeout=timeout)

    def execute_script(self, script: str, arg: Any = None) -> Any:
        """Execute custom JavaScript (legacy)."""
        return self.automation.execute_script(script, arg=arg)

    def take_screenshot(self, path: Optional[str] = None, full_page: bool = False) -> bytes:
        """Capture screenshot (legacy)."""
        return self.automation.take_screenshot(path=path, full_page=full_page)

    def close(self) -> None:
        """Shut down browser engine and release allocated connection pool resources."""
        self._logger.info("Closing Browser Facade and allocated resources.")
        if self.fetcher:
            self.fetcher.close()
        if self._automation_engine:
            self._automation_engine.close()
        self.current_state = None

    async def aclose(self) -> None:
        """Shut down browser engine asynchronously."""
        if hasattr(self.fetcher, "aclose"):
            await self.fetcher.aclose()
        if self._automation_engine:
            await self._automation_engine.aclose()
        self.current_state = None

    # Context Manager Protocols for RAII Resource Management
    def __enter__(self) -> "Browser":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    async def __aenter__(self) -> "Browser":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()
