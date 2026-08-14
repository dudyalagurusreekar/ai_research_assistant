"""End-to-end reflection benchmark tests for Sprint 4."""

import pytest
from core.planner.engine import IntelligentPlanningEngine
from core.reflection.integration import ReflectionIntegration
from core.reflection.models.reflection import ReflectionAction, EvidenceQuality


class TestReflectionE2E:
    def setup_method(self):
        self.integration = ReflectionIntegration()
        self.planner = IntelligentPlanningEngine()

    def test_e2e_successful_reflection(self):
        ctx = self.planner.plan("Who won Nobel Prize in Physics in 2023?")
        outputs = {
            ctx.sub_tasks[0].task_id: {"source": "search_tool", "text": "Pierre Agostini, Ferenc Krausz and Anne L'Huillier won the Nobel Prize in Physics in 2023 with detailed facts."},
            ctx.sub_tasks[1].task_id: {"source": "browser_tool", "text": "Official announcement confirming Pierre Agostini, Ferenc Krausz and Anne L'Huillier won Nobel Prize in 2023."},
        }
        decision = self.integration.reflect_and_correct(ctx, outputs)
        assert decision.action == ReflectionAction.PROCEED
        assert decision.evidence_assessment.quality == EvidenceQuality.HIGH
        assert decision.reasoning_assessment.completeness_score == 1.0

    def test_e2e_conflict_detection_and_resolution(self):
        ctx = self.planner.plan("When was CRISPR invented?")
        outputs = {
            "node_1": "CRISPR gene editing technology was invented in 2012 by Doudna and Charpentier.",
            "node_2": "Source B claims CRISPR was invented in 2023, however this conflicts with previous reports.",
        }
        decision = self.integration.reflect_and_correct(ctx, outputs)
        assert decision.action == ReflectionAction.RESOLVE_CONFLICT
        assert len(ctx.sub_tasks) > 2  # New task injected into context!
        assert "Conflict" in ctx.sub_tasks[-1].title

    def test_e2e_weak_evidence_replan_injection(self):
        ctx = self.planner.plan("Analyze solid state battery advancements in 2024")
        outputs = {}  # Empty / weak outputs

        decision = self.integration.reflect_and_correct(ctx, outputs)
        assert decision.action == ReflectionAction.GATHER_MORE_EVIDENCE
        assert len(decision.nodes_to_add) == 1
        assert "Deep Evidence" in ctx.sub_tasks[-1].title
