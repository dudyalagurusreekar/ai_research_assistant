"""Comprehensive Unit, Integration, Concurrency, Recovery, Performance, and End-to-End Tests for Phase 13 GAIA Benchmark Framework."""

import os
import json
import asyncio
import tempfile

from tools.benchmark import (
    BenchmarkToolFacade,
    BenchmarkTool,
    BenchmarkRegistry,
    TaskLoader,
    ExecutionTracer,
    AnswerFormatter,
    LocalScoringEngine,
    FailureAnalyzer,
    MetricsEngine,
    RegressionEngine,
    OptimizationAdvisor,
    SubmissionGenerator,
    BenchmarkReportGenerator,
    BenchmarkRunner,
    GAIATask,
    TaskLevel,
    ErrorCategory,
    ExecutionTrace,
    ExecutionStep,
    EvaluationMetrics,
    BenchmarkSuiteMetadata,
    BenchmarkReportModel,
    NormalizedBenchmarkResult,
)
from core.events import AsyncEventBus


def test_benchmark_registry():
    """Verify BenchmarkRegistry suite registration and retrieval."""
    registry = BenchmarkRegistry()
    suites = registry.list_suites()
    assert len(suites) >= 5

    gaia = registry.get_suite("gaia")
    assert gaia is not None
    assert gaia.name == "General AI Assistants Benchmark (GAIA)"

    custom_suite = BenchmarkSuiteMetadata(
        suite_id="custom_bench",
        name="Custom Benchmark",
        description="Test benchmark suite",
    )
    registry.register_suite(custom_suite)
    assert registry.get_suite("custom_bench") is not None
    assert registry.unregister_suite("custom_bench") is True


def test_task_loader_and_validation():
    """Verify task loading, level filtering, and dataset integrity validation."""
    loader = TaskLoader()
    all_tasks = loader.load_tasks()
    lvl1_tasks = loader.load_tasks(level=TaskLevel.LEVEL_1)

    assert len(all_tasks) == 3
    assert len(lvl1_tasks) == 1
    assert lvl1_tasks[0].level == TaskLevel.LEVEL_1

    # Validate dataset integrity
    val_res = loader.validate_dataset(all_tasks)
    assert val_res.is_valid is True
    assert val_res.total_tasks == 3
    assert val_res.invalid_tasks == 0


def test_execution_tracer():
    """Verify fine-grained execution trace recording."""
    tracer = ExecutionTracer()
    trace = tracer.start_trace("task_123")

    step1 = ExecutionStep(
        step_type="tool_invocation",
        tool_name="browser_tool",
        duration_ms=120.0,
        status="success",
    )
    tracer.record_step(trace.trace_id, step1)

    final_trace = tracer.finalize_trace(trace.trace_id, "42")
    assert final_trace.task_id == "task_123"
    assert final_trace.final_answer == "42"
    assert "browser_tool" in final_trace.tool_invocations
    assert len(final_trace.steps) == 1


def test_answer_formatter():
    """Verify GAIA answer normalization rules and format validation."""
    formatter = AnswerFormatter()

    # 1. Explanation removal
    raw_exp = "Based on our analysis, the final answer is: **42**."
    fmt_exp = formatter.format_answer(raw_exp)
    assert fmt_exp == "42"

    # 2. Number normalization
    raw_num = "$1,250.00"
    fmt_num = formatter.format_answer(raw_num)
    assert fmt_num == "1250"

    # 3. List sorting & normalization
    raw_list = "apple, Banana, Cherry"
    fmt_list = formatter.format_answer(raw_list)
    assert fmt_list == "apple, banana, cherry"

    # 4. Format validation
    assert formatter.validate_format("42") is True
    assert formatter.validate_format("The answer is 42") is False


def test_local_scoring_engine():
    """Verify GAIA string, numeric, and set/list comparison scoring rules."""
    scoring = LocalScoringEngine()

    # String match
    is_exact, s_exact = scoring.score("Quantum supremacy", "Quantum supremacy")
    assert is_exact is True and s_exact == 1.0

    # Numeric relative tolerance match
    is_num, s_num = scoring.score("100.001", "100.000")
    assert is_num is True and s_num == 1.0

    # Comma-separated list set match
    is_list, s_list = scoring.score("cat, dog", "dog, cat")
    assert is_list is True and s_list == 1.0

    # Wrong answer
    is_wrong, s_wrong = scoring.score("wrong answer", "correct answer")
    assert is_wrong is False and s_wrong == 0.0


def test_failure_analyzer():
    """Verify failure taxonomy classification across 16 categories."""
    analyzer = FailureAnalyzer()

    # Empty prediction -> PLANNING
    plan_err = analyzer.classify_error("", "Ground Truth")
    assert plan_err == ErrorCategory.PLANNING

    # Browser failure
    b_trace = ExecutionTrace(
        tool_invocations=["browser_tool"],
        steps=[{"tool_name": "browser_tool", "error": "Element not found"}],
    )
    b_rep = analyzer.generate_failure_report(GAIATask(task_id="t1"), "wrong", b_trace)
    assert b_rep.error_category == ErrorCategory.BROWSER
    assert "Browser DOM" in b_rep.probable_root_cause

    # Code execution failure
    c_trace = ExecutionTrace(
        tool_invocations=["code_tool"],
        steps=[{"tool_name": "code_tool", "error": "SyntaxError in script"}],
    )
    c_rep = analyzer.generate_failure_report(GAIATask(task_id="t2"), "wrong", c_trace)
    assert c_rep.error_category == ErrorCategory.CODE_EXECUTION


