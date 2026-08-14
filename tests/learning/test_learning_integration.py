"""Integration tests for Continuous Learning Engine with IntelligentPlanningEngine."""

import tempfile
import shutil
import pytest
from core.planner.engine import IntelligentPlanningEngine
from core.learning.engine import ContinuousLearningEngine
from core.learning.integration import reset_learning_engine


@pytest.fixture
def temp_env():
    tmp_dir = tempfile.mkdtemp()
    reset_learning_engine()
    yield tmp_dir
    shutil.rmtree(tmp_dir)
    reset_learning_engine()


def test_planner_learning_engine_consultation(temp_env):
    planner = IntelligentPlanningEngine()
    ctx = planner.plan("Research solid state battery technology and summarize market trends")
    
    assert ctx is not None
    assert ctx.metadata is not None
    assert "strategy_recommendation" in ctx.metadata
    rec = ctx.metadata["strategy_recommendation"]
    assert rec.query == "Research solid state battery technology and summarize market trends"
    assert len(rec.recommended_tools) > 0
