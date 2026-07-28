"""Regression Engine comparing benchmark runs to detect improvements, regressions, and performance shifts."""

from typing import List
from tools.benchmark.interfaces.benchmark_interfaces import IRegressionEngine
from tools.benchmark.models.benchmark_models import (
    BenchmarkReportModel,
    RegressionReport,
)
from infrastructure.logging.logger import StructuredLogger


class RegressionEngine(IRegressionEngine):
    """Compares baseline and target evaluation executions to highlight accuracy improvements, regressions, and latency drifts."""

    def __init__(self, latency_drift_threshold_percent: float = 20.0) -> None:
        self._logger = StructuredLogger("RegressionEngine")
        self._drift_threshold = latency_drift_threshold_percent

    def compare_runs(
        self, baseline_report: BenchmarkReportModel, target_report: BenchmarkReportModel
    ) -> RegressionReport:
        """Compare baseline and target benchmark runs."""
        run_a_id = baseline_report.report_id
        run_b_id = target_report.report_id

        acc_a = baseline_report.metrics.accuracy_percentage
        acc_b = target_report.metrics.accuracy_percentage
        delta_acc = round(acc_b - acc_a, 2)

        improvements: List[str] = []
        regressions: List[str] = []
        stability_changes: List[str] = []
        perf_regressions: List[str] = []

        # Overall accuracy check
        if delta_acc > 0:
            improvements.append(f"Overall accuracy improved by +{delta_acc}% ({acc_a}% -> {acc_b}%)")
        elif delta_acc < 0:
            regressions.append(f"Overall accuracy regressed by {delta_acc}% ({acc_a}% -> {acc_b}%)")

        # Check latency drift
        lat_a = baseline_report.metrics.avg_latency_ms
        lat_b = target_report.metrics.avg_latency_ms
        if lat_a > 0:
            lat_change_percent = ((lat_b - lat_a) / lat_a) * 100.0
            if lat_change_percent > self._drift_threshold:
                perf_regressions.append(
                    f"Average latency increased by {round(lat_change_percent, 1)}% ({lat_a}ms -> {lat_b}ms)"
                )
            elif lat_change_percent < -10.0:
                improvements.append(
                    f"Average latency decreased by {round(abs(lat_change_percent), 1)}% ({lat_a}ms -> {lat_b}ms)"
                )

        # Failure category breakdown comparison
        err_a = baseline_report.error_breakdown
        err_b = target_report.error_breakdown
        for cat, count_b in err_b.items():
            count_a = err_a.get(cat, 0)
            if count_b > count_a:
                regressions.append(f"Failure category '{cat}' increased from {count_a} to {count_b} occurrences.")
            elif count_b < count_a:
                improvements.append(f"Failure category '{cat}' decreased from {count_a} to {count_b} occurrences.")

        summary = (
            f"Regression Analysis ({run_a_id} vs {run_b_id}): Delta Accuracy: {delta_acc}%. "
            f"Detected {len(improvements)} improvements, {len(regressions)} regressions, and "
            f"{len(perf_regressions)} performance regressions."
        )

        self._logger.info(summary)
        return RegressionReport(
            run_a_id=run_a_id,
            run_b_id=run_b_id,
            improvements=improvements,
            regressions=regressions,
            stability_changes=stability_changes,
            performance_regressions=perf_regressions,
            total_delta_accuracy=delta_acc,
            summary=summary,
        )
