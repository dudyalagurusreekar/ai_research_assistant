"""Tests for planner integration adapters."""

import pytest
from core.planner.engine import IntelligentPlanningEngine
from core.planner.integration import (
    AgentPlannerIntegration,
    PlannerPromptAdapter,
    PlannerWorkflowAdapter,
)
from core.planner.models.context import PlannerContext, PlannerStage


class TestPlannerPromptAdapter:
    def setup_method(self):
        self.adapter = PlannerPromptAdapter()
        self.engine = IntelligentPlanningEngine()
        self.tools = [
            {"name": "search_tool", "description": "Search", "capabilities": ["search"]},
            {"name": "python_interpreter", "description": "Python", "capabilities": ["python"]},
        ]

    def test_generates_prompt(self):
        ctx = self.engine.plan("Who won Nobel Prize 2023?", self.tools)
        prompt = self.adapter.generate_prompt_injection(ctx)
        assert "EXECUTION PLAN" in prompt
        assert "Intent" in prompt
        assert "Constraints" in prompt

    def test_empty_on_failed_plan(self):
        ctx = PlannerContext(user_query="test")
        ctx.advance_stage(PlannerStage.PLANNING_FAILED)
        prompt = self.adapter.generate_prompt_injection(ctx)
        assert prompt == ""

    def test_includes_selected_tools(self):
        ctx = self.engine.plan("Search for AI news", self.tools)
        prompt = self.adapter.generate_prompt_injection(ctx)
        assert "Selected Tools" in prompt

    def test_includes_step_plan(self):
        ctx = self.engine.plan("Compare GPT vs Claude", self.tools)
        prompt = self.adapter.generate_prompt_injection(ctx)
        assert "Planned Steps" in prompt


class TestPlannerWorkflowAdapter:
    def setup_method(self):
        self.adapter = PlannerWorkflowAdapter()
        self.engine = IntelligentPlanningEngine()
        self.tools = [
            {"name": "search_tool", "description": "Search", "capabilities": ["search"]},
            {"name": "python_interpreter", "description": "Python", "capabilities": ["python"]},
        ]

    def test_generates_workflow_tasks(self):
        ctx = self.engine.plan("What is machine learning?", self.tools)
        tasks = self.adapter.to_workflow_tasks(ctx)
        assert len(tasks) > 0
        assert "task_id" in tasks[0]
        assert "tool_name" in tasks[0]

    def test_empty_on_failed(self):
        ctx = PlannerContext(user_query="test")
        ctx.advance_stage(PlannerStage.PLANNING_FAILED)
        tasks = self.adapter.to_workflow_tasks(ctx)
        assert tasks == []


class TestAgentPlannerIntegration:
    def setup_method(self):
        self.integration = AgentPlannerIntegration()
        self.tools = [
            {"name": "search_tool", "description": "Search", "capabilities": ["search"]},
            {"name": "python_interpreter", "description": "Python", "capabilities": ["python"]},
        ]

    def test_plan_for_agent(self):
        ctx = self.integration.plan_for_agent("What is AI?", self.tools)
        assert ctx.current_stage == PlannerStage.PLANNING_COMPLETE
        assert ctx.intent is not None

    def test_get_prompt_hint(self):
        ctx = self.integration.plan_for_agent("What is AI?", self.tools)
        hint = self.integration.get_prompt_hint(ctx)
        assert "EXECUTION PLAN" in hint

    def test_get_workflow_tasks(self):
        ctx = self.integration.plan_for_agent("What is AI?", self.tools)
        tasks = self.integration.get_workflow_tasks(ctx)
        assert len(tasks) > 0

    def test_get_planning_summary(self):
        ctx = self.integration.plan_for_agent("What is AI?", self.tools)
        summary = self.integration.get_planning_summary(ctx)
        assert "plan_id" in summary
        assert "intent" in summary
