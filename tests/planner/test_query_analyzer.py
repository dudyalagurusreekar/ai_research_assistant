"""Tests for QueryAnalyzer component."""

import pytest
from core.planner.components.query_analyzer import QueryAnalyzer
from core.planner.models.context import PlannerContext


class TestQueryAnalyzer:
    def setup_method(self):
        self.analyzer = QueryAnalyzer()

    def test_component_name(self):
        assert self.analyzer.component_name == "QueryAnalyzer"

    def test_basic_query(self):
        ctx = PlannerContext(user_query="Who won the Nobel Prize in Physics in 2023?")
        result = self.analyzer.analyze(ctx)
        assert result.raw_query == "Who won the Nobel Prize in Physics in 2023?"
        assert "Nobel Prize" in result.entities or "Physics" in result.entities
        assert len(result.keywords) > 0
        assert result.ambiguity_score < 0.5

    def test_file_reference_detection(self):
        ctx = PlannerContext(user_query="Summarize the PDF document about machine learning")
        result = self.analyzer.analyze(ctx)
        assert result.has_file_reference is True

    def test_url_detection(self):
        ctx = PlannerContext(user_query="Visit https://example.com and extract the content")
        result = self.analyzer.analyze(ctx)
        assert result.has_url_reference is True

    def test_code_detection(self):
        ctx = PlannerContext(user_query="Execute a Python script that calculates fibonacci numbers")
        result = self.analyzer.analyze(ctx)
        assert result.has_code_request is True

    def test_comparison_detection(self):
        ctx = PlannerContext(user_query="Compare GPT-4 versus Claude in terms of performance")
        result = self.analyzer.analyze(ctx)
        assert result.has_comparison is True

    def test_source_count_comparison(self):
        ctx = PlannerContext(user_query="Compare three different approaches to machine learning")
        result = self.analyzer.analyze(ctx)
        assert result.source_count_hint >= 2

    def test_ambiguity_short_query(self):
        ctx = PlannerContext(user_query="cats")
        result = self.analyzer.analyze(ctx)
        assert result.ambiguity_score > 0.2

    def test_research_requirements_inferred(self):
        ctx = PlannerContext(user_query="Research the latest advancements in quantum computing")
        result = self.analyzer.analyze(ctx)
        assert "web_search" in result.research_requirements

    def test_memory_requirement(self):
        ctx = PlannerContext(user_query="Remember that the meeting is on Friday")
        result = self.analyzer.analyze(ctx)
        assert "memory_operation" in result.research_requirements

    def test_context_attached(self):
        ctx = PlannerContext(user_query="What is AI?")
        self.analyzer.analyze(ctx)
        assert ctx.query_analysis is not None
        assert len(ctx.reasoning_trace) > 0

    def test_empty_query(self):
        ctx = PlannerContext(user_query="")
        result = self.analyzer.analyze(ctx)
        assert result.keywords == []
        assert result.entities == []
