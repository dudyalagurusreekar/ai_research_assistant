"""LLMRoutingEngine — dynamic model selection for ARA v2.0.

Routes LLM completion requests based on task complexity (Sprint 1 Planner score 1-10),
task type, latency budget, cost constraints, model capabilities, and real-time provider health.
Offloads routine tasks (planning, summarization, basic QA) to local Ollama models when available.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from core.orchestration.models.descriptor import LLMProviderDescriptor, ModelTier, ProviderType
from core.orchestration.models.policy import LLMRoutingPolicy
from core.orchestration.models.request import LLMRequest
from core.orchestration.registry import LLMProviderRegistry
from infrastructure.logging.logger import StructuredLogger


class LLMRoutingEngine:
    """Dynamic complexity-driven router for LLM completion requests."""

    def __init__(
        self,
        registry: Optional[LLMProviderRegistry] = None,
        policy: Optional[LLMRoutingPolicy] = None,
    ) -> None:
        self.registry = registry or LLMProviderRegistry()
        self.policy = policy or LLMRoutingPolicy()
        self._logger = StructuredLogger("LLMRoutingEngine")

    def route(self, request: LLMRequest) -> Tuple[LLMProviderDescriptor, List[str]]:
        """Select optimal primary LLM provider descriptor and return fallback model ID chain.

        Args:
            request: Target LLMRequest detailing prompt, complexity_score, task_type, etc.

        Returns:
            Tuple of (Primary LLMProviderDescriptor, List of Fallback model IDs)
        """
        # 1. Determine target ModelTier from complexity score & request preference
        target_tier = self._infer_target_tier(request)

        # 2. Get available candidates from registry
        candidates = self.registry.list_available_descriptors()
        if not candidates:
            raise RuntimeError("No LLM provider endpoints available in registry")

        # 3. If policy prefers local models for routine tasks (complexity <= 3) and no explicit preferred_tier is set, filter local candidates first
        if not request.preferred_tier and self.policy.prefer_local_for_routine and request.complexity_score <= self.policy.routine_complexity_max:
            local_candidates = [c for c in candidates if c.provider_type == ProviderType.LOCAL]
            if local_candidates:
                candidates = local_candidates
                self._logger.debug("Offloading routine task to local LLM provider")

        # 4. Score all candidates using composite utility function
        scored_candidates: List[Tuple[LLMProviderDescriptor, float]] = []
        for candidate in candidates:
            score = candidate.compute_routing_score(
                target_tier=target_tier,
                complexity_score=request.complexity_score,
                weight_tier=self.policy.weight_tier,
                weight_reliability=self.policy.weight_reliability,
                weight_cost=self.policy.weight_cost,
                weight_latency=self.policy.weight_latency,
            )
            scored_candidates.append((candidate, score))

        # Sort by score descending
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        primary_desc, best_score = scored_candidates[0]

        # 5. Build fallback candidate list
        fallbacks = [c[0].model_id for c in scored_candidates[1:] if c[0].model_id != primary_desc.model_id]
        if primary_desc.fallback_models:
            for fb in primary_desc.fallback_models:
                if fb not in fallbacks and fb != primary_desc.model_id:
                    fallbacks.append(fb)

        self._logger.info(
            f"Routed request '{request.task_type}' (complexity={request.complexity_score}) "
            f"-> Primary model: '{primary_desc.model_id}' (tier={primary_desc.tier.value}, score={best_score:.2f})"
        )

        return primary_desc, fallbacks

    def _infer_target_tier(self, request: LLMRequest) -> ModelTier:
        """Derive target ModelTier based on request preference or complexity score."""
        if request.preferred_tier:
            return request.preferred_tier

        complexity = request.complexity_score
        if complexity <= self.policy.routine_complexity_max:
            return ModelTier.ROUTINE
        elif complexity <= self.policy.balanced_complexity_max:
            return ModelTier.BALANCED
        elif complexity <= self.policy.advanced_complexity_max:
            return ModelTier.ADVANCED
        else:
            return ModelTier.REASONING
