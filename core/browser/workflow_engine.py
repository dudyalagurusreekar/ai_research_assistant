"""Browser Workflow Recorder & Execution Replay Engine."""

import logging
import uuid
from typing import Dict, Any, List, Optional
from core.browser.models import WorkflowDefinition, WorkflowStep
from core.browser.navigation_engine import NavigationEngine
from core.browser.interaction_engine import InteractionEngine
from core.browser.extraction_engine import ExtractionEngine
from core.browser.security_guard import BrowserSecurityGuard

logger = logging.getLogger(__name__)


class WorkflowRecorder:
    """Records browser navigation and interaction steps into JSON workflow definitions."""

    def __init__(self, name: str, description: Optional[str] = None):
        self.workflow_id = f"wf_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.description = description
        self.steps: List[WorkflowStep] = []

    def record_step(
        self,
        action_type: str,
        selector: Optional[str] = None,
        value: Optional[str] = None,
        target_url: Optional[str] = None,
        description: Optional[str] = None,
    ) -> WorkflowStep:
        """Append step to recorded workflow definition."""
        step = WorkflowStep(
            step_id=f"step_{len(self.steps) + 1}",
            action_type=action_type,
            selector=selector,
            value=value,
            target_url=target_url,
            description=description or f"Execute {action_type}",
        )
        self.steps.append(step)
        return step

    def export_definition(self) -> WorkflowDefinition:
        """Export completed JSON workflow schema."""
        return WorkflowDefinition(
            workflow_id=self.workflow_id,
            name=self.name,
            description=self.description,
            steps=self.steps,
        )


class WorkflowExecutor:
    """Replays recorded browser workflows with dynamic parameter substitution and error recovery."""

    def __init__(
        self,
        navigation_engine: Optional[NavigationEngine] = None,
        interaction_engine: Optional[InteractionEngine] = None,
        extraction_engine: Optional[ExtractionEngine] = None,
        security_guard: Optional[BrowserSecurityGuard] = None,
    ):
        self.nav_engine = navigation_engine or NavigationEngine()
        self.interact_engine = interaction_engine or InteractionEngine()
        self.extract_engine = extraction_engine or ExtractionEngine()
        self.security_guard = security_guard or BrowserSecurityGuard()

    async def execute_workflow(
        self,
        session: Dict[str, Any],
        definition: WorkflowDefinition,
        variables: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Execute all steps in workflow sequence."""
        vars_map = variables or {}
        results: List[Dict[str, Any]] = []

        logger.info(f"Starting execution of workflow '{definition.name}' ({len(definition.steps)} steps).")

        for step in definition.steps:
            # 1. Security Check
            validated_step = self.security_guard.validate_action(step)

            # 2. Variable Substitution
            val = validated_step.value
            target_url = validated_step.target_url
            if val and val.startswith("{{") and val.endswith("}}"):
                var_key = val[2:-2].strip()
                val = vars_map.get(var_key, val)
            if target_url and target_url.startswith("{{") and target_url.endswith("}}"):
                var_key = target_url[2:-2].strip()
                target_url = vars_map.get(var_key, target_url)

            # 3. Action Dispatch
            action = validated_step.action_type.upper()
            step_res = {"step_id": step.step_id, "action": action, "status": "success"}

            try:
                if action == "NAVIGATE" and target_url:
                    meta = await self.nav_engine.navigate(session, target_url)
                    step_res["details"] = meta.model_dump()
                elif action == "CLICK" and validated_step.selector:
                    await self.interact_engine.click(session, validated_step.selector)
                elif action == "TYPE" and validated_step.selector:
                    await self.interact_engine.type_text(session, validated_step.selector, val or "")
                elif action == "EXTRACT":
                    extraction = await self.extract_engine.extract_content(session)
                    step_res["extraction"] = extraction.model_dump()
                elif action == "SCREENSHOT":
                    img_bytes = await self.extract_engine.capture_screenshot(session)
                    step_res["screenshot_bytes"] = len(img_bytes)

            except Exception as ex:
                logger.error(f"Workflow step '{step.step_id}' failed: {ex}")
                step_res["status"] = "failed"
                step_res["error"] = str(ex)

            results.append(step_res)

        return {
            "workflow_id": definition.workflow_id,
            "status": "completed",
            "executed_steps": len(results),
            "step_results": results,
        }
