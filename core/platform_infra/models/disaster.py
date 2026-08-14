"""Disaster Recovery models — Backup snapshot and state restore models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class RestoreStatus(Enum):
    """Restore operation status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class BackupSnapshot:
    """Disaster recovery state backup snapshot metadata."""

    snapshot_id: str = field(default_factory=lambda: f"snp_{uuid.uuid4().hex[:8]}")
    tenant_id: str = "global"
    components_backed_up: List[str] = field(default_factory=list)
    storage_file: str = ""
    size_bytes: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "tenant_id": self.tenant_id,
            "components_backed_up": self.components_backed_up,
            "storage_file": self.storage_file,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at,
        }
