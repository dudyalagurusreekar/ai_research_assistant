"""System Settings, User Preferences, and Immutable Audit Log ORM models."""

from sqlalchemy import Boolean, Column, ForeignKey, String, Text, JSON
from infrastructure.database.models.base import BaseORMModel, Base, TimestampMixin, UUIDPrimaryKeyMixin


class SystemSetting(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Global platform configuration setting."""

    __tablename__ = "system_settings"

    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)


class UserSetting(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Per-user customization and preferences."""

    __tablename__ = "user_settings"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    setting_key = Column(String(100), nullable=False, index=True)
    setting_value = Column(JSON, default=dict, nullable=False)


class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Immutable audit trail for compliance and security events."""

    __tablename__ = "audit_logs"

    user_id = Column(String(36), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # create, update, delete, login, export
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(100), nullable=True)
    payload = Column(JSON, default=dict, nullable=False)
    ip_address = Column(String(45), nullable=True)
