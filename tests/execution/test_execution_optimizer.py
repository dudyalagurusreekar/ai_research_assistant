"""Tests for ExecutionOptimizationEngine."""

import pytest
from core.execution.cache import ToolResultCache
from core.execution.optimizer import ExecutionOptimizationEngine
from core.execution.registry import AdaptiveToolRegistry
from core.planner.models.context import PlannerContext
from core.planner.models.graph import ExecutionGraph, PlanEdge, PlanNode


class TestExecutionOptimizationEngine:
    def setup_method(self):
        self.registry = AdaptiveToolRegistry()
        self.cache = ToolResultCache()
        self.optimizer = ExecutionOptimizationEngine(registry=self.registry, cache=self.cache)

    def test_optimize_empty_graph(self):
        ctx = PlannerContext(user_query="test")
        plan = self.optimizer.optimize(ctx)
        assert plan.total_nodes == 0

    def test_optimize_linear_dag(self):
        g = ExecutionGraph()
        g.add_node(PlanNode(node_id="A", tool_name="search_tool", action="search", parameters={"q": "1"}))
        g.add_node(PlanNode(node_id="B", tool_name="python_interpreter", action="synthesize"))
        g.add_edge(PlanEdge(source_id="A", target_id="B"))
        ctx = PlannerContext(user_query="test")
        ctx.execution_graph = g

        plan = self.optimizer.optimize(ctx)
        assert plan.total_nodes == 2
        assert plan.cached_nodes == 0
        assert plan.runnable_nodes == 2
        assert len(plan.execution_waves) == 2
        assert plan.parallelization_efficiency == 1.0

    def test_optimize_with_cached_node(self):
        # Pre-populate cache for search_tool
        self.cache.put("search_tool", "search", {"q": "1"}, "Cached Output")

        g = ExecutionGraph()
        g.add_node(PlanNode(node_id="A", tool_name="search_tool", action="search", parameters={"q": "1"}))
        g.add_node(PlanNode(node_id="B", tool_name="python_interpreter", action="synthesize"))
        g.add_edge(PlanEdge(source_id="A", target_id="B"))
        ctx = PlannerContext(user_query="test")
        ctx.execution_graph = g

        plan = self.optimizer.optimize(ctx)
        assert plan.total_nodes == 2
        assert plan.cached_nodes == 1
        assert plan.runnable_nodes == 1
        assert plan.execution_waves[0][0].is_cached is True

    def test_optimize_parallel_waves(self):
        g = ExecutionGraph()
        g.add_node(PlanNode(node_id="A", tool_name="search_tool", action="search"))
        g.add_node(PlanNode(node_id="B", tool_name="browser_tool", action="browse"))
        g.add_node(PlanNode(node_id="C", tool_name="python_interpreter", action="synthesize"))
        g.add_edge(PlanEdge(source_id="A", target_id="C"))
        g.add_edge(PlanEdge(source_id="B", target_id="C"))
        ctx = PlannerContext(user_query="test")
        ctx.execution_graph = g

        plan = self.optimizer.optimize(ctx)
        assert plan.total_nodes == 3
        assert len(plan.execution_waves) == 2
        assert len(plan.execution_waves[0]) == 2  # A and B in parallel wave 0
        assert plan.parallelization_efficiency > 1.0
