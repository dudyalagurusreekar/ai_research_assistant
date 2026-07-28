"""Capability Router for selecting suitable tools without executing them."""

import logging
from typing import Optional
from core.interfaces.registry import IRegistry
from core.interfaces.router import IRouter, RoutingDecision
from core.models.request import Request

logger = logging.getLogger("Core.CapabilityRouter")


class CapabilityRouter(IRouter):
    """Evaluates requests against registered capabilities and returns routing decisions."""

    def __init__(self, registry: IRegistry) -> None:
        """Initialize router with a target CapabilityRegistry instance."""
        self._registry = registry
        self._logger = logger

    def route(self, request: Request) -> Optional[RoutingDecision]:
        """Evaluate request intent and parameters to select the optimal tool capability.

        Does NOT execute the tool. Returns a pure RoutingDecision.

        Args:
            request: Unified request model.

        Returns:
            RoutingDecision if a matching tool is found, else None.
        """
        intent = request.intent.lower().strip()
        requested_tool = request.parameters.get("tool_name") or request.metadata.get("target_tool")

        # 1. Exact tool name match
        if requested_tool:
            tool = self._registry.get_tool(str(requested_tool))
            if tool and tool.metadata.enabled:
                self._logger.info(f"Routed request '{request.request_id}' to tool '{tool.metadata.name}' via explicit match.")
                return RoutingDecision(
                    tool_name=tool.metadata.name,
                    capability=tool.metadata.capabilities[0] if tool.metadata.capabilities else "general",
                    confidence=1.0,
                    reason=f"Explicit target tool match for '{requested_tool}'.",
                )

        # 2. Match tools by capability keyword in intent
        tools = self._registry.list_tools()
        best_tool_name: Optional[str] = None
        best_capability: str = "general"
        highest_confidence: float = 0.0
        best_reason: str = ""

        for meta in tools:
            if not meta.enabled:
                continue

            # Direct match with tool name or capability tags
            if meta.name.lower() in intent:
                best_tool_name = meta.name
                best_capability = meta.capabilities[0] if meta.capabilities else "general"
                highest_confidence = 0.95
                best_reason = f"Intent matches tool name '{meta.name}'."
                break

            for cap in meta.capabilities:
                if cap.lower() in intent:
                    best_tool_name = meta.name
                    best_capability = cap
                    highest_confidence = 0.85
                    best_reason = f"Intent matches capability '{cap}'."
                    break

        if best_tool_name:
            self._logger.info(f"Routed request '{request.request_id}' to tool '{best_tool_name}' (Confidence: {highest_confidence}).")
            return RoutingDecision(
                tool_name=best_tool_name,
                capability=best_capability,
                confidence=highest_confidence,
                reason=best_reason,
            )

        self._logger.warning(f"No suitable tool found for request '{request.request_id}' (Intent: '{request.intent}').")
        return None
