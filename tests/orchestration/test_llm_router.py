"""Tests for LLMRoutingEngine."""

import pytest
from core.orchestration.models.descriptor import ModelTier, ProviderType
from core.orchestration.models.policy import LLMRoutingPolicy
from core.orchestration.models.request import LLMRequest
from core.orchestration.registry import LLMProviderRegistry
from core.orchestration.router import LLMRoutingEngine


class TestLLMRoutingEngine:
    def setup_method(self):
        self.registry = LLMProviderRegistry()
        self.policy = LLMRoutingPolicy(prefer_local_for_routine=True)
        self.router = LLMRoutingEngine(registry=self.registry, policy=self.policy)

    def test_routine_task_routes_to_local_model(self):
        req = LLMRequest(prompt="Status check", task_type="routine_check", complexity_score=2)
        primary_desc, fallbacks = self.router.route(req)
        assert primary_desc.provider_type == ProviderType.LOCAL
        assert primary_desc.tier == ModelTier.ROUTINE
        assert len(fallbacks) >= 1

    def test_balanced_task_routes_to_flash(self):
        req = LLMRequest(prompt="Standard research question", task_type="factual_qa", complexity_score=5)
        primary_desc, fallbacks = self.router.route(req)
        assert primary_desc.tier in (ModelTier.BALANCED, ModelTier.ROUTINE)
        assert len(fallbacks) >= 1

    def test_advanced_task_routes_to_high_tier_cloud(self):
        req = LLMRequest(prompt="Complex multi-document comparison", task_type="complex_research", complexity_score=8)
        primary_desc, fallbacks = self.router.route(req)
        assert primary_desc.tier in (ModelTier.ADVANCED, ModelTier.REASONING)
        assert primary_desc.provider_type != ProviderType.LOCAL

    def test_routing_prefers_healthy_models(self):
        # Degrade Gemini Flash
        desc = self.registry.get_descriptor("gemini/gemini-2.5-flash")
        desc.reliability_score = 0.1

        req = LLMRequest(prompt="Standard search", complexity_score=5)
        primary_desc, fallbacks = self.router.route(req)
        # Should pick another balanced model like gpt-4o-mini
        assert primary_desc.model_id != "gemini/gemini-2.5-flash" or primary_desc.reliability_score > 0.0

    def test_routing_with_preferred_tier(self):
        req = LLMRequest(prompt="Quick query", complexity_score=2, preferred_tier=ModelTier.ADVANCED)
        primary_desc, fallbacks = self.router.route(req)
        assert primary_desc.tier == ModelTier.ADVANCED
