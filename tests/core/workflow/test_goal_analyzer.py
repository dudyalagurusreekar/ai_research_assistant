"""Unit test for ResearchGoalAnalyzer."""

import pytest

from core.workflow.components.goal_analyzer import ResearchGoalAnalyzer
from core.workflow.models.goal import GoalDomain, GoalPriority


def test_goal_analyzer_deconstruction():
    analyzer = ResearchGoalAnalyzer()
    query = "Compare AI Transformer benchmark accuracy and GPU latency"

    goal = analyzer.analyze_goal(query)

    assert goal.domain == GoalDomain.COMPUTER_SCIENCE
    assert len(goal.primary_objectives) >= 1
    assert "Compare" in goal.primary_objectives[0] or "Synthesize" in goal.primary_objectives[0]
    assert goal.priority == GoalPriority.NORMAL
    assert goal.raw_query == query
