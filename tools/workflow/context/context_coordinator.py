"""Context Coordinator managing variable propagation across workflow tasks."""

from typing import Dict, Any
from tools.workflow.interfaces.workflow_interfaces import IContextCoordinator
from infrastructure.logging.logger import StructuredLogger


class ContextCoordinator(IContextCoordinator):
    """Assembles and propagates shared context across workflow tasks."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("ContextCoordinator")

    def update_context(self, context: Dict[str, Any], task_result: Any) -> Dict[str, Any]:
        """Merge task execution outputs into shared workflow context."""
        updated = dict(context)
        if isinstance(task_result, dict):
            updated.update(task_result)
        elif task_result:
            updated["last_result"] = str(task_result)
        return updated
