"""Tests for ToolFallbackEngine."""

import pytest
from core.execution.fallback import ToolFallbackEngine
from core.execution.models.result import ExecutionStatus
from core.execution.registry import AdaptiveToolRegistry


class TestToolFallbackEngine:
    def setup_method(self):
        self.registry = AdaptiveToolRegistry()
        self.engine = ToolFallbackEngine(registry=self.registry, circuit_breaker_threshold=3)

    def test_default_fallback_chain(self):
        fallbacks = self.engine.get_fallbacks("search_tool")
        assert "browser_tool" in fallbacks or "python_interpreter" in fallbacks

    def test_primary_tool_success(self):
        executors = {
            "search_tool": lambda action, params: "Primary Output",
        }
        res = self.engine.execute_with_fallback(
            primary_tool="search_tool",
            action="search",
            parameters={"query": "test"},
            task_id="t1",
            executors=executors,
        )
        assert res.status == ExecutionStatus.SUCCESS
        assert res.output == "Primary Output"
        assert res.fallback_used is None

    def test_primary_tool_fails_fallback_succeeds(self):
        def primary_fail(action, params):
            raise RuntimeError("Primary search failed")

        executors = {
            "search_tool": primary_fail,
            "browser_tool": lambda action, params: "Fallback Browser Output",
        }
        res = self.engine.execute_with_fallback(
            primary_tool="search_tool",
            action="search",
            parameters={"query": "test"},
            task_id="t1",
            executors=executors,
        )
        assert res.status == ExecutionStatus.DEGRADED
        assert res.output == "Fallback Browser Output"
        assert res.fallback_used == "browser_tool"
        assert len(self.engine.fallback_events) == 1
        assert self.engine.fallback_events[0].success is True

    def test_all_candidates_fail(self):
        def fail(action, params):
            raise RuntimeError("Tool failed")

        executors = {
            "search_tool": fail,
            "browser_tool": fail,
            "python_interpreter": fail,
        }
        res = self.engine.execute_with_fallback(
            primary_tool="search_tool",
            action="search",
            parameters={"query": "test"},
            task_id="t1",
            executors=executors,
        )
        assert res.status == ExecutionStatus.FAILURE
        assert "All tools in fallback chain failed" in res.error_message

    def test_circuit_breaker_opens_after_failures(self):
        def fail(action, params):
            raise RuntimeError("Failure")

        executors = {"search_tool": fail, "browser_tool": lambda a, p: "Fallback OK"}

        # 3 consecutive failures to trigger circuit breaker
        for i in range(3):
            self.engine.execute_with_fallback("search_tool", "search", {}, f"task_{i}", executors)

        assert self.engine.is_circuit_open("search_tool") is True

        # Next attempt should bypass primary tool immediately due to circuit breaker
        res = self.engine.execute_with_fallback("search_tool", "search", {}, "task_4", executors)
        assert res.output == "Fallback OK"
        assert res.fallback_used == "browser_tool"

    def test_custom_fallback_chain(self):
        self.engine.register_fallback_chain("custom_tool", ["search_tool"])
        fallbacks = self.engine.get_fallbacks("custom_tool")
        assert fallbacks == ["search_tool"]
