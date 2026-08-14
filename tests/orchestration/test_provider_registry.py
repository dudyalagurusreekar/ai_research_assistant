"""Tests for LLMProviderRegistry and LLMProviderDescriptor."""

import pytest
from core.orchestration.models.descriptor import (
    LLMProviderDescriptor,
    ModelTier,
    ProviderHealthStatus,
    ProviderType,
)
from core.orchestration.registry import DEFAULT_MODEL_DESCRIPTORS, LLMProviderRegistry


class TestLLMProviderDescriptor:
    def test_default_creation(self):
        desc = LLMProviderDescriptor(model_id="test/model")
        assert desc.model_id == "test/model"
        assert desc.reliability_score == 0.98
        assert desc.health_status == ProviderHealthStatus.HEALTHY
        assert desc.is_available() is True

    def test_record_success_updates_metrics(self):
        desc = LLMProviderDescriptor(model_id="test/model", reliability_score=0.90)
        desc.record_success(latency_ms=1000.0, tokens=500, cost=0.001)
        assert desc.total_requests == 1
        assert desc.successful_requests == 1
        assert desc.total_tokens_processed == 500
        assert desc.total_cost_accumulated == 0.001
        assert desc.reliability_score > 0.90

    def test_record_failure_degrades_health(self):
        desc = LLMProviderDescriptor(model_id="test/model", reliability_score=0.90)
        desc.record_failure("429 Rate Limit")
        assert desc.failed_requests == 1
        assert desc.consecutive_failures == 1
        assert desc.health_status == ProviderHealthStatus.DEGRADED

        desc.record_failure("429 Rate Limit")
        desc.record_failure("500 Server Error")
        assert desc.consecutive_failures == 3
        assert desc.health_status == ProviderHealthStatus.CIRCUIT_OPEN
        assert desc.is_available() is False

    def test_compute_routing_score(self):
        desc = LLMProviderDescriptor(
            model_id="gemini/gemini-2.5-flash",
            tier=ModelTier.BALANCED,
            reliability_score=0.98,
        )
        score = desc.compute_routing_score(target_tier=ModelTier.BALANCED, complexity_score=5)
        assert score > 0.5

    def test_to_dict(self):
        desc = LLMProviderDescriptor(model_id="gemini/gemini-2.5-flash")
        d = desc.to_dict()
        assert d["model_id"] == "gemini/gemini-2.5-flash"
        assert "reliability_score" in d


class TestLLMProviderRegistry:
    def setup_method(self):
        self.registry = LLMProviderRegistry()

    def test_defaults_loaded(self):
        descriptors = self.registry.list_descriptors()
        assert len(descriptors) >= len(DEFAULT_MODEL_DESCRIPTORS)
        model_ids = {d.model_id for d in descriptors}
        assert "gemini/gemini-2.5-flash" in model_ids
        assert "ollama/phi3:latest" in model_ids

    def test_get_descriptor(self):
        desc = self.registry.get_descriptor("gemini/gemini-2.5-flash")
        assert desc is not None
        assert desc.provider_type == ProviderType.CLOUD_GEMINI

    def test_filter_by_tier(self):
        routine_models = self.registry.filter_by_tier(ModelTier.ROUTINE)
        assert len(routine_models) >= 1
        assert any(m.provider_type == ProviderType.LOCAL for m in routine_models)

    def test_filter_by_provider_type(self):
        local_models = self.registry.filter_by_provider_type(ProviderType.LOCAL)
        assert len(local_models) >= 1
        assert all(m.provider_type == ProviderType.LOCAL for m in local_models)

    def test_record_outcome(self):
        self.registry.record_outcome(
            model_id="gemini/gemini-2.5-flash",
            success=True,
            latency_ms=800.0,
            prompt_tokens=100,
            completion_tokens=50,
        )
        desc = self.registry.get_descriptor("gemini/gemini-2.5-flash")
        assert desc.total_requests == 1
        assert desc.total_tokens_processed == 150

    def test_reset_circuit_breaker(self):
        self.registry.record_outcome("gemini/gemini-2.5-flash", success=False)
        self.registry.record_outcome("gemini/gemini-2.5-flash", success=False)
        self.registry.record_outcome("gemini/gemini-2.5-flash", success=False)
        assert self.registry.get_descriptor("gemini/gemini-2.5-flash").health_status == ProviderHealthStatus.CIRCUIT_OPEN

        self.registry.reset_circuit_breaker("gemini/gemini-2.5-flash")
        assert self.registry.get_descriptor("gemini/gemini-2.5-flash").health_status == ProviderHealthStatus.HEALTHY
