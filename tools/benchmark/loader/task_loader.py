"""GAIA Task Loader supporting dataset loading, integrity validation, and attachment verification."""

import os
import json
from typing import List, Optional, Dict, Any
from tools.benchmark.interfaces.benchmark_interfaces import ITaskLoader
from tools.benchmark.models.benchmark_models import (
    GAIATask,
    TaskLevel,
    TaskCategory,
    DatasetIntegrityResult,
)
from infrastructure.logging.logger import StructuredLogger


class TaskLoader(ITaskLoader):
    """Loads GAIA and custom benchmark datasets from memory, JSON, or JSONL files with integrity validation."""

    def __init__(self, data_directory: Optional[str] = None) -> None:
        self._logger = StructuredLogger("TaskLoader")
        self._data_dir = data_directory or os.path.join(os.getcwd(), "data", "benchmarks")
        self._default_tasks: List[GAIATask] = [
            GAIATask(
                task_id="gaia_level1_001",
                question="What is the title of the 2021 quantum computing paper by Google Quantum AI?",
                level=TaskLevel.LEVEL_1,
                category=TaskCategory.WEB_RESEARCH,
                ground_truth="Quantum supremacy using a programmable superconducting processor",
                file_attachments=[],
                metadata={"suite": "gaia", "source": "public_dev"},
            ),
            GAIATask(
                task_id="gaia_level2_001",
                question="Calculate the total lines of code and function count in the provided project directory.",
                level=TaskLevel.LEVEL_2,
                category=TaskCategory.CODE_EXECUTION,
                ground_truth="Total Files: 5, Total Lines: 450",
                file_attachments=[],
                metadata={"suite": "gaia", "source": "public_dev"},
            ),
            GAIATask(
                task_id="gaia_level3_001",
                question="Extract all bar chart data points from the screenshot and summarize in JSON.",
                level=TaskLevel.LEVEL_3,
                category=TaskCategory.MULTIMODAL_VISION,
                ground_truth="{'Baseline': 78.5, 'Proposed': 94.2}",
                file_attachments=[],
                metadata={"suite": "gaia", "source": "public_dev"},
            ),
        ]

    def load_tasks(
        self,
        level: Optional[TaskLevel] = None,
        suite_id: str = "gaia",
        dataset_path: Optional[str] = None,
    ) -> List[GAIATask]:
        """Load benchmark tasks filtered by level, suite_id, or custom dataset path."""
        tasks: List[GAIATask] = []

        if dataset_path and os.path.exists(dataset_path):
            tasks = self._load_from_file(dataset_path)
        else:
            # Fallback to checking default suite path or default in-memory tasks
            file_name = f"{suite_id}_dataset.jsonl" if suite_id else "gaia_dataset.jsonl"
            target_path = os.path.join(self._data_dir, file_name)
            if os.path.exists(target_path):
                tasks = self._load_from_file(target_path)
            else:
                tasks = list(self._default_tasks)

        # Filter by level if specified
        if level:
            target_lvl_val = level.value if isinstance(level, TaskLevel) else str(level)
            filtered = [
                t for t in tasks
                if (t.level.value if isinstance(t.level, TaskLevel) else str(t.level)) == target_lvl_val
            ]
            self._logger.info(f"Loaded {len(filtered)} tasks filtered by level '{target_lvl_val}'")
            return filtered

        self._logger.info(f"Loaded {len(tasks)} benchmark tasks for suite '{suite_id}'")
        return tasks

    def validate_dataset(self, tasks: List[GAIATask]) -> DatasetIntegrityResult:
        """Validate dataset structure, schema integrity, and attachments."""
        result = DatasetIntegrityResult(total_tasks=len(tasks))
        seen_ids = set()

        for idx, task in enumerate(tasks):
            if not task.task_id:
                result.errors.append(f"Task at index {idx} has missing task_id.")
                result.invalid_tasks += 1
                continue

            if task.task_id in seen_ids:
                result.errors.append(f"Duplicate task_id '{task.task_id}' detected at index {idx}.")
                result.invalid_tasks += 1
            seen_ids.add(task.task_id)

            if not task.question or not task.question.strip():
                result.errors.append(f"Task '{task.task_id}' has empty question.")
                result.invalid_tasks += 1

            if not task.ground_truth or not task.ground_truth.strip():
                result.warnings.append(f"Task '{task.task_id}' has empty ground_truth.")

            # Validate attachments if specified
            for att in task.file_attachments:
                if not os.path.exists(att):
                    result.warnings.append(f"Task '{task.task_id}' attachment missing: {att}")

        result.is_valid = result.invalid_tasks == 0
        self._logger.info(f"Dataset integrity check: valid={result.is_valid}, invalid={result.invalid_tasks}/{len(tasks)}")
        return result

    def _load_from_file(self, filepath: str) -> List[GAIATask]:
        """Parse tasks from .json or .jsonl file."""
        tasks: List[GAIATask] = []
        try:
            if filepath.endswith(".jsonl"):
                with open(filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            tasks.append(self._dict_to_gaia_task(data))
            else:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    items = content if isinstance(content, list) else content.get("tasks", [])
                    for data in items:
                        tasks.append(self._dict_to_gaia_task(data))
        except Exception as e:
            self._logger.error(f"Error loading dataset file '{filepath}': {e}")
        return tasks

    def _dict_to_gaia_task(self, data: Dict[str, Any]) -> GAIATask:
        """Convert raw dict into GAIATask object."""
        lvl_raw = data.get("level", "level_1")
        cat_raw = data.get("category", "web_research")

        try:
            level = TaskLevel(lvl_raw)
        except ValueError:
            level = TaskLevel.LEVEL_1

        try:
            category = TaskCategory(cat_raw)
        except ValueError:
            category = TaskCategory.WEB_RESEARCH

        return GAIATask(
            task_id=data.get("task_id", data.get("id", "")),
            question=data.get("question", data.get("Question", "")),
            level=level,
            category=category,
            ground_truth=str(data.get("ground_truth", data.get("Final answer", ""))),
            file_attachments=data.get("file_attachments", data.get("file_name", [])),
            metadata=data.get("metadata", {}),
        )
