"""End-to-End integration tests for DataIntelligenceEngine."""

import pytest
from core.data_intelligence.engine import DataIntelligenceEngine
from tools.data.tool import DataTool


@pytest.fixture
def sample_dataset():
    return [
        {"department": "Engineering", "salary": 110000, "experience_years": 5},
        {"department": "Engineering", "salary": 125000, "experience_years": 7},
        {"department": "Marketing", "salary": 85000, "experience_years": 3},
        {"department": "Marketing", "salary": 95000, "experience_years": 4},
        {"department": "Sales", "salary": 70000, "experience_years": 2},
    ]


def test_data_intelligence_engine_analyze(sample_dataset):
    engine = DataIntelligenceEngine()
    report = engine.analyze_dataset("employee_salaries", sample_dataset, run_ml=True, clean_data=True)

    assert report is not None
    assert report.dataset_name == "employee_salaries"
    assert report.profile.row_count == 5
    assert len(report.insights) >= 1
    assert len(report.visualizations) >= 1
    assert "# Data Intelligence Report: employee_salaries" in report.markdown_content


def test_data_tool_wrapper(sample_dataset):
    tool = DataTool()
    engine = tool._engine
    engine.memory.store_dataset("emp_ds", sample_dataset)

    output = tool.forward(action="analyze", dataset_name="emp_ds", source="emp_ds", run_ml=True)
    assert "Data Intelligence Report" in output
    assert "employee_salaries" not in output or "emp_ds" in output
