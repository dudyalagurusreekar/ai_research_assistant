"""Unit tests for Capability Registry."""

import unittest
from typing import Any, Dict
from core.registry import CapabilityRegistry
from core.interfaces.tool import ITool
from core.models import ToolMetadata, ToolResult
from core.exceptions import CapabilityError


class DummyTool(ITool):
    def __init__(self, name: str, capabilities: list) -> None:
        self._meta = ToolMetadata(
            name=name,
            version="1.0.0",
            description=f"Dummy tool {name}",
            capabilities=capabilities,
        )

    @property
    def metadata(self) -> ToolMetadata:
        return self._meta

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        return ToolResult(tool_name=self.metadata.name, success=True, data={"dummy": True})


class TestCapabilityRegistry(unittest.TestCase):
    """Test tool registration, duplicate prevention, and capability discovery."""

    def test_register_and_lookup_tool(self):
        registry = CapabilityRegistry()
        tool1 = DummyTool("search_tool", ["search", "web"])
        registry.register_tool(tool1)

        retrieved = registry.get_tool("search_tool")
        self.assertIs(retrieved, tool1)

        # Test duplicate registration error
        with self.assertRaises(CapabilityError):
            registry.register_tool(tool1)

    def test_find_by_capability(self):
        registry = CapabilityRegistry()
        tool1 = DummyTool("search_tool", ["search", "web"])
        tool2 = DummyTool("pdf_reader", ["pdf", "files"])

        registry.register_tool(tool1)
        registry.register_tool(tool2)

        web_tools = registry.find_by_capability("web")
        self.assertEqual(len(web_tools), 1)
        self.assertEqual(web_tools[0].metadata.name, "search_tool")


if __name__ == "__main__":
    unittest.main()
