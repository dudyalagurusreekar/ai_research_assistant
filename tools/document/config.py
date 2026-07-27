"""Typed Configuration settings for Document Intelligence Platform."""

from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class DocumentConfig:
    """Configuration options for document processing pipeline, parsers, and retrieval."""

    # Processing options
    default_encoding: str = "utf-8"
    max_file_size_bytes: int = 100 * 1024 * 1024  # 100 MB
    enable_ocr: bool = True
    ocr_language: str = "eng"
    ocr_min_text_len: int = 20  # If extracted text length < 20, trigger OCR

    # Semantic Chunking defaults
    default_chunk_size: int = 500  # Words / tokens approx
    default_chunk_overlap: int = 50
    min_chunk_size: int = 50

    # Pipeline Steps enabling
    enable_cleaning: bool = True
    enable_header_footer_removal: bool = True
    enable_heading_detection: bool = True
    enable_table_extraction: bool = True
    enable_image_extraction: bool = True
    enable_chunking: bool = True

    # Storage settings
    store_original_file: bool = True
    artifact_storage_dir: str = ".document_artifacts"

    # Custom options
    custom_options: Dict[str, Any] = field(default_factory=dict)
