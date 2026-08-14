"""Workflow Recorder for Sprint 11 Browser Automation Platform."""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from tools.browser.platform.models import BrowserAction, WorkflowDefinition, WorkflowStep

logger = logging.getLogger("Tools.Browser.Platform.WorkflowRecorder")


class WorkflowRecorder:
    """Records browser interaction sequences into reusable JSON workflow definitions."""

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        self.storage_dir = Path(storage_dir or ".storage/workflows")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._current_recording: Optional[WorkflowDefinition] = None
        self._recording_active: bool = False

    def start_recording(self, workflow_id: str, name: str, description: str = "") -> WorkflowDefinition:
        """Start a new workflow recording session."""
        self._current_recording = WorkflowDefinition(
            workflow_id=workflow_id,
            name=name,
            description=description,
            steps=[],
            created_at=time.time(),
        )
        self._recording_active = True
        logger.info(f"Started workflow recording session for '{workflow_id}'.")
        return self._current_recording

    def record_step(
        self,
        action: BrowserAction,
        description: str = "",
        assertion: Optional[Dict[str, Any]] = None,
        continue_on_failure: bool = False,
    ) -> Optional[WorkflowStep]:
        """Record an interactive step in active workflow recording."""
        if not self._recording_active or not self._current_recording:
            logger.warning("Attempted to record step while recording session is inactive.")
            return None

        step_id = f"step_{len(self._current_recording.steps) + 1}"
        desc = description or f"Execute {action.action_type.value} on {action.target_selector or action.url}"

        step = WorkflowStep(
            step_id=step_id,
            description=desc,
            action=action,
            assertion=assertion,
            continue_on_failure=continue_on_failure,
        )

        self._current_recording.steps.append(step)
        logger.info(f"Recorded step '{step_id}': {desc}")
        return step

    def stop_recording(self) -> Optional[WorkflowDefinition]:
        """Stop active recording session and return completed workflow definition."""
        if not self._recording_active or not self._current_recording:
            return None

        workflow = self._current_recording
        self._recording_active = False
        self.save_workflow(workflow)
        logger.info(f"Stopped recording workflow '{workflow.workflow_id}' with {len(workflow.steps)} steps.")
        return workflow

    def save_workflow(self, workflow: WorkflowDefinition) -> bool:
        """Save workflow definition to storage file."""
        file_path = self.storage_dir / f"{workflow.workflow_id}.json"

        data = {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "created_at": workflow.created_at,
            "input_parameters": workflow.input_parameters,
            "steps": [
                {
                    "step_id": s.step_id,
                    "description": s.description,
                    "continue_on_failure": s.continue_on_failure,
                    "assertion": s.assertion,
                    "action": {
                        "action_type": s.action.action_type.value,
                        "target_selector": s.action.target_selector,
                        "url": s.action.url,
                        "text": s.action.text,
                        "value": s.action.value,
                        "key_name": s.action.key_name,
                        "scroll_direction": s.action.scroll_direction,
                        "scroll_amount": s.action.scroll_amount,
                        "parameters": s.action.parameters,
                    },
                }
                for s in workflow.steps
            ],
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved workflow definition to '{file_path}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to save workflow '{workflow.workflow_id}': {e}")
            return False

    def load_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Load workflow definition from storage file."""
        file_path = self.storage_dir / f"{workflow_id}.json"
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            steps = []
            for sdata in data.get("steps", []):
                act_data = sdata["action"]
                action = BrowserAction(
                    action_type=act_data["action_type"],
                    target_selector=act_data.get("target_selector"),
                    url=act_data.get("url"),
                    text=act_data.get("text"),
                    value=act_data.get("value"),
                    key_name=act_data.get("key_name"),
                    scroll_direction=act_data.get("scroll_direction", "down"),
                    scroll_amount=act_data.get("scroll_amount", 500),
                    parameters=act_data.get("parameters", {}),
                )
                steps.append(
                    WorkflowStep(
                        step_id=sdata["step_id"],
                        description=sdata.get("description", ""),
                        action=action,
                        assertion=sdata.get("assertion"),
                        continue_on_failure=sdata.get("continue_on_failure", False),
                    )
                )

            return WorkflowDefinition(
                workflow_id=data["workflow_id"],
                name=data.get("name", ""),
                description=data.get("description", ""),
                input_parameters=data.get("input_parameters", {}),
                steps=steps,
                created_at=data.get("created_at", time.time()),
            )
        except Exception as e:
            logger.error(f"Failed to load workflow '{workflow_id}': {e}")
            return None
