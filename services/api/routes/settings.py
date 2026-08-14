"""REST API Router for System and User Settings (/api/v1/settings)."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.auth.dependencies import get_current_user, get_db_session
from infrastructure.database.models.auth import User
from services.api.schemas.envelope import ResponseEnvelope
from services.api.services.setting_service import UserSettingService

router = APIRouter(prefix="/settings", tags=["Settings & Preferences"])


class UpdatePreferencesRequest(BaseModel):
    preferences: dict


@router.get("/system")
def get_system_settings(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Retrieve platform system settings."""
    service = UserSettingService(db)
    system_settings = service.get_system_settings()
    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(data=system_settings, correlation_id=correlation_id)


@router.get("/user")
def get_user_preferences(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Retrieve user custom preferences."""
    service = UserSettingService(db)
    prefs = service.get_user_preferences(current_user.id)
    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(data=prefs, correlation_id=correlation_id)


@router.patch("/user")
def update_user_preferences(
    req: UpdatePreferencesRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Update user custom preferences."""
    service = UserSettingService(db)
    updated = service.update_user_preferences(current_user.id, req.preferences)
    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(data=updated, correlation_id=correlation_id)
