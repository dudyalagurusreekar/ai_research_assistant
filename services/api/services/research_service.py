"""Clean Architecture Service for Research Sessions, Conversations, and Messages."""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from infrastructure.database.models.research import Conversation, Message, ResearchSession
from infrastructure.database.repositories.research_repository import ResearchSessionRepository


class ResearchService:
    """Business logic service for Research Sessions and Conversation Streams."""

    def __init__(self, db_session: Session):
        self.session = db_session
        self.repo = ResearchSessionRepository(db_session)

    def create_research_session(
        self,
        user_id: str,
        workspace_id: str,
        title: str,
        objective: str,
        settings_override: Optional[dict] = None,
    ) -> ResearchSession:
        """Create a new research session."""
        return self.repo.create({
            "user_id": user_id,
            "title": title,
            "goal": objective,
            "status": "active",
            "context_data": settings_override or {},
        })

    def list_user_sessions(self, user_id: str, skip: int = 0, limit: int = 20) -> Tuple[List[ResearchSession], int]:
        """List active research sessions for user."""
        sessions = self.session.query(ResearchSession).filter(ResearchSession.user_id == user_id).all()
        total = len(sessions)
        return sessions[skip : skip + limit], total

    def get_session_by_id(self, session_id: str, user_id: str) -> Optional[ResearchSession]:
        """Get research session by ID."""
        session_obj = self.session.query(ResearchSession).filter(ResearchSession.id == session_id, ResearchSession.user_id == user_id).first()
        return session_obj

    def create_conversation(self, session_id: str, user_id: str, title: str = "Main Thread") -> Optional[Conversation]:
        """Create conversation thread under a session."""
        session_obj = self.get_session_by_id(session_id, user_id)
        if not session_obj:
            return None
        
        conv = Conversation(
            session_id=session_id,
            title=title,
        )
        self.session.add(conv)
        self.session.commit()
        self.session.refresh(conv)
        return conv

    def add_message(
        self,
        conversation_id: str,
        sender_type: str,
        content: str,
        sender_id: Optional[str] = None,
        tool_calls: Optional[list] = None,
    ) -> Message:
        """Append a message to a conversation thread."""
        msg = Message(
            conversation_id=conversation_id,
            sender=sender_type,
            content=content,
            extra_metadata={"sender_id": sender_id, "tool_calls": tool_calls or []},
        )
        self.session.add(msg)
        self.session.commit()
        self.session.refresh(msg)
        return msg

    def list_messages(self, conversation_id: str) -> List[Message]:
        """Retrieve all messages in a conversation thread."""
        return self.session.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()
