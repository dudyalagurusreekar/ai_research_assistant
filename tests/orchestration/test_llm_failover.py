"""Tests for LLMFailoverManager."""

import pytest
from core.orchestration.failover import LLMFailoverManager
from core.orchestration.models.descriptor import ProviderHealthStatus
from core.orchestration.models.request import LLMRequest
from core.orchestration.registry import LLMProviderRegistry


class TestLLMFailoverManager:
    def setup_method(self):
        self.registry = LLMProviderRegistry()
        self.failover = LLMFailoverManager(registry=self.registry, circuit_breaker_threshold=3)

    def test_primary_model_success(self):
        req = LLMRequest(prompt="Test prompt")
        runner = lambda mid, r: (f"Success from {mid}", 50, 20)

        res = self.failover.execute_with_failover(
            request=req,
            primary_model_id="gemini/gemini-2.5-flash",
            fallback_chain=["openai/gpt-4o-mini"],
            completion_runner=runner,
        )
        assert res.model_id == "gemini/gemini-2.5-flash"
        assert res.text == "Success from gemini/gemini-2.5-flash"
        assert res.error_message is None
        assert res.fallback_chain_used == []

    def test_primary_fails_fallback_succeeds(self):
        def runner(mid, r):
            if mid == "gemini/gemini-2.5-flash":
                raise RuntimeError("429 Rate Limit Exceeded")
            return (f"Fallback output from {mid}", 40, 20)

        req = LLMRequest(prompt="Test prompt")
        res = self.failover.execute_with_failover(
            request=req,
            primary_model_id="gemini/gemini-2.5-flash",
            fallback_chain=["openai/gpt-4o-mini", "ollama/phi3:latest"],
            completion_runner=runner,
        )
        assert res.model_id == "openai/gpt-4o-mini"
        assert "Fallback output" in res.text
        assert len(res.fallback_chain_used) == 2
        assert self.failover.successful_failovers == 1

    def test_all_models_fail(self):
        def runner(mid, r):
            raise RuntimeError(f"500 Error on {mid}")

        req = LLMRequest(prompt="Test prompt")
        res = self.failover.execute_with_failover(
            request=req,
            primary_model_id="gemini/gemini-2.5-flash",
            fallback_chain=["openai/gpt-4o-mini"],
            completion_runner=runner,
        )
        assert res.error_message is not None
        assert "All models in failover chain failed" in res.error_message

    def test_circuit_breaker_trips(self):
        def runner(mid, r):
            raise RuntimeError("API Outage")

        req = LLMRequest(prompt="Test prompt")

        # 3 failures trip circuit breaker
        for i in range(3):
            self.failover.execute_with_failover(
                req, "gemini/gemini-2.5-flash", ["openai/gpt-4o-mini"], runner
            )

        assert self.failover.is_circuit_open("gemini/gemini-2.5-flash") is True
        desc = self.registry.get_descriptor("gemini/gemini-2.5-flash")
        assert desc.health_status == ProviderHealthStatus.CIRCUIT_OPEN
