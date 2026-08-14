"""Tests for DAGGenerator component."""

import pytest
from core.planner.components.query_analyzer import QueryAnalyzer
from core.planner.components.intent_classifier import IntentClassifier
from core.planner.components.task_decomposer import TaskDecomposer
from core.planner.components.dag_generator import DAGGenerator
from core.planner.models.context import PlannerContext, SubTask


class TestDAGGenerator:
    def setup_method(self):
        self.analyzer = QueryAnalyzer()
        self.classifier = IntentClassifier()
        self.decomposer = TaskDecomposer()
        self.generator = DAGGenerator()

    def _prepare_ctx(self, query: str) -> PlannerContext:
        ctx = PlannerContext(user_query=query)
        self.analyzer.analyze(ctx)
        self.classifier.classify(ctx)
        self.decomposer.decompose(ctx)
        return ctx

    def test_component_name(self):
        assert self.generator.component_name == "DAGGenerator"

    def test_dag_generation_basic(self):
        ctx = self._prepare_ctx("Who won the Nobel Prize in 2023?")
        graph = self.generator.generate(ctx)
        assert graph.node_count() >= 1
        assert graph.has_cycle() is False

    def test_dag_edges_from_dependencies(self):
        ctx = self._prepare_ctx("Who won the Nobel Prize in 2023?")
        graph = self.generator.generate(ctx)
        if len(ctx.sub_tasks) >= 2:
            assert graph.edge_count() >= 1

    def test_dag_no_cycle(self):
        ctx = self._prepare_ctx("Compare GPT-4 versus Claude")
        graph = self.generator.generate(ctx)
        assert graph.has_cycle() is False

    def test_dag_topological_sort_succeeds(self):
        ctx = self._prepare_ctx("Research quantum computing advancements")
        graph = self.generator.generate(ctx)
        sorted_nodes = graph.topological_sort()
        assert len(sorted_nodes) == graph.node_count()

    def test_dag_context_attached(self):
        ctx = self._prepare_ctx("What is machine learning?")
        self.generator.generate(ctx)
        assert ctx.execution_graph is not None
        assert ctx.metrics.dag_node_count >= 1

    def test_dag_with_manual_subtasks(self):
        """Test DAG generation with explicitly crafted sub-tasks."""
        ctx = PlannerContext(user_query="test")
        t1 = SubTask(task_id="t1", title="Task 1", tool_name="search_tool", output_keys=["r1"])
        t2 = SubTask(task_id="t2", title="Task 2", tool_name="browser_tool", output_keys=["r2"])
        t3 = SubTask(task_id="t3", title="Task 3", tool_name="python_interpreter",
                     dependencies=["t1", "t2"], input_keys=["r1", "r2"])
        ctx.sub_tasks = [t1, t2, t3]
        graph = self.generator.generate(ctx)
        assert graph.node_count() == 3
        assert graph.edge_count() == 2
        assert graph.has_cycle() is False
        roots = graph.get_roots()
        assert len(roots) == 2
        leaves = graph.get_leaves()
        assert len(leaves) == 1

    def test_dag_handles_missing_dependency(self):
        """Missing dependency should be logged but not crash."""
        ctx = PlannerContext(user_query="test")
        t1 = SubTask(task_id="t1", title="Task 1", tool_name="search_tool")
        t2 = SubTask(task_id="t2", title="Task 2", tool_name="browser_tool",
                     dependencies=["nonexistent"])
        ctx.sub_tasks = [t1, t2]
        graph = self.generator.generate(ctx)
        assert graph.node_count() == 2
        assert graph.edge_count() == 0
