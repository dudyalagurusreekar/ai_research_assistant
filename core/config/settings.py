"""Typed Configuration Objects for the Core Foundation."""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class EventConfig:
    """Configuration for Event Bus infrastructure."""

    max_queue_size: int = 1000
    dispatch_timeout_seconds: float = 30.0
    enable_async_execution: bool = True


@dataclass
class SessionConfig:
    """Configuration for Session management."""

    default_timeout_seconds: float = 3600.0
    max_concurrent_sessions: int = 50
    session_cleanup_interval_seconds: float = 300.0


@dataclass
class AppConfig:
    """Root Application Configuration container."""

    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    events: EventConfig = field(default_factory=EventConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    custom: Dict[str, Any] = field(default_factory=dict)
