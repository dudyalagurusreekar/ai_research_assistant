"""Tests for ReasoningEvaluator."""

import pytest
from core.planner.models.context import PlannerContext, SubTask
from core.reflection.components.reasoning_evaluator import ReasoningEvaluator


class TestReasoningEvaluator:
    def setup_method(self):
        self.evaluator = ReasoningEvaluator()

    def test_evaluate_empty_outputs(self):
        ctx = PlannerContext(user_query="Test query")
        ctx.sub_tasks = [SubTask(task_id="t1", tool_name="search_tool")]
        assess = self.evaluator.evaluate(ctx, {})
        assert assess.completeness_score == 0.0
        assert assess.confidence_score == 0.0
        assert len(assess.unaddressed_aspects) >= 1

    def test_evaluate_full_coverage(self):
        ctx = PlannerContext(user_query="Who won Nobel Prize in 2023?")
        ctx.sub_tasks = [
            SubTask(task_id="t1", tool_name="search_tool"),
            SubTask(task_id="t2", tool_name="python_interpreter"),
        ]
        outputs = {
            "t1": "Pierre Agostini, Ferenc Krausz and Anne L'Huillier won the Nobel Prize in Physics in 2023.",
            "t2": "Synthesized report output.",
        }
        assess = self.evaluator.evaluate(ctx, outputs)
        assert assess.completeness_score == 1.0
        assert assess.hallucination_risk_score < 0.20
        assert assess.confidence_score > 0.80

    def test_evaluate_comparison_unaddressed(self):
        ctx = PlannerContext(user_query="Compare GPT-4 vs Claude")
        ctx.sub_tasks = [SubTask(task_id="t1", tool_name="search_tool")]
        outputs = {"t1": "GPT-4 was released by OpenAI."}  # missing comparison terms
        assess = self.evaluator.evaluate(ctx, outputs)
        assert len(assess.unaddressed_aspects) >= 1
        assert assess.hallucination_risk_score > 0.10
