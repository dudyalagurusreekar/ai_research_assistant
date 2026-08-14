"""Unit tests for VisualizationEngine."""

import pytest
from core.data_intelligence.components.visualization import VisualizationEngine


@pytest.fixture
def chart_records():
    return [
        {"category": "Electronics", "sales": 150.0},
        {"category": "Apparel", "sales": 80.0},
        {"category": "Groceries", "sales": 220.0},
    ]


def test_visualization_bar_chart(chart_records):
    viz_engine = VisualizationEngine()
    config = viz_engine.create_visualization(
        chart_type="bar",
        title="Sales by Category",
        records=chart_records,
        x_column="category",
        y_column="sales",
    )

    assert config.chart_type == "bar"
    assert config.title == "Sales by Category"
    assert "<svg" in config.rendered_svg
    assert "</svg>" in config.rendered_svg
