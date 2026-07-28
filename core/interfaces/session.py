"""Interface for session orchestrator/manager."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from core.models.session import Session, SessionState
from core.models.request import Request
from core.models.response import Response


class ISessionManager(ABC):
    """Abstract Interface for Session creation, tracking, and execution coordination."""

    @abstractmethod
    async def create_session(self, user_id: str, metadata: Optional[Dict] = None) -> Session:
        """Create a new session."""

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID."""

    @abstractmethod
    async def update_session_state(self, session_id: str, new_state: SessionState) -> Session:
        """Update session state."""

    @abstractmethod
    async def process_request(self, request: Request) -> Response:
        """Coordinate execution of a user request within its session context."""

    @abstractmethod
    def list_sessions(self, user_id: Optional[str] = None) -> List[Session]:
        """List active/archived sessions."""
