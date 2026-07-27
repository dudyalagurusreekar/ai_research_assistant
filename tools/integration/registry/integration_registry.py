"""Integration Registry managing dynamic connector strategies."""

from typing import Dict, List, Optional
from tools.integration.interfaces.integration_interfaces import IConnector, IIntegrationRegistry
from tools.integration.models.integration_models import ConnectorMetadata
from infrastructure.logging.logger import StructuredLogger


class IntegrationRegistry(IIntegrationRegistry):
    """Registry maintaining mappings between connector names and concrete IConnector strategy instances."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("IntegrationRegistry")
        self._connectors: Dict[str, IConnector] = {}

    def register(self, connector: IConnector) -> None:
        """Register a connector strategy."""
        name = connector.connector_name.lower()
        self._connectors[name] = connector
        self._logger.debug(f"Registered external connector '{connector.connector_name}' (protocol={connector.protocol.value})")

    def get_connector(self, name: str) -> Optional[IConnector]:
        """Retrieve registered connector strategy by name."""
        return self._connectors.get(name.lower())

    def list_connectors(self) -> List[ConnectorMetadata]:
        """List metadata for registered connectors."""
        items = []
        for name, conn in self._connectors.items():
            items.append(
                ConnectorMetadata(
                    name=conn.connector_name,
                    protocol=conn.protocol,
                    is_active=True,
                    health_status="healthy",
                )
            )
        return items
