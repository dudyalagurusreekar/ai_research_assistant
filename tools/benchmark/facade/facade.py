"""Unified BenchmarkToolFacade for the GAIA Benchmark Framework."""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple

from core.interfaces.tool import ITool
from core.models.metadata import ToolMetadata
from core.models.tool_result import ToolResult
from core.models.event import Event
from core.events import AsyncEventBus
from tools.benchmark.models.benchmark_models import (
    NormalizedBenchmarkResult,
    BenchmarkReportModel,
    TaskLevel,
    RegressionReport,
    SubmissionPackage,
)
from tools.benchmark.registry.benchmark_registry import BenchmarkRegistry
from tools.benchmark.loader.task_loader import TaskLoader
from tools.benchmark.scoring.scoring_engine import LocalScoringEngine
from tools.benchmark.analysis.error_analyzer import FailureAnalyzer
from tools.benchmark.metrics.metrics_engine import MetricsEngine
from tools.benchmark.regression.regression_engine import RegressionEngine
from tools.benchmark.optimization.optimization_manager import OptimizationAdvisor
from tools.benchmark.submission.submission_generator import SubmissionGenerator
from tools.benchmark.report.report_generator import BenchmarkReportGenerator
from tools.benchmark.engine.evaluation_engine import EvaluationEngine
from tools.benchmark.runner.benchmark_runner import BenchmarkRunner
from infrastructure.logging.logger import StructuredLogger


