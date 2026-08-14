"""Tests for ReflectionIntegration facade."""

import pytest
from core.planner.engine import IntelligentPlanningEngine
from core.reflection.integration import ReflectionIntegration
from core.reflection.models.reflection import ReflectionAction


class TestReflectionIntegration:
    def setup_method(self):
        self.integration = ReflectionIntegration()
        self.planner = IntelligentPlanningEngine()

    def test_reflect_and_correct(self):
        ctx = self.planner.plan("Compare GPT-4 vs Claude")
        outputs = {
            t.task_id: f"Completed analysis output for {t.title} comparing GPT-4 vs Claude."
            for t in ctx.sub_tasks
        }
        decision = self.integration.reflect_and_correct(ctx, outputs)
        assert decision is not None
        assert decision.action in (ReflectionAction.PROCEED, ReflectionAction.PRUNE_STEPS)

    def test_get_summary(self):
        ctx = self.planner.plan("Test query")
        self.integration.reflect_and_correct(ctx, {"t1": "output"})
        summary = self.integration.get_summary()
        assert "total_decisions" in summary
        assert summary["total_decisions"] >= 1
