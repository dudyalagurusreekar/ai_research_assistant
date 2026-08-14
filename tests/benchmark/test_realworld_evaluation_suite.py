"""Benchmark Test Suite — Executes all 10 Real-World Tasks and verifies rubric scoring and report generation."""

import os
from pathlib import Path

import pytest

from core.evaluation.models import EvaluationRubricCategory, ScoreGrade
from core.evaluation.realworld_suite import RealWorldEvaluationSuite
from core.evaluation.task_definitions import get_all_evaluation_tasks
from core.platform_infra.engine import PlatformEngine


def test_get_all_evaluation_tasks():
    tasks = get_all_evaluation_tasks()
    assert len(tasks) == 10

    task_ids = [t.task_id for t in tasks]
    assert "task_01" in task_ids
    assert "task_10" in task_ids


def test_realworld_suite_execution(tmp_path):
    reports_dir = tmp_path / "reports"
    brain_dir = tmp_path / "brain"

    suite = RealWorldEvaluationSuite(
        reports_dir=str(reports_dir),
        brain_dir=str(brain_dir),
    )

    result = suite.execute_suite()

    # 1. Verify 10 tasks completed
    assert len(result.results) == 10
    assert result.all_passed is True
    assert result.total_score == 1000.0
    assert result.average_score == 100.0

    # 2. Verify all reports exist on filesystem
    for t_res in result.results:
        assert Path(t_res.report_file_path).exists()
        assert Path(t_res.artifact_path).exists()
        assert len(t_res.report_markdown) > 500
        assert "References & Citations" in t_res.report_markdown
        assert t_res.total_score == 100.0

        # Verify rubric categories
        for cat in EvaluationRubricCategory:
            assert cat in t_res.category_scores
            assert t_res.category_scores[cat].grade == ScoreGrade.EXCELLENT
            assert t_res.category_scores[cat].score_points == 10.0

    # 3. Verify Master Scorecard Generated
    scorecard_path = reports_dir / "MASTER_EVALUATION_SCORECARD.md"
    assert scorecard_path.exists()
    content = scorecard_path.read_text(encoding="utf-8")
    assert "10 / 10" in content
    assert "1000.0 / 1000.0" in content


def test_realworld_suite_platform_integration():
    """Verify Real-World Suite integrates with Platform RBAC and Multi-Tenant Quotas."""
    platform = PlatformEngine()
    auth_ctx = platform.auth_manager.verify_jwt_token(
        platform.auth_manager.issue_jwt_token("usr_admin").access_token
    )

    assert platform.auth_manager.check_rbac(auth_ctx, "execute") is True
    assert platform.tenant_manager.check_quota("default_tenant") is True

    suite = RealWorldEvaluationSuite()
    tasks = get_all_evaluation_tasks()
    single_res = suite.execute_task(tasks[0])

    assert single_res.status == "completed"
    assert single_res.total_score == 100.0
    assert len(single_res.subsystems_exercised) == 8
