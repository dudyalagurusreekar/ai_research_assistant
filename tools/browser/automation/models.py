"""Data Models and DTOs for the Browser Automation Engine.

This module defines structures for network logs, element properties,
dialog operations, and authenticated session state persistence.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class NetworkRequestLog:
    """Captured details of an intercepted HTTP request."""
    url: str
    method: str
    headers: Dict[str, str] = field(default_factory=dict)
    post_data: Optional[str] = None
    resource_type: str = "document"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "method": self.method,
            "headers": self.headers,
            "post_data": self.post_data,
            "resource_type": self.resource_type,
        }


@dataclass
class NetworkResponseLog:
    """Captured details of an intercepted HTTP response."""
    url: str
    status: int
    headers: Dict[str, str] = field(default_factory=dict)
    mime_type: str = "text/html"
    body_length: int = 0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "status": self.status,
            "headers": self.headers,
            "mime_type": self.mime_type,
            "body_length": self.body_length,
            "error": self.error,
        }


@dataclass
class DialogLog:
    """Captured details of a JavaScript dialog window."""
    type: str  # alert, confirm, prompt
    message: str
    default_value: Optional[str] = None
    action_taken: str = "dismissed"  # accepted or dismissed
    user_input: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "message": self.message,
            "default_value": self.default_value,
            "action_taken": self.action_taken,
            "user_input": self.user_input,
        }


@dataclass
class ElementSpec:
    """Properties and state of a DOM element."""
    selector: str
    tag_name: str
    text: str = ""
    attributes: Dict[str, str] = field(default_factory=dict)
    is_visible: bool = False
    is_enabled: bool = False
    is_editable: bool = False


@dataclass
class SessionState:
    """State containing cookies and local storage for authentication persistence."""
    cookies: List[Dict[str, Any]] = field(default_factory=list)
    origins: List[Dict[str, Any]] = field(default_factory=list)  # localStorage / sessionStorage
