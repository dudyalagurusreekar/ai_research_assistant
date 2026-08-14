"""Regression Tracker — Historical golden baseline storage and regression detection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from evaluation.models.result import TaskResult
from utils.logger import get_logger

logger = get_logger("RegressionTracker")


class RegressionReport(BaseModel):
    """Detailed comparison report between current evaluation run and golden baseline."""

    has_regression: bool = Field(default=False, description="True if any metrics degraded beyond tolerance")
    quality_delta: float = Field(default=0.0, description="Current quality score - Baseline quality score")
    pass_rate_delta: float = Field(default=0.0, description="Current pass rate % - Baseline pass rate %")
    latency_delta_ms: float = Field(default=0.0, description="Current latency ms - Baseline latency ms")
    degraded_categories: List[str] = Field(default_factory=list, description="Categories showing metric degradation")
    degraded_metrics: Dict[str, float] = Field(default_factory=dict, description="Metric degradation details")
    details: Dict[str, Any] = Field(default_factory=dict, description="Summary details")


class RegressionTracker:
    """Manages baseline persistence and performs automated regression detection."""

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        self.storage_dir = Path(storage_dir) if storage_dir else Path.cwd() / ".storage" / "evaluation" / "baselines"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_baseline(self, run_id: str, report_dict: Dict[str, Any], tag: str = "golden") -> Path:
        """Save an approved evaluation run as a golden baseline."""
        file_path = self.storage_dir / f"baseline_{tag}.json"
        file_path.write_text(json.dumps(report_dict, indent=2), encoding="utf-8")
        logger.info(f"RegressionTracker saved baseline '{tag}' ({run_id}) to {file_path}")
        return file_path

    def load_baseline(self, tag: str = "golden") -> Optional[Dict[str, Any]]:
        """Load a golden baseline evaluation run."""
        file_path = self.storage_dir / f"baseline_{tag}.json"
        if not file_path.exists():
            logger.warning(f"Baseline file {file_path} does not exist")
            return None
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.error(f"Failed to read baseline file {file_path}: {exc}")
            return None

    def compare_with_baseline(
        self, current_run: Dict[str, Any], tag: str = "golden", tolerance_pct: float = 5.0
    ) -> RegressionReport:
        """Compare current evaluation run metrics against baseline and detect regressions."""
        baseline = self.load_baseline(tag=tag)
        if not baseline:
            # First run scenario: no baseline to regress against
            return RegressionReport(has_regression=False, details={"info": "No prior baseline found for comparison"})

        b_metrics = baseline.get("dashboard_metrics", {})
        c_metrics = current_run.get("dashboard_metrics", {})

        b_quality = b_metrics.get("overall_quality_score", 1.0)
        c_quality = c_metrics.get("overall_quality_score", 1.0)
        quality_delta = round(c_quality - b_quality, 4)

        b_pass = b_metrics.get("overall_pass_rate", 100.0)
        c_pass = c_metrics.get("overall_pass_rate", 100.0)
        pass_delta = round(c_pass - b_pass, 2)

        b_lat = b_metrics.get("avg_latency_ms", 0.0)
        c_lat = c_metrics.get("avg_latency_ms", 0.0)
        lat_delta = round(c_lat - b_lat, 2)

        degraded_categories = []
        degraded_metrics = {}
        has_reg = False

        # Quality drop exceeding tolerance threshold (e.g. > 5%)
        if quality_delta < -(tolerance_pct / 100.0):
            has_reg = True
            degraded_metrics["overall_quality_score"] = quality_delta

        if pass_delta < -tolerance_pct:
            has_reg = True
            degraded_metrics["overall_pass_rate"] = pass_delta

        # Category level checks
        b_cats = baseline.get("category_summaries", {})
        c_cats = current_run.get("category_summaries", {})

        for cat_name, c_cat_info in c_cats.items():
            b_cat_info = b_cats.get(cat_name, {})
            b_cat_pass = b_cat_info.get("pass_rate", 100.0)
            c_cat_pass = c_cat_info.get("pass_rate", 100.0)

            if (c_cat_pass - b_cat_pass) < -tolerance_pct:
                has_reg = True
                degraded_categories.append(cat_name)

        report = RegressionReport(
            has_regression=has_reg,
            quality_delta=quality_delta,
            pass_rate_delta=pass_delta,
            latency_delta_ms=lat_delta,
            degraded_categories=degraded_categories,
            degraded_metrics=degraded_metrics,
            details={
                "baseline_quality": b_quality,
                "current_quality": c_quality,
                "baseline_pass_rate": b_pass,
                "current_pass_rate": c_pass,
            },
        )
        logger.info(f"Regression comparison complete. Has Regression: {has_reg}")
        return report
