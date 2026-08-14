"""DatabaseConnector base class for relational and NoSQL database integrations."""

from abc import abstractmethod
from typing import Dict, Any, Optional, List

from tools.integration.sdk.base_connector import BaseConnector
from tools.integration.models.integration_models import (
    ProtocolType,
    IntegrationRequest,
    IntegrationResponse,
)


class DatabaseConnector(BaseConnector):
    """Specialized BaseConnector for database connections (PostgreSQL, MySQL, SQLite, MongoDB)."""

    def __init__(
        self,
        name: str = "database",
        connection_string: str = "",
        db_type: str = "sqlite",
        description: str = "Database connector for SQL/NoSQL queries",
    ) -> None:
        super().__init__(name=name, protocol=ProtocolType.REST, base_url="", description=description)
        self._connection_string = connection_string
        self._db_type = db_type
        self._connection_pool_size = 5
        self._active_connections = 0

    @property
    def db_type(self) -> str:
        """Type of target database engine."""
        return self._db_type

    @abstractmethod
    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Execute parameterized query against database."""
        pass

    @abstractmethod
    async def inspect_schema(self) -> Dict[str, Any]:
        """Inspect database schema, listing tables, views, and column definitions."""
        pass

    async def execute(self, request: IntegrationRequest) -> IntegrationResponse:
        """Route database query request."""
        query = request.params.get("query", request.endpoint_or_tool)
        params = request.params.get("parameters", {})
        limit = request.params.get("limit", 100)
        offset = request.params.get("offset", 0)

        if request.method == "INSPECT_SCHEMA":
            schema_data = await self.inspect_schema()
            return IntegrationResponse(status_code=200, data=schema_data)

        rows = await self.execute_query(query=query, parameters=params, limit=limit, offset=offset)
        return IntegrationResponse(
            status_code=200,
            data={"rows": rows, "count": len(rows), "limit": limit, "offset": offset},
        )
