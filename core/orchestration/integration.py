"""LLMOrchestrationIntegration — facade connecting the Orchestrator to Agent Runtimes.

Enables seamless integration with SafeCodeAgent, ResilientLiteLLMModel, and
IntelligentPlanningEngine.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Tuple

from core.orchestration.models.policy import LLMRoutingPolicy
from core.orchestration.models.request import LLMRequest, LLMResponse
from core.orchestration.orchestrator import IntelligentLLMOrchestrator
from infrastructure.logging.logger import StructuredLogger


class LLMOrchestrationIntegration:
    """Facade exposing orchestrator capabilities to agents and planning engines."""

    def __init__(
        self,
        orchestrator: Optional[IntelligentLLMOrchestrator] = None,
        policy: Optional[LLMRoutingPolicy] = None,
    ) -> None:
        self.orchestrator = orchestrator or IntelligentLLMOrchestrator(policy=policy)
        self._logger = StructuredLogger("LLMOrchestrationIntegration")

    def route_and_generate(
        self,
        prompt: str,
        task_type: str = "general_qa",
        complexity_score: int = 5,
        completion_runner: Optional[Callable[[str, LLMRequest], Tuple[str, int, int]]] = None,
    ) -> LLMResponse:
        """Route and execute prompt generation."""
        return self.orchestrator.complete_for_agent(
            prompt=prompt,
            task_type=task_type,
            complexity_score=complexity_score,
            completion_runner=completion_runner,
        )

    def get_summary(self) -> Dict[str, Any]:
        """Return orchestrator telemetry summary."""
        return self.orchestrator.get_telemetry_summary()
