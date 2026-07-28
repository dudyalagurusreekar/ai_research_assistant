"""Abstract interface contracts for the Code Intelligence Platform."""

from abc import ABC, abstractmethod
from typing import List, Optional
from tools.code.models.code_models import (
    CodeFile,
    CodeSymbol,
    NormalizedCodeProject,
    DependencyItem,
    StaticAnalysisResult,
    ExecutionResult,
    DocGenResult,
)


class ILanguageProvider(ABC):
    """Abstract strategy interface for language-specific parsing and symbol resolution."""

    @property
    @abstractmethod
    def language_name(self) -> str:
        """Language identifier (e.g., 'python', 'javascript', 'java')."""

    @property
    @abstractmethod
    def file_extensions(self) -> List[str]:
        """File extensions handled by this provider."""

    @abstractmethod
    async def parse_file(self, file_path: str, content: str) -> CodeFile:
        """Parse source file into CodeFile model and extract symbols."""


class ILanguageRegistry(ABC):
    """Abstract strategy registry interface for language providers."""

    @abstractmethod
    def register(self, provider: ILanguageProvider) -> None:
        """Register a language provider strategy."""

    @abstractmethod
    def get_provider_for_extension(self, ext: str) -> Optional[ILanguageProvider]:
        """Get provider strategy by file extension."""


class IProjectIndexer(ABC):
    """Abstract project indexing engine interface."""

    @abstractmethod
    async def index_project(self, root_path: str) -> NormalizedCodeProject:
        """Scan project directory tree and build NormalizedCodeProject model."""


class ISymbolResolver(ABC):
    """Abstract symbol resolution engine interface."""

    @abstractmethod
    async def resolve_symbols(self, project: NormalizedCodeProject) -> List[CodeSymbol]:
        """Extract and resolve symbol cross-references across project."""


class IDependencyAnalyzer(ABC):
    """Abstract dependency analysis engine interface."""

    @abstractmethod
    async def analyze_dependencies(self, root_path: str) -> List[DependencyItem]:
        """Parse manifest files and build dependency list."""


class IStaticAnalysisEngine(ABC):
    """Abstract static code analysis engine interface."""

    @abstractmethod
    async def analyze_project(self, project: NormalizedCodeProject) -> StaticAnalysisResult:
        """Run static inspection, complexity metrics, and quality linting."""


class ISandboxedExecutionEngine(ABC):
    """Abstract sandboxed code execution engine interface."""

    @abstractmethod
    async def execute_code(self, code: str, language: str = "python", timeout_seconds: float = 10.0) -> ExecutionResult:
        """Run code snippet in secure sandbox with timeout protection."""


class IDocumentationEngine(ABC):
    """Abstract documentation generator engine interface."""

    @abstractmethod
    async def generate_documentation(self, project: NormalizedCodeProject) -> DocGenResult:
        """Generate API documentation and Markdown overviews for project."""
