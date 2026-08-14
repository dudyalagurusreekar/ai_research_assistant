"""IntelligentLLMOrchestrator — unified LLM orchestration engine for ARA v2.0.

Provides provider-agnostic LLM generation, dynamic complexity-driven routing,
prompt response caching, automatic failover chains, cost tracking, and telemetry export.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

from core.orchestration.cache import LLMResponseCache
from core.orchestration.failover import LLMFailoverManager
from core.orchestration.models.policy import LLMRoutingPolicy
from core.orchestration.models.request import LLMRequest, LLMResponse
from core.orchestration.registry import LLMProviderRegistry
from core.orchestration.router import LLMRoutingEngine
from infrastructure.logging.logger import StructuredLogger


from core.orchestration.providers import LLMProviderDispatcher


class IntelligentLLMOrchestrator:
    """Production LLM orchestrator coordinating routing, caching, and failover."""

    def __init__(
        self,
        registry: Optional[LLMProviderRegistry] = None,
        cache: Optional[LLMResponseCache] = None,
        router: Optional[LLMRoutingEngine] = None,
        failover_manager: Optional[LLMFailoverManager] = None,
        policy: Optional[LLMRoutingPolicy] = None,
    ) -> None:
        self.policy = policy or LLMRoutingPolicy()
        self.registry = registry or LLMProviderRegistry()
        self.cache = cache or LLMResponseCache(default_ttl_seconds=self.policy.default_ttl_seconds)
        self.router = router or LLMRoutingEngine(registry=self.registry, policy=self.policy)
        self.failover_manager = failover_manager or LLMFailoverManager(
            registry=self.registry,
            circuit_breaker_threshold=self.policy.circuit_breaker_threshold,
        )
        self._logger = StructuredLogger("IntelligentLLMOrchestrator")

    def generate(
        self,
        request: LLMRequest,
        completion_runner: Optional[Callable[[str, LLMRequest], Tuple[str, int, int]]] = None,
    ) -> LLMResponse:
        """Execute LLM generation with routing, caching, and failover.

        Args:
            request: Target LLMRequest.
            completion_runner: Optional Callable(model_id, request) -> (text_out, prompt_tokens, completion_tokens).

        Returns:
            Fully populated LLMResponse object.
        """
        runner = completion_runner or LLMProviderDispatcher.run_completion

        # 1. Check prompt response cache if enabled
        if self.policy.enable_response_caching:
            cached_resp = self.cache.get(request)
            if cached_resp:
                return cached_resp

        # 2. Dynamically route request to optimal model & fallback chain
        primary_desc, fallback_chain = self.router.route(request)

        # 3. Execute with automatic failover if enabled
        if self.policy.enable_fallback_chain:
            response = self.failover_manager.execute_with_failover(
                request=request,
                primary_model_id=primary_desc.model_id,
                fallback_chain=fallback_chain,
                completion_runner=runner,
            )
        else:
            # Direct execution without fallback
            import time
            start = time.perf_counter()
            try:
                text_out, p_toks, c_toks = runner(primary_desc.model_id, request)

                lat = (time.perf_counter() - start) * 1000.0
                cost = (p_toks / 1000.0 * primary_desc.input_cost_per_1k) + (c_toks / 1000.0 * primary_desc.output_cost_per_1k)
                self.registry.record_outcome(primary_desc.model_id, success=True, latency_ms=lat, prompt_tokens=p_toks, completion_tokens=c_toks)
                response = LLMResponse(
                    request_id=request.request_id,
                    text=text_out,
                    model_id=primary_desc.model_id,
                    provider_type=primary_desc.provider_type,
                    latency_ms=lat,
                    prompt_tokens=p_toks,
                    completion_tokens=c_toks,
                    total_cost=cost,
                )
            except Exception as e:
                lat = (time.perf_counter() - start) * 1000.0
                self.registry.record_outcome(primary_desc.model_id, success=False, latency_ms=lat, error_message=str(e))
                response = LLMResponse(
                    request_id=request.request_id,
                    text="",
                    model_id=primary_desc.model_id,
                    provider_type=primary_desc.provider_type,
                    error_message=str(e),
                )

        # 4. Cache response on success
        if response.text and not response.error_message and self.policy.enable_response_caching:
            self.cache.put(request, response)

        return response

    def complete_for_agent(
        self,
        prompt: str,
        task_type: str = "general_qa",
        complexity_score: int = 5,
        completion_runner: Optional[Callable[[str, LLMRequest], Tuple[str, int, int]]] = None,
    ) -> LLMResponse:
        """Convenience helper method for agents to request LLM completion."""
        req = LLMRequest(
            prompt=prompt,
            task_type=task_type,
            complexity_score=complexity_score,
        )
        runner = completion_runner or self._default_mock_runner
        return self.generate(req, runner)

    @staticmethod
    def _default_mock_runner(model_id: str, request: LLMRequest) -> Tuple[str, int, int]:
        """Default completion runner for dry-run/testing."""
        prompt_len = len(request.prompt)
        prompt_tokens = max(10, prompt_len // 4)
        completion_tokens = 50
        return f"[Response from {model_id}] Answer to: {request.prompt[:50]}...", prompt_tokens, completion_tokens

    def get_telemetry_summary(self) -> Dict[str, Any]:
        """Return unified LLM orchestration telemetry summary."""
        return {
            "registry": self.registry.to_dict(),
            "cache": self.cache.to_dict(),
            "failover": self.failover_manager.to_dict(),
            "policy": self.policy.to_dict(),
        }
