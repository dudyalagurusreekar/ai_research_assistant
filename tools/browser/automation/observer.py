"""Observer Pattern Implementation for Event & Network Monitoring.

This module implements `NetworkObserver`, allowing the browser automation engine
to attach listeners to browser page events, capturing HTTP network traffic,
console logs, page errors, and JavaScript dialog interactions.
"""

from typing import List, Dict, Any, Optional
from tools.browser.automation.models import NetworkRequestLog, NetworkResponseLog, DialogLog
from tools.browser.utils.logging import get_browser_logger


class NetworkObserver:
    """Observer collecting real-time network traffic, console output, and dialog events."""

    def __init__(self) -> None:
        """Initialize empty observer event storage lists."""
        self.requests: List[NetworkRequestLog] = []
        self.responses: List[NetworkResponseLog] = []
        self.dialogs: List[DialogLog] = []
        self.console_logs: List[Dict[str, Any]] = []
        self.page_errors: List[str] = []
        self._logger = get_browser_logger("NetworkObserver")

    def record_request(self, request_log: NetworkRequestLog) -> None:
        """Record an outbound HTTP request."""
        self.requests.append(request_log)
        self._logger.debug(f"[Request] {request_log.method} {request_log.url}")

    def record_response(self, response_log: NetworkResponseLog) -> None:
        """Record an inbound HTTP response."""
        self.responses.append(response_log)
        self._logger.debug(f"[Response] {response_log.status} {response_log.url}")

    def record_dialog(self, dialog_log: DialogLog) -> None:
        """Record a JavaScript dialog event (alert, confirm, prompt)."""
        self.dialogs.append(dialog_log)
        self._logger.info(f"[Dialog] {dialog_log.type}: {dialog_log.message} -> {dialog_log.action_taken}")

    def record_console(self, type_: str, text: str, location: Optional[str] = None) -> None:
        """Record a browser console message."""
        entry = {"type": type_, "text": text, "location": location}
        self.console_logs.append(entry)

    def record_page_error(self, error_msg: str) -> None:
        """Record an unhandled JavaScript window exception."""
        self.page_errors.append(error_msg)
        self._logger.warning(f"[PageError] {error_msg}")

    def get_summary(self) -> Dict[str, Any]:
        """Return aggregated summary dictionary of all captured events."""
        return {
            "request_count": len(self.requests),
            "response_count": len(self.responses),
            "dialog_count": len(self.dialogs),
            "console_count": len(self.console_logs),
            "error_count": len(self.page_errors),
            "requests": self.requests,
            "responses": self.responses,
            "dialogs": self.dialogs,
            "console_logs": self.console_logs,
            "page_errors": self.page_errors,
        }

    def clear(self) -> None:
        """Clear recorded events log."""
        self.requests.clear()
        self.responses.clear()
        self.dialogs.clear()
        self.console_logs.clear()
        self.page_errors.clear()
