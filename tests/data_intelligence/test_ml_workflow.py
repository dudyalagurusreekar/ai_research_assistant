"""Unit tests for MLWorkflowEngine."""

import pytest
from core.data_intelligence.components.ml_workflow import MLWorkflowEngine


@pytest.fixture
def ml_records():
    return [
        {"feature1": 1.0, "feature2": 2.0, "target": 5.0},
        {"feature1": 2.0, "feature2": 4.0, "target": 7.0},
        {"feature1": 3.0, "feature2": 6.0, "target": 9.0},
        {"feature1": 4.0, "feature2": 8.0, "target": 11.0},
        {"feature1": 10.0, "feature2": 20.0, "target": 23.0}, # Potential cluster / anomaly
    ]


def test_ml_kmeans_clustering(ml_records):
    ml_engine = MLWorkflowEngine()
    result = ml_engine.run_clustering(ml_records, numeric_cols=["feature1", "feature2"], k=2)

    assert result.task_type == "clustering"
    assert len(result.cluster_centers) == 2
    assert "inertia" in result.metrics


def test_ml_regression(ml_records):
    ml_engine = MLWorkflowEngine()
    result = ml_engine.run_regression(ml_records, x_col="feature1", y_col="target")

    assert result.task_type == "regression"
    assert "r2_score" in result.metrics
    assert result.metrics["r2_score"] > 0.95


def test_ml_anomaly_detection(ml_records):
    ml_engine = MLWorkflowEngine()
    result = ml_engine.run_anomaly_detection(ml_records, numeric_cols=["feature1", "feature2"], threshold_z=1.5)

    assert result.task_type == "anomaly_detection"
    assert result.anomalies_count >= 1
