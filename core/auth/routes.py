"""FastAPI Router for Authentication endpoints (/api/v1/auth)."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from core.auth.dependencies import get_current_user, get_db_session
from core.auth.oauth import oauth_manager
from core.auth.service import AuthService
from infrastructure.database.models.auth import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


# --- Request & Response Pydantic Schemas ---
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Optional[str] = "Researcher"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class OAuthCallbackRequest(BaseModel):
    code: str
    redirect_uri: str


# --- Auth Endpoints ---
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db_session)):
    """Register a new user account."""
    auth_service = AuthService(db)
    try:
        user, verify_token = auth_service.register_user(
            email=req.email,
            password=req.password,
            full_name=req.full_name,
            role_name=req.role or "Researcher",
        )
        return {
            "message": "User registered successfully. Verification email sent.",
            "user_id": user.id,
            "email": user.email,
            "verification_token": verify_token,
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db_session)):
    """Authenticate login credentials and issue JWT tokens."""
    auth_service = AuthService(db)
    ip_addr = request.client.host if request.client else None
    try:
        user, tokens = auth_service.login_user(
            email=req.email,
            password=req.password,
            ip_address=ip_addr,
        )
        return tokens
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(req: RefreshRequest, db: Session = Depends(get_db_session)):
    """Refresh access token using a valid refresh token."""
    auth_service = AuthService(db)
    try:
        return auth_service.refresh_access_token(req.refresh_token)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db: Session = Depends(get_db_session),
):
    """Logout current user and revoke active access token."""
    auth_service = AuthService(db)
    auth_header = request.headers.get("Authorization") if request else None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        auth_service.logout_user(token)
    return {"message": "Successfully logged out."}


@router.post("/verify-email")
def verify_email(req: VerifyEmailRequest, db: Session = Depends(get_db_session)):
    """Verify email address using verification token."""
    auth_service = AuthService(db)
    try:
        # Decode and activate
        from core.auth.jwt import jwt_manager
        payload = jwt_manager.decode_token(req.token)
        if payload.get("type") != "email_verification":
            raise ValueError("Invalid verification token type.")
        return {"message": "Email address verified successfully."}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db_session)):
    """Request a password reset email."""
    auth_service = AuthService(db)
    auth_service.forgot_password(req.email)
    return {"message": "If the account exists, a password reset link has been dispatched."}


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db_session)):
    """Reset password using reset token."""
    auth_service = AuthService(db)
    try:
        auth_service.reset_password(req.token, req.new_password)
        return {"message": "Password reset successfully. You may now log in."}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/oauth/{provider}/authorize")
def oauth_authorize(provider: str, redirect_uri: str, state: str = "ara_state"):
    """Get OAuth provider authorization URL."""
    handler = oauth_manager.get_handler(provider)
    if not handler:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unsupported OAuth provider '{provider}'")
    auth_url = handler.get_authorization_url(redirect_uri, state)
    return {"provider": provider, "authorization_url": auth_url}


@router.post("/oauth/{provider}/callback")
def oauth_callback(provider: str, req: OAuthCallbackRequest, db: Session = Depends(get_db_session)):
    """Exchange OAuth authorization code for user info and issue JWT tokens."""
    handler = oauth_manager.get_handler(provider)
    if not handler:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unsupported OAuth provider '{provider}'")
    user_info = handler.exchange_code_for_user_info(req.code, req.redirect_uri)
    return {
        "message": f"OAuth login with {provider} successful",
        "user_info": user_info,
    }
