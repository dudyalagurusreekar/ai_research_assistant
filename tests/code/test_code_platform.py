"""Comprehensive Unit, Integration, Concurrency, and End-to-End Tests for Phase 7 Code Intelligence Platform."""

import asyncio
import os
import tempfile

from tools.code.facade.facade import CodeToolFacade
from tools.code.registry.language_registry import LanguageRegistry
from tools.code.providers.python_provider import PythonLanguageProvider
from tools.code.indexer.project_indexer import ProjectIndexer
from tools.code.dependencies.dependency_analyzer import DependencyAnalyzer
from tools.code.analysis.static_analysis import StaticAnalysisEngine
from tools.code.execution.sandboxed_executor import SandboxedExecutionEngine
from tools.code.docs.documentation_engine import DocumentationEngine
from tools.code.tool import CodeTool
from core.events import AsyncEventBus


def test_language_registry():
    """Verify language provider strategy registration and extension lookup."""
    registry = LanguageRegistry()
    py_provider = registry.get_provider_for_extension(".py")
    js_provider = registry.get_provider_for_extension(".ts")
    gen_provider = registry.get_provider_for_extension(".unknown")

    assert py_provider.language_name == "python"
    assert js_provider.language_name == "javascript"
    assert gen_provider.language_name == "generic"


def test_python_language_provider():
    """Verify Python AST symbol parsing."""
    async def _test():
        provider = PythonLanguageProvider()
        code = '''"""Sample module docstring."""
import os, sys

class SampleModel:
    """Sample class docstring."""
    def __init__(self, name: str):
        self.name = name

async def process_data(data: list) -> dict:
    """Async process data function."""
    return {"status": "ok"}
'''
        cfile = await provider.parse_file("sample.py", code)
        assert cfile.language == "python"
        assert len(cfile.symbols) >= 3
        assert len(cfile.imports) >= 2
        
        sym_names = [s.name for s in cfile.symbols]
        assert "SampleModel" in sym_names
        assert "process_data" in sym_names

    asyncio.run(_test())


def test_project_indexer():
    """Verify project directory tree indexing."""
    async def _test():
        indexer = ProjectIndexer()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dummy project structure
            main_py = os.path.join(tmpdir, "main.py")
            with open(main_py, "w", encoding="utf-8") as f:
                f.write("def main():\n    print('Hello World')\n")
            
            utils_py = os.path.join(tmpdir, "utils.py")
            with open(utils_py, "w", encoding="utf-8") as f:
                f.write("class Helper:\n    pass\n")

            project = await indexer.index_project(tmpdir)
            assert project.total_files == 2
            assert project.total_lines > 0
            assert "python" in project.languages

    asyncio.run(_test())


def test_dependency_analyzer():
    """Verify manifest file dependency parsing."""
    async def _test():
        analyzer = DependencyAnalyzer()
        with tempfile.TemporaryDirectory() as tmpdir:
            req_file = os.path.join(tmpdir, "requirements.txt")
            with open(req_file, "w", encoding="utf-8") as f:
                f.write("pytest>=8.0.0\nsmolagents==1.0.0\n")

            deps = await analyzer.analyze_dependencies(tmpdir)
            assert len(deps) == 2
            pkg_names = [d.package_name for d in deps]
            assert "pytest" in pkg_names
            assert "smolagents" in pkg_names

    asyncio.run(_test())


def test_static_analysis_engine():
    """Verify static inspection, complexity, and security warning detection."""
    async def _test():
        analysis = StaticAnalysisEngine()
        indexer = ProjectIndexer()

        with tempfile.TemporaryDirectory() as tmpdir:
            unsafe_py = os.path.join(tmpdir, "unsafe.py")
            with open(unsafe_py, "w", encoding="utf-8") as f:
                f.write("import os\n\ndef run():\n    eval('1 + 1')\n    if True:\n        print('ok')\n")

            project = await indexer.index_project(tmpdir)
            res = await analysis.analyze_project(project)

            assert res.total_files_analyzed == 1
            assert len(res.security_warnings) >= 1
            assert res.security_warnings[0]["file"] == "unsafe.py"

    asyncio.run(_test())


def test_sandboxed_executor():
    """Verify sandboxed code execution and timeout handling."""
    async def _test():
        executor = SandboxedExecutionEngine()

        # Success execution
        code_valid = "print('Hello from Sandbox')"
        res_valid = await executor.execute_code(code_valid, timeout_seconds=5.0)
        assert res_valid.status == "success"
        assert "Hello from Sandbox" in res_valid.stdout

        # Timeout execution
        code_timeout = "import time\ntime.sleep(5)"
        res_timeout = await executor.execute_code(code_timeout, timeout_seconds=0.1)
        assert res_timeout.status == "timeout"
        assert "timed out" in res_timeout.stderr.lower()

    asyncio.run(_test())


def test_documentation_engine():
    """Verify Markdown documentation generation."""
    async def _test():
        doc_engine = DocumentationEngine()
        indexer = ProjectIndexer()

        with tempfile.TemporaryDirectory() as tmpdir:
            api_py = os.path.join(tmpdir, "api.py")
            with open(api_py, "w", encoding="utf-8") as f:
                f.write("def calculate_total(x: int) -> int:\n    '''Calculates total value.'''\n    return x * 2\n")

            project = await indexer.index_project(tmpdir)
            doc_res = await doc_engine.generate_documentation(project)

            assert doc_res.symbols_documented >= 1
            assert "calculate_total" in doc_res.markdown_doc
            assert "Calculates total value." in doc_res.markdown_doc

    asyncio.run(_test())


def test_code_facade_end_to_end_and_events():
    """Verify CodeToolFacade unified APIs and AsyncEventBus notifications."""
    async def _test():
        bus = AsyncEventBus()
        events_fired = []

        async def _on_event(evt):
            events_fired.append(evt.event_type)

        bus.subscribe("repository.loaded", _on_event)
        bus.subscribe("code.indexed", _on_event)
        bus.subscribe("execution.started", _on_event)
        bus.subscribe("execution.completed", _on_event)

        facade = CodeToolFacade(event_bus=bus)

        with tempfile.TemporaryDirectory() as tmpdir:
            main_py = os.path.join(tmpdir, "main.py")
            with open(main_py, "w", encoding="utf-8") as f:
                f.write("class Engine:\n    def start(self):\n        pass\n")

            # 1. Indexing API
            project = await facade.index_project(tmpdir)
            assert project.total_files == 1

            # 2. Static Analysis API
            ana_res = await facade.analyze_code(tmpdir)
            assert ana_res.total_files_analyzed == 1

            # 3. Execution API
            exec_res = await facade.execute_code("print('Facade execute test')", timeout_seconds=5.0)
            assert exec_res.status == "success"

        # Wait briefly for async events
        await asyncio.sleep(0.05)
        assert "repository.loaded" in events_fired
        assert "code.indexed" in events_fired
        assert "execution.started" in events_fired
        assert "execution.completed" in events_fired

        # Test forward JSON method
        forward_json = await facade.forward(action="execute", code="print('forward')")
        assert "execution_id" in forward_json

    asyncio.run(_test())


def test_smolagents_code_tool_wrapper():
    """Verify smolagents CodeTool wrapper."""
    tool = CodeTool()
    res_str = tool.forward(action="execute", code="print('Smolagents wrapper test')")
    assert "execution_id" in res_str
