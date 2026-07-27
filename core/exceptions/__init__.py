"""Exceptions package for the Core Foundation."""

from core.exceptions.codes import ErrorCode
from core.exceptions.base import (
    CoreError,
    ValidationError,
    SessionError,
    CapabilityError,
    RoutingError,
    EventError,
    ConfigError,
    DependencyError,
)

__all__ = [
    "ErrorCode",
    "CoreError",
    "ValidationError",
    "SessionError",
    "CapabilityError",
    "RoutingError",
    "EventError",
    "ConfigError",
    "DependencyError",
]
