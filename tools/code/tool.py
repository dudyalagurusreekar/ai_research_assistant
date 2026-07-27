"""Smolagents Tool wrapper for the Code Intelligence Platform."""

from smolagents import Tool
from tools.code.facade.facade import CodeToolFacade


class CodeTool(Tool):
    """Tool wrapper exposing CodeToolFacade capabilities to smolagents."""

    name = "code_tool"
    description = "Unified software engineering tool for repository indexing, symbol resolution, static analysis, sandboxed execution, and doc generation."
    inputs = {
        "action": {
            "type": "string",
            "description": "Action to perform: 'index', 'symbols', 'dependencies', 'analyze', 'execute', or 'docs'",
            "nullable": True,
        },
        "root_path": {
            "type": "string",
            "description": "Directory or repository root path",
            "nullable": True,
        },
        "code": {
            "type": "string",
            "description": "Code snippet string for execution",
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(self, facade: CodeToolFacade = None):
        super().__init__()
        self._facade = facade or CodeToolFacade()

    def forward(self, action: str = "index", root_path: str = ".", code: str = "") -> str:
        import asyncio
        return asyncio.run(self._facade.forward(action=action, root_path=root_path, code=code))
