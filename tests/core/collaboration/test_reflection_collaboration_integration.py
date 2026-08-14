"""Integration tests for Reflection Engine evaluation and multi-agent replanning coordination."""

import pytest

from core.collaboration import (
    MultiAgentCollaborationEngine,
    ReflectionCollaborationIntegration,
)
from core.reflection.engine import ReflectionEngine


def test_reflection_integration_on_collaboration():
    collab_engine = MultiAgentCollaborationEngine()
    reflection_engine = ReflectionEngine()
    integration = ReflectionCollaborationIntegration(collab_engine)

    ctx = collab_engine.execute_preset_workflow("code_reviewer", "Optimize Sorting Algorithm")

    reflected_ctx = integration.evaluate_and_replan_if_needed(ctx, reflection_engine)
    assert reflected_ctx is not None
    assert reflected_ctx.session_id == ctx.session_id
