"""Intelligent Browser Task Planner Engine.

Translates high-level natural language instructions into optimized TaskGraphs,
and executes them sequentially using the BrowserActionExecutor.
"""

import json
import logging
import time
import litellm
from utils.resilience import resilient_completion
from typing import Dict, Any, List, Optional, Set

from config.model import resolve_model_config
from tools.browser.core.browser import Browser
from tools.browser.executor import BrowserActionExecutor
from tools.browser.models.response import ActionResult, ActionMetrics
from tools.browser.planner.graph import TaskGraph, TaskNode, TaskStatus
from tools.browser.planner.prompts import GRAPH_SYSTEM_INSTRUCTIONS, GRAPH_PROMPT_TEMPLATE

logger = logging.getLogger("TaskPlannerEngine")


class TaskPlannerEngine:
    """Planning and execution engine for task graphs representing browser workflows."""

    def __init__(self, browser: Browser) -> None:
        """Initialize the TaskPlannerEngine.

        Args:
            browser (Browser): Browser instance.
        """
        self.browser = browser
        self.executor = BrowserActionExecutor(browser)
        self.model_name, self.model_kwargs = resolve_model_config()
        self._logger = logger
        from tools.browser.memory.manager import MemoryManager
        self.memory_manager = MemoryManager()

    def generate_plan(self, goal: str) -> TaskGraph:
        """Query LLM to generate a structured TaskGraph.

        Args:
            goal (str): Natural language task goal.

        Returns:
            TaskGraph: The validated and optimized execution plan.
        """
        # Fetch memory context
        memory_context = ""
        if hasattr(self, 'memory_manager'):
            try:
                # Use current URL as domain context if available
                url_res = self.browser.get_current_url()
                domain = url_res.data if url_res.success else ""
                memory_context = self.memory_manager.get_relevant_context(goal, domain=domain)
            except Exception as e:
                self._logger.warning(f"Failed to fetch memory context: {e}")

        # Inject context into prompt if available
        prompt_content = GRAPH_PROMPT_TEMPLATE.format(goal=goal)
        if memory_context:
            prompt_content = f"### RELEVANT MEMORY & STRATEGIES ###\n{memory_context}\n\n" + prompt_content

        messages = [
            {"role": "system", "content": GRAPH_SYSTEM_INSTRUCTIONS},
            {"role": "user", "content": prompt_content}
        ]

        litellm_kwargs = dict(self.model_kwargs)
        
        self._logger.info(f"Generating task graph for goal: '{goal}'")
        try:
            response = resilient_completion(
                model=self.model_name,
                messages=messages,
                **litellm_kwargs
            )
            response_text = response.choices[0].message.content.strip()

            # Clean markdown wrappers if present
            if response_text.startswith("```"):
                lines = response_text.splitlines()
                if lines[0].startswith("```json"):
                    response_text = "\n".join(lines[1:-1])
                else:
                    response_text = "\n".join(lines[1:-1])
            response_text = response_text.strip()

            graph_data = json.loads(response_text)
            graph = TaskGraph.from_dict(graph_data)
        except Exception as e:
            self._logger.error(f"Failed to generate/parse TaskGraph from LLM response: {e}")
            # Fallback: create single-node fallback navigation/crawling plan or re-raise
            raise RuntimeError(f"Plan generation failed: {e}")

        # Validate graph
        errors = graph.validate()
        if errors:
            self._logger.error(f"TaskGraph validation failed: {errors}")
            raise ValueError(f"Invalid TaskGraph generated: {errors}")

        # Optimize graph
        graph.optimize()
        return graph

    def evaluate_condition(self, condition: Dict[str, Any]) -> bool:
        """Evaluate branching conditions against current browser state.

        Args:
            condition (Dict[str, Any]): Dictionary definition of the branching condition.

        Returns:
            bool: True if condition is satisfied, False otherwise.
        """
        cond_type = condition.get("type", "").strip().lower()
        selector = condition.get("selector")
        text = condition.get("text")
        expression = condition.get("expression")

        try:
            if cond_type == "element_exists":
                if not selector:
                    return False
                # Use a fast wait selector action with short timeout
                res = self.executor.execute({
                    "action": "wait_for_selector",
                    "selector": selector,
                    "timeout": 1.0,
                    "text": "attached"
                })
                return res.success

            elif cond_type == "text_matches":
                if not selector or not text:
                    return False
                # Execute script to retrieve element innerText/value
                val_res = self.browser.execute_javascript(
                    f"document.querySelector('{selector}') ? (document.querySelector('{selector}').value || document.querySelector('{selector}').innerText) : ''"
                )
                val = str(val_res.data or "") if val_res.success else ""
                return text in val

            elif cond_type == "js_expression":
                if not expression:
                    return False
                res = self.browser.execute_javascript(expression)
                return bool(res.data) if res.success else False

        except Exception as e:
            self._logger.warning(f"Condition evaluation encountered error: {e}")
            return False

        return False

    def propagate_failure(self, graph: TaskGraph, failed_node_id: str) -> None:
        """Mark all dependent nodes downstream as SKIPPED due to failure.

        Args:
            graph (TaskGraph): Active TaskGraph.
            failed_node_id (str): ID of the failed node.
        """
        queue = [failed_node_id]
        visited = set()
        while queue:
            curr = queue.pop(0)
            for node_id, node in graph.nodes.items():
                if curr in node.dependencies and node.status == TaskStatus.PENDING:
                    node.status = TaskStatus.SKIPPED
                    node.name += f" (Skipped: Dependency '{curr}' failed)"
                    if node_id not in visited:
                        visited.add(node_id)
                        queue.append(node_id)

    def propagate_skip(self, graph: TaskGraph, skipped_node_id: str) -> None:
        """Recursively mark downstream unique dependents of skipped branch nodes as SKIPPED.

        Args:
            graph (TaskGraph): Active TaskGraph.
            skipped_node_id (str): ID of the skipped node.
        """
        queue = [skipped_node_id]
        visited = set()
        while queue:
            curr = queue.pop(0)
            for node_id, node in graph.nodes.items():
                if curr in node.dependencies and node.status == TaskStatus.PENDING:
                    # Skip only if all parent dependencies are skipped/failed
                    all_parents_skipped = True
                    for dep in node.dependencies:
                        dep_node = graph.nodes.get(dep)
                        if dep_node and dep_node.status not in (TaskStatus.SKIPPED, TaskStatus.FAILED):
                            all_parents_skipped = False
                    
                    if all_parents_skipped:
                        node.status = TaskStatus.SKIPPED
                        node.name += f" (Skipped: Branch bypassed)"
                        if node_id not in visited:
                            visited.add(node_id)
                            queue.append(node_id)

    def execute_plan(self, graph: TaskGraph) -> Dict[str, Any]:
        """Execute task graph nodes topologically.

        Args:
            graph (TaskGraph): TaskGraph execution model.

        Returns:
            Dict[str, Any]: Summary dictionary of plan execution.
        """
        start_time = time.time()
        steps_taken = 0
        errors: List[str] = []

        topo_ids = graph.get_topological_order()

        while True:
            # Find nodes that are PENDING and whose dependency parent nodes are completed/skipped
            executable_ids = []
            for node_id in topo_ids:
                node = graph.nodes[node_id]
                if node.status == TaskStatus.PENDING:
                    # Check if all dependencies are satisfied (COMPLETED or SKIPPED)
                    deps_satisfied = True
                    for dep in node.dependencies:
                        dep_node = graph.nodes.get(dep)
                        if not dep_node or dep_node.status not in (TaskStatus.COMPLETED, TaskStatus.SKIPPED):
                            deps_satisfied = False
                            break
                    if deps_satisfied:
                        executable_ids.append(node_id)

            if not executable_ids:
                break

            for node_id in executable_ids:
                node = graph.nodes[node_id]
                node.status = TaskStatus.RUNNING
                steps_taken += 1

                # A. Handle Branching Node
                if node.condition:
                    cond_bool = self.evaluate_condition(node.condition)
                    then_node = node.condition.get("then_node")
                    else_node = node.condition.get("else_node")
                    
                    self._logger.info(f"Branch condition evaluated to {cond_bool}. routing then_node={then_node}, else_node={else_node}")
                    
                    if cond_bool:
                        if else_node and else_node in graph.nodes:
                            graph.nodes[else_node].status = TaskStatus.SKIPPED
                            self.propagate_skip(graph, else_node)
                    else:
                        if then_node and then_node in graph.nodes:
                            graph.nodes[then_node].status = TaskStatus.SKIPPED
                            self.propagate_skip(graph, then_node)

                    node.status = TaskStatus.COMPLETED
                    node.result = f"Branch evaluated to {cond_bool}"
                    continue

                # B. Handle Action Node execution
                action_dict = {
                    "action": node.action,
                    **node.params
                }
                
                res = self.executor.execute(action_dict)
                if res.success:
                    node.status = TaskStatus.COMPLETED
                    node.result = res
                else:
                    if node.retry_count < node.max_retries:
                        node.retry_count += 1
                        node.status = TaskStatus.PENDING  # Queue for retry next round
                        self._logger.warning(f"Task '{node_id}' failed. Retrying ({node.retry_count}/{node.max_retries})")
                    else:
                        node.status = TaskStatus.FAILED
                        node.result = res
                        errors.extend(res.errors)
                        self._logger.error(f"Task '{node_id}' failed permanently. Propagating failure downstream.")
                        self.propagate_failure(graph, node_id)

        all_completed = all(
            node.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED)
            for node in graph.nodes.values()
        )
        duration_ms = (time.time() - start_time) * 1000.0

        return {
            "success": all_completed,
            "steps_taken": steps_taken,
            "errors": errors,
            "duration_ms": duration_ms,
            "graph": graph,
        }
