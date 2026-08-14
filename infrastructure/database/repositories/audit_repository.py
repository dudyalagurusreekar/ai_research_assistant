"""Audit Log and System Setting Repository implementation."""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from infrastructure.database.models.settings import AuditLog, SystemSetting, UserSetting
from infrastructure.database.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for managing audit logs and system configurations."""

    def __init__(self, session: Session):
        super().__init__(AuditLog, session)

    def record_event(
        self,
        action: str,
        resource_type: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Create an immutable audit log entry."""
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            payload=payload or {},
            ip_address=ip_address,
        )
        self.session.add(entry)
        self.session.flush()
        return entry

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Fetch global system setting value by key."""
        setting = self.session.query(SystemSetting).filter(SystemSetting.key == key).first()
        return setting.value if setting else default

    def set_setting(self, key: str, value: str, description: Optional[str] = None, is_public: bool = False) -> SystemSetting:
        """Set or update a system setting."""
        setting = self.session.query(SystemSetting).filter(SystemSetting.key == key).first()
        if not setting:
            setting = SystemSetting(key=key, value=value, description=description, is_public=is_public)
            self.session.add(setting)
        else:
            setting.value = value
            if description:
                setting.description = description
            setting.is_public = is_public
        self.session.flush()
        return setting
