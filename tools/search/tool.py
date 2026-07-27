"""Smolagents Tool wrapper for Search & Knowledge Platform."""

from smolagents import Tool
from tools.search.facade.facade import SearchToolFacade


class SearchTool(Tool):
    """Tool wrapper exposing SearchToolFacade capabilities to smolagents."""

    name = "search_tool"
    description = "Unified search tool for multi-provider web, academic, github, and document knowledge discovery."
    inputs = {
        "action": {
            "type": "string",
            "description": "Action to perform: 'search', 'fetch', or 'local_search'",
            "nullable": True,
        },
        "query": {
            "type": "string",
            "description": "Search query string",
            "nullable": True,
        },
        "url": {
            "type": "string",
            "description": "URL or document path to fetch",
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(self, facade: SearchToolFacade = None):
        super().__init__()
        self._facade = facade or SearchToolFacade()

    def forward(self, action: str = "search", query: str = "", url: str = "") -> str:
        import asyncio
        return asyncio.run(self._facade.forward(action=action, query=query, url=url))
