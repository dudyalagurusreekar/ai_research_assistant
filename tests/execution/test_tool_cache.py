"""Tests for ToolResultCache and CacheEntry."""

import pytest
import time
from core.execution.cache import ToolResultCache
from core.execution.models.result import ExecutionStatus


class TestToolResultCache:
    def setup_method(self):
        self.cache = ToolResultCache(default_ttl_seconds=10.0, max_size=5)

    def test_cache_miss_initially(self):
        res = self.cache.get("search_tool", "search", {"query": "AI research"})
        assert res is None
        assert self.cache.hits == 0
        assert self.cache.misses == 1

    def test_cache_put_and_hit(self):
        self.cache.put("search_tool", "search", {"query": "AI research"}, "Output 123")
        res = self.cache.get("search_tool", "search", {"query": "AI research"}, estimated_latency_ms=1500.0)
        assert res is not None
        assert res.status == ExecutionStatus.CACHED
        assert res.output == "Output 123"
        assert res.is_cached is True
        assert self.cache.hits == 1
        assert self.cache.hit_rate == 100.0  # 1 hit out of 1 lookup
        assert self.cache.estimated_latency_saved_ms == 1500.0

    def test_deterministic_key(self):
        key1 = ToolResultCache.compute_cache_key("search_tool", "search", {"b": 2, "a": 1})
        key2 = ToolResultCache.compute_cache_key("search_tool", "search", {"a": 1, "b": 2})
        assert key1 == key2

    def test_ttl_expiration(self):
        cache = ToolResultCache(default_ttl_seconds=0.1)
        cache.put("search_tool", "search", {"q": "test"}, "output")
        time.sleep(0.15)
        res = cache.get("search_tool", "search", {"q": "test"})
        assert res is None

    def test_max_size_eviction(self):
        cache = ToolResultCache(default_ttl_seconds=100.0, max_size=2)
        cache.put("t1", "a", {"q": "1"}, "out1")
        time.sleep(0.01)
        cache.put("t2", "a", {"q": "2"}, "out2")
        time.sleep(0.01)
        cache.put("t3", "a", {"q": "3"}, "out3")  # should evict oldest (t1)

        assert cache.get("t1", "a", {"q": "1"}) is None
        assert cache.get("t2", "a", {"q": "2"}) is not None
        assert cache.get("t3", "a", {"q": "3"}) is not None

    def test_invalidate_by_tool(self):
        self.cache.put("search_tool", "search", {"q": "1"}, "out1")
        self.cache.put("browser_tool", "browse", {"q": "2"}, "out2")
        removed = self.cache.invalidate("search_tool")
        assert removed == 1
        assert self.cache.get("search_tool", "search", {"q": "1"}) is None
        assert self.cache.get("browser_tool", "browse", {"q": "2"}) is not None

    def test_invalidate_all(self):
        self.cache.put("t1", "a", {"q": "1"}, "out1")
        self.cache.put("t2", "a", {"q": "2"}, "out2")
        removed = self.cache.invalidate()
        assert removed == 2

    def test_to_dict(self):
        self.cache.put("t1", "a", {"q": "1"}, "out1")
        d = self.cache.to_dict()
        assert d["total_entries"] == 1
        assert "hit_rate_pct" in d
