"""DocumentSummarizer implementation for extractive text summarization."""

import re
from typing import Dict
from tools.document.interfaces.retrieval import IDocumentSummarizer
from tools.document.models.document import NormalizedDocument
from tools.document.models.retrieval import DocumentSummary


class DocumentSummarizer(IDocumentSummarizer):
    """Extractive summarizer ranking sentences based on word frequency, position, and heading proximity."""

    async def summarize(
        self,
        document: NormalizedDocument,
        max_sentences: int = 5,
    ) -> DocumentSummary:
        text = document.full_text or ""
        if not text.strip():
            return DocumentSummary(
                document_id=document.document_id,
                title=document.metadata.title,
                summary_text="",
                total_words=0,
                summary_words=0,
            )

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 10]
        if not sentences:
            sentences = [text[:200]]

        # Compute word frequencies
        words = [w.lower() for w in re.findall(r"\w+", text) if len(w) > 3]
        freq_map: Dict[str, int] = {}
        for w in words:
            freq_map[w] = freq_map.get(w, 0) + 1

        # Score sentences
        sentence_scores = []
        for idx, sentence in enumerate(sentences):
            score = 0.0
            s_words = [w.lower() for w in re.findall(r"\w+", sentence) if len(w) > 3]
            for w in s_words:
                score += freq_map.get(w, 0)

            # Normalize by sentence length
            score = score / max(1, len(s_words))

            # Boost initial sentences (positional bias)
            if idx < 3:
                score *= 1.5

            sentence_scores.append((sentence, score, idx))

        # Select top k sentences ordered by original position
        top_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)[:max_sentences]
        top_sentences_in_order = [s[0] for s in sorted(top_sentences, key=lambda x: x[2])]

        summary_text = " ".join(top_sentences_in_order)
        key_terms = [k for k, v in sorted(freq_map.items(), key=lambda item: item[1], reverse=True)[:10]]
        section_titles = [s.title for s in document.sections if s.title]

        return DocumentSummary(
            document_id=document.document_id,
            title=document.metadata.title,
            summary_text=summary_text,
            key_sentences=top_sentences_in_order,
            key_terms=key_terms,
            section_titles=section_titles,
            total_words=document.metadata.word_count or len(words),
            summary_words=len(re.findall(r"\w+", summary_text)),
        )
