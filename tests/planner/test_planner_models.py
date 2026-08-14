"""Tests for planner data models: PlannerContext, ExecutionGraph, DecisionLog."""

import pytest
from core.planner.models.context import (
    PlannerContext, PlannerStage, QueryAnalysis, QueryIntent,
    ComplexityEstimate, SubTask, ToolSelection, ExecutionConstraints,
    PlannerMetrics,
)
from core.planner.models.graph import ExecutionGraph, PlanNode, PlanEdge, NodeStatus
from core.planner.models.decision import PlannerDecision, DecisionLog


# ==========================================================================
# PlannerContext
# ==========================================================================

class TestPlannerContext:
    def test_default_creation(self):
        ctx = PlannerContext(user_query="test query")
        assert ctx.user_query == "test query"
        assert ctx.current_stage == PlannerStage.INITIALIZED
        assert ctx.plan_id.startswith("plan_")
        assert ctx.intent is None
        assert ctx.errors == []
        assert ctx.reasoning_trace == []

    def test_add_trace(self):
        ctx = PlannerContext(user_query="test")
        ctx.add_trace("stage1", "message1", {"key": "val"})
        assert len(ctx.reasoning_trace) == 1
        assert ctx.reasoning_trace[0]["stage"] == "stage1"
        assert ctx.reasoning_trace[0]["message"] == "message1"
        assert ctx.reasoning_trace[0]["data"]["key"] == "val"

    def test_add_error(self):
        ctx = PlannerContext(user_query="test")
        ctx.add_error("stage1", "something broke", recoverable=False)
        assert len(ctx.errors) == 1
        assert ctx.errors[0]["error"] == "something broke"
        assert ctx.errors[0]["recoverable"] is False

    def test_advance_stage(self):
        ctx = PlannerContext(user_query="test")
        ctx.advance_stage(PlannerStage.QUERY_ANALYZED)
        assert ctx.current_stage == PlannerStage.QUERY_ANALYZED
        assert ctx.metrics.stages_completed == 1

    def test_is_failed(self):
        ctx = PlannerContext(user_query="test")
        assert ctx.is_failed() is False
        ctx.advance_stage(PlannerStage.PLANNING_FAILED)
        assert ctx.is_failed() is True

    def test_to_dict(self):
        ctx = PlannerContext(user_query="test query")
        ctx.intent = QueryIntent.FACTUAL_QA
        result = ctx.to_dict()
        assert result["user_query"] == "test query"
        assert result["intent"] == "factual_qa"
        assert "plan_id" in result


class TestQueryAnalysis:
    def test_defaults(self):
        qa = QueryAnalysis()
        assert qa.raw_query == ""
        assert qa.ambiguity_score == 0.0
        assert qa.entities == []
        assert qa.has_file_reference is False

    def test_custom_values(self):
        qa = QueryAnalysis(
            raw_query="Who won Nobel Prize?",
            entities=["Nobel Prize"],
            keywords=["won", "nobel", "prize"],
            ambiguity_score=0.1,
        )
        assert len(qa.entities) == 1
        assert len(qa.keywords) == 3


class TestSubTask:
    def test_default_creation(self):
        st = SubTask(title="Search", tool_name="search_tool")
        assert st.title == "Search"
        assert st.task_id.startswith("subtask_")
        assert st.dependencies == []

    def test_with_dependencies(self):
        st = SubTask(title="Analyze", dependencies=["dep1", "dep2"])
        assert len(st.dependencies) == 2


class TestPlannerMetrics:
    def test_compute_latency(self):
        from datetime import datetime, timezone, timedelta
        m = PlannerMetrics()
        m.planning_start_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
        m.planning_end_time = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(milliseconds=150)
        m.compute_latency()
        assert 149 < m.planning_latency_ms < 151


# ==========================================================================
# ExecutionGraph
# ==========================================================================

