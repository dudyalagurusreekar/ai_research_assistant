"""Workflow Registry storing reusable research templates."""

from typing import Dict, List, Any, Optional
from tools.workflow.interfaces.workflow_interfaces import IWorkflowRegistry
from infrastructure.logging.logger import StructuredLogger


class WorkflowRegistry(IWorkflowRegistry):
    """Registry maintaining reusable research workflow templates (e.g. Deep Research, Code Audit, Literature Review)."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("WorkflowRegistry")
        self._templates: Dict[str, List[Dict[str, Any]]] = {}

        # Register default templates
        self.register_template("deep_research", [
            {
                "title": "Multi-Provider Web & Academic Search",
                "tool_name": "search_tool",
                "action": "search",
                "parameters": {"query": "{objective}"},
            },
            {
                "title": "Ingest Results into Memory",
                "tool_name": "memory_tool",
                "action": "store",
                "parameters": {"content": "Search results for: {objective}"},
                "dependencies": [0],
            },
        ])

        self.register_template("code_audit", [
            {
                "title": "Project Repository Indexing",
                "tool_name": "code_tool",
                "action": "index",
                "parameters": {"root_path": "."},
            },
            {
                "title": "Static Complexity & Security Linting",
                "tool_name": "code_tool",
                "action": "analyze",
                "parameters": {"root_path": "."},
                "dependencies": [0],
            },
        ])

    def register_template(self, name: str, tasks: List[Dict[str, Any]]) -> None:
        """Register a workflow template."""
        self._templates[name.lower()] = tasks
        self._logger.debug(f"Registered workflow template '{name}' ({len(tasks)} tasks)")

    def get_template(self, name: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieve registered template by name."""
        return self._templates.get(name.lower())
