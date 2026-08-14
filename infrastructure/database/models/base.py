"""Base ORM model and reusable Mixins for ARA v1.0."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class UUIDPrimaryKeyMixin:
    """Mixin for UUID string primary keys."""

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
        comment="Unique UUID primary key",
    )


class TimestampMixin:
    """Mixin for tracking creation and update timestamps."""

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        comment="Timestamp when record was created",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
        comment="Timestamp when record was last updated",
    )


class SoftDeleteMixin:
    """Mixin for soft-deleting database records."""

    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Flag indicating if record is soft-deleted",
    )
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="Timestamp when record was soft-deleted",
    )

    def soft_delete(self) -> None:
        """Mark record as soft-deleted."""
        self.is_deleted = True
        self.deleted_at = utc_now()

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None


class AuditMixin:
    """Mixin for tracking user actions on records."""

    created_by_id = Column(
        String(36),
        nullable=True,
        comment="ID of user who created this record",
    )
    updated_by_id = Column(
        String(36),
        nullable=True,
        comment="ID of user who last updated this record",
    )


class BaseORMModel(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Abstract base model combining UUID PK, Timestamps, and Soft-delete."""

    __abstract__ = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert ORM object columns to python dictionary."""
        res = {}
        for col in self.__table__.columns:
            val = getattr(self, col.name)
            if isinstance(val, datetime):
                val = val.isoformat()
            res[col.name] = val
        return res
