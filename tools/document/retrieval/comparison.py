"""DocumentComparator implementation comparing structural and text metrics between NormalizedDocument objects."""

import re
import math
from typing import Set, Dict
from tools.document.interfaces.retrieval import IDocumentComparator
from tools.document.models.document import NormalizedDocument
from tools.document.models.retrieval import DocumentComparisonResult


class DocumentComparator(IDocumentComparator):
    """Compares two NormalizedDocument objects for textual and structural similarity."""

    async def compare(
        self,
        doc_a: NormalizedDocument,
        doc_b: NormalizedDocument,
    ) -> DocumentComparisonResult:
        """Compare structural and text differences between doc_a and doc_b."""
        words_a = set([w.lower() for w in re.findall(r"\w+", doc_a.full_text) if len(w) > 1])
        words_b = set([w.lower() for w in re.findall(r"\w+", doc_b.full_text) if len(w) > 1])

        # Jaccard Similarity
        intersection = words_a.intersection(words_b)
        union = words_a.union(words_b)
        jaccard = len(intersection) / max(1, len(union))

        # Cosine Similarity via Word Vector term frequencies
        tf_a = self._get_term_freq(doc_a.full_text)
        tf_b = self._get_term_freq(doc_b.full_text)
        all_terms = set(tf_a.keys()).union(set(tf_b.keys()))

        dot_product = sum(tf_a.get(t, 0) * tf_b.get(t, 0) for t in all_terms)
        norm_a = math.sqrt(sum(v * v for v in tf_a.values()))
        norm_b = math.sqrt(sum(v * v for v in tf_b.values()))
        cosine = dot_product / (max(0.001, norm_a) * max(0.001, norm_b))

        # Combined Similarity Score
        combined_score = round(0.5 * jaccard + 0.5 * cosine, 4)

        sec_diff = len(doc_a.sections) - len(doc_b.sections)
        tbl_diff = len(doc_a.tables) - len(doc_b.tables)
        img_diff = len(doc_a.images) - len(doc_b.images)

        summary_diff = (
            f"Similarity: {combined_score * 100:.1f}%. "
            f"Doc A has {len(words_a)} unique terms, Doc B has {len(words_b)}. "
            f"Shared terms: {len(intersection)}. "
            f"Section diff: {sec_diff}, Table diff: {tbl_diff}, Image diff: {img_diff}."
        )

        return DocumentComparisonResult(
            doc_a_id=doc_a.document_id,
            doc_b_id=doc_b.document_id,
            text_similarity_score=combined_score,
            jaccard_similarity=round(jaccard, 4),
            cosine_similarity=round(cosine, 4),
            common_words_count=len(intersection),
            doc_a_unique_words=len(words_a),
            doc_b_unique_words=len(words_b),
            section_count_diff=sec_diff,
            table_count_diff=tbl_diff,
            image_count_diff=img_diff,
            summary_diff=summary_diff,
        )

    def _get_term_freq(self, text: str) -> Dict[str, int]:
        freq: Dict[str, int] = {}
        for w in re.findall(r"\w+", text.lower()):
            if len(w) > 1:
                freq[w] = freq.get(w, 0) + 1
        return freq
