"""Tests for IntelligentLLMOrchestrator."""

import pytest
from core.orchestration.models.request import LLMRequest
from core.orchestration.orchestrator import IntelligentLLMOrchestrator


class TestIntelligentLLMOrchestrator:
    def setup_method(self):
        self.orchestrator = IntelligentLLMOrchestrator()

    def test_generate_simple_request(self):
        req = LLMRequest(prompt="Who wrote Hamlet?", complexity_score=2)
        runner = lambda mid, r: ("William Shakespeare wrote Hamlet.", 20, 10)

        res = self.orchestrator.generate(req, runner)
        assert res.text == "William Shakespeare wrote Hamlet."
        assert res.is_cached is False
        assert res.prompt_tokens == 20
        assert res.completion_tokens == 10

    def test_generate_response_caching(self):
        req = LLMRequest(prompt="Who wrote Hamlet?", complexity_score=2)
        runner = lambda mid, r: ("William Shakespeare wrote Hamlet.", 20, 10)

        # 1st call: miss & cache
        res1 = self.orchestrator.generate(req, runner)
        assert res1.is_cached is False

        # 2nd call: hit from cache!
        res2 = self.orchestrator.generate(req, runner)
        assert res2.is_cached is True
        assert res2.text == "William Shakespeare wrote Hamlet."
        assert res2.total_cost == 0.0

    def test_complete_for_agent(self):
        res = self.orchestrator.complete_for_agent("What is machine learning?")
        assert res.text != ""
        assert res.model_id != ""

    def test_get_telemetry_summary(self):
        telemetry = self.orchestrator.get_telemetry_summary()
        assert "registry" in telemetry
        assert "cache" in telemetry
        assert "failover" in telemetry
        assert "policy" in telemetry
