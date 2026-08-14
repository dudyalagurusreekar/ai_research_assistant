"""Tests for ToolSelector component."""

import pytest
from core.planner.components.tool_selector import ToolSelector
from core.planner.models.context import PlannerContext, SubTask


class TestToolSelector:
    def setup_method(self):
        self.selector = ToolSelector()
        self.available_tools = [
            {"name": "search_tool", "description": "Web search", "capabilities": ["search"]},
            {"name": "browser_tool", "description": "Browse URLs", "capabilities": ["browse"]},
            {"name": "document_tool", "description": "Document processing", "capabilities": ["document"]},
            {"name": "code_tool", "description": "Code execution", "capabilities": ["code"]},
            {"name": "memory_tool", "description": "Memory store/recall", "capabilities": ["memory"]},
            {"name": "vision_tool", "description": "Image analysis", "capabilities": ["vision"]},
            {"name": "report_tool", "description": "Report generation", "capabilities": ["report"]},
            {"name": "python_interpreter", "description": "Python code execution", "capabilities": ["python"]},
        ]

    def test_component_name(self):
        assert self.selector.component_name == "ToolSelector"

    def test_selects_required_tools_only(self):
        ctx = PlannerContext(user_query="test", available_tools=self.available_tools)
        ctx.sub_tasks = [
            SubTask(tool_name="search_tool"),
            SubTask(tool_name="python_interpreter"),
        ]
        selection = self.selector.select(ctx)
        assert "search_tool" in selection.selected_tools
        assert "python_interpreter" in selection.selected_tools
        assert "vision_tool" in selection.excluded_tools
        assert "memory_tool" in selection.excluded_tools

    def test_reduction_percentage(self):
        ctx = PlannerContext(user_query="test", available_tools=self.available_tools)
        ctx.sub_tasks = [SubTask(tool_name="search_tool")]
        selection = self.selector.select(ctx)
        # Only search_tool + python_interpreter should be selected (2 out of 8)
        assert selection.reduction_percentage > 50.0

    def test_python_interpreter_always_included(self):
        ctx = PlannerContext(user_query="test", available_tools=self.available_tools)
        ctx.sub_tasks = [SubTask(tool_name="memory_tool")]
        selection = self.selector.select(ctx)
        assert "python_interpreter" in selection.selected_tools

    def test_empty_sub_tasks(self):
        ctx = PlannerContext(user_query="test", available_tools=self.available_tools)
        ctx.sub_tasks = []
        selection = self.selector.select(ctx)
        # Only python_interpreter should be selected
        assert "python_interpreter" in selection.selected_tools
        assert len(selection.selected_tools) == 1

    def test_context_attached(self):
        ctx = PlannerContext(user_query="test", available_tools=self.available_tools)
        ctx.sub_tasks = [SubTask(tool_name="search_tool")]
        self.selector.select(ctx)
        assert ctx.tool_selection is not None
        assert ctx.metrics.unnecessary_tools_removed > 0

    def test_all_tools_selected_when_all_needed(self):
        ctx = PlannerContext(user_query="test", available_tools=self.available_tools)
        ctx.sub_tasks = [
            SubTask(tool_name="search_tool"),
            SubTask(tool_name="browser_tool"),
            SubTask(tool_name="document_tool"),
            SubTask(tool_name="code_tool"),
            SubTask(tool_name="memory_tool"),
            SubTask(tool_name="vision_tool"),
            SubTask(tool_name="report_tool"),
        ]
        selection = self.selector.select(ctx)
        assert len(selection.selected_tools) == 8  # all + python_interpreter
        assert selection.reduction_percentage == 0.0
