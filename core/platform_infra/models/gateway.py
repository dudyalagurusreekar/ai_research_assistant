"""Gateway models — API Gateway routing, request validation, and rate limiting."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class RateLimitPolicy:
    """Sliding window rate limit policy."""

    max_requests_per_minute: int = 120
    max_requests_per_hour: int = 5000


@dataclass
class RouteConfig:
    """Gateway route specification."""

    path_pattern: str
    target_handler: str
    require_auth: bool = True
    required_permission: str = "read"
    rate_limit_policy: RateLimitPolicy = field(default_factory=RateLimitPolicy)


@dataclass
class APIRequest:
    """Inbound API Request model."""

    path: str
    method: str = "POST"
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    body: Dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: f"req_{uuid.uuid4().hex[:8]}")
    client_ip: str = "127.0.0.1"


@dataclass
class APIResponse:
    """Outbound API Response model."""

    status_code: int = 200
    data: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    error_message: Optional[str] = None
    request_id: str = ""

    @classmethod
    def success(cls, data: Dict[str, Any], request_id: str = "") -> APIResponse:
        return cls(status_code=200, data=data, request_id=request_id)

    @classmethod
    def error(cls, message: str, status_code: int = 400, request_id: str = "") -> APIResponse:
        return cls(status_code=status_code, error_message=message, request_id=request_id)
