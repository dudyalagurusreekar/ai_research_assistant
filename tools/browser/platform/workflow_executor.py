"""Workflow Executor for Sprint 11 Browser Automation Platform."""

import logging
import time
from typing import Any, Dict, Optional
from tools.browser.platform.interaction_engine import InteractionEngine
from tools.browser.platform.models import (
    ActionResult,
    ActionType,
    WorkflowDefinition,
    WorkflowExecutionResult,
)
from tools.browser.platform.navigation_engine import NavigationEngine

logger = logging.getLogger("Tools.Browser.Platform.WorkflowExecutor")


class WorkflowExecutor:
    """Executes and replays recorded workflow definitions with variable substitution and assertions."""

    def __init__(
        self,
        navigation_engine: Optional[NavigationEngine] = None,
        interaction_engine: Optional[InteractionEngine] = None,
    ) -> None:
        self.navigation_engine = navigation_engine or NavigationEngine()
        self.interaction_engine = interaction_engine or InteractionEngine()

    async def execute_workflow(
        self,
        page: Any,
        workflow: WorkflowDefinition,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> WorkflowExecutionResult:
        """Replay recorded workflow steps with optional dynamic parameters."""
        start_time = time.time()
        param_dict = {**workflow.input_parameters, **(parameters or {})}
        step_results = []
        failed_step_id = None

        logger.info(f"Replaying workflow '{workflow.workflow_id}' with {len(workflow.steps)} step(s).")

        for step in workflow.steps:
            action = step.action

            # Substitute parameters into URL, text, value, selector
            if action.url and "{" in action.url:
                for k, v in param_dict.items():
                    action.url = action.url.replace(f"{{{k}}}", str(v))

            if action.text and "{" in action.text:
                for k, v in param_dict.items():
                    action.text = action.text.replace(f"{{{k}}}", str(v))

            if action.value and "{" in action.value:
                for k, v in param_dict.items():
                    action.value = action.value.replace(f"{{{k}}}", str(v))

            if action.target_selector and "{" in action.target_selector:
                for k, v in param_dict.items():
                    action.target_selector = action.target_selector.replace(f"{{{k}}}", str(v))

            if action.action_type == ActionType.NAVIGATE:
                res = await self.navigation_engine.navigate(page, action.url or "about:blank")
            else:
                res = await self.interaction_engine.execute_action(page, action)

            step_results.append(res)

            if not res.success and not step.continue_on_failure:
                failed_step_id = step.step_id
                exec_time = (time.time() - start_time) * 1000
                logger.error(f"Workflow '{workflow.workflow_id}' halted on failed step '{step.step_id}'.")
                return WorkflowExecutionResult(
                    workflow_id=workflow.workflow_id,
                    success=False,
                    step_results=step_results,
                    execution_time_ms=exec_time,
                    failed_step_id=failed_step_id,
                    error=res.error or f"Failed step '{step.step_id}'",
                )

        exec_time = (time.time() - start_time) * 1000
        return WorkflowExecutionResult(
            workflow_id=workflow.workflow_id,
            success=True,
            step_results=step_results,
            execution_time_ms=exec_time,
        )
