"""Abstract interface contracts for the Research Workflow Engine."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from tools.workflow.models.workflow_models import (
    NormalizedWorkflow,
    WorkflowTask,
    WorkflowState,
    WorkflowCheckpoint,
)


class IWorkflowPlanner(ABC):
    """Abstract workflow planner interface decomposing objectives into task DAGs."""

    @abstractmethod
    async def plan_workflow(self, objective: str, template_name: Optional[str] = None) -> NormalizedWorkflow:
        """Decompose high-level research objective into structured task DAG."""
        pass


class ITaskScheduler(ABC):
    """Abstract task scheduler interface managing task queues and dependency sorting."""

    @abstractmethod
    def get_ready_tasks(self, workflow: NormalizedWorkflow) -> List[WorkflowTask]:
        """Return list of tasks whose parent dependencies have completed."""
        pass


class IWorkflowExecutor(ABC):
    """Abstract workflow executor interface dispatching tasks to registered platform tools."""

    @abstractmethod
    async def execute_task(self, task: WorkflowTask, context: Dict[str, Any]) -> Any:
        """Dispatch task execution through global ToolRegistry / CapabilityRegistry."""
        pass


class IWorkflowStateManager(ABC):
    """Abstract workflow state and checkpoint manager interface."""

    @abstractmethod
    async def save_checkpoint(self, workflow: NormalizedWorkflow) -> WorkflowCheckpoint:
        """Persist snapshot checkpoint of current workflow state."""
        pass

    @abstractmethod
    async def load_checkpoint(self, checkpoint_id: str) -> Optional[WorkflowCheckpoint]:
        """Restore saved checkpoint snapshot."""
        pass


class IContextCoordinator(ABC):
    """Abstract context coordinator interface managing state variables across tasks."""

    @abstractmethod
    def update_context(self, context: Dict[str, Any], task_result: Any) -> Dict[str, Any]:
        """Merge task execution result into workflow shared context."""
        pass


class IDecisionEngine(ABC):
    """Abstract decision engine interface evaluating task outcomes and retries."""

    @abstractmethod
    def evaluate_task_outcome(self, task: WorkflowTask) -> str:
        """Evaluate task status and return action ('continue', 'retry', 'replan', 'fail')."""
        pass


class IGoalTracker(ABC):
    """Abstract goal tracker interface calculating progress and completion criteria."""

    @abstractmethod
    def update_progress(self, workflow: NormalizedWorkflow) -> float:
        """Calculate and update workflow progress percentage."""
        pass


class IWorkflowRegistry(ABC):
    """Abstract registry interface for reusable research workflow templates."""

    @abstractmethod
    def register_template(self, name: str, tasks: List[Dict[str, Any]]) -> None:
        """Register a workflow template."""
        pass

    @abstractmethod
    def get_template(self, name: str) -> Optional[List[Dict[str, Any]]]:
        """Get template tasks by name."""
        pass
