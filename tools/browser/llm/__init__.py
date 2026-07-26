"""LLM Layer (`tools/browser/llm/`).

Provides stateless LLM reasoning and structured JSON action generation, keeping
the LLM strictly isolated from browser mechanics.
"""

from tools.browser.llm.client import (
    LLMClient,
    LLMResponse,
)

__all__ = [
    "LLMClient",
    "LLMResponse",
]
