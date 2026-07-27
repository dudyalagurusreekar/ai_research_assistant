"""DocumentArtifactManager implementation integrating Phase 2 ArtifactStore and Phase 1 EventBus."""

import json
from typing import List, Optional, Dict, Any
from core.models.artifact import Artifact
from core.models.event import Event
from core.interfaces.event_bus import IEventBus
from infrastructure.artifacts.store import ArtifactStore
from tools.document.interfaces.artifact_manager import IDocumentArtifactManager
from tools.document.models.document import NormalizedDocument, AttachedArtifact
from infrastructure.logging.logger import StructuredLogger


class DocumentArtifactManager(IDocumentArtifactManager):
    """Stores raw document files, normalized document structures, tables, images, and OCR artifacts."""

    def __init__(
        self,
        artifact_store: Optional[ArtifactStore] = None,
        event_bus: Optional[IEventBus] = None,
    ) -> None:
        self._logger = StructuredLogger("DocumentArtifactManager")
        self.artifact_store = artifact_store or ArtifactStore()
        self.event_bus = event_bus

    async def store_document_artifacts(
        self,
        document: NormalizedDocument,
        raw_bytes: Optional[bytes] = None,
    ) -> List[Artifact]:
        """Store raw document, normalized JSON, extracted tables, images, and OCR outputs."""
        saved_artifacts: List[Artifact] = []

        # 1. Store Raw File if provided
        if raw_bytes:
            raw_art = await self.artifact_store.save_artifact(
                name=f"raw_{document.metadata.file_name}",
                artifact_type="raw_document",
                content=raw_bytes.hex(),  # Stored as hex string for serializability
                mime_type=document.metadata.mime_type,
                metadata={"document_id": document.document_id},
            )
            saved_artifacts.append(raw_art)
            document.artifacts.append(
                AttachedArtifact(
                    artifact_id=raw_art.artifact_id,
                    name=raw_art.name,
                    artifact_type="raw_document",
                    mime_type=document.metadata.mime_type,
                )
            )

        # 2. Store Normalized Document JSON
        doc_json = json.dumps(document.to_dict(), indent=2)
        norm_art = await self.artifact_store.save_artifact(
            name=f"normalized_{document.document_id}.json",
            artifact_type="normalized_doc",
            content=doc_json,
            mime_type="application/json",
            metadata={"document_id": document.document_id, "version": document.version},
        )
        saved_artifacts.append(norm_art)
        document.artifacts.append(
            AttachedArtifact(
                artifact_id=norm_art.artifact_id,
                name=norm_art.name,
                artifact_type="normalized_doc",
                mime_type="application/json",
            )
        )

        # 3. Store Extracted Tables (CSV format)
        for tbl in document.tables:
            if tbl.csv_content:
                tbl_art = await self.artifact_store.save_artifact(
                    name=f"table_{tbl.table_id}.csv",
                    artifact_type="table_csv",
                    content=tbl.csv_content,
                    mime_type="text/csv",
                    metadata={"document_id": document.document_id, "table_id": tbl.table_id},
                )
                saved_artifacts.append(tbl_art)

        # 4. Store Extracted Images & OCR
        for img in document.images:
            if img.raw_bytes:
                img_art = await self.artifact_store.save_artifact(
                    name=f"image_{img.image_id}",
                    artifact_type="extracted_image",
                    content=img.raw_bytes.hex(),
                    mime_type=img.mime_type,
                    metadata={"document_id": document.document_id, "image_id": img.image_id},
                )
                img.artifact_id = img_art.artifact_id
                saved_artifacts.append(img_art)

            if img.ocr_text:
                ocr_art = await self.artifact_store.save_artifact(
                    name=f"ocr_{img.image_id}.txt",
                    artifact_type="ocr_text",
                    content=img.ocr_text,
                    mime_type="text/plain",
                    metadata={"document_id": document.document_id, "image_id": img.image_id},
                )
                saved_artifacts.append(ocr_art)

        # 5. Emit Event if EventBus configured
        if self.event_bus:
            evt = Event(
                event_type="document.artifacts_stored",
                source="DocumentArtifactManager",
                payload={
                    "document_id": document.document_id,
                    "artifact_count": len(saved_artifacts),
                    "artifact_ids": [a.artifact_id for a in saved_artifacts],
                },
            )
            await self.event_bus.publish(evt)

        self._logger.info(f"Stored {len(saved_artifacts)} artifacts for document '{document.document_id}'")
        return saved_artifacts

    async def get_normalized_document(self, document_id: str) -> Optional[NormalizedDocument]:
        """Retrieve stored NormalizedDocument by ID."""
        artifacts = await self.artifact_store.list_artifacts(artifact_type="normalized_doc")
        for art in artifacts:
            if art.metadata.get("document_id") == document_id or art.name.startswith(f"normalized_{document_id}"):
                full_art = await self.artifact_store.get_artifact(art.artifact_id)
                if full_art and full_art.content:
                    try:
                        data = json.loads(full_art.content)
                        return NormalizedDocument.from_dict(data)
                    except Exception as e:
                        self._logger.error(f"Error parsing stored JSON artifact: {e}")
        return None

    async def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Retrieve a specific stored artifact by ID."""
        return await self.artifact_store.get_artifact(artifact_id)
