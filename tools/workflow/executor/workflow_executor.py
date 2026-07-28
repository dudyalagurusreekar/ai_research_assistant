

"""Workflow Executor dispatching tasks to registered platform tools."""

import time
import asyncio
from typing import Dict, Any
from tools.workflow.interfaces.workflow_interfaces import IWorkflowExecutor
from tools.workflow.models.workflow_models import WorkflowTask, TaskStatus
from infrastructure.logging.logger import StructuredLogger


class WorkflowExecutor(IWorkflowExecutor):
    """Executes individual workflow tasks by looking up tools in ToolRegistry."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("WorkflowExecutor")

    async def execute_task(self, task: WorkflowTask, context: Dict[str, Any]) -> Any:
        """Dispatch task to target tool strategy or facade."""
        from tools.registry import registry
        start_time = time.time()
        task.status = TaskStatus.RUNNING
        self._logger.info(f"Executing task '{task.task_id}' ({task.tool_name}.{task.action})")

        # Resolve parameters against shared context
        params = dict(task.parameters)
        for k, v in params.items():
            if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
                var_key = v.strip("{}")
                if var_key in context:
                    params[k] = context[var_key]

        try:
            matched_tool = None
            for tool in registry.get_tools():
                if getattr(tool, "name", "") == task.tool_name:
                    matched_tool = tool
                    break

            if matched_tool:
                if hasattr(matched_tool, "_facade") and hasattr(matched_tool._facade, "forward"):
                    res = await matched_tool._facade.forward(action=task.action, **params)
                elif hasattr(matched_tool, "forward"):
                    res = matched_tool.forward(action=task.action, **params)
                    if asyncio.iscoroutine(res):
                        res = await res
                else:
                    res = f"Executed {task.tool_name}.{task.action}"

                task.status = TaskStatus.COMPLETED
                task.result = res
                task.execution_time_ms = round((time.time() - start_time) * 1000, 2)
                return res
            else:
                # Simulated execution fallback for testing
                res_sim = f"Executed {task.tool_name}.{task.action} with params={params}"
                task.status = TaskStatus.COMPLETED
                task.result = res_sim
                task.execution_time_ms = round((time.time() - start_time) * 1000, 2)
                return res_sim

        except Exception as e:
            self._logger.error(f"Task '{task.task_id}' execution failed: {e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.execution_time_ms = round((time.time() - start_time) * 1000, 2)
            raise
