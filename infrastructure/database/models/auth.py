"""Authentication, User, Role, and Session ORM models."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, JSON
from sqlalchemy.orm import relationship
from infrastructure.database.models.base import BaseORMModel, Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(BaseORMModel):
    """User account model."""

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    tenant_id = Column(String(36), nullable=True, index=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    auth_sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    research_sessions = relationship("ResearchSession", back_populates="user", cascade="all, delete-orphan")


class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Role definition model."""

    __tablename__ = "roles"

    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    permissions = Column(JSON, default=list, nullable=False)

    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")


class UserRole(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Junction table associating Users and Roles."""

    __tablename__ = "user_roles"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)

    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")


class APIKey(BaseORMModel):
    """API Key for automated programmatic access."""

    __tablename__ = "api_keys"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    key_prefix = Column(String(16), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    permissions = Column(JSON, default=list, nullable=False)

    user = relationship("User", back_populates="api_keys")


class AuthToken(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """JWT / Refresh Token tracking model."""

    __tablename__ = "auth_tokens"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(Text, unique=True, nullable=False, index=True)
    token_type = Column(String(50), default="bearer", nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)


class Session(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Active user web session tracking."""

    __tablename__ = "sessions"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="auth_sessions")
