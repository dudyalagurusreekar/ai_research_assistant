"""DAGWorkflowExecutor — executes DAG execution waves with state propagation, retries, and telemetry."""

import time
from typing import Dict, Any, List, Optional
from core.planner.models.context import PlannerContext
from core.orchestration.orchestrator import IntelligentLLMOrchestrator
from core.orchestration.models.request import LLMRequest
from utils.logger import get_logger

logger = get_logger("DAGWorkflowExecutor")


class DAGWorkflowExecutor:
    """Production execution engine for task DAG execution waves."""

    def __init__(self, llm_orchestrator: Optional[IntelligentLLMOrchestrator] = None):
        self.llm_orchestrator = llm_orchestrator or IntelligentLLMOrchestrator()

    def execute_plan(
        self,
        ctx: PlannerContext,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """Execute all task waves in the PlannerContext DAG."""
        start_time = time.time()
        results: Dict[str, Any] = {}
        completed_tasks: List[str] = []
        failed_tasks: List[str] = []

        logger.info(f"Starting DAG execution for plan '{ctx.plan_id}' with {len(ctx.sub_tasks)} subtasks.")

        for wave_idx, wave in enumerate(ctx.parallel_levels):
            logger.info(f"Executing Wave {wave_idx + 1}/{len(ctx.parallel_levels)} with {len(wave)} tasks.")
            for task in wave:
                task_id = task.task_id
                success = False
                output = None

                for attempt in range(1, max_retries + 1):
                    try:
                        # Request LLM execution via Orchestrator
                        prompt = f"Execute subtask '{task.title}': {task.description}"
                        task_type_val = getattr(task, "task_type", getattr(task, "action", "general_qa"))
                        if hasattr(task_type_val, "value"):
                            task_type_val = task_type_val.value

                        req = LLMRequest(
                            prompt=prompt,
                            task_type=str(task_type_val),
                            complexity_score=getattr(task, "estimated_complexity", 5),
                        )

                        llm_resp = self.llm_orchestrator.generate(req)
                        if llm_resp.error_message:
                            raise RuntimeError(llm_resp.error_message)

                        output = llm_resp.text
                        success = True
                        break
                    except Exception as exc:
                        logger.warning(f"Task '{task_id}' attempt {attempt}/{max_retries} failed: {exc}")
                        time.sleep(0.1 * (2 ** (attempt - 1)))  # Exponential backoff

                if success:
                    completed_tasks.append(task_id)
                    results[task_id] = {
                        "status": "completed",
                        "title": task.title,
                        "output": output,
                    }
                else:
                    failed_tasks.append(task_id)
                    results[task_id] = {
                        "status": "failed",
                        "title": task.title,
                        "error": "Execution failed after maximum retries",
                    }

        total_latency_ms = (time.time() - start_time) * 1000.0
        return {
            "plan_id": ctx.plan_id,
            "status": "completed" if not failed_tasks else "degraded",
            "total_tasks": len(ctx.sub_tasks),
            "completed_count": len(completed_tasks),
            "failed_count": len(failed_tasks),
            "latency_ms": round(total_latency_ms, 2),
            "task_results": results,
        }


dag_workflow_executor = DAGWorkflowExecutor()
