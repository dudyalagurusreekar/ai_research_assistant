"""Browser Execution Tool Facade.

Provides a clean, deterministic execution interface for browser actions.
Ensures strict separation of concerns: this layer contains zero reasoning or LLM logic.
Every action executed through this facade automatically mutates and notifies the
event-driven BrowserState single source of truth.
"""

from typing import Dict, Any, Optional, List
import logging

from tools.browser.core.browser import Browser
from tools.browser.browser.state import BrowserState, BrowserStateSnapshot
from tools.browser.browser.events import EventDispatcher

logger = logging.getLogger("BrowserToolFacade")


class BrowserToolFacade:
    """Deterministic execution facade for browser automation.

    Wraps a core Browser orchestrator and an Event-Driven BrowserState.
    All browser operations flow through this facade, automatically triggering
    state snapshots and event emissions without requiring external polling.
    """

    def __init__(
        self,
        browser: Optional[Browser] = None,
        state: Optional[BrowserState] = None,
        dispatcher: Optional[EventDispatcher] = None,
    ) -> None:
        """Initialize the browser tool facade.

        Args:
            browser (Optional[Browser]): Core browser orchestrator instance.
            state (Optional[BrowserState]): Central event-driven state instance.
            dispatcher (Optional[EventDispatcher]): Optional custom event dispatcher.
        """
        self.browser = browser or Browser()
        self.dispatcher = dispatcher or EventDispatcher()
        self.state = state or BrowserState(dispatcher=self.dispatcher)

    def _get_error(self, res: Any) -> Optional[str]:
        if hasattr(res, "error") and getattr(res, "error"):
            return getattr(res, "error")
        if hasattr(res, "errors") and getattr(res, "errors"):
            return getattr(res, "errors")[0]
        return None

    def execute_action(self, action: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute a deterministic browser action and update browser state.

        Args:
            action (str): Action name (e.g., 'open_url', 'click', 'fill_input', 'get_clean_text').
            **kwargs: Keyword arguments for the action.

        Returns:
            Dict[str, Any]: Standardized execution result containing success flag, data, and error.
        """
        logger.debug(f"Executing deterministic browser action: {action} with args: {kwargs}")

        result: Dict[str, Any] = {
            "success": False,
            "action": action,
            "data": None,
            "error": None,
        }

        try:
            if action == "open_url":
                url = kwargs.get("url")
                if not url:
                    raise ValueError("Missing required argument 'url' for open_url action.")
                res = self.browser.open_url(url)
                result["success"] = res.success
                result["data"] = res.data
                result["error"] = self._get_error(res)

            elif action == "click":
                selector = kwargs.get("selector")
                if not selector:
                    raise ValueError("Missing required argument 'selector' for click action.")
                res = self.browser.click(selector)
                result["success"] = res.success
                result["data"] = res.data
                result["error"] = self._get_error(res)

            elif action == "fill_input" or action == "type_text":
                selector = kwargs.get("selector")
                text = kwargs.get("text_input") or kwargs.get("text", "")
                if not selector:
                    raise ValueError(f"Missing required argument 'selector' for {action} action.")
                res = self.browser.fill_input(selector, text)
                result["success"] = res.success
                result["data"] = res.data
                result["error"] = self._get_error(res)

            elif action == "get_current_url":
                res = self.browser.get_current_url()
                result["success"] = res.success
                result["data"] = res.data
                result["error"] = self._get_error(res)

            elif action == "get_page_title":
                res = self.browser.get_page_title()
                result["success"] = res.success
                result["data"] = res.data
                result["error"] = self._get_error(res)

            elif action == "get_page_html":
                res = self.browser.get_page_html()
                result["success"] = res.success
                result["data"] = res.data
                result["error"] = self._get_error(res)

            elif action == "get_clean_text":
                res = self.browser.get_clean_text()
                result["success"] = res.success
                result["data"] = res.data
                result["error"] = self._get_error(res)

            elif action == "execute_javascript":
                script = kwargs.get("script") or kwargs.get("text_input", "")
                res = self.browser.execute_javascript(script)
                result["success"] = res.success
                result["data"] = res.data
                result["error"] = self._get_error(res)

            elif action == "capture_screenshot":
                path = kwargs.get("path") or kwargs.get("text_input")
                res = self.browser.capture_screenshot(path)
                result["success"] = res.success
                result["data"] = res.data
                result["error"] = self._get_error(res)
                if res.success and res.data:
                    self.state.record_screenshot(res.data)

            else:
                # Fallback to invoking method on browser if it exists
                if hasattr(self.browser, action):
                    method = getattr(self.browser, action)
                    res = method(**kwargs)
                    if hasattr(res, "success"):
                        result["success"] = res.success
                        result["data"] = res.data
                        result["error"] = self._get_error(res)
                    else:
                        result["success"] = True
                        result["data"] = res
                else:
                    raise AttributeError(f"Unsupported browser action: {action}")

        except Exception as e:
            logger.error(f"Error executing action '{action}': {e}", exc_info=True)
            result["success"] = False
            result["error"] = str(e)

        # Automatically update state snapshot after action execution
        try:
            self._sync_state(previous_action={"action": action, **kwargs})
        except Exception as e:
            logger.debug(f"Non-fatal error while syncing browser state after action '{action}': {e}")

        return result

    def _sync_state(self, previous_action: Optional[Dict[str, Any]] = None) -> None:
        """Capture live browser snapshot and dispatch state updates via BrowserState."""
        url_res = self.browser.get_current_url()
        url = url_res.data if url_res.success else "about:blank"

        title_res = self.browser.get_page_title()
        title = title_res.data if title_res.success else ""

        html_res = self.browser.get_page_html()
        dom = html_res.data if html_res.success else ""

        snapshot = BrowserStateSnapshot(
            version=self.state.version + 1,
            timestamp=0.0,
            url=url,
            title=title,
            dom_snapshot=dom,
            tabs=list(self.state.tabs) or [url],
            active_tab_index=self.state.active_tab_index,
            cookies=list(self.state.cookies),
            local_storage=dict(self.state.local_storage),
            session_storage=dict(self.state.session_storage),
            scroll_position=dict(self.state.scroll_position),
            focused_element_selector=None,
            detected_forms=[],
            previous_action=previous_action,
        )
        self.state.update_state(snapshot, previous_action=previous_action)

    def close(self) -> None:
        """Close the underlying browser orchestrator."""
        self.browser.close()
