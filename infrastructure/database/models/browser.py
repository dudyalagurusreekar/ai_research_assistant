"""Browser Automation Metadata, Screenshots, and Downloads ORM models."""

from sqlalchemy import Column, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from infrastructure.database.models.base import BaseORMModel, Base, TimestampMixin, UUIDPrimaryKeyMixin


class BrowserSession(BaseORMModel):
    """Browser automation session tracking active browser context."""

    __tablename__ = "browser_sessions"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    current_url = Column(Text, nullable=True)
    status = Column(String(50), default="active", nullable=False)  # active, closed, crashed
    user_agent = Column(Text, nullable=True)
    viewport = Column(String(50), default="1280x800", nullable=False)
    session_data = Column(JSON, default=dict, nullable=False)

    actions = relationship("BrowserActionLog", back_populates="browser_session", cascade="all, delete-orphan")
    downloads = relationship("BrowserDownload", back_populates="browser_session", cascade="all, delete-orphan")
    screenshots = relationship("BrowserScreenshot", back_populates="browser_session", cascade="all, delete-orphan")


class BrowserActionLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Log of actions taken by browser automation subagent."""

    __tablename__ = "browser_action_logs"

    browser_session_id = Column(String(36), ForeignKey("browser_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String(100), nullable=False)  # navigate, click, type, scroll, extract
    target_selector = Column(Text, nullable=True)
    value = Column(Text, nullable=True)
    duration_ms = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="success", nullable=False)

    browser_session = relationship("BrowserSession", back_populates="actions")


class BrowserDownload(BaseORMModel):
    """Metadata for files downloaded during browser navigation."""

    __tablename__ = "browser_downloads"

    browser_session_id = Column(String(36), ForeignKey("browser_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    storage_path = Column(String(512), nullable=False)
    minio_bucket = Column(String(100), default="ara-browser-downloads", nullable=False)
    source_url = Column(Text, nullable=False)

    browser_session = relationship("BrowserSession", back_populates="downloads")


class BrowserScreenshot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Metadata for page screenshots captured during browser session."""

    __tablename__ = "browser_screenshots"

    browser_session_id = Column(String(36), ForeignKey("browser_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    page_title = Column(String(255), nullable=True)
    page_url = Column(Text, nullable=False)
    storage_path = Column(String(512), nullable=False)
    minio_bucket = Column(String(100), default="ara-screenshots", nullable=False)

    browser_session = relationship("BrowserSession", back_populates="screenshots")
