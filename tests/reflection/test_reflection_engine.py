"""Tests for ReflectionEngine."""

import pytest
from core.planner.models.context import PlannerContext, SubTask
from core.reflection.engine import ReflectionEngine
from core.reflection.models.reflection import ReflectionAction


class TestReflectionEngine:
    def setup_method(self):
        self.engine = ReflectionEngine()

    def test_evaluate_and_reflect_proceed(self):
        ctx = PlannerContext(user_query="Who won Nobel Prize in 2023?")
        ctx.sub_tasks = [SubTask(task_id="t1", tool_name="search_tool")]
        outputs = {"t1": "Pierre Agostini, Ferenc Krausz and Anne L'Huillier won in 2023."}

        decision = self.engine.evaluate_and_reflect(ctx, outputs, iteration=1)
        assert decision.action == ReflectionAction.PROCEED
        assert "meets criteria" in decision.rationale

    def test_evaluate_and_reflect_resolve_conflict(self):
        ctx = PlannerContext(user_query="When was CRISPR invented?")
        outputs = {
            "search_tool": "Source A says CRISPR was invented in 2012.",
            "browser_tool": "Source B claims CRISPR was invented in 2023, however this conflicts with previous reports.",
        }

        decision = self.engine.evaluate_and_reflect(ctx, outputs, iteration=1)
        assert decision.action == ReflectionAction.RESOLVE_CONFLICT
        assert len(decision.nodes_to_add) == 1
        assert "Conflict" in decision.nodes_to_add[0]["title"]

    def test_evaluate_and_reflect_gather_evidence(self):
        ctx = PlannerContext(user_query="Detailed solid state battery analysis")
        outputs = {}  # Empty weak outputs

        decision = self.engine.evaluate_and_reflect(ctx, outputs, iteration=1)
        assert decision.action == ReflectionAction.GATHER_MORE_EVIDENCE
        assert len(decision.nodes_to_add) == 1

    def test_evaluate_and_reflect_max_loops_force_proceed(self):
        ctx = PlannerContext(user_query="test")
        outputs = {}

        # Loop count 4 > policy max (3) -> force PROCEED
        decision = self.engine.evaluate_and_reflect(ctx, outputs, iteration=4)
        assert decision.action == ReflectionAction.PROCEED
        assert "Max reflection loops" in decision.rationale
