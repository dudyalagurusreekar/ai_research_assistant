"""End-to-End benchmark tests for Continuous Learning Engine."""

import tempfile
import shutil
import pytest
from core.learning.engine import ContinuousLearningEngine
from core.learning.models.context import ExperienceOutcome


@pytest.fixture
def temp_engine():
    tmp_dir = tempfile.mkdtemp()
    engine = ContinuousLearningEngine(storage_dir=tmp_dir)
    yield engine
    shutil.rmtree(tmp_dir)


def test_learning_cold_vs_warm_start(temp_engine):
    engine = temp_engine
    query = "Execute Python matrix computation and export JSON"
    
    # 1. Cold start recommendation (0 records in store)
    rec_cold = engine.consult_experience(query, intent="code_execution")
    assert rec_cold.confidence == 0.0

    # 2. Record multiple successful executions
    for _ in range(3):
        engine.record_experience(
            query=query,
            intent="code_execution",
            complexity_score=3,
            selected_tools=["code_tool", "python_interpreter"],
            excluded_tools=["vision_tool"],
            dag_nodes_count=1,
            dag_edges_count=0,
            parallel_waves=1,
            execution_latency_ms=150.0,
            outcome=ExperienceOutcome.SUCCESS,
        )

    # 3. Warm start recommendation (historical experiences present)
    rec_warm = engine.consult_experience(query, intent="code_execution")
    assert rec_warm.confidence > 0.0
    assert rec_warm.historical_success_probability == 1.0
    assert "code_tool" in rec_warm.recommended_tools or "python_interpreter" in rec_warm.recommended_tools
