"""Smolagents Tool wrapper for the Research Workflow Engine."""

from smolagents import Tool
from tools.workflow.facade.facade import WorkflowEngineFacade


class WorkflowTool(Tool):
    """Tool wrapper exposing WorkflowEngineFacade capabilities to smolagents."""

    name = "workflow_tool"
    description = "Central orchestration engine for planning, scheduling, state checkpointing, and executing complex research workflows."
    inputs = {
        "action": {
            "type": "string",
            "description": "Action to perform: 'create', 'run', 'pause', 'resume', or 'status'",
            "nullable": True,
        },
        "objective": {
            "type": "string",
            "description": "High-level research objective string",
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(self, facade: WorkflowEngineFacade = None):
        super().__init__()
        self._facade = facade or WorkflowEngineFacade()

    def forward(self, action: str = "create", objective: str = "") -> str:
        import asyncio
        return asyncio.run(self._facade.forward(action=action, objective=objective))
