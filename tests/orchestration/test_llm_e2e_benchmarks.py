"""End-to-end benchmark tests for Sprint 3 Intelligent LLM Orchestration Layer."""

import pytest
from core.orchestration.models.descriptor import ProviderType
from core.orchestration.models.request import LLMRequest
from core.orchestration.orchestrator import IntelligentLLMOrchestrator


class TestLLMOrchestrationE2E:
    def setup_method(self):
        self.orchestrator = IntelligentLLMOrchestrator()

    def test_e2e_routine_task_local_offload(self):
        req = LLMRequest(
            prompt="Generate a quick 3-step checklist for researching quantum physics",
            task_type="routine_plan",
            complexity_score=2,
        )
        runner = lambda mid, r: ("1. Search papers\n2. Compare models\n3. Write report", 30, 20)

        res = self.orchestrator.generate(req, runner)
        assert res.provider_type == ProviderType.LOCAL
        assert res.total_cost == 0.0

    def test_e2e_complex_reasoning_task_cloud_routing(self):
        req = LLMRequest(
            prompt="Perform multi-source comparative analysis of transformer models",
            task_type="complex_analysis",
            complexity_score=8,
        )
        runner = lambda mid, r: ("Comprehensive comparative report...", 200, 150)

        res = self.orchestrator.generate(req, runner)
        assert res.provider_type != ProviderType.LOCAL
        assert res.total_cost > 0.0

    def test_e2e_cache_deduplication_saves_cost(self):
        req = LLMRequest(prompt="What is the speed of light?", complexity_score=2)
        runner = lambda mid, r: ("299,792,458 m/s", 15, 10)

        res1 = self.orchestrator.generate(req, runner)
        assert res1.is_cached is False

        res2 = self.orchestrator.generate(req, runner)
        assert res2.is_cached is True
        assert res2.total_cost == 0.0
        assert self.orchestrator.cache.tokens_saved >= 25

    def test_e2e_failover_on_cloud_429(self):
        def failing_runner(mid, r):
            if mid == "gemini/gemini-2.5-flash":
                raise RuntimeError("429 Resource Exhausted")
            return ("Fallback answer", 20, 10)

        req = LLMRequest(prompt="Standard research query", complexity_score=5)
        res = self.orchestrator.generate(req, failing_runner)

        assert res.model_id != "gemini/gemini-2.5-flash"
        assert res.text == "Fallback answer"
        assert len(res.fallback_chain_used) >= 2
