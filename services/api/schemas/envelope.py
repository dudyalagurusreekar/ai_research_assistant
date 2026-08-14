"""Standardized JSON Response Envelopes and Pagination Metadata Schemas."""

from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata model."""
    page: int = 1
    limit: int = 20
    total_items: int = 0
    total_pages: int = 0


class ErrorPayload(BaseModel):
    """Structured error payload."""
    code: str
    message: str
    details: Optional[Any] = None


class ResponseEnvelope(BaseModel, Generic[T]):
    """Standardized JSON API Response Envelope."""
    success: bool = True
    data: Optional[T] = None
    meta: Optional[PaginationMeta] = None
    error: Optional[ErrorPayload] = None
    correlation_id: Optional[str] = None

    @classmethod
    def success_response(
        cls,
        data: Any,
        meta: Optional[PaginationMeta] = None,
        correlation_id: Optional[str] = None,
    ) -> "ResponseEnvelope":
        return cls(
            success=True,
            data=data,
            meta=meta,
            error=None,
            correlation_id=correlation_id,
        )

    @classmethod
    def error_response(
        cls,
        code: str,
        message: str,
        details: Optional[Any] = None,
        correlation_id: Optional[str] = None,
    ) -> "ResponseEnvelope":
        return cls(
            success=False,
            data=None,
            meta=None,
            error=ErrorPayload(code=code, message=message, details=details),
            correlation_id=correlation_id,
        )
