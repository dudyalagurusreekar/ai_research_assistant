"""Task Scheduler handling task dependencies and ready queues."""

from typing import List
from tools.workflow.interfaces.workflow_interfaces import ITaskScheduler
from tools.workflow.models.workflow_models import NormalizedWorkflow, WorkflowTask, TaskStatus
from infrastructure.logging.logger import StructuredLogger


class TaskScheduler(ITaskScheduler):
    """Manages task execution dependencies and filters tasks ready for execution."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("TaskScheduler")

    def get_ready_tasks(self, workflow: NormalizedWorkflow) -> List[WorkflowTask]:
        """Return tasks whose status is PENDING and all parent dependencies are COMPLETED."""
        completed_ids = {t.task_id for t in workflow.tasks if t.status == TaskStatus.COMPLETED}
        ready = []

        for task in workflow.tasks:
            if task.status == TaskStatus.PENDING:
                # Check if all parent dependencies are in completed_ids
                if all(dep_id in completed_ids for dep_id in task.dependencies):
                    ready.append(task)

        return ready
