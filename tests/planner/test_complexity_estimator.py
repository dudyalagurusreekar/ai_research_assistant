"""Tests for ComplexityEstimator component."""

import pytest
from core.planner.components.query_analyzer import QueryAnalyzer
from core.planner.components.intent_classifier import IntentClassifier
from core.planner.components.complexity_estimator import ComplexityEstimator
from core.planner.models.context import PlannerContext, QueryIntent


class TestComplexityEstimator:
    def setup_method(self):
        self.analyzer = QueryAnalyzer()
        self.classifier = IntentClassifier()
        self.estimator = ComplexityEstimator()

    def _prepare_ctx(self, query: str) -> PlannerContext:
        ctx = PlannerContext(user_query=query)
        self.analyzer.analyze(ctx)
        self.classifier.classify(ctx)
        return ctx

    def test_component_name(self):
        assert self.estimator.component_name == "ComplexityEstimator"

    def test_simple_factual_qa(self):
        ctx = self._prepare_ctx("Who invented the telephone?")
        estimate = self.estimator.estimate(ctx)
        assert estimate.score <= 4
        assert estimate.estimated_steps <= 4
        assert estimate.estimated_latency_seconds < 60.0

    def test_complex_research(self):
        ctx = self._prepare_ctx("Research the latest advancements in solid-state batteries and compare three manufacturers")
        estimate = self.estimator.estimate(ctx)
        assert estimate.score >= 4
        assert estimate.estimated_steps >= 3

    def test_file_reference_overhead(self):
        ctx = self._prepare_ctx("Read the PDF document and summarize it")
        estimate = self.estimator.estimate(ctx)
        assert estimate.estimated_tokens > 1000

    def test_memory_operation_low_complexity(self):
        ctx = PlannerContext(user_query="store memory_tool this fact")
        self.analyzer.analyze(ctx)
        ctx.intent = QueryIntent.MEMORY_OPERATION
        estimate = self.estimator.estimate(ctx)
        assert estimate.score <= 3
        assert estimate.estimated_steps <= 3

    def test_max_step_limit_reasonable(self):
        ctx = self._prepare_ctx("Do a comprehensive multi-source research on quantum computing")
        estimate = self.estimator.estimate(ctx)
        assert estimate.max_step_limit >= 5
        assert estimate.max_step_limit <= 20

    def test_context_attached(self):
        ctx = self._prepare_ctx("What is AI?")
        self.estimator.estimate(ctx)
        assert ctx.complexity is not None
        assert ctx.complexity.reasoning != ""
