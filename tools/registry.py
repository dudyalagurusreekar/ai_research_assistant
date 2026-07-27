from typing import List

from smolagents import Tool

# Core Tools
from tools.core import CalculatorTool

# Web Tools
from tools.web import (
    WebSearchTool,
    WebPageReaderTool,
)
from tools.browser import BrowserTool

# File Tools
from tools.file import (
    FileReaderTool,
    PdfReaderTool,
)

# Document Tools
from tools.document.tool import DocumentTool

# Search & Knowledge Tools
from tools.search.tool import SearchTool

# Memory Tools
from tools.memory.tool import MemoryTool

# Code Tools
from tools.code.tool import CodeTool

# Vision Tools
from tools.vision.tool import VisionTool

# Integration Tools
from tools.integration.tool import IntegrationTool

# Workflow Engine Tools
from tools.workflow.tool import WorkflowTool

# Report Generation Tools
from tools.report.tool import ReportTool

# GAIA Benchmark Tools
from tools.benchmark.tool import BenchmarkTool

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
registry.register(BrowserTool())
registry.register(FileReaderTool())
registry.register(PdfReaderTool())
registry.register(ResearchTool())
registry.register(DocumentTool())
registry.register(SearchTool())
registry.register(MemoryTool())
registry.register(CodeTool())
registry.register(VisionTool())
registry.register(IntegrationTool())
registry.register(WorkflowTool())
registry.register(ReportTool())
registry.register(BenchmarkTool())


