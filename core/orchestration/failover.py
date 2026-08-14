"""LLMFailoverManager — automatic failover and circuit breaker engine for LLMs.

Intercepts provider execution errors (rate limit 429, API timeouts, 500 server errors)
and automatically re-routes requests through assigned backup failover model chains.
Trips provider circuit breakers after consecutive failures.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.orchestration.models.descriptor import ProviderHealthStatus
from core.orchestration.models.request import LLMRequest, LLMResponse
from core.orchestration.registry import LLMProviderRegistry
from infrastructure.logging.logger import StructuredLogger


class LLMFailoverManager:
    """Manages automatic LLM provider failover chains and circuit breakers."""

    def __init__(
        self,
        registry: Optional[LLMProviderRegistry] = None,
        circuit_breaker_threshold: int = 3,
    ) -> None:
        self.registry = registry or LLMProviderRegistry()
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self._logger = StructuredLogger("LLMFailoverManager")

        # Audit history
        self.failover_attempts: int = 0
        self.successful_failovers: int = 0

    def is_circuit_open(self, model_id: str) -> bool:
        """Return True if circuit breaker is open for a model ID."""
        desc = self.registry.get_descriptor(model_id)
        if not desc:
            return False
        return desc.health_status == ProviderHealthStatus.CIRCUIT_OPEN or desc.consecutive_failures >= self.circuit_breaker_threshold

    def execute_with_failover(
        self,
        request: LLMRequest,
        primary_model_id: str,
        fallback_chain: List[str],
        completion_runner: Callable[[str, LLMRequest], Tuple[str, int, int]],
    ) -> LLMResponse:
        """Execute completion request with automatic failover down the model chain.

        Args:
            request: The LLMRequest object.
            primary_model_id: Model ID selected by routing engine.
            fallback_chain: Ordered list of backup model IDs.
            completion_runner: Callable(model_id, request) -> (text_output, prompt_tokens, completion_tokens).

        Returns:
            LLMResponse detailing completion, model used, latency, cost, and failover chain.
        """
        candidate_models = [primary_model_id] + [m for m in fallback_chain if m != primary_model_id]

        last_error = ""
        used_chain: List[str] = []

        for idx, model_id in enumerate(candidate_models):
            used_chain.append(model_id)
            desc = self.registry.get_descriptor(model_id)

            # Check circuit breaker
            if self.is_circuit_open(model_id):
                self._logger.warning(
                    f"Circuit breaker OPEN for provider model '{model_id}' — skipping to next fallback"
                )
                self.failover_attempts += 1
                continue

            if idx > 0:
                self.failover_attempts += 1
                self._logger.info(
                    f"Executing FAILOVER provider model '{model_id}' for request '{request.request_id}' "
                    f"(primary '{primary_model_id}' failed: {last_error})"
                )

            start_time = time.perf_counter()
            try:
                text_out, prompt_toks, comp_toks = completion_runner(model_id, request)
                latency_ms = (time.perf_counter() - start_time) * 1000.0

                # Compute cost if descriptor exists
                in_cost = desc.input_cost_per_1k if desc else 0.0001
                out_cost = desc.output_cost_per_1k if desc else 0.0004
                total_cost = (prompt_toks / 1000.0 * in_cost) + (comp_toks / 1000.0 * out_cost)

                # Record success in registry
                self.registry.record_outcome(
                    model_id=model_id,
                    success=True,
                    latency_ms=latency_ms,
                    prompt_tokens=prompt_toks,
                    completion_tokens=comp_toks,
                )

                if idx > 0:
                    self.successful_failovers += 1

                provider_type = desc.provider_type if desc else None

                return LLMResponse(
                    request_id=request.request_id,
                    text=text_out,
                    model_id=model_id,
                    provider_type=provider_type,  # type: ignore[arg-type]
                    latency_ms=latency_ms,
                    prompt_tokens=prompt_toks,
                    completion_tokens=comp_toks,
                    total_cost=total_cost,
                    is_cached=False,
                    fallback_chain_used=used_chain if idx > 0 else [],
                )

            except Exception as e:
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                last_error = str(e)

                # Record failure in registry
                self.registry.record_outcome(
                    model_id=model_id,
                    success=False,
                    latency_ms=latency_ms,
                    error_message=last_error,
                )

                self._logger.warning(
                    f"Provider model '{model_id}' failed for request '{request.request_id}': {e}. "
                    f"Attempting failover..."
                )

        # All candidate models failed
        return LLMResponse(
            request_id=request.request_id,
            text="",
            model_id=primary_model_id,
            latency_ms=0.0,
            error_message=f"All models in failover chain failed. Last error: {last_error}",
            fallback_chain_used=used_chain,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return failover stats dict for telemetry."""
        return {
            "failover_attempts": self.failover_attempts,
            "successful_failovers": self.successful_failovers,
            "failover_success_rate_pct": (
                (self.successful_failovers / self.failover_attempts * 100.0)
                if self.failover_attempts > 0 else 100.0
            ),
        }
