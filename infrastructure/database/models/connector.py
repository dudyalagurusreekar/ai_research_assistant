"""Universal Connectors Configuration and Sync Logs ORM models."""

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from infrastructure.database.models.base import BaseORMModel, Base, TimestampMixin, UUIDPrimaryKeyMixin


class ConnectorConfig(BaseORMModel):
    """External platform connector configuration."""

    __tablename__ = "connector_configs"

    name = Column(String(255), nullable=False, index=True)
    connector_type = Column(String(100), nullable=False, index=True)  # gmail, drive, github, slack, jira, notion, db
    config_data = Column(JSON, default=dict, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    last_synced_at = Column(Text, nullable=True)

    sync_logs = relationship("ConnectorSyncLog", back_populates="connector", cascade="all, delete-orphan")


class ConnectorSyncLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Sync log for external connectors."""

    __tablename__ = "connector_sync_logs"

    connector_id = Column(String(36), ForeignKey("connector_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    sync_type = Column(String(50), default="full", nullable=False)  # full, incremental
    items_synced = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="success", nullable=False, index=True)  # success, failed
    duration_ms = Column(Float, default=0.0, nullable=False)
    error_log = Column(Text, nullable=True)

    connector = relationship("ConnectorConfig", back_populates="sync_logs")
