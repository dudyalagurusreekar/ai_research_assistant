"""Smolagents Tool wrapper for the GAIA Benchmark Framework."""

from smolagents import Tool
from tools.benchmark.facade.facade import BenchmarkToolFacade


class BenchmarkTool(Tool):
    """Tool wrapper exposing BenchmarkToolFacade capabilities to smolagents."""

    name = "benchmark_tool"
    description = "Unified benchmark evaluation tool for executing GAIA tasks, trace scoring, error analysis, and performance optimization."
    inputs = {
        "action": {
            "type": "string",
            "description": "Action to perform: 'run_suite', 'score', or 'list_tasks'",
            "nullable": True,
        },
        "level": {
            "type": "string",
            "description": "GAIA task level: 'level_1', 'level_2', or 'level_3'",
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(self, facade: BenchmarkToolFacade = None):
        super().__init__()
        self._facade = facade or BenchmarkToolFacade()

    def forward(self, action: str = "run_suite", level: str = None) -> str:
        import asyncio
        return asyncio.run(self._facade.forward(action=action, level=level))
