"""Unit tests for StatisticalAnalyzer."""

import pytest
from core.data_intelligence.components.schema_detector import SchemaDetector
from core.data_intelligence.components.statistical_analyzer import StatisticalAnalyzer


@pytest.fixture
def correlated_records():
    return [
        {"x": 1.0, "y": 2.0},
        {"x": 2.0, "y": 4.0},
        {"x": 3.0, "y": 6.0},
        {"x": 4.0, "y": 8.0},
        {"x": 5.0, "y": 10.0},
    ]


def test_statistical_correlation(correlated_records):
    detector = SchemaDetector()
    analyzer = StatisticalAnalyzer()
    schema = detector.detect_schema("correlated_ds", correlated_records)
    result = analyzer.analyze(schema, correlated_records)

    assert result.analysis_type == "multivariate_statistical_analysis"
    assert "x" in result.correlation_matrix
    assert result.correlation_matrix["x"]["y"] == 1.0
    assert len(result.significant_findings) >= 1
