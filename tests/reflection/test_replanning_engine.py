"""Tests for AdaptiveReplanningEngine."""

import pytest
from core.planner.models.context import PlannerContext, SubTask
from core.planner.models.graph import ExecutionGraph, PlanNode
from core.reflection.components.replanning_engine import AdaptiveReplanningEngine
from core.reflection.models.reflection import ReflectionAction, ReflectionDecision


class TestAdaptiveReplanningEngine:
    def setup_method(self):
        self.engine = AdaptiveReplanningEngine()

    def test_prune_nodes(self):
        g = ExecutionGraph()
        g.add_node(PlanNode(node_id="A", tool_name="search_tool"))
        g.add_node(PlanNode(node_id="B", tool_name="search_tool"))
        ctx = PlannerContext(user_query="test")
        ctx.execution_graph = g
        ctx.sub_tasks = [SubTask(task_id="A"), SubTask(task_id="B")]

        decision = ReflectionDecision(
            action=ReflectionAction.PRUNE_STEPS,
            nodes_to_remove=["B"],
        )
        modified = self.engine.apply_replan(ctx, decision)
        assert modified is True
        assert "B" not in ctx.execution_graph.nodes
        assert len(ctx.sub_tasks) == 1

    def test_inject_subtask(self):
        g = ExecutionGraph()
        ctx = PlannerContext(user_query="test")
        ctx.execution_graph = g

        decision = ReflectionDecision(
            action=ReflectionAction.RESOLVE_CONFLICT,
            nodes_to_add=[{
                "tool_name": "search_tool",
                "action": "search",
                "title": "Resolve conflict",
            }],
        )
        modified = self.engine.apply_replan(ctx, decision)
        assert modified is True
        assert len(ctx.sub_tasks) == 1
        assert ctx.sub_tasks[0].title == "Resolve conflict"
        assert ctx.execution_graph.node_count() == 1
