"""Workflow Generator — Maps research questions into execution DAG task assignments."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.collaboration.models.context import TaskAssignment
from core.workflow.models.goal import ResearchGoal
from core.workflow.models.question import ResearchQuestion
from utils.logger import get_logger

logger = get_logger("WorkflowGenerator")


class WorkflowGenerator:
    """Transforms sub-questions into multi-wave TaskAssignments for MultiAgentCollaborationEngine."""

    def generate_task_assignments(
        self, goal: ResearchGoal, questions: List[ResearchQuestion]
    ) -> List[TaskAssignment]:
        """Convert sub-questions into typed multi-agent TaskAssignments."""
        assignments: List[TaskAssignment] = []

        for q in questions:
            assignment = TaskAssignment(
                task_id=q.question_id,
                title=f"Research Question: {q.question_text[:50]}",
                description=q.question_text,
                target_role=q.target_role,
                required_capabilities=q.required_capabilities,
                parameters={"hypothesis": q.hypothesis, "topic": goal.title, "raw_query": goal.raw_query},
                parallel_wave=q.execution_wave,
                dependencies=q.dependencies,
            )
            assignments.append(assignment)

        logger.info(f"WorkflowGenerator generated {len(assignments)} TaskAssignments across wave scheduling")
        return assignments
