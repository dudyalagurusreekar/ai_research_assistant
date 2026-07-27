"""Exceptions for Document Intelligence Platform."""

from core.exceptions.base import CoreError
from core.exceptions.codes import ErrorCode


class DocumentError(CoreError):
    """Base exception for Document Intelligence Platform errors."""

    def __init__(self, message: str, code: ErrorCode = ErrorCode.UNKNOWN_ERROR, details: dict = None):
        super().__init__(message=message, code=code, context=details or {})


class ParserNotFoundError(DocumentError):
    """Raised when no parser can be found for a given document format."""

    def __init__(self, format_name: str):
        super().__init__(
            message=f"No document parser registered for format: '{format_name}'",
            code=ErrorCode.VALIDATION_ERROR,
            details={"format": format_name},
        )


class FormatDetectionError(DocumentError):
    """Raised when document format detection fails."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Failed to detect document format: {reason}",
            code=ErrorCode.VALIDATION_ERROR,
            details={"reason": reason},
        )


class DocumentParsingError(DocumentError):
    """Raised when document parsing fails."""

    def __init__(self, file_name: str, reason: str):
        super().__init__(
            message=f"Error parsing document '{file_name}': {reason}",
            code=ErrorCode.EXECUTION_FAILED,
            details={"file_name": file_name, "reason": reason},
        )


class PipelineExecutionError(DocumentError):
    """Raised when processing pipeline step execution fails."""

    def __init__(self, step_name: str, reason: str):
        super().__init__(
            message=f"Pipeline step '{step_name}' failed: {reason}",
            code=ErrorCode.EXECUTION_FAILED,
            details={"step": step_name, "reason": reason},
        )
