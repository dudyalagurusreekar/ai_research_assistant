"""ExecutionOptimizationEngine — execution wave and DAG optimizer.

Prunes redundant nodes using cache lookup, groups independent task nodes into
parallel execution waves bounded by worker pools, attaches fallback chains, and
calculates total plan latency and cost estimates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from core.execution.cache import ToolResultCache
from core.execution.fallback import ToolFallbackEngine
from core.execution.models.policy import ExecutionPolicy
from core.execution.registry import AdaptiveToolRegistry
from core.planner.models.context import PlannerContext
from core.planner.models.graph import ExecutionGraph, PlanNode
from infrastructure.logging.logger import StructuredLogger


@dataclass
class OptimizedNode:
    """An execution-optimized PlanNode wrapper with fallback and cache annotations."""

    node_id: str = ""
    task_id: str = ""
    title: str = ""
    tool_name: str = ""
    action: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    fallback_tools: List[str] = field(default_factory=list)
    is_cached: bool = False
    cache_key: Optional[str] = None
    estimated_latency_ms: float = 1000.0
    estimated_cost: float = 0.001
    parallel_wave: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize node optimization info."""
        return {
            "node_id": self.node_id,
            "task_id": self.task_id,
            "title": self.title,
            "tool_name": self.tool_name,
            "action": self.action,
            "fallback_tools": self.fallback_tools,
            "is_cached": self.is_cached,
            "parallel_wave": self.parallel_wave,
            "estimated_latency_ms": self.estimated_latency_ms,
        }


@dataclass
class OptimizedExecutionPlan:
    """Complete execution plan ready for parallel/sequential dispatch."""

    plan_id: str = ""
    execution_waves: List[List[OptimizedNode]] = field(default_factory=list)
    total_nodes: int = 0
    cached_nodes: int = 0
    runnable_nodes: int = 0
    estimated_total_latency_ms: float = 0.0
    estimated_total_cost: float = 0.0
    parallelization_efficiency: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize plan for logging and metrics."""
        return {
            "plan_id": self.plan_id,
            "total_nodes": self.total_nodes,
            "cached_nodes": self.cached_nodes,
            "runnable_nodes": self.runnable_nodes,
            "wave_count": len(self.execution_waves),
            "estimated_total_latency_ms": round(self.estimated_total_latency_ms, 1),
            "estimated_total_cost": round(self.estimated_total_cost, 4),
            "parallelization_efficiency": round(self.parallelization_efficiency, 2),
        }


class ExecutionOptimizationEngine:
    """Optimizes execution DAGs by pruning cached calls and building parallel waves."""

    def __init__(
        self,
        registry: Optional[AdaptiveToolRegistry] = None,
        cache: Optional[ToolResultCache] = None,
        fallback_engine: Optional[ToolFallbackEngine] = None,
        policy: Optional[ExecutionPolicy] = None,
    ) -> None:
        self.registry = registry or AdaptiveToolRegistry()
        self.cache = cache or ToolResultCache()
        self.fallback_engine = fallback_engine or ToolFallbackEngine(registry=self.registry)
        self.policy = policy or ExecutionPolicy()
        self._logger = StructuredLogger("ExecutionOptimizationEngine")

    def optimize(self, ctx: PlannerContext) -> OptimizedExecutionPlan:
        """Analyze PlannerContext DAG and produce an OptimizedExecutionPlan."""
        graph = ctx.execution_graph
        plan = OptimizedExecutionPlan(plan_id=ctx.plan_id)

        if not graph or graph.node_count() == 0:
            return plan

        # 1. Compute parallel levels from DAG
        levels = graph.compute_parallel_levels()

        total_nodes = 0
        cached_nodes = 0
        runnable_nodes = 0
        sequential_latency_sum = 0.0
        wave_latency_sum = 0.0
        total_cost = 0.0

        optimized_waves: List[List[OptimizedNode]] = []

        for wave_idx, level_nodes in enumerate(levels):
            wave: List[OptimizedNode] = []
            max_wave_latency = 0.0

            for node_id in level_nodes:
                node = graph.nodes[node_id]
                total_nodes += 1

                # Check descriptor info
                desc = self.registry.get_descriptor(node.tool_name)
                est_lat = desc.avg_actual_latency_ms if desc else 1000.0
                cost = desc.cost_per_call if desc else 0.001
                fallbacks = self.fallback_engine.get_fallbacks(node.tool_name)

                # Check result cache
                cache_key = None
                is_cached = False
                if self.policy.enable_caching and node.tool_name and node.action:
                    cached_res = self.cache.get(
                        tool_name=node.tool_name,
                        action=node.action,
                        parameters=node.parameters,
                        estimated_latency_ms=est_lat,
                    )
                    if cached_res:
                        is_cached = True
                        cache_key = cached_res.cache_key
                        cached_nodes += 1
                    else:
                        runnable_nodes += 1
                        sequential_latency_sum += est_lat
                        max_wave_latency = max(max_wave_latency, est_lat)
                        total_cost += cost
                else:
                    runnable_nodes += 1
                    sequential_latency_sum += est_lat
                    max_wave_latency = max(max_wave_latency, est_lat)
                    total_cost += cost

                opt_node = OptimizedNode(
                    node_id=node.node_id,
                    task_id=node.task_id,
                    title=node.title,
                    tool_name=node.tool_name,
                    action=node.action,
                    parameters=node.parameters,
                    fallback_tools=fallbacks,
                    is_cached=is_cached,
                    cache_key=cache_key,
                    estimated_latency_ms=0.5 if is_cached else est_lat,
                    estimated_cost=0.0 if is_cached else cost,
                    parallel_wave=wave_idx,
                )
                wave.append(opt_node)

            optimized_waves.append(wave)
            wave_latency_sum += max_wave_latency

        # Compute parallelization efficiency (sequential latency / wave latency)
        efficiency = (sequential_latency_sum / wave_latency_sum) if wave_latency_sum > 0 else 1.0

        plan.execution_waves = optimized_waves
        plan.total_nodes = total_nodes
        plan.cached_nodes = cached_nodes
        plan.runnable_nodes = runnable_nodes
        plan.estimated_total_latency_ms = wave_latency_sum
        plan.estimated_total_cost = total_cost
        plan.parallelization_efficiency = efficiency

        ctx.add_trace(
            stage="execution_optimization",
            message=f"Optimized execution plan: {len(optimized_waves)} waves, "
                    f"{cached_nodes} cached, {runnable_nodes} runnable, "
                    f"efficiency={efficiency:.2f}x",
            data=plan.to_dict(),
        )
        self._logger.info(
            f"Execution plan optimized: {len(optimized_waves)} waves, "
            f"{cached_nodes}/{total_nodes} cached, "
            f"est_latency={wave_latency_sum:.0f}ms (efficiency={efficiency:.2f}x)"
        )
        return plan
