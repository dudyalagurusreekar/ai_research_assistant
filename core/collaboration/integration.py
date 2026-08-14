"""Integration adapters connecting Multi-Agent Collaboration Engine with Planner, Reflection, Learning, and Data Intelligence engines."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.collaboration.engine import MultiAgentCollaborationEngine
from core.collaboration.models.agent_info import AgentRole
from core.collaboration.models.context import CollaborationContext, TaskAssignment
from utils.logger import get_logger

logger = get_logger("CollaborationIntegration")


class PlannerCollaborationIntegration:
    """Adapter bridging supervisory Intelligent Planning Engine DAGs with Multi-Agent Collaboration Engine."""

    def __init__(self, collab_engine: Optional[MultiAgentCollaborationEngine] = None) -> None:
        self.collab_engine = collab_engine or MultiAgentCollaborationEngine()

    def convert_planner_context_to_assignments(self, planner_ctx: Any) -> List[TaskAssignment]:
        """Convert a PlannerContext DAG into typed multi-agent TaskAssignments."""
        assignments: List[TaskAssignment] = []
        if not hasattr(planner_ctx, "execution_graph") or not planner_ctx.execution_graph:
            return assignments

        graph = planner_ctx.execution_graph
        nodes = getattr(graph, "nodes", {})

        for node_id, node in nodes.items():
            tool_name = getattr(node, "tool_name", "").lower()
            action = getattr(node, "action", "").lower()
            title = getattr(node, "title", node_id)
            wave = getattr(node, "parallel_level", 0)

            # Map tool/action to agent role
            if "data" in tool_name or "stat" in action or "profile" in action:
                role = AgentRole.DATA
            elif "code" in tool_name or "python" in tool_name or "exec" in action:
                role = AgentRole.CODE
            elif "report" in action or "writer" in tool_name or "summary" in action:
                role = AgentRole.WRITER
            elif "review" in action or "audit" in action or "verify" in action:
                role = AgentRole.REVIEWER
            else:
                role = AgentRole.RESEARCH

            assignment = TaskAssignment(
                task_id=getattr(node, "node_id", node_id),
                title=title,
                description=f"Action: {action} via {tool_name}",
                target_role=role,
                parameters=getattr(node, "parameters", {}),
                parallel_wave=wave,
            )
            assignments.append(assignment)

        return assignments

    def execute_planner_dag(self, planner_ctx: Any) -> CollaborationContext:
        """Execute a PlannerContext execution graph via multi-agent collaboration."""
        query = getattr(planner_ctx, "query", "Supervised research plan")
        intent = getattr(planner_ctx, "intent", "multi_step_research")
        if hasattr(intent, "value"):
            intent = intent.value

        assignments = self.convert_planner_context_to_assignments(planner_ctx)

        if not assignments:
            # Create default multi-agent assignments for query
            ctx = self.collab_engine.execute_preset_workflow("full_multi_agent", query)
        else:
            ctx = self.collab_engine.create_collaboration_session(query=query, intent=str(intent))
            ctx = self.collab_engine.execute_assignments(assignments, context=ctx)

        return ctx


class ReflectionCollaborationIntegration:
    """Adapter bridging Reflection Engine evaluation with Multi-Agent Conflict Resolution."""

    def __init__(self, collab_engine: Optional[MultiAgentCollaborationEngine] = None) -> None:
        self.collab_engine = collab_engine or MultiAgentCollaborationEngine()

    def evaluate_and_replan_if_needed(self, ctx: CollaborationContext, reflection_engine: Any) -> CollaborationContext:
        """Evaluate collaboration output quality via Reflection Engine and trigger replanning if required."""
        if not reflection_engine or not hasattr(reflection_engine, "evaluate_and_reflect"):
            return ctx

        # Check for unresolved conflicts or failures
        has_unresolved = any(not c.is_resolved for c in ctx.conflicts)
        failed_tasks = [t_id for t_id, out in ctx.task_outputs.items() if out.status == "failed"]

        if has_unresolved or failed_tasks:
            logger.info(f"Triggering ReflectionEngine replanning for session [{ctx.session_id}] due to agent failures")
            # Invoke reflection engine
            try:
                task_outputs_dict = {k: v.to_dict() for k, v in ctx.task_outputs.items()}
                decision = reflection_engine.evaluate_and_reflect(ctx, task_outputs_dict)
                ctx.shared_workspace_id += f"_reflected"
            except Exception as exc:
                logger.warning(f"Reflection engine evaluation exception: {exc}")

        return ctx


class LearningCollaborationIntegration:
    """Adapter logging multi-agent execution experiences into ContinuousLearningEngine."""

    def record_collaboration_experience(self, ctx: CollaborationContext, learning_engine: Any) -> bool:
        """Record session latency, parallel speedup, token usage, and outcome into ContinuousLearningEngine."""
        if not learning_engine or not hasattr(learning_engine, "record_experience"):
            return False

        try:
            metrics = ctx.metrics
            learning_engine.record_experience(
                query=ctx.query,
                intent=ctx.intent,
                complexity_score=5,
                selected_tools=["multi_agent_framework"],
                excluded_tools=[],
                dag_nodes_count=len(ctx.task_assignments),
                dag_edges_count=len(ctx.task_assignments) - 1 if ctx.task_assignments else 0,
                parallel_waves=len(set(t.parallel_wave for t in ctx.task_assignments)),
                execution_latency_ms=metrics.total_latency_ms,
                total_tokens_used=metrics.total_tokens_used,
                total_cost_usd=metrics.total_cost_usd,
            )
            logger.info(f"Recorded collaboration experience for query '{ctx.query}' in ContinuousLearningEngine")
            return True
        except Exception as exc:
            logger.warning(f"Failed to record experience in ContinuousLearningEngine: {exc}")
            return False
