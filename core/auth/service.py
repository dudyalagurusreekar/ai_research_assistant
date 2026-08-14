"""Master AuthService orchestrating authentication, sessions, security, and user profiles."""

import time
from typing import Any, Dict, List, Optional, Tuple
import jwt
from sqlalchemy.orm import Session

from core.auth.email_service import email_service
from core.auth.jwt import jwt_manager
from core.auth.password import PasswordHasher, PasswordPolicyValidator
from core.auth.rbac import RoleEnum, RBACManager
from infrastructure.cache.cache_manager import cache_manager
from infrastructure.database.models.auth import Role, User, UserRole
from infrastructure.database.repositories.audit_repository import AuditLogRepository
from infrastructure.database.repositories.user_repository import UserRepository
from utils.logger import get_logger

logger = get_logger("AuthService")


class AuthService:
    """Master production authentication and user management service."""

    MAX_FAILED_LOGIN_ATTEMPTS = 5
    LOCKOUT_TIME_SECONDS = 900  # 15 minutes lockout

    def __init__(self, db_session: Session):
        self.session = db_session
        self.user_repo = UserRepository(db_session)
        self.audit_repo = AuditLogRepository(db_session)

    # --- 1. User Registration ---
    def register_user(
        self,
        email: str,
        password: str,
        full_name: str,
        role_name: str = RoleEnum.RESEARCHER.value,
        tenant_id: Optional[str] = None,
    ) -> Tuple[User, str]:
        """Register a new user account."""
        email = email.lower().strip()

        # Check existing user
        if self.user_repo.get_by_email(email):
            raise ValueError(f"User with email '{email}' already exists.")

        # Validate password strength
        is_valid, errors = PasswordPolicyValidator.validate(password)
        if not is_valid:
            raise ValueError(f"Password complexity failed: {'; '.join(errors)}")

        # Hash password and create user
        pwd_hash = PasswordHasher.hash_password(password)
        user = self.user_repo.create({
            "email": email,
            "full_name": full_name,
            "password_hash": pwd_hash,
            "is_active": True,
            "tenant_id": tenant_id or "tenant-default-001",
        })

        # Assign Role
        role = self.session.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(name=role_name, permissions=RBACManager.get_role_permissions(role_name))
            self.session.add(role)
            self.session.flush()

        self.user_repo.assign_role(user.id, role.id)

        # Generate Email Verification Token & Dispatch Email
        verify_token = jwt_manager.create_email_verification_token(user.id, email)
        email_service.send_verification_email(email, verify_token)

        # Audit Event
        self.audit_repo.record_event(
            action="USER_REGISTERED",
            resource_type="USER",
            user_id=user.id,
            payload={"email": email, "role": role_name},
        )

        return user, verify_token

    # --- 2. Login & Throttling ---
    def login_user(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
    ) -> Tuple[User, Dict[str, str]]:
        """Authenticate user login with lockout throttling & issue JWT token pair."""
        email = email.lower().strip()
        lockout_key = f"auth:lockout:{email}"
        attempts_key = f"auth:failed_attempts:{email}"

        # Check if account is locked out
        if cache_manager.get(lockout_key):
            self.audit_repo.record_event(
                action="LOGIN_BLOCKED_LOCKOUT",
                resource_type="USER",
                payload={"email": email, "ip": ip_address},
                ip_address=ip_address,
            )
            raise PermissionError("Account temporarily locked due to repeated failed login attempts. Please try again later.")

        user = self.user_repo.get_by_email(email)
        if not user or not PasswordHasher.verify_password(password, user.password_hash):
            # Increment failed attempt count
            failed_count = (cache_manager.get(attempts_key) or 0) + 1
            cache_manager.set(attempts_key, failed_count, ttl_seconds=self.LOCKOUT_TIME_SECONDS)

            if failed_count >= self.MAX_FAILED_LOGIN_ATTEMPTS:
                cache_manager.set(lockout_key, {"locked_at": time.time()}, ttl_seconds=self.LOCKOUT_TIME_SECONDS)
                logger.warning(f"Account locked out for {email} after {failed_count} failed login attempts.")

            self.audit_repo.record_event(
                action="LOGIN_FAILED",
                resource_type="USER",
                user_id=user.id if user else None,
                payload={"email": email, "failed_count": failed_count},
                ip_address=ip_address,
            )
            raise ValueError("Invalid email or password.")

        if not user.is_active:
            raise PermissionError("User account is disabled.")

        # Clear failed attempt counter on successful login
        cache_manager.delete(attempts_key)

        # Get primary user role
        roles = self.user_repo.get_user_roles(user.id)
        role_name = roles[0].name if roles else RoleEnum.RESEARCHER.value

        # Issue JWT Access and Refresh Tokens
        access_token = jwt_manager.create_access_token(
            user_id=user.id,
            email=user.email,
            tenant_id=user.tenant_id,
            role=role_name,
        )
        refresh_token = jwt_manager.create_refresh_token(user_id=user.id)

        # Store session in Redis
        cache_manager.store_session(access_token, {"user_id": user.id, "email": user.email, "role": role_name})

        # Audit Event
        self.audit_repo.record_event(
            action="LOGIN_SUCCESS",
            resource_type="USER",
            user_id=user.id,
            payload={"email": email, "role": role_name},
            ip_address=ip_address,
        )

        tokens = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
        }
        return user, tokens

    # --- 3. Token Refresh & Rotation ---
    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """Validate refresh token and issue rotated new access/refresh token pair."""
        try:
            payload = jwt_manager.decode_token(refresh_token)
        except jwt.PyJWTError as exc:
            raise ValueError(f"Invalid or expired refresh token: {exc}")

        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type for refresh.")

        user_id = payload["sub"]
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise PermissionError("User account inactive or not found.")

        # Revoke old refresh token (Token Rotation)
        jti = payload.get("jti")
        if jti:
            jwt_manager.revoke_token(jti, ttl_seconds=86400 * 7)

        roles = self.user_repo.get_user_roles(user.id)
        role_name = roles[0].name if roles else RoleEnum.RESEARCHER.value

        # Issue new token pair
        new_access_token = jwt_manager.create_access_token(
            user_id=user.id,
            email=user.email,
            tenant_id=user.tenant_id,
            role=role_name,
        )
        new_refresh_token = jwt_manager.create_refresh_token(user_id=user.id)

        cache_manager.store_session(new_access_token, {"user_id": user.id, "email": user.email, "role": role_name})

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer",
        }

    # --- 4. Logout & Token Revocation ---
    def logout_user(self, access_token: str) -> bool:
        """Revoke user session and blacklist access token."""
        try:
            payload = jwt_manager.decode_token(access_token)
            jti = payload.get("jti")
            if jti:
                jwt_manager.revoke_token(jti, ttl_seconds=86400)
            cache_manager.revoke_session(access_token)
            
            self.audit_repo.record_event(
                action="USER_LOGOUT",
                resource_type="USER",
                user_id=payload.get("sub"),
            )
            return True
        except Exception:
            return False

    # --- 5. Password Reset ---
    def forgot_password(self, email: str) -> bool:
        """Initiate password reset flow by sending token email."""
        user = self.user_repo.get_by_email(email)
        if not user:
            return True  # Avoid leaking user existence

        reset_token = jwt_manager.create_password_reset_token(user.id, user.email)
        email_service.send_password_reset_email(user.email, reset_token)

        self.audit_repo.record_event(
            action="FORGOT_PASSWORD_REQUESTED",
            resource_type="USER",
            user_id=user.id,
        )
        return True

    def reset_password(self, reset_token: str, new_password: str) -> bool:
        """Reset password using token."""
        try:
            payload = jwt_manager.decode_token(reset_token)
        except jwt.PyJWTError as exc:
            raise ValueError(f"Invalid or expired reset token: {exc}")

        if payload.get("type") != "password_reset":
            raise ValueError("Invalid token type for password reset.")

        jti = payload.get("jti")
        # Check single-use token key in Redis
        used_key = f"auth:reset_used:{jti}"
        if cache_manager.get(used_key):
            raise ValueError("Password reset token has already been used.")

        is_valid, errors = PasswordPolicyValidator.validate(new_password)
        if not is_valid:
            raise ValueError(f"New password complexity failed: {'; '.join(errors)}")

        user_id = payload["sub"]
        pwd_hash = PasswordHasher.hash_password(new_password)
        self.user_repo.update(user_id, {"password_hash": pwd_hash})

        # Mark single-use reset token as consumed
        cache_manager.set(used_key, {"used_at": time.time()}, ttl_seconds=86400)

        self.audit_repo.record_event(
            action="PASSWORD_RESET_SUCCESS",
            resource_type="USER",
            user_id=user_id,
        )
        return True

    # --- 6. User Profile Management ---
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change password for an authenticated user."""
        user = self.user_repo.get_by_id(user_id)
        if not user or not PasswordHasher.verify_password(old_password, user.password_hash):
            raise ValueError("Incorrect old password.")

        is_valid, errors = PasswordPolicyValidator.validate(new_password)
        if not is_valid:
            raise ValueError(f"New password complexity failed: {'; '.join(errors)}")

        new_hash = PasswordHasher.hash_password(new_password)
        self.user_repo.update(user.id, {"password_hash": new_hash})

        self.audit_repo.record_event(
            action="PASSWORD_CHANGED",
            resource_type="USER",
            user_id=user.id,
        )
        return True

    def assign_user_role(self, user_id: str, role_name: str, admin_user_id: str) -> Role:
        """Assign role to user (Admin action)."""
        role = self.session.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(name=role_name, permissions=RBACManager.get_role_permissions(role_name))
            self.session.add(role)
            self.session.flush()

        # Remove existing roles and assign new role
        self.session.query(UserRole).filter(UserRole.user_id == user_id).delete()
        self.user_repo.assign_role(user_id, role.id)

        self.audit_repo.record_event(
            action="ROLE_ASSIGNED",
            resource_type="USER",
            user_id=user_id,
            payload={"assigned_role": role_name, "by_admin": admin_user_id},
        )
        return role
