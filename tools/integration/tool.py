"""Smolagents Tool wrapper for the External Integration Platform."""

from smolagents import Tool
from tools.integration.facade.facade import IntegrationToolFacade


class IntegrationTool(Tool):
    """Tool wrapper exposing IntegrationToolFacade capabilities to smolagents."""

    name = "integration_tool"
    description = "Unified connectivity tool for external REST APIs, GraphQL, MCP servers, authentication, and third-party integrations."
    inputs = {
        "action": {
            "type": "string",
            "description": "Action to perform: 'rest', 'graphql', 'mcp', 'health', or 'list_connectors'",
            "nullable": True,
        },
        "endpoint": {
            "type": "string",
            "description": "Target endpoint URL or tool name",
            "nullable": True,
        },
        "method": {
            "type": "string",
            "description": "HTTP method or query type",
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(self, facade: IntegrationToolFacade = None):
        super().__init__()
        self._facade = facade or IntegrationToolFacade()

    def forward(self, action: str = "rest", endpoint: str = "", method: str = "GET") -> str:
        import asyncio
        return asyncio.run(self._facade.forward(action=action, endpoint=endpoint, method=method))
