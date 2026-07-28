"""Data models for the Code Intelligence Platform."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from core.utils.id_generator import generate_id
from core.utils.time_utils import utc_isoformat


class SymbolType(str, Enum):
    """Categorization of code symbols."""
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    IMPORT = "import"
    INTERFACE = "interface"
    MODULE = "module"


@dataclass
class CodeSymbol:
    """Model representing an extracted code symbol."""
    symbol_id: str = field(default_factory=lambda: generate_id("sym_"))
    name: str = ""
    symbol_type: SymbolType = SymbolType.FUNCTION
    file_path: str = ""
    start_line: int = 1
    end_line: int = 1
    docstring: Optional[str] = None
    signature: str = ""
    parent_symbol_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol_id": self.symbol_id,
            "name": self.name,
            "symbol_type": self.symbol_type.value,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "docstring": self.docstring,
            "signature": self.signature,
            "parent_symbol_id": self.parent_symbol_id,
            "metadata": self.metadata,
        }


@dataclass
class CodeFile:
    """Model representing a parsed source code file."""
    file_id: str = field(default_factory=lambda: generate_id("cfile_"))
    relative_path: str = ""
    absolute_path: str = ""
    language: str = "python"
    size_bytes: int = 0
    line_count: int = 0
    symbols: List[CodeSymbol] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_id": self.file_id,
            "relative_path": self.relative_path,
            "absolute_path": self.absolute_path,
            "language": self.language,
            "size_bytes": self.size_bytes,
            "line_count": self.line_count,
            "symbols": [s.to_dict() for s in self.symbols],
            "imports": self.imports,
            "metadata": self.metadata,
        }


@dataclass
class DependencyItem:
    """Model representing a project dependency."""
    package_name: str = ""
    version_spec: str = ""
    ecosystem: str = "pip"  # 'pip', 'npm', 'maven', 'cargo', 'go'
    is_dev: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "package_name": self.package_name,
            "version_spec": self.version_spec,
            "ecosystem": self.ecosystem,
            "is_dev": self.is_dev,
        }


@dataclass
class NormalizedCodeProject:
    """Unified container model representing an indexed software project."""
    project_id: str = field(default_factory=lambda: generate_id("proj_"))
    project_name: str = ""
    root_path: str = ""
    files: List[CodeFile] = field(default_factory=list)
    dependencies: List[DependencyItem] = field(default_factory=list)
    total_files: int = 0
    total_lines: int = 0
    languages: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_isoformat)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "root_path": self.root_path,
            "files": [f.to_dict() for f in self.files],
            "dependencies": [d.to_dict() for d in self.dependencies],
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "languages": self.languages,
            "created_at": self.created_at,
        }


@dataclass
class StaticAnalysisResult:
    """Metrics and inspection results from static analysis."""
    project_id: str = ""
    total_files_analyzed: int = 0
    total_lines_of_code: int = 0
    cyclomatic_complexity: float = 1.0
    issues: List[Dict[str, Any]] = field(default_factory=list)
    security_warnings: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "total_files_analyzed": self.total_files_analyzed,
            "total_lines_of_code": self.total_lines_of_code,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "issues": self.issues,
            "security_warnings": self.security_warnings,
            "metrics": self.metrics,
        }


@dataclass
class ExecutionResult:
    """Output from sandboxed code execution."""
    execution_id: str = field(default_factory=lambda: generate_id("exec_"))
    status: str = "success"  # 'success', 'timeout', 'error'
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: float = 0.0
    memory_used_mb: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "status": self.status,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "execution_time_ms": self.execution_time_ms,
            "memory_used_mb": self.memory_used_mb,
        }


@dataclass
class DocGenResult:
    """Generated documentation output container."""
    project_name: str = ""
    markdown_doc: str = ""
    table_of_contents: List[str] = field(default_factory=list)
    symbols_documented: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "markdown_doc": self.markdown_doc,
            "table_of_contents": self.table_of_contents,
            "symbols_documented": self.symbols_documented,
        }
