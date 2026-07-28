"""Python Language Provider strategy implementing AST symbol parsing."""

import ast
from typing import List
from tools.code.interfaces.code_interfaces import ILanguageProvider
from tools.code.models.code_models import CodeFile, CodeSymbol, SymbolType
from infrastructure.logging.logger import StructuredLogger


class PythonLanguageProvider(ILanguageProvider):
    """Python language parser strategy using built-in ast module."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("PythonLanguageProvider")

    @property
    def language_name(self) -> str:
        return "python"

    @property
    def file_extensions(self) -> List[str]:
        return [".py", ".pyw"]

    async def parse_file(self, file_path: str, content: str) -> CodeFile:
        """Parse Python source file into CodeFile model and extract AST symbols."""
        file_obj = CodeFile(
            relative_path=file_path,
            absolute_path=file_path,
            language="python",
            size_bytes=len(content.encode("utf-8")),
            line_count=len(content.splitlines()),
            content=content,
        )

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    sym = CodeSymbol(
                        name=node.name,
                        symbol_type=SymbolType.CLASS,
                        file_path=file_path,
                        start_line=node.lineno,
                        end_line=getattr(node, "end_lineno", node.lineno),
                        docstring=ast.get_docstring(node),
                        signature=f"class {node.name}",
                    )
                    file_obj.symbols.append(sym)

                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
                    sym = CodeSymbol(
                        name=node.name,
                        symbol_type=SymbolType.FUNCTION,
                        file_path=file_path,
                        start_line=node.lineno,
                        end_line=getattr(node, "end_lineno", node.lineno),
                        docstring=ast.get_docstring(node),
                        signature=f"{prefix} {node.name}(...)",
                    )
                    file_obj.symbols.append(sym)

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        file_obj.imports.append(alias.name)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        file_obj.imports.append(node.module)

        except SyntaxError as se:
            self._logger.warning(f"Syntax error parsing '{file_path}': {se}")
        except Exception as e:
            self._logger.warning(f"AST parsing failed for '{file_path}': {e}")

        return file_obj
