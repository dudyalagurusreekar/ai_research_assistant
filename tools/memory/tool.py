"""Smolagents Tool wrapper for the Memory Platform."""

from smolagents import Tool
from tools.memory.facade.facade import MemoryToolFacade


class MemoryTool(Tool):
    """Tool wrapper exposing MemoryToolFacade capabilities to smolagents."""

    name = "memory_tool"
    description = "Centralized persistent memory tool for knowledge storage, retrieval, graph linking, and consolidation."
    inputs = {
        "action": {
            "type": "string",
            "description": "Action to perform: 'remember', 'recall', 'link', or 'consolidate'",
            "nullable": True,
        },
        "content": {
            "type": "string",
            "description": "Memory text content to remember",
            "nullable": True,
        },
        "query": {
            "type": "string",
            "description": "Search query text for memory recall",
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(self, facade: MemoryToolFacade = None):
        super().__init__()
        self._facade = facade or MemoryToolFacade()

    def forward(self, action: str = "recall", content: str = "", query: str = "") -> str:
        import asyncio
        return asyncio.run(self._facade.forward(action=action, content=content, query=query))
