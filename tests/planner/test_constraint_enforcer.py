"""Tests for ConstraintEnforcer component."""

import pytest
from core.planner.components.constraint_enforcer import ConstraintEnforcer
from core.planner.models.context import PlannerContext, QueryIntent, ComplexityEstimate


class TestConstraintEnforcer:
    def setup_method(self):
        self.enforcer = ConstraintEnforcer()

    def test_component_name(self):
        assert self.enforcer.component_name == "ConstraintEnforcer"

    def test_default_constraints(self):
        ctx = PlannerContext(user_query="test")
        ctx.intent = QueryIntent.AMBIGUOUS
        constraints = self.enforcer.enforce(ctx)
        assert constraints.max_steps > 0
        assert constraints.timeout_seconds > 0
        assert len(constraints.stopping_criteria) > 0

    def test_code_execution_no_verification(self):
        ctx = PlannerContext(user_query="test")
        ctx.intent = QueryIntent.CODE_EXECUTION
        ctx.complexity = ComplexityEstimate(score=3, estimated_steps=2, max_step_limit=10)
        constraints = self.enforcer.enforce(ctx)
        assert constraints.require_verification is False
        assert constraints.max_retries_per_step == 3

    def test_factual_qa_requires_verification(self):
        ctx = PlannerContext(user_query="test")
        ctx.intent = QueryIntent.FACTUAL_QA
        ctx.complexity = ComplexityEstimate(score=2, estimated_steps=2, max_step_limit=10)
        constraints = self.enforcer.enforce(ctx)
        assert constraints.require_verification is True

    def test_memory_operation_short_timeout(self):
        ctx = PlannerContext(user_query="test")
        ctx.intent = QueryIntent.MEMORY_OPERATION
        ctx.complexity = ComplexityEstimate(score=1, estimated_steps=1, max_step_limit=5,
                                            estimated_latency_seconds=5.0)
        constraints = self.enforcer.enforce(ctx)
        assert constraints.max_steps <= 5
        assert constraints.timeout_seconds <= 60.0

    def test_research_high_steps(self):
        ctx = PlannerContext(user_query="test")
        ctx.intent = QueryIntent.MULTI_STEP_RESEARCH
        ctx.complexity = ComplexityEstimate(score=7, estimated_steps=6, max_step_limit=15,
                                            estimated_latency_seconds=60.0)
        constraints = self.enforcer.enforce(ctx)
        assert constraints.max_steps >= 10
        assert constraints.allow_parallel is True

    def test_context_attached(self):
        ctx = PlannerContext(user_query="test")
        ctx.intent = QueryIntent.FACTUAL_QA
        self.enforcer.enforce(ctx)
        assert ctx.constraints is not None
        assert len(ctx.constraints.stopping_criteria) > 0
        assert len(ctx.reasoning_trace) > 0
