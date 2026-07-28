"""Retrieval, Comparison, and Summarization Result Models."""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class SearchResult:
    """Keyword / Ranked search result item."""

    chunk_id: str
    document_id: str
    score: float
    text: str
    section_title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "score": self.score,
            "text": self.text,
            "section_title": self.section_title,
            "metadata": self.metadata,
        }


@dataclass
class DocumentComparisonResult:
    """Result of comparing two NormalizedDocument objects."""

    doc_a_id: str
    doc_b_id: str
    text_similarity_score: float  # 0.0 to 1.0 (Cosine / Jaccard)
    jaccard_similarity: float
    cosine_similarity: float
    common_words_count: int
    doc_a_unique_words: int
    doc_b_unique_words: int
    section_count_diff: int
    table_count_diff: int
    image_count_diff: int
    summary_diff: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_a_id": self.doc_a_id,
            "doc_b_id": self.doc_b_id,
            "text_similarity_score": self.text_similarity_score,
            "jaccard_similarity": self.jaccard_similarity,
            "cosine_similarity": self.cosine_similarity,
            "common_words_count": self.common_words_count,
            "doc_a_unique_words": self.doc_a_unique_words,
            "doc_b_unique_words": self.doc_b_unique_words,
            "section_count_diff": self.section_count_diff,
            "table_count_diff": self.table_count_diff,
            "image_count_diff": self.image_count_diff,
            "summary_diff": self.summary_diff,
            "details": self.details,
        }


@dataclass
class DocumentSummary:
    """Extractive summary of a NormalizedDocument."""

    document_id: str
    title: Optional[str]
    summary_text: str
    key_sentences: List[str] = field(default_factory=list)
    key_terms: List[str] = field(default_factory=list)
    section_titles: List[str] = field(default_factory=list)
    total_words: int = 0
    summary_words: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "title": self.title,
            "summary_text": self.summary_text,
            "key_sentences": self.key_sentences,
            "key_terms": self.key_terms,
            "section_titles": self.section_titles,
            "total_words": self.total_words,
            "summary_words": self.summary_words,
        }
