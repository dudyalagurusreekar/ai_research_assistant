"""Unified BenchmarkToolFacade for the GAIA Benchmark Framework."""

import json
import asyncio
from typing import Dict, List, Any, Optional

from core.interfaces.tool import ITool
from core.models.metadata import ToolMetadata
from core.models.tool_result import ToolResult
from core.models.event import Event
from core.events import AsyncEventBus
from tools.benchmark.models.benchmark_models import (
    GAIATask,
    NormalizedBenchmarkResult,
    BenchmarkReportModel,
    TaskLevel,
)
from tools.benchmark.loader.task_loader import TaskLoader
from tools.benchmark.scoring.scoring_engine import ScoringEngine
from tools.benchmark.analysis.error_analyzer import ErrorAnalyzer
from tools.benchmark.optimization.optimization_manager import OptimizationManager
from tools.benchmark.engine.evaluation_engine import EvaluationEngine
from tools.benchmark.runner.benchmark_runner import BenchmarkRunner
from infrastructure.logging.logger import StructuredLogger


class BenchmarkToolFacade(ITool):
    """Public unified API facade for the GAIA Benchmark Evaluation & Optimization Framework."""

    name = "benchmark_tool"
    description = "Unified benchmark evaluation tool for executing GAIA tasks, trace scoring, error analysis, and performance optimization."

    def __init__(
        self,
        task_loader: Optional[TaskLoader] = None,
        scoring_engine: Optional[ScoringEngine] = None,
        error_analyzer: Optional[ErrorAnalyzer] = None,
        opt_manager: Optional[OptimizationManager] = None,
        eval_engine: Optional[EvaluationEngine] = None,
        runner: Optional[BenchmarkRunner] = None,
        event_bus: Optional[AsyncEventBus] = None,
    ) -> None:
        self.name = "benchmark_tool"
        self._logger = StructuredLogger("BenchmarkToolFacade")
        self._event_bus = event_bus or AsyncEventBus()

        self._task_loader = task_loader or TaskLoader()
        self._scoring_engine = scoring_engine or ScoringEngine()
        self._error_analyzer = error_analyzer or ErrorAnalyzer()
        self._opt_manager = opt_manager or OptimizationManager()
        self._eval_engine = eval_engine or EvaluationEngine(scoring_engine=self._scoring_engine, error_analyzer=self._error_analyzer)
        self._runner = runner or BenchmarkRunner(task_loader=self._task_loader, evaluation_engine=self._eval_engine)

        self._metadata = ToolMetadata(
            name="benchmark_tool",
            version="1.0.0",
            description="Unified benchmark evaluation tool for executing GAIA tasks, trace scoring, error analysis, and performance optimization.",
            capabilities=["gaia_benchmark", "trace_scoring", "error_taxonomy", "performance_optimization"],
            parameters_schema={
                "action": "Action to perform ('run_suite', 'score', 'list_tasks')",
                "level": "GAIA task level ('level_1', 'level_2', 'level_3')",
                "predicted": "Predicted answer text",
                "ground_truth": "Ground truth answer text",
            },
            tags=["benchmark", "gaia", "evaluation", "scoring"],
            is_async=True,
            enabled=True,
        )

    @property
    def metadata(self) -> ToolMetadata:
        """Return tool metadata descriptor."""
        return self._metadata

    async def forward(self, action: str = "run_suite", **kwargs) -> str:
        """Standard tool execution wrapper returning JSON string."""
        try:
            level_str = kwargs.get("level")
            lvl_enum = TaskLevel(level_str) if level_str else None

            if action in ["run_suite", "run", "eval"]:
                report = await self.run_suite(level=lvl_enum)
                return json.dumps(report.to_dict(), indent=2)
            elif action in ["score", "evaluate"]:
                pred = kwargs.get("predicted", "")
                gt = kwargs.get("ground_truth", "")
                is_corr, score_val = self.score_answer(pred, gt)
                return json.dumps({"is_correct": is_corr, "score": score_val}, indent=2)
            elif action in ["list_tasks", "list"]:
                tasks = self._task_loader.load_tasks(level=lvl_enum)
                return json.dumps([t.to_dict() for t in tasks], indent=2)
            else:
                return json.dumps({"error": f"Unknown benchmark action '{action}'"}, indent=2)
        except Exception as e:
            self._logger.error(f"Error in BenchmarkToolFacade.forward action '{action}': {e}")
            return json.dumps({"error": str(e)}, indent=2)

    async def execute(self, parameters: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
        """Execute method returning ToolResult object conforming to ITool interface."""
        params = dict(parameters or {})
        params.update(kwargs)
        action = params.get("action", "run_suite")
        try:
            output_json = await self.forward(action=action, **params)
            data = json.loads(output_json)
            if isinstance(data, dict) and "error" in data:
                return ToolResult.error(error_message=data["error"])
            return ToolResult.success(data=data)
        except Exception as e:
            return ToolResult.error(error_message=str(e))

    async def run_suite(self, level: Optional[TaskLevel] = None) -> BenchmarkReportModel:
        """Execute benchmark suite across GAIA levels."""
        try:
            await self._publish_event("benchmark.started", {"level": level.value if level else "all"})
            report = await self._runner.run_benchmark(level=level)
            await self._publish_event("benchmark.completed", {"accuracy": report.metrics.accuracy_percentage})
            await self._publish_event("evaluation.report.generated", {"report_id": report.report_id})
            return report
        except Exception as e:
            await self._publish_event("benchmark.failed", {"action": "run_suite", "error": str(e)})
            raise

    def score_answer(self, predicted: str, ground_truth: str) -> tuple[bool, float]:
        """Score predicted answer against ground truth."""
        return self._scoring_engine.score(predicted, ground_truth)

    async def _publish_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish domain event over AsyncEventBus."""
        if self._event_bus:
            try:
                event_obj = Event(
                    event_type=event_type,
                    source="BenchmarkToolFacade",
                    payload=payload,
                )
                await self._event_bus.publish(event_obj)
            except Exception as e:
                self._logger.warning(f"Error publishing benchmark event '{event_type}': {e}")
