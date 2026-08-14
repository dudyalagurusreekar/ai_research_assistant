"""REST API Router for AI Planning and Reasoning Engine (/api/v1/planner)."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field

from core.auth.dependencies import get_current_user
from infrastructure.database.models.auth import User
from services.api.schemas.envelope import ResponseEnvelope
from core.planner.orchestration_planner import orchestration_planner

router = APIRouter(prefix="/planner", tags=["AI Planning & Reasoning Engine"])


class CreatePlanRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    available_tools: Optional[List[Dict[str, Any]]] = None


@router.post("/plan", status_code=status.HTTP_201_CREATED)
def generate_execution_plan(
    req: CreatePlanRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Deconstruct query, estimate complexity, generate DAG, and select tools."""
    ctx = orchestration_planner.create_plan(
        query=req.query,
        available_tools=req.available_tools,
        session_id=req.session_id,
    )

    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={
            "plan_id": ctx.plan_id,
            "session_id": ctx.session_id,
            "intent": ctx.intent.value if ctx.intent else "unknown",
            "complexity_score": ctx.complexity_score,
            "stage": ctx.current_stage.value,


            "sub_tasks": [
                {
                    "task_id": t.task_id,
                    "title": t.title,
                    "description": t.description,
                    "task_type": str(getattr(t, "task_type", getattr(t, "action", "general_qa"))),
                    "estimated_complexity": getattr(t, "estimated_complexity", 5),

                }
                for t in ctx.sub_tasks
            ],
            "execution_waves": [
                [t.task_id for t in wave] for wave in ctx.parallel_levels
            ],
            "selected_tools": ctx.selected_tools,
            "metrics": {
                "planning_latency_ms": ctx.metrics.planning_latency_ms,
                "sub_task_count": len(ctx.sub_tasks),
                "waves_count": len(ctx.parallel_levels),
            },
        },
        correlation_id=correlation_id,
    )
