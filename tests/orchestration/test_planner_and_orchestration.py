"""Unit and Integration Tests for Sprint 5 — AI Orchestration, Planning, and Reasoning Platform."""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
from fastapi.testclient import TestClient
from services.api.app import app
from infrastructure.database.connection import DatabaseManager
from infrastructure.database.models import Base
from infrastructure.database.seed import seed_database
from core.auth.dependencies import get_db_session

from core.planner.orchestration_planner import OrchestrationPlanner
from core.prompts.manager import PromptManager, PromptTemplate
from core.orchestration.orchestrator import IntelligentLLMOrchestrator
from core.orchestration.models.request import LLMRequest
from core.workflow.executor import DAGWorkflowExecutor

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    manager = DatabaseManager("sqlite:///:memory:")
    manager.create_all_tables(Base)
    session = manager.SessionLocal()
    seed_database(session=session)

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_get_db
    yield
    app.dependency_overrides.clear()
    session.close()
    manager.drop_all_tables(Base)


def get_auth_headers():
    reg_res = client.post("/api/v1/auth/register", json={
        "email": "planner_user@ara-research.org",
        "password": "PlannerPassword123!",
        "full_name": "Planner User",
    })
    token = client.post("/api/v1/auth/login", json={
        "email": "planner_user@ara-research.org",
        "password": "PlannerPassword123!",
    }).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_prompt_manager_template_registration_and_rendering():
    pm = PromptManager()
    tpl = PromptTemplate(
        name="custom_eval",
        version="1.0.0",
        description="Custom evaluation prompt",
        template_text="Evaluate model: {model_name} on task: {task_id}.",
        default_variables={"model_name": "gemini-2.5-pro", "task_id": "T001"},
    )
    pm.register_template(tpl)
    rendered = pm.render("custom_eval", {"task_id": "T999"})
    assert "gemini-2.5-pro" in rendered
    assert "T999" in rendered


def test_llm_orchestrator_multi_provider_routing_and_caching():
    orchestrator = IntelligentLLMOrchestrator()
    
    # Request 1 (Low complexity)
    req_flash = LLMRequest(prompt="Summarize recent papers in QML", task_type="general_qa", complexity_score=2)
    res_flash = orchestrator.generate(req_flash)
    assert res_flash.model_id is not None
    assert len(res_flash.text) > 0

    # Request 2 (High complexity -> Pro model)
    req_pro = LLMRequest(prompt="Synthesize quantum error correction proofs", task_type="research", complexity_score=9)
    res_pro = orchestrator.generate(req_pro)
    assert "gemini-2.5-pro" in res_pro.model_id
    assert "[Google Gemini 2.5 Pro]" in res_pro.text



def test_orchestration_planner_dag_generation_and_workflow_execution():
    planner = OrchestrationPlanner()
    ctx = planner.create_plan(
        query="Synthesize latest developments in multi-agent graph neural networks",
    )
    assert ctx.plan_id is not None
    assert len(ctx.sub_tasks) > 0
    assert len(ctx.parallel_levels) > 0

    executor = DAGWorkflowExecutor()
    results = executor.execute_plan(ctx)
    assert results["status"] in ["completed", "degraded"]
    assert results["total_tasks"] == len(ctx.sub_tasks)
    assert results["completed_count"] > 0


def test_planner_api_plan_endpoint():
    headers = get_auth_headers()
    res = client.post(
        "/api/v1/planner/plan",
        json={"query": "Perform competitive benchmark analysis of LLM inference engines"},
        headers=headers,
    )
    assert res.status_code == 201
    env = res.json()
    assert env["success"] is True
    assert "plan_id" in env["data"]
    assert len(env["data"]["sub_tasks"]) > 0
    assert len(env["data"]["execution_waves"]) > 0


def test_orchestration_api_llm_generate_and_execution_endpoints():
    headers = get_auth_headers()

    # 1. LLM Generation Endpoint
    gen_res = client.post(
        "/api/v1/orchestration/llm/generate",
        json={"prompt": "Explain topological quantum computing", "complexity_score": 8},
        headers=headers,
    )
    assert gen_res.status_code == 200
    gen_env = gen_res.json()
    assert gen_env["success"] is True
    assert "gemini-2.5-pro" in gen_env["data"]["model_id"]


    # 2. Plan Execution Endpoint
    exec_res = client.post(
        "/api/v1/orchestration/execute",
        json={"query": "Automate systematic literature review for Alzheimer therapy"},
        headers=headers,
    )
    assert exec_res.status_code == 200
    exec_env = exec_res.json()
    assert exec_env["success"] is True
    assert exec_env["data"]["completed_count"] > 0

    # 3. Telemetry Endpoint
    telem_res = client.get("/api/v1/orchestration/telemetry", headers=headers)
    assert telem_res.status_code == 200
    telem_env = telem_res.json()
    assert telem_env["success"] is True
    assert "registry" in telem_env["data"]
