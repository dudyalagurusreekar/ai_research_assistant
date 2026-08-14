"""Integration tests for Continuous Learning Engine experience logging of multi-agent sessions."""

import pytest

from core.collaboration import (
    LearningCollaborationIntegration,
    MultiAgentCollaborationEngine,
)
from core.learning.engine import ContinuousLearningEngine


def test_learning_engine_experience_recording():
    collab_engine = MultiAgentCollaborationEngine()
    learning_engine = ContinuousLearningEngine()
    integration = LearningCollaborationIntegration()

    ctx = collab_engine.execute_preset_workflow("research_writer", "Quantum Computing Breakthroughs")

    recorded = integration.record_collaboration_experience(ctx, learning_engine)
    assert recorded is True

    # Consult experience store to verify recommendation
    recommendation = learning_engine.consult_experience("Quantum Computing Breakthroughs")
    assert recommendation is not None
