"""Data Models for the Browser Tool.

This package contains strongly typed data transfer objects (DTOs) and domain
models representing requests, responses, and page states.
"""

from tools.browser.models.request import (
    BrowserRequest,
    NavigationParams,
    ActionParams,
)
from tools.browser.models.response import (
    BrowserResponse,
    PageMetadata,
    PerformanceMetrics,
    FetchResult,
    ActionResult,
    ActionMetrics,
)
from tools.browser.models.page import (
    PageState,
    ElementNode,
    LinkInfo,
    FormInfo,
)

__all__ = [
    "BrowserRequest",
    "NavigationParams",
    "ActionParams",
    "BrowserResponse",
    "PageMetadata",
    "PerformanceMetrics",
    "FetchResult",
    "ActionResult",
    "ActionMetrics",
    "PageState",
    "ElementNode",
    "LinkInfo",
    "FormInfo",
]
