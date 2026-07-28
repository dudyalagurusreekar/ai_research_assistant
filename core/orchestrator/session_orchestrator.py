"""Session Orchestrator for managing session lifecycles and coordinating execution workflows."""

import logging
from typing import Dict, List, Optional
from core.interfaces.session import ISessionManager
from core.interfaces.event_bus import IEventBus
from core.interfaces.registry import IRegistry
from core.interfaces.router import IRouter
from core.models.session import Session, SessionState
from core.models.request import Request
from core.models.response import Response, ResponseStatus
from core.models.event import Event
from core.exceptions.base import SessionError
from core.exceptions.codes import ErrorCode
from core.utils.time_utils import utc_now
from core.orchestrator.recovery_engine import GlobalRecoveryEngine

logger = logging.getLogger("Core.SessionOrchestrator")


class SessionOrchestrator(ISessionManager):
    """Coordinates session creation, lifecycle tracking, event notification, and request processing."""

    def __init__(
        self,
        event_bus: Optional[IEventBus] = None,
        registry: Optional[IRegistry] = None,
        router: Optional[IRouter] = None,
    ) -> None:
        self._sessions: Dict[str, Session] = {}
        self._event_bus = event_bus
        self._registry = registry
        self._router = router
        self._logger = logger
        self._recovery_engine = GlobalRecoveryEngine()

    async def create_session(self, user_id: str, metadata: Optional[Dict] = None) -> Session:
        """Create a new session and publish session.created event.

        Args:
            user_id: Owner user identifier.
            metadata: Optional initial metadata dictionary.

        Returns:
            Newly created Session instance.
        """
        if not user_id:
            raise SessionError("user_id must be provided to create a session.", code=ErrorCode.INVALID_REQUEST)

        session = Session(user_id=user_id, metadata=metadata or {})
        self._sessions[session.session_id] = session
        self._logger.info(f"Created session '{session.session_id}' for user '{user_id}'.")

        if self._event_bus:
            await self._event_bus.publish(
                Event(
                    event_type="session.created",
                    source="SessionOrchestrator",
                    payload=session.to_dict(),
                )
            )

        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve an active or archived session by ID."""
        return self._sessions.get(session_id)

    async def update_session_state(self, session_id: str, new_state: SessionState) -> Session:
        """Update session lifecycle state and publish session.state_changed event.

        Args:
            session_id: Target session ID.
            new_state: Target SessionState enum value.

        Returns:
            Updated Session instance.
        """
        session = self.get_session(session_id)
        if not session:
            raise SessionError(
                f"Session '{session_id}' not found.",
                code=ErrorCode.SESSION_NOT_FOUND,
                context={"session_id": session_id},
            )

        old_state = session.state
        session.update_state(new_state)
        self._logger.info(f"Session '{session_id}' state changed: {old_state.value} -> {new_state.value}.")

        if self._event_bus:
            await self._event_bus.publish(
                Event(
                    event_type="session.state_changed",
                    source="SessionOrchestrator",
                    payload={
                        "session_id": session_id,
                        "old_state": old_state.value,
                        "new_state": new_state.value,
                        "updated_at": session.updated_at.isoformat(),
                    },
                )
            )

        return session

    async def process_request(self, request: Request) -> Response:
        """Coordinate execution of a request within its session context.

        Args:
            request: Unified request object.

        Returns:
            Structured Response object.
        """
        session = self.get_session(request.session_id)
        if not session:
            raise SessionError(
                f"Session '{request.session_id}' not found for request '{request.request_id}'.",
                code=ErrorCode.SESSION_NOT_FOUND,
                context={"session_id": request.session_id, "request_id": request.request_id},
            )

        if session.state in (SessionState.TERMINATED, SessionState.FAILED):
            raise SessionError(
                f"Cannot process request in session state '{session.state.value}'.",
                code=ErrorCode.SESSION_STATE_INVALID,
                context={"session_id": request.session_id, "state": session.state.value},
            )

        await self.update_session_state(session.session_id, SessionState.RUNNING)

        try:
            # Route request if router is provided
            tool_result_data = None
            artifacts = []

            if self._router:
                decision = self._router.route(request)
                if decision and self._registry:
                    tool = self._registry.get_tool(decision.tool_name)
                    if tool:
                        result = await self._recovery_engine.execute_with_recovery(
                            tool_name=decision.tool_name,
                            func=tool.execute,
                            parameters=request.parameters,
                            session_id=session.session_id
                        )
                        tool_result_data = result.to_dict()
                        artifacts = result.artifacts

            response = Response(
                request_id=request.request_id,
                session_id=request.session_id,
                status=ResponseStatus.SUCCESS,
                data=tool_result_data or {"message": "Request processed successfully.", "intent": request.intent},
                artifacts=artifacts,
                timestamp=utc_now(),
            )

            await self.update_session_state(session.session_id, SessionState.COMPLETED)

            if self._event_bus:
                await self._event_bus.publish(
                    Event(
                        event_type="request.processed",
                        source="SessionOrchestrator",
                        payload=response.to_dict(),
                    )
                )

            return response

        except Exception as e:
            await self.update_session_state(session.session_id, SessionState.FAILED)
            self._logger.error(f"Error processing request '{request.request_id}': {e}", exc_info=True)
            return Response(
                request_id=request.request_id,
                session_id=request.session_id,
                status=ResponseStatus.FAILURE,
                error={"message": str(e), "type": type(e).__name__},
                timestamp=utc_now(),
            )

    def list_sessions(self, user_id: Optional[str] = None) -> List[Session]:
        """List active or user-filtered sessions."""
        if user_id:
            return [s for s in self._sessions.values() if s.user_id == user_id]
        return list(self._sessions.values())
