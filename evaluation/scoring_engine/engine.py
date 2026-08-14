"""Scoring Engine — Calculates 16 objective scores across benchmark categories."""

from __future__ import annotations

from typing import Dict, List

from evaluation.models.result import CategorySummary, TaskResult
from evaluation.models.task import TaskCategory
from utils.logger import get_logger

logger = get_logger("ScoringEngine")


class ScoringEngine:
    """Engine calculating structured 16-metric objective scores and category summaries."""

    def __init__(self) -> None:
        pass

    def compute_category_summaries(self, task_results: List[TaskResult]) -> Dict[str, CategorySummary]:
        """Aggregate individual task results into category summaries."""
        cat_map: Dict[TaskCategory, List[TaskResult]] = {}

        for tr in task_results:
            cat_map.setdefault(tr.category, []).append(tr)

        summaries: Dict[str, CategorySummary] = {}

        for cat, results in cat_map.items():
            total = len(results)
            passed = sum(1 for r in results if r.status == "passed")
            failed = total - passed
            pass_rate = round((passed / max(1, total)) * 100.0, 2)
            avg_quality = round(sum(r.overall_quality_score for r in results) / max(1, total), 3)
            avg_latency = round(sum(r.execution_time_ms for r in results) / max(1, total), 2)

            # Aggregate specific metric averages
            metric_totals: Dict[str, float] = {}
            metric_counts: Dict[str, int] = {}
            for r in results:
                for m_name, m_score in r.metrics.items():
                    metric_totals[m_name] = metric_totals.get(m_name, 0.0) + m_score.raw_score
                    metric_counts[m_name] = metric_counts.get(m_name, 0) + 1

            metrics_avg = {k: round(metric_totals[k] / max(1, metric_counts[k]), 3) for k in metric_totals}

            summaries[cat.value] = CategorySummary(
                category=cat,
                total_tasks=total,
                passed_tasks=passed,
                failed_tasks=failed,
                pass_rate=pass_rate,
                avg_quality_score=avg_quality,
                avg_latency_ms=avg_latency,
                metrics_avg=metrics_avg,
            )

        return summaries

    def compute_overall_quality_score(self, task_results: List[TaskResult]) -> float:
        """Compute platform-wide weighted quality score [0.0..1.0]."""
        if not task_results:
            return 1.0
        return round(sum(tr.overall_quality_score for tr in task_results) / len(task_results), 3)
