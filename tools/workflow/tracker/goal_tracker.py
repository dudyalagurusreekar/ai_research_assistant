"""Goal Tracker calculating workflow progress percentage."""

from tools.workflow.interfaces.workflow_interfaces import IGoalTracker
from tools.workflow.models.workflow_models import NormalizedWorkflow, TaskStatus
from infrastructure.logging.logger import StructuredLogger


class GoalTracker(IGoalTracker):
    """Calculates and updates overall workflow progress percentage."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("GoalTracker")

    def update_progress(self, workflow: NormalizedWorkflow) -> float:
        """Calculate progress percentage based on completed tasks."""
        if not workflow.tasks:
            workflow.metrics.progress_percentage = 100.0
            return 100.0

        completed = sum(1 for t in workflow.tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in workflow.tasks if t.status == TaskStatus.FAILED)
        total = len(workflow.tasks)

        workflow.metrics.completed_tasks = completed
        workflow.metrics.failed_tasks = failed
        workflow.metrics.total_tasks = total

        pct = round((completed / total) * 100.0, 2)
        workflow.metrics.progress_percentage = pct
        return pct
