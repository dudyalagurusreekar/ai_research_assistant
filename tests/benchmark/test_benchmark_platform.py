"""Comprehensive Unit, Integration, Concurrency, and End-to-End Tests for Phase 13 GAIA Benchmark Framework."""

import asyncio
import json
import pytest

from tools.benchmark.facade.facade import BenchmarkToolFacade
from tools.benchmark.models.benchmark_models import (
    GAIATask,
    TaskLevel,
    TaskCategory,
    ExecutionTrace,
    EvaluationMetrics,
    ErrorCategory,
    BenchmarkReportModel,
    NormalizedBenchmarkResult,
)
from tools.benchmark.loader.task_loader import TaskLoader
from tools.benchmark.scoring.scoring_engine import ScoringEngine
from tools.benchmark.analysis.error_analyzer import ErrorAnalyzer
from tools.benchmark.optimization.optimization_manager import OptimizationManager
from tools.benchmark.engine.evaluation_engine import EvaluationEngine
from tools.benchmark.runner.benchmark_runner import BenchmarkRunner
from tools.benchmark.tool import BenchmarkTool
from core.events import AsyncEventBus


def test_task_loader():
    """Verify GAIA benchmark task loading and level filtering."""
    loader = TaskLoader()
    all_tasks = loader.load_tasks()
    lvl1_tasks = loader.load_tasks(level=TaskLevel.LEVEL_1)

    assert len(all_tasks) == 3
    assert len(lvl1_tasks) == 1
    assert lvl1_tasks[0].level == TaskLevel.LEVEL_1


def test_scoring_engine():
    """Verify answer matching and token overlap scoring."""
    scoring = ScoringEngine()

    is_exact, s_exact = scoring.score("Quantum supremacy using a programmable superconducting processor", "Quantum supremacy using a programmable superconducting processor")
    is_fuzzy, s_fuzzy = scoring.score("quantum supremacy using programmable processor", "Quantum supremacy using a programmable superconducting processor")
    is_wrong, s_wrong = scoring.score("Classical computing limits", "Quantum supremacy using a programmable superconducting processor")

    assert is_exact is True and s_exact == 1.0
    assert is_fuzzy is True and s_fuzzy >= 0.70
    assert is_wrong is False and s_wrong == 0.0


def test_error_analyzer():
    """Verify error taxonomy classification."""
    analyzer = ErrorAnalyzer()
    empty_err = analyzer.classify_error("", "Ground Truth")
    browser_err = analyzer.classify_error("Wrong answer", "Ground Truth", ExecutionTrace(tool_invocations=["browser_tool"]))
    code_err = analyzer.classify_error("Syntax error", "Ground Truth", ExecutionTrace(tool_invocations=["code_tool"]))

    assert empty_err == ErrorCategory.PLANNING
    assert browser_err == ErrorCategory.BROWSER
    assert code_err == ErrorCategory.CODE


def test_optimization_manager():
    """Verify optimization policy configurations."""
    opt_mgr = OptimizationManager()
    task = GAIATask(question="Test question", level=TaskLevel.LEVEL_1)
    params = opt_mgr.get_optimized_params(task)

    assert params["retry_limit"] == 3
    assert params["verification_enabled"] is True


def test_evaluation_engine():
    """Verify task evaluation and result construction."""
    async def _test():
        engine = EvaluationEngine()
        task = GAIATask(question="Test", ground_truth="Answer 42")
        trace = ExecutionTrace(final_answer="Answer 42", tool_invocations=["search_tool"])

        res = await engine.evaluate_task(task, "Answer 42", trace)
        assert res.is_correct is True
        assert res.score == 1.0
        assert res.error_category == ErrorCategory.NONE

    asyncio.run(_test())


def test_benchmark_runner():
    """Verify benchmark suite execution and metric aggregation."""
    async def _test():
        runner = BenchmarkRunner()
        report = await runner.run_benchmark()

        assert report.report_id != ""
        assert report.metrics.total_tasks == 3
        assert report.metrics.passed_tasks == 3
        assert report.metrics.accuracy_percentage == 100.0

    asyncio.run(_test())


def test_benchmark_facade_end_to_end_and_events():
    """Verify BenchmarkToolFacade APIs and AsyncEventBus event notifications."""
    async def _test():
        bus = AsyncEventBus()
        events_fired = []

        async def _on_event(evt):
            events_fired.append(evt.event_type)

        bus.subscribe("benchmark.started", _on_event)
        bus.subscribe("benchmark.completed", _on_event)
        bus.subscribe("evaluation.report.generated", _on_event)

        facade = BenchmarkToolFacade(event_bus=bus)

        # 1. Run Suite API
        rep = await facade.run_suite()
        assert rep.metrics.accuracy_percentage == 100.0

        # 2. Score Answer API
        is_corr, val = facade.score_answer("Direct Match", "Direct Match")
        assert is_corr is True

        await asyncio.sleep(0.05)
        assert "benchmark.started" in events_fired
        assert "benchmark.completed" in events_fired
        assert "evaluation.report.generated" in events_fired

        # Test forward JSON method
        forward_json = await facade.forward(action="run_suite")
        assert "metrics" in forward_json

    asyncio.run(_test())


def test_smolagents_benchmark_tool_wrapper():
    """Verify smolagents BenchmarkTool wrapper."""
    tool = BenchmarkTool()
    res_str = tool.forward(action="run_suite")
    assert "metrics" in res_str
