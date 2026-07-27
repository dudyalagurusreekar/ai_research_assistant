"""Comprehensive Unit, Integration, Concurrency, and End-to-End Tests for Phase 10 Research Workflow Engine."""

import asyncio
import os
import pytest

from tools.workflow.facade.facade import WorkflowEngineFacade
from tools.workflow.models.workflow_models import (
    NormalizedWorkflow,
    WorkflowTask,
    TaskStatus,
    WorkflowState,
    WorkflowCheckpoint,
)
from tools.workflow.planner.workflow_planner import WorkflowPlanner
from tools.workflow.scheduler.task_scheduler import TaskScheduler
from tools.workflow.executor.workflow_executor import WorkflowExecutor
from tools.workflow.state.state_manager import WorkflowStateManager
from tools.workflow.context.context_coordinator import ContextCoordinator
from tools.workflow.decision.decision_engine import DecisionEngine
from tools.workflow.tracker.goal_tracker import GoalTracker
from tools.workflow.registry.workflow_registry import WorkflowRegistry
from tools.workflow.tool import WorkflowTool
from core.events import AsyncEventBus


def test_workflow_registry():
    """Verify reusable workflow template registration and lookup."""
    registry = WorkflowRegistry()
    templates = ["deep_research", "code_audit"]

    for name in templates:
        t_tasks = registry.get_template(name)
        assert t_tasks is not None
        assert len(t_tasks) >= 2


def test_workflow_planner():
    """Verify objective decomposition into DAG tasks."""
    async def _test():
        planner = WorkflowPlanner()
        wf = await planner.plan_workflow("Quantum Computing Research", template_name="deep_research")

        assert wf.workflow_id != ""
        assert len(wf.tasks) == 2
        assert wf.tasks[0].tool_name == "search_tool"
        assert wf.tasks[1].dependencies == [wf.tasks[0].task_id]

    asyncio.run(_test())


def test_task_scheduler():
    """Verify ready task dependency filtering."""
    scheduler = TaskScheduler()
    wf = NormalizedWorkflow(objective="Test Scheduler")

    t1 = WorkflowTask(title="Task 1", status=TaskStatus.PENDING)
    t2 = WorkflowTask(title="Task 2", status=TaskStatus.PENDING, dependencies=[t1.task_id])
    wf.tasks = [t1, t2]

    # Initially only t1 is ready
    ready1 = scheduler.get_ready_tasks(wf)
    assert len(ready1) == 1
    assert ready1[0].task_id == t1.task_id

    # Mark t1 as COMPLETED
    t1.status = TaskStatus.COMPLETED
    ready2 = scheduler.get_ready_tasks(wf)
    assert len(ready2) == 1
    assert ready2[0].task_id == t2.task_id


def test_workflow_state_manager():
    """Verify workflow state checkpointing and recovery snapshot."""
    async def _test():
        state_mgr = WorkflowStateManager()
        wf = NormalizedWorkflow(objective="Checkpoint Test")
        t1 = WorkflowTask(title="Task 1", status=TaskStatus.COMPLETED)
        wf.tasks = [t1]

        chk = await state_mgr.save_checkpoint(wf)
        assert chk.checkpoint_id != ""
        assert t1.task_id in chk.completed_task_ids

        restored = await state_mgr.load_checkpoint(chk.checkpoint_id)
        assert restored is not None
        assert restored.workflow_id == wf.workflow_id

    asyncio.run(_test())


def test_context_coordinator():
    """Verify context variable propagation across workflow tasks."""
    coord = ContextCoordinator()
    initial_ctx = {"objective": "Test Goal"}

    updated_ctx = coord.update_context(initial_ctx, {"search_result": "Found 10 papers"})
    assert updated_ctx["objective"] == "Test Goal"
    assert updated_ctx["search_result"] == "Found 10 papers"


def test_decision_engine():
    """Verify task outcome evaluation."""
    engine = DecisionEngine()
    t_success = WorkflowTask(status=TaskStatus.COMPLETED)
    t_failed = WorkflowTask(status=TaskStatus.FAILED)

    assert engine.evaluate_task_outcome(t_success) == "continue"
    assert engine.evaluate_task_outcome(t_failed) == "fail"


def test_goal_tracker():
    """Verify workflow progress percentage calculation."""
    tracker = GoalTracker()
    wf = NormalizedWorkflow()
    t1 = WorkflowTask(status=TaskStatus.COMPLETED)
    t2 = WorkflowTask(status=TaskStatus.PENDING)
    wf.tasks = [t1, t2]

    pct = tracker.update_progress(wf)
    assert pct == 50.0
    assert wf.metrics.completed_tasks == 1


def test_workflow_facade_end_to_end_and_events():
    """Verify WorkflowEngineFacade unified APIs, state checkpoints, and AsyncEventBus notifications."""
    async def _test():
        bus = AsyncEventBus()
        events_fired = []

        async def _on_event(evt):
            events_fired.append(evt.event_type)

        bus.subscribe("workflow.started", _on_event)
        bus.subscribe("task.started", _on_event)
        bus.subscribe("task.completed", _on_event)
        bus.subscribe("workflow.checkpointed", _on_event)
        bus.subscribe("workflow.completed", _on_event)

        facade = WorkflowEngineFacade(event_bus=bus)

        # 1. Create Workflow API
        wf = await facade.create_workflow("Autonomous AI Research", template_name="deep_research")
        assert wf.workflow_id != ""

        # 2. Run Workflow API
        run_wf = await facade.run_workflow(wf)
        assert run_wf.state == WorkflowState.COMPLETED

        # 3. Pause & Checkpoint API
        chk_wf = await facade.pause_workflow(wf.workflow_id)
        assert chk_wf.state == WorkflowState.PAUSED

        # Wait briefly for async events
        await asyncio.sleep(0.05)
        assert "workflow.started" in events_fired
        assert "task.started" in events_fired
        assert "task.completed" in events_fired
        assert "workflow.checkpointed" in events_fired
        assert "workflow.completed" in events_fired

        # Test forward JSON method
        forward_json = await facade.forward(action="create", objective="Forward Workflow Test")
        assert "workflow_id" in forward_json

    asyncio.run(_test())


def test_smolagents_workflow_tool_wrapper():
    """Verify smolagents WorkflowTool wrapper."""
    tool = WorkflowTool()
    res_str = tool.forward(action="create", objective="Smolagents workflow test")
    assert "workflow_id" in res_str
