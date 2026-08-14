"""Unit tests for Workflow Recorder & Replay Executor."""

import asyncio
import pytest
from core.browser.workflow_engine import WorkflowRecorder, WorkflowExecutor


def test_workflow_recording_and_export():
    recorder = WorkflowRecorder(name="PubMed Search Workflow", description="Search & Extract Literature")
    recorder.record_step("NAVIGATE", target_url="https://pubmed.ncbi.nlm.nih.gov")
    recorder.record_step("TYPE", selector="#search-input", value="{{query}}")
    recorder.record_step("CLICK", selector="#search-btn")
    recorder.record_step("EXTRACT")

    definition = recorder.export_definition()
    assert definition.name == "PubMed Search Workflow"
    assert len(definition.steps) == 4
    assert definition.steps[1].value == "{{query}}"


def test_workflow_executor_replay():
    async def _test():
        recorder = WorkflowRecorder(name="Replay Test")
        recorder.record_step("NAVIGATE", target_url="{{search_url}}")
        recorder.record_step("EXTRACT")
        definition = recorder.export_definition()

        executor = WorkflowExecutor()
        session = {"session_id": "bs_wf_test", "page": None, "current_url": "about:blank", "history": []}
        
        result = await executor.execute_workflow(
            session,
            definition,
            variables={"search_url": "https://ncbi.nlm.nih.gov/crispr"},
        )

        assert result["status"] == "completed"
        assert result["executed_steps"] == 2
        assert result["step_results"][0]["details"]["url"] == "https://ncbi.nlm.nih.gov/crispr"

    asyncio.run(_test())
