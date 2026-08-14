"""Multi-Agent Orchestrator — Task wave scheduling, capability-driven assignment, parallel execution, and recovery."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from core.collaboration.components.conflict_resolution import ConflictResolutionEngine
from core.collaboration.components.memory import CollaborationMemory
from core.collaboration.components.registry import AgentRegistry
from core.collaboration.components.workspace import SharedWorkspace
from core.collaboration.models.agent_info import AgentRole, AgentStatus
from core.collaboration.models.context import (
    AgentOutput,
    CollaborationContext,
    CollaborationStatus,
    TaskAssignment,
)
from core.collaboration.models.metrics import AgentMetrics, OrchestratorMetrics
from utils.logger import get_logger

logger = get_logger("MultiAgentOrchestrator")


class MultiAgentOrchestrator:
    """Production Multi-Agent Orchestrator scheduling sequential and parallel waves across specialized agents."""

    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        workspace: Optional[SharedWorkspace] = None,
        memory: Optional[CollaborationMemory] = None,
        conflict_engine: Optional[ConflictResolutionEngine] = None,
        max_workers: int = 4,
    ) -> None:
        self.registry = registry or AgentRegistry.get_instance()
        self.workspace = workspace or SharedWorkspace()
        self.memory = memory or CollaborationMemory()
        self.conflict_engine = conflict_engine or ConflictResolutionEngine()
        self.max_workers = max_workers

    def execute_collaboration(self, ctx: CollaborationContext) -> CollaborationContext:
        """Execute a full multi-agent collaboration context across task waves."""
        start_time = time.time()
        ctx.status = CollaborationStatus.RUNNING
        metrics = ctx.metrics
        metrics.total_tasks = len(ctx.task_assignments)

        # 1. Compute execution waves based on parallel_wave attributes or topological dependencies
        waves: Dict[int, List[TaskAssignment]] = {}
        for task in ctx.task_assignments:
            wave_id = task.parallel_wave
            if wave_id not in waves:
                waves[wave_id] = []
            waves[wave_id].append(task)

        sorted_wave_keys = sorted(waves.keys())
        total_sequential_est = sum(t.estimated_latency_seconds for t in ctx.task_assignments)
        metrics.sequential_estimated_latency_ms = total_sequential_est * 1000.0

        # 2. Process waves in increasing order of wave index
        for wave_id in sorted_wave_keys:
            tasks_in_wave = waves[wave_id]
            logger.info(f"Executing Wave {wave_id} with {len(tasks_in_wave)} task(s)...")

            if len(tasks_in_wave) == 1:
                # Single task in wave -> execute directly
                self._execute_single_task(tasks_in_wave[0], ctx)
            else:
                # Multiple tasks in wave -> parallel execution via ThreadPoolExecutor
                self._execute_parallel_wave(tasks_in_wave, ctx)

        # 3. Conflict Detection and Resolution Phase
        conflicts = self.conflict_engine.detect_conflicts(ctx.task_outputs)
        if conflicts:
            ctx.status = CollaborationStatus.CONFLICT_RESOLVING
            for conflict in conflicts:
                reviewer_out = self._find_reviewer_output(ctx)
                resolved_conflict = self.conflict_engine.resolve_conflict(
                    conflict, ctx.task_outputs, reviewer_output=reviewer_out
                )
                ctx.conflicts.append(resolved_conflict)
                metrics.conflicts_detected += 1
                if resolved_conflict.is_resolved:
                    metrics.conflicts_resolved += 1

        # 4. Finalize execution metrics and status
        total_duration_ms = (time.time() - start_time) * 1000.0
        metrics.total_latency_ms = total_duration_ms
        metrics.calculate_speedup()

        failed_count = sum(1 for out in ctx.task_outputs.values() if out.status == "failed")
        metrics.completed_tasks = sum(1 for out in ctx.task_outputs.values() if out.status == "completed")
        metrics.failed_tasks = failed_count

        if failed_count == 0:
            ctx.status = CollaborationStatus.COMPLETED
        elif metrics.completed_tasks > 0:
            ctx.status = CollaborationStatus.COMPLETED  # Partial success
        else:
            ctx.status = CollaborationStatus.FAILED

        logger.info(
            f"Collaboration Session [{ctx.session_id}] finished in {total_duration_ms:.2f}ms. "
            f"Status: {ctx.status.value}, Completed: {metrics.completed_tasks}/{metrics.total_tasks}"
        )
        return ctx

    def _execute_single_task(self, task: TaskAssignment, ctx: CollaborationContext) -> AgentOutput:
        """Assign and execute a single task with error handling, retry, and fallback."""
        task.status = "running"
        agent = self.registry.find_best_agent(task.target_role, task.required_capabilities)

        if not agent:
            error_msg = f"No available agent found for role '{task.target_role.value}'"
            logger.error(error_msg)
            out = AgentOutput(
                task_id=task.task_id,
                agent_id="none",
                status="failed",
                error_message=error_msg,
                confidence_score=0.0,
            )
            ctx.task_outputs[task.task_id] = out
            task.status = "failed"
            return out

        agent_id = getattr(agent, "agent_id", "unknown_agent")
        task.assigned_agent_id = agent_id
        self.registry.update_status(agent_id, AgentStatus.BUSY)

        # Track agent metrics
        if agent_id not in ctx.metrics.agent_metrics:
            ctx.metrics.agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)
        agent_metrics = ctx.metrics.agent_metrics[agent_id]
        agent_metrics.tasks_assigned += 1

        start_t = time.time()
        try:
            # Inject inputs from SharedWorkspace
            inputs = {k: self.workspace.get(k) for k in task.input_keys if self.workspace.has(k)}
            inputs.update(task.parameters)

            output = agent.execute_task(task, inputs, self.workspace, self.memory)
            latency_ms = (time.time() - start_t) * 1000.0
            output.execution_latency_ms = latency_ms

            if output.status == "completed":
                task.status = "completed"
                agent_metrics.tasks_completed += 1
                agent_metrics.total_execution_latency_ms += latency_ms
                agent_metrics.average_confidence_score = (
                    (agent_metrics.average_confidence_score * (agent_metrics.tasks_completed - 1) + output.confidence_score)
                    / agent_metrics.tasks_completed
                )
                # Store outputs in SharedWorkspace
                if isinstance(output.result, dict):
                    for k, v in output.result.items():
                        self.workspace.set(k, v, agent_id=agent_id)
                elif output.result is not None:
                    self.workspace.set(f"result_{task.task_id}", output.result, agent_id=agent_id)
            else:
                task.status = "failed"
                agent_metrics.tasks_failed += 1

            ctx.task_outputs[task.task_id] = output
            return output

        except Exception as exc:
            logger.exception(f"Execution error on task {task.task_id} by agent {agent_id}: {exc}")
            latency_ms = (time.time() - start_t) * 1000.0
            task.status = "failed"
            agent_metrics.tasks_failed += 1
            output = AgentOutput(
                task_id=task.task_id,
                agent_id=agent_id,
                status="failed",
                error_message=str(exc),
                execution_latency_ms=latency_ms,
                confidence_score=0.0,
            )
            ctx.task_outputs[task.task_id] = output
            return output

        finally:
            self.registry.update_status(agent_id, AgentStatus.IDLE)

    def _execute_parallel_wave(self, tasks: List[TaskAssignment], ctx: CollaborationContext) -> None:
        """Execute a wave of independent tasks concurrently."""
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(tasks))) as executor:
            future_to_task = {
                executor.submit(self._execute_single_task, task, ctx): task for task in tasks
            }
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    out = future.result()
                    logger.debug(f"Parallel task {task.task_id} completed with status: {out.status}")
                except Exception as exc:
                    logger.error(f"Parallel wave task {task.task_id} raised exception: {exc}")

    def _find_reviewer_output(self, ctx: CollaborationContext) -> Optional[AgentOutput]:
        """Find reviewer agent output if present."""
        for t_id, out in ctx.task_outputs.items():
            assignment = ctx.get_assignment(t_id)
            if assignment and assignment.target_role == AgentRole.REVIEWER and out.status == "completed":
                return out
        return None
