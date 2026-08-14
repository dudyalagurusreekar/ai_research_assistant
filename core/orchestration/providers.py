"""LLM Provider Dispatcher for Google Gemini 2.5, OpenAI, Anthropic, and Local LLMs."""

import time
from typing import Dict, Any, Tuple, Optional
from core.orchestration.models.request import LLMRequest
from utils.logger import get_logger

logger = get_logger("LLMProviderDispatcher")


class LLMProviderDispatcher:
    """Dispatches generation requests to underlying LLM APIs or mock fallbacks."""

    @staticmethod
    def run_completion(model_id: str, request: LLMRequest) -> Tuple[str, int, int]:
        """Execute text completion for specified model.

        Returns: (completion_text, prompt_tokens, completion_tokens)
        """
        logger.info(f"Dispatching LLM request (id={request.request_id}) to model '{model_id}'")
        
        # Simulate realistic token counts and text output
        prompt_len = len(request.prompt)
        prompt_tokens = max(12, prompt_len // 4)
        completion_tokens = 120

        if "gemini-2.5-pro" in model_id:
            output_text = (
                f"[Google Gemini 2.5 Pro] Detailed analytical response for task '{request.task_type}' "
                f"(Complexity: {request.complexity_score}/10). Goal resolved with deep reasoning trace."
            )
        elif "gemini-2.5-flash" in model_id:
            output_text = (
                f"[Google Gemini 2.5 Flash] Fast response for task '{request.task_type}'. "
                f"Summary: {request.prompt[:60]}..."
            )
        elif "claude" in model_id:
            output_text = (
                f"[Anthropic Claude 3.5 Sonnet] Structured response for query '{request.prompt[:50]}...'"
            )
        elif "gpt-4" in model_id or "openai" in model_id:
            output_text = (
                f"[OpenAI GPT-4o] High-precision output for task '{request.task_type}'."
            )
        else:
            output_text = (
                f"[{model_id}] Generated completion response for prompt."
            )

        return output_text, prompt_tokens, completion_tokens
