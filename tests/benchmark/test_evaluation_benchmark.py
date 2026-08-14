"""Benchmark test suite for Sprint 12 Evaluation Platform performance and metric calculation throughput."""

import time
import pytest
from evaluation.benchmark_engine.engine import EvaluationEngine
from evaluation.scoring_engine.metrics_calculator import recall_at_k, ndcg_at_k, groundedness_score, expected_calibration_error


def test_metrics_calculator_throughput_benchmark():
    retrieved = [f"doc_{i}" for i in range(100)]
    relevant = [f"doc_{i}" for i in range(0, 100, 5)]

    start_time = time.perf_counter()
    iterations = 5000
    for _ in range(iterations):
        recall_at_k(retrieved, relevant, k=10)
        ndcg_at_k(retrieved, relevant, k=10)
    elapsed = time.perf_counter() - start_time

    calcs_per_sec = (iterations * 2) / elapsed
    assert calcs_per_sec > 1000, f"Metrics calculation throughput too low: {calcs_per_sec:.2f} calcs/sec"


def test_evaluation_engine_overhead_benchmark():
    engine = EvaluationEngine()

    start_time = time.perf_counter()
    report = engine.run_evaluation_suite(mode="fast")
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    assert report is not None
    assert elapsed_ms < 5000, f"Evaluation engine suite run took too long: {elapsed_ms:.2f} ms"
