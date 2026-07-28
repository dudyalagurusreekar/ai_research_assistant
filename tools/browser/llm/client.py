"""LLM Reasoning Client Layer (`tools/browser/llm/client.py`).

Provides a clean, stateless interface for LLM reasoning and structured JSON action generation.
Ensures strict separation of concerns: the LLM is responsible solely for reasoning
and action selection, with zero awareness of browser mechanics or DOM execution.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from utils.resilience import resilient_completion, AllModelsFailedError
from config.model import resolve_model_config

logger = logging.getLogger("LLMClient")


@dataclass
class LLMResponse:
    """Structured response from LLM reasoning."""

    content: str
    parsed_json: Optional[Dict[str, Any]] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    duration_ms: float = 0.0
    model: str = ""
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None and self.parsed_json is not None


class LLMClient:
    """Stateless LLM client for structured JSON reasoning and decision making.

    Handles prompt submission, JSON parsing, token accounting, and resilient
    fallback across models without coupling to browser execution.
    """

    def __init__(self, model: Optional[str] = None, max_tokens: int = 1500) -> None:
        """Initialize LLM Client.

        Args:
            model (Optional[str]): Target LLM model name.
            max_tokens (int): Maximum completion tokens to generate.
        """
        self.model = model or resolve_model_config()
        self.max_tokens = max_tokens
        self._logger = logger

    def generate_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
    ) -> LLMResponse:
        """Submit a prompt and parse the JSON output from the model.

        Args:
            messages: OpenAI-format messages list.
            temperature: Sampling temperature (default 0.1 for deterministic reasoning).

        Returns:
            LLMResponse containing parsed JSON action dictionary and token metrics.
        """
        start_time = time.time()
        try:
            resp = resilient_completion(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )
            duration_ms = (time.time() - start_time) * 1000.0

            content_str = resp.choices[0].message.content or "{}"
            usage = getattr(resp, "usage", None)
            prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
            completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
            total_tokens = getattr(usage, "total_tokens", 0) if usage else (prompt_tokens + completion_tokens)

            # Clean and parse JSON
            cleaned_json_str = self._clean_json_markdown(content_str)
            parsed = json.loads(cleaned_json_str)

            return LLMResponse(
                content=content_str,
                parsed_json=parsed,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                duration_ms=duration_ms,
                model=self.model,
            )

        except AllModelsFailedError as e:
            duration_ms = (time.time() - start_time) * 1000.0
            self._logger.error(f"All LLM models failed: {e}")
            return LLMResponse(
                content="",
                error=f"All models failed: {e}",
                duration_ms=duration_ms,
                model=self.model,
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000.0
            self._logger.error(f"LLM generation/parsing failed: {e}", exc_info=True)
            return LLMResponse(
                content="",
                error=str(e),
                duration_ms=duration_ms,
                model=self.model,
            )

    def _clean_json_markdown(self, raw: str) -> str:
        """Strip markdown code block fences if present around JSON."""
        cleaned = raw.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()
