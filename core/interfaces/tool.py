"""Interface contract for tools and capabilities."""

from abc import ABC, abstractmethod
from typing import Any, Dict
from core.models.metadata import ToolMetadata
from core.models.tool_result import ToolResult


class ITool(ABC):
    """Abstract Interface that all platform tools must implement."""

    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """Return the metadata descriptor for this tool."""

    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute tool logic asynchronously with parameters.

        Args:
            parameters: Parameter dictionary conforming to parameters_schema.

        Returns:
            ToolResult encapsulating output and artifacts.
        """
