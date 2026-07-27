"""Workflow State Manager saving and loading snapshot checkpoints."""

import asyncio
from typing import Dict, Any, Optional
from tools.workflow.interfaces.workflow_interfaces import IWorkflowStateManager
from tools.workflow.models.workflow_models import NormalizedWorkflow, WorkflowCheckpoint, TaskStatus
from infrastructure.storage.storage import DiskStorage
from infrastructure.logging.logger import StructuredLogger


class WorkflowStateManager(IWorkflowStateManager):
    """Manages state persistence, checkpoint snapshots, and workflow restoration."""

    def __init__(self, storage: Optional[DiskStorage] = None) -> None:
        self._logger = StructuredLogger("WorkflowStateManager")
        self._storage = storage or DiskStorage()
        self._checkpoints: Dict[str, WorkflowCheckpoint] = {}

    async def save_checkpoint(self, workflow: NormalizedWorkflow) -> WorkflowCheckpoint:
        """Save execution snapshot checkpoint."""
        completed_ids = [t.task_id for t in workflow.tasks if t.status == TaskStatus.COMPLETED]
        chk = WorkflowCheckpoint(
            workflow_id=workflow.workflow_id,
            completed_task_ids=completed_ids,
            state_context=dict(workflow.context),
        )
        self._checkpoints[chk.checkpoint_id] = chk
        self._logger.info(f"Saved checkpoint '{chk.checkpoint_id}' for workflow '{workflow.workflow_id}' ({len(completed_ids)} completed tasks).")
        return chk

    async def load_checkpoint(self, checkpoint_id: str) -> Optional[WorkflowCheckpoint]:
        """Restore saved checkpoint snapshot."""
        return self._checkpoints.get(checkpoint_id)
