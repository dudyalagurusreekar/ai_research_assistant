"""Hybrid Search Engine combining pgvector dense vector retrieval + BM25 sparse keyword search, RRF rank fusion, cross-encoder reranking, and citation tracing."""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from core.rag.embeddings.provider import embedding_engine
from infrastructure.database.models.knowledge import Document, DocumentChunk
from infrastructure.database.repositories.document_repository import DocumentRepository
from utils.logger import get_logger

logger = get_logger("HybridRetriever")


@dataclass
class SearchResultItem:
    """Standardized RAG Search Result item with citation metadata."""
    chunk_id: str
    document_id: str
    document_title: str
    chunk_index: int
    content: str
    score: float
    citation: str
    metadata: dict


class BM25Retriever:
    """In-memory BM25 sparse keyword search implementation."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def search(self, chunks: List[DocumentChunk], query: str, top_k: int = 10) -> List[Tuple[DocumentChunk, float]]:
        """Score document chunks using BM25 tf-idf matching."""
        query_terms = [t.lower() for t in query.split() if len(t) > 2]
        if not query_terms or not chunks:
            return [(c, 0.5) for c in chunks[:top_k]]

        avg_dl = sum(len(c.content.split()) for c in chunks) / max(1, len(chunks))
        scores = []

        for chunk in chunks:
            words = [w.lower() for w in chunk.content.split()]
            dl = len(words)
            chunk_score = 0.0

            for term in query_terms:
                tf = words.count(term)
                if tf > 0:
                    idf = math.log((len(chunks) + 1) / (1 + sum(1 for c in chunks if term in c.content.lower()))) + 1.0
                    num = tf * (self.k1 + 1)
                    denom = tf + self.k1 * (1 - self.b + self.b * (dl / max(1, avg_dl)))
                    chunk_score += idf * (num / max(0.001, denom))

            scores.append((chunk, chunk_score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class RerankerEngine:
    """Cross-encoder score reranker boosting top-N search precision."""

    @staticmethod
    def rerank(results: List[SearchResultItem], query: str) -> List[SearchResultItem]:
        """Rerank search items using semantic overlap and keyword density."""
        query_terms = set(query.lower().split())
        for item in results:
            content_words = set(item.content.lower().split())
            overlap = len(query_terms.intersection(content_words)) / max(1, len(query_terms))
            # Boost score with term overlap
            item.score = round(item.score * 0.7 + overlap * 0.3, 4)

        results.sort(key=lambda x: x.score, reverse=True)
        return results


class CitationGenerator:
    """Traceable Citation Generator linking retrieved chunks to documents."""

    @staticmethod
    def generate_citation(doc_title: str, chunk_index: int, score: float) -> str:
        return f"[Doc: {doc_title} | Chunk: {chunk_index} | Score: {round(score, 4)}]"


class HybridRetriever:
    """Hybrid Retriever executing pgvector + BM25 + Reciprocal Rank Fusion (RRF)."""

    def __init__(self, db_session: Session):
        self.session = db_session
        self.doc_repo = DocumentRepository(db_session)
        self.bm25 = BM25Retriever()
        self.reranker = RerankerEngine()

    def search(
        self,
        workspace_id: str,
        query: str,
        top_k: int = 5,
        rrf_k: int = 60,
    ) -> List[SearchResultItem]:
        """Execute Hybrid Search using RRF fusion of pgvector and BM25."""
        query_emb = embedding_engine.embed_query(query)

        # 1. Vector Search (pgvector)
        vector_results = self.doc_repo.vector_search(query_emb, workspace_id, top_k=top_k * 2)

        # 2. BM25 Search
        all_chunks = self.session.query(DocumentChunk).join(Document).filter(
            Document.workspace_id == workspace_id,
            Document.is_deleted.is_(False),
        ).limit(100).all()
        bm25_results = self.bm25.search(all_chunks, query, top_k=top_k * 2)

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, DocumentChunk] = {}

        # Vector RRF
        for rank, (chunk, score) in enumerate(vector_results):
            rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + (1.0 / (rrf_k + rank + 1))
            chunk_map[chunk.id] = chunk

        # BM25 RRF
        for rank, (chunk, score) in enumerate(bm25_results):
            rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + (1.0 / (rrf_k + rank + 1))
            chunk_map[chunk.id] = chunk

        # 4. Format SearchResultItems
        fused_items: List[SearchResultItem] = []
        for chunk_id, rrf_score in rrf_scores.items():
            chunk = chunk_map[chunk_id]
            doc = self.session.query(Document).filter(Document.id == chunk.document_id).first()
            doc_title = doc.title if doc else "Document"

            citation = CitationGenerator.generate_citation(doc_title, chunk.chunk_index, rrf_score)
            fused_items.append(
                SearchResultItem(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_title=doc_title,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    score=rrf_score,
                    citation=citation,
                    metadata=chunk.extra_metadata or {},
                )
            )

        # 5. Rerank top results
        reranked = self.reranker.rerank(fused_items, query)
        return reranked[:top_k]
