"""Decision Engine evaluating task outcomes and retries."""

from tools.workflow.interfaces.workflow_interfaces import IDecisionEngine
from tools.workflow.models.workflow_models import WorkflowTask, TaskStatus
from infrastructure.logging.logger import StructuredLogger


class DecisionEngine(IDecisionEngine):
    """Evaluates task execution outcomes and determines next control flow step."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("DecisionEngine")

    def evaluate_task_outcome(self, task: WorkflowTask) -> str:
        """Return decision string ('continue', 'retry', 'replan', 'fail')."""
        if task.status == TaskStatus.COMPLETED:
            return "continue"
        elif task.status == TaskStatus.FAILED:
            return "fail"
        return "continue"
