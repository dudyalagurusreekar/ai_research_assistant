"""AdaptiveToolSelectionEngine — intelligent tool selection for ARA v2.0.

Evaluates execution plan sub-tasks against the AdaptiveToolRegistry and selects the
optimal tool using a multi-attribute utility scoring formula combining capability match,
historical reliability (0.0 to 1.0), latency, and cost. Assigns fallback tool chains.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from core.execution.models.descriptor import ToolCapabilityDescriptor
from core.execution.models.policy import ExecutionPolicy
from core.execution.registry import AdaptiveToolRegistry
from core.planner.interfaces.base import IToolSelector
from core.planner.models.context import PlannerContext, ToolSelection
from infrastructure.logging.logger import StructuredLogger


class AdaptiveToolSelectionEngine(IToolSelector):
    """Production tool selection engine combining capability matching with dynamic reliability."""

    def __init__(
        self,
        registry: Optional[AdaptiveToolRegistry] = None,
        policy: Optional[ExecutionPolicy] = None,
    ) -> None:
        self.registry = registry or AdaptiveToolRegistry()
        self.policy = policy or ExecutionPolicy()
        self._logger = StructuredLogger("AdaptiveToolSelectionEngine")

    @property
    def component_name(self) -> str:
        return "AdaptiveToolSelectionEngine"

    def select(self, ctx: PlannerContext) -> ToolSelection:
        """Select optimal tools for the planner context using composite utility scoring."""
        available_descriptors = self.registry.list_healthy_descriptors()
        available_names = {d.name for d in available_descriptors}

        # Also register any tools from ctx.available_tools that aren't yet in registry
        for tool_info in ctx.available_tools:
            d = self.registry.register_from_tool_info(tool_info)
            available_names.add(d.name)

        selected_tools: Set[str] = set()
        selection_reasons: Dict[str, str] = {}
        fallback_assignments: Dict[str, List[str]] = {}

        # 1. Evaluate required tools for each sub-task
        for sub_task in ctx.sub_tasks:
            req_tool = sub_task.tool_name
            if not req_tool:
                continue

            best_descriptor, score = self._find_best_tool(req_tool, sub_task.action)
            if best_descriptor:
                selected_tools.add(best_descriptor.name)
                reason = (
                    f"Selected for '{sub_task.title}' (score={score:.2f}, "
                    f"reliability={best_descriptor.reliability_score:.2f}, "
                    f"latency={best_descriptor.avg_actual_latency_ms:.0f}ms)"
                )
                selection_reasons[best_descriptor.name] = reason
                fallback_assignments[best_descriptor.name] = best_descriptor.fallback_tools

        # 2. Always include python_interpreter as orchestration core
        selected_tools.add("python_interpreter")
        selection_reasons["python_interpreter"] = "Core execution runtime backbone"

        # 3. Determine excluded tools
        all_known_tools = {d.name for d in self.registry.list_descriptors()}
        excluded_tools = sorted(all_known_tools - selected_tools)

        total_available = len(all_known_tools)
        reduction = 0.0
        if total_available > 0:
            reduction = ((total_available - len(selected_tools)) / total_available) * 100.0

        selection = ToolSelection(
            selected_tools=sorted(selected_tools),
            excluded_tools=excluded_tools,
            selection_reasons=selection_reasons,
            total_available=total_available,
            reduction_percentage=round(reduction, 1),
        )

        ctx.tool_selection = selection
        ctx.metrics.unnecessary_tools_removed = len(excluded_tools)
        ctx.add_trace(
            stage="adaptive_tool_selection",
            message=f"Adaptively selected {len(selected_tools)}/{total_available} tools "
                    f"({selection.reduction_percentage}% noise reduction)",
            data={
                "selected": sorted(selected_tools),
                "excluded": excluded_tools,
                "reasons": selection_reasons,
                "fallbacks": fallback_assignments,
            },
        )
        self._logger.info(
            f"Adaptive Tool Selection: {len(selected_tools)}/{total_available} tools selected "
            f"({selection.reduction_percentage}% reduction)"
        )
        return selection

    def _find_best_tool(
        self,
        required_capability: str,
        action: str = "",
    ) -> tuple[Optional[ToolCapabilityDescriptor], float]:
        """Find the tool descriptor with the highest composite utility score for a capability."""
        candidates = self.registry.find_by_capability(required_capability)
        if not candidates:
            # Fallback to direct lookup
            desc = self.registry.get_descriptor(required_capability)
            if desc and desc.is_available():
                candidates = [desc]

        if not candidates:
            # Fallback to python_interpreter if capability is unavailable
            py_desc = self.registry.get_descriptor("python_interpreter")
            return py_desc, 0.5

        best_desc: Optional[ToolCapabilityDescriptor] = None
        best_score: float = -1.0

        for candidate in candidates:
            # Check capability match
            cap_match = 1.0 if required_capability.lower() == candidate.name.lower() else 0.85
            score = candidate.compute_score(
                capability_match=cap_match,
                weight_capability=self.policy.weight_capability,
                weight_reliability=self.policy.weight_reliability,
                weight_latency=self.policy.weight_latency,
                weight_cost=self.policy.weight_cost,
            )
            if score > best_score:
                best_score = score
                best_desc = candidate

        return best_desc, best_score
