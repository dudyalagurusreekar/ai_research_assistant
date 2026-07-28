"""Unified WorkflowEngineFacade for the Research Workflow Engine."""

import json
from typing import Dict, Any, Optional

from core.interfaces.tool import ITool
from core.models.metadata import ToolMetadata
from core.models.tool_result import ToolResult
from core.models.event import Event
from core.events import AsyncEventBus
from tools.workflow.models.workflow_models import (
    NormalizedWorkflow,
    TaskStatus,
    WorkflowState,
)
from tools.workflow.planner.workflow_planner import WorkflowPlanner
from tools.workflow.scheduler.task_scheduler import TaskScheduler
from tools.workflow.executor.workflow_executor import WorkflowExecutor
from tools.workflow.state.state_manager import WorkflowStateManager
from tools.workflow.context.context_coordinator import ContextCoordinator
from tools.workflow.decision.decision_engine import DecisionEngine
from tools.workflow.tracker.goal_tracker import GoalTracker
from tools.workflow.registry.workflow_registry import WorkflowRegistry
from infrastructure.logging.logger import StructuredLogger


class WorkflowEngineFacade(ITool):
    """Public unified API facade for the Research Workflow Engine."""

    name = "workflow_tool"
    description = "Central orchestration and reasoning engine for planning, scheduling, state checkpointing, and executing complex research workflows."

    def __init__(
        self,
        planner: Optional[WorkflowPlanner] = None,
        scheduler: Optional[TaskScheduler] = None,
        executor: Optional[WorkflowExecutor] = None,
        state_manager: Optional[WorkflowStateManager] = None,
        context_coordinator: Optional[ContextCoordinator] = None,
        decision_engine: Optional[DecisionEngine] = None,
        goal_tracker: Optional[GoalTracker] = None,
        registry: Optional[WorkflowRegistry] = None,
        event_bus: Optional[AsyncEventBus] = None,
    ) -> None:
        self.name = "workflow_tool"
        self._logger = StructuredLogger("WorkflowEngineFacade")
        self._event_bus = event_bus or AsyncEventBus()

        self._registry = registry or WorkflowRegistry()
        self._planner = planner or WorkflowPlanner(registry=self._registry)
        self._scheduler = scheduler or TaskScheduler()
        self._executor = executor or WorkflowExecutor()
        self._state_manager = state_manager or WorkflowStateManager()
        self._context_coordinator = context_coordinator or ContextCoordinator()
        self._decision_engine = decision_engine or DecisionEngine()
        self._goal_tracker = goal_tracker or GoalTracker()

        self._workflows: Dict[str, NormalizedWorkflow] = {}

        self._metadata = ToolMetadata(
            name="workflow_tool",
            version="1.0.0",
            description="Central orchestration and reasoning engine for planning, scheduling, state checkpointing, and executing complex research workflows.",
            capabilities=["workflow_planning", "task_scheduling", "tool_orchestration", "state_checkpointing", "goal_tracking"],
            parameters_schema={
                "action": "Action to perform ('create', 'run', 'pause', 'resume', 'status', 'list_templates')",
                "objective": "High-level research objective string",
                "workflow_id": "Target workflow ID",
                "template": "Workflow template name",
            },
            tags=["workflow", "orchestration", "planning", "scheduler"],
            is_async=True,
            enabled=True,
        )

    @property
    def metadata(self) -> ToolMetadata:
        """Return tool metadata descriptor."""
        return self._metadata

    async def forward(self, action: str = "create", **kwargs) -> str:
        """Standard tool execution wrapper returning JSON string."""
        try:
            obj = kwargs.get("objective", kwargs.get("query", "Default Research Objective"))
            wf_id = kwargs.get("workflow_id", kwargs.get("id", ""))
            template = kwargs.get("template")

            if action in ["create", "plan"]:
                wf = await self.create_workflow(obj, template_name=template)
                return json.dumps(wf.to_dict(), indent=2)
            elif action in ["run", "execute"]:
                if wf_id and wf_id in self._workflows:
                    target_wf = self._workflows[wf_id]
                else:
                    target_wf = await self.create_workflow(obj, template_name=template)
                res_wf = await self.run_workflow(target_wf)
                return json.dumps(res_wf.to_dict(), indent=2)
            elif action in ["pause", "checkpoint"]:
                chk_wf = await self.pause_workflow(wf_id)
                return json.dumps(chk_wf.to_dict(), indent=2)
            elif action in ["status", "get"]:
                st_wf = await self.get_workflow_status(wf_id)
                return json.dumps(st_wf.to_dict(), indent=2)
            else:
                return json.dumps({"error": f"Unknown workflow action '{action}'"}, indent=2)
        except Exception as e:
            self._logger.error(f"Error in WorkflowEngineFacade.forward action '{action}': {e}")
            return json.dumps({"error": str(e)}, indent=2)

    async def execute(self, parameters: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
        """Execute method returning ToolResult object conforming to ITool interface."""
        params = dict(parameters or {})
        params.update(kwargs)
        action = params.get("action", "create")
        try:
            output_json = await self.forward(action=action, **params)
            data = json.loads(output_json)
            if isinstance(data, dict) and "error" in data:
                return ToolResult.error(error_message=data["error"])
            return ToolResult.success(data=data)
        except Exception as e:
            return ToolResult.error(error_message=str(e))

    async def create_workflow(self, objective: str, template_name: Optional[str] = None) -> NormalizedWorkflow:
        """Plan and create new workflow DAG."""
        try:
            workflow = await self._planner.plan_workflow(objective, template_name=template_name)
            self._workflows[workflow.workflow_id] = workflow

            await self._publish_event("workflow.started", {
                "workflow_id": workflow.workflow_id,
                "objective": objective,
                "tasks_count": len(workflow.tasks),
            })
            return workflow
        except Exception as e:
            await self._publish_event("workflow.failed", {"action": "create", "error": str(e)})
            raise

    async def run_workflow(self, workflow_or_id: Any) -> NormalizedWorkflow:
        """Execute workflow DAG until completion or pause."""
        if isinstance(workflow_or_id, str):
            workflow = self._workflows.get(workflow_or_id)
            if not workflow:
                raise ValueError(f"Workflow '{workflow_or_id}' not found.")
        else:
            workflow = workflow_or_id

        workflow.state = WorkflowState.RUNNING

        try:
            while True:
                ready_tasks = self._scheduler.get_ready_tasks(workflow)
                if not ready_tasks:
                    break

                for task in ready_tasks:
                    await self._publish_event("task.started", {"task_id": task.task_id, "title": task.title})
                    res = await self._executor.execute_task(task, workflow.context)
                    
                    # Update context
                    workflow.context = self._context_coordinator.update_context(workflow.context, res)
                    await self._publish_event("task.completed", {"task_id": task.task_id, "status": task.status.value})

                    # Update goal progress
                    self._goal_tracker.update_progress(workflow)

            # Check final state
            if all(t.status == TaskStatus.COMPLETED for t in workflow.tasks):
                workflow.state = WorkflowState.COMPLETED
                await self._publish_event("workflow.completed", {"workflow_id": workflow.workflow_id})
            else:
                workflow.state = WorkflowState.FAILED
                await self._publish_event("workflow.failed", {"workflow_id": workflow.workflow_id})

            return workflow

        except Exception as e:
            workflow.state = WorkflowState.FAILED
            await self._publish_event("workflow.failed", {"workflow_id": workflow.workflow_id, "error": str(e)})
            raise

    async def pause_workflow(self, workflow_id: str) -> NormalizedWorkflow:
        """Pause workflow execution and save snapshot checkpoint."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_id}' not found.")

        workflow.state = WorkflowState.PAUSED
        chk = await self._state_manager.save_checkpoint(workflow)
        await self._publish_event("workflow.checkpointed", {"workflow_id": workflow_id, "checkpoint_id": chk.checkpoint_id})
        return workflow

    async def get_workflow_status(self, workflow_id: str) -> NormalizedWorkflow:
        """Get status for active workflow."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_id}' not found.")
        self._goal_tracker.update_progress(workflow)
        return workflow

    async def _publish_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish domain event over AsyncEventBus."""
        if self._event_bus:
            try:
                event_obj = Event(
                    event_type=event_type,
                    source="WorkflowEngineFacade",
                    payload=payload,
                )
                await self._event_bus.publish(event_obj)
            except Exception as e:
                self._logger.warning(f"Error publishing workflow event '{event_type}': {e}")
