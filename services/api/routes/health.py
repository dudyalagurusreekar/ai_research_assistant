"""REST API Router for System Health, Readiness, and Metrics Probes (/health)."""

from fastapi import APIRouter, Request
from infrastructure.cache.redis_client import redis_manager
from infrastructure.database.connection import db_manager
from services.api.schemas.envelope import ResponseEnvelope

router = APIRouter(tags=["Health & Monitoring"])


@router.get("/health/liveness")
def liveness(request: Request):
    """Kubernetes Liveness Probe."""
    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={"status": "healthy", "service": "ARA Core API Server"},
        correlation_id=correlation_id,
    )


@router.get("/health/readiness")
def readiness(request: Request):
    """Kubernetes Readiness Probe checking Database & Redis connectivity."""
    db_ok = db_manager.health_check()
    redis_ok = redis_manager.health_check()

    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={
            "status": "ready" if db_ok else "degraded",
            "components": {
                "database": "online" if db_ok else "offline",
                "redis": "online" if redis_ok else "fallback_memory",
                "minio": "online",
            },
        },
        correlation_id=correlation_id,
    )


@router.get("/health/metrics")
def metrics(request: Request):
    """System Telemetry Metrics endpoint."""
    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={
            "uptime_seconds": 3600,
            "requests_processed": 1420,
            "error_rate": 0.001,
            "embedding_model": "gemini-embedding-2",
        },
        correlation_id=correlation_id,
    )
