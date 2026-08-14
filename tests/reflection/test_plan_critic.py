"""Tests for PlanCritic."""

import pytest
from core.planner.models.context import PlannerContext
from core.planner.models.graph import ExecutionGraph, PlanNode
from core.reflection.components.plan_critic import PlanCritic


class TestPlanCritic:
    def setup_method(self):
        self.critic = PlanCritic()

    def test_critique_empty_graph(self):
        ctx = PlannerContext(user_query="test")
        report = self.critic.critique(ctx, {})
        assert report.has_issues is False

    def test_critique_detects_redundant_nodes(self):
        g = ExecutionGraph()
        g.add_node(PlanNode(node_id="A", tool_name="search_tool", action="search", parameters={"q": "AI"}))
        g.add_node(PlanNode(node_id="B", tool_name="search_tool", action="search", parameters={"q": "AI"}))
        ctx = PlannerContext(user_query="test")
        ctx.execution_graph = g

        report = self.critic.critique(ctx, {"A": "res1", "B": "res1"})
        assert "B" in report.redundant_node_ids
        assert report.has_issues is True

    def test_critique_detects_dead_end_empty_nodes(self):
        g = ExecutionGraph()
        g.add_node(PlanNode(node_id="A", tool_name="search_tool", action="search"))
        ctx = PlannerContext(user_query="test")
        ctx.execution_graph = g

        report = self.critic.critique(ctx, {"A": ""})  # empty output
        assert "A" in report.dead_end_node_ids
        assert "A" in report.suggested_prunings
