"""Unit test for ReportComposer."""

import pytest

from core.workflow.components.goal_analyzer import ResearchGoalAnalyzer
from core.workflow.components.question_generator import ResearchQuestionGenerator
from core.workflow.components.report_composer import ReportComposer


def test_report_composer_synthesis():
    analyzer = ResearchGoalAnalyzer()
    q_gen = ResearchQuestionGenerator()
    composer = ReportComposer()

    goal = analyzer.analyze_goal("Compare Transformer and Mamba architectures")
    questions = q_gen.generate_questions(goal)

    report = composer.compose_report(goal, questions, [], [], [])

    assert "Autonomous Research Report" in report.title
    assert "Executive Summary" in report.markdown_content
    assert len(report.sections) >= 2
