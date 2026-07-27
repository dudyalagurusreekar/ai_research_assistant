"""Unit tests for LLM Client and Resilience."""

import unittest
from infrastructure.llm import LLMClient, CircuitBreaker, CircuitState, ProviderFailover


class TestLLMClient(unittest.IsolatedAsyncioTestCase):
    """Test resilient LLM completions, circuit breaker, and JSON validation."""

    def test_circuit_breaker(self):
        cb = CircuitBreaker(failure_threshold=2)
        self.assertTrue(cb.can_execute())

        cb.record_failure()
        self.assertTrue(cb.can_execute())

        cb.record_failure()
        self.assertFalse(cb.can_execute())
        self.assertEqual(cb.state, CircuitState.OPEN)

    def test_provider_failover(self):
        pf = ProviderFailover(["p1", "p2"])
        self.assertEqual(pf.get_current_provider(), "p1")
        self.assertEqual(pf.failover(), "p2")

    async def test_llm_client_generate_json(self):
        client = LLMClient()
        res = await client.generate_json([{"role": "user", "content": "Return JSON"}])
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("status"), "success")


if __name__ == "__main__":
    unittest.main()
