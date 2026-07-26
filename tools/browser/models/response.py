"""Response Data Models for the Browser Tool.

This module defines DTOs representing lower-level fetch results, page metadata,
performance metrics, and unified browser response objects returned to agents.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import time

from tools.browser.constants import PageStatus


@dataclass
class PageMetadata:
    """Metadata describing a fetched/parsed web document.

    Attributes:
        title (str): HTML title tag content.
        description (Optional[str]): Meta description text.
        keywords (Optional[str]): Meta keywords content.
        canonical_url (Optional[str]): Canonical link tag URL.
        language (Optional[str]): Document html lang attribute.
        charset (str): Character set encoding (e.g. 'utf-8').
        og_type (Optional[str]): Open Graph og:type tag.
        open_graph (Dict[str, str]): Open Graph meta tags (og:title, og:image, etc.).
    """

    title: str = ""
    description: Optional[str] = None
    keywords: Optional[str] = None
    canonical_url: Optional[str] = None
    language: Optional[str] = None
    charset: str = "utf-8"
    og_type: Optional[str] = None
    open_graph: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Execution timing and payload metrics for telemetry and performance optimization.

    Attributes:
        fetch_duration_ms (float): Network fetch duration in milliseconds.
        parse_duration_ms (float): DOM parsing duration in milliseconds.
        total_duration_ms (float): Total processing time in milliseconds.
        content_length_bytes (int): Total size of raw HTTP response payload.
        redirect_count (int): Number of HTTP redirects followed.
    """

    fetch_duration_ms: float = 0.0
    parse_duration_ms: float = 0.0
    total_duration_ms: float = 0.0
    content_length_bytes: int = 0
    redirect_count: int = 0


@dataclass
class FetchResult:
    """Raw network fetch result returned by a BaseFetcher implementation.

    Attributes:
        url (str): Final resolved URL after any redirects.
        status_code (int): HTTP status code (e.g. 200, 404, 500).
        headers (Dict[str, str]): HTTP response headers.
        content (bytes): Raw unparsed binary/text payload body.
        encoding (str): Detected content character encoding.
        mime_type (str): Detected MIME content type (e.g. 'text/html').
        redirect_count (int): Number of HTTP redirects followed.
        response_time_ms (float): Fetch duration in milliseconds.
        success (bool): True if fetch completed with 2xx HTTP status.
        error_message (Optional[str]): Error description if fetch failed.
    """

    url: str
    status_code: int
    headers: Dict[str, str] = field(default_factory=dict)
    content: bytes = b""
    encoding: str = "utf-8"
    mime_type: str = "text/html"
    redirect_count: int = 0
    response_time_ms: float = 0.0
    success: bool = True
    error_message: Optional[str] = None

    @property
    def text(self) -> str:
        """Decode raw content bytes to string using detected encoding."""
        if not self.content:
            return ""
        try:
            return self.content.decode(self.encoding, errors="replace")
        except Exception:
            return self.content.decode("utf-8", errors="replace")


@dataclass
class BrowserResponse:
    """Unified high-level response object produced by the Browser orchestrator.

    Attributes:
        request_id (str): Matching request identifier.
        url (str): Target page URL.
        status (PageStatus): Page load lifecycle status.
        status_code (int): HTTP status code.
        metadata (PageMetadata): Extracted page metadata.
        extracted_text (str): Cleaned readable main text content.
        raw_html (Optional[str]): Raw HTML content string (if requested).
        metrics (PerformanceMetrics): Timing and size metrics.
        errors (List[str]): List of warning or error messages encountered.
        timestamp (float): UNIX timestamp when response was generated.
    """

    request_id: str
    url: str
    status: PageStatus = PageStatus.UNINITIALIZED
    status_code: int = 0
    metadata: PageMetadata = field(default_factory=PageMetadata)
    extracted_text: str = ""
    raw_html: Optional[str] = None
    metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    errors: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to a serializable dictionary format for agent tools."""
        return {
            "request_id": self.request_id,
            "url": self.url,
            "status": self.status.value,
            "status_code": self.status_code,
            "metadata": {
                "title": self.metadata.title,
                "description": self.metadata.description,
                "canonical_url": self.metadata.canonical_url,
                "language": self.metadata.language,
            },
            "extracted_text_preview": self.extracted_text[:200] if self.extracted_text else "",
            "content_length": len(self.extracted_text),
            "metrics": {
                "fetch_duration_ms": self.metrics.fetch_duration_ms,
                "parse_duration_ms": self.metrics.parse_duration_ms,
                "total_duration_ms": self.metrics.total_duration_ms,
            },
            "errors": self.errors,
            "timestamp": self.timestamp,
        }


@dataclass
class ActionMetrics:
    """Execution timing and telemetry for SDK actions."""
    execution_time_ms: float
    retries_attempted: int = 0
    timestamp: float = field(default_factory=time.time)
    validation_time_ms: float = 0.0
    execution_only_time_ms: float = 0.0
    wait_time_ms: float = 0.0
    verification_time_ms: float = 0.0


@dataclass
class ActionResult:
    """Structured result returned by every first-class action in the Browser Action Engine SDK."""
    success: bool
    url: str
    title: str
    action: str = ""
    data: Any = None
    verification: Optional[Dict[str, Any]] = None
    metrics: Optional[ActionMetrics] = None
    errors: List[str] = field(default_factory=list)
    console_logs: List[Dict[str, Any]] = field(default_factory=list)
    network_requests: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """Sanitize data and verification fields immediately upon creation to prevent object leaks."""
        from tools.browser.serializer import sanitize_payload
        self.data = sanitize_payload(self.data)
        if self.verification is not None:
            self.verification = sanitize_payload(self.verification)
        if self.errors:
            self.errors = sanitize_payload(self.errors)
        if self.console_logs:
            self.console_logs = sanitize_payload(self.console_logs)
        if self.network_requests:
            self.network_requests = sanitize_payload(self.network_requests)

    def to_dict(self) -> Dict[str, Any]:
        """Convert action result to dictionary representation with strict serialization."""
        from tools.browser.serializer import sanitize_payload

        return {
            "action": self.action,
            "success": self.success,
            "url": self.url,
            "title": self.title,
            "data": sanitize_payload(self.data),
            "verification": sanitize_payload(self.verification),
            "metrics": {
                "execution_time_ms": self.metrics.execution_time_ms if self.metrics else 0.0,
                "retries_attempted": self.metrics.retries_attempted if self.metrics else 0,
                "timestamp": self.metrics.timestamp if self.metrics else time.time(),
                "validation_time_ms": self.metrics.validation_time_ms if self.metrics else 0.0,
                "execution_only_time_ms": self.metrics.execution_only_time_ms if self.metrics else 0.0,
                "wait_time_ms": self.metrics.wait_time_ms if self.metrics else 0.0,
                "verification_time_ms": self.metrics.verification_time_ms if self.metrics else 0.0,
            } if self.metrics else None,
            "console_logs": sanitize_payload(self.console_logs),
            "network_requests": sanitize_payload(self.network_requests),
            "errors": sanitize_payload(self.errors),
        }

