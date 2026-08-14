"""LLMRequest and LLMResponse data structures for ARA v2.0 LLM Orchestration Layer."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.orchestration.models.descriptor import ModelTier, ProviderType


@dataclass
class LLMRequest:
    """Input request structure passed to the Intelligent LLM Orchestrator."""

    request_id: str = field(default_factory=lambda: f"req_{uuid.uuid4().hex[:8]}")
    prompt: str = ""
    messages: List[Dict[str, str]] = field(default_factory=list)
    task_type: str = "general_qa"
    complexity_score: int = 5
    max_tokens: int = 2048
    temperature: float = 0.0
    latency_budget_ms: float = 12000.0
    preferred_tier: Optional[ModelTier] = None
    required_capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Output response structure returned by the Intelligent LLM Orchestrator."""

    response_id: str = field(default_factory=lambda: f"resp_{uuid.uuid4().hex[:8]}")
    request_id: str = ""
    text: str = ""
    model_id: str = ""
    provider_type: ProviderType = ProviderType.CLOUD_GEMINI
    latency_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_cost: float = 0.0
    is_cached: bool = False
    cache_key: Optional[str] = None
    fallback_chain_used: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def total_tokens(self) -> int:
        """Total token count for the request and completion."""
        return self.prompt_tokens + self.completion_tokens

    def to_dict(self) -> Dict[str, Any]:
        """Serialize response object to dict for logging and telemetry."""
        return {
            "response_id": self.response_id,
            "request_id": self.request_id,
            "model_id": self.model_id,
            "provider_type": self.provider_type.value,
            "latency_ms": round(self.latency_ms, 1),
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 6),
            "is_cached": self.is_cached,
            "fallback_chain_used": self.fallback_chain_used,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
        }
