"""Tests for ExecutionIntegration facade."""

import pytest
from core.execution.integration import ExecutionIntegration
from core.execution.models.result import ExecutionStatus
from core.planner.engine import IntelligentPlanningEngine


class TestExecutionIntegration:
    def setup_method(self):
        self.integration = ExecutionIntegration()
        self.planner = IntelligentPlanningEngine()
        self.executors = {
            "search_tool": lambda action, params: "Search Result",
            "browser_tool": lambda action, params: "Browser Result",
            "python_interpreter": lambda action, params: "Python Result",
        }

    def test_select_tools(self):
        ctx = self.planner.plan("Who won Nobel Prize in 2023?")
        self.integration.select_tools(ctx)
        assert ctx.tool_selection is not None
        assert "search_tool" in ctx.tool_selection.selected_tools

    def test_optimize_execution(self):
        ctx = self.planner.plan("Compare GPT-4 vs Claude")
        plan = self.integration.optimize_execution(ctx)
        assert plan.total_nodes > 0
        assert len(plan.execution_waves) >= 1

    def test_execute_task_caching(self):
        # 1st execution: miss, executes, caches
        res1 = self.integration.execute_task(
            task_id="t1",
            tool_name="search_tool",
            action="search",
            parameters={"query": "AI"},
            executors=self.executors,
        )
        assert res1.status == ExecutionStatus.SUCCESS
        assert res1.is_cached is False

        # 2nd execution: hit from cache!
        res2 = self.integration.execute_task(
            task_id="t1",
            tool_name="search_tool",
            action="search",
            parameters={"query": "AI"},
            executors=self.executors,
        )
        assert res2.status == ExecutionStatus.CACHED
        assert res2.is_cached is True
        assert res2.output == "Search Result"

    def test_execute_task_fallback(self):
        def primary_fail(action, params):
            raise RuntimeError("Primary search failed")

        failing_executors = {
            "search_tool": primary_fail,
            "browser_tool": lambda action, params: "Fallback Browser Result",
        }

        res = self.integration.execute_task(
            task_id="t1",
            tool_name="search_tool",
            action="search",
            parameters={"query": "Unique Fail Task"},
            executors=failing_executors,
        )
        assert res.status == ExecutionStatus.DEGRADED
        assert res.output == "Fallback Browser Result"
        assert res.fallback_used == "browser_tool"

    def test_get_telemetry_summary(self):
        telemetry = self.integration.get_telemetry_summary()
        assert "registry" in telemetry
        assert "cache" in telemetry
        assert "fallbacks" in telemetry
