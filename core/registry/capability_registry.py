"""Capability Registry for registering, storing, and discovering platform tools."""

import logging
from typing import Dict, List, Optional
from core.interfaces.registry import IRegistry
from core.interfaces.tool import ITool
from core.models.metadata import ToolMetadata
from core.exceptions.base import CapabilityError
from core.exceptions.codes import ErrorCode

logger = logging.getLogger("Core.CapabilityRegistry")


class CapabilityRegistry(IRegistry):
    """Central registry for discovering available tools and supporting future plugin extensions."""

    def __init__(self) -> None:
        self._tools: Dict[str, ITool] = {}
        self._logger = logger

    def register_tool(self, tool: ITool) -> None:
        """Register a tool instance.

        Args:
            tool: Object implementing ITool interface.

        Raises:
            CapabilityError: If a tool with the same name is already registered or metadata is invalid.
        """
        if not tool or not hasattr(tool, "metadata") or not tool.metadata:
            raise CapabilityError("Invalid tool: tool metadata missing.", code=ErrorCode.CAPABILITY_INVALID)

        name = tool.metadata.name
        if not name:
            raise CapabilityError("Tool metadata must specify a valid name.", code=ErrorCode.CAPABILITY_INVALID)

        if name in self._tools:
            raise CapabilityError(
                f"Tool '{name}' is already registered in registry.",
                code=ErrorCode.CAPABILITY_ALREADY_REGISTERED,
            )

        self._tools[name] = tool
        self._logger.info(f"Registered tool capability '{name}' v{tool.metadata.version}.")

    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool by name.

        Args:
            name: Tool name string.

        Returns:
            True if tool was removed, False if not found.
        """
        if name in self._tools:
            del self._tools[name]
            self._logger.info(f"Unregistered tool capability '{name}'.")
            return True
        return False

    def get_tool(self, name: str) -> Optional[ITool]:
        """Retrieve a tool instance by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[ToolMetadata]:
        """List metadata of all registered tools."""
        return [tool.metadata for tool in self._tools.values() if tool.metadata.enabled]

    def find_by_capability(self, capability: str) -> List[ITool]:
        """Find all registered tools matching a capability string (case-insensitive)."""
        cap_lower = capability.lower().strip()
        matched: List[ITool] = []

        for tool in self._tools.values():
            if not tool.metadata.enabled:
                continue
            tool_caps = [c.lower() for c in tool.metadata.capabilities]
            if cap_lower in tool_caps or cap_lower == tool.metadata.name.lower():
                matched.append(tool)

        return matched

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
