"""JWT Token Generation, Verification, Rotation, and Redis Revocation Blacklist."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt

from config.settings import settings
from infrastructure.cache.cache_manager import cache_manager
from utils.logger import get_logger

logger = get_logger("JWTManager")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class JWTManager:
    """Production JWT Manager supporting Access, Refresh, Verification, and Reset Tokens."""

    def __init__(self, secret_key: Optional[str] = None, algorithm: Optional[str] = None):
        self.secret_key = secret_key or settings.SECRET_KEY
        self.algorithm = algorithm or settings.JWT_ALGORITHM

    def create_access_token(
        self,
        user_id: str,
        email: str,
        tenant_id: Optional[str] = None,
        role: str = "Researcher",
        expires_minutes: Optional[int] = None,
    ) -> str:
        """Issue a short-lived access JWT token."""
        minutes = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
        now = utc_now()
        expires = now + timedelta(minutes=minutes)
        jti = str(uuid.uuid4())

        payload = {
            "sub": user_id,
            "email": email,
            "tenant_id": tenant_id,
            "role": role,
            "type": "access",
            "jti": jti,
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self,
        user_id: str,
        expires_days: int = 7,
    ) -> str:
        """Issue a long-lived refresh JWT token."""
        now = utc_now()
        expires = now + timedelta(days=expires_days)
        jti = str(uuid.uuid4())

        payload = {
            "sub": user_id,
            "type": "refresh",
            "jti": jti,
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_email_verification_token(self, user_id: str, email: str, expires_hours: int = 24) -> str:
        """Issue an email verification token."""
        now = utc_now()
        expires = now + timedelta(hours=expires_hours)

        payload = {
            "sub": user_id,
            "email": email,
            "type": "email_verification",
            "jti": str(uuid.uuid4()),
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_password_reset_token(self, user_id: str, email: str, expires_minutes: int = 30) -> str:
        """Issue a single-use password reset token."""
        now = utc_now()
        expires = now + timedelta(minutes=expires_minutes)

        payload = {
            "sub": user_id,
            "email": email,
            "type": "password_reset",
            "jti": str(uuid.uuid4()),
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate JWT signature & expiration. Raises jwt.PyJWTError on failure."""
        payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        
        # Check Redis blacklist for token revocation
        jti = payload.get("jti")
        if jti and self.is_token_revoked(jti):
            raise jwt.InvalidTokenError("Token has been revoked.")

        return payload

    def revoke_token(self, jti: str, ttl_seconds: int = 86400) -> bool:
        """Blacklist a JWT JTI in Redis."""
        key = f"jwt:blacklist:{jti}"
        return cache_manager.set(key, {"revoked_at": int(utc_now().timestamp())}, ttl_seconds=ttl_seconds)

    def is_token_revoked(self, jti: str) -> bool:
        """Check if JWT JTI is blacklisted in Redis."""
        key = f"jwt:blacklist:{jti}"
        return cache_manager.get(key) is not None


# Singleton JWTManager instance
jwt_manager = JWTManager()
