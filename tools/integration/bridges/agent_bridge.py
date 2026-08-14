"""Multi-Agent Framework Integration Bridge for Universal Connector Platform."""

from typing import Dict, Any, List, Optional
from infrastructure.logging.logger import StructuredLogger


class AgentConnectorBridge:
    """Enables multi-agent workflows to securely share connector credentials and delegate tasks."""

    def __init__(self, platform_engine: Optional[Any] = None) -> None:
        self._logger = StructuredLogger("AgentConnectorBridge")
        self._platform_engine = platform_engine
        self._agent_sessions: Dict[str, Dict[str, Any]] = {}

    def authorize_agent_session(self, agent_id: str, allowed_services: List[str]) -> Dict[str, Any]:
        """Grant multi-agent session access to designated service connectors."""
        self._agent_sessions[agent_id] = {
            "agent_id": agent_id,
            "allowed_services": [s.lower() for s in allowed_services],
            "is_active": True,
        }
        self._logger.info(f"Agent session authorized: agent={agent_id} services={allowed_services}")
        return self._agent_sessions[agent_id]

    def can_agent_access(self, agent_id: str, service_name: str) -> bool:
        """Check whether agent session has access to service connector."""
        session = self._agent_sessions.get(agent_id)
        if not session or not session["is_active"]:
            return False
        return "*" in session["allowed_services"] or service_name.lower() in session["allowed_services"]
