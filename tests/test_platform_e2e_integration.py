"""End-to-End Interoperability Test Suite validating integration across all 12 platform pillars."""

import asyncio
import os
import tempfile
import pytest

from core.orchestrator import SessionOrchestrator
from core.events import AsyncEventBus
from core.dependency import DependencyContainer
from tools.browser.facade.facade import BrowserToolFacade
from tools.document.facade.facade import DocumentToolFacade
from tools.search.facade.facade import SearchToolFacade
from tools.memory.facade.facade import MemoryToolFacade
from tools.code.facade.facade import CodeToolFacade
from tools.vision.facade.facade import VisionToolFacade
from tools.integration.facade.facade import IntegrationToolFacade
from tools.workflow.facade.facade import WorkflowEngineFacade
from tools.report.facade.facade import ReportToolFacade
from tools.benchmark.facade.facade import BenchmarkToolFacade
from tools.registry import registry


def test_platform_e2e_integration_flow():
    """Validate end-to-end multi-platform workflow across all 12 integrated phases."""
    async def _test():
        event_bus = AsyncEventBus()
        events_received = []

        async def _capture_event(event):
            events_received.append(event.event_type)

        # Subscribe to key domain events across all platforms
        event_bus.subscribe("search.started", _capture_event)
        event_bus.subscribe("document.parsed", _capture_event)
        event_bus.subscribe("memory.created", _capture_event)
        event_bus.subscribe("code.indexed", _capture_event)
        event_bus.subscribe("execution.completed", _capture_event)
        event_bus.subscribe("vision.started", _capture_event)
        event_bus.subscribe("integration.started", _capture_event)
        event_bus.subscribe("workflow.started", _capture_event)
        event_bus.subscribe("report.started", _capture_event)
        event_bus.subscribe("benchmark.started", _capture_event)
        event_bus.subscribe("benchmark.completed", _capture_event)

        # Initialize platform facades
        doc_facade = DocumentToolFacade(event_bus=event_bus)
        search_facade = SearchToolFacade(event_bus=event_bus, document_facade=doc_facade)
        memory_facade = MemoryToolFacade(event_bus=event_bus)
        code_facade = CodeToolFacade(event_bus=event_bus, memory_facade=memory_facade)
        vision_facade = VisionToolFacade(event_bus=event_bus, memory_facade=memory_facade, document_facade=doc_facade)
        integration_facade = IntegrationToolFacade(event_bus=event_bus, memory_facade=memory_facade)
        workflow_facade = WorkflowEngineFacade(event_bus=event_bus)
        report_facade = ReportToolFacade(event_bus=event_bus, memory_facade=memory_facade)
        benchmark_facade = BenchmarkToolFacade(event_bus=event_bus)

        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Create source code repository (Phase 7 Code Tool)
            sample_code_path = os.path.join(tmpdir, "main.py")
            with open(sample_code_path, "w", encoding="utf-8") as f:
                f.write("class ResearchAssistant:\n    def run(self):\n        return 'Executing research'\n")

            # 2. Index project and resolve symbols (Phase 7)
            proj = await code_facade.index_project(tmpdir)
            assert proj.total_files == 1

            # 3. Execute sandboxed code snippet (Phase 7)
            exec_res = await code_facade.execute_code("print('Sandboxed Execution OK')")
            assert exec_res.status == "success"

            # 4. Perform multi-provider search (Phase 5)
            search_res = await search_facade.search("Artificial Intelligence research paper filetype:pdf")
            assert len(search_res.results) > 0

            # 5. Ingest search results into Memory Platform (Phase 6)
            mem_items = await memory_facade.ingest_search_results(search_res)
            assert len(mem_items) > 0

            # 6. Parse document (Phase 4)
            sample_doc_path = os.path.join(tmpdir, "paper.txt")
            with open(sample_doc_path, "w", encoding="utf-8") as f:
                f.write("# Quantum Computing Study\n\nAbstract: Quantum algorithms enhance research efficiency.")
            
            doc_obj = await doc_facade.parse_document(sample_doc_path)
            assert doc_obj.metadata.title != ""

            # 7. Ingest document into Memory Platform (Phase 6)
            doc_mems = await memory_facade.ingest_document(doc_obj)
            assert len(doc_mems) > 0

            # 8. Visual Screenshot & OCR Analysis (Phase 8 Vision Tool)
            screenshot_path = os.path.join(tmpdir, "viewport.png")
            with open(screenshot_path, "wb") as f:
                f.write(b"dummy_png_bytes")
            
            ss_res = await vision_facade.analyze_screenshot(screenshot_path)
            assert len(ss_res.detected_regions) > 0

            # 9. External Integration APIs (Phase 9 Integration Tool)
            ext_res = await integration_facade.query_rest("https://api.example.com/v1/status")
            assert ext_res.success is True

            # 10. Autonomous Research Workflow Engine (Phase 10 Workflow Tool)
            wf = await workflow_facade.create_workflow("Autonomous AI Research", template_name="deep_research")
            run_wf = await workflow_facade.run_workflow(wf)
            assert run_wf.state.value == "completed"

            # 11. Final Deliverable Report Generation (Phase 11 Report Tool)
            rep = await report_facade.compose_report("AI Research Assistant Deliverable", template_name="research_report")
            md_output = await report_facade.export_report(rep, format_type="markdown")
            assert "# AI Research Assistant Deliverable" in md_output

            # 12. GAIA Benchmark Evaluation (Phase 13 Benchmark Tool)
            bm_rep = await benchmark_facade.run_suite()
            assert bm_rep.metrics.accuracy_percentage == 100.0

            # 13. Recall memory items (Phase 6)
            recalled = await memory_facade.recall("Quantum")
            assert recalled.total_found >= 1

            # 14. Verify Tool Registry registration of all 12 tools
            tool_names = registry.list_tools()
            assert "browser_tool" in tool_names
            assert "document_tool" in tool_names
            assert "search_tool" in tool_names
            assert "memory_tool" in tool_names
            assert "code_tool" in tool_names
            assert "vision_tool" in tool_names
            assert "integration_tool" in tool_names
            assert "workflow_tool" in tool_names
            assert "report_tool" in tool_names
            assert "benchmark_tool" in tool_names

        await asyncio.sleep(0.05)
        assert "code.indexed" in events_received
        assert "execution.completed" in events_received
        assert "search.started" in events_received
        assert "memory.created" in events_received
        assert "vision.started" in events_received
        assert "integration.started" in events_received
        assert "workflow.started" in events_received
        assert "report.started" in events_received
        assert "benchmark.started" in events_received
        assert "benchmark.completed" in events_received

    asyncio.run(_test())
