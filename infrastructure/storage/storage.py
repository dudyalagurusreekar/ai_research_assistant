"""Async Storage Layer with checkpointing, metadata, and versioning support."""

import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from core.utils.time_utils import utc_isoformat


class IStorage(ABC):
    """Generic async storage interface."""

    @abstractmethod
    async def write(self, key: str, data: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        pass

    @abstractmethod
    async def read(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    async def save_checkpoint(self, checkpoint_id: str, state_data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        pass


class DiskStorage(IStorage):
    """File-system backed asynchronous storage provider with versioning and checkpoints."""

    def __init__(self, base_dir: str = ".storage") -> None:
        self.base_dir = base_dir
        self.checkpoints_dir = os.path.join(base_dir, "checkpoints")
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.checkpoints_dir, exist_ok=True)

    async def write(self, key: str, data: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Write key-value data to disk with metadata wrapping."""
        filepath = os.path.join(self.base_dir, f"{key}.json")
        payload = {
            "key": key,
            "data": data,
            "metadata": metadata or {},
            "updated_at": utc_isoformat(),
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return True

    async def read(self, key: str) -> Optional[Any]:
        """Read data payload for a key."""
        filepath = os.path.join(self.base_dir, f"{key}.json")
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            payload = json.load(f)
            return payload.get("data")

    async def delete(self, key: str) -> bool:
        """Delete storage file for key."""
        filepath = os.path.join(self.base_dir, f"{key}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False

    async def save_checkpoint(self, checkpoint_id: str, state_data: Dict[str, Any]) -> bool:
        """Save execution state snapshot as a checkpoint."""
        filepath = os.path.join(self.checkpoints_dir, f"{checkpoint_id}.json")
        payload = {
            "checkpoint_id": checkpoint_id,
            "state": state_data,
            "timestamp": utc_isoformat(),
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return True

    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Load state snapshot from a checkpoint."""
        filepath = os.path.join(self.checkpoints_dir, f"{checkpoint_id}.json")
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            payload = json.load(f)
            return payload.get("state")
