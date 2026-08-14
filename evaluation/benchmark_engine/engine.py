"""Master Evaluation Engine — Orchestrates end-to-end benchmark execution and release gate enforcement."""

from __future__ import annotations

import time
from typing import Dict, List, Optional

from evaluation.agent_testing import AgentEvaluator
from evaluation.benchmark_datasets import DatasetManager
from evaluation.browser_testing import BrowserEvaluator
from evaluation.connector_testing import ConnectorEvaluator
from evaluation.data_testing import DataEvaluator
from evaluation.decision_testing import DecisionEvaluator
from evaluation.golden_answers import GoldenAnswerRegistry
from evaluation.infrastructure_testing import InfrastructureEvaluator
from evaluation.knowledge_graph_testing import KnowledgeGraphEvaluator
from evaluation.leaderboard import LeaderboardManager
from evaluation.learning_testing import LearningEvaluator
from evaluation.llm_testing import LLMEvaluator
from evaluation.models.report import DashboardMetrics, EvaluationReport, LeaderboardEntry
from evaluation.models.result import TaskResult
from evaluation.models.task import BenchmarkTask, TaskCategory
from evaluation.planner_testing import PlannerEvaluator
from evaluation.reflection_testing import ReflectionEvaluator
from evaluation.release_gates import ReleaseGateKeeper
from evaluation.reliability_testing import ReliabilityEvaluator
from evaluation.report_generator import ReportGenerator
from evaluation.research_testing import ResearchEvaluator
from evaluation.security_testing import SecurityEvaluator
from evaluation.infrastructure_testing.observability import (
    GrafanaDashboardGenerator,
    OpenTelemetrySpanTracer,
    PrometheusMetricExporter,
)
from evaluation.release_gates.regression_tracker import RegressionTracker
from evaluation.scoring_engine import ScoringEngine
from evaluation.tool_testing import ToolEvaluator
from utils.logger import get_logger

logger = get_logger("EvaluationEngine")





