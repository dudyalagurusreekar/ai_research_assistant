"""Tests for the IntelligentPlanningEngine — full pipeline integration."""

import pytest
from core.planner.engine import IntelligentPlanningEngine
from core.planner.models.context import PlannerStage, QueryIntent


class TestIntelligentPlanningEngine:
    def setup_method(self):
        self.engine = IntelligentPlanningEngine()
        self.tools = [
            {"name": "search_tool", "description": "Web search", "capabilities": ["search"]},
            {"name": "browser_tool", "description": "Browse URLs", "capabilities": ["browse"]},
            {"name": "document_tool", "description": "Document processing", "capabilities": ["document"]},
            {"name": "code_tool", "description": "Code execution", "capabilities": ["code"]},
            {"name": "memory_tool", "description": "Memory operations", "capabilities": ["memory"]},
            {"name": "vision_tool", "description": "Image analysis", "capabilities": ["vision"]},
            {"name": "report_tool", "description": "Report generation", "capabilities": ["report"]},
            {"name": "python_interpreter", "description": "Python execution", "capabilities": ["python"]},
        ]

    def test_full_pipeline_factual_qa(self):
        ctx = self.engine.plan("Who won the Nobel Prize in Physics in 2023?", self.tools)
        assert ctx.current_stage == PlannerStage.PLANNING_COMPLETE
        assert ctx.query_analysis is not None
        assert ctx.intent is not None
        assert ctx.complexity is not None
        assert len(ctx.sub_tasks) > 0
        assert ctx.execution_graph is not None
        assert ctx.tool_selection is not None
        assert ctx.metrics.planning_latency_ms > 0
        assert ctx.metrics.stages_completed == 10
        assert len(ctx.errors) == 0

    def test_full_pipeline_comparison(self):
        ctx = self.engine.plan("Compare GPT-4 versus Claude in NLP tasks", self.tools)
        assert ctx.current_stage == PlannerStage.PLANNING_COMPLETE
        assert ctx.intent == QueryIntent.COMPARISON
        assert len(ctx.sub_tasks) >= 2

    def test_full_pipeline_code_execution(self):
        ctx = self.engine.plan("Using code_tool, execute a Python fibonacci script", self.tools)
        assert ctx.current_stage == PlannerStage.PLANNING_COMPLETE
        assert ctx.intent == QueryIntent.CODE_EXECUTION
        assert ctx.constraints.require_verification is False

    def test_full_pipeline_document_analysis(self):
        ctx = self.engine.plan("Read the PDF file and summarize the content", self.tools)
        assert ctx.current_stage == PlannerStage.PLANNING_COMPLETE
        assert ctx.intent == QueryIntent.DOCUMENT_ANALYSIS

    def test_full_pipeline_multi_step_research(self):
        ctx = self.engine.plan(
            "Research the latest advancements in solid-state batteries and summarize key players",
            self.tools
        )
        assert ctx.current_stage == PlannerStage.PLANNING_COMPLETE
        assert len(ctx.sub_tasks) >= 2
        assert ctx.execution_graph.node_count() >= 2

    def test_full_pipeline_memory_operation(self):
        ctx = self.engine.plan("Using memory_tool, store this fact: ARA v2 launched", self.tools)
        assert ctx.current_stage == PlannerStage.PLANNING_COMPLETE
        assert ctx.intent == QueryIntent.MEMORY_OPERATION
        assert ctx.constraints.max_steps <= 5

    def test_tool_reduction(self):
        ctx = self.engine.plan("Who is the CEO of Google?", self.tools)
        assert ctx.tool_selection is not None
        assert ctx.tool_selection.reduction_percentage > 0
        assert len(ctx.tool_selection.excluded_tools) > 0

    def test_parallel_groups_generated(self):
        ctx = self.engine.plan("Compare GPT-4 versus Claude", self.tools)
        assert ctx.parallel_groups is not None
        assert len(ctx.parallel_groups) >= 1

    def test_dag_is_acyclic(self):
        ctx = self.engine.plan("Research quantum computing", self.tools)
        assert ctx.execution_graph.has_cycle() is False

    def test_reasoning_trace_populated(self):
        ctx = self.engine.plan("What is machine learning?", self.tools)
        assert len(ctx.reasoning_trace) >= 5

    def test_planning_latency_sub_second(self):
        """The deterministic planner should complete in under 1 second."""
        ctx = self.engine.plan("Who invented the telephone?", self.tools)
        assert ctx.metrics.planning_latency_ms < 1000

    def test_to_dict_serialization(self):
        ctx = self.engine.plan("What is AI?", self.tools)
        d = ctx.to_dict()
        assert "plan_id" in d
        assert "intent" in d
        assert "metrics" in d

    def test_empty_query(self):
        ctx = self.engine.plan("", self.tools)
        assert ctx.current_stage == PlannerStage.PLANNING_COMPLETE
        assert len(ctx.sub_tasks) > 0

    def test_no_tools_available(self):
        ctx = self.engine.plan("What is AI?", [])
        assert ctx.current_stage == PlannerStage.PLANNING_COMPLETE
        assert ctx.tool_selection is not None
