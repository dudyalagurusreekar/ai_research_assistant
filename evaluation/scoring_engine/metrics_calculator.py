"""Metrics Calculator — Automated evaluation metric algorithms for IR, RAG, Reasoning, Observability, and Calibration."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Sequence, Tuple
from utils.logger import get_logger

logger = get_logger("MetricsCalculator")


def recall_at_k(retrieved: Sequence[str], relevant: Sequence[str], k: int = 5) -> float:
    """Calculate Recall@K: proportion of relevant items retrieved in top K."""
    if not relevant:
        return 1.0
    top_k = retrieved[:k]
    relevant_set = {str(r).lower().strip() for r in relevant}
    matched = sum(1 for item in top_k if str(item).lower().strip() in relevant_set)
    return round(matched / len(relevant_set), 4)


def precision_at_k(retrieved: Sequence[str], relevant: Sequence[str], k: int = 5) -> float:
    """Calculate Precision@K: proportion of retrieved top K items that are relevant."""
    if not retrieved or k <= 0:
        return 0.0
    top_k = retrieved[:k]
    relevant_set = {str(r).lower().strip() for r in relevant}
    matched = sum(1 for item in top_k if str(item).lower().strip() in relevant_set)
    return round(matched / len(top_k), 4)


def mean_reciprocal_rank(retrieved: Sequence[str], relevant: Sequence[str]) -> float:
    """Calculate Reciprocal Rank (MRR): 1 / rank of first relevant item."""
    if not retrieved or not relevant:
        return 0.0
    relevant_set = {str(r).lower().strip() for r in relevant}
    for rank, item in enumerate(retrieved, start=1):
        if str(item).lower().strip() in relevant_set:
            return round(1.0 / rank, 4)
    return 0.0


def ndcg_at_k(retrieved: Sequence[str], relevant: Sequence[str], k: int = 5) -> float:
    """Calculate Normalized Discounted Cumulative Gain (nDCG@K)."""
    if not retrieved or not relevant or k <= 0:
        return 0.0

    relevant_set = {str(r).lower().strip() for r in relevant}
    dcg = 0.0
    for i, item in enumerate(retrieved[:k]):
        rel = 1.0 if str(item).lower().strip() in relevant_set else 0.0
        dcg += rel / math.log2(i + 2)

    # Ideal DCG: all top items are relevant up to min(k, len(relevant))
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(k, len(relevant_set))))
    if idcg == 0.0:
        return 0.0
    return round(dcg / idcg, 4)


def groundedness_score(claims: Sequence[str], evidence_sources: Sequence[str]) -> float:
    """Calculate Groundedness score [0.0..1.0]: percentage of claims supported by evidence."""
    if not claims:
        return 1.0
    if not evidence_sources:
        return 0.0

    evidence_text = " ".join(evidence_sources).lower()
    supported = 0
    for claim in claims:
        words = set(w.lower() for w in claim.split() if len(w) > 3)
        if not words:
            supported += 1
            continue
        overlap = sum(1 for w in words if w in evidence_text)
        if (overlap / len(words)) >= 0.4:
            supported += 1

    return round(supported / len(claims), 4)


def citation_accuracy_score(citations: Sequence[str], source_docs: Sequence[str]) -> float:
    """Calculate Citation Accuracy score [0.0..1.0]."""
    if not citations:
        return 1.0
    if not source_docs:
        return 0.0

    valid_docs = {str(d).lower().strip() for d in source_docs}
    valid_citations = sum(1 for c in citations if any(vd in str(c).lower() for vd in valid_docs))
    return round(valid_citations / len(citations), 4)


def hallucination_rate_score(text: str, context_sources: Sequence[str]) -> float:
    """Calculate Hallucination Rate [0.0..1.0] (0 = no hallucination, 1 = ungrounded)."""
    if not text:
        return 0.0
    sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 10]
    if not sentences:
        return 0.0

    grounded = groundedness_score(sentences, context_sources)
    hallucination_rate = max(0.0, 1.0 - grounded)
    return round(hallucination_rate, 4)


def reasoning_quality_score(plan_steps: Sequence[str], execution_trace: Sequence[str]) -> float:
    """Calculate Reasoning Quality score based on plan completion and trace coherence."""
    if not plan_steps:
        return 1.0
    if not execution_trace:
        return 0.0

    trace_text = " ".join(execution_trace).lower()
    completed = 0
    for step in plan_steps:
        keywords = set(w.lower() for w in step.split() if len(w) > 3)
        if not keywords or any(kw in trace_text for kw in keywords):
            completed += 1

    return round(completed / len(plan_steps), 4)


def expected_calibration_error(
    confidences: Sequence[float], accuracies: Sequence[int], num_bins: int = 10
) -> float:
    """Calculate Expected Calibration Error (ECE) [0.0..1.0]."""
    if not confidences or len(confidences) != len(accuracies):
        return 0.0

    N = len(confidences)
    bin_boundaries = [i / num_bins for i in range(num_bins + 1)]
    ece = 0.0

    for i in range(num_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        # Identify items in bin
        bin_indices = [
            j for j, conf in enumerate(confidences)
            if bin_lower <= conf < bin_upper or (i == num_bins - 1 and conf == bin_upper)
        ]

        if bin_indices:
            bin_size = len(bin_indices)
            avg_confidence = sum(confidences[j] for j in bin_indices) / bin_size
            avg_accuracy = sum(accuracies[j] for j in bin_indices) / bin_size
            ece += (bin_size / N) * abs(avg_accuracy - avg_confidence)

    return round(ece, 4)
