"""Tests for ParallelPlanner component."""

import pytest
from core.planner.components.parallel_planner import ParallelPlanner
from core.planner.models.context import PlannerContext
from core.planner.models.graph import ExecutionGraph, PlanNode, PlanEdge


class TestParallelPlanner:
    def setup_method(self):
        self.planner = ParallelPlanner()

    def test_component_name(self):
        assert self.planner.component_name == "ParallelPlanner"

    def test_parallel_levels_linear_chain(self):
        """A -> B -> C should produce 3 sequential waves."""
        g = ExecutionGraph()
        g.add_node(PlanNode(node_id="A", title="A"))
        g.add_node(PlanNode(node_id="B", title="B"))
        g.add_node(PlanNode(node_id="C", title="C"))
        g.add_edge(PlanEdge(source_id="A", target_id="B"))
        g.add_edge(PlanEdge(source_id="B", target_id="C"))
        ctx = PlannerContext(user_query="test")
        ctx.execution_graph = g
        levels = self.planner.plan_parallelism(ctx)
        assert len(levels) == 3
        assert levels[0] == ["A"]
        assert levels[1] == ["B"]
        assert levels[2] == ["C"]

    def test_parallel_levels_diamond(self):
        """A -> B, A -> C, B -> D, C -> D should produce 3 waves with B,C parallel."""
        g = ExecutionGraph()
        for nid in ["A", "B", "C", "D"]:
            g.add_node(PlanNode(node_id=nid, title=nid))
        g.add_edge(PlanEdge(source_id="A", target_id="B"))
        g.add_edge(PlanEdge(source_id="A", target_id="C"))
        g.add_edge(PlanEdge(source_id="B", target_id="D"))
        g.add_edge(PlanEdge(source_id="C", target_id="D"))
        ctx = PlannerContext(user_query="test")
        ctx.execution_graph = g
        levels = self.planner.plan_parallelism(ctx)
        assert len(levels) == 3
        assert set(levels[0]) == {"A"}
        assert set(levels[1]) == {"B", "C"}
        assert set(levels[2]) == {"D"}

    def test_parallel_levels_independent_nodes(self):
        """All independent nodes should be in one wave."""
        g = ExecutionGraph()
        for nid in ["A", "B", "C"]:
            g.add_node(PlanNode(node_id=nid, title=nid))
        ctx = PlannerContext(user_query="test")
        ctx.execution_graph = g
        levels = self.planner.plan_parallelism(ctx)
        assert len(levels) == 1
        assert set(levels[0]) == {"A", "B", "C"}

    def test_empty_graph(self):
        ctx = PlannerContext(user_query="test")
        ctx.execution_graph = ExecutionGraph()
        levels = self.planner.plan_parallelism(ctx)
        assert levels == []

    def test_no_graph(self):
        ctx = PlannerContext(user_query="test")
        levels = self.planner.plan_parallelism(ctx)
        assert levels == []

    def test_context_attached(self):
        g = ExecutionGraph()
        g.add_node(PlanNode(node_id="A", title="A"))
        g.add_node(PlanNode(node_id="B", title="B"))
        ctx = PlannerContext(user_query="test")
        ctx.execution_graph = g
        self.planner.plan_parallelism(ctx)
        assert ctx.parallel_groups is not None
        assert ctx.metrics.parallel_groups >= 1