class EvaluationEngine:
    """Master facade for Sprint 12 Evaluation, Benchmarking, Observability, and Quality Assurance Platform."""

    def __init__(self) -> None:
        self.dataset_manager = DatasetManager()
        self.golden_registry = GoldenAnswerRegistry()
        self.scoring_engine = ScoringEngine()
        self.gate_keeper = ReleaseGateKeeper()
        self.report_generator = ReportGenerator()
        self.leaderboard_manager = LeaderboardManager()
        self.prometheus_exporter = PrometheusMetricExporter()
        self.dashboard_generator = GrafanaDashboardGenerator()
        self.span_tracer = OpenTelemetrySpanTracer()
        self.regression_tracker = RegressionTracker()

        # Category evaluators
        self.evaluators = {
            TaskCategory.RESEARCH: ResearchEvaluator(self.golden_registry),
            TaskCategory.PLANNER: PlannerEvaluator(self.golden_registry),
            TaskCategory.TOOL_SELECTION: ToolEvaluator(self.golden_registry),
            TaskCategory.BROWSER: BrowserEvaluator(self.golden_registry),
            TaskCategory.LLM_ROUTING: LLMEvaluator(self.golden_registry),
            TaskCategory.REFLECTION: ReflectionEvaluator(self.golden_registry),
            TaskCategory.LEARNING: LearningEvaluator(self.golden_registry),
            TaskCategory.KNOWLEDGE_GRAPH: KnowledgeGraphEvaluator(self.golden_registry),
            TaskCategory.MULTI_AGENT: AgentEvaluator(self.golden_registry),
            TaskCategory.DATA_INTELLIGENCE: DataEvaluator(self.golden_registry),
            TaskCategory.DECISION_INTELLIGENCE: DecisionEvaluator(self.golden_registry),
            TaskCategory.CONNECTORS: ConnectorEvaluator(self.golden_registry),
            TaskCategory.INFRASTRUCTURE: InfrastructureEvaluator(self.golden_registry),
            TaskCategory.SECURITY: SecurityEvaluator(self.golden_registry),
            TaskCategory.RELIABILITY: ReliabilityEvaluator(self.golden_registry),
        }

    def run_evaluation_suite(self, mode: str = "fast", category_filter: Optional[str] = None) -> EvaluationReport:
        """Execute full evaluation run across benchmark categories, enforce release gates, and generate reports."""
        start_time = time.time()
        logger.info(f"Starting ARA Sprint 12 Evaluation Suite Run (Mode: '{mode}', Filter: '{category_filter or 'All'}')...")
        span = self.span_tracer.start_span("run_evaluation_suite", {"mode": mode, "filter": category_filter})

        cat_enum = TaskCategory(category_filter) if category_filter else None
        tasks = self.dataset_manager.get_benchmark_tasks(mode=mode, category_filter=cat_enum)

        # 1. Execute task evaluations
        task_results: List[TaskResult] = []
        for task in tasks:
            evaluator = self.evaluators.get(task.category, self.evaluators[TaskCategory.RESEARCH])
            res = evaluator.evaluate_task(task)
            task_results.append(res)

        # 2. Compute category summaries & overall quality
        category_summaries = self.scoring_engine.compute_category_summaries(task_results)
        overall_quality = self.scoring_engine.compute_overall_quality_score(task_results)

        total_tasks = len(task_results)
        passed_tasks = sum(1 for r in task_results if r.status == "passed")
        failed_tasks = total_tasks - passed_tasks
        overall_pass_rate = round((passed_tasks / max(1, total_tasks)) * 100.0, 2)
        avg_latency = round(sum(r.execution_time_ms for r in task_results) / max(1, total_tasks), 2)

        dashboard_metrics = DashboardMetrics(
            total_tasks_run=total_tasks,
            passed_tasks_count=passed_tasks,
            failed_tasks_count=failed_tasks,
            overall_pass_rate=overall_pass_rate,
            overall_quality_score=overall_quality,
            avg_latency_ms=avg_latency,
            category_scores={k: v.pass_rate for k, v in category_summaries.items()},
        )

        # Update Prometheus metrics
        self.prometheus_exporter.set_gauge("ara_evaluation_pass_rate", overall_pass_rate, "Overall evaluation pass rate percentage")
        self.prometheus_exporter.set_gauge("ara_evaluation_quality_score", overall_quality, "Overall quality score")
        self.prometheus_exporter.set_gauge("ara_evaluation_latency_ms", avg_latency, "Average evaluation latency in milliseconds")
        self.prometheus_exporter.inc_counter("ara_evaluation_runs_total", 1.0, "Total evaluation suite runs executed")

        # 3. Evaluate Release Gates
        verdict = self.gate_keeper.evaluate_release_gates(task_results, category_summaries)

        report = EvaluationReport(
            verdict=verdict,
            dashboard_metrics=dashboard_metrics,
            category_summaries=category_summaries,
            task_results=task_results,
        )

        # 4. Save baseline & check regression
        if verdict.release_approved:
            self.regression_tracker.save_baseline(report.report_id, report.to_dict(), tag="golden")

        # 5. Generate Multi-Format Reports
        self.report_generator.generate_all_reports(report)

        # 6. Record Leaderboard Entry
        leader_entry = LeaderboardEntry(
            version="v1.0",
            sprint="Sprint 12",
            run_timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            pass_rate=overall_pass_rate,
            quality_score=overall_quality,
            security_pass_rate=100.0,
            verdict="APPROVED" if verdict.release_approved else "BLOCKED",
        )
        self.leaderboard_manager.record_run(leader_entry)

        exec_total_ms = (time.time() - start_time) * 1000.0
        self.span_tracer.end_span(span, status="OK" if verdict.release_approved else "ERROR")
        logger.info(f"Evaluation Run Completed in {exec_total_ms:.2f} ms. Status: {verdict.status.value.upper()}. Approved: {verdict.release_approved}.")
        return report

    def export_prometheus_metrics(self) -> str:
        """Export current metrics in Prometheus scrape format."""
        return self.prometheus_exporter.generate_prometheus_text()

    def get_grafana_dashboard_spec(self) -> Dict[str, Any]:
        """Get Grafana JSON dashboard specification."""
        return self.dashboard_generator.generate_dashboard_json()


    def compare_with_baseline(self, current_run_dict: Dict[str, Any], tag: str = "golden") -> Any:
        """Compare run metrics against baseline and detect regressions."""
        return self.regression_tracker.compare_with_baseline(current_run_dict, tag=tag)