def test_metrics_engine():
    """Verify metrics calculation, throughput, latencies, and token cost estimation."""
    engine = MetricsEngine()
    trace = ExecutionTrace(execution_time_ms=150.0, tool_invocations=["browser_tool", "search_tool"])

    res1 = NormalizedBenchmarkResult(task_id="t1", is_correct=True, score=1.0, trace=trace)
    res2 = NormalizedBenchmarkResult(task_id="t2", is_correct=False, score=0.0, trace=trace, error_category=ErrorCategory.BROWSER)

    metrics = engine.compute_metrics([res1, res2], start_time_ms=1000.0, end_time_ms=2000.0)
    assert metrics.total_tasks == 2
    assert metrics.passed_tasks == 1
    assert metrics.accuracy_percentage == 50.0
    assert metrics.avg_latency_ms == 150.0
    assert metrics.estimated_cost_usd > 0.0


def test_regression_engine():
    """Verify run comparison and regression detection."""
    engine = RegressionEngine()

    rep_a = BenchmarkReportModel(
        report_id="run_a",
        metrics=EvaluationMetrics(accuracy_percentage=80.0, avg_latency_ms=100.0),
        error_breakdown={"browser": 2},
    )
    rep_b = BenchmarkReportModel(
        report_id="run_b",
        metrics=EvaluationMetrics(accuracy_percentage=90.0, avg_latency_ms=150.0),
        error_breakdown={"browser": 1},
    )

    reg_rep = engine.compare_runs(rep_a, rep_b)
    assert reg_rep.total_delta_accuracy == 10.0
    assert len(reg_rep.improvements) >= 1
    assert "Overall accuracy improved" in reg_rep.improvements[0]


def test_optimization_advisor():
    """Verify recommendation generation from failure taxonomy."""
    advisor = OptimizationAdvisor()

    rep = BenchmarkReportModel(
        error_breakdown={"browser": 3, "formatting": 2},
    )
    recs = advisor.analyze_and_recommend(rep)

    categories = [r.category for r in recs]
    assert "browser_recovery" in categories
    assert "prompt_refinement" in categories


def test_submission_generator():
    """Verify GAIA jsonl submission package generation."""
    generator = SubmissionGenerator()

    results = [
        NormalizedBenchmarkResult(task_id="t1", predicted_answer="Answer 1"),
        NormalizedBenchmarkResult(task_id="t2", predicted_answer="Answer 2"),
    ]

    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        pkg = generator.generate_submission(results, tmp_path)
        assert pkg.is_valid is True
        assert len(pkg.entries) == 2
        assert os.path.exists(tmp_path)

        with open(tmp_path, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]
            assert len(lines) == 2
            assert lines[0]["task_id"] == "t1"
            assert lines[0]["model_answer"] == "Answer 1"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_report_generator():
    """Verify markdown evaluation report generation."""
    generator = BenchmarkReportGenerator()
    rep_model = BenchmarkReportModel(
        metrics=EvaluationMetrics(total_tasks=5, passed_tasks=4, accuracy_percentage=80.0, avg_latency_ms=120.0),
        error_breakdown={"browser": 1},
    )

    report_md = generator.generate_report(rep_model)
    assert "# GAIA Benchmark Evaluation - Evaluation Report" in report_md
    assert "80.0% overall accuracy" in report_md
    assert "`browser`" in report_md


def test_benchmark_runner_and_checkpoint():
    """Verify benchmark runner execution, concurrency, and checkpoint recovery."""
    async def _test():
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            checkpoint_file = tmp.name

        try:
            runner = BenchmarkRunner()
            report = await runner.run_benchmark(concurrency=2, checkpoint_file=checkpoint_file)

            assert report.report_id != ""
            assert report.metrics.total_tasks == 3
            assert report.metrics.passed_tasks == 3
            assert report.metrics.accuracy_percentage == 100.0
            assert os.path.exists(checkpoint_file)

            # Re-running with checkpoint file should load completed tasks
            report2 = await runner.run_benchmark(checkpoint_file=checkpoint_file)
            assert report2.metrics.total_tasks == 3
            assert report2.metrics.passed_tasks == 3
        finally:
            if os.path.exists(checkpoint_file):
                os.remove(checkpoint_file)

    asyncio.run(_test())


def test_benchmark_facade_end_to_end_and_events():
    """Verify BenchmarkToolFacade APIs and all AsyncEventBus lifecycle event notifications."""
    async def _test():
        bus = AsyncEventBus()
        events_fired = []

        async def _on_event(evt):
            events_fired.append(evt.event_type)

        for event_name in [
            "benchmark.started",
            "benchmark.task.completed",
            "benchmark.scoring.completed",
            "benchmark.analysis.completed",
            "benchmark.optimization.completed",
            "benchmark.completed",
            "evaluation.report.generated",
        ]:
            bus.subscribe(event_name, _on_event)

        facade = BenchmarkToolFacade(event_bus=bus)

        # 1. Run Suite API
        rep = await facade.run_suite()
        assert rep.metrics.accuracy_percentage == 100.0

        # 2. Score Answer API
        is_corr, val = facade.score_answer("Direct Match", "Direct Match")
        assert is_corr is True

        await asyncio.sleep(0.05)
        assert "benchmark.started" in events_fired
        assert "benchmark.scoring.completed" in events_fired
        assert "benchmark.analysis.completed" in events_fired
        assert "benchmark.optimization.completed" in events_fired
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
