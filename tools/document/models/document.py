"""Unified NormalizedDocument data model for the Document Intelligence Platform."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from core.utils.id_generator import generate_id
from core.utils.time_utils import utc_now, utc_isoformat


@dataclass
class DocumentMetadata:
    """Document metadata model."""

    title: Optional[str] = None
    author: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    page_count: int = 0
    word_count: int = 0
    line_count: int = 0
    file_size_bytes: int = 0
    mime_type: str = "text/plain"
    file_name: str = "document"
    file_hash: Optional[str] = None
    language: str = "en"
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "author": self.author,
            "creation_date": self.creation_date,
            "modification_date": self.modification_date,
            "page_count": self.page_count,
            "word_count": self.word_count,
            "line_count": self.line_count,
            "file_size_bytes": self.file_size_bytes,
            "mime_type": self.mime_type,
            "file_name": self.file_name,
            "file_hash": self.file_hash,
            "language": self.language,
            "custom": self.custom,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentMetadata":
        return cls(**data)


@dataclass
class DocumentSection:
    """Structural section model."""

    section_id: str = field(default_factory=lambda: generate_id("sec_"))
    title: str = ""
    level: int = 1
    content: str = ""
    start_char: int = 0
    end_char: int = 0
    sub_sections: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_id": self.section_id,
            "title": self.title,
            "level": self.level,
            "content": self.content,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "sub_sections": self.sub_sections,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentSection":
        return cls(**data)


@dataclass
class DocumentParagraph:
    """Paragraph content model."""

    paragraph_id: str = field(default_factory=lambda: generate_id("par_"))
    text: str = ""
    section_id: Optional[str] = None
    paragraph_index: int = 0
    formatting: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "paragraph_id": self.paragraph_id,
            "text": self.text,
            "section_id": self.section_id,
            "paragraph_index": self.paragraph_index,
            "formatting": self.formatting,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentParagraph":
        return cls(**data)


@dataclass
class DocumentTable:
    """Extracted table model."""

    table_id: str = field(default_factory=lambda: generate_id("tbl_"))
    caption: Optional[str] = None
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    matrix: List[List[Any]] = field(default_factory=list)
    csv_content: str = ""
    json_content: str = ""
    section_id: Optional[str] = None
    page_number: Optional[int] = None
    format_type: str = "grid"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_id": self.table_id,
            "caption": self.caption,
            "headers": self.headers,
            "rows": self.rows,
            "matrix": self.matrix,
            "csv_content": self.csv_content,
            "json_content": self.json_content,
            "section_id": self.section_id,
            "page_number": self.page_number,
            "format_type": self.format_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentTable":
        return cls(**data)


@dataclass
class DocumentImage:
    """Extracted embedded image model."""

    image_id: str = field(default_factory=lambda: generate_id("img_"))
    caption: Optional[str] = None
    mime_type: str = "image/png"
    width: Optional[int] = None
    height: Optional[int] = None
    artifact_id: Optional[str] = None
    raw_bytes: Optional[bytes] = None
    ocr_text: Optional[str] = None
    section_id: Optional[str] = None
    page_number: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "image_id": self.image_id,
            "caption": self.caption,
            "mime_type": self.mime_type,
            "width": self.width,
            "height": self.height,
            "artifact_id": self.artifact_id,
            "ocr_text": self.ocr_text,
            "section_id": self.section_id,
            "page_number": self.page_number,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentImage":
        raw_bytes = data.pop("raw_bytes", None)
        inst = cls(**data)
        inst.raw_bytes = raw_bytes
        return inst


@dataclass
class DocumentReference:
    """Document reference / hyperlink / footnote model."""

    reference_id: str = field(default_factory=lambda: generate_id("ref_"))
    ref_type: str = "link"  # 'link', 'citation', 'footnote', 'cross_ref'
    title: Optional[str] = None
    url: Optional[str] = None
    text: str = ""
    section_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "ref_type": self.ref_type,
            "title": self.title,
            "url": self.url,
            "text": self.text,
            "section_id": self.section_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentReference":
        return cls(**data)


@dataclass
class DocumentChunk:
    """Semantic text chunk model."""

    chunk_id: str = field(default_factory=lambda: generate_id("chk_"))
    text: str = ""
    chunk_index: int = 0
    token_count: int = 0
    section_id: Optional[str] = None
    start_char: int = 0
    end_char: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "chunk_index": self.chunk_index,
            "token_count": self.token_count,
            "section_id": self.section_id,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentChunk":
        return cls(**data)


@dataclass
class AttachedArtifact:
    """Attached artifact reference model."""

    artifact_id: str
    name: str
    artifact_type: str
    mime_type: str = "text/plain"
    storage_key: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "name": self.name,
            "artifact_type": self.artifact_type,
            "mime_type": self.mime_type,
            "storage_key": self.storage_key,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AttachedArtifact":
        return cls(**data)


@dataclass
class NormalizedDocument:
    """Unified Normalized Document representation produced by all parsers and pipeline steps."""

    document_id: str = field(default_factory=lambda: generate_id("doc_"))
    version: str = "1.0"  # Version field for backward compatibility
    full_text: str = ""
    metadata: DocumentMetadata = field(default_factory=DocumentMetadata)
    sections: List[DocumentSection] = field(default_factory=list)
    paragraphs: List[DocumentParagraph] = field(default_factory=list)
    tables: List[DocumentTable] = field(default_factory=list)
    images: List[DocumentImage] = field(default_factory=list)
    references: List[DocumentReference] = field(default_factory=list)
    chunks: List[DocumentChunk] = field(default_factory=list)
    artifacts: List[AttachedArtifact] = field(default_factory=list)
    processing_history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=utc_isoformat)

    def add_section(self, title: str, level: int = 1, content: str = "") -> DocumentSection:
        section = DocumentSection(title=title, level=level, content=content)
        self.sections.append(section)
        return section

    def add_paragraph(self, text: str, section_id: Optional[str] = None) -> DocumentParagraph:
        par = DocumentParagraph(
            text=text,
            section_id=section_id,
            paragraph_index=len(self.paragraphs),
        )
        self.paragraphs.append(par)
        return par

    def get_full_text(self) -> str:
        """Return full document text or aggregate paragraphs."""
        if self.full_text:
            return self.full_text
        return "\n\n".join(p.text for p in self.paragraphs)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize NormalizedDocument to dictionary."""
        return {
            "document_id": self.document_id,
            "version": self.version,
            "full_text": self.full_text,
            "metadata": self.metadata.to_dict(),
            "sections": [s.to_dict() for s in self.sections],
            "paragraphs": [p.to_dict() for p in self.paragraphs],
            "tables": [t.to_dict() for t in self.tables],
            "images": [i.to_dict() for i in self.images],
            "references": [r.to_dict() for r in self.references],
            "chunks": [c.to_dict() for c in self.chunks],
            "artifacts": [a.to_dict() for a in self.artifacts],
            "processing_history": self.processing_history,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NormalizedDocument":
        """Deserialize dictionary to NormalizedDocument."""
        meta_dict = data.get("metadata", {})
        metadata = DocumentMetadata.from_dict(meta_dict) if isinstance(meta_dict, dict) else DocumentMetadata()

        sections = [DocumentSection.from_dict(s) for s in data.get("sections", [])]
        paragraphs = [DocumentParagraph.from_dict(p) for p in data.get("paragraphs", [])]
        tables = [DocumentTable.from_dict(t) for t in data.get("tables", [])]
        images = [DocumentImage.from_dict(i) for i in data.get("images", [])]
        references = [DocumentReference.from_dict(r) for r in data.get("references", [])]
        chunks = [DocumentChunk.from_dict(c) for c in data.get("chunks", [])]
        artifacts = [AttachedArtifact.from_dict(a) for a in data.get("artifacts", [])]

        return cls(
            document_id=data.get("document_id", generate_id("doc_")),
            version=data.get("version", "1.0"),
            full_text=data.get("full_text", ""),
            metadata=metadata,
            sections=sections,
            paragraphs=paragraphs,
            tables=tables,
            images=images,
            references=references,
            chunks=chunks,
            artifacts=artifacts,
            processing_history=data.get("processing_history", []),
            created_at=data.get("created_at", utc_isoformat()),
        )
