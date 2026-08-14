"""Unit & Integration tests for Sprint 14 Evaluation & Quality Assurance Platform."""

import os
from pathlib import Path
import pytest

from evaluation.benchmark_datasets import DatasetManager
from evaluation.benchmark_engine import EvaluationEngine
from evaluation.golden_answers import GoldenAnswerRegistry
from evaluation.leaderboard import LeaderboardManager
from evaluation.models import GoldenAnswer, ReleaseGateConfig, TaskCategory
from evaluation.release_gates import ReleaseGateKeeper
from evaluation.report_generator import ReportGenerator
from evaluation.scoring_engine import ScoringEngine


def test_dataset_manager_generation():
    mgr = DatasetManager()

    # Fast mode
    fast_tasks = mgr.get_benchmark_tasks(mode="fast")
    assert len(fast_tasks) == 150
    assert len(set(t.category for t in fast_tasks)) == 15

    # Filter category
    sec_tasks = mgr.get_benchmark_tasks(mode="fast", category_filter=TaskCategory.SECURITY)
    assert all(t.category == TaskCategory.SECURITY for t in sec_tasks)


def test_golden_answer_validation():
    registry = GoldenAnswerRegistry()
    ga = GoldenAnswer(
        expected_keywords=["methodology", "results"],
        forbidden_keywords=["hallucinated_fact"],
        max_allowed_latency_ms=5000.0,
    )

    passed, score, msg = registry.validate_output(ga, "Methodology and results presented cleanly.", latency_ms=100.0)
    assert passed is True
    assert score == 1.0

    # Forbidden keyword failure
    passed_forbidden, score_f, msg_f = registry.validate_output(ga, "Contains hallucinated_fact in text", latency_ms=100.0)
    assert passed_forbidden is False
    assert "Forbidden" in msg_f


def test_release_gate_keeper_verdict():
    keeper = ReleaseGateKeeper(ReleaseGateConfig(min_overall_success_rate=95.0))
    engine = EvaluationEngine()
    report = engine.run_evaluation_suite(mode="fast")

    assert report.verdict is not None
    assert report.verdict.release_approved is True
    assert report.verdict.failed_gate_count == 0
    assert len(report.verdict.gate_checks) == 11


def test_report_generator():
    engine = EvaluationEngine()
    report = engine.run_evaluation_suite(mode="fast")
    generator = ReportGenerator()

    paths = generator.generate_all_reports(report)
    assert "html_dashboard" in paths
    assert "markdown" in paths
    assert "json" in paths

    assert Path(paths["html_dashboard"]).exists()
    assert Path(paths["markdown"]).exists()
    assert Path(paths["json"]).exists()


def test_leaderboard_manager():
    manager = LeaderboardManager(leaderboard_file="evaluation/logs/test_leaderboard.json")
    history = manager.get_history()
    assert len(history) >= 1
