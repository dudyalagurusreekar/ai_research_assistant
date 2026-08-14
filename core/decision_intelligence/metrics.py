"""Decision Metrics Engine — Observability and performance counters for Decision Intelligence."""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

from utils.logger import get_logger

logger = get_logger("DecisionMetricsEngine")


class DecisionMetricsEngine:
    """Thread-safe metrics collector for Decision Intelligence performance and evaluation analytics."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._total_requests: int = 0
        self._successful_requests: int = 0
        self._failed_requests: int = 0
        self._total_latency_ms: float = 0.0
        self._total_options_evaluated: int = 0
        self._total_evidence_items_aggregated: int = 0
        self._total_pareto_options_found: int = 0
        self._confidence_scores: List[float] = []
        self._risk_scores: List[float] = []

    def record_evaluation(
        self,
        success: bool,
        latency_ms: float,
        option_count: int = 0,
        evidence_count: int = 0,
        pareto_count: int = 0,
        top_confidence: float = 0.0,
        top_risk: float = 0.0,
    ) -> None:
        """Record telemetry for a decision evaluation execution."""
        with self._lock:
            self._total_requests += 1
            if success:
                self._successful_requests += 1
            else:
                self._failed_requests += 1

            self._total_latency_ms += latency_ms
            self._total_options_evaluated += option_count
            self._total_evidence_items_aggregated += evidence_count
            self._total_pareto_options_found += pareto_count

            if top_confidence > 0.0:
                self._confidence_scores.append(top_confidence)
            if top_risk > 0.0:
                self._risk_scores.append(top_risk)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary snapshot of decision metrics."""
        with self._lock:
            avg_latency = (
                self._total_latency_ms / self._total_requests
                if self._total_requests > 0
                else 0.0
            )
            avg_confidence = (
                sum(self._confidence_scores) / len(self._confidence_scores)
                if self._confidence_scores
                else 0.0
            )
            avg_risk = (
                sum(self._risk_scores) / len(self._risk_scores)
                if self._risk_scores
                else 0.0
            )

            return {
                "total_requests": self._total_requests,
                "successful_requests": self._successful_requests,
                "failed_requests": self._failed_requests,
                "success_rate": (
                    (self._successful_requests / self._total_requests)
                    if self._total_requests > 0
                    else 1.0
                ),
                "avg_latency_ms": round(avg_latency, 2),
                "total_options_evaluated": self._total_options_evaluated,
                "total_evidence_items_aggregated": self._total_evidence_items_aggregated,
                "total_pareto_options_found": self._total_pareto_options_found,
                "avg_confidence_score": round(avg_confidence, 3),
                "avg_risk_score": round(avg_risk, 3),
            }

    def reset(self) -> None:
        """Reset internal counter metrics."""
        with self._lock:
            self._total_requests = 0
            self._successful_requests = 0
            self._failed_requests = 0
            self._total_latency_ms = 0.0
            self._total_options_evaluated = 0
            self._total_evidence_items_aggregated = 0
            self._total_pareto_options_found = 0
            self._confidence_scores.clear()
            self._risk_scores.clear()
