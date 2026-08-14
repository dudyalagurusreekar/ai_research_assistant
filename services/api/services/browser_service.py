"""Clean Architecture Service for Browser Automation Tracking and Screenshots."""

from typing import List, Optional
from sqlalchemy.orm import Session

from infrastructure.database.models.browser import BrowserActionLog, BrowserScreenshot, BrowserSession
from infrastructure.storage.storage_manager import storage_manager


class BrowserWorkflowService:
    """Business logic service for Browser Automation Metadata and Screenshots."""

    def __init__(self, db_session: Session):
        self.session = db_session

    def create_browser_session(self, user_id: str, initial_url: str = "about:blank") -> BrowserSession:
        """Create new browser automation tracking session."""
        bs = BrowserSession(
            user_id=user_id,
            current_url=initial_url,
            status="active",
        )
        self.session.add(bs)
        self.session.commit()
        self.session.refresh(bs)
        return bs

    def log_action(self, session_id: str, action_type: str, selector: Optional[str] = None, value: Optional[str] = None) -> BrowserActionLog:
        """Log a browser navigation/interaction action."""
        action = BrowserActionLog(
            browser_session_id=session_id,
            action_type=action_type,
            target_selector=selector,
            value=value,
            status="success",
        )
        self.session.add(action)
        self.session.commit()
        self.session.refresh(action)
        return action

    def capture_screenshot(self, session_id: str, image_bytes: bytes, page_url: str) -> BrowserScreenshot:
        """Upload screenshot blob to MinIO (ara-screenshots) and create metadata entry."""
        screenshot = storage_manager.store_screenshot(
            browser_session_id=session_id,
            page_url=page_url,
            screenshot_bytes=image_bytes,
            db_session=self.session,
        )
        self.session.commit()
        self.session.refresh(screenshot)
        return screenshot