class BenchmarkToolFacade(ITool):
    """Public unified API facade for the GAIA Benchmark Evaluation & Optimization Framework."""

    name = "benchmark_tool"
    description = "Unified benchmark tool executing GAIA tasks, trace scoring, failure analysis, regression comparison, submission generation, and optimization recommendations."

    def __init__(
        self,
        registry: Optional[BenchmarkRegistry] = None,
        task_loader: Optional[TaskLoader] = None,
        scoring_engine: Optional[LocalScoringEngine] = None,
        error_analyzer: Optional[FailureAnalyzer] = None,
        metrics_engine: Optional[MetricsEngine] = None,
        regression_engine: Optional[RegressionEngine] = None,
        opt_advisor: Optional[OptimizationAdvisor] = None,
        submission_generator: Optional[SubmissionGenerator] = None,
        report_generator: Optional[BenchmarkReportGenerator] = None,
        eval_engine: Optional[EvaluationEngine] = None,
        runner: Optional[BenchmarkRunner] = None,
        event_bus: Optional[AsyncEventBus] = None,
        capability_registry: Optional[Any] = None,
    ) -> None:
        self.name = "benchmark_tool"
        self._logger = StructuredLogger("BenchmarkToolFacade")
        self._event_bus = event_bus or AsyncEventBus()

        self._registry = registry or BenchmarkRegistry()
        self._task_loader = task_loader or TaskLoader()
        self._scoring_engine = scoring_engine or LocalScoringEngine()
        self._error_analyzer = error_analyzer or FailureAnalyzer()
        self._metrics_engine = metrics_engine or MetricsEngine()
        self._regression_engine = regression_engine or RegressionEngine()
        self._opt_advisor = opt_advisor or OptimizationAdvisor()
        self._submission_generator = submission_generator or SubmissionGenerator()
        self._report_generator = report_generator or BenchmarkReportGenerator()

        self._eval_engine = eval_engine or EvaluationEngine(
            scoring_engine=self._scoring_engine, error_analyzer=self._error_analyzer
        )
        self._runner = runner or BenchmarkRunner(
            task_loader=self._task_loader,
            evaluation_engine=self._eval_engine,
            metrics_engine=self._metrics_engine,
            opt_advisor=self._opt_advisor,
            report_generator=self._report_generator,
        )

        self._metadata = ToolMetadata(
            name="benchmark_tool",
            version="1.0.0",
            description="Unified benchmark tool executing GAIA tasks, trace scoring, failure analysis, regression comparison, submission generation, and optimization recommendations.",
            capabilities=[
                "gaia_benchmark",
                "trace_scoring",
                "failure_taxonomy",
                "performance_optimization",
                "submission_generation",
                "regression_detection",
            ],
            parameters_schema={
                "action": "Action to perform ('run_suite', 'score', 'list_tasks', 'validate_dataset', 'generate_submission', 'compare_runs', 'generate_report', 'list_suites')",
                "level": "GAIA task level ('level_1', 'level_2', 'level_3')",
                "suite_id": "Benchmark suite ID ('gaia', 'swe_bench', etc.)",
                "predicted": "Predicted answer text",
                "ground_truth": "Ground truth answer text",
            },
            tags=["benchmark", "gaia", "evaluation", "scoring", "submission"],
            is_async=True,
            enabled=True,
        )

        # Automatically register with CapabilityRegistry if provided
        if capability_registry and hasattr(capability_registry, "register_tool"):
            try:
                capability_registry.register_tool(self)
                self._logger.info("Registered BenchmarkToolFacade with global CapabilityRegistry.")
            except Exception as e:
                self._logger.warning(f"Could not register BenchmarkToolFacade with CapabilityRegistry: {e}")

    @property
    def metadata(self) -> ToolMetadata:
        """Return tool metadata descriptor."""
        return self._metadata

    async def forward(self, action: str = "run_suite", **kwargs) -> str:
        """Standard tool execution wrapper returning JSON string."""
        try:
            level_str = kwargs.get("level")
            lvl_enum = TaskLevel(level_str) if level_str else None
            suite_id = kwargs.get("suite_id", "gaia")

            if action in ["run_suite", "run", "eval", "run_benchmark"]:
                report = await self.run_suite(
                    level=lvl_enum,
                    suite_id=suite_id,
                    max_tasks=kwargs.get("max_tasks"),
                    concurrency=kwargs.get("concurrency", 1),
                    checkpoint_file=kwargs.get("checkpoint_file"),
                )
                return json.dumps(report.to_dict(), indent=2)

            elif action in ["score", "evaluate"]:
                pred = kwargs.get("predicted", "")
                gt = kwargs.get("ground_truth", "")
                is_corr, score_val = self.score_answer(pred, gt)
                await self._publish_event("benchmark.scoring.completed", {"is_correct": is_corr, "score": score_val})
                return json.dumps({"is_correct": is_corr, "score": score_val}, indent=2)

            elif action in ["list_tasks", "list"]:
                tasks = self._task_loader.load_tasks(level=lvl_enum, suite_id=suite_id)
                return json.dumps([t.to_dict() for t in tasks], indent=2)

            elif action in ["list_suites"]:
                suites = self._registry.list_suites()
                return json.dumps([s.to_dict() for s in suites], indent=2)

            elif action in ["validate_dataset"]:
                tasks = self._task_loader.load_tasks(level=lvl_enum, suite_id=suite_id)
                val_res = self._task_loader.validate_dataset(tasks)
                return json.dumps(val_res.to_dict(), indent=2)

            elif action in ["generate_report"]:
                rep = await self.run_suite(level=lvl_enum, suite_id=suite_id)
                report_md = self._report_generator.generate_report(rep)
                return report_md

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
            output_str = await self.forward(action=action, **params)
            try:
                data = json.loads(output_str)
                if isinstance(data, dict) and "error" in data:
                    return ToolResult.error(error_message=data["error"])
                return ToolResult.success(data=data)
            except json.JSONDecodeError:
                # Returned plain text (e.g. report markdown)
                return ToolResult.success(data={"report": output_str})
        except Exception as e:
            return ToolResult.error(error_message=str(e))

    async def run_suite(
        self,
        level: Optional[TaskLevel] = None,
        suite_id: str = "gaia",
        max_tasks: Optional[int] = None,
        concurrency: int = 1,
        checkpoint_file: Optional[str] = None,
    ) -> BenchmarkReportModel:
        """Execute benchmark suite across difficulty levels and publish lifecycle events."""
        try:
            # 1. Event: benchmark.started
            await self._publish_event("benchmark.started", {"suite_id": suite_id, "level": level.value if level else "all"})

            report = await self._runner.run_benchmark(
                level=level,
                suite_id=suite_id,
                max_tasks=max_tasks,
                concurrency=concurrency,
                checkpoint_file=checkpoint_file,
            )

            # 2. Events: task, scoring, analysis, optimization completed
            await self._publish_event("benchmark.scoring.completed", {"accuracy": report.metrics.accuracy_percentage})
            await self._publish_event("benchmark.analysis.completed", {"failure_count": len(report.failure_reports)})
            await self._publish_event("benchmark.optimization.completed", {"recommendation_count": len(report.detailed_recommendations)})

            # 3. Event: benchmark.completed
            await self._publish_event("benchmark.completed", {"report_id": report.report_id, "accuracy": report.metrics.accuracy_percentage})
            await self._publish_event("evaluation.report.generated", {"report_id": report.report_id})

            return report

        except Exception as e:
            await self._publish_event("benchmark.task.failed", {"action": "run_suite", "error": str(e)})
            raise

    def score_answer(self, predicted: str, ground_truth: str) -> Tuple[bool, float]:
        """Score predicted answer against ground truth."""
        return self._scoring_engine.score(predicted, ground_truth)

    def generate_submission(
        self, results: List[NormalizedBenchmarkResult], output_file: str
    ) -> SubmissionPackage:
        """Generate official GAIA jsonl submission file and publish lifecycle event."""
        pkg = self._submission_generator.generate_submission(results, output_file)
        asyncio.create_task(
            self._publish_event("benchmark.submission.generated", {"submission_id": pkg.submission_id, "is_valid": pkg.is_valid})
        )
        return pkg

    def compare_runs(
        self, baseline_report: BenchmarkReportModel, target_report: BenchmarkReportModel
    ) -> RegressionReport:
        """Compare two benchmark runs to identify improvements, regressions, and latency shifts."""
        return self._regression_engine.compare_runs(baseline_report, target_report)

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
