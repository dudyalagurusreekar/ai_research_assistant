"""Smolagents BaseTool wrapper integration for the Browser Tool.

This module exposes the `BrowserTool` class inheriting from `tools.base.BaseTool`,
allowing the Browser orchestrator to be registered in `ToolRegistry`
and used by LLM agents.
"""

import json
from typing import Optional, Any, Dict, List

from tools.base import BaseTool
from tools.browser.core.browser import Browser
from tools.browser.config import BrowserConfig
from tools.browser.constants import BrowserEngineType


class BrowserTool(BaseTool):
    """AI Agent interface wrapper for the Browser Action Engine SDK.

    Inherits from BaseTool to provide structured action APIs for research agents.
    """

    name = "browser_tool"
    description = (
        "Interactive Browser Tool for dynamic, programmatic browser actions. "
        "Allows navigating, clicking, hovering, form filling, selecting checkboxes/dropdowns, "
        "taking screenshots, downloading/uploading files, executing custom scripts, "
        "intercepting network traffic, extracting clean DOM text, managing multiple tabs, "
        "capturing annotated visual state, and performing macro workflows "
        "like search, form filling, article extraction, and login."
    )
    inputs = {
        "action": {
            "type": "string",
            "description": (
                "The browser action to execute. Must be one of: "
                "'plan', 'open_url', 'click', 'double_click', 'hover', 'fill_input', 'type_text', 'clear_input', "
                "'press_key', 'select_dropdown', 'check_checkbox', 'upload_file', 'download_file', "
                "'wait_for_selector', 'wait_for_navigation', 'scroll_page', 'execute_javascript', "
                "'capture_screenshot', 'capture_network_requests', 'capture_console_logs', "
                "'get_current_url', 'get_page_title', 'get_page_html', 'get_clean_text', "
                "'new_tab', 'close_tab', 'switch_tab', 'list_tabs', "
                "'screenshot_annotated', 'visual_state', "
                "'macro_search', 'macro_extract_article', 'macro_fill_form', 'macro_login', "
                "'macro_capture_page', 'macro_navigate_and_read'."
            ),
            "nullable": True,
        },
        "url": {
            "type": "string",
            "description": "URL to navigate to (required for 'open_url' and macro navigation actions).",
            "nullable": True,
        },
        "selector": {
            "type": "string",
            "description": "CSS selector or XPath expression of target DOM element.",
            "nullable": True,
        },
        "text_input": {
            "type": "string",
            "description": "Text to enter (required for 'fill_input').",
            "nullable": True,
        },
        "key": {
            "type": "string",
            "description": "Keyboard key to press (required for 'press_key' - e.g. 'Enter').",
            "nullable": True,
        },
        "checked": {
            "type": "boolean",
            "description": "Checked state for checkbox/radio input (required for 'check_checkbox').",
            "nullable": True,
        },
        "scroll_direction": {
            "type": "string",
            "description": "Scroll direction ('down', 'up', 'top', 'bottom') (required for 'scroll_page').",
            "nullable": True,
        },
        "scroll_amount": {
            "type": "integer",
            "description": "Scroll amount in pixels (optional for 'scroll_page').",
            "nullable": True,
        },
        "extra_args": {
            "type": "string",
            "description": "JavaScript code snippet or extra parameters.",
            "nullable": True,
        },
        "query": {
            "type": "string",
            "description": "Query string to search for (required for 'macro_search').",
            "nullable": True,
        },
        "form_data": {
            "type": "string",
            "description": "JSON string mapping selectors to form input values (required for 'macro_fill_form').",
            "nullable": True,
        },
        "credentials": {
            "type": "string",
            "description": "JSON string representing login credentials mapping selectors to passwords (required for 'macro_login').",
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(
        self,
        config: Optional[BrowserConfig] = None,
        browser: Optional[Browser] = None,
    ) -> None:
        """Initialize BrowserTool wrapper.

        Args:
            config (Optional[BrowserConfig]): Custom browser configuration.
            browser (Optional[Browser]): Injected Browser orchestrator instance.
        """
        super().__init__()
        cfg = config or BrowserConfig(engine_type=BrowserEngineType.PLAYWRIGHT)
        self.browser = browser or Browser(config=cfg)
        from tools.browser.executor import BrowserActionExecutor
        self.executor = BrowserActionExecutor(self.browser)

    def forward(
        self,
        action: Optional[str] = None,
        url: Optional[str] = None,
        selector: Optional[str] = None,
        text_input: Optional[str] = None,
        key: Optional[str] = None,
        checked: Optional[bool] = None,
        scroll_direction: Optional[str] = None,
        scroll_amount: Optional[int] = None,
        extra_args: Optional[str] = None,
        query: Optional[str] = None,
        form_data: Optional[str] = None,
        credentials: Optional[str] = None,
    ) -> str:
        """Execute structured browser SDK action and return serialized ActionResult.

        Args:
            action (Optional[str]): Target action API to invoke.
            url (Optional[str]): Target navigation url.
            selector (Optional[str]): Target DOM selector.
            text_input (Optional[str]): Target text entry value.
            key (Optional[str]): Keyboard key value.
            checked (Optional[bool]): Checkbox checked state.
            scroll_direction (Optional[str]): Scroll direction.
            scroll_amount (Optional[int]): Scroll pixel distance.
            extra_args (Optional[str]): Script string or serializable arguments.
            query (Optional[str]): Query search text.
            form_data (Optional[str]): JSON mapping of form fields.
            credentials (Optional[str]): JSON mapping of credentials.

        Returns:
            str: JSON representation of ActionResult.
        """
        is_legacy = False
        if action is None and url is not None:
            action = "open_url"
            is_legacy = True
        elif action is not None and (action.startswith("http://") or action.startswith("https://") or "://" in action):
            url = action
            action = "open_url"
            is_legacy = True

        if is_legacy:
            if not url:
                return "Error: URL is required."
            response = self.browser.read_page(url)
            if response.extracted_text:
                return response.extracted_text
            return f"Navigated to {url}. Status: {response.status.value} ({response.status_code})"

        if not action:
            return json.dumps({
                "success": False,
                "url": "unknown",
                "title": "",
                "data": None,
                "metrics": None,
                "errors": ["Action argument is required."],
            }, indent=2)

        action_lower = action.strip().lower()

        if action_lower == "plan":
            if not text_input:
                return json.dumps({
                    "success": False,
                    "url": "unknown",
                    "title": "",
                    "data": None,
                    "metrics": None,
                    "errors": ["'text_input' containing the goal instruction is required for action 'plan'."],
                }, indent=2)
            try:
                from tools.browser.planner.planner import BrowserPlanner
                res = BrowserPlanner(self.browser).execute(text_input)
                from tools.browser.serializer import to_json_str
                return to_json_str(res.to_dict(), indent=2)
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "url": "unknown",
                    "title": "",
                    "data": None,
                    "metrics": None,
                    "errors": [f"Plan execution error: {e}"],
                }, indent=2)

        # Route all actions through the middleware executor
        executor_action = {
            "action": action_lower,
            "url": url,
            "selector": selector,
            "text_input": text_input,
            "key": key,
            "checked": checked,
            "scroll_direction": scroll_direction,
            "scroll_amount": scroll_amount,
            "extra_args": extra_args,
            "query": query,
            "form_data": form_data,
            "credentials": credentials,
        }
        return self.executor.execute_to_json(executor_action)
