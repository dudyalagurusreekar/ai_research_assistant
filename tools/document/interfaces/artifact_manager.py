"""Artifact Manager Interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from core.models.artifact import Artifact
from tools.document.models.document import NormalizedDocument


class IDocumentArtifactManager(ABC):
    """Interface for managing raw document and extracted artifact persistence using Phase 2 infrastructure."""

    @abstractmethod
    async def store_document_artifacts(
        self,
        document: NormalizedDocument,
        raw_bytes: Optional[bytes] = None,
    ) -> List[Artifact]:
        """Store raw document, normalized JSON, extracted tables, images, and OCR outputs."""
        pass

    @abstractmethod
    async def get_normalized_document(self, document_id: str) -> Optional[NormalizedDocument]:
        """Retrieve stored NormalizedDocument by ID."""
        pass

    @abstractmethod
    async def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Retrieve a specific stored artifact by ID."""
        pass
