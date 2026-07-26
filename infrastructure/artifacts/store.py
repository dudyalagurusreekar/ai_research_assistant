"""Artifact Store for persisting and retrieving multimodal execution artifacts."""

import os
from typing import Any, Dict, List, Optional
from core.models.artifact import Artifact
from core.utils.id_generator import generate_id
from infrastructure.storage.storage import IStorage, DiskStorage


class ArtifactStore:
    """Stores and retrieves documents, screenshots, downloads, HTML, logs, reports, and embeddings."""

    def __init__(self, storage: Optional[IStorage] = None) -> None:
        self._storage = storage or DiskStorage(base_dir=".artifacts_store")
        self._index: Dict[str, Artifact] = {}

    async def save_artifact(
        self,
        name: str,
        artifact_type: str,
        content: Any,
        mime_type: str = "text/plain",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Artifact:
        """Store an artifact and generate a unique artifact ID."""
        artifact = Artifact(
            name=name,
            artifact_type=artifact_type,
            content=content,
            mime_type=mime_type,
            metadata=metadata or {},
        )
        self._index[artifact.artifact_id] = artifact
        await self._storage.write(artifact.artifact_id, artifact.to_dict(), metadata)
        return artifact

    async def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Retrieve an artifact by its unique ID."""
        if artifact_id in self._index:
            return self._index[artifact_id]

        data = await self._storage.read(artifact_id)
        if not data:
            return None

        artifact = Artifact(
            artifact_id=data["artifact_id"],
            name=data["name"],
            artifact_type=data["artifact_type"],
            mime_type=data.get("mime_type", "text/plain"),
            metadata=data.get("metadata", {}),
        )
        self._index[artifact_id] = artifact
        return artifact

    async def list_artifacts(self, artifact_type: Optional[str] = None) -> List[Artifact]:
        """List all artifacts, optionally filtered by type (e.g. 'screenshot', 'pdf', 'html')."""
        artifacts = list(self._index.values())
        if artifact_type:
            return [a for a in artifacts if a.artifact_type == artifact_type]
        return artifacts
