"""Disaster Recovery Manager — Automated backup snapshots, state serialization, and restore operations."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.platform_infra.models.disaster import BackupSnapshot, RestoreStatus
from utils.logger import get_logger

logger = get_logger("DisasterRecoveryManager")


class DisasterRecoveryManager:
    """Manages disaster recovery backup snapshot generation and point-in-time state restore operations."""

    def __init__(self, backup_dir: Optional[str] = None) -> None:
        if backup_dir is None:
            backup_dir = os.path.join(os.getcwd(), ".backups")
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._snapshots: Dict[str, BackupSnapshot] = {}

    def create_snapshot(
        self, tenant_id: str = "global", state_data: Optional[Dict[str, Any]] = None
    ) -> BackupSnapshot:
        """Serialize state data into backup snapshot file."""
        state_data = state_data or {"timestamp": "2026-07-29", "tenant_id": tenant_id, "status": "active"}

        snapshot = BackupSnapshot(
            tenant_id=tenant_id,
            components_backed_up=["planner", "collaboration", "knowledge_graph", "workflow"],
        )

        file_path = self.backup_dir / f"{snapshot.snapshot_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2)

        snapshot.storage_file = str(file_path.resolve())
        snapshot.size_bytes = file_path.stat().st_size
        self._snapshots[snapshot.snapshot_id] = snapshot

        logger.info(f"DisasterRecoveryManager created backup snapshot '{snapshot.snapshot_id}' ({snapshot.size_bytes} bytes)")
        return snapshot

    def restore_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """Restore state from snapshot file."""
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot or not Path(snapshot.storage_file).exists():
            raise ValueError(f"Snapshot '{snapshot_id}' not found or backup file missing.")

        with open(snapshot.storage_file, "r", encoding="utf-8") as f:
            restored_data = json.load(f)

        logger.info(f"DisasterRecoveryManager restored snapshot '{snapshot_id}' successfully")
        return restored_data

    def list_snapshots(self) -> List[BackupSnapshot]:
        """List all available backup snapshots."""
        return list(self._snapshots.values())
