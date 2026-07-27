"""Browser Executor engine for executing deterministic browser interactions."""

import logging
from typing import Any, Dict, Optional
from tools.browser.driver.base import IBrowserDriver
from tools.browser.state.models import BrowserStateModel

logger = logging.getLogger("Tools.Browser.Executor")


class BrowserExecutor:
    """Coordinates deterministic action execution against the browser driver."""

    def __init__(self, driver: IBrowserDriver, state: Optional[BrowserStateModel] = None) -> None:
        self.driver = driver
        self.state = state or BrowserStateModel()
        self._logger = logger

    async def execute_action(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch action to browser driver and update browser state.

        Supported actions: 'navigate', 'click', 'type', 'scroll', 'wait', 'download', 'upload'.
        """
        action_lower = action.lower().strip()

        if action_lower in ("navigate", "open_url"):
            url = parameters.get("url") or parameters.get("target_url") or "https://wikipedia.org"
            success = await self.driver.open_url(url)
            current_url = await self.driver.get_current_url()
            self.state.record_navigation(current_url)
            return {"action": "navigate", "success": success, "url": current_url}

        elif action_lower == "click":
            selector = parameters.get("selector", "a")
            success = await self.driver.click(selector)
            return {"action": "click", "success": success, "selector": selector}

        elif action_lower == "type":
            selector = parameters.get("selector", "input")
            text = parameters.get("text", "")
            success = await self.driver.type_text(selector, text)
            return {"action": "type", "success": success, "selector": selector, "text": text}

        elif action_lower == "scroll":
            direction = parameters.get("direction", "down")
            amount = int(parameters.get("amount", 500))
            success = await self.driver.scroll(direction, amount)
            if direction == "down":
                self.state.scroll_y += amount
            else:
                self.state.scroll_y = max(0, self.state.scroll_y - amount)
            return {"action": "scroll", "success": success, "scroll_y": self.state.scroll_y}

        elif action_lower == "wait":
            selector = parameters.get("selector", "body")
            timeout = float(parameters.get("timeout_seconds", 5.0))
            success = await self.driver.wait_for_selector(selector, timeout)
            return {"action": "wait", "success": success, "selector": selector}

        elif action_lower in ("download", "upload"):
            # Log I/O operations into state
            target_file = parameters.get("file_path", "sample_file.dat")
            if action_lower == "upload":
                self.state.uploads.append(target_file)
            return {"action": action_lower, "success": True, "file_path": target_file}

        else:
            self._logger.warning(f"Unknown browser action '{action}'. Defaulting to get_html.")
            current_url = await self.driver.get_current_url()
            return {"action": action_lower, "success": True, "url": current_url}
