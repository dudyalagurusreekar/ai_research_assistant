"""Context Lifecycle & Minimal Working Memory Manager (`tools/browser/context/manager.py`).

Enforces prompt context token boundaries during multi-step browser tasks by summarizing
older steps, offloading large console/network/data payloads to non-blocking local storage,
and pruning raw DOM trees into minimal interactive element maps.
"""

import os
import logging
from typing import Any, Dict, List, Optional

from tools.browser.storage.artifact_store import ArtifactStore
from tools.browser.context.pruner import DOMPruner, PrunedDOM

logger = logging.getLogger("BrowserContextManager")


class ContextLifecycleManager:
    """Manages context window bloat by offloading large artifacts and summarizing history.

    Combines history compression, payload offloading, and DOM pruning to ensure
    low-latency LLM calls with minimal prompt token footprint.
    """

    def __init__(
        self,
        artifact_dir: str = ".browser_artifacts",
        max_dom_tokens: int = 1500,
    ) -> None:
        """Initialize Context Lifecycle Manager.

        Args:
            artifact_dir (str): Directory to save offloaded JSON/text artifacts.
            max_dom_tokens (int): Maximum token budget for DOM pruning.
        """
        self.artifact_dir = os.path.abspath(artifact_dir)
        self.pruner = DOMPruner(max_tokens=max_dom_tokens)
        self._logger = logger

    def prune_dom(self, raw_html: str, url: Optional[str] = None) -> PrunedDOM:
        """Prune raw HTML into a minimal interactive DOM representation within budget."""
        return self.pruner.prune(raw_html, url=url)

    def _save_artifact(self, name: str, data: Any) -> str:
        """Save a large artifact to disk and return a reference string."""
        try:
            filepath = ArtifactStore.save_artifact_sync(name, data)
            return f"[Artifact offloaded to: {filepath}]"
        except Exception as e:
            self._logger.error(f"Failed to save artifact {name}: {e}")
            return f"[Error offloading artifact: {e}]"

    def compact_response(self, response_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Compress the response dictionary for the LLM context.

        Args:
            response_dict: The sanitized output of ActionResult.to_dict().

        Returns:
            A new, compressed dictionary.
        """
        compacted = dict(response_dict)

        logs = compacted.get("console_logs", [])
        if logs and isinstance(logs, list) and len(logs) > 0:
            compacted["console_logs"] = self._save_artifact("console_logs", logs)

        requests = compacted.get("network_requests", [])
        if requests and isinstance(requests, list) and len(requests) > 0:
            compacted["network_requests"] = self._save_artifact("network_requests", requests)

        data = compacted.get("data")
        if data is not None:
            data_str = str(data)
            if len(data_str) > 5000:
                compacted["data"] = self._save_artifact(
                    "large_data_payload",
                    data if isinstance(data, (dict, list)) else {"raw_text": data_str},
                )

        return compacted

    def summarize_history(self, steps: list, max_recent: int = 2) -> str:
        """Summarize old execution steps to save context window tokens.

        Args:
            steps: List of PlannerStep objects.
            max_recent: Number of most recent steps to keep full text for.

        Returns:
            A compressed string representation of the history.
        """
        if not steps:
            return "No history yet."

        summary_lines = []

        # Summarize older steps
        older_steps = steps[:-max_recent] if len(steps) > max_recent else []
        if older_steps:
            summary_lines.append(f"--- Summarized older steps (1 to {len(older_steps)}) ---")
            for step in older_steps:
                step_num = getattr(step, "step_number", step.get("step_number") if isinstance(step, dict) else "?")
                cmd = getattr(step, "command", step.get("command") if isinstance(step, dict) else "")
                sel = getattr(step, "selector", step.get("selector") if isinstance(step, dict) else "")
                txt = getattr(step, "text", step.get("text") if isinstance(step, dict) else "")
                success = getattr(step, "success", step.get("success") if isinstance(step, dict) else False)
                status = "SUCCESS" if success else "FAILED"
                summary_lines.append(f"Step {step_num}: {cmd}({sel or ''}, {txt or ''}) -> {status}")
            summary_lines.append("--- End of summarized history ---\n")

        # Keep recent steps detailed
        recent_steps = steps[-max_recent:] if len(steps) > max_recent else steps
        if recent_steps:
            summary_lines.append("--- Recent steps ---")
            for step in recent_steps:
                step_num = getattr(step, "step_number", step.get("step_number") if isinstance(step, dict) else "?")
                thought = getattr(step, "thought", step.get("thought") if isinstance(step, dict) else "")
                cmd = getattr(step, "command", step.get("command") if isinstance(step, dict) else "")
                sel = getattr(step, "selector", step.get("selector") if isinstance(step, dict) else "")
                txt = getattr(step, "text", step.get("text") if isinstance(step, dict) else "")
                success = getattr(step, "success", step.get("success") if isinstance(step, dict) else False)
                res_msg = getattr(step, "result_message", step.get("result_message") if isinstance(step, dict) else "")
                status = "SUCCESS" if success else "FAILED"
                summary_lines.append(f"Step {step_num}:")
                summary_lines.append(f"  Thought: {thought}")
                summary_lines.append(f"  Action: {cmd}")
                if sel:
                    summary_lines.append(f"  Selector: {sel}")
                if txt:
                    summary_lines.append(f"  Text/Arg: {txt}")
                summary_lines.append(f"  Result: {status} - {res_msg}")

        return "\n".join(summary_lines)

    def build_compact_context(
        self, state: Any, simplified_dom_str: str, current_url: str, current_title: str
    ) -> str:
        """Build a minimal working-memory context string for the planner prompt."""
        history_summary = self.summarize_history(state.history, max_recent=2)

        completed_tasks = []
        latest_observation = "No actions executed yet."

        if hasattr(state, "history") and state.history:
            last_step = state.history[-1]
            cmd = getattr(last_step, "command", last_step.get("command") if isinstance(last_step, dict) else "")
            success = getattr(last_step, "success", last_step.get("success") if isinstance(last_step, dict) else False)
            res_msg = getattr(
                last_step, "result_message", last_step.get("result_message") if isinstance(last_step, dict) else ""
            )
            res_msg_str = str(res_msg) if res_msg is not None else ""
            latest_observation = f"Command '{cmd}' success: {success} | Outcome: {res_msg_str[:300]}..."

            for step in state.history:
                step_success = getattr(step, "success", step.get("success") if isinstance(step, dict) else False)
                step_cmd = getattr(step, "command", step.get("command") if isinstance(step, dict) else "")
                step_res = getattr(
                    step, "result_message", step.get("result_message") if isinstance(step, dict) else ""
                )
                step_res_str = str(step_res) if step_res is not None else ""
                if step_success:
                    completed_tasks.append(f"- Completed: {step_cmd} -> {step_res_str[:150]}...")

        completed_tasks_str = "\n".join(completed_tasks) if completed_tasks else "- None yet."
        remaining_goal = state.goal
        execution_summary = (
            f"Steps taken: {len(state.history) if hasattr(state, 'history') else 0}. "
            f"Tokens used: {getattr(state, 'total_tokens_used', 0)}."
        )

        compact_prompt = f"""### High-Level Goal
{state.goal}

### Compact Working Memory
- **Current URL**: {current_url}
- **Current Title**: {current_title}
- **Remaining Objective**: {remaining_goal}
- **Execution Summary**: {execution_summary}
- **Latest Observation**: {latest_observation}

### Completed Actions & Steps
{completed_tasks_str}

### Action Execution History (Recent Details)
{history_summary}

### Simplified DOM (Interactive Elements on Current Page)
{simplified_dom_str}

Output the JSON action dictionary:
"""
        return compact_prompt


ContextManager = ContextLifecycleManager
