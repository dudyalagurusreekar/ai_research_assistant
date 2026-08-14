"""Unit and integration tests for Data Intelligence & Analytics Platform."""

import pytest
from core.data_intelligence.engine import DataIntelligenceEngine
from core.data_intelligence.components.sql_assistant import SQLAssistant


def test_data_ingestion_csv_and_records():
    engine = DataIntelligenceEngine()
    records = [
        {"target_gene": "EMX1", "off_target_rate": 0.02, "confidence": 0.98},
        {"target_gene": "VEGFA", "off_target_rate": 0.45, "confidence": 0.85},
    ]

    report = engine.analyze_dataset("crispr_test_ds", records)
    assert report is not None
    assert report.profile.row_count == 2
    assert len(report.profile.schema.columns) == 3


def test_sql_assistant():
    assistant = SQLAssistant()
    records = [
        {"gene": "EMX1", "rate": 0.02},
        {"gene": "VEGFA", "rate": 0.45},
    ]

    table_name = assistant.load_table("test_genes", records)
    assert table_name == "test_genes"

    sql = assistant.generate_sql("What is the average rate?", table_name, ["gene", "rate"])
    assert "AVG" in sql

    res = assistant.execute_sql(f'SELECT * FROM "{table_name}" WHERE rate < 0.1')
    assert res["row_count"] == 1
    assert res["records"][0]["gene"] == "EMX1"


def test_ml_anomaly_and_regression():
    engine = DataIntelligenceEngine()
    records = [
        {"val1": 10.0, "val2": 20.0},
        {"val1": 12.0, "val2": 24.0},
        {"val1": 14.0, "val2": 28.0},
        {"val1": 1000.0, "val2": 2000.0},  # Extreme Anomaly
    ]

    anomalies = engine.ml_engine.run_anomaly_detection(records, ["val1", "val2"], threshold_z=1.0)
    assert anomalies.anomalies_count > 0
