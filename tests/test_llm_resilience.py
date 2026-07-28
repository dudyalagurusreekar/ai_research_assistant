"""Unit tests for the LLM resilience framework."""

import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add workspace root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import litellm
from utils.resilience import (
    resilient_completion,
    AllModelsFailedError,
    circuit_breaker,
    request_cache,
)


class TestLLMResilience(unittest.TestCase):
    """Test suite covering retry, circuit breaking, failover, and metrics logging."""

    def setUp(self) -> None:
        # Clear health registry state and cache before each test
        circuit_breaker.healths.clear()
        request_cache.cache.clear()
        request_cache.save()
        
        # Enable cloud provider keys in mock environment
        self.env_patcher = patch.dict(
            "os.environ",
            {
                "MODEL_NAME": "gemini/gemini-2.5-flash",
                "FALLBACK_MODELS": "gemini/gemini-2.5-flash,openai/gpt-4o-mini,ollama_chat/phi3:latest",
                "GEMINI_API_KEY": "mock_gemini_key",
                "OPENAI_API_KEY": "mock_openai_key",
                "MODEL_NUM_RETRIES": "2",
            },
        )
        self.env_patcher.start()

    def tearDown(self) -> None:
        self.env_patcher.stop()

    @patch("time.sleep")
    @patch("litellm.completion")
    def test_http_429_rate_limit(self, mock_completion, mock_sleep) -> None:
        """Should retry on HTTP 429 and eventually succeed if the API recovers."""
        # Mock 429 on first call, success on second
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Success response"
        mock_response.usage = MagicMock()

        mock_completion.side_effect = [
            litellm.exceptions.RateLimitError(message="Rate limit hit (429)", response=MagicMock(), llm_provider="gemini", model="gemini-2.5-flash"),
            mock_response,
        ]

        messages = [{"role": "user", "content": "hello"}]
        res = resilient_completion(model="gemini/gemini-2.5-flash", messages=messages)

        self.assertEqual(res.choices[0].message.content, "Success response")
        self.assertEqual(mock_completion.call_count, 2)
        mock_sleep.assert_called_once()  # Backoff sleep was triggered

    @patch("time.sleep")
    @patch("litellm.completion")
    def test_daily_quota_exceeded(self, mock_completion, mock_sleep) -> None:
        """Should classify quota exceeded as non-retryable and trigger immediate failover."""
        # Fail Gemini with Quota Exceeded immediately, then OpenAI succeeds
        openai_response = MagicMock()
        openai_response.choices = [MagicMock()]
        openai_response.choices[0].message.content = "OpenAI response"
        openai_response.usage = MagicMock()

        mock_completion.side_effect = [
            litellm.exceptions.RateLimitError(message="Daily quota exceeded", response=MagicMock(), llm_provider="gemini", model="gemini-2.5-flash"),
            openai_response,
        ]

        messages = [{"role": "user", "content": "hello"}]
        res = resilient_completion(model="gemini/gemini-2.5-flash", messages=messages)

        self.assertEqual(res.choices[0].message.content, "OpenAI response")
        # Should call Gemini once (no retries because it's non-retryable), then OpenAI once
        self.assertEqual(mock_completion.call_count, 2)
        mock_sleep.assert_not_called()  # No backoff delay since it was a permanent error
        
        # Verify Gemini circuit breaker is tripped (OPEN)
        health = circuit_breaker.get_status("gemini/gemini-2.5-flash")
        self.assertEqual(health["status"], "OPEN")

    @patch("time.sleep")
    @patch("litellm.completion")
    def test_api_timeout(self, mock_completion, mock_sleep) -> None:
        """Should retry on Timeout and succeed if the timeout clears."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Recovery after timeout"
        mock_response.usage = MagicMock()

        mock_completion.side_effect = [
            litellm.exceptions.Timeout(message="Gateway timeout", model="gemini-2.5-flash", llm_provider="gemini"),
            mock_response,
        ]

        messages = [{"role": "user", "content": "hello"}]
        res = resilient_completion(model="gemini/gemini-2.5-flash", messages=messages)

        self.assertEqual(res.choices[0].message.content, "Recovery after timeout")
        self.assertEqual(mock_completion.call_count, 2)
        mock_sleep.assert_called_once()

    @patch("time.sleep")
    @patch("litellm.completion")
    def test_connection_reset(self, mock_completion, mock_sleep) -> None:
        """Should retry on connection failures and succeed on retry."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Recovery after connection failure"
        mock_response.usage = MagicMock()

        mock_completion.side_effect = [
            litellm.exceptions.APIConnectionError(message="Connection reset by peer", llm_provider="gemini", model="gemini-2.5-flash"),
            mock_response,
        ]

        messages = [{"role": "user", "content": "hello"}]
        res = resilient_completion(model="gemini/gemini-2.5-flash", messages=messages)

        self.assertEqual(res.choices[0].message.content, "Recovery after connection failure")
        self.assertEqual(mock_completion.call_count, 2)
        mock_sleep.assert_called_once()

    @patch("time.sleep")
    @patch("litellm.completion")
    def test_provider_unavailable(self, mock_completion, mock_sleep) -> None:
        """Should retry on provider temporary unavailability (ServiceUnavailableError / 503)."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Recovery after 503"
        mock_response.usage = MagicMock()

        mock_completion.side_effect = [
            litellm.exceptions.ServiceUnavailableError(message="Service overloaded (503)", llm_provider="gemini", model="gemini-2.5-flash"),
            mock_response,
        ]

        messages = [{"role": "user", "content": "hello"}]
        res = resilient_completion(model="gemini/gemini-2.5-flash", messages=messages)

        self.assertEqual(res.choices[0].message.content, "Recovery after 503")
        self.assertEqual(mock_completion.call_count, 2)
        mock_sleep.assert_called_once()

    @patch("time.sleep")
    @patch("litellm.completion")
    def test_successful_provider_failover(self, mock_completion, mock_sleep) -> None:
        """Should failover to secondary provider when primary retries are fully exhausted."""
        openai_response = MagicMock()
        openai_response.choices = [MagicMock()]
        openai_response.choices[0].message.content = "Resolved via OpenAI failover"
        openai_response.usage = MagicMock()

        # Fail Gemini 3 times (1 initial + 2 retries), then succeed on OpenAI
        mock_completion.side_effect = [
            litellm.exceptions.Timeout(message="Gemini Timeout", model="gemini-2.5-flash", llm_provider="gemini"),
            litellm.exceptions.Timeout(message="Gemini Timeout", model="gemini-2.5-flash", llm_provider="gemini"),
            litellm.exceptions.Timeout(message="Gemini Timeout", model="gemini-2.5-flash", llm_provider="gemini"),
            openai_response,
        ]

        messages = [{"role": "user", "content": "hello"}]
        res = resilient_completion(model="gemini/gemini-2.5-flash", messages=messages)

        self.assertEqual(res.choices[0].message.content, "Resolved via OpenAI failover")
        # 3 calls to Gemini, 1 to OpenAI
        self.assertEqual(mock_completion.call_count, 4)

        # Verify Gemini is now marked as OPEN (unhealthy)
        health = circuit_breaker.get_status("gemini/gemini-2.5-flash")
        self.assertEqual(health["status"], "OPEN")

    @patch("time.sleep")
    @patch("litellm.completion")
    def test_retry_exhaustion_raises_all_models_failed(self, mock_completion, mock_sleep) -> None:
        """Should raise AllModelsFailedError when all fallback providers are exhausted."""
        # Fail every model request
        mock_completion.side_effect = litellm.exceptions.Timeout(message="Timeout error", model="gemini-2.5-flash", llm_provider="gemini")

        messages = [{"role": "user", "content": "hello"}]
        
        with self.assertRaises(AllModelsFailedError):
            resilient_completion(model="gemini/gemini-2.5-flash", messages=messages)

        # Gemini: 3 attempts, OpenAI: 3 attempts, Ollama: 3 attempts. Total: 9
        self.assertEqual(mock_completion.call_count, 9)


if __name__ == "__main__":
    unittest.main()
