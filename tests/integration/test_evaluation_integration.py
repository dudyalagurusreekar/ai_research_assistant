"""Integration test suite for Sprint 12: Evaluation, Benchmarking, Observability, and QA Platform."""

import pytest
import tempfile
from pathlib import Path

from evaluation.benchmark_engine.engine import EvaluationEngine
from evaluation.scoring_engine.metrics_calculator import (
    recall_at_k,
    precision_at_k,
    mean_reciprocal_rank,
    ndcg_at_k,
    groundedness_score,
    citation_accuracy_score,
    hallucination_rate_score,
    reasoning_quality_score,
    expected_calibration_error,
)
from evaluation.infrastructure_testing.observability import PrometheusMetricExporter, GrafanaDashboardGenerator
from evaluation.release_gates.regression_tracker import RegressionTracker
from evaluation.reliability_testing.load_and_stress_testing import LoadStressTestingSuite


@pytest.fixture
def temp_eval_engine():
    engine = EvaluationEngine()
    yield engine


def test_metrics_calculator_functions():
    # Recall and Precision
    retrieved = ["doc_a", "doc_b", "doc_c", "doc_d"]
    relevant = ["doc_b", "doc_d"]
    assert recall_at_k(retrieved, relevant, k=4) == 1.0
    assert precision_at_k(retrieved, relevant, k=2) == 0.5
    assert mean_reciprocal_rank(retrieved, relevant) == 0.5
    assert ndcg_at_k(retrieved, relevant, k=4) > 0.0

    # Groundedness & Hallucination Rate
    claims = ["PyTorch is an open source machine learning framework.", "BERT achieves state-of-the-art results."]
    evidence = ["PyTorch is an open-source machine learning framework used worldwide.", "BERT model trained on Wikipedia."]
    g_score = groundedness_score(claims, evidence)
    assert g_score >= 0.5

    h_rate = hallucination_rate_score("PyTorch is an open source framework.", evidence)
    assert h_rate <= 0.5

    # ECE Calibration
    confidences = [0.9, 0.8, 0.7, 0.6, 0.5]
    accuracies = [1, 1, 1, 0, 0]
    ece = expected_calibration_error(confidences, accuracies, num_bins=5)
    assert 0.0 <= ece <= 1.0


def test_evaluation_engine_full_run(temp_eval_engine):
    engine = temp_eval_engine
    report = engine.run_evaluation_suite(mode="fast")

    assert report.report_id is not None
    assert report.dashboard_metrics.total_tasks_run > 0
    assert report.dashboard_metrics.overall_quality_score >= 0.0
    assert report.verdict.status.value in ["passed", "approved", "blocked"]



def test_prometheus_and_grafana_observability(temp_eval_engine):
    engine = temp_eval_engine
    engine.run_evaluation_suite(mode="fast")

    prom_text = engine.export_prometheus_metrics()
    assert "# TYPE ara_evaluation_pass_rate gauge" in prom_text
    assert "ara_evaluation_pass_rate" in prom_text

    dashboard_spec = engine.get_grafana_dashboard_spec()
    assert "dashboard" in dashboard_spec
    assert len(dashboard_spec["dashboard"]["panels"]) >= 4


def test_regression_tracker_and_baselines():
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = RegressionTracker(storage_dir=tmpdir)
        run_data = {
            "report_id": "run_001",
            "dashboard_metrics": {"overall_quality_score": 0.95, "overall_pass_rate": 98.0, "avg_latency_ms": 150.0},
            "category_summaries": {"research": {"pass_rate": 100.0}},
        }
        tracker.save_baseline("run_001", run_data, tag="golden")

        # Compare with non-degraded run
        reg_report = tracker.compare_with_baseline(run_data, tag="golden", tolerance_pct=5.0)
        assert reg_report.has_regression is False

        # Compare with degraded run
        degraded_run = {
            "report_id": "run_002",
            "dashboard_metrics": {"overall_quality_score": 0.80, "overall_pass_rate": 85.0, "avg_latency_ms": 300.0},
            "category_summaries": {"research": {"pass_rate": 80.0}},
        }
        deg_report = tracker.compare_with_baseline(degraded_run, tag="golden", tolerance_pct=5.0)
        assert deg_report.has_regression is True


def test_load_and_stress_testing_suite():
    suite = LoadStressTestingSuite()

    def dummy_task():
        sum(range(100))

    results = suite.run_concurrency_benchmark(dummy_task, num_users=5, iterations_per_user=2)
    assert results["total_requests"] == 10
    assert results["requests_per_sec"] > 0.0
    assert results["error_rate_pct"] == 0.0
