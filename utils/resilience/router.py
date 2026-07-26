"""Provider router for dynamically selecting the best available LLM provider."""

import logging
from typing import List, Dict
from utils.resilience.registry import ProviderRegistry
from utils.resilience.circuit_breaker import CircuitBreaker
from utils.resilience.errors import AllModelsFailedError

logger = logging.getLogger("LLMResilience.Router")


class ProviderRouter:
    """Selects the best available model/provider dynamically based on health and scoring."""

    def __init__(self, registry: ProviderRegistry, circuit_breaker: CircuitBreaker) -> None:
        self.registry = registry
        self.circuit_breaker = circuit_breaker

    def select_model(self, requested_model: str) -> str:
        """Selects a model dynamically.

        If requested_model is healthy, returns it. Otherwise, selects the highest scoring
        available alternative from the registry fallback chain.
        """
        configured_models = self.registry.get_configured_providers()
        if not configured_models:
            raise AllModelsFailedError("No LLM providers are configured in the environment.")

        # Check if the requested model is configured and healthy
        if requested_model in configured_models and self.circuit_breaker.is_available(requested_model):
            return requested_model

        # Requested model is unavailable, score all configured alternatives
        scores: Dict[str, float] = {}
        for model in configured_models:
            if not self.circuit_breaker.is_available(model):
                continue

            # Calculate base priority
            if model.startswith(("ollama/", "ollama_chat/")):
                base_priority = 100.0  # Local models first
            elif model.startswith("gemini/"):
                base_priority = 80.0
            elif model.startswith("openai/"):
                base_priority = 70.0
            elif model.startswith("anthropic/"):
                base_priority = 60.0
            else:
                base_priority = 50.0

            # Fetch health status metrics
            health = self.circuit_breaker.get_status(model)
            failures = health.get("consecutive_failures", 0)
            avg_latency = health.get("average_latency", 0.0)

            # Apply penalties
            failure_penalty = failures * 20.0
            latency_penalty = avg_latency * 10.0

            score = base_priority - failure_penalty - latency_penalty
            scores[model] = score

        if not scores:
            # All configured models are currently OPEN/cooling down
            raise AllModelsFailedError(
                f"All configured LLM providers failed. Cooldowns are active for: {configured_models}"
            )

        # Pick the highest scoring model
        selected_model = max(scores, key=scores.get)
        
        if selected_model != requested_model:
            logger.info(
                f"Failover routing triggered. Failing over from '{requested_model}' "
                f"to '{selected_model}' (Scores: {scores})"
            )

        return selected_model
