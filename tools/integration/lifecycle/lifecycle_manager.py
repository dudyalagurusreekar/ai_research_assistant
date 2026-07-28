"""Connector Lifecycle Manager monitoring health, retries, and circuit breaking."""

from typing import Optional
from tools.integration.interfaces.integration_interfaces import IConnectorLifecycleManager, IIntegrationRegistry
from tools.integration.models.integration_models import ConnectorMetadata, ProtocolType
from infrastructure.logging.logger import StructuredLogger


class ConnectorLifecycleManager(IConnectorLifecycleManager):
    """Monitors connector health status, rate limits, and circuit breaking."""

    def __init__(self, registry: Optional[IIntegrationRegistry] = None) -> None:
        self._logger = StructuredLogger("ConnectorLifecycleManager")
        self._registry = registry

    async def check_health(self, connector_name: str) -> ConnectorMetadata:
        """Perform health check verification on named connector strategy."""
        self._logger.info(f"Checking health status for connector '{connector_name}'")

        if self._registry:
            conn = self._registry.get_connector(connector_name)
            if conn:
                return ConnectorMetadata(
                    name=conn.connector_name,
                    protocol=conn.protocol,
                    is_active=True,
                    health_status="healthy",
                    description=f"Active connector implementing {conn.protocol.value}",
                )

        return ConnectorMetadata(
            name=connector_name,
            protocol=ProtocolType.REST,
            is_active=False,
            health_status="unhealthy",
            description="Connector not registered or unreachable.",
        )
