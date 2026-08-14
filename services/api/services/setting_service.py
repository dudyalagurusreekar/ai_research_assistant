"""Clean Architecture Service for System and User Settings."""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from infrastructure.database.models.settings import SystemSetting, UserSetting


class UserSettingService:
    """Business logic service for platform configuration and user preferences."""

    def __init__(self, db_session: Session):
        self.session = db_session

    def get_system_settings(self) -> Dict[str, Any]:
        """Fetch all platform system settings."""
        settings_objs = self.session.query(SystemSetting).all()
        return {s.key: s.value for s in settings_objs}

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Fetch custom user preferences."""
        setting = self.session.query(UserSetting).filter(UserSetting.user_id == user_id, UserSetting.setting_key == "preferences").first()
        return setting.setting_value if setting else {"theme": "dark", "notifications": True}

    def update_user_preferences(self, user_id: str, new_preferences: dict) -> Dict[str, Any]:
        """Update user preferences."""
        setting = self.session.query(UserSetting).filter(UserSetting.user_id == user_id, UserSetting.setting_key == "preferences").first()
        if not setting:
            setting = UserSetting(user_id=user_id, setting_key="preferences", setting_value=new_preferences)
            self.session.add(setting)
        else:
            updated = dict(setting.setting_value) if setting.setting_value else {}
            updated.update(new_preferences)
            setting.setting_value = updated
        
        self.session.commit()
        self.session.refresh(setting)
        return setting.setting_value
