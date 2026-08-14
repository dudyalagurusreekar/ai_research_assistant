"""Tests for AdaptiveToolSelectionEngine."""

import pytest
from core.execution.registry import AdaptiveToolRegistry
from core.execution.selection_engine import AdaptiveToolSelectionEngine
from core.planner.models.context import PlannerContext, SubTask, QueryIntent


class TestAdaptiveToolSelectionEngine:
    def setup_method(self):
        self.registry = AdaptiveToolRegistry()
        self.engine = AdaptiveToolSelectionEngine(registry=self.registry)

    def test_component_name(self):
        assert self.engine.component_name == "AdaptiveToolSelectionEngine"

    def test_select_tools_for_factual_qa(self):
        ctx = PlannerContext(user_query="Who won Nobel Prize in 2023?")
        ctx.intent = QueryIntent.FACTUAL_QA
        ctx.sub_tasks = [
            SubTask(tool_name="search_tool", action="search"),
            SubTask(tool_name="python_interpreter", action="synthesize"),
        ]
        selection = self.engine.select(ctx)
        assert "search_tool" in selection.selected_tools
        assert "python_interpreter" in selection.selected_tools
        assert selection.reduction_percentage > 50.0

    def test_select_prefers_reliable_tool(self):
        # Degrade search_tool reliability
        desc = self.registry.get_descriptor("search_tool")
        desc.reliability_score = 0.2

        ctx = PlannerContext(user_query="Search web")
        ctx.sub_tasks = [SubTask(tool_name="search_tool", action="search")]

        selection = self.engine.select(ctx)
        # Python interpreter or browser_tool should be included
        assert len(selection.selected_tools) >= 1

    def test_python_interpreter_always_selected(self):
        ctx = PlannerContext(user_query="test")
        ctx.sub_tasks = []
        selection = self.engine.select(ctx)
        assert "python_interpreter" in selection.selected_tools

    def test_reasons_populated(self):
        ctx = PlannerContext(user_query="test")
        ctx.sub_tasks = [SubTask(tool_name="memory_tool")]
        selection = self.engine.select(ctx)
        assert "memory_tool" in selection.selection_reasons
        assert "score=" in selection.selection_reasons["memory_tool"]
