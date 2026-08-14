"""FastAPI Router for User Profile and Administration endpoints (/api/v1/users)."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.auth.dependencies import get_current_user, get_db_session, require_roles
from core.auth.rbac import RoleEnum
from core.auth.service import AuthService
from infrastructure.database.models.auth import User
from infrastructure.database.repositories.user_repository import UserRepository

router = APIRouter(prefix="/users", tags=["User Profile & Admin"])


# --- Request & Response Models ---
class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    tenant_id: Optional[str]
    is_active: bool
    is_superuser: bool


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class AssignRoleRequest(BaseModel):
    role_name: str


# --- User Profile Endpoints ---
@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve current authenticated user profile."""
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        tenant_id=current_user.tenant_id,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
    )


@router.patch("/me", response_model=UserProfileResponse)
def update_current_user_profile(
    req: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Update current user profile information."""
    user_repo = UserRepository(db)
    updated = user_repo.update(current_user.id, req.model_dump(exclude_unset=True))
    return UserProfileResponse(
        id=updated.id,
        email=updated.email,
        full_name=updated.full_name,
        tenant_id=updated.tenant_id,
        is_active=updated.is_active,
        is_superuser=updated.is_superuser,
    )


@router.post("/me/change-password")
def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Change password for authenticated user."""
    auth_service = AuthService(db)
    try:
        auth_service.change_password(current_user.id, req.old_password, req.new_password)
        return {"message": "Password changed successfully."}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# --- Admin Only Endpoints ---
@router.get("/", dependencies=[Depends(require_roles(RoleEnum.ADMIN))])
def list_all_users(skip: int = 0, limit: int = 50, db: Session = Depends(get_db_session)):
    """List all registered users (Admin only)."""
    user_repo = UserRepository(db)
    users = user_repo.list(skip=skip, limit=limit)
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "is_active": u.is_active,
            "tenant_id": u.tenant_id,
        }
        for u in users
    ]


@router.patch("/{user_id}/role", dependencies=[Depends(require_roles(RoleEnum.ADMIN))])
def assign_role(
    user_id: str,
    req: AssignRoleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Assign role to a user (Admin only)."""
    auth_service = AuthService(db)
    try:
        role = auth_service.assign_user_role(user_id, req.role_name, admin_user_id=current_user.id)
        return {"message": f"Assigned role '{role.name}' to user '{user_id}'."}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
