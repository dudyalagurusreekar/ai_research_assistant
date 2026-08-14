"""Unit tests for Real-World Scenarios and AI Benchmarks evaluation runner."""

import os
import sys
import pytest

from scripts.evaluate_realworld_scenarios import REALWORLD_SCENARIOS, REALWORLD_SCENARIOS
from core.planner.engine import IntelligentPlanningEngine

def test_realworld_scenarios_schema():
    assert len(REALWORLD_SCENARIOS) == 6
    for sc in REALWORLD_SCENARIOS:
        assert "id" in sc
        assert "category" in sc
        assert "query" in sc
        assert "type" in sc

def test_realworld_scenario_planner_integration():
    sc = REALWORLD_SCENARIOS[5] # RW6
    engine = IntelligentPlanningEngine()
    tools = [
        {"name": "search_tool", "description": "Web search"},
        {"name": "document_tool", "description": "Document analysis"},
        {"name": "code_tool", "description": "Code execution"},
        {"name": "report_tool", "description": "Report validation"},
    ]
    ctx = engine.plan(sc["query"], tools)
    assert ctx.sub_tasks is not None
    assert len(ctx.sub_tasks) > 0
    assert ctx.metrics.planning_latency_ms < 200.0 # Sub-second deterministic planning
    assert ctx.tool_selection.reduction_percentage >= 0.0
