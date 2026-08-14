"""Unit tests for StrategyOptimizer."""

import tempfile
import shutil
import pytest
from core.learning.engine import ContinuousLearningEngine
from core.learning.models.context import ExperienceRecord, ExperienceOutcome


@pytest.fixture
def setup_engine():
    tmp_dir = tempfile.mkdtemp()
    engine = ContinuousLearningEngine(storage_dir=tmp_dir)
    
    # Populate historical records
    engine.record_experience(
        query="Research battery advancements in 2024",
        intent="multi_step_research",
        complexity_score=7,
        selected_tools=["search_tool", "document_tool"],
        excluded_tools=["vision_tool"],
        dag_nodes_count=3,
        dag_edges_count=2,
        parallel_waves=2,
        execution_latency_ms=1200.0,
        outcome=ExperienceOutcome.SUCCESS,
    )
    yield engine
    shutil.rmtree(tmp_dir)


def test_strategy_optimizer_recommendation(setup_engine):
    engine = setup_engine
    rec = engine.consult_experience(query="Research battery technology 2025", intent="multi_step_research")
    
    assert rec is not None
    assert rec.query == "Research battery technology 2025"
    assert rec.intent == "multi_step_research"
    assert len(rec.recommended_tools) > 0
    assert "search_tool" in rec.recommended_tools
    assert len(rec.preferred_providers) > 0
