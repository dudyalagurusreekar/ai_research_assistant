from typing import List

from smolagents import Tool

# Core Tools
from tools.core import CalculatorTool

# Web Tools
from tools.web import (
    WebSearchTool,
    WebPageReaderTool,
)

# File Tools
from tools.file import (
    FileReaderTool,
    PdfReaderTool,
)

# Research Tools
from tools.research import ResearchTool


class ToolRegistry:
    """
    Central registry for all tools used by the AI Research Assistant.
    """

    def __init__(self):
        self._tools: List[Tool] = []

    def register(self, tool: Tool):
        """Register a tool only once."""
        if not any(type(t) == type(tool) for t in self._tools):
            self._tools.append(tool)

    def get_tools(self) -> List[Tool]:
        """Return all registered tools."""
        return self._tools

    def list_tools(self) -> List[str]:
        """Return tool names."""
        return [tool.name for tool in self._tools]


# --------------------------------------------------
# Global Registry
# --------------------------------------------------

registry = ToolRegistry()

# ---------------- Register Tools ----------------

registry.register(CalculatorTool())
registry.register(WebSearchTool())
registry.register(WebPageReaderTool())
registry.register(FileReaderTool())
registry.register(PdfReaderTool())
registry.register(ResearchTool())
