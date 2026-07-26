"""Base Exception Hierarchy for the Core Foundation."""

from typing import Any, Dict, Optional
from core.exceptions.codes import ErrorCode


class CoreError(Exception):
    """Base exception class for all errors originating within the Core Foundation."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.context = context or {}
        self.cause = cause

    def to_dict(self) -> Dict[str, Any]:
        """Serialize error details for structured logging and API responses."""
        return {
            "error_code": self.code.value,
            "message": self.message,
            "context": self.context,
            "cause": str(self.cause) if self.cause else None,
        }

    def __str__(self) -> str:
        return f"[{self.code.value}] {self.message}"


class ValidationError(CoreError):
    """Raised when data input or configuration validation fails."""

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        super().__init__(message, code=ErrorCode.VALIDATION_ERROR, context=context, cause=cause)


class SessionError(CoreError):
    """Raised when session creation, lookup, state transition, or lifecycle fails."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.SESSION_EXECUTION_FAILED,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        super().__init__(message, code=code, context=context, cause=cause)


class CapabilityError(CoreError):
    """Raised when capability/tool registration, lookup, or validation fails."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.CAPABILITY_INVALID,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        super().__init__(message, code=code, context=context, cause=cause)


class RoutingError(CoreError):
    """Raised when capability routing resolution fails."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.ROUTING_FAILED,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        super().__init__(message, code=code, context=context, cause=cause)


class EventError(CoreError):
    """Raised when event publishing, subscription, or handler execution fails."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.EVENT_DISPATCH_FAILED,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        super().__init__(message, code=code, context=context, cause=cause)


class ConfigError(CoreError):
    """Raised when configuration loading or typed setting parsing fails."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.CONFIG_INVALID,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        super().__init__(message, code=code, context=context, cause=cause)


class DependencyError(CoreError):
    """Raised when dependency registration or resolution in IoC container fails."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.DEPENDENCY_RESOLUTION_FAILED,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        super().__init__(message, code=code, context=context, cause=cause)
