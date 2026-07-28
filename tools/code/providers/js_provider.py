"""JavaScript / TypeScript Language Provider strategy implementation."""

import re
from typing import List
from tools.code.interfaces.code_interfaces import ILanguageProvider
from tools.code.models.code_models import CodeFile, CodeSymbol, SymbolType
from infrastructure.logging.logger import StructuredLogger


class JavaScriptLanguageProvider(ILanguageProvider):
    """JavaScript/TypeScript language parser strategy using regex regex extraction."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("JavaScriptLanguageProvider")

    @property
    def language_name(self) -> str:
        return "javascript"

    @property
    def file_extensions(self) -> List[str]:
        return [".js", ".jsx", ".ts", ".tsx", ".mjs"]

    async def parse_file(self, file_path: str, content: str) -> CodeFile:
        """Parse JS/TS file and extract symbols."""
        lines = content.splitlines()
        file_obj = CodeFile(
            relative_path=file_path,
            absolute_path=file_path,
            language="javascript",
            size_bytes=len(content.encode("utf-8")),
            line_count=len(lines),
            content=content,
        )

        for idx, line in enumerate(lines, start=1):
            line_str = line.strip()

            # Classes
            class_match = re.search(r"class\s+([A-Za-z0-9_$]+)", line_str)
            if class_match:
                file_obj.symbols.append(
                    CodeSymbol(
                        name=class_match.group(1),
                        symbol_type=SymbolType.CLASS,
                        file_path=file_path,
                        start_line=idx,
                        end_line=idx,
                        signature=class_match.group(0),
                    )
                )

            # Functions
            func_match = re.search(r"(?:function|const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?\(", line_str) or re.search(r"function\s+([A-Za-z0-9_$]+)", line_str)
            if func_match:
                file_obj.symbols.append(
                    CodeSymbol(
                        name=func_match.group(1),
                        symbol_type=SymbolType.FUNCTION,
                        file_path=file_path,
                        start_line=idx,
                        end_line=idx,
                        signature=func_match.group(0),
                    )
                )

            # Imports
            imp_match = re.search(r"import\s+.*?from\s+['\"](.*?)['\"]", line_str) or re.search(r"require\(['\"](.*?)['\"]\)", line_str)
            if imp_match:
                file_obj.imports.append(imp_match.group(1))

        return file_obj
