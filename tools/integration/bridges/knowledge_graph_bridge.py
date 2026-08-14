"""Knowledge Graph Integration Bridge for Universal Connector Platform."""

from typing import Dict, Any, List, Optional
from infrastructure.logging.logger import StructuredLogger


class KnowledgeGraphConnectorBridge:
    """Ingests external entities, files, issues, emails, and pages into Knowledge Graph."""

    def __init__(self, platform_engine: Optional[Any] = None) -> None:
        self._logger = StructuredLogger("KnowledgeGraphConnectorBridge")
        self._platform_engine = platform_engine
        self._nodes: List[Dict[str, Any]] = []
        self._edges: List[Dict[str, Any]] = []

    def ingest_entity(
        self,
        service_name: str,
        entity_type: str,
        entity_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Convert external entity to Knowledge Graph node and semantic edge."""
        entity_id = entity_data.get("id") or entity_data.get("key") or "entity_unknown"
        node_id = f"kg_{service_name}_{entity_id}"

        node = {
            "node_id": node_id,
            "label": str(entity_data.get("name") or entity_data.get("subject") or entity_data.get("title") or entity_id),
            "type": entity_type,
            "domain": service_name,
            "properties": entity_data,
        }
        self._nodes.append(node)

        edge = {
            "source": f"connector_{service_name}",
            "target": node_id,
            "relation": "PROVIDES_ENTITY",
        }
        self._edges.append(edge)

        self._logger.info(f"Ingested Knowledge Graph node '{node_id}' from service '{service_name}'")
        return {"node": node, "edge": edge}

    def get_graph_summary(self) -> Dict[str, Any]:
        """Return total ingested nodes and edges count."""
        return {"nodes_count": len(self._nodes), "edges_count": len(self._edges)}
