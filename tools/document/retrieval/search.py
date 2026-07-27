"""Keyword and BM25 Search Engine implementation over NormalizedDocument chunks."""

import re
import math
from typing import List, Union, Any, Dict, Tuple
from tools.document.interfaces.retrieval import IRetrievalEngine
from tools.document.models.document import NormalizedDocument, DocumentChunk
from tools.document.models.retrieval import SearchResult
from infrastructure.logging.logger import StructuredLogger


class KeywordSearchEngine(IRetrievalEngine):
    """TF-IDF / BM25 term frequency search engine operating over document chunks."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self._logger = StructuredLogger("KeywordSearchEngine")
        self.k1 = k1
        self.b = b

    async def search(
        self,
        query: str,
        documents_or_chunks: List[Union[NormalizedDocument, DocumentChunk, Dict[str, Any]]],
        top_k: int = 5,
    ) -> List[SearchResult]:
        """Perform ranked keyword/BM25 search across documents or chunks."""
        if not query or not documents_or_chunks:
            return []

        query_terms = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 1]
        if not query_terms:
            return []

        # Flatten inputs to chunks
        chunks: List[Tuple[DocumentChunk, str]] = []  # (Chunk, document_id)
        for item in documents_or_chunks:
            if isinstance(item, NormalizedDocument):
                for chk in item.chunks:
                    chunks.append((chk, item.document_id))
                if not item.chunks and item.full_text:
                    # Fallback single chunk
                    fallback_chk = DocumentChunk(text=item.full_text, metadata={"section_title": item.metadata.title})
                    chunks.append((fallback_chk, item.document_id))
            elif isinstance(item, DocumentChunk):
                chunks.append((item, item.metadata.get("document_id", "doc_unknown")))
            elif isinstance(item, dict):
                chk = DocumentChunk.from_dict(item)
                chunks.append((chk, item.get("document_id", "doc_unknown")))

        if not chunks:
            return []

        # BM25 Corpus Statistics
        avg_dl = sum(len(c[0].text.split()) for c in chunks) / max(1, len(chunks))
        N = len(chunks)

        # Document Frequency for query terms
        df: Dict[str, int] = {term: 0 for term in query_terms}
        for chk, _ in chunks:
            text_lower = chk.text.lower()
            for term in query_terms:
                if term in text_lower:
                    df[term] += 1

        results: List[SearchResult] = []
        for chk, doc_id in chunks:
            words = [w.lower() for w in re.findall(r"\w+", chk.text)]
            dl = len(words)
            tf_map: Dict[str, int] = {}
            for w in words:
                tf_map[w] = tf_map.get(w, 0) + 1

            score = 0.0
            for term in query_terms:
                if term in tf_map:
                    tf = tf_map[term]
                    n_q = df[term]
                    idf = math.log((N - n_q + 0.5) / (n_q + 0.5) + 1.0)
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (dl / max(1.0, avg_dl)))
                    score += idf * (numerator / max(0.001, denominator))

            if score > 0.0:
                sec_title = chk.metadata.get("section_title") if isinstance(chk.metadata, dict) else None
                results.append(
                    SearchResult(
                        chunk_id=chk.chunk_id,
                        document_id=doc_id,
                        score=round(score, 4),
                        text=chk.text,
                        section_title=sec_title,
                        metadata=chk.metadata,
                    )
                )

        # Sort descending by score
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]
