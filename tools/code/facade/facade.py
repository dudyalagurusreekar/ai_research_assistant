"""Unified CodeToolFacade for the Code Intelligence Platform."""

import json
from typing import Dict, List, Any, Optional

from core.interfaces.tool import ITool
from core.models.metadata import ToolMetadata
from core.models.tool_result import ToolResult
from core.models.event import Event
from core.events import AsyncEventBus
from tools.code.models.code_models import (
    NormalizedCodeProject,
    DependencyItem,
    StaticAnalysisResult,
    ExecutionResult,
    DocGenResult,
)
from tools.code.registry.language_registry import LanguageRegistry
from tools.code.indexer.project_indexer import ProjectIndexer
from tools.code.symbols.symbol_resolver import SymbolResolver
from tools.code.dependencies.dependency_analyzer import DependencyAnalyzer
from tools.code.analysis.static_analysis import StaticAnalysisEngine
from tools.code.execution.sandboxed_executor import SandboxedExecutionEngine
from tools.code.docs.documentation_engine import DocumentationEngine
from infrastructure.logging.logger import StructuredLogger


class CodeToolFacade(ITool):
    """Public unified API facade for the Code Intelligence Platform."""

    name = "code_tool"
    description = "Unified software engineering tool for repository indexing, symbol resolution, static analysis, sandboxed execution, and doc generation."

    def __init__(
        self,
        registry: Optional[LanguageRegistry] = None,
        indexer: Optional[ProjectIndexer] = None,
        resolver: Optional[SymbolResolver] = None,
        dependency_analyzer: Optional[DependencyAnalyzer] = None,
        static_analysis: Optional[StaticAnalysisEngine] = None,
        executor: Optional[SandboxedExecutionEngine] = None,
        doc_engine: Optional[DocumentationEngine] = None,
        event_bus: Optional[AsyncEventBus] = None,
        memory_facade: Optional[Any] = None,
    ) -> None:
        self.name = "code_tool"
        self._logger = StructuredLogger("CodeToolFacade")
        self._event_bus = event_bus or AsyncEventBus()
        self._memory_facade = memory_facade

        self._registry = registry or LanguageRegistry()
        self._indexer = indexer or ProjectIndexer(registry=self._registry)
        self._resolver = resolver or SymbolResolver()
        self._dependency_analyzer = dependency_analyzer or DependencyAnalyzer()
        self._static_analysis = static_analysis or StaticAnalysisEngine()
        self._executor = executor or SandboxedExecutionEngine()
        self._doc_engine = doc_engine or DocumentationEngine()

        self._metadata = ToolMetadata(
            name="code_tool",
            version="1.0.0",
            description="Unified software engineering tool for repository indexing, symbol resolution, static analysis, sandboxed execution, and doc generation.",
            capabilities=["code_indexing", "symbol_resolution", "static_analysis", "sandboxed_execution", "doc_generation"],
            parameters_schema={
                "action": "Action to perform ('index', 'symbols', 'dependencies', 'analyze', 'execute', 'docs')",
                "root_path": "Target directory or repository root path",
                "code": "Code snippet string for execution",
                "language": "Programming language identifier",
            },
            tags=["code", "engineering", "sandbox", "ast"],
            is_async=True,
            enabled=True,
        )

    @property
    def metadata(self) -> ToolMetadata:
        """Return tool metadata descriptor."""
        return self._metadata

    async def forward(self, action: str = "index", **kwargs) -> str:
        """Standard tool execution wrapper returning JSON string."""
        try:
            r_path = kwargs.get("root_path", kwargs.get("path", "."))
            if action in ["index", "scan"]:
                proj = await self.index_project(r_path)
                return json.dumps(proj.to_dict(), indent=2)
            elif action in ["symbols", "resolve"]:
                proj = await self.index_project(r_path)
                syms = await self._resolver.resolve_symbols(proj)
                return json.dumps([s.to_dict() for s in syms], indent=2)
            elif action in ["dependencies", "deps"]:
                deps = await self.analyze_dependencies(r_path)
                return json.dumps([d.to_dict() for d in deps], indent=2)
            elif action in ["analyze", "static_analysis", "lint"]:
                res_ana = await self.analyze_code(r_path)
                return json.dumps(res_ana.to_dict(), indent=2)
            elif action in ["execute", "run"]:
                code_str = kwargs.get("code", "")
                lang = kwargs.get("language", "python")
                timeout = float(kwargs.get("timeout_seconds", 10.0))
                res_exec = await self.execute_code(code_str, language=lang, timeout_seconds=timeout)
                return json.dumps(res_exec.to_dict(), indent=2)
            elif action in ["docs", "generate_docs"]:
                res_doc = await self.generate_docs(r_path)
                return json.dumps(res_doc.to_dict(), indent=2)
            else:
                return json.dumps({"error": f"Unknown code action '{action}'"}, indent=2)
        except Exception as e:
            self._logger.error(f"Error in CodeToolFacade.forward action '{action}': {e}")
            return json.dumps({"error": str(e)}, indent=2)

    async def execute(self, parameters: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
        """Execute method returning ToolResult object conforming to ITool interface."""
        params = dict(parameters or {})
        params.update(kwargs)
        action = params.get("action", "index")
        try:
            output_json = await self.forward(action=action, **params)
            data = json.loads(output_json)
            if isinstance(data, dict) and "error" in data:
                return ToolResult.error(error_message=data["error"])
            return ToolResult.success(data=data)
        except Exception as e:
            return ToolResult.error(error_message=str(e))

    async def index_project(self, root_path: str) -> NormalizedCodeProject:
        """Index directory tree and extract symbols."""
        try:
            await self._publish_event("repository.loaded", {"root_path": root_path})
            project = await self._indexer.index_project(root_path)

            # Analyze dependencies
            deps = await self._dependency_analyzer.analyze_dependencies(root_path)
            project.dependencies = deps

            await self._publish_event("code.indexed", {
                "project_id": project.project_id,
                "files_count": project.total_files,
                "lines_count": project.total_lines,
            })

            # Optionally ingest into Memory Platform if available
            if self._memory_facade:
                try:
                    await self._memory_facade.remember(
                        content=f"Indexed project '{project.project_name}': {project.total_files} files, {project.total_lines} lines.",
                        memory_type="knowledge",
                        tags=["code_project"],
                        metadata={"project_id": project.project_id},
                    )
                except Exception as me:
                    self._logger.warning(f"Error persisting project memory: {me}")

            return project
        except Exception as e:
            await self._publish_event("code.failed", {"action": "index", "error": str(e)})
            raise

    async def analyze_code(self, root_path: str) -> StaticAnalysisResult:
        """Run static inspection and quality linting."""
        try:
            project = await self.index_project(root_path)
            res = await self._static_analysis.analyze_project(project)
            await self._publish_event("static_analysis.completed", {
                "project_id": project.project_id,
                "warnings_count": len(res.security_warnings),
            })
            return res
        except Exception as e:
            await self._publish_event("code.failed", {"action": "analyze", "error": str(e)})
            raise

    async def analyze_dependencies(self, root_path: str) -> List[DependencyItem]:
        """Analyze project dependencies."""
        deps = await self._dependency_analyzer.analyze_dependencies(root_path)
        await self._publish_event("dependency.analyzed", {"root_path": root_path, "count": len(deps)})
        return deps

    async def execute_code(self, code: str, language: str = "python", timeout_seconds: float = 10.0) -> ExecutionResult:
        """Run code snippet in secure sandboxed process."""
        try:
            await self._publish_event("execution.started", {"language": language})
            res = await self._executor.execute_code(code, language=language, timeout_seconds=timeout_seconds)
            await self._publish_event("execution.completed", {"status": res.status, "exit_code": res.exit_code})
            return res
        except Exception as e:
            await self._publish_event("code.failed", {"action": "execute", "error": str(e)})
            raise

    async def generate_docs(self, root_path: str) -> DocGenResult:
        """Generate Markdown documentation for project."""
        try:
            project = await self.index_project(root_path)
            doc_res = await self._doc_engine.generate_documentation(project)
            await self._publish_event("documentation.generated", {
                "project_name": project.project_name,
                "symbols_count": doc_res.symbols_documented,
            })
            return doc_res
        except Exception as e:
            await self._publish_event("code.failed", {"action": "docs", "error": str(e)})
            raise

    async def _publish_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish domain event over AsyncEventBus."""
        if self._event_bus:
            try:
                event_obj = Event(
                    event_type=event_type,
                    source="CodeToolFacade",
                    payload=payload,
                )
                await self._event_bus.publish(event_obj)
            except Exception as e:
                self._logger.warning(f"Error publishing code event '{event_type}': {e}")
