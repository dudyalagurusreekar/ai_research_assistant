"""REST API Router for Research Sessions, Conversations, and Messages (/api/v1/research)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.auth.dependencies import get_current_user, get_db_session
from infrastructure.database.models.auth import User
from services.api.schemas.envelope import PaginationMeta, ResponseEnvelope
from services.api.services.research_service import ResearchService

router = APIRouter(prefix="", tags=["Research & Conversations"])


class CreateSessionRequest(BaseModel):
    workspace_id: str
    title: str
    objective: str
    settings: Optional[dict] = None


class CreateConversationRequest(BaseModel):
    title: Optional[str] = "Main Thread"


class AddMessageRequest(BaseModel):
    sender_type: str = "USER"  # USER, ASSISTANT, TOOL
    content: str
    tool_calls: Optional[list] = None


@router.post("/research/sessions", status_code=status.HTTP_201_CREATED)
def create_session(
    req: CreateSessionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Start a new research session."""
    service = ResearchService(db)
    session_obj = service.create_research_session(
        user_id=current_user.id,
        workspace_id=req.workspace_id,
        title=req.title,
        objective=req.objective,
        settings_override=req.settings,
    )
    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={
            "id": session_obj.id,
            "workspace_id": session_obj.project_id or req.workspace_id,
            "title": session_obj.title,
            "objective": session_obj.goal,
            "status": session_obj.status,
            "created_at": session_obj.created_at.isoformat() if session_obj.created_at else None,
        },
        correlation_id=correlation_id,
    )


@router.get("/research/sessions")
def list_sessions(
    page: int = 1,
    limit: int = 20,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """List active research sessions for current user."""
    service = ResearchService(db)
    skip = (page - 1) * limit
    sessions, total = service.list_user_sessions(current_user.id, skip=skip, limit=limit)

    meta = PaginationMeta(page=page, limit=limit, total_items=total, total_pages=(total + limit - 1) // limit if limit > 0 else 1)
    correlation_id = getattr(request.state, "correlation_id", None) if request else None

    data = [
        {
            "id": s.id,
            "workspace_id": s.project_id,
            "title": s.title,
            "objective": s.goal,
            "status": s.status,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in sessions
    ]
    return ResponseEnvelope.success_response(data=data, meta=meta, correlation_id=correlation_id)


@router.get("/research/sessions/{session_id}")
def get_session(
    session_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Get research session details."""
    service = ResearchService(db)
    session_obj = service.get_session_by_id(session_id, current_user.id)
    if not session_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session '{session_id}' not found.")

    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={
            "id": session_obj.id,
            "workspace_id": session_obj.project_id,
            "title": session_obj.title,
            "objective": session_obj.goal,
            "status": session_obj.status,
        },
        correlation_id=correlation_id,
    )


@router.post("/research/sessions/{session_id}/conversations", status_code=status.HTTP_201_CREATED)
def create_conversation(
    session_id: str,
    req: CreateConversationRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Create conversation thread under session."""
    service = ResearchService(db)
    conv = service.create_conversation(session_id, current_user.id, title=req.title or "Main Thread")
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session '{session_id}' not found.")

    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={"id": conv.id, "research_session_id": conv.session_id, "title": conv.title},
        correlation_id=correlation_id,
    )


@router.post("/conversations/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
def add_message(
    conversation_id: str,
    req: AddMessageRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Append chat or tool message to conversation thread."""
    service = ResearchService(db)
    msg = service.add_message(
        conversation_id=conversation_id,
        sender_type=req.sender_type,
        content=req.content,
        sender_id=current_user.id,
        tool_calls=req.tool_calls,
    )
    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "sender_type": msg.sender,
            "content": msg.content,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        },
        correlation_id=correlation_id,
    )


@router.get("/conversations/{conversation_id}/messages")
def list_messages(
    conversation_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """List all messages in a conversation thread."""
    service = ResearchService(db)
    messages = service.list_messages(conversation_id)
    correlation_id = getattr(request.state, "correlation_id", None)
    data = [
        {
            "id": m.id,
            "conversation_id": m.conversation_id,
            "sender_type": m.sender,
            "content": m.content,
            "tool_calls": m.extra_metadata.get("tool_calls", []) if m.extra_metadata else [],
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]
    return ResponseEnvelope.success_response(data=data, correlation_id=correlation_id)