class TestExecutionGraph:
    def _make_graph(self):
        """A -> B -> C, A -> C"""
        g = ExecutionGraph()
        a = PlanNode(node_id="A", title="Task A")
        b = PlanNode(node_id="B", title="Task B")
        c = PlanNode(node_id="C", title="Task C")
        g.add_node(a)
        g.add_node(b)
        g.add_node(c)
        g.add_edge(PlanEdge(source_id="A", target_id="B"))
        g.add_edge(PlanEdge(source_id="B", target_id="C"))
        g.add_edge(PlanEdge(source_id="A", target_id="C"))
        return g

    def test_node_and_edge_counts(self):
        g = self._make_graph()
        assert g.node_count() == 3
        assert g.edge_count() == 3

    def test_get_roots(self):
        g = self._make_graph()
        roots = g.get_roots()
        assert len(roots) == 1
        assert roots[0].node_id == "A"

    def test_get_leaves(self):
        g = self._make_graph()
        leaves = g.get_leaves()
        assert len(leaves) == 1
        assert leaves[0].node_id == "C"

    def test_get_predecessors(self):
        g = self._make_graph()
        preds = g.get_predecessors("C")
        pred_ids = {p.node_id for p in preds}
        assert pred_ids == {"A", "B"}

    def test_get_successors(self):
        g = self._make_graph()
        succs = g.get_successors("A")
        succ_ids = {s.node_id for s in succs}
        assert succ_ids == {"B", "C"}

    def test_topological_sort(self):
        g = self._make_graph()
        sorted_nodes = g.topological_sort()
        ids = [n.node_id for n in sorted_nodes]
        assert ids.index("A") < ids.index("B")
        assert ids.index("B") < ids.index("C")

    def test_has_cycle_false(self):
        g = self._make_graph()
        assert g.has_cycle() is False

    def test_cycle_detection_on_add(self):
        g = ExecutionGraph()
        g.add_node(PlanNode(node_id="X"))
        g.add_node(PlanNode(node_id="Y"))
        g.add_edge(PlanEdge(source_id="X", target_id="Y"))
        with pytest.raises(ValueError, match="cycle"):
            g.add_edge(PlanEdge(source_id="Y", target_id="X"))

    def test_parallel_levels(self):
        g = ExecutionGraph()
        g.add_node(PlanNode(node_id="A"))
        g.add_node(PlanNode(node_id="B"))
        g.add_node(PlanNode(node_id="C"))
        g.add_node(PlanNode(node_id="D"))
        g.add_edge(PlanEdge(source_id="A", target_id="C"))
        g.add_edge(PlanEdge(source_id="B", target_id="C"))
        g.add_edge(PlanEdge(source_id="C", target_id="D"))
        levels = g.compute_parallel_levels()
        assert len(levels) == 3
        assert set(levels[0]) == {"A", "B"}
        assert levels[1] == ["C"]
        assert levels[2] == ["D"]

    def test_remove_node(self):
        g = self._make_graph()
        g.remove_node("B")
        assert g.node_count() == 2
        assert g.edge_count() == 1  # only A->C remains

    def test_add_edge_invalid_node(self):
        g = ExecutionGraph()
        g.add_node(PlanNode(node_id="A"))
        with pytest.raises(ValueError, match="not in graph"):
            g.add_edge(PlanEdge(source_id="A", target_id="MISSING"))

    def test_to_dict(self):
        g = self._make_graph()
        d = g.to_dict()
        assert d["node_count"] == 3
        assert d["edge_count"] == 3
        assert len(d["nodes"]) == 3


class TestPlanNode:
    def test_to_dict(self):
        n = PlanNode(node_id="n1", title="Test", tool_name="tool1", status=NodeStatus.PENDING)
        d = n.to_dict()
        assert d["node_id"] == "n1"
        assert d["status"] == "pending"


# ==========================================================================
# DecisionLog
# ==========================================================================

class TestDecisionLog:
    def test_record(self):
        log = DecisionLog(plan_id="plan_test")
        log.record(stage="s1", component="c1", description="Did thing")
        assert log.count == 1
        assert log.decisions[0].stage == "s1"

    def test_get_by_stage(self):
        log = DecisionLog()
        log.record(stage="alpha", component="c1", description="d1")
        log.record(stage="beta", component="c2", description="d2")
        log.record(stage="alpha", component="c3", description="d3")
        assert len(log.get_by_stage("alpha")) == 2
        assert len(log.get_by_stage("beta")) == 1

    def test_get_by_component(self):
        log = DecisionLog()
        log.record(stage="s1", component="QueryAnalyzer", description="d1")
        log.record(stage="s2", component="IntentClassifier", description="d2")
        assert len(log.get_by_component("QueryAnalyzer")) == 1

    def test_to_dict(self):
        log = DecisionLog(plan_id="plan_x")
        log.record(stage="s1", component="c1", description="d1")
        d = log.to_dict()
        assert d["plan_id"] == "plan_x"
        assert d["decision_count"] == 1
        assert len(d["decisions"]) == 1
