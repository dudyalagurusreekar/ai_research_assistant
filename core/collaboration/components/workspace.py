"""Shared Workspace — Thread-safe shared execution context and artifact store across agents."""

from __future__ import annotations

import copy
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from utils.logger import get_logger

logger = get_logger("SharedWorkspace")


@dataclass
class WorkspaceArtifact:
    """Wrapper metadata for objects stored in the shared workspace."""

    key: str
    value: Any
    created_by_agent: str
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    artifact_type: str = "general"
    version: int = 1
    tags: List[str] = field(default_factory=list)


class SharedWorkspace:
    """Thread-safe state workspace allowing agents to share intermediate results, dataframes, and artifacts."""

    def __init__(self, workspace_id: str = "global_workspace") -> None:
        self.workspace_id = workspace_id
        self._store: Dict[str, WorkspaceArtifact] = {}
        self._lock = threading.RLock()

    def set(
        self,
        key: str,
        value: Any,
        agent_id: str = "system",
        artifact_type: str = "general",
        tags: Optional[List[str]] = None,
    ) -> WorkspaceArtifact:
        """Store a key-value artifact in the shared workspace."""
        with self._lock:
            tags = tags or []
            existing = self._store.get(key)
            version = (existing.version + 1) if existing else 1

            artifact = WorkspaceArtifact(
                key=key,
                value=value,
                created_by_agent=agent_id,
                updated_at=datetime.now(timezone.utc).isoformat(),
                artifact_type=artifact_type,
                version=version,
                tags=tags,
            )
            self._store[key] = artifact
            logger.debug(f"Workspace [{self.workspace_id}] set key '{key}' by agent '{agent_id}' (v{version})")
            return artifact

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve the value associated with key."""
        with self._lock:
            artifact = self._store.get(key)
            if artifact is None:
                return default
            return artifact.value

    def get_artifact(self, key: str) -> Optional[WorkspaceArtifact]:
        """Retrieve full artifact metadata container."""
        with self._lock:
            return self._store.get(key)

    def has(self, key: str) -> bool:
        """Check if key exists in workspace."""
        with self._lock:
            return key in self._store

    def delete(self, key: str) -> bool:
        """Remove key from workspace."""
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def list_keys(self, artifact_type: Optional[str] = None, tag: Optional[str] = None) -> List[str]:
        """List stored keys, optionally filtered by type or tag."""
        with self._lock:
            keys = []
            for k, artifact in self._store.items():
                if artifact_type and artifact.artifact_type != artifact_type:
                    continue
                if tag and tag not in artifact.tags:
                    continue
                keys.append(k)
            return keys

    def get_all(self) -> Dict[str, Any]:
        """Get a copy of all stored values as key-value dict."""
        with self._lock:
            return {k: art.value for k, art in self._store.items()}

    def clear(self) -> None:
        """Clear all artifacts from workspace."""
        with self._lock:
            self._store.clear()
            logger.debug(f"Workspace [{self.workspace_id}] cleared.")
