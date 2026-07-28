"""Interface for capability and tool registration/lookup."""

from abc import ABC, abstractmethod
from typing import List, Optional
from core.interfaces.tool import ITool
from core.models.metadata import ToolMetadata


class IRegistry(ABC):
    """Abstract Interface for capability registration and discovery."""

    @abstractmethod
    def register_tool(self, tool: ITool) -> None:
        """Register a tool instance."""

    @abstractmethod
    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool by name."""

    @abstractmethod
    def get_tool(self, name: str) -> Optional[ITool]:
        """Retrieve tool by name."""

    @abstractmethod
    def list_tools(self) -> List[ToolMetadata]:
        """List metadata of all registered tools."""

    @abstractmethod
    def find_by_capability(self, capability: str) -> List[ITool]:
        """Find tools supporting a specific capability string."""
