"""Unit tests for PatternAnalyzer."""

import tempfile
import shutil
import pytest
from core.learning.components.experience_store import ExperienceStore
from core.learning.components.pattern_analyzer import PatternAnalyzer
from core.learning.models.context import ExperienceRecord, ExperienceOutcome


@pytest.fixture
def setup_analyzer():
    tmp_dir = tempfile.mkdtemp()
    store = ExperienceStore(storage_dir=tmp_dir)
    
    # Add sample historical records
    for i in range(5):
        store.add_record(
            ExperienceRecord(
                query=f"Compare paper {i}",
                intent="comparison",
                selected_tools=["search_tool", "report_tool"],
                parallel_waves=2,
                outcome=ExperienceOutcome.SUCCESS,
            )
        )

    analyzer = PatternAnalyzer(store)
    yield analyzer, store
    shutil.rmtree(tmp_dir)


def test_pattern_analyzer_intent_patterns(setup_analyzer):
    analyzer, _ = setup_analyzer
    insight = analyzer.analyze_intent_patterns("comparison")
    assert insight is not None
    assert insight.intent == "comparison"
    assert insight.sample_count == 5
    assert insight.avg_success_rate == 1.0
    assert "search_tool" in insight.optimal_tools
    assert "report_tool" in insight.optimal_tools


def test_pattern_analyzer_co_occurrence(setup_analyzer):
    analyzer, _ = setup_analyzer
    co_matrix = analyzer.get_tool_co_occurrence()
    assert "search_tool" in co_matrix
    assert "report_tool" in co_matrix["search_tool"]
