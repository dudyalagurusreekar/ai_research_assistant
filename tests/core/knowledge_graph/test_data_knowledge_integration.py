"""Integration tests for Data Intelligence Engine ingestion into Knowledge Graph."""

import pytest

from core.data_intelligence.models.context import (
    DataQualityReport,
    DataProfile,
    DataReport,
    DatasetSchema,
    StatisticalAnalysisResult,
)
from core.knowledge_graph import DataKnowledgeIntegration, KnowledgeGraphEngine


def test_data_knowledge_integration():
    kg_engine = KnowledgeGraphEngine()
    integration = DataKnowledgeIntegration(kg_engine)

    schema = DatasetSchema(dataset_name="latency_benchmarks", row_count=100, column_count=2)
    quality = DataQualityReport(total_rows=100, duplicate_rows_count=0, total_missing_cells=0, overall_quality_score=0.98)
    profile = DataProfile(
        dataset_name="latency_benchmarks",
        row_count=100,
        column_count=2,
        schema=schema,
        quality_report=quality,
    )
    stat = StatisticalAnalysisResult(
        analysis_type="descriptive",
        summary_metrics={"mean_ms": 1.8, "p95_ms": 3.2},
    )
    report = DataReport(
        title="Latency Report",
        dataset_name="latency_benchmarks",
        executive_summary="Summary",
        profile=profile,
        statistical_result=stat,
    )

    node_count = integration.ingest_data_report(report)
    assert node_count >= 3
    assert kg_engine.graph.find_node_by_name("latency_benchmarks") is not None
