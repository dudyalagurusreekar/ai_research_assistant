"""ConnectorManager for dynamic loading, lifecycle, and circuit breaking."""

from typing import Dict, Any, Optional, List
import time

from tools.integration.sdk.base_connector import BaseConnector
from tools.integration.models.integration_models import (
    ConnectorMetadata,
    IntegrationRequest,
    NormalizedIntegrationResult,
)
from infrastructure.logging.logger import StructuredLogger


class CircuitBreakerOpenException(Exception):
    """Raised when request is rejected due to open circuit breaker."""
    pass


class CircuitBreaker:
    """Circuit breaker monitoring failure rates per connector."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = "CLOSED"  # 'CLOSED', 'OPEN', 'HALF_OPEN'
        self.last_state_change = time.time()

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_state_change = time.time()

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.last_state_change = time.time()

    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_state_change > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        return True


class ConnectorManager:
    """Manages connector registry, dynamic loading, health monitoring, and circuit breaking."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("ConnectorManager")
        self._connectors: Dict[str, BaseConnector] = {}
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}

    def register_connector(self, connector: BaseConnector) -> None:
        """Register connector strategy instance."""
        name = connector.connector_name.lower()
        self._connectors[name] = connector
        self._circuit_breakers[name] = CircuitBreaker()
        self._logger.info(f"Registered connector '{connector.connector_name}' (protocol={connector.protocol.value})")

    def unregister_connector(self, name: str) -> bool:
        """Remove connector by name."""
        name = name.lower()
        if name in self._connectors:
            del self._connectors[name]
            del self._circuit_breakers[name]
            return True
        return False

    def get_connector(self, name: str) -> Optional[BaseConnector]:
        """Retrieve registered connector instance."""
        return self._connectors.get(name.lower())

    def list_connectors(self) -> List[ConnectorMetadata]:
        """List metadata for all registered connectors."""
        return [c.metadata for c in self._connectors.values()]

    async def initialize_all(self, configs: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        """Initialize all registered connectors."""
        configs = configs or {}
        for name, conn in self._connectors.items():
            cfg = configs.get(name)
            await conn.initialize(cfg)

    async def check_all_health(self) -> Dict[str, ConnectorMetadata]:
        """Check health status across all registered connectors."""
        statuses = {}
        for name, conn in self._connectors.items():
            statuses[name] = await conn.check_health()
        return statuses

    async def execute_request(self, request: IntegrationRequest) -> NormalizedIntegrationResult:
        """Execute request using targeted connector with circuit breaking."""
        name = request.connector_name.lower()
        conn = self._connectors.get(name)
        if not conn:
            return NormalizedIntegrationResult(
                connector_name=request.connector_name,
                success=False,
                status_code=404,
                error=f"Connector '{request.connector_name}' is not registered.",
            )

        cb = self._circuit_breakers[name]
        if not cb.can_execute():
            return NormalizedIntegrationResult(
                connector_name=name,
                success=False,
                status_code=503,
                error=f"Circuit breaker is OPEN for connector '{name}'",
            )

        try:
            res = await conn.execute_normalized(request)
            if res.success:
                cb.record_success()
            else:
                cb.record_failure()
            return res
        except Exception as e:
            cb.record_failure()
            return NormalizedIntegrationResult(
                connector_name=name,
                success=False,
                status_code=500,
                error=str(e),
            )
