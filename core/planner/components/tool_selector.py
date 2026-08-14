"""ToolSelector — determines the minimum required tool set for a request.

Filters the full list of available tools to only those that the execution plan
actually needs, reducing prompt noise and preventing unnecessary invocations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from core.execution.selection_engine import AdaptiveToolSelectionEngine
from core.planner.interfaces.base import IToolSelector
from core.planner.models.context import PlannerContext, ToolSelection
from infrastructure.logging.logger import StructuredLogger


class ToolSelector(IToolSelector):
    """Adaptively selects the minimum required tool set using utility scoring."""

    def __init__(self, adaptive_engine: Optional[AdaptiveToolSelectionEngine] = None) -> None:
        self._adaptive_engine = adaptive_engine or AdaptiveToolSelectionEngine()
        self._logger = StructuredLogger("ToolSelector")

    @property
    def component_name(self) -> str:
        return "ToolSelector"

    def select(self, ctx: PlannerContext) -> ToolSelection:
        """Delegate tool selection to the AdaptiveToolSelectionEngine."""
        return self._adaptive_engine.select(ctx)
