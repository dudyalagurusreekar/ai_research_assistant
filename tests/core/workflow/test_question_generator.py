"""Unit test for ResearchQuestionGenerator."""

import pytest

from core.workflow.components.goal_analyzer import ResearchGoalAnalyzer
from core.workflow.components.question_generator import ResearchQuestionGenerator
from core.workflow.models.question import QuestionStatus


def test_question_generator_sub_questions():
    analyzer = ResearchGoalAnalyzer()
    generator = ResearchQuestionGenerator()

    goal = analyzer.analyze_goal("Benchmark LLM latency and python implementation")
    questions = generator.generate_questions(goal)

    assert len(questions) >= 4
    assert any(q.target_role.value == "research" for q in questions)
    assert any(q.target_role.value == "writer" for q in questions)
    assert any(q.target_role.value == "reviewer" for q in questions)
    assert all(q.status == QuestionStatus.PENDING for q in questions)
