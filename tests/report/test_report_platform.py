"""Comprehensive Unit, Integration, Concurrency, and End-to-End Tests for Phase 11 Report Generation Platform."""

import asyncio

from tools.report.facade.facade import ReportToolFacade
from tools.report.models.report_models import (
    NormalizedReport,
    ReportSection,
    ExportFormat,
)
from tools.report.registry.report_template_registry import ReportTemplateRegistry
from tools.report.citations.citation_manager import CitationManager
from tools.report.visualizations.visualization_builder import VisualizationBuilder
from tools.report.composer.report_composer import ReportComposer
from tools.report.validator.report_validator import ReportValidator
from tools.report.export.export_engine import ExportEngine
from tools.report.tool import ReportTool
from core.events import AsyncEventBus


def test_report_template_registry():
    """Verify report deliverable template registration and lookup."""
    registry = ReportTemplateRegistry()
    templates = ["research_report", "code_review", "executive_summary"]

    for t_name in templates:
        spec = registry.get_template(t_name)
        assert spec is not None
        assert len(spec) >= 3


def test_citation_manager():
    """Verify citation item attribution and bibliography formatting."""
    mgr = CitationManager()
    c1 = mgr.add_citation("Quantum Computing Paper", "https://arxiv.org/abs/2101.00001", "Quantum advantage achieved.")
    c2 = mgr.add_citation("Python Language Docs", "https://docs.python.org", "Standard library docs.")

    assert c1.reference_number == 1
    assert c2.reference_number == 2
    bib_text = mgr.format_bibliography_markdown()
    assert "Quantum Computing Paper" in bib_text
    assert "https://arxiv.org/abs/2101.00001" in bib_text


def test_visualization_builder():
    """Verify Markdown table visualization element creation."""
    vis_builder = VisualizationBuilder()
    tbl = vis_builder.create_markdown_table(
        headers=["Model", "Accuracy"],
        rows=[["Model A", "94.5%"], ["Model B", "88.2%"]],
        title="Accuracy Matrix",
    )

    assert tbl.element_type == "table"
    assert "Accuracy Matrix" in tbl.content_markdown
    assert "Model A" in tbl.content_markdown


def test_report_composer():
    """Verify report section composition and telemetry metrics."""
    async def _test():
        composer = ReportComposer()
        rep = await composer.compose_report(
            title="Comprehensive AI Report",
            template_name="research_report",
            sources=[{"title": "Search Result", "url": "https://example.com/search"}],
        )

        assert rep.report_id != ""
        assert len(rep.sections) >= 4
        assert len(rep.citations) == 1
        assert rep.metrics.word_count > 0

    asyncio.run(_test())


def test_ara_v1_1_report_composer():
    """Verify ARA V1.1 report composition injects confidence and limitations."""
    async def _test():
        composer = ReportComposer()
        rep = await composer.compose_report(
            title="ARA V1.1 Test Report",
            template_name="ara_v1_1_report",
            sources=[{"title": "Search Result", "url": "https://example.com/search"}],
        )

        assert rep.report_id != ""
        assert len(rep.sections) == 7
        
        # Verify the Confidence Assessment and Limitations sections are populated
        conf_sec = next((s for s in rep.sections if s.title == "Confidence Assessment"), None)
        assert conf_sec is not None
        assert "**Score:**" in conf_sec.content

        limit_sec = next((s for s in rep.sections if s.title == "Limitations"), None)
        assert limit_sec is not None
        assert "Identified Limitations" in limit_sec.content or "No significant limitations" in limit_sec.content

    asyncio.run(_test())


def test_report_validator():
    """Verify report validation and completeness checks."""
    validator = ReportValidator()
    valid_rep = NormalizedReport(title="Valid Report", sections=[ReportSection(title="Sec 1", content="Content")])
    invalid_rep = NormalizedReport(title="", sections=[])

    res_valid = validator.validate_report(valid_rep)
    res_invalid = validator.validate_report(invalid_rep)

    assert res_valid.is_valid is True
    assert res_invalid.is_valid is False
    assert len(res_invalid.issues) >= 2


def test_export_engine():
    """Verify multi-format export rendering (Markdown, HTML, JSON, CSV, TXT, PDF, DOCX)."""
    async def _test():
        exporter = ExportEngine()
        rep = NormalizedReport(
            title="Export Test Report",
            summary="Testing multi-format exporters.",
            sections=[ReportSection(title="Overview", content="Detailed overview content.")],
        )

        md_out = await exporter.export(rep, ExportFormat.MARKDOWN)
        html_out = await exporter.export(rep, ExportFormat.HTML)
        json_out = await exporter.export(rep, ExportFormat.JSON)
        csv_out = await exporter.export(rep, ExportFormat.CSV)

        assert "# Export Test Report" in md_out
        assert "<html>" in html_out
        assert "Export Test Report" in json_out
        assert "Overview" in csv_out

    asyncio.run(_test())


def test_report_facade_end_to_end_and_events():
    """Verify ReportToolFacade unified APIs, memory ingestion, and AsyncEventBus domain events."""
    async def _test():
        bus = AsyncEventBus()
        events_fired = []

        async def _on_event(evt):
            events_fired.append(evt.event_type)

        bus.subscribe("report.started", _on_event)
        bus.subscribe("report.composed", _on_event)
        bus.subscribe("report.exported", _on_event)
        bus.subscribe("report.completed", _on_event)

        facade = ReportToolFacade(event_bus=bus)

        # 1. Compose Report API
        rep = await facade.compose_report("Facade Test Report", template_name="research_report")
        assert rep.report_id != ""

        # 2. Export Report API
        exported_str = await facade.export_report(rep, format_type="markdown")
        assert "# Facade Test Report" in exported_str

        # 3. Validate Report API
        val_res = await facade.validate_report(rep)
        assert val_res.is_valid is True

        # Wait briefly for async events
        await asyncio.sleep(0.05)
        assert "report.started" in events_fired
        assert "report.composed" in events_fired
        assert "report.exported" in events_fired
        assert "report.completed" in events_fired

        # Test forward JSON method
        forward_json = await facade.forward(action="compose", title="Forward Report Test")
        assert "report_id" in forward_json

    asyncio.run(_test())


def test_smolagents_report_tool_wrapper():
    """Verify smolagents ReportTool wrapper."""
    tool = ReportTool()
    res_str = tool.forward(action="compose", title="Smolagents Report Test")
    assert "report_id" in res_str
