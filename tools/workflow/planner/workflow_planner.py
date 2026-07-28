"""Workflow Planner decomposing objectives into task DAGs."""

from typing import Optional
from tools.workflow.interfaces.workflow_interfaces import IWorkflowPlanner, IWorkflowRegistry
from tools.workflow.models.workflow_models import NormalizedWorkflow, WorkflowTask, TaskStatus, WorkflowState
from tools.workflow.registry.workflow_registry import WorkflowRegistry
from infrastructure.logging.logger import StructuredLogger


class WorkflowPlanner(IWorkflowPlanner):
    """Decomposes high-level research objectives into structured DAG tasks."""

    def __init__(self, registry: Optional[IWorkflowRegistry] = None) -> None:
        self._logger = StructuredLogger("WorkflowPlanner")
        self._registry = registry or WorkflowRegistry()

    async def plan_workflow(self, objective: str, template_name: Optional[str] = None) -> NormalizedWorkflow:
        """Decompose objective into tasks, using template if specified."""
        self._logger.info(f"Planning research workflow for objective: '{objective}'")

        workflow = NormalizedWorkflow(
            objective=objective,
            state=WorkflowState.IDLE,
            context={"objective": objective},
        )

        template_tasks = self._registry.get_template(template_name) if template_name else None

        if template_tasks:
            # Instantiate from template
            task_id_map = {}
            for idx, t_spec in enumerate(template_tasks):
                task = WorkflowTask(
                    title=t_spec.get("title", f"Task {idx + 1}"),
                    tool_name=t_spec.get("tool_name", "search_tool"),
                    action=t_spec.get("action", "search"),
                    parameters=t_spec.get("parameters", {}),
                    status=TaskStatus.PENDING,
                )
                
                # Resolve parent dependencies
                deps_indices = t_spec.get("dependencies", [])
                for parent_idx in deps_indices:
                    if parent_idx in task_id_map:
                        task.dependencies.append(task_id_map[parent_idx])

                task_id_map[idx] = task.task_id
                workflow.tasks.append(task)
        else:
            # Default 2-step research DAG
            task1 = WorkflowTask(
                title=f"Search Knowledge for '{objective}'",
                tool_name="search_tool",
                action="search",
                parameters={"query": objective},
                status=TaskStatus.PENDING,
            )
            task2 = WorkflowTask(
                title=f"Store Results in Memory",
                tool_name="memory_tool",
                action="store",
                parameters={"content": f"Research output for {objective}"},
                status=TaskStatus.PENDING,
                dependencies=[task1.task_id],
            )
            workflow.tasks = [task1, task2]

        workflow.metrics.total_tasks = len(workflow.tasks)
        self._logger.info(f"Planned workflow '{workflow.workflow_id}' with {len(workflow.tasks)} tasks.")
        return workflow
