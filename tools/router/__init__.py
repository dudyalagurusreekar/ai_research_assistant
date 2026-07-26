"""Capability-Based Tool Router package (`tools/router/`).

Provides ToolRouter, ToolCapability, and ToolRouteResult for routing agent
intents across Browser, Files, Code, Search, API, and Memory capabilities.
"""

from tools.router.router import (
    ToolRouter,
    ToolCapability,
    ToolRouteResult,
)

__all__ = [
    "ToolRouter",
    "ToolCapability",
    "ToolRouteResult",
]
