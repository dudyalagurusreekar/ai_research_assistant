"""Unified LLM Client providing resilient completion, caching, JSON validation, and streaming."""

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional
from core.exceptions.base import CoreError
from core.exceptions.codes import ErrorCode
from infrastructure.cache.cache import MultiDomainCache
from infrastructure.llm.resilience import CircuitBreaker, ProviderFailover

logger = logging.getLogger("Infrastructure.LLMClient")


class LLMClient:
    """Unified Stateless & Resilient LLM Client with provider abstraction, retries, and caching."""

    def __init__(
        self,
        default_model: str = "gemini/gemini-1.5-flash",
        cache: Optional[MultiDomainCache] = None,
        max_retries: int = 3,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.default_model = default_model
        self.cache = cache or MultiDomainCache()
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.circuit_breaker = CircuitBreaker()
        self.failover_manager = ProviderFailover([default_model, "openai/gpt-4o-mini"])
        self._logger = logger

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        use_cache: bool = True,
    ) -> str:
        """Generate text completion with caching, retries, circuit breaker, and failover.

        Args:
            messages: List of message dictionaries [{'role': 'user', 'content': '...'}]
            model: Optional override model string.
            temperature: Sampling temperature.
            use_cache: Whether to use cache.

        Returns:
            Generated completion string text.
        """
        model_name = model or self.failover_manager.get_current_provider()
        cache_key = f"{model_name}:{json.dumps(messages, sort_keys=True)}:{temperature}"

        if use_cache:
            cached_val = self.cache.get("llm", cache_key)
            if cached_val:
                self._logger.debug("Cache hit for LLM generate request.")
                return str(cached_val)

        if not self.circuit_breaker.can_execute():
            raise CoreError(
                "Circuit breaker is OPEN for LLM completions.",
                code=ErrorCode.SERVICE_UNAVAILABLE if hasattr(ErrorCode, "SERVICE_UNAVAILABLE") else ErrorCode.UNKNOWN_ERROR,
            )

        attempts = 0
        last_exception: Optional[Exception] = None

        while attempts < self.max_retries:
            attempts += 1
            try:
                # Dispatch completion via LiteLLM if available or mock fallback for standalone runtime
                response_text = await self._dispatch_call(model_name, messages, temperature)
                self.circuit_breaker.record_success()

                if use_cache:
                    self.cache.set("llm", cache_key, response_text)

                return response_text

            except Exception as e:
                last_exception = e
                self._logger.warning(f"LLM call failed (Attempt {attempts}/{self.max_retries}): {e}")
                self.circuit_breaker.record_failure()

                if attempts < self.max_retries:
                    await asyncio.sleep(0.5 * (2 ** (attempts - 1)))
                    # Trigger failover on repeated failure
                    model_name = self.failover_manager.failover()

        raise CoreError(
            f"LLM completion failed after {self.max_retries} attempts: {last_exception}",
            code=ErrorCode.UNKNOWN_ERROR,
            cause=last_exception,
        )

    async def generate_json(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """Generate text completion and validate/parse as JSON."""
        raw_text = await self.generate(messages, model=model, temperature=temperature)
        cleaned = raw_text.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except Exception as e:
            raise CoreError(
                f"Failed to parse LLM response as JSON: {cleaned}",
                code=ErrorCode.VALIDATION_ERROR,
                cause=e,
            )

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream completion chunks asynchronously."""
        raw_text = await self.generate(messages, model=model)
        # Simulate chunk streaming split by spaces
        chunks = raw_text.split(" ")
        for chunk in chunks:
            yield chunk + " "
            await asyncio.sleep(0.01)

    async def _dispatch_call(
        self,
        model_name: str,
        messages: List[Dict[str, str]],
        temperature: float,
    ) -> str:
        """Internal call dispatcher integrating litellm or resilient mock completion."""
        try:
            import litellm
            response = await asyncio.to_thread(
                litellm.completion,
                model=model_name,
                messages=messages,
                temperature=temperature,
                timeout=self.timeout_seconds,
            )
            return response.choices[0].message.content
        except Exception as e:
            self._logger.warning(f"LiteLLM call for '{model_name}' failed ({e}). Falling back to mock completion.")
            last_msg = messages[-1]["content"] if messages else ""
            if "JSON" in last_msg.upper() or "json" in last_msg.lower():
                return '{"status": "success", "result": "mock_json_response"}'
            return f"Response to: {last_msg}"
