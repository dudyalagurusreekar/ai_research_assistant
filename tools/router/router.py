"""Capability-Based Tool Router (`tools/router/router.py`).

Provides a lightweight routing layer so the planner can dispatch intents across
multiple tool capabilities (Browser, Files, Code, Search, API, Memory) rather
than assuming all operations require browser automation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import logging

logger = logging.getLogger("ToolRouter")


class ToolCapability(Enum):
    """Supported tool domain capabilities."""

    BROWSER = "browser"
    FILES = "files"
    CODE = "code"
    SEARCH = "search"
    API = "api"
    MEMORY = "memory"
    CALCULATOR = "calculator"


@dataclass
class ToolRouteResult:
    """Resolution of an intent to a target tool capability and handler."""

    tool_name: str
    capability: ToolCapability
    description: str
    handler: Optional[Callable] = None


class ToolRouter:
    """Lightweight capability-based tool router for AI agents.

    Allows planners to register tool handlers by capability and route queries or
    sub-tasks to the appropriate tool (e.g., local files vs. browser vs. code execution).
    """

    def __init__(self) -> None:
        self.registry: Dict[str, ToolRouteResult] = {}
        self.capabilities_map: Dict[ToolCapability, List[str]] = {
            cap: [] for cap in ToolCapability
        }
        self._logger = logger

    def register_tool(
        self,
        name: str,
        capability: ToolCapability,
        handler: Callable,
        description: str,
    ) -> None:
        """Register a tool with its capability domain and handler function."""
        route = ToolRouteResult(
            tool_name=name,
            capability=capability,
            description=description,
            handler=handler,
        )
        self.registry[name] = route
        self.capabilities_map[capability].append(name)
        self._logger.debug(f"Registered tool '{name}' under capability '{capability.value}'.")

    def route_by_name(self, name: str) -> Optional[ToolRouteResult]:
        """Lookup a registered tool route by name."""
        return self.registry.get(name)

    def route_by_capability(self, capability: ToolCapability) -> List[ToolRouteResult]:
        """Return all registered tools matching a capability domain."""
        names = self.capabilities_map.get(capability, [])
        return [self.registry[n] for n in names if n in self.registry]

    def resolve_intent(self, prompt_or_action: str) -> Optional[ToolRouteResult]:
        """Heuristically resolve a prompt or action intent to a tool capability.

        Args:
            prompt_or_action (str): Intent string or action name.

        Returns:
            Optional[ToolRouteResult]: Best matching tool route.
        """
        lower = prompt_or_action.lower().strip()

        # Check explicit tool names first
        if lower in self.registry:
            return self.registry[lower]

        # Check file operation keywords
        if any(kw in lower for kw in ["file", "read file", "pdf", "disk", ".txt", ".pdf"]):
            routes = self.route_by_capability(ToolCapability.FILES)
            if routes:
                return routes[0]

        # Check search keywords
        if any(kw in lower for kw in ["search", "google", "query"]):
            routes = self.route_by_capability(ToolCapability.SEARCH)
            if routes:
                return routes[0]

        # Check math/calculator keywords
        if any(kw in lower for kw in ["calculate", "math", "+", "-", "*", "/"]):
            routes = self.route_by_capability(ToolCapability.CALCULATOR)
            if routes:
                return routes[0]

        # Default fallback to browser capability if available
        routes = self.route_by_capability(ToolCapability.BROWSER)
        return routes[0] if routes else None

    def execute_route(self, route: ToolRouteResult, **kwargs: Any) -> Any:
        """Execute the handler associated with a resolved tool route."""
        if not route.handler:
            raise ValueError(f"Tool route '{route.tool_name}' has no registered handler.")
        self._logger.info(f"Routing execution to capability '{route.capability.value}' ({route.tool_name})")
        return route.handler(**kwargs)
