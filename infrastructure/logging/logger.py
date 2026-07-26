"""Structured JSON Logger with session, trace, and correlation ID support."""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from core.utils.time_utils import utc_isoformat


class JSONFormatter(logging.Formatter):
    """Formats log records as structured JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": utc_isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "session_id": getattr(record, "session_id", None),
            "trace_id": getattr(record, "trace_id", None),
            "correlation_id": getattr(record, "correlation_id", None),
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            log_entry["extra"] = record.extra_fields

        return json.dumps(log_entry)


class StructuredLogger:
    """Contextual structured logger providing session, trace, and correlation context."""

    def __init__(self, name: str, level: str = "INFO") -> None:
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        self._session_id: Optional[str] = None
        self._trace_id: Optional[str] = None
        self._correlation_id: Optional[str] = None

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(JSONFormatter())
            self.logger.addHandler(handler)

    def set_context(
        self,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Bind contextual identifiers to subsequent log outputs."""
        if session_id:
            self._session_id = session_id
        if trace_id:
            self._trace_id = trace_id
        if correlation_id:
            self._correlation_id = correlation_id

    def _log(self, level: int, msg: str, extra_fields: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        extra = {
            "session_id": kwargs.get("session_id", self._session_id),
            "trace_id": kwargs.get("trace_id", self._trace_id),
            "correlation_id": kwargs.get("correlation_id", self._correlation_id),
            "extra_fields": extra_fields or {},
        }
        self.logger.log(level, msg, extra=extra)

    def debug(self, msg: str, extra_fields: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        self._log(logging.DEBUG, msg, extra_fields, **kwargs)

    def info(self, msg: str, extra_fields: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        self._log(logging.INFO, msg, extra_fields, **kwargs)

    def warning(self, msg: str, extra_fields: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        self._log(logging.WARNING, msg, extra_fields, **kwargs)

    def error(self, msg: str, extra_fields: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, extra_fields, **kwargs)
