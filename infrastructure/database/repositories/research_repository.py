"""Research Session, Conversation, and Message repository."""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from infrastructure.database.models.research import Conversation, Message, MessageAttachment, ResearchSession
from infrastructure.database.repositories.base import BaseRepository


class ResearchSessionRepository(BaseRepository[ResearchSession]):
    """Repository for managing research sessions and message context."""

    def __init__(self, session: Session):
        super().__init__(ResearchSession, session)

    def get_user_sessions(self, user_id: str, status: Optional[str] = None) -> List[ResearchSession]:
        """Fetch all research sessions for a user."""
        query = self.session.query(ResearchSession).filter(
            ResearchSession.user_id == user_id,
            ResearchSession.is_deleted.is_(False),
        )
        if status:
            query = query.filter(ResearchSession.status == status)
        return query.order_by(ResearchSession.created_at.desc()).all()

    def create_conversation(self, session_id: str, title: str, model_name: str = "gemini-2.5-pro") -> Conversation:
        """Create a new conversation thread."""
        conversation = Conversation(session_id=session_id, title=title, model_name=model_name)
        self.session.add(conversation)
        self.session.flush()
        return conversation

    def append_message(
        self,
        conversation_id: str,
        sender: str,
        content: str,
        token_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """Append a message to a conversation thread."""
        message = Message(
            conversation_id=conversation_id,
            sender=sender,
            content=content,
            token_count=token_count,
            extra_metadata=metadata or {},
        )
        self.session.add(message)
        self.session.flush()
        return message

    def get_conversation_messages(self, conversation_id: str, limit: int = 100) -> List[Message]:
        """Fetch all messages for a conversation ordered chronologically."""
        return (
            self.session.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .all()
        )
