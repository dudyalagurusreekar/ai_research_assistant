"""SynchronizationEngine, WatermarkTracker, and SyncCheckpoint for incremental sync."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time
import json
import os

from infrastructure.logging.logger import StructuredLogger


class SyncMode(str, Enum):
    """Supported synchronization modes."""
    FULL = "full"
    INCREMENTAL = "incremental"
    DELTA = "delta"


@dataclass
class Watermark:
    """State watermark tracking sync progress and tokens."""
    service_name: str
    entity_type: str
    last_sync_timestamp: float = 0.0
    sync_token: Optional[str] = None
    page_token: Optional[str] = None
    records_synced: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "entity_type": self.entity_type,
            "last_sync_timestamp": self.last_sync_timestamp,
            "sync_token": self.sync_token,
            "page_token": self.page_token,
            "records_synced": self.records_synced,
        }


@dataclass
class SyncCheckpoint:
    """Checkpoint capturing incremental sync state for recovery."""
    checkpoint_id: str
    service_name: str
    watermark: Watermark
    status: str = "in_progress"  # 'in_progress', 'completed', 'failed'
    created_at: float = field(default_factory=time.time)


class WatermarkTracker:
    """Tracks and persists watermarks across services and entity types."""

    def __init__(self, store_path: Optional[str] = None) -> None:
        self._logger = StructuredLogger("WatermarkTracker")
        self._store_path = store_path or ".storage/watermarks.json"
        self._watermarks: Dict[str, Watermark] = {}
        self._load_watermarks()

    def _key(self, service: str, entity_type: str) -> str:
        return f"{service.lower()}:{entity_type.lower()}"

    def _load_watermarks(self) -> None:
        if os.path.exists(self._store_path):
            try:
                with open(self._store_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self._watermarks[k] = Watermark(
                            service_name=v["service_name"],
                            entity_type=v["entity_type"],
                            last_sync_timestamp=v.get("last_sync_timestamp", 0.0),
                            sync_token=v.get("sync_token"),
                            page_token=v.get("page_token"),
                            records_synced=v.get("records_synced", 0),
                        )
            except Exception as e:
                self._logger.warning(f"Failed to load watermark tracker state: {e}")

    def save_watermarks(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._store_path), exist_ok=True)
            data = {k: v.to_dict() for k, v in self._watermarks.items()}
            with open(self._store_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self._logger.error(f"Failed to save watermark state: {e}")

    def get_watermark(self, service: str, entity_type: str) -> Watermark:
        key = self._key(service, entity_type)
        if key not in self._watermarks:
            self._watermarks[key] = Watermark(service_name=service, entity_type=entity_type)
        return self._watermarks[key]

    def update_watermark(
        self,
        service: str,
        entity_type: str,
        sync_token: Optional[str] = None,
        page_token: Optional[str] = None,
        added_records: int = 0,
    ) -> Watermark:
        wm = self.get_watermark(service, entity_type)
        wm.last_sync_timestamp = time.time()
        if sync_token:
            wm.sync_token = sync_token
        wm.page_token = page_token
        wm.records_synced += added_records
        self.save_watermarks()
        return wm


class SynchronizationEngine:
    """Master engine orchestrating Full, Incremental, and Delta synchronization."""

    def __init__(self, tracker: Optional[WatermarkTracker] = None) -> None:
        self._logger = StructuredLogger("SynchronizationEngine")
        self._tracker = tracker or WatermarkTracker()
        self._checkpoints: Dict[str, SyncCheckpoint] = {}

    def start_sync(
        self,
        service_name: str,
        entity_type: str,
        mode: SyncMode = SyncMode.INCREMENTAL,
    ) -> SyncCheckpoint:
        """Start a sync session and return checkpoint state."""
        wm = self._tracker.get_watermark(service_name, entity_type)
        checkpoint_id = f"chk_{service_name}_{entity_type}_{int(time.time())}"
        checkpoint = SyncCheckpoint(checkpoint_id=checkpoint_id, service_name=service_name, watermark=wm)
        self._checkpoints[checkpoint_id] = checkpoint
        self._logger.info(f"Sync started: [{service_name}:{entity_type}] mode={mode.value} checkpoint={checkpoint_id}")
        return checkpoint

    def record_sync_progress(
        self,
        checkpoint_id: str,
        records_fetched: int,
        next_sync_token: Optional[str] = None,
        next_page_token: Optional[str] = None,
    ) -> SyncCheckpoint:
        """Record sync progress against active checkpoint."""
        checkpoint = self._checkpoints.get(checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Sync checkpoint '{checkpoint_id}' not found.")

        wm = self._tracker.update_watermark(
            service=checkpoint.service_name,
            entity_type=checkpoint.watermark.entity_type,
            sync_token=next_sync_token,
            page_token=next_page_token,
            added_records=records_fetched,
        )
        checkpoint.watermark = wm
        return checkpoint

    def complete_sync(self, checkpoint_id: str) -> SyncCheckpoint:
        """Complete sync session successfully."""
        checkpoint = self._checkpoints.get(checkpoint_id)
        if checkpoint:
            checkpoint.status = "completed"
            self._logger.info(f"Sync completed: [{checkpoint.service_name}] checkpoint={checkpoint_id}")
        return checkpoint
