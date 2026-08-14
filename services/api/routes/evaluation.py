"""REST API Router for Evaluation, Benchmarking, Observability, and Quality Assurance Platform (/api/v1/evaluation)."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from core.auth.dependencies import get_current_user
from evaluation.benchmark_engine.engine import EvaluationEngine
from infrastructure.database.models.auth import User
from services.api.schemas.envelope import ResponseEnvelope

router = APIRouter(prefix="/evaluation", tags=["Evaluation, Benchmarking & QA Platform"])

# Singleton EvaluationEngine instance
_eval_engine: Optional[EvaluationEngine] = None


def get_eval_engine() -> EvaluationEngine:
    """Get or create singleton EvaluationEngine instance."""
    global _eval_engine
    if _eval_engine is None:
        _eval_engine = EvaluationEngine()
    return _eval_engine


# --- Request/Response Schemas ---

class RunEvaluationRequest(BaseModel):
    mode: str = Field(default="fast", description="Evaluation run mode: 'fast' or 'full'")
    category_filter: Optional[str] = Field(default=None, description="Optional TaskCategory filter")


class CompareBaselineRequest(BaseModel):
    current_run: dict = Field(..., description="Current evaluation run report dict")
    tag: str = Field(default="golden", description="Golden baseline tag to compare against")
    tolerance_pct: float = Field(default=5.0, ge=0.0, le=50.0, description="Tolerance percentage drop before flagging regression")


# --- Endpoints ---

@router.get("/health")
async def evaluation_health():
    """Evaluation engine health check probe."""
    return ResponseEnvelope(data={"status": "healthy", "version": "1.0.0"}, message="Evaluation engine healthy")


@router.post("/run", status_code=status.HTTP_201_CREATED)
async def run_evaluation_suite(
    body: RunEvaluationRequest,
    current_user: User = Depends(get_current_user),
):
    """Trigger full or fast evaluation suite run, enforce release gates, and generate reports."""
    engine = get_eval_engine()
    report = engine.run_evaluation_suite(mode=body.mode, category_filter=body.category_filter)
    return ResponseEnvelope(
        data=report.to_dict(),
        message=f"Evaluation run completed. Verdict: {report.verdict.status.value.upper()}. Release Approved: {report.verdict.release_approved}",
    )


@router.get("/reports/latest")
async def get_latest_report(
    current_user: User = Depends(get_current_user),
):
    """Retrieve the latest evaluation report."""
    engine = get_eval_engine()
    report = engine.run_evaluation_suite(mode="fast")
    return ResponseEnvelope(data=report.to_dict(), message="Latest evaluation report retrieved")


@router.get("/metrics")
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
):
    """Retrieve aggregated dashboard quality, pass rate, and category metrics."""
    engine = get_eval_engine()
    report = engine.run_evaluation_suite(mode="fast")
    return ResponseEnvelope(data=report.dashboard_metrics.to_dict(), message="Evaluation metrics retrieved")


@router.get("/gates")
async def check_release_gates(
    current_user: User = Depends(get_current_user),
):
    """Check release gate status and verdict."""
    engine = get_eval_engine()
    report = engine.run_evaluation_suite(mode="fast")
    return ResponseEnvelope(data=report.verdict.to_dict(), message=f"Release Gate Verdict: {report.verdict.status.value.upper()}")


@router.get("/leaderboard")
async def get_leaderboard(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """Retrieve run history leaderboard."""
    engine = get_eval_engine()
    runs = engine.leaderboard_manager.list_runs()[:limit]
    return ResponseEnvelope(data=[r.to_dict() for r in runs], message=f"Retrieved {len(runs)} leaderboard runs")


@router.get("/prometheus", response_class=Response)
async def get_prometheus_metrics():
    """Prometheus metrics scrape endpoint (returns raw text/plain exposition format)."""
    engine = get_eval_engine()
    # Trigger metric collection
    engine.run_evaluation_suite(mode="fast")
    metrics_text = engine.export_prometheus_metrics()
    return Response(content=metrics_text, media_type="text/plain; version=0.0.4; charset=utf-8")


@router.get("/dashboard/grafana")
async def get_grafana_dashboard_spec(
    current_user: User = Depends(get_current_user),
):
    """Retrieve Grafana JSON dashboard specification."""
    engine = get_eval_engine()
    spec = engine.get_grafana_dashboard_spec()
    return ResponseEnvelope(data=spec, message="Grafana dashboard specification retrieved")


@router.post("/regression/compare")
async def compare_baseline_regression(
    body: CompareBaselineRequest,
    current_user: User = Depends(get_current_user),
):
    """Compare current evaluation run metrics against historical golden baseline."""
    engine = get_eval_engine()
    report = engine.regression_tracker.compare_with_baseline(
        current_run=body.current_run,
        tag=body.tag,
        tolerance_pct=body.tolerance_pct,
    )
    return ResponseEnvelope(data=report.model_dump(), message=f"Regression analysis complete. Has Regression: {report.has_regression}")
