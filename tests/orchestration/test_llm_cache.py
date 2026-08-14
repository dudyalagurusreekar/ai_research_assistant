"""Tests for LLMResponseCache."""

import pytest
import time
from core.orchestration.cache import LLMResponseCache
from core.orchestration.models.descriptor import ProviderType
from core.orchestration.models.request import LLMRequest, LLMResponse


class TestLLMResponseCache:
    def setup_method(self):
        self.cache = LLMResponseCache(default_ttl_seconds=10.0, max_size=5)

    def test_cache_miss(self):
        req = LLMRequest(prompt="What is quantum computing?", task_type="general_qa")
        res = self.cache.get(req)
        assert res is None
        assert self.cache.hits == 0
        assert self.cache.misses == 1

    def test_cache_put_and_hit(self):
        req = LLMRequest(prompt="What is quantum computing?", task_type="general_qa")
        resp = LLMResponse(
            request_id=req.request_id,
            text="Quantum computing utilizes qubits.",
            model_id="gemini/gemini-2.5-flash",
            provider_type=ProviderType.CLOUD_GEMINI,
            prompt_tokens=20,
            completion_tokens=30,
            total_cost=0.0001,
        )
        self.cache.put(request=req, response=resp)

        hit_resp = self.cache.get(req)
        assert hit_resp is not None
        assert hit_resp.is_cached is True
        assert hit_resp.text == "Quantum computing utilizes qubits."
        assert hit_resp.total_cost == 0.0
        assert hit_resp.latency_ms < 1.0
        assert self.cache.hits == 1
        assert self.cache.tokens_saved == 50

    def test_deterministic_cache_key(self):
        key1 = LLMResponseCache.compute_cache_key("prompt test", [], "qa", 0.0)
        key2 = LLMResponseCache.compute_cache_key("prompt test", [], "qa", 0.0)
        assert key1 == key2

    def test_ttl_expiration(self):
        cache = LLMResponseCache(default_ttl_seconds=0.1)
        req = LLMRequest(prompt="TTL test")
        resp = LLMResponse(text="Output", prompt_tokens=10, completion_tokens=10)
        cache.put(req, resp)

        time.sleep(0.15)
        res = cache.get(req)
        assert res is None

    def test_max_size_eviction(self):
        cache = LLMResponseCache(default_ttl_seconds=100.0, max_size=2)
        r1 = LLMRequest(prompt="q1")
        r2 = LLMRequest(prompt="q2")
        r3 = LLMRequest(prompt="q3")

        cache.put(r1, LLMResponse(text="out1"))
        time.sleep(0.01)
        cache.put(r2, LLMResponse(text="out2"))
        time.sleep(0.01)
        cache.put(r3, LLMResponse(text="out3"))  # evicts r1

        assert cache.get(r1) is None
        assert cache.get(r2) is not None
        assert cache.get(r3) is not None

    def test_invalidate(self):
        req = LLMRequest(prompt="q1")
        cache = LLMResponseCache()
        cache.put(req, LLMResponse(text="out1"))
        removed = cache.invalidate()
        assert removed == 1
        assert cache.get(req) is None

    def test_to_dict(self):
        req = LLMRequest(prompt="q1")
        self.cache.put(req, LLMResponse(text="out1", prompt_tokens=10, completion_tokens=10, total_cost=0.001))
        self.cache.get(req)
        d = self.cache.to_dict()
        assert d["hits"] == 1
        assert d["tokens_saved"] == 20
        assert "hit_rate_pct" in d
