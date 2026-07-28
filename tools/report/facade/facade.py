"""Unified ReportToolFacade for the Report Generation Platform."""

import json
from typing import Dict, List, Any, Optional

from core.interfaces.tool import ITool
from core.models.metadata import ToolMetadata
from core.models.tool_result import ToolResult
from core.models.event import Event
from core.events import AsyncEventBus
from tools.report.models.report_models import (
    NormalizedReport,
    ExportFormat,
    ReportValidationResult,
)
from tools.report.registry.report_template_registry import ReportTemplateRegistry
from tools.report.composer.report_composer import ReportComposer
from tools.report.validator.report_validator import ReportValidator
from tools.report.export.export_engine import ExportEngine
from infrastructure.logging.logger import StructuredLogger


class ReportToolFacade(ITool):
    """Public unified API facade for the Report Generation Platform."""

    name = "report_tool"
    description = "Unified output generation tool for composing, validating, formatting, and exporting research reports."

    def __init__(
        self,
        registry: Optional[ReportTemplateRegistry] = None,
        composer: Optional[ReportComposer] = None,
        validator: Optional[ReportValidator] = None,
        export_engine: Optional[ExportEngine] = None,
        event_bus: Optional[AsyncEventBus] = None,
        memory_facade: Optional[Any] = None,
    ) -> None:
        self.name = "report_tool"
        self._logger = StructuredLogger("ReportToolFacade")
        self._event_bus = event_bus or AsyncEventBus()
        self._memory_facade = memory_facade

        self._registry = registry or ReportTemplateRegistry()
        self._composer = composer or ReportComposer(template_registry=self._registry)
        self._validator = validator or ReportValidator()
        self._export_engine = export_engine or ExportEngine()

        self._metadata = ToolMetadata(
            name="report_tool",
            version="1.0.0",
            description="Unified output generation tool for composing, validating, formatting, and exporting research reports.",
            capabilities=["report_composition", "citation_management", "visualization_building", "multi_format_export", "report_validation"],
            parameters_schema={
                "action": "Action to perform ('compose', 'export', 'validate', 'list_templates')",
                "title": "Report title string",
                "template": "Report template name",
                "format": "Export format ('markdown', 'html', 'json', 'pdf', 'docx')",
            },
            tags=["report", "export", "deliverable", "composition"],
            is_async=True,
            enabled=True,
        )

    @property
    def metadata(self) -> ToolMetadata:
        """Return tool metadata descriptor."""
        return self._metadata

    async def forward(self, action: str = "compose", **kwargs) -> str:
        """Standard tool execution wrapper returning JSON string."""
        try:
            title = kwargs.get("title", kwargs.get("name", "AI Research Report"))
            template = kwargs.get("template", kwargs.get("template_name", "research_report"))
            fmt = kwargs.get("format", kwargs.get("export_format", "markdown"))

            if action in ["compose", "create", "build"]:
                sources = kwargs.get("sources")
                sections = kwargs.get("sections")
                rep = await self.compose_report(title, template_name=template, sources=sources, custom_sections=sections)
                return json.dumps(rep.to_dict(), indent=2)
            elif action in ["export", "render"]:
                rep_obj = await self.compose_report(title, template_name=template)
                exported_str = await self.export_report(rep_obj, format_type=fmt)
                return exported_str
            elif action in ["validate", "check"]:
                rep_obj = await self.compose_report(title, template_name=template)
                val_res = await self.validate_report(rep_obj)
                return json.dumps(val_res.to_dict(), indent=2)
            else:
                return json.dumps({"error": f"Unknown report action '{action}'"}, indent=2)
        except Exception as e:
            self._logger.error(f"Error in ReportToolFacade.forward action '{action}': {e}")
            return json.dumps({"error": str(e)}, indent=2)

    async def execute(self, parameters: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
        """Execute method returning ToolResult object conforming to ITool interface."""
        params = dict(parameters or {})
        params.update(kwargs)
        action = params.get("action", "compose")
        try:
            output_json = await self.forward(action=action, **params)
            if output_json.startswith("{") or output_json.startswith("["):
                data = json.loads(output_json)
                if isinstance(data, dict) and "error" in data:
                    return ToolResult.error(error_message=data["error"])
                return ToolResult.success(data=data)
            return ToolResult.success(data={"rendered_report": output_json})
        except Exception as e:
            return ToolResult.error(error_message=str(e))

    async def compose_report(
        self,
        title: str,
        template_name: str = "research_report",
        sources: Optional[List[Any]] = None,
        custom_sections: Optional[List[Dict[str, Any]]] = None,
    ) -> NormalizedReport:
        """Compose structured deliverable report."""
        try:
            await self._publish_event("report.started", {"title": title, "template": template_name})
            report = await self._composer.compose_report(
                title=title,
                template_name=template_name,
                sources=sources,
                custom_sections=custom_sections,
            )
            await self._publish_event("report.composed", {"report_id": report.report_id, "sections_count": len(report.sections)})

            if self._memory_facade:
                try:
                    await self._memory_facade.remember(
                        content=f"Generated Report '{report.title}' ({len(report.sections)} sections, {len(report.citations)} citations).",
                        memory_type="knowledge",
                        tags=["report", report.template_name],
                        metadata={"report_id": report.report_id},
                    )
                except Exception as me:
                    self._logger.warning(f"Error persisting report memory: {me}")

            await self._publish_event("report.completed", {"report_id": report.report_id})
            return report
        except Exception as e:
            await self._publish_event("report.failed", {"action": "compose", "error": str(e)})
            raise

    async def export_report(self, report_or_title: Any, format_type: str = "markdown") -> str:
        """Export report into target format string."""
        try:
            if isinstance(report_or_title, str):
                report = await self.compose_report(report_or_title)
            else:
                report = report_or_title

            fmt_enum = ExportFormat(format_type.lower()) if isinstance(format_type, str) else format_type
            exported_content = await self._export_engine.export(report, fmt_enum)
            await self._publish_event("report.exported", {"report_id": report.report_id, "format": fmt_enum.value})
            return exported_content
        except Exception as e:
            await self._publish_event("report.failed", {"action": "export", "error": str(e)})
            raise

    async def validate_report(self, report_or_title: Any) -> ReportValidationResult:
        """Validate report structure and citation references."""
        try:
            if isinstance(report_or_title, str):
                report = await self.compose_report(report_or_title)
            else:
                report = report_or_title

            val_res = self._validator.validate_report(report)
            await self._publish_event("report.validated", {"report_id": report.report_id, "is_valid": val_res.is_valid})
            return val_res
        except Exception as e:
            await self._publish_event("report.failed", {"action": "validate", "error": str(e)})
            raise

    async def _publish_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish domain event over AsyncEventBus."""
        if self._event_bus:
            try:
                event_obj = Event(
                    event_type=event_type,
                    source="ReportToolFacade",
                    payload=payload,
                )
                await self._event_bus.publish(event_obj)
            except Exception as e:
                self._logger.warning(f"Error publishing report event '{event_type}': {e}")
