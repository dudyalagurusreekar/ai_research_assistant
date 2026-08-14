"""Unit tests for SchemaDetector, DataProfiler, and DataCleaner."""

import pytest
from core.data_intelligence.components.schema_detector import SchemaDetector
from core.data_intelligence.components.profiler import DataProfiler
from core.data_intelligence.components.cleaner import DataCleaner
from core.data_intelligence.models.context import DataType


@pytest.fixture
def sample_records():
    return [
        {"id": 1, "score": 85.0, "group": "A"},
        {"id": 2, "score": 92.5, "group": "B"},
        {"id": 3, "score": 78.0, "group": "A"},
        {"id": 4, "score": None, "group": "B"},
        {"id": 4, "score": None, "group": "B"}, # Duplicate row
    ]


def test_schema_detector(sample_records):
    detector = SchemaDetector()
    schema = detector.detect_schema("test_ds", sample_records)
    assert schema.row_count == 5
    assert schema.column_count == 3
    assert schema.get_column("score").data_type == DataType.NUMERIC


def test_profiler(sample_records):
    detector = SchemaDetector()
    profiler = DataProfiler()
    schema = detector.detect_schema("test_ds", sample_records)
    profile = profiler.profile_dataset(schema, sample_records)

    assert profile.row_count == 5
    assert profile.quality_report.duplicate_rows_count == 1
    assert profile.column_profiles["score"].mean is not None


def test_cleaner(sample_records):
    detector = SchemaDetector()
    cleaner = DataCleaner()
    schema = detector.detect_schema("test_ds", sample_records)
    cleaned = cleaner.clean_dataset(sample_records, schema=schema, drop_duplicates=True, impute_missing=True)

    assert len(cleaned) == 4 # Duplicate removed
    assert all(r["score"] is not None for r in cleaned) # Imputed
