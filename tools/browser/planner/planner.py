"""Core AI Browser Planner Orchestrator Loop.

Coordinates DOM simplification, history state tracking, structured LLM reasoning,
selector discovery, execution, verification, and failure recovery.
"""

import os
import json
import time
import litellm
from utils.resilience import resilient_completion, AllModelsFailedError
from typing import Dict, Any, List, Optional

from config.model import resolve_model_config
from tools.browser.core.browser import Browser
from tools.browser.models.response import ActionResult
from tools.browser.planner.simplifier import DOMSimplifier
from tools.browser.planner.state import PlannerState
from tools.browser.planner.prompts import SYSTEM_INSTRUCTIONS, PROMPT_TEMPLATE
from tools.browser.context_manager import ContextLifecycleManager
from tools.browser.reporting_legacy import ReportingEngine
from tools.browser.storage.checkpoint_store import CheckpointStore


class PlannerResult:
    """Consolidated outcome of the planning execution."""

    def __init__(
        self,
        success: bool,
        goal: str,
        steps_taken: int,
        final_output: Optional[str],
        duration_ms: float,
        errors: List[str],
        report: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.success = success
        self.goal = goal
        self.steps_taken = steps_taken
        self.final_output = final_output
        self.duration_ms = duration_ms
        self.errors = errors
        self.report = report

    def to_dict(self) -> Dict[str, Any]:
        """Serialize planning result to dictionary."""
        d = {
            "success": self.success,
            "goal": self.goal,
            "steps_taken": self.steps_taken,
            "final_output": self.final_output,
            "duration_ms": self.duration_ms,
            "errors": self.errors,
        }
        if self.report:
            d["report"] = self.report
        return d


class BrowserPlanner:
    """AI Browser Planner reasoning layer converting high-level goals to browser actions."""

    def __init__(self, browser: Browser) -> None:
        self.browser = browser
        self.simplifier = DOMSimplifier()
        self.context_manager = ContextLifecycleManager()
        self.model_name, self.model_kwargs = resolve_model_config()
        from tools.browser.executor import BrowserActionExecutor
        self.executor = BrowserActionExecutor(browser)

    def _save_checkpoint(self, state: PlannerState) -> None:
        """Saves a periodic checkpoint of the planner state to disk asynchronously."""
        checkpoint_path = os.path.join(getattr(self.context_manager, "artifact_dir", None) or "logs", "planner_checkpoint.json")
        CheckpointStore.save_checkpoint_async(state.to_dict(), checkpoint_path)

    def _save_recovery_state(self, state: PlannerState) -> str:
        """Saves the final recovery state of the planner state to disk synchronously on failure."""
        recovery_path = os.path.join("logs", f"planner_recovery_{int(time.time())}.json")
        CheckpointStore.save_checkpoint_sync(state.to_dict(), recovery_path)
        return recovery_path

    def execute(self, goal: str, max_steps: int = 15, state: Optional[PlannerState] = None) -> PlannerResult:
        """Execute the planner loop to achieve a goal.

        Args:
            goal (str): Natural language task goal.
            max_steps (int): Safety limit on max reasoning steps.
            state (Optional[PlannerState]): Optional pre-existing planner state to resume from.

        Returns:
            PlannerResult: Output summary DTO.
        """
        state = state or PlannerState(goal)
        start_time = time.time()

        litellm_kwargs = dict(self.model_kwargs)
        
        last_action_mutated = True
        current_url = "about:blank"
        current_title = ""
        html = ""
        simplified_dom_str = ""
        
        from tools.browser.planner.controller import ExecutionController, BudgetExceededError, LoopDetectedError
        controller = ExecutionController(max_actions=max_steps)
        
        # Estimate dynamic budget and pick the larger of the two
        dynamic_max = controller.estimate_budget(goal)
        controller.max_actions = max(max_steps, dynamic_max)

        try:
            while True:
                # Check step budget
                try:
                    controller.record_action()
                except BudgetExceededError as e:
                    state.success = False
                    state.errors.append(str(e))
                    duration = (time.time() - start_time) * 1000.0
                    report = ReportingEngine.generate_report(
                        task_id=f"task_{int(start_time)}",
                        goal=goal,
                        planner_state=state,
                        start_time=start_time,
                        final_output=None
                    )
                    report.save_to_file(os.path.join(self.context_manager.artifact_dir, f"report_{int(start_time)}.json"))
                    return PlannerResult(
                        success=False,
                        goal=goal,
                        steps_taken=state.current_step - 1,
                        final_output=None,
                        duration_ms=duration,
                        errors=state.errors,
                        report=report.to_dict()
                    )
    
                # 1. Smart DOM Simplification & Timing
                dom_simplify_start = time.time()
                if last_action_mutated:
                    url_res = self.browser.get_current_url()
                    current_url = url_res.data if url_res.success else "about:blank"
                    state.record_visit(current_url)
    
                    title_res = self.browser.get_page_title()
                    current_title = title_res.data if title_res.success else ""
    
                    html_res = self.browser.get_page_html()
                    html = html_res.data if html_res.success else ""
    
                    simplified_dom_str = self.simplifier.simplify(html)
                else:
                    state.record_visit(current_url)
                dom_simplify_duration = (time.time() - dom_simplify_start) * 1000.0
    
                # 2. Compile context prompt using ContextLifecycleManager
                prompt = self.context_manager.build_compact_context(
                    state=state,
                    simplified_dom_str=simplified_dom_str,
                    current_url=current_url,
                    current_title=current_title
                )
    
                messages = [
                    {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                    {"role": "user", "content": prompt}
                ]
    
                # 3. Invoke LLM reasoning engine & Time it
                llm_start = time.time()
                thought = ""
                action = ""
                try:
                    response = resilient_completion(
                        model=self.model_name,
                        messages=messages,
                        **litellm_kwargs
                    )
                    usage = getattr(response, "usage", None)
                    controller.record_token_usage(usage)
                    state.total_tokens_used = controller.total_tokens_used
    
                    response_text = response.choices[0].message.content.strip()
    
                    if response_text.startswith("```"):
                        lines = response_text.splitlines()
                        if lines[0].startswith("```json"):
                            response_text = "\n".join(lines[1:-1])
                        else:
                            response_text = "\n".join(lines[1:-1])
                    response_text = response_text.strip()
    
                    action_dict = json.loads(response_text)
                    thought = action_dict.get("thought", "")
                    action = action_dict.get("action", "").strip().lower()
                except Exception as e:
                    llm_duration = (time.time() - llm_start) * 1000.0
                    state.add_step(
                        thought="LLM response parsing failed.",
                        command="parse_llm_response",
                        selector=None,
                        text=None,
                        result_message=f"JSON Parse/API Error: {e}",
                        success=False,
                        duration_ms=0.0,
                        dom_simplify_time_ms=dom_simplify_duration,
                        llm_inference_time_ms=llm_duration
                    )
                    continue
                llm_duration = (time.time() - llm_start) * 1000.0
    
                # 4. Check early termination Finisher
                if action == "finish":
                    final_answer = action_dict.get("answer", "Goal achieved successfully.")
                    state.success = True
                    duration = (time.time() - start_time) * 1000.0
                    report = ReportingEngine.generate_report(
                        task_id=f"task_{int(start_time)}",
                        goal=goal,
                        planner_state=state,
                        start_time=start_time,
                        final_output=final_answer
                    )
                    report.save_to_file(os.path.join(self.context_manager.artifact_dir, f"report_{int(start_time)}.json"))
                    return PlannerResult(
                        success=True,
                        goal=goal,
                        steps_taken=state.current_step - 1,
                        final_output=final_answer,
                        duration_ms=duration,
                        errors=state.errors,
                        report=report.to_dict()
                    )
    
                # 5. Resolve target node selector
                ref_id = action_dict.get("ref_id")
                selector = None
                if ref_id is not None:
                    try:
                        ref_int = int(ref_id)
                        selector = self.simplifier.get_selector(ref_int)
                    except (ValueError, TypeError):
                        pass
    
                text_val = action_dict.get("text")
                query_val = action_dict.get("query")
                key_val = action_dict.get("key")
                checked_val = action_dict.get("checked", True)
                scroll_dir = action_dict.get("scroll_direction", "down")
                action_selector = action_dict.get("selector")
                form_data = action_dict.get("form_data")
                credentials = action_dict.get("credentials")
    
                # 6. Execute browser action (Primitive or Macro)
                step_start = time.time()
                executor_action = {
                    "action": action,
                    "selector": selector or action_selector,
                    "text_input": text_val or query_val,
                    "url": action_dict.get("url") or text_val,
                    "key": key_val,
                    "checked": checked_val,
                    "scroll_direction": scroll_dir,
                    "extra_args": text_val,
                    "form_data": form_data,
                    "credentials": credentials,
                }
                action_res = self.executor.execute(executor_action)
                step_duration = (time.time() - step_start) * 1000.0
                
                success = action_res.success if (action_res and isinstance(action_res, ActionResult)) else False
                result_msg = (
                    ", ".join(action_res.errors)
                    if (action_res and action_res.errors)
                    else "Action succeeded"
                )
    
                # Track screenshot or data artifact path
                if action_res and action_res.success:
                    if action == "capture_screenshot" or action == "macro_capture_page":
                        screenshot_path = action_res.data.get("screenshot_path") if isinstance(action_res.data, dict) else action_res.data
                        if screenshot_path:
                            state.screenshots.append(str(screenshot_path))
                    if action == "macro_extract_article" or action == "macro_navigate_and_read" or action == "get_clean_text":
                        if action_res.data:
                            # Offload extracted text to an artifact
                            artifact_ref = self.context_manager._save_artifact("extracted_text", {"text": action_res.data})
                            state.artifacts.append(artifact_ref)
    
                # 7. Check for infinite loops
                current_action_signature = f"{action}_{selector or action_selector or current_url}_{text_val or query_val}"
                try:
                    controller.check_loop(current_action_signature, success)
                except LoopDetectedError as e:
                    state.success = False
                    state.errors.append(str(e))
                    duration = (time.time() - start_time) * 1000.0
                    report = ReportingEngine.generate_report(
                        task_id=f"task_{int(start_time)}",
                        goal=goal,
                        planner_state=state,
                        start_time=start_time,
                        final_output=None
                    )
                    report.save_to_file(os.path.join(self.context_manager.artifact_dir, f"report_{int(start_time)}.json"))
                    return PlannerResult(
                        success=False,
                        goal=goal,
                        steps_taken=state.current_step - 1,
                        final_output=None,
                        duration_ms=duration,
                        errors=state.errors,
                        report=report.to_dict()
                    )
    
                # Record step execution to state
                state.add_step(
                    thought=thought,
                    command=action,
                    selector=selector or action_selector,
                    text=text_val or key_val or scroll_dir or query_val,
                    result_message=result_msg,
                    success=success,
                    duration_ms=step_duration,
                    dom_simplify_time_ms=dom_simplify_duration,
                    llm_inference_time_ms=llm_duration
                )
                
                # Save periodic checkpoint
                self._save_checkpoint(state)
    
                # Update cache mutation flag
                non_mutating_actions = {
                    "get_current_url", "get_page_title", "get_page_html", "get_clean_text", 
                    "capture_screenshot", "capture_network_requests", "capture_console_logs",
                    "macro_capture_page"
                }
                last_action_mutated = action not in non_mutating_actions and success
    
            # End of loop safety fallback
            state.success = False
            duration = (time.time() - start_time) * 1000.0
            report = ReportingEngine.generate_report(
                task_id=f"task_{int(start_time)}",
                goal=goal,
                planner_state=state,
                start_time=start_time,
                final_output=None
            )
            report.save_to_file(os.path.join(self.context_manager.artifact_dir or "logs", f"report_{int(start_time)}.json"))
            return PlannerResult(
                success=False,
                goal=goal,
                steps_taken=state.current_step - 1,
                final_output=None,
                duration_ms=duration,
                errors=state.errors + ["Max planner steps reached without achieving goal."],
                report=report.to_dict()
            )
        except Exception as e:
            recovery_path = self._save_recovery_state(state)
            state.success = False
            state.errors.append(f"Planner execution interrupted: {e}. Recovery state saved to: {recovery_path}")
            duration = (time.time() - start_time) * 1000.0
            report = ReportingEngine.generate_report(
                task_id=f"task_{int(start_time)}",
                goal=goal,
                planner_state=state,
                start_time=start_time,
                final_output=None
            )
            report_dir = getattr(self.context_manager, "artifact_dir", None) or "logs"
            report.save_to_file(os.path.join(report_dir, f"report_{int(start_time)}.json"))
            return PlannerResult(
                success=False,
                goal=goal,
                steps_taken=state.current_step - 1,
                final_output=None,
                duration_ms=duration,
                errors=state.errors,
                report=report.to_dict()
            )
