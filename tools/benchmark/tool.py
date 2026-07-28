"""Smolagents Tool wrapper for the GAIA Benchmark Framework."""

import asyncio
from typing import Optional
from smolagents import Tool
from tools.benchmark.facade.facade import BenchmarkToolFacade


class BenchmarkTool(Tool):
    """Tool wrapper exposing BenchmarkToolFacade capabilities to smolagents."""

    name = "benchmark_tool"
    description = "Unified benchmark tool executing GAIA tasks, trace scoring, failure analysis, submission generation, and performance optimization."
    inputs = {
        "action": {
            "type": "string",
            "description": "Action to perform: 'run_suite', 'score', 'list_tasks', 'validate_dataset', 'generate_report', 'list_suites'",
            "nullable": True,
        },
        "level": {
            "type": "string",
            "description": "GAIA task level: 'level_1', 'level_2', or 'level_3'",
            "nullable": True,
        },
        "suite_id": {
            "type": "string",
            "description": "Benchmark suite ID (e.g. 'gaia', 'swe_bench')",
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(self, facade: Optional[BenchmarkToolFacade] = None):
        super().__init__()
        self._facade = facade or BenchmarkToolFacade()

    def forward(self, action: str = "run_suite", level: Optional[str] = None, suite_id: Optional[str] = None) -> str:
        """Synchronous wrapper for smolagents forward call."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # If event loop is already running, run in a separate task or thread
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(self._facade.forward(action=action, level=level, suite_id=suite_id))
        else:
            return loop.run_until_complete(self._facade.forward(action=action, level=level, suite_id=suite_id))
