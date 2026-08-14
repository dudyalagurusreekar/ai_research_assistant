"""REST API Router for Multi-Provider LLM Orchestration & Execution (/api/v1/orchestration)."""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field

from core.auth.dependencies import get_current_user
from infrastructure.database.models.auth import User
from services.api.schemas.envelope import ResponseEnvelope
from core.planner.orchestration_planner import orchestration_planner
from core.orchestration.orchestrator import IntelligentLLMOrchestrator
from core.orchestration.models.request import LLMRequest
from core.workflow.executor import dag_workflow_executor

router = APIRouter(prefix="/orchestration", tags=["AI Orchestration & Multi-Provider LLM Router"])

llm_orchestrator = IntelligentLLMOrchestrator()


class LLMGenerateRequest(BaseModel):
    prompt: str
    task_type: Optional[str] = "general_qa"
    complexity_score: Optional[int] = 5
    bypass_cache: Optional[bool] = False


class ExecutePlanRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    max_retries: Optional[int] = 3


@router.post("/llm/generate", status_code=status.HTTP_200_OK)
def generate_llm_response(
    req: LLMGenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Route request dynamically across LLM providers with caching, failover, and telemetry."""
    llm_req = LLMRequest(
        prompt=req.prompt,
        task_type=req.task_type or "general_qa",
        complexity_score=req.complexity_score or 5,
    )
    
    if req.bypass_cache:
        llm_orchestrator.policy.enable_response_caching = False

    resp = llm_orchestrator.generate(llm_req)

    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={
            "request_id": resp.request_id,
            "text": resp.text,
            "model_id": resp.model_id,
            "provider_type": resp.provider_type,
            "latency_ms": resp.latency_ms,
            "prompt_tokens": resp.prompt_tokens,
            "completion_tokens": resp.completion_tokens,
            "total_cost": resp.total_cost,
            "error_message": resp.error_message,
        },
        correlation_id=correlation_id,
    )


@router.post("/execute", status_code=status.HTTP_200_OK)
def execute_research_plan(
    req: ExecutePlanRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Deconstruct query into execution DAG waves and concurrently run workflow tasks."""
    plan_ctx = orchestration_planner.create_plan(
        query=req.query,
        session_id=req.session_id,
    )
    
    execution_result = dag_workflow_executor.execute_plan(
        plan_ctx,
        max_retries=req.max_retries or 3,
    )

    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data=execution_result,
        correlation_id=correlation_id,
    )


@router.get("/telemetry", status_code=status.HTTP_200_OK)
def get_orchestration_telemetry(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Return unified LLM orchestrator metrics, provider health, cache statistics, and routing policy."""
    telemetry = llm_orchestrator.get_telemetry_summary()
    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data=telemetry,
        correlation_id=correlation_id,
    )
