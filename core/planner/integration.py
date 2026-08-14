"""Integration adapters connecting IntelligentPlanningEngine to existing systems.

Provides adapters for:
1. SafeCodeAgent — injects planning results as enhanced prompt context
2. SessionOrchestrator — converts DAG plans into workflow task trees

All adapters preserve backward compatibility with Version 1.1.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.planner.engine import IntelligentPlanningEngine
from core.planner.models.context import PlannerContext, PlannerStage
from infrastructure.logging.logger import StructuredLogger


class PlannerPromptAdapter:
    """Converts a PlannerContext into prompt-injection text for SafeCodeAgent.

    The adapter generates a structured planning summary that is injected into
    the agent's system prompt, giving it awareness of the execution plan, tool
    selection, and constraints before it begins generating code.
    """

    def __init__(self) -> None:
        self._logger = StructuredLogger("PlannerPromptAdapter")

    def generate_prompt_injection(self, ctx: PlannerContext) -> str:
        """Generate a structured planning summary for agent prompt injection."""
        if ctx.is_failed():
            return ""

        sections: List[str] = []
        sections.append("### EXECUTION PLAN")
        sections.append(f"**Intent:** {ctx.intent.value if ctx.intent else 'unknown'}")
        sections.append(f"**Complexity:** {ctx.complexity.score}/10" if ctx.complexity else "")

        # Sub-task plan
        if ctx.sub_tasks:
            sections.append("\n**Planned Steps:**")
            for i, task in enumerate(ctx.sub_tasks, 1):
                dep_str = ""
                if task.dependencies:
                    dep_str = f" (depends on: {', '.join(task.dependencies[:2])})"
                optional_str = " [optional]" if task.is_optional else ""
                sections.append(
                    f"{i}. {task.title} → tool: `{task.tool_name}`{dep_str}{optional_str}"
                )

        # Tool selection
        if ctx.tool_selection:
            sections.append(
                f"\n**Selected Tools:** {', '.join(ctx.tool_selection.selected_tools)}"
            )

        # Parallel execution hints
        if ctx.parallel_groups and len(ctx.parallel_groups) > 1:
            sections.append("\n**Parallel Execution Waves:**")
            for i, group in enumerate(ctx.parallel_groups):
                if ctx.execution_graph:
                    titles = [
                        ctx.execution_graph.nodes[nid].title
                        for nid in group
                        if nid in ctx.execution_graph.nodes
                    ]
                    sections.append(f"  Wave {i}: {', '.join(titles)}")

        # Constraints
        sections.append(
            f"\n**Constraints:** max_steps={ctx.constraints.max_steps}, "
            f"timeout={ctx.constraints.timeout_seconds:.0f}s, "
            f"verification={'required' if ctx.constraints.require_verification else 'optional'}"
        )

        prompt = "\n".join(s for s in sections if s)
        self._logger.info(f"Generated prompt injection ({len(prompt)} chars)")
        return prompt


class PlannerWorkflowAdapter:
    """Converts a PlannerContext into workflow tasks for SessionOrchestrator.

    This adapter translates the planning engine's DAG-based plan into the
    existing WorkflowTask format used by the SessionOrchestrator, ensuring
    seamless backward compatibility.
    """

    def __init__(self) -> None:
        self._logger = StructuredLogger("PlannerWorkflowAdapter")

    def to_workflow_tasks(self, ctx: PlannerContext) -> List[Dict[str, Any]]:
        """Convert sub-tasks into a list of workflow-compatible task dicts."""
        if ctx.is_failed() or not ctx.sub_tasks:
            return []

        workflow_tasks: List[Dict[str, Any]] = []
        for task in ctx.sub_tasks:
            wf_task: Dict[str, Any] = {
                "task_id": task.task_id,
                "title": task.title,
                "tool_name": task.tool_name,
                "action": task.action,
                "parameters": task.parameters,
                "dependencies": task.dependencies,
                "is_optional": task.is_optional,
                "estimated_latency_seconds": task.estimated_latency_seconds,
            }
            workflow_tasks.append(wf_task)

        self._logger.info(f"Converted {len(workflow_tasks)} sub-tasks to workflow format")
        return workflow_tasks


class AgentPlannerIntegration:
    """High-level integration facade for attaching the planner to an agent.

    Usage:
        integration = AgentPlannerIntegration()
        ctx = integration.plan_for_agent(query, tool_metadata_list)
        prompt_hint = integration.get_prompt_hint(ctx)
        # Inject prompt_hint into agent's system prompt
    """

    def __init__(self, engine: Optional[IntelligentPlanningEngine] = None) -> None:
        self._engine = engine or IntelligentPlanningEngine()
        self._prompt_adapter = PlannerPromptAdapter()
        self._workflow_adapter = PlannerWorkflowAdapter()
        self._logger = StructuredLogger("AgentPlannerIntegration")

    def plan_for_agent(
        self,
        query: str,
        available_tools: Optional[List[Dict[str, Any]]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        session_id: Optional[str] = None,
    ) -> PlannerContext:
        """Run the planning engine and return the full context."""
        return self._engine.plan(
            query=query,
            available_tools=available_tools,
            conversation_history=conversation_history,
            session_id=session_id,
        )

    def get_prompt_hint(self, ctx: PlannerContext) -> str:
        """Generate the prompt injection string from a planned context."""
        return self._prompt_adapter.generate_prompt_injection(ctx)

    def get_workflow_tasks(self, ctx: PlannerContext) -> List[Dict[str, Any]]:
        """Convert planned context into workflow tasks."""
        return self._workflow_adapter.to_workflow_tasks(ctx)

    def get_planning_summary(self, ctx: PlannerContext) -> Dict[str, Any]:
        """Return the serialized planning context summary."""
        return ctx.to_dict()
