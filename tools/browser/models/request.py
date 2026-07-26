"""Request Data Models for the Browser Tool.

This module defines DTOs representing requests for browser operations,
navigation actions, and element interactions.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import time

from tools.browser.constants import HttpMethod, BrowserAction
from tools.browser.exceptions import ValidationError


@dataclass
class NavigationParams:
    """Parameters specific to page navigation requests.

    Attributes:
        url (str): Target web page URL.
        method (HttpMethod): HTTP request method (GET, POST, etc.).
        headers (Dict[str, str]): Custom headers for this navigation request.
        timeout (Optional[float]): Custom timeout overriding default config.
        wait_until (str): Loading threshold strategy (e.g. 'domcontentloaded', 'networkidle').
    """

    url: str
    method: HttpMethod = HttpMethod.GET
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: Optional[float] = None
    wait_until: str = "domcontentloaded"

    def validate(self) -> bool:
        """Validate navigation parameters."""
        if not self.url or not isinstance(self.url, str):
            raise ValidationError("Navigation URL must be a non-empty string.")
        if not (self.url.startswith("http://") or self.url.startswith("https://")):
            raise ValidationError(f"Invalid URL protocol: '{self.url}'. Must start with http:// or https://")
        return True


@dataclass
class ActionParams:
    """Parameters specific to interactive browser actions (click, type, scroll).

    Attributes:
        action (BrowserAction): Type of browser action to perform.
        selector (Optional[str]): CSS or XPath selector of target DOM element.
        text_input (Optional[str]): Text string to insert for TYPE actions.
        scroll_offset (Optional[int]): Pixel offset for SCROLL actions.
        extra_args (Dict[str, Any]): Additional action-specific metadata.
    """

    action: BrowserAction
    selector: Optional[str] = None
    text_input: Optional[str] = None
    scroll_offset: Optional[int] = None
    extra_args: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """Validate action parameters based on action type."""
        if self.action in (BrowserAction.CLICK, BrowserAction.TYPE, BrowserAction.EXTRACT):
            if not self.selector:
                raise ValidationError(f"Action '{self.action.value}' requires a target selector.")
        if self.action == BrowserAction.TYPE and self.text_input is None:
            raise ValidationError("Action 'TYPE' requires text_input string.")
        return True


@dataclass
class BrowserRequest:
    """Unified request model encapsulating navigation or interaction requests.

    Attributes:
        request_id (str): Unique tracking identifier for this request.
        navigation (Optional[NavigationParams]): Navigation payload if this is a navigation request.
        action (Optional[ActionParams]): Action payload if this is an interactive request.
        timestamp (float): UNIX timestamp when request was constructed.
    """

    request_id: str
    navigation: Optional[NavigationParams] = None
    action: Optional[ActionParams] = None
    timestamp: float = field(default_factory=time.time)

    def validate(self) -> bool:
        """Validate overall browser request."""
        if not self.request_id:
            raise ValidationError("BrowserRequest must have a valid request_id.")
        if not self.navigation and not self.action:
            raise ValidationError("BrowserRequest must specify either navigation or action params.")
        if self.navigation:
            self.navigation.validate()
        if self.action:
            self.action.validate()
        return True
