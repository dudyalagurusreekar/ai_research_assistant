"""Data models for the External Integration Platform."""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from core.utils.id_generator import generate_id
from core.utils.time_utils import utc_now, utc_isoformat


class ProtocolType(str, Enum):
    """Supported external connectivity protocols."""
    REST = "rest"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"
    GRPC = "grpc"
    MCP = "mcp"


class AuthType(str, Enum):
    """Supported authentication schemes."""
    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC = "basic"
    OAUTH2 = "oauth2"
    JWT = "jwt"


@dataclass
class AuthenticationConfig:
    """Configuration container for external service authentication."""
    auth_type: AuthType = AuthType.NONE
    api_key: Optional[str] = None
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    header_name: str = "Authorization"
    header_prefix: str = "Bearer "
    extra_headers: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "auth_type": self.auth_type.value,
            "header_name": self.header_name,
            "header_prefix": self.header_prefix,
            "has_api_key": bool(self.api_key),
            "has_token": bool(self.token),
        }


@dataclass
class ConnectorMetadata:
    """Metadata describing a registered connector strategy."""
    connector_id: str = field(default_factory=lambda: generate_id("conn_"))
    name: str = ""
    protocol: ProtocolType = ProtocolType.REST
    base_url: str = ""
    is_active: bool = True
    health_status: str = "healthy"  # 'healthy', 'degraded', 'unhealthy'
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "connector_id": self.connector_id,
            "name": self.name,
            "protocol": self.protocol.value,
            "base_url": self.base_url,
            "is_active": self.is_active,
            "health_status": self.health_status,
            "description": self.description,
        }


@dataclass
class IntegrationRequest:
    """Model representing an outbound request to an external service."""
    request_id: str = field(default_factory=lambda: generate_id("req_"))
    connector_name: str = "rest"
    endpoint_or_tool: str = ""
    method: str = "GET"  # 'GET', 'POST', 'PUT', 'DELETE', 'QUERY', 'MUTATION', 'TOOL_CALL'
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    body: Optional[Any] = None
    auth_config: Optional[AuthenticationConfig] = None
    timeout_seconds: float = 10.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "connector_name": self.connector_name,
            "endpoint_or_tool": self.endpoint_or_tool,
            "method": self.method,
            "headers": self.headers,
            "params": self.params,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass
class IntegrationResponse:
    """Raw response returned from an external service connector."""
    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    data: Any = None
    error_message: Optional[str] = None
    response_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status_code": self.status_code,
            "headers": self.headers,
            "data": self.data,
            "error_message": self.error_message,
            "response_time_ms": self.response_time_ms,
        }


@dataclass
class IntegrationMetrics:
    """Telemetry metrics for external integration requests."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    active_connectors_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "avg_response_time_ms": self.avg_response_time_ms,
            "active_connectors_count": self.active_connectors_count,
        }


@dataclass
class NormalizedIntegrationResult:
    """Unified container model representing the result of an external integration invocation."""
    result_id: str = field(default_factory=lambda: generate_id("ires_"))
    connector_name: str = ""
    protocol: ProtocolType = ProtocolType.REST
    success: bool = True
    status_code: int = 200
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_isoformat)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "connector_name": self.connector_name,
            "protocol": self.protocol.value,
            "success": self.success,
            "status_code": self.status_code,
            "data": self.data,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }
