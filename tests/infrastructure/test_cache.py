"""Unit tests for Multi-Domain Cache."""

import time
import unittest
from infrastructure.cache import MultiDomainCache


class TestMultiDomainCache(unittest.TestCase):
    """Test multi-domain caching, TTL expiration, and hit rates."""

    def test_cache_set_get_ttl(self):
        cache = MultiDomainCache(default_ttl_seconds=1.0)
        cache.set("llm", "key1", "val1")

        self.assertEqual(cache.get("llm", "key1"), "val1")
        self.assertGreater(cache.get_hit_rate(), 0.0)

        # Test expiration
        time.sleep(1.1)
        self.assertIsNone(cache.get("llm", "key1"))


if __name__ == "__main__":
    unittest.main()
