"""Execution result, cache entry, and fallback event data structures."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class ExecutionStatus(Enum):
    """Status of an executed task/tool call."""

    SUCCESS = "success"
    FAILURE = "failure"
    CACHED = "cached"
    DEGRADED = "degraded"
    SKIPPED = "skipped"


@dataclass
class ExecutionResult:
    """Outcome of a tool execution attempt."""

    result_id: str = field(default_factory=lambda: f"res_{uuid.uuid4().hex[:8]}")
    task_id: str = ""
    tool_name: str = ""
    action: str = ""
    status: ExecutionStatus = ExecutionStatus.SUCCESS
    output: Any = None
    latency_ms: float = 0.0
    is_cached: bool = False
    cache_key: Optional[str] = None
    fallback_used: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for logging and metrics export."""
        return {
            "result_id": self.result_id,
            "task_id": self.task_id,
            "tool_name": self.tool_name,
            "action": self.action,
            "status": self.status.value,
            "latency_ms": round(self.latency_ms, 2),
            "is_cached": self.is_cached,
            "fallback_used": self.fallback_used,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class CacheEntry:
    """Stored execution result in the ToolResultCache."""

    cache_key: str = ""
    tool_name: str = ""
    action: str = ""
    parameters_hash: str = ""
    output: Any = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl_seconds: float = 3600.0
    hit_count: int = 0

    def is_expired(self) -> bool:
        """Return True if the cache entry has exceeded its Time-To-Live."""
        delta = (datetime.now(timezone.utc) - self.created_at).total_seconds()
        return delta > self.ttl_seconds

    def touch(self) -> None:
        """Increment hit count on cache lookup."""
        self.hit_count += 1


@dataclass
class FallbackEvent:
    """Audit entry recording an automatic failover to a secondary tool."""

    event_id: str = field(default_factory=lambda: f"fbe_{uuid.uuid4().hex[:8]}")
    primary_tool: str = ""
    fallback_tool: str = ""
    task_id: str = ""
    reason: str = ""
    success: bool = True
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for audit logs."""
        return {
            "event_id": self.event_id,
            "primary_tool": self.primary_tool,
            "fallback_tool": self.fallback_tool,
            "task_id": self.task_id,
            "reason": self.reason,
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
        }
