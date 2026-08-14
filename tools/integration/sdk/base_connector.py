"""BaseConnector abstract class for Sprint 12 Universal Connector SDK."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import time

from tools.integration.interfaces.integration_interfaces import IConnector
from tools.integration.models.integration_models import (
    ProtocolType,
    ConnectorMetadata,
    IntegrationRequest,
    IntegrationResponse,
    NormalizedIntegrationResult,
)
from infrastructure.logging.logger import StructuredLogger


class BaseConnector(IConnector):
    """Abstract base class for all Sprint 12 Universal Service Connectors."""

    def __init__(
        self,
        name: str,
        protocol: ProtocolType = ProtocolType.REST,
        base_url: str = "",
        description: str = "",
    ) -> None:
        self._name = name
        self._protocol = protocol
        self._base_url = base_url
        self._description = description
        self._logger = StructuredLogger(f"Connector[{name}]")
        self._is_initialized = False
        self._health_status = "healthy"
        self._rate_limit_per_minute = 600
        self._request_timestamps: List[float] = []

    @property
    def connector_name(self) -> str:
        """Unique identifier name of the connector."""
        return self._name

    @property
    def protocol(self) -> ProtocolType:
        """Protocol type used by connector."""
        return self._protocol

    @property
    def metadata(self) -> ConnectorMetadata:
        """Return ConnectorMetadata object."""
        return ConnectorMetadata(
            name=self._name,
            protocol=self._protocol,
            base_url=self._base_url,
            is_active=self._is_initialized,
            health_status=self._health_status,
            description=self._description,
        )

    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize connector resources and configuration."""
        self._is_initialized = True
        self._logger.info(f"Connector '{self._name}' initialized successfully.")
        return True

    async def shutdown(self) -> bool:
        """Release connector connections and resources."""
        self._is_initialized = False
        self._logger.info(f"Connector '{self._name}' shut down cleanly.")
        return True

    async def check_health(self) -> ConnectorMetadata:
        """Verify health status of connector target endpoint."""
        meta = self.metadata
        meta.is_active = self._is_initialized
        meta.health_status = self._health_status
        return meta

    def get_supported_actions(self) -> List[str]:
        """Return list of supported high-level action names."""
        return ["query", "execute", "health", "sync"]

    def get_schema(self) -> Dict[str, Any]:
        """Return connector action schemas and parameter definitions."""
        return {
            "name": self._name,
            "protocol": self._protocol.value,
            "actions": self.get_supported_actions(),
        }

    def _check_rate_limit(self) -> bool:
        """Enforce rate limits per minute."""
        now = time.time()
        self._request_timestamps = [t for t in self._request_timestamps if now - t < 60.0]
        if len(self._request_timestamps) >= self._rate_limit_per_minute:
            return False
        self._request_timestamps.append(now)
        return True

    @abstractmethod
    async def execute(self, request: IntegrationRequest) -> IntegrationResponse:
        """Execute request against target service."""
        pass

    async def execute_normalized(self, request: IntegrationRequest) -> NormalizedIntegrationResult:
        """Execute request and return normalized integration result."""
        start_time = time.time()
        if not self._check_rate_limit():
            return NormalizedIntegrationResult(
                connector_name=self._name,
                protocol=self._protocol,
                success=False,
                status_code=429,
                error="Rate limit exceeded for connector",
                execution_time_ms=(time.time() - start_time) * 1000.0,
            )

        try:
            resp = await self.execute(request)
            exec_time = (time.time() - start_time) * 1000.0
            return NormalizedIntegrationResult(
                connector_name=self._name,
                protocol=self._protocol,
                success=resp.status_code < 400 and resp.error_message is None,
                status_code=resp.status_code,
                data=resp.data,
                error=resp.error_message,
                execution_time_ms=exec_time,
                metadata={"headers": resp.headers},
            )
        except Exception as e:
            exec_time = (time.time() - start_time) * 1000.0
            self._logger.error(f"Error executing request on '{self._name}': {e}")
            return NormalizedIntegrationResult(
                connector_name=self._name,
                protocol=self._protocol,
                success=False,
                status_code=500,
                error=str(e),
                execution_time_ms=exec_time,
            )
