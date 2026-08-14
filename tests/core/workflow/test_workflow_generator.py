"""Unit test for WorkflowGenerator."""

import pytest

from core.workflow.components.goal_analyzer import ResearchGoalAnalyzer
from core.workflow.components.question_generator import ResearchQuestionGenerator
from core.workflow.components.workflow_generator import WorkflowGenerator


def test_workflow_generator_assignments():
    analyzer = ResearchGoalAnalyzer()
    q_gen = ResearchQuestionGenerator()
    wf_gen = WorkflowGenerator()

    goal = analyzer.analyze_goal("Analyze quantum algorithm benchmarks")
    questions = q_gen.generate_questions(goal)
    assignments = wf_gen.generate_task_assignments(goal, questions)

    assert len(assignments) == len(questions)
    assert assignments[0].task_id == questions[0].question_id
    assert assignments[0].parallel_wave == questions[0].execution_wave
