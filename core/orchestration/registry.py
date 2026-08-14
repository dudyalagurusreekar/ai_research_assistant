"""LLMProviderRegistry — metadata store and health tracking for LLM endpoints.

Maintains LLMProviderDescriptor records for local (Ollama/vLLM) and cloud models,
tracks real-time token processing, pricing, latencies, reliability scores (0.0 to 1.0),
and circuit breaker health status.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.orchestration.models.descriptor import (
    LLMProviderDescriptor,
    ModelTier,
    ProviderHealthStatus,
    ProviderType,
)
from infrastructure.logging.logger import StructuredLogger


# Default specifications for standard LLM models across tiers and providers
DEFAULT_MODEL_DESCRIPTORS: Dict[str, Dict[str, Any]] = {
    # -----------------------------------------------------------------------
    # Local Models (Ollama / vLLM) — $0 cost, Routine tasks
    # -----------------------------------------------------------------------
    "ollama/phi3:latest": {
        "name": "Phi-3 Mini (Local)",
        "provider_type": ProviderType.LOCAL,
        "tier": ModelTier.ROUTINE,
        "description": "Fast local model for routine planning, basic QA, and status checks",
        "capabilities": ["text", "planning", "summarization"],
        "context_window": 8192,
        "max_tokens": 2048,
        "input_cost_per_1k": 0.0,
        "output_cost_per_1k": 0.0,
        "estimated_latency_ms": 300.0,
        "reliability_score": 0.99,
        "fallback_models": ["ollama/llama3:latest", "gemini/gemini-2.5-flash"],
    },
    "ollama/llama3:latest": {
        "name": "Llama-3 8B (Local)",
        "provider_type": ProviderType.LOCAL,
        "tier": ModelTier.ROUTINE,
        "description": "Local 8B parameter model for routine tasks and summaries",
        "capabilities": ["text", "planning", "summarization"],
        "context_window": 8192,
        "max_tokens": 2048,
        "input_cost_per_1k": 0.0,
        "output_cost_per_1k": 0.0,
        "estimated_latency_ms": 450.0,
        "reliability_score": 0.98,
        "fallback_models": ["gemini/gemini-2.5-flash"],
    },

    # -----------------------------------------------------------------------
    # Cloud Models (Gemini / OpenAI / Anthropic) — Tiered Pricing & Capabilities
    # -----------------------------------------------------------------------
    "gemini/gemini-2.5-flash": {
        "name": "Google Gemini 2.5 Flash",
        "provider_type": ProviderType.CLOUD_GEMINI,
        "tier": ModelTier.BALANCED,
        "description": "High-speed, low-cost balanced model for standard research tasks",
        "capabilities": ["text", "structured_output", "code", "vision"],
        "context_window": 1048576,
        "max_tokens": 8192,
        "input_cost_per_1k": 0.0001,
        "output_cost_per_1k": 0.0004,
        "estimated_latency_ms": 800.0,
        "reliability_score": 0.98,
        "fallback_models": ["openai/gpt-4o-mini", "ollama/phi3:latest"],
    },
    "gemini/gemini-2.5-pro": {
        "name": "Google Gemini 2.5 Pro",
        "provider_type": ProviderType.CLOUD_GEMINI,
        "tier": ModelTier.ADVANCED,
        "description": "Advanced multi-modal model for complex document analysis and research",
        "capabilities": ["text", "structured_output", "code", "vision", "complex_reasoning"],
        "context_window": 2097152,
        "max_tokens": 8192,
        "input_cost_per_1k": 0.00125,
        "output_cost_per_1k": 0.005,
        "estimated_latency_ms": 2200.0,
        "reliability_score": 0.96,
        "fallback_models": ["anthropic/claude-3-5-sonnet", "openai/gpt-4o"],
    },
    "openai/gpt-4o-mini": {
        "name": "OpenAI GPT-4o Mini",
        "provider_type": ProviderType.CLOUD_OPENAI,
        "tier": ModelTier.BALANCED,
        "description": "Fast and efficient balanced model for general tasks",
        "capabilities": ["text", "structured_output", "code"],
        "context_window": 128000,
        "max_tokens": 4096,
        "input_cost_per_1k": 0.00015,
        "output_cost_per_1k": 0.0006,
        "estimated_latency_ms": 900.0,
        "reliability_score": 0.98,
        "fallback_models": ["gemini/gemini-2.5-flash"],
    },
    "openai/gpt-4o": {
        "name": "OpenAI GPT-4o",
        "provider_type": ProviderType.CLOUD_OPENAI,
        "tier": ModelTier.ADVANCED,
        "description": "Flagship multi-modal model for advanced reasoning and coding",
        "capabilities": ["text", "structured_output", "code", "vision", "complex_reasoning"],
        "context_window": 128000,
        "max_tokens": 4096,
        "input_cost_per_1k": 0.0025,
        "output_cost_per_1k": 0.010,
        "estimated_latency_ms": 1800.0,
        "reliability_score": 0.97,
        "fallback_models": ["anthropic/claude-3-5-sonnet", "gemini/gemini-2.5-pro"],
    },
    "anthropic/claude-3-5-sonnet": {
        "name": "Anthropic Claude 3.5 Sonnet",
        "provider_type": ProviderType.CLOUD_ANTHROPIC,
        "tier": ModelTier.ADVANCED,
        "description": "State-of-the-art model for coding, reasoning, and document analysis",
        "capabilities": ["text", "code", "vision", "complex_reasoning"],
        "context_window": 200000,
        "max_tokens": 8192,
        "input_cost_per_1k": 0.003,
        "output_cost_per_1k": 0.015,
        "estimated_latency_ms": 1900.0,
        "reliability_score": 0.97,
        "fallback_models": ["openai/gpt-4o", "gemini/gemini-2.5-pro"],
    },
}


class LLMProviderRegistry:
    """Central registry tracking LLM descriptors, performance, costs, and health."""

    def __init__(self) -> None:
        self._descriptors: Dict[str, LLMProviderDescriptor] = {}
        self._logger = StructuredLogger("LLMProviderRegistry")
        self._initialize_defaults()

    def _initialize_defaults(self) -> None:
        """Populate the registry with standard LLM descriptors."""
        for model_id, spec in DEFAULT_MODEL_DESCRIPTORS.items():
            descriptor = LLMProviderDescriptor(
                model_id=model_id,
                name=spec["name"],
                provider_type=spec["provider_type"],
                tier=spec["tier"],
                description=spec["description"],
                capabilities=spec["capabilities"],
                context_window=spec["context_window"],
                max_tokens=spec["max_tokens"],
                input_cost_per_1k=spec["input_cost_per_1k"],
                output_cost_per_1k=spec["output_cost_per_1k"],
                estimated_latency_ms=spec["estimated_latency_ms"],
                avg_actual_latency_ms=spec["estimated_latency_ms"],
                reliability_score=spec["reliability_score"],
                fallback_models=spec["fallback_models"],
            )
            self._descriptors[model_id] = descriptor

    def register_descriptor(self, descriptor: LLMProviderDescriptor) -> None:
        """Register or overwrite an LLM descriptor."""
        self._descriptors[descriptor.model_id] = descriptor
        self._logger.info(f"Registered LLM provider descriptor for '{descriptor.model_id}'")

    def get_descriptor(self, model_id: str) -> Optional[LLMProviderDescriptor]:
        """Retrieve descriptor by model ID."""
        return self._descriptors.get(model_id)

    def list_descriptors(self) -> List[LLMProviderDescriptor]:
        """List all registered LLM descriptors."""
        return list(self._descriptors.values())

    def list_available_descriptors(self) -> List[LLMProviderDescriptor]:
        """Return descriptors for healthy and degraded (available) providers."""
        return [d for d in self._descriptors.values() if d.is_available()]

    def filter_by_tier(self, tier: ModelTier) -> List[LLMProviderDescriptor]:
        """Return available descriptors matching a specific tier."""
        return [d for d in self.list_available_descriptors() if d.tier == tier]

    def filter_by_provider_type(self, provider_type: ProviderType) -> List[LLMProviderDescriptor]:
        """Return available descriptors for a specific provider type (e.g. LOCAL vs CLOUD)."""
        return [d for d in self.list_available_descriptors() if d.provider_type == provider_type]

    def record_outcome(
        self,
        model_id: str,
        success: bool,
        latency_ms: float = 0.0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        error_message: str = "",
    ) -> None:
        """Update provider metrics, token counts, costs, and reliability scores."""
        d = self._descriptors.get(model_id)
        if not d:
            return

        if success:
            tokens = prompt_tokens + completion_tokens
            cost = (
                (prompt_tokens / 1000.0 * d.input_cost_per_1k) +
                (completion_tokens / 1000.0 * d.output_cost_per_1k)
            )
            d.record_success(latency_ms=latency_ms, tokens=tokens, cost=cost)
            self._logger.debug(
                f"Provider '{model_id}' success: tokens={tokens}, cost=${cost:.5f}, "
                f"reliability={d.reliability_score:.2f}"
            )
        else:
            d.record_failure(error_message)
            self._logger.warning(
                f"Provider '{model_id}' failure: error='{error_message}', "
                f"consecutive_failures={d.consecutive_failures}, health={d.health_status.value}"
            )

    def reset_circuit_breaker(self, model_id: Optional[str] = None) -> None:
        """Reset consecutive failure counter and restore health status."""
        if model_id:
            d = self._descriptors.get(model_id)
            if d:
                d.reset_circuit_breaker()
        else:
            for d in self._descriptors.values():
                d.reset_circuit_breaker()

    def to_dict(self) -> Dict[str, Any]:
        """Return telemetry summary of all registered providers."""
        total_cost = sum(d.total_cost_accumulated for d in self._descriptors.values())
        total_tokens = sum(d.total_tokens_processed for d in self._descriptors.values())

        return {
            "total_providers": len(self._descriptors),
            "available_providers": len(self.list_available_descriptors()),
            "total_tokens_processed": total_tokens,
            "total_cost_accumulated": round(total_cost, 6),
            "descriptors": {mid: d.to_dict() for mid, d in self._descriptors.items()},
        }
