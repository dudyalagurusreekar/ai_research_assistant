"""Global Exception Handlers for FastAPI returning standardized JSON response envelopes."""

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from services.api.schemas.envelope import ResponseEnvelope
from utils.logger import get_logger

logger = get_logger("GlobalExceptionHandler")


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    envelope = ResponseEnvelope.error_response(
        code=f"HTTP_{exc.status_code}",
        message=str(exc.detail),
        correlation_id=correlation_id,
    )
    return JSONResponse(status_code=exc.status_code, content=envelope.model_dump())


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    envelope = ResponseEnvelope.error_response(
        code="VALIDATION_ERROR",
        message="Request payload validation failed",
        details=exc.errors(),
        correlation_id=correlation_id,
    )
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=envelope.model_dump())


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    envelope = ResponseEnvelope.error_response(
        code="BAD_REQUEST",
        message=str(exc),
        correlation_id=correlation_id,
    )
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=envelope.model_dump())


async def permission_error_handler(request: Request, exc: PermissionError) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    envelope = ResponseEnvelope.error_response(
        code="FORBIDDEN",
        message=str(exc),
        correlation_id=correlation_id,
    )
    return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content=envelope.model_dump())


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    logger.exception(f"Unhandled Internal Error: {exc}")
    envelope = ResponseEnvelope.error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected internal server error occurred.",
        correlation_id=correlation_id,
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=envelope.model_dump())
