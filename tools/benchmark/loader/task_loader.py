"""GAIA Task Loader loading benchmark tasks across Levels 1, 2, and 3."""

from typing import List, Optional
from tools.benchmark.interfaces.benchmark_interfaces import ITaskLoader
from tools.benchmark.models.benchmark_models import GAIATask, TaskLevel, TaskCategory
from infrastructure.logging.logger import StructuredLogger


class TaskLoader(ITaskLoader):
    """Loads GAIA benchmark task instances categorized by Level 1, 2, and 3."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("TaskLoader")
        self._tasks: List[GAIATask] = [
            GAIATask(
                question="What is the title of the 2021 quantum computing paper by Google Quantum AI?",
                level=TaskLevel.LEVEL_1,
                category=TaskCategory.WEB_RESEARCH,
                ground_truth="Quantum supremacy using a programmable superconducting processor",
            ),
            GAIATask(
                question="Calculate the total lines of code and function count in the provided project directory.",
                level=TaskLevel.LEVEL_2,
                category=TaskCategory.CODE_EXECUTION,
                ground_truth="Total Files: 5, Total Lines: 450",
            ),
            GAIATask(
                question="Extract all bar chart data points from the screenshot and summarize in JSON.",
                level=TaskLevel.LEVEL_3,
                category=TaskCategory.MULTIMODAL_VISION,
                ground_truth="{'Baseline': 78.5, 'Proposed': 94.2}",
            ),
        ]

    def load_tasks(self, level: Optional[TaskLevel] = None) -> List[GAIATask]:
        """Return tasks filtered by level or all tasks."""
        if level:
            filtered = [t for t in self._tasks if t.level == level]
            self._logger.info(f"Loaded {len(filtered)} GAIA tasks for level '{level.value}'")
            return filtered
        self._logger.info(f"Loaded {len(self._tasks)} total GAIA tasks across all levels.")
        return list(self._tasks)
